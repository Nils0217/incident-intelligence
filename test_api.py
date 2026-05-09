#!/usr/bin/env python3
"""
Quick test script to verify Pipeshift API key works
"""

import requests
import os
import json

API_KEY = os.getenv("PIPESHIFT_API_KEY", "")

if not API_KEY:
    print("❌ PIPESHIFT_API_KEY not set!")
    print("Set it with: export PIPESHIFT_API_KEY='sk_...'")
    exit(1)

print(f"🧪 Testing Pipeshift API")
print(f"API Key: {API_KEY[:20]}...")
print()

# Test 1: Simple prompt
print("Test 1: Simple prompt...")
try:
    response = requests.post(
        "https://api.pipeshift.com/api/v0/chat/completions",
        json={
            "model": "moonshotai/Kimi-K2.6",
            "messages": [
                {"role": "user", "content": "Say 'Hello'"}
            ],
            "temperature": 0.3,
            "stream": False
        },
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        timeout=60
    )

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        print(f"✅ SUCCESS!")
        print(f"Response: {content}")
    else:
        print(f"❌ Error {response.status_code}")
        print(f"Response: {response.text[:300]}")

except requests.exceptions.Timeout:
    print("❌ TIMEOUT - API took too long")
except Exception as e:
    print(f"❌ Error: {str(e)}")

print()
print("Test 2: JSON extraction...")
try:
    response = requests.post(
        "https://api.pipeshift.com/api/v0/chat/completions",
        json={
            "model": "moonshotai/Kimi-K2.6",
            "messages": [
                {"role": "user", "content": 'Return only: {"test": "success"}'}
            ],
            "temperature": 0.3,
            "stream": False
        },
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        timeout=60
    )

    if response.status_code == 200:
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        print(f"✅ Got response: {content}")

        # Try to extract JSON
        import re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
            print(f"✅ Successfully parsed JSON: {parsed}")
        else:
            print(f"⚠️ Could not find JSON in response")
    else:
        print(f"❌ Error {response.status_code}: {response.text[:300]}")

except Exception as e:
    print(f"❌ Error: {str(e)}")

print()
print("=" * 60)
print("Test complete!")
print("If both tests passed, your API key works!")
