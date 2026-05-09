# Gmail Integration Setup

## What Changed

The app now:
- ✅ **Connects to your Gmail** via OAuth (secure, standard Google login)
- ✅ **Reads "AI fetch" label** - automatically created if needed
- ✅ **Manual sync button** - pull new emails on demand
- ✅ **Never deletes emails** - just marks as read
- ✅ **Auto-cleans with Kimi** - via Pipeshift API
- ✅ **Marks failures** - "needs_review" tag if cleaning fails
- ✅ **Real-time dashboard** - shows newly added incidents with before/after

---

## Setup (5 minutes)

### Step 1: Get Google OAuth Credentials

1. Go to: https://console.cloud.google.com
2. Create a new project (or select existing)
3. Enable Gmail API:
   - Search "Gmail API"
   - Click "Enable"
4. Create OAuth credentials:
   - Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
   - Choose "Desktop application"
   - Download the JSON file
5. **Save the file as `client_secret.json`** in the same folder as `app.py`

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Run the App

```bash
export PIPESHIFT_API_KEY="sk_your_key_here"
streamlit run app.py
```

### Step 4: Connect Gmail

1. Go to **"🔗 Gmail Sync"** tab
2. Click **"🔗 Connect Gmail"**
3. Browser opens → Sign in with Google
4. Grant permission (app asks to read/modify emails)
5. Closes automatically → You're connected!

### Step 5: Setup Gmail Label

In your Gmail:
1. Create a new label called **"AI fetch"**
2. Any emails labeled "AI fetch" = incidents to process

### Step 6: Sync!

1. Forward incident reports to your email
2. Label them **"AI fetch"** in Gmail
3. Go to **"🔗 Gmail Sync"** tab
4. Click **"🔄 Sync Now"**
5. App fetches, cleans, and stores
6. Check **"📊 Live Dashboard"** to see before/after

---

## How It Works

### Email Format
- **Subject:** Brief incident title
- **Body:** Details (timestamps, systems, what happened, etc.)
- **Example:**
  ```
  Subject: Database connection pool exhausted at 3pm
  Body: 
  Our postgres primary ran out of connections around 3pm UTC.
  Pool was at 500+ waiting. We restarted all dependent services
  (auth, payments, user api). Full recovery took ~8 mins.
  Severity: critical/P0
  ```

### Processing Flow
```
1. Email labeled "AI fetch" in Gmail
2. Click "Sync Now" button
3. App fetches unread emails from "AI fetch"
4. For each email:
   a. Extracts subject + body
   b. Sends to Kimi 2.6 for cleaning
   c. Gets back clean JSON
   d. Stores in SQLite
   e. Marks email as read (never deleted!)
5. Email marked "needs_review" if cleaning failed
6. Dashboard shows newly added incidents
```

### What Gets Saved
```json
{
  "incident_id": "INC-2024-05-09-123",
  "timestamp": "2024-05-09T15:30:00Z",
  "severity": "P0",
  "system_affected": "Database",
  "root_cause": "Connection pool exhaustion",
  "resolution": "Restarted dependent services",
  "tags": "database,critical,incident-response"
}
```

Plus:
- Raw email text (so you can see what was pulled)
- Email message ID (to avoid re-processing)
- "needs_review" flag (if cleaning failed)

---

## Dashboard Tabs

### 🔗 Gmail Sync
- Connect to Gmail (OAuth login)
- Manual "Sync Now" button
- Shows setup instructions

### 📊 Live Dashboard
- Shows 20 newest incidents
- Before/after JSON side-by-side
- Toggle to show only "needs_review"
- Real-time as you sync

### 🔍 All Incidents
- Browse all incidents
- Filter by severity (P0-P4)
- Filter by system affected
- Full details for each incident

---

## Important Notes

### Privacy & Security
- ✅ OAuth is **secure** - standard Google authentication
- ✅ Emails are **never deleted** - just marked as read
- ✅ `client_secret.json` should be kept **private** (add to .gitignore)
- ✅ Token stored in `gmail_token.pickle` (local machine only)
- ✅ All data stays **local** (SQLite on your machine)

### Error Handling
- ❌ Email fails to clean? → Marked "needs_review"
- ❌ Already processed? → Skipped (by message ID)
- ❌ Missing "AI fetch" label? → Auto-created

### Limits
- Syncs up to 10 emails per click
- Reads only **unread** emails
- Never deletes anything

---

## Troubleshooting

### "Missing client_secret.json"
→ Download from Google Cloud Console (see Step 1)

### "Gmail not connecting"
→ Check internet connection
→ Make sure OAuth credentials are valid
→ Delete `gmail_token.pickle` and try again

### "No new emails found"
→ Make sure emails are labeled "AI fetch"
→ Make sure they're marked as **unread**
→ Check label name is exactly "AI fetch" (case-sensitive)

### "Cleaning failed for email"
→ Check error in "📊 Live Dashboard"
→ Email marked "needs_review" - you can review manually
→ Could be API issue - check PIPESHIFT_API_KEY

### "Want to test without Gmail?"
→ Use the "📝 Clean Reports" tab (still in old version)
→ Or run `python test_demo.py`

---

## Next Steps

1. ✅ Install dependencies: `pip install -r requirements.txt`
2. ✅ Download `client_secret.json` from Google Cloud Console
3. ✅ Run: `streamlit run app.py`
4. ✅ Connect Gmail
5. ✅ Label emails "AI fetch" in Gmail
6. ✅ Click "Sync Now" on app
7. ✅ Check Dashboard!

---

## Files

- `app.py` - Main app with Gmail integration
- `requirements.txt` - Updated with Gmail libraries
- `client_secret.json` - Your Google OAuth credentials (you provide this)
- `gmail_token.pickle` - Auto-created after first login (keep private)
- `incidents.db` - SQLite database (auto-created)
- `GMAIL_SETUP.md` - This file

---

**Ready to sync!** 🚀
