#!/usr/bin/env python3
"""
Panix Waitlist — Airtable Integration

To set up:
1. Create free Airtable account at airtable.com
2. Get API key: https://airtable.com/account (under "API")
3. Get Personal Access Token: https://airtable.com/create/tokens (needs data.records:read/write scope)
4. Create a base named "Panix Waitlist" with these fields:
   - Email (email)
   - Timestamp (date)
   - Source (single line text) — "website" or "instagram"
   - Status (single select) — "new", "contacted", "converted"
5. Replace AIRTABLE_API_KEY, AIRTABLE_PAT, BASE_ID below

Usage:
    python3 airtable_integration.py "test@email.com" --source website
"""
import os, sys, json, time, urllib.request

# ═══ CONFIG — Fill these in ═══
AIRTABLE_API_KEY = "YOUR_API_KEY"           # From https://airtable.com/account
AIRTABLE_PAT = "YOUR_PAT"                   # Personal Access Token
BASE_ID = "appXXXXXXXXXXXXXX"              # From your base URL: airtable.com/YOUR_BASE_ID
TABLE_NAME = "Waitlist"                    # Table name in your base
# ═══════════════════════════════════════

BASE_URL = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_PAT}",
    "Content-Type": "application/json"
}

def add_waitlist_email(email: str, source: str = "website", status: str = "new") -> bool:
    """Add an email to the Panix waitlist in Airtable."""
    if AIRTABLE_API_KEY == "YOUR_API_KEY":
        print("❌ Airtable not configured — set AIRTABLE_API_KEY, AIRTABLE_PAT, and BASE_ID above")
        return False

    payload = {
        "records": [{
            "fields": {
                "Email": email,
                "Timestamp": time.strftime("%Y-%m-%d"),
                "Source": source,
                "Status": status,
            }
        }]
    }

    req = urllib.request.Request(
        BASE_URL,
        data=json.dumps(payload).encode(),
        headers=HEADERS,
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            created = len(data.get("records", []))
            print(f"✅ Added {email} to Airtable ({created} record created)")
            return True
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"❌ Airtable error {e.code}: {error_body[:200]}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def get_waitlist_count() -> int:
    """Get total waitlist records from Airtable."""
    if AIRTABLE_API_KEY == "YOUR_API_KEY":
        return -1

    req = urllib.request.Request(
        BASE_URL + "?maxRecords=100",
        headers=HEADERS
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return len(data.get("records", []))
    except Exception as e:
        print(f"❌ Error fetching count: {e}")
        return -1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 airtable_integration.py email@example.com [--source website|instagram]")
        sys.exit(1)

    email = sys.argv[1]
    source = "instagram" if "--source" in sys.argv and "instagram" in sys.argv else "website"
    add_waitlist_email(email, source=source)
