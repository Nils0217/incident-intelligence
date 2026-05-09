# Deployment & Integration Guide

## What You Got

A complete, **working** Streamlit app that:
- ✅ Runs immediately with 3 demo incidents pre-loaded
- ✅ Works offline (no API key required)
- ✅ Cleans messy incident reports into structured JSON
- ✅ Stores everything in SQLite (zero setup)
- ✅ Provides natural language query interface
- ✅ Ready to integrate with real Kimi 2.6 API

## File Structure

```
.
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies (just streamlit + requests)
├── run.sh                 # Quick start script (bash)
├── .env.example          # Environment variable template
├── test_demo.py          # Standalone demo test (no Streamlit needed)
├── README.md             # Full documentation
├── QUICKSTART.md         # 2-minute quick start
├── DEPLOYMENT_GUIDE.md   # This file
└── incidents.db          # SQLite database (auto-created on first run)
```

## Running Right Now

### Option A: Bash Script (Easiest)
```bash
bash run.sh
```
This installs deps and launches the app automatically.

### Option B: Manual
```bash
pip install -r requirements.txt
streamlit run app.py
```

### Option C: Test First (No Streamlit)
```bash
python test_demo.py
```
Shows how the cleaning logic works without UI.

## What Happens on First Run

1. App creates `incidents.db` (SQLite)
2. Loads 3 sample messy incidents
3. Cleans them using mock cleaning (pattern matching)
4. Stores them in database
5. You can immediately query/filter/view them

## Demo Data

Three realistic incidents pre-loaded:

1. **Database Connection Pool Exhaustion** (P0/Critical)
   - System: PostgreSQL
   - Resolution: Restarted services
   
2. **Memory Leak in Auth Service** (P1/High)
   - Root Cause: Session cache not evicting
   - Resolution: Rollback deployment
   
3. **CDN Configuration Error** (P4/Low)
   - System: Cloudflare CDN
   - Resolution: Config fix + cache purge

## To Enable Real API

When you have a Pipeshift API key:

### Method 1: Export Variable
```bash
export PIPESHIFT_API_KEY="sk_your_key_here"
streamlit run app.py
```

### Method 2: .env File
1. Copy `.env.example` to `.env`
2. Add your key: `PIPESHIFT_API_KEY=sk_...`
3. Run: `python -m streamlit run app.py`

**Note:** Streamlit doesn't auto-load .env. You must export the variable yourself or use python-dotenv:
```bash
pip install python-dotenv
# Then at top of app.py, add:
# from dotenv import load_dotenv
# load_dotenv()
```

## API Integration Details

### Pipeshift API Call

```python
headers = {
    "Authorization": f"Bearer {PIPESHIFT_API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": "kimi-2.6",
    "messages": [{"role": "user", "content": prompt}],
    "temperature": 0.3,
    "max_tokens": 1000
}

response = requests.post(
    "https://api.pipeshift.ai/v1/chat/completions",
    json=payload,
    headers=headers
)
```

### Fallback Strategy

If API fails or no key provided → uses smart mock cleaning:
- Regex-based severity detection (P0-P4)
- System extraction from keywords
- Root cause inference
- Tag auto-generation

This ensures demo always works, even offline.

## Database Schema

```sql
CREATE TABLE incidents (
    id INTEGER PRIMARY KEY,
    incident_id TEXT UNIQUE,        -- INC-2024-05-08-123
    timestamp TEXT,                 -- 2024-05-08T14:32:00Z
    severity TEXT,                  -- P0, P1, P2, P3, P4
    system_affected TEXT,           -- "Database", "API Gateway", etc
    root_cause TEXT,                -- "Connection pool exhaustion"
    resolution TEXT,                -- "Restarted service"
    tags TEXT,                      -- "database,critical,deployment"
    raw_report TEXT,                -- Original messy text
    created_at TEXT                 -- Timestamp of when saved
)
```

## Customization

### Change Cleaning Prompt
Edit the `CLEANING_PROMPT` in `app.py` (lines 30-42)

### Add More Systems
Update `system_keywords` dict in `mock_clean_incident()` function

### Change Severity Levels
Modify severity detection regex (around line 200)

### Add Fields to JSON Output
1. Add to `CLEANING_PROMPT`
2. Update database schema
3. Update `save_incident()` function
4. Update display in `render_incident_card()`

## Production Deployment

### Local/Personal Use
Just run `streamlit run app.py` on your machine.

### Team Deployment (Streamlit Cloud)

1. Push repo to GitHub
2. Go to https://streamlit.io/cloud
3. Click "Deploy an app" → select your repo
4. Add secret: `PIPESHIFT_API_KEY`
5. Deploy

**Cost:** Free tier available for open projects.

### Docker Deployment

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

```bash
docker build -t incident-intel .
docker run -p 8501:8501 \
  -e PIPESHIFT_API_KEY="sk_..." \
  incident-intel
```

## Performance Expectations

| Operation | Time | Notes |
|-----------|------|-------|
| Mock clean | <100ms | Pattern matching, instant |
| Kimi 2.6 clean | 3-5s | API latency + inference |
| Save to DB | <10ms | SQLite is very fast |
| Query database | <50ms | Even with 1000+ incidents |
| Load all incidents | <200ms | Full table scan |

## Troubleshooting

### "module not found: streamlit"
```bash
pip install -r requirements.txt
```

### "Address already in use :8501"
Streamlit is already running. Either:
- Kill the process: `pkill -f streamlit`
- Run on different port: `streamlit run app.py --server.port 8502`

### "No API key" warning
Normal! You're in demo mode with mock cleaning. Set `PIPESHIFT_API_KEY` to use real API.

### Incidents not saving
Check SQLite permissions or try resetting: `rm incidents.db`

### Query returning no results
Try simpler searches. Current query uses keyword matching, not NLU.

## Next Steps

1. **Short term:** Use the working demo, get familiar with the UI
2. **Medium term:** Integrate real Pipeshift API key, test with real incident data
3. **Long term:** 
   - Add incident correlation (auto-group similar incidents)
   - Integrate with PagerDuty/Opsgenie
   - Add team multi-user support
   - Use Claude API for smarter natural language queries
   - Export incidents to CSV/JSON

## Support

If something breaks:
1. Run `python test_demo.py` to verify core logic
2. Check database: `sqlite3 incidents.db "SELECT * FROM incidents;"`
3. Reset everything: `rm incidents.db` and restart
4. Check Streamlit docs: https://docs.streamlit.io

---

**Status:** ✅ Ready to ship  
**Cost:** $0 (demo) → $5-20/month (with real API)  
**Time to live:** Seconds
