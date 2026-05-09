# Quick Start - Gmail Integration (10 minutes)

## Prerequisites
- Google account with Gmail
- Pipeshift API key ($50 hackathon credit)

## Step 1: Install (1 min)
```bash
cd /Users/liunils/Desktop/Hackathon/Hack\ gmail\ fetch/outputs
pip install -r requirements.txt
```

## Step 2: Get Google OAuth Credentials (3 min)

1. Go to: https://console.cloud.google.com
2. **Create new project** (or use existing)
3. **Enable Gmail API:**
   - Search box: "Gmail API"
   - Click result
   - Click "ENABLE"
4. **Create credentials:**
   - Left menu: "Credentials"
   - Top: "Create Credentials" → "OAuth 2.0 Client ID"
   - Application type: "Desktop application"
   - Click "Create"
   - Click "Download JSON"
5. **Save the file:**
   - Rename to: `client_secret.json`
   - Put in same folder as `app.py`

## Step 3: Set API Key (1 min)
```bash
export PIPESHIFT_API_KEY="sk_your_actual_key_here"
```

## Step 4: Run App (1 min)
```bash
streamlit run app.py
```

Browser opens automatically → You see the app!

## Step 5: Connect Gmail (2 min)

1. Go to **"🔗 Gmail Sync"** tab
2. Click **"🔗 Connect Gmail"** button
3. Google login popup appears
4. Sign in with your Gmail
5. "This app wants to access your Gmail" → Click **"Allow"**
6. Done! You'll see ✅ confirmation

## Step 6: Create Label in Gmail (1 min)

Open Gmail:
1. Left sidebar: **"Labels"** → **"Create new label"**
2. Name: `AI fetch`
3. Click "Create"
4. Done!

## Step 7: Test It!

Send a test email:
```
To: your-email@gmail.com
Subject: Database crashed at 3pm
Body: Our postgres primary ran out of connections around 3pm UTC.
      Pool exhausted. We restarted all services. 
      Full recovery took ~8 mins.
      P0 critical severity.
```

In Gmail:
1. Find the email
2. Click label icon (or more)
3. Select **"AI fetch"**
4. Email now labeled

In the App:
1. Go to **"🔗 Gmail Sync"** tab
2. Click **"🔄 Sync Now"**
3. Wait for processing...
4. Go to **"📊 Live Dashboard"** tab
5. See your incident! 🎉

Shows:
- **Left:** Raw email (what was pulled)
- **Right:** Clean JSON (what Kimi cleaned it to)

---

## That's It!

Now:
- ✅ Keep sending emails with incidents
- ✅ Label them "AI fetch"
- ✅ Click "Sync Now" whenever you want
- ✅ Dashboard updates instantly
- ✅ Kimi auto-cleans everything
- ✅ SQLite stores everything forever

---

## Troubleshooting Quick Fixes

**"Can't find client_secret.json"**
→ Make sure you downloaded it from Google Cloud
→ Make sure it's in the same folder as app.py
→ Filename must be exactly `client_secret.json`

**"Gmail won't connect"**
→ Delete `gmail_token.pickle` file
→ Click "Connect Gmail" button again
→ Go through login flow again

**"No emails found"**
→ Make sure email is labeled "AI fetch"
→ Make sure it's **unread** in Gmail
→ Label name is case-sensitive
→ Click "Sync Now" again

**"Cleaning failed"**
→ Check you set PIPESHIFT_API_KEY
→ Check your key is valid
→ Email marked "needs_review" in dashboard

---

## File Checklist

Before running, you should have:
- ✅ `app.py` (provided)
- ✅ `requirements.txt` (provided)
- ✅ `client_secret.json` (you download from Google)
- ✅ `PIPESHIFT_API_KEY` set in terminal

After running:
- ✅ `gmail_token.pickle` (auto-created)
- ✅ `incidents.db` (auto-created)

---

## Next: Read Full Docs

For more details:
- `README_GMAIL.md` - Full feature overview
- `GMAIL_SETUP.md` - Detailed setup guide

Enjoy! 🚀
