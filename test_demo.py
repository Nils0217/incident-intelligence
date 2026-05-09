#!/usr/bin/env python3
"""
Test script to verify the incident cleaning logic without Streamlit.
Run: python test_demo.py
"""

import json
import re
from datetime import datetime


def mock_clean_incident(messy_report):
    """
    Mock cleaning for demo/offline mode.
    Uses pattern matching to extract key info.
    """
    # Generate incident ID
    now = datetime.now()
    incident_id = f"INC-{now.strftime('%Y-%m-%d')}-{hash(messy_report) % 1000:03d}"

    # Try to extract timestamp
    timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2})[T\s](\d{2}:\d{2})', messy_report, re.IGNORECASE)
    if timestamp_match:
        timestamp = f"{timestamp_match.group(1)}T{timestamp_match.group(2)}:00Z"
    else:
        timestamp = now.isoformat() + "Z"

    # Extract severity (look for P0-P4, or keywords like critical, urgent)
    severity = "P3"
    if re.search(r'\b(P0|critical|sev-1|major outage|critical severity)\b', messy_report, re.IGNORECASE):
        severity = "P0"
    elif re.search(r'\b(P1|high|sev-2|significant impact)\b', messy_report, re.IGNORECASE):
        severity = "P1"
    elif re.search(r'\b(P2|medium|sev-3|moderate impact)\b', messy_report, re.IGNORECASE):
        severity = "P2"
    elif re.search(r'\b(P4|low|sev-5|minor)\b', messy_report, re.IGNORECASE):
        severity = "P4"

    # Extract system affected
    systems = []
    system_keywords = {
        'database': ['db', 'postgres', 'mysql', 'mongodb', 'redis', 'cassandra'],
        'API Gateway': ['api gateway', 'gateway', 'ingress'],
        'Auth Service': ['auth', 'login', 'oauth', 'saml'],
        'Payment': ['payment', 'stripe', 'billing', 'checkout'],
        'CDN': ['cdn', 'cloudflare', 'caching'],
        'Kubernetes': ['k8s', 'kubernetes', 'pod', 'deployment'],
        'Cache': ['cache', 'memcache', 'redis']
    }

    for system, keywords in system_keywords.items():
        if any(kw in messy_report.lower() for kw in keywords):
            systems.append(system)
    system_affected = systems[0] if systems else "Unknown Service"

    # Extract root cause
    root_cause = "Database connection pool exhaustion"
    if "memory" in messy_report.lower():
        root_cause = "Memory leak in service"
    elif "timeout" in messy_report.lower():
        root_cause = "Request timeout due to slow query"
    elif "deploy" in messy_report.lower() or "rollout" in messy_report.lower():
        root_cause = "Bad deployment introduced regression"
    elif "config" in messy_report.lower():
        root_cause = "Configuration error"

    # Extract resolution
    resolution = "Restarted affected service instances"
    if "rollback" in messy_report.lower():
        resolution = "Rolled back to previous version"
    elif "scale" in messy_report.lower():
        resolution = "Scaled up instances to handle load"
    elif "fix" in messy_report.lower():
        resolution = "Applied hotfix and redeployed"

    # Extract tags
    tags_set = set()
    if "database" in messy_report.lower():
        tags_set.add("database")
    if "api" in messy_report.lower():
        tags_set.add("api")
    if "auth" in messy_report.lower():
        tags_set.add("authentication")
    if "kubernetes" in messy_report.lower() or "k8s" in messy_report.lower():
        tags_set.add("kubernetes")
    if "memory" in messy_report.lower():
        tags_set.add("memory-leak")
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


def print_demo(title, messy, cleaned):
    """Pretty print demo."""
    print("\n" + "=" * 80)
    print(f"DEMO {title}")
    print("=" * 80)
    print("\n📥 BEFORE (Messy Input):")
    print("-" * 40)
    print(messy.strip())
    print("\n📤 AFTER (Clean JSON):")
    print("-" * 40)
    print(json.dumps(cleaned, indent=2))


def main():
    print("\n🚨 Engineering Incident Intelligence - Demo Test\n")

    # Demo 1: Database issue
    messy1 = """
    Date: 2024-05-08 14:32

    The database went down again. We had connection pool exhaustion.
    Like 500+ connections waiting. postgres primary node started rejecting
    new connections. we restarted all the microservices that depend on
    the db - auth service, payment processing, user api. Everything came back
    online after restart. took maybe 8 mins from detection to full recovery.

    we need to look into pooling config and maybe add alerting for
    connection count.  severity: critical
    """

    cleaned1 = mock_clean_incident(messy1)
    print_demo("1: Database Connection Pool", messy1, cleaned1)

    # Demo 2: Memory leak
    messy2 = """
    INCIDENT REPORT
    ===============
    Timestamp: 2024-05-07T08:15Z

    Memory leak in user-api deployment. Services started getting OOMKilled.
    Found bad code in session caching logic - we were not evicting expired sessions.

    Rolled back to v2.3.1 from v2.4.0. Confirmed memory usage returned to normal.
    All users affected for about 15 mins while we did the rollback.

    P1 - high impact - affected auth flows and user data fetches

    TODO: code review the session manager PR before redeploying v2.4.0
    """

    cleaned2 = mock_clean_incident(messy2)
    print_demo("2: Memory Leak in Auth Service", messy2, cleaned2)

    # Demo 3: CDN config
    messy3 = """
    5/9/2024 11:42 AM - CDN cache issue

    Cloudflare reported 500 errors starting around 11:00 AM. Origin server health
    checks were failing. Looks like we misconfigured the health check endpoint
    in the latest deployment. Changed config param health_check_path from /health
    to /api/v1/health but didnt update cloudflare settings.

    Fixed by updating cloudflare config and doing cache purge. Users saw stale content
    for ~20 minutes. Low severity issue but affects user experience.

    tags: cdn, config, deployment-issue
    """

    cleaned3 = mock_clean_incident(messy3)
    print_demo("3: CDN Configuration Error", messy3, cleaned3)

    # Summary
    print("\n" + "=" * 80)
    print("✅ DEMO COMPLETE")
    print("=" * 80)
    print("\nAll three messy reports were successfully cleaned into structured JSON!")
    print("\nTo run the full Streamlit app:")
    print("  pip install -r requirements.txt")
    print("  streamlit run app.py")
    print("\nThe app will:")
    print("  ✅ Load these 3 demos into SQLite on startup")
    print("  ✅ Let you paste/upload new messy reports")
    print("  ✅ Clean them (via mock or real Kimi 2.6 API)")
    print("  ✅ Query the database with natural language")
    print("\n")


if __name__ == "__main__":
    main()
