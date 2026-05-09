# 🚨 Engineering Incident Intelligence

A Streamlit app that cleans messy incident reports, structures them into JSON, stores them in SQLite, and provides natural language query interface.

## Features

✅ **Demo-ready** - 3 built-in sample messy incidents (works immediately)  
✅ **Text + File Upload** - Paste text or upload .txt/.md/.log files  
✅ **Before/After View** - Side-by-side comparison of messy vs. clean data  
✅ **Kimi 2.6 Integration** - Via Pipeshift API for intelligent cleaning  
✅ **Offline Mode** - Works without API key using smart mock cleaning  
✅ **SQLite Storage** - Zero-config local database  
✅ **Query Interface** - Natural language search (P0 incidents, system filters, tags)  
✅ **Zero cost** - All free components  

## Quick Start

### 1. Install

```bash
pip install -r requirements.txt
```

### 2. Run (Demo Mode)

```bash
streamlit run app.py
```

This launches the app in **demo mode** with 3 sample incidents pre-loaded. You can immediately:
- View the sample incidents in the database
- Clean new reports using smart mock cleaning
- Query the database

### 3. (Optional) Enable Real Kimi 2.6 API

If you have a Pipeshift API key:

```bash
export PIPESHIFT_API_KEY="your-key-here"
streamlit run app.py
```

The app will automatically use Kimi 2.6 instead of mock cleaning.

## How It Works

### Tab 1: Clean Reports
1. **Paste** messy text or **Upload** a file
2. Click "Clean & Structure"
3. See before/after comparison
4. Click "Save to Database"

### Tab 2: Incident Database
- View all cleaned incidents
- Filter by severity (P0-P4) or system
- See incident details, root causes, resolutions

### Tab 3: Query
- Natural language search
- Examples: "show P1 incidents", "what database errors?", "recent incidents"

## Output Format

All incidents are normalized to this JSON structure:

```json
{
  "incident_id": "INC-2024-05-08-123",
  "timestamp": "2024-05-08T14:32:00Z",
  "severity": "P0",
  "system_affected": "Database",
  "root_cause": "Connection pool exhaustion",
  "resolution": "Restarted service",
  "tags": "database,critical,deployment"
}
```

## Tech Stack

| Component | Technology | Cost |
|-----------|-----------|------|
| Frontend | Streamlit | Free |
| LLM | Kimi 2.6 (Pipeshift) | Hackathon credits |
| Storage | SQLite | Free |
| Language | Python 3.9+ | Free |

## Demo Data

3 realistic messy incident reports are loaded on first run:
1. **Database connection pool exhaustion** - P0 - Detection to recovery in 8 mins
2. **Memory leak in deployment** - P1 - User API session caching bug
3. **CDN configuration error** - Low severity - Misconfigured health check endpoint

## Files

- `app.py` - Main Streamlit application
- `requirements.txt` - Python dependencies
- `incidents.db` - SQLite database (created automatically)
- `README.md` - This file

## Environment Variables

- `PIPESHIFT_API_KEY` - (Optional) Your Pipeshift API key for Kimi 2.6

If not set, app runs in demo mode with mock cleaning.

## Troubleshooting

**"Module not found" errors**
```bash
pip install -r requirements.txt
```

**Streamlit not starting**
```bash
python -m streamlit run app.py
```

**Want to reset incidents?**
```bash
rm incidents.db
streamlit run app.py
```

## Next Steps

- Enhance query with actual NLU (could use Claude via Anthropic API)
- Add export to CSV/JSON
- Multi-user support with user tagging
- Incident correlation and auto-grouping
- Integration with real incident management tools (PagerDuty, Opsgenie)

---

**Built for speed.** Ready to ship. 🚀
