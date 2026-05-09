#!/usr/bin/env python3
"""
Engineering Incident Intelligence - Streamlit App with Gmail Integration
Pulls incident reports from Gmail "AI fetch" label, cleans with Gemma 4 26B, stores in SQLite
"""

import streamlit as st
import sqlite3
import json
import os
import requests
from datetime import datetime
import re
from pathlib import Path
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient import discovery

# ============================================================================
# CONFIG & SETUP
# ============================================================================

DB_PATH = "incidents.db"
PIPESHIFT_API_KEY = os.getenv("PIPESHIFT_API_KEY", "")
FORCE_MOCK_MODE = os.getenv("FORCE_MOCK_MODE", "false").lower() == "true"
USE_MOCK_MODE = FORCE_MOCK_MODE or not PIPESHIFT_API_KEY
GMAIL_TOKEN_PATH = "gmail_token.pickle"
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
CLIENT_SECRETS_FILE = "client_secret.json"  # User must provide this

# System prompt - WITH CLEAR JSON TEMPLATE
CLEANING_PROMPT = """Extract incident data from the email. Generate a UNIQUE incident_id using format INC-YYYY-MM-DD-NNN (use current date and random 3-digit number). Return ONLY valid JSON (no markdown, no extra text):

{{"incident_id":"INC-2024-05-09-123","timestamp":"2024-05-09T15:30:00Z","severity":"P1","system_affected":"Database","root_cause":"root cause here","resolution":"resolution here","tags":"tag1,tag2"}}

Email to parse:
{report_text}"""


# ============================================================================
# DATABASE SETUP
# ============================================================================

def init_db():
    """Initialize SQLite database with incidents table."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id TEXT UNIQUE NOT NULL,
            timestamp TEXT NOT NULL,
            severity TEXT NOT NULL,
            system_affected TEXT NOT NULL,
            root_cause TEXT NOT NULL,
            resolution TEXT NOT NULL,
            tags TEXT NOT NULL,
            raw_report TEXT NOT NULL,
            email_message_id TEXT,
            needs_review INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def get_db_connection():
    """Get SQLite connection with better concurrency handling."""
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for better concurrency
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def incident_exists(incident_id):
    """Check if incident already in DB."""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute("SELECT 1 FROM incidents WHERE incident_id = ?", (incident_id,))
        exists = c.fetchone() is not None
        return exists
    finally:
        conn.close()


def incident_by_email_id(email_message_id):
    """Check if email already processed."""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute("SELECT id FROM incidents WHERE email_message_id = ?", (email_message_id,))
        result = c.fetchone()
        return result is not None
    finally:
        conn.close()


def save_incident(incident_json, raw_report, email_message_id=None, needs_review=False):
    """Save cleaned incident to database."""
    try:
        conn = get_db_connection()
        try:
            c = conn.cursor()
            c.execute('''
                INSERT INTO incidents
                (incident_id, timestamp, severity, system_affected, root_cause, resolution, tags, raw_report, email_message_id, needs_review)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                incident_json.get('incident_id'),
                incident_json.get('timestamp'),
                incident_json.get('severity'),
                incident_json.get('system_affected'),
                incident_json.get('root_cause'),
                incident_json.get('resolution'),
                incident_json.get('tags'),
                raw_report,
                email_message_id,
                1 if needs_review else 0
            ))
            conn.commit()
            return True
        finally:
            conn.close()
    except sqlite3.IntegrityError:
        return False


def load_all_incidents():
    """Load all incidents from database."""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM incidents ORDER BY created_at DESC")
        incidents = [dict(row) for row in c.fetchall()]
        return incidents
    finally:
        conn.close()


def load_new_incidents(limit=10):
    """Load newest incidents."""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM incidents ORDER BY created_at DESC LIMIT ?", (limit,))
        incidents = [dict(row) for row in c.fetchall()]
        return incidents
    finally:
        conn.close()


# ============================================================================
# GMAIL INTEGRATION
# ============================================================================

def get_gmail_service():
    """Get authenticated Gmail service."""
    creds = None

    # Load existing token
    if os.path.exists(GMAIL_TOKEN_PATH):
        with open(GMAIL_TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)

    # Refresh or create new token
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif not creds:
        if not os.path.exists(CLIENT_SECRETS_FILE):
            st.error(f"❌ Missing {CLIENT_SECRETS_FILE}")
            st.info("Download your OAuth credentials from Google Cloud Console")
            return None

        flow = InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, GMAIL_SCOPES)
        creds = flow.run_local_server(port=0)

        # Save token for future use
        with open(GMAIL_TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)

    return discovery.build('gmail', 'v1', credentials=creds)


def get_ai_fetch_label_id(service):
    """Get the ID of 'AI fetch' label."""
    try:
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])

        for label in labels:
            if label['name'] == 'AI fetch':
                return label['id']

        # Label doesn't exist, create it
        label_body = {
            'name': 'AI fetch',
            'labelListVisibility': 'labelShow',
            'messageListVisibility': 'show'
        }
        created = service.users().labels().create(userId='me', body=label_body).execute()
        return created['id']
    except Exception as e:
        st.error(f"Error getting label: {str(e)}")
        return None


def fetch_emails_from_label(service, label_id, max_results=10):
    """Fetch emails from AI fetch label (all emails, not just unread)."""
    try:
        # Fetch ANY email in the label, regardless of read status
        # The database will track which ones we've already processed
        results = service.users().messages().list(
            userId='me',
            labelIds=label_id,
            maxResults=max_results
        ).execute()

        messages = results.get('messages', [])

        # Debug: Show total count
        total_in_label = results.get('resultSizeEstimate', 0)
        print(f"📊 Total emails in 'AI fetch': {total_in_label}")
        print(f"📥 Fetching up to {max_results}, found {len(messages)}")
        email_data = []

        for message in messages:
            msg = service.users().messages().get(
                userId='me',
                id=message['id'],
                format='full'
            ).execute()

            headers = msg['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')

            # Extract body
            body = ""
            if 'parts' in msg['payload']:
                for part in msg['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body'].get('data', '')
                        if data:
                            import base64
                            body = base64.urlsafe_b64decode(data).decode('utf-8')
                            break
            else:
                data = msg['payload']['body'].get('data', '')
                if data:
                    import base64
                    body = base64.urlsafe_b64decode(data).decode('utf-8')

            email_data.append({
                'id': message['id'],
                'subject': subject,
                'sender': sender,
                'body': body,
                'combined': f"{subject}\n\n{body}"
            })

        return email_data
    except Exception as e:
        st.error(f"Error fetching emails: {str(e)}")
        return []


def mark_email_as_read(service, message_id):
    """Mark email as read."""
    try:
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
        return True
    except Exception as e:
        st.warning(f"Could not mark as read: {str(e)}")
        return False


# ============================================================================
# LLM INTEGRATION
# ============================================================================

def clean_incident_with_gemma(messy_report):
    """
    Send messy report to Gemma 4 26B via Pipeshift API for cleaning.
    Falls back to mock data if no API key.
    """
    if USE_MOCK_MODE:
        return mock_clean_incident(messy_report)

    # Truncate email to avoid token limit
    max_length = 800
    truncated_report = messy_report[:max_length]
    if len(messy_report) > max_length:
        truncated_report += "..."

    prompt = CLEANING_PROMPT.format(report_text=truncated_report)
    print(f"   Prompt length: {len(prompt)} chars")

    # Retry logic for API failures
    max_retries = 2
    for attempt in range(max_retries):
        try:
            print(f"🔄 Calling Pipeshift API (attempt {attempt + 1}/{max_retries})...")
            print(f"   URL: https://api.pipeshift.com/api/v0/chat/completions")
            print(f"   Model: google/gemma-4-26B-A4B-it")

            # Correct Pipeshift endpoint with Gemma 4
            response = requests.post(
                "https://api.pipeshift.com/api/v0/chat/completions",
                json={
                    "model": "google/gemma-4-26B-A4B-it",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 1,
                    "max_tokens": 500,  # Small response needed
                    "stream": False
                },
                headers={
                    "Authorization": f"Bearer {PIPESHIFT_API_KEY}",
                    "Content-Type": "application/json"
                },
                timeout=90
            )

            # Check response status
            if response.status_code == 502:
                print(f"⚠️ 502 Bad Gateway - server issue, retrying...")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2)
                    continue
                else:
                    print(f"❌ API Error 502: Server unavailable")
                    return None

            if response.status_code != 200:
                error_msg = f"API Error {response.status_code}: {response.text[:200]}"
                print(f"❌ {error_msg}")
                return None

            response.raise_for_status()

            result = response.json()
            print(f"✓ API Response received")

            # Extract completion from response (OpenAI format)
            if result.get("choices") and len(result["choices"]) > 0:
                message = result["choices"][0].get("message", {})
                content = message.get("content")
                finish_reason = result["choices"][0].get("finish_reason", "")

                print(f"   Content: {str(content)[:100]}")
                print(f"   Finish reason: {finish_reason}")

                if not content:
                    print(f"⚠️ Empty response")
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(1)
                        continue
                    return None

                if content:
                    print(f"✓ Got response text")
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        try:
                            cleaned = json.loads(json_match.group())
                            print(f"✓ Successfully parsed JSON:")
                            print(f"   ID: {cleaned.get('incident_id')}")
                            print(f"   Severity: {cleaned.get('severity')}")
                            print(f"   System: {cleaned.get('system_affected')}")
                            print(f"   Root Cause: {cleaned.get('root_cause')}")

                            # Check for required fields
                            required = ['incident_id', 'timestamp', 'severity', 'system_affected', 'root_cause']
                            missing = [f for f in required if not cleaned.get(f)]
                            if missing:
                                print(f"⚠️ Missing fields: {', '.join(missing)}")

                            return cleaned
                        except json.JSONDecodeError as e:
                            print(f"❌ JSON decode error: {str(e)}")
                            return None

            print(f"⚠️ No valid JSON in response")
            return None

        except requests.exceptions.Timeout:
            print("❌ API Timeout")
            if attempt < max_retries - 1:
                import time
                time.sleep(2)
                continue
            return None
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Connection Error")
            if attempt < max_retries - 1:
                import time
                time.sleep(2)
                continue
            return None
        except Exception as e:
            print(f"❌ API Error: {str(e)}")
            if attempt < max_retries - 1:
                import time
                time.sleep(1)
                continue
            return None

    return None


def mock_clean_incident(messy_report):
    """Mock cleaning using pattern matching."""
    now = datetime.now()
    incident_id = f"INC-{now.strftime('%Y-%m-%d')}-{hash(messy_report) % 1000:03d}"

    timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2})[T\s](\d{2}:\d{2})', messy_report, re.IGNORECASE)
    if timestamp_match:
        timestamp = f"{timestamp_match.group(1)}T{timestamp_match.group(2)}:00Z"
    else:
        timestamp = now.isoformat() + "Z"

    severity = "P3"
    if re.search(r'\b(P0|critical|sev-1|major outage)\b', messy_report, re.IGNORECASE):
        severity = "P0"
    elif re.search(r'\b(P1|high|sev-2|significant)\b', messy_report, re.IGNORECASE):
        severity = "P1"
    elif re.search(r'\b(P2|medium|sev-3)\b', messy_report, re.IGNORECASE):
        severity = "P2"
    elif re.search(r'\b(P4|low|sev-5|minor)\b', messy_report, re.IGNORECASE):
        severity = "P4"

    systems = []
    system_keywords = {
        'database': ['db', 'postgres', 'mysql', 'mongodb', 'redis'],
        'API Gateway': ['api gateway', 'gateway'],
        'Auth Service': ['auth', 'login', 'oauth'],
        'CDN': ['cdn', 'cloudflare'],
        'Kubernetes': ['k8s', 'kubernetes', 'pod'],
        'Cache': ['cache', 'memcache']
    }

    for system, keywords in system_keywords.items():
        if any(kw in messy_report.lower() for kw in keywords):
            systems.append(system)
    system_affected = systems[0] if systems else "Unknown Service"

    root_cause = "Database connection pool exhaustion"
    if "memory" in messy_report.lower():
        root_cause = "Memory leak"
    elif "timeout" in messy_report.lower():
        root_cause = "Request timeout"
    elif "deploy" in messy_report.lower():
        root_cause = "Bad deployment"
    elif "config" in messy_report.lower():
        root_cause = "Configuration error"

    resolution = "Restarted services"
    if "rollback" in messy_report.lower():
        resolution = "Rolled back deployment"
    elif "scale" in messy_report.lower():
        resolution = "Scaled up instances"

    tags_set = set()
    if "database" in messy_report.lower():
        tags_set.add("database")
    if severity in ["P0", "P1"]:
        tags_set.add("critical")

    tags = ",".join(sorted(tags_set)) if tags_set else "untagged"

    return {
        "incident_id": incident_id,
        "timestamp": timestamp,
        "severity": severity,
        "system_affected": system_affected,
        "root_cause": root_cause,
        "resolution": resolution,
        "tags": tags
    }


# ============================================================================
# UI COMPONENTS
# ============================================================================

def render_incident_card(incident, show_raw=False, raw_text=""):
    """Render a single incident as a card."""
    severity_color = {
        "P0": "🔴", "P1": "🟠", "P2": "🟡", "P3": "🔵", "P4": "⚪"
    }

    color = severity_color.get(incident['severity'], "⚪")
    needs_review = "⚠️ NEEDS REVIEW" if incident.get('needs_review') else ""

    with st.container(border=True):
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown(f"**{incident['incident_id']}** {color} `{incident['severity']}` {needs_review}")
            st.caption(f"System: {incident['system_affected']}")
        with col2:
            st.caption(incident['timestamp'][:10])
        with col3:
            st.caption(f"Added: {incident['created_at'][:19]}")

        if show_raw and raw_text:
            col_before, col_after = st.columns(2)
            with col_before:
                st.write("**📥 Raw Email**")
                st.text_area("", raw_text, height=200, disabled=True, key=f"raw_{incident['id']}")
            with col_after:
                st.write("**📤 Clean JSON**")
                st.code(json.dumps({
                    'incident_id': incident['incident_id'],
                    'timestamp': incident['timestamp'],
                    'severity': incident['severity'],
                    'system_affected': incident['system_affected'],
                    'root_cause': incident['root_cause'],
                    'resolution': incident['resolution'],
                    'tags': incident['tags']
                }, indent=2), language='json')
        else:
            st.write(f"**Root Cause:** {incident['root_cause']}")
            st.write(f"**Resolution:** {incident['resolution']}")
            if incident['tags']:
                tags = [t.strip() for t in incident['tags'].split(',') if t.strip()]
                st.write(f"**Tags:** {' '.join([f'`{t}`' for t in tags])}")


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    st.set_page_config(page_title="Incident Intelligence + Gmail", layout="wide")

    init_db()

    st.title("🚨 Engineering Incident Intelligence + Gmail")
    st.markdown("**Auto-capture from Gmail → Clean with Kimi 2.6 → Real-time Dashboard**")

    if USE_MOCK_MODE:
        st.info("⚙️ **Demo Mode**: Using mock cleaning. Set `PIPESHIFT_API_KEY` for real Kimi 2.6.")

    # Tabs
    tab1, tab2, tab3 = st.tabs(["🔗 Gmail Sync", "📊 Live Dashboard", "🔍 All Incidents"])

    # ========== TAB 1: GMAIL SYNC ==========
    with tab1:
        st.subheader("Connect Gmail & Sync Incidents")

        # Show API Key Status
        st.divider()
        st.write("**API Key Status:**")
        if PIPESHIFT_API_KEY:
            st.success(f"✅ Gemma 4 API Key Set: `{PIPESHIFT_API_KEY[:15]}...`")
        else:
            st.error("❌ PIPESHIFT_API_KEY not set! Set it before running: `export PIPESHIFT_API_KEY='sk_...'`")
        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔗 Connect Gmail", key="connect_gmail", use_container_width=True):
                try:
                    service = get_gmail_service()
                    if service:
                        st.success("✅ Gmail connected!")
                        st.session_state.gmail_service = service
                except Exception as e:
                    st.error(f"Connection failed: {str(e)}")

        with col2:
            if st.button("🔄 Sync Now", key="sync_btn", use_container_width=True):
                try:
                    service = get_gmail_service()
                    if not service:
                        st.error("❌ Not connected to Gmail")
                        st.stop()

                    label_id = get_ai_fetch_label_id(service)
                    if not label_id:
                        st.error("❌ Could not find/create 'AI fetch' label")
                        st.stop()

                    with st.spinner("📧 Fetching emails from 'AI fetch' label..."):
                        emails = fetch_emails_from_label(service, label_id, max_results=10)

                    if not emails:
                        st.warning("⚠️ No emails found in 'AI fetch' label")
                        st.info("""
**Troubleshooting:**
1. Are your emails labeled **"AI fetch"**? (Check the label name is exact)
2. Already synced? Check the database - they may already be processed
3. Try sending a new email and labeling it
                        """)
                        st.stop()

                    st.write(f"📧 Found {len(emails)} unread email(s). Processing...")

                    processed_count = 0
                    failed_count = 0
                    skipped_count = 0
                    sync_results = []

                    for idx, email in enumerate(emails, 1):
                        if incident_by_email_id(email['id']):
                            skipped_count += 1
                            sync_results.append({
                                'subject': email['subject'][:50],
                                'status': '⏭️ SKIPPED',
                                'reason': 'Already processed'
                            })
                            continue

                        st.write(f"**[{idx}/{len(emails)}] Processing:** {email['subject'][:60]}...")

                        with st.spinner(f"Cleaning incident..."):
                            cleaned = clean_incident_with_gemma(email['combined'])

                            if cleaned:
                                # ✅ SUCCESS - Save and mark as read
                                needs_review = False
                                if save_incident(cleaned, email['combined'], email['id'], needs_review):
                                    processed_count += 1

                                    # Show what was extracted
                                    st.write("**Extracted:**")
                                    col_e1, col_e2, col_e3 = st.columns(3)
                                    with col_e1:
                                        st.write(f"🆔 {cleaned.get('incident_id', 'N/A')}")
                                    with col_e2:
                                        sev = cleaned.get('severity', 'N/A')
                                        colors = {'P0': '🔴', 'P1': '🟠', 'P2': '🟡', 'P3': '🔵', 'P4': '⚪'}
                                        st.write(f"{colors.get(sev, '⚪')} {sev}")
                                    with col_e3:
                                        st.write(f"🖥️ {cleaned.get('system_affected', 'N/A')}")

                                    st.write(f"**Root Cause:** {cleaned.get('root_cause', 'N/A')}")

                                    sync_results.append({
                                        'subject': email['subject'][:50],
                                        'status': '✅ SUCCESS',
                                        'severity': cleaned.get('severity'),
                                        'system': cleaned.get('system_affected')
                                    })
                                    st.success(f"✅ Saved to database")
                                    # Mark as read only on success
                                    mark_email_as_read(service, email['id'])
                                else:
                                    sync_results.append({
                                        'subject': email['subject'][:50],
                                        'status': '⚠️ DUPLICATE',
                                        'reason': 'Already in database'
                                    })
                                    mark_email_as_read(service, email['id'])
                            else:
                                # ❌ FAILED - Don't save, leave unread for retry
                                st.error(f"❌ Gemma API failed - email NOT saved, will retry next sync")
                                failed_count += 1
                                sync_results.append({
                                    'subject': email['subject'][:50],
                                    'status': '❌ FAILED',
                                    'reason': 'Gemma API error - will retry next sync'
                                })
                                # DO NOT mark as read - keep it unread so it gets retried

                    # Show sync summary
                    st.divider()
                    st.subheader("📊 Sync Summary")
                    col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns(5)
                    with col_s1:
                        st.metric("📧 Emails Found", len(emails))
                    with col_s2:
                        st.metric("✅ Saved", processed_count)
                    with col_s3:
                        st.metric("⏭️ Skipped", skipped_count)
                    with col_s4:
                        st.metric("❌ Failed", failed_count)
                    with col_s5:
                        expected_new = processed_count + failed_count
                        st.metric("🔍 Expected New", expected_new)

                    # Detailed breakdown
                    st.info(f"""
**📋 Breakdown:**
- **{len(emails)}** emails in "AI fetch" label
- **{processed_count}** successfully parsed & saved ✅
- **{skipped_count}** already processed before ⏭️
- **{failed_count}** failed to parse ❌
- **Total in database:** check "All Incidents" tab
                    """)

                    # Show detailed results
                    if sync_results:
                        st.divider()
                        st.subheader("✅ Sync Complete - Results:")
                        for result in sync_results:
                            status = result['status']
                            subject = result['subject']
                            if status == '✅ SUCCESS':
                                with st.container(border=True):
                                    st.success(f"{status} - {subject}")
                                    st.write(f"  **Severity:** {result.get('severity')} | **System:** {result.get('system')}")
                            elif status == '⚠️ NEEDS REVIEW':
                                st.warning(f"{status} - {subject} - {result.get('reason')}")
                            elif status == '⏭️ SKIPPED':
                                st.info(f"{status} - {subject} - {result.get('reason')}")
                            elif status == '❌ FAILED':
                                st.error(f"{status} - {subject} - {result.get('reason')}")

                        st.divider()
                        st.info("✅ **Check the 'Live Dashboard' tab to see your incidents!**")
                        st.rerun()

                except Exception as e:
                    st.error(f"❌ Sync error: {str(e)}")
                    import traceback
                    st.write("**Error details:**")
                    st.code(traceback.format_exc())

        st.divider()
        st.subheader("Setup Instructions")
        with st.expander("📋 How to set up Gmail integration", expanded=True):
            st.markdown("""
            1. **Create 'AI fetch' label** in Gmail (or app creates it automatically)
            2. **Forward incident reports** to your email and label them "AI fetch"
            3. **Click "Connect Gmail"** - opens Google login (once only)
            4. **Click "Sync Now"** - fetches and cleans incidents
            5. **Check Dashboard** - see newly added incidents with before/after

            **Email Format:** Any format works! Subject + body will be combined and cleaned.
            """)

    # ========== TAB 2: LIVE DASHBOARD ==========
    with tab2:
        st.subheader("📊 Newly Added Incidents (Latest First)")

        new_incidents = load_new_incidents(limit=20)
        all_incidents_count = len(load_all_incidents())
        print(f"DEBUG: Dashboard loaded {len(new_incidents)} incidents, {all_incidents_count} total in DB")

        # Show email-to-incident mapping
        st.info(f"""
**📧 Email to Incident Mapping:**
- Incidents in database: **{all_incidents_count}** total
- Latest incidents shown below: **{len(new_incidents)}** most recent
- If you sent 4 emails but see 3 incidents:
  - 1 may have been skipped (already processed)
  - 1 may have failed to parse (check sync tab)
  - Check "🔍 All Incidents" tab for complete list
        """)

        if not new_incidents:
            st.warning("⚠️ **No incidents yet!** Go to the '🔗 Gmail Sync' tab and click 'Sync Now' to pull incidents from Gmail")
        else:
            col_metric1, col_metric2, col_metric3 = st.columns(3)
            with col_metric1:
                st.metric("📊 Total Incidents", len(new_incidents))
            with col_metric2:
                successful = len([i for i in new_incidents if not i['needs_review']])
                st.metric("✅ Successful", successful)
            with col_metric3:
                failed = len([i for i in new_incidents if i['needs_review']])
                st.metric("⚠️ Needs Review", failed)

            st.divider()

            # Filter for needs_review
            show_all = st.toggle("Show all incidents", value=True)

            if not show_all:
                new_incidents = [i for i in new_incidents if i['needs_review']]
                if new_incidents:
                    st.write(f"**Showing {len(new_incidents)} incidents marked for review:**")
                else:
                    st.success("✅ All incidents extracted successfully!")

            if new_incidents:
                for idx, incident in enumerate(new_incidents, 1):
                    st.write(f"**Incident {idx}:**")
                    raw_text = incident.get('raw_report', 'No raw report')
                    print(f"DEBUG: Rendering incident {incident.get('incident_id')}")
                    render_incident_card(incident, show_raw=True, raw_text=raw_text)
            else:
                st.info("No incidents to display with current filters")

    # ========== TAB 3: ALL INCIDENTS ==========
    with tab3:
        st.subheader("🔍 All Incidents")

        all_incidents = load_all_incidents()

        if not all_incidents:
            st.info("No incidents in database")
        else:
            st.metric("Total Incidents", len(all_incidents))

            # Filters
            col1, col2 = st.columns(2)
            with col1:
                severity_filter = st.multiselect(
                    "Filter by severity:",
                    options=["P0", "P1", "P2", "P3", "P4"],
                    default=[]
                )
            with col2:
                system_filter = st.multiselect(
                    "Filter by system:",
                    options=sorted(set(i['system_affected'] for i in all_incidents)),
                    default=[]
                )

            filtered = all_incidents
            if severity_filter:
                filtered = [i for i in filtered if i['severity'] in severity_filter]
            if system_filter:
                filtered = [i for i in filtered if i['system_affected'] in system_filter]

            st.write(f"**Showing {len(filtered)} of {len(all_incidents)} incidents**")

            for incident in filtered:
                render_incident_card(incident, show_raw=False)


if __name__ == "__main__":
    main()
