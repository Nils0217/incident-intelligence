# Quick Start Guide (2 minutes to working demo)

## Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

## Step 2: Run the App
```bash
streamlit run app.py
```

Your browser will open to `http://localhost:8501`

## Step 3: View Demo

**You now have 3 pre-loaded sample incidents:**

1. Go to **"📊 Incident Database"** tab
2. See 3 incidents with full details
3. Try filtering by severity (P0, P1) or system

## Step 4: Clean a Report (Without API Key)

In **"📝 Clean Reports"** tab:

1. Click the **Paste text** radio button (if not selected)
2. Paste this messy report:
```
We had an outage today around 3pm. The kubernetes cluster ran
out of memory. Some pods were getting evicted. We scaled up the
cluster from 5 to 8 nodes. Took about 12 mins to stabilize.
This is a P0 issue - all services were impacted.
```

3. Click **"🔄 Clean & Structure"**
4. See before/after side-by-side
5. Click **"💾 Save to Database"**
6. Go to **"📊 Incident Database"** - your incident appears!

## Step 5: Query the Database

Go to **"❓ Query"** tab:

Try these searches:
- `P0` → shows critical incidents
- `database` → shows database-related incidents
- `kubernetes` → shows K8s incidents
- `memory` → shows memory-related issues

## That's It! 🎉

You now have:
- ✅ 3 demo incidents loaded
- ✅ Ability to clean new messy reports
- ✅ SQLite database storing everything
- ✅ Query interface working

## To Use Real Kimi 2.6 API

If you get a Pipeshift API key, set it:

```bash
export PIPESHIFT_API_KEY="sk-xxx..."
streamlit run app.py
```

App will automatically switch to using real Kimi 2.6 for smarter cleaning.

## Helpful Tips

- **Reset database:** Delete `incidents.db` and restart
- **Sample data reloads:** On first run only
- **The app detects API key automatically** - you don't need to restart
- **All data is local** - nothing leaves your machine unless you provide an API key

---

Enjoy! 🚨
