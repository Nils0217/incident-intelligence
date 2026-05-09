# 🚨 Engineering Incident Intelligence + Gmail

**Auto-capture incident reports from Gmail → Clean with Kimi 2.6 → Real-time dashboard**

## What It Does

1. **Connect Gmail** - OAuth login (one-time setup)
2. **Create "AI fetch" label** - Auto-creates if missing
3. **Send incidents to Gmail** - Label them "AI fetch"
4. **Click "Sync Now"** - App pulls unread emails
5. **Auto-clean** - Kimi 2.6 structures into JSON
6. **See before/after** - Dashboard shows raw vs. cleaned
7. **Persists everything** - SQLite (never deleted)

---

## Quick Start

### 1. Install
```bash
pip install -r requirements.txt
```

### 2. Get Google OAuth Credentials
- Go to https://console.cloud.google.com
- Enable Gmail API
- Create OAuth 2.0 credentials (Desktop)
- Download JSON → Save as `client_secret.json`

### 3. Run
```bash
export PIPESHIFT_API_KEY="sk_your_key"
streamlit run app.py
```

### 4. Connect Gmail
- Click "🔗 Connect Gmail" button
- Login to Google (standard popup)
- Grant permission
- Done!

### 5. Create Label in Gmail
- Open Gmail
- Create new label: **"AI fetch"**

### 6. Send Incidents
- Forward/send emails with incident reports
- Label them **"AI fetch"**
- Click **"🔄 Sync Now"** in app
- See dashboard update instantly

---

## Features

✅ **Real-time Gmail sync** - Pull incidents on demand  
✅ **OAuth authentication** - Secure Google login  
✅ **Auto-label creation** - "AI fetch" created automatically  
✅ **Never deletes emails** - Marks as read, preserves forever  
✅ **Before/after display** - Raw email → Clean JSON side-by-side  
✅ **Error handling** - Marks failures as "needs_review"  
✅ **Live dashboard** - Shows newly added incidents instantly  
✅ **Three views:**
  - 🔗 Gmail Sync (connect & sync)
  - 📊 Live Dashboard (new incidents with before/after)
  - 🔍 All Incidents (browse, filter, search)

---

## Data Flow

```
Gmail "AI fetch" label
        ↓
    Sync Now (manual)
        ↓
Fetch unread emails
        ↓
Extract subject + body
        ↓
Send to Kimi 2.6 for cleaning
        ↓
Get structured JSON
        ↓
Store in SQLite
        ↓
Real-time Dashboard
```

---

## Output Format

Each incident gets normalized to:

```json
{
  "incident_id": "INC-2024-05-09-456",
  "timestamp": "2024-05-09T15:30:00Z",
  "severity": "P0",
  "system_affected": "Database",
  "root_cause": "Connection pool exhaustion",
  "resolution": "Restarted dependent services",
  "tags": "database,critical,incident-response"
}
```

Plus:
- Raw email text (for review)
- Email message ID (avoid duplicates)
- "needs_review" flag (if cleaning fails)

---

## Tabs Explained

### 🔗 Gmail Sync
- **Connect Gmail** - First-time setup (OAuth)
- **Sync Now** - Pull new emails from "AI fetch"
- **Setup Instructions** - Step-by-step guide
- Shows last sync status

### 📊 Live Dashboard
- **Newest incidents** - 20 most recent
- **Before/After view** - Raw email vs. clean JSON
- **"needs_review" filter** - Toggle to show failures
- Real-time updates as you sync

### 🔍 All Incidents
- **Browse all incidents** - Entire database
- **Filter by severity** - P0, P1, P2, P3, P4
- **Filter by system** - Database, API, Kubernetes, etc.
- Full details for each incident

---

## Tech Stack

| Component | Technology | Cost |
|-----------|-----------|------|
| Frontend | Streamlit | Free |
| Email API | Gmail API | Free |
| Auth | Google OAuth 2.0 | Free |
| LLM | Kimi 2.6 (Pipeshift) | $20/mo (hackathon credit) |
| Storage | SQLite | Free |
| Language | Python 3.9+ | Free |

**Total:** Free (app) + Hackathon credits (API)

---

## Setup Checklist

- [ ] `pip install -r requirements.txt`
- [ ] Download `client_secret.json` from Google Cloud
- [ ] Save `client_secret.json` in this folder
- [ ] `export PIPESHIFT_API_KEY="sk_..."`
- [ ] `streamlit run app.py`
- [ ] Click "🔗 Connect Gmail"
- [ ] Create "AI fetch" label in Gmail
- [ ] Send test email and label it
- [ ] Click "🔄 Sync Now"
- [ ] Check "📊 Live Dashboard"

---

## Important Notes

### Privacy
- ✅ OAuth is secure (standard Google authentication)
- ✅ Emails never deleted (only marked as read)
- ✅ All data stays local (SQLite on your machine)
- ✅ `client_secret.json` is private (add to .gitignore)

### Email Format
Any format works! Subject + body combined.

Example:
```
Subject: DB down at 3pm
Body: Postgres primary out of connections. 
      Restarted services. P0 critical.
```

### Error Handling
- ❌ Email already processed? Skipped
- ❌ Cleaning fails? Marked "needs_review"
- ❌ Missing label? Auto-created
- ❌ Auth fails? Click "Connect Gmail" again

---

## Troubleshooting

**"Missing client_secret.json"**
→ Download from Google Cloud Console

**"Not connecting to Gmail"**
→ Delete `gmail_token.pickle`
→ Click "Connect Gmail" again

**"No new emails found"**
→ Check they're labeled "AI fetch"
→ Check they're unread
→ Label name is case-sensitive

**"Cleaning failed for email"**
→ Check PIPESHIFT_API_KEY
→ Email marked "needs_review"
→ Can review manually in dashboard

---

## Files

```
/outputs/
├── app.py                 (Main app with Gmail)
├── requirements.txt       (Dependencies)
├── client_secret.json     (Your Google OAuth - you provide)
├── gmail_token.pickle     (Auto-created after login)
├── incidents.db           (SQLite database - auto-created)
├── GMAIL_SETUP.md         (Detailed setup guide)
├── README_GMAIL.md        (This file)
└── Other docs...
```

---

## Next Steps

1. **Read** `GMAIL_SETUP.md` for detailed setup
2. **Install** dependencies
3. **Get** `client_secret.json`
4. **Run** the app
5. **Connect** Gmail
6. **Create** "AI fetch" label
7. **Send** incident emails
8. **Sync** and watch dashboard update!

---

**Ready to automate incident capture?** 🚀
