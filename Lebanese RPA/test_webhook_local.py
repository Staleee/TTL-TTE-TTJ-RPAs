"""
Test the Lebanon Visa RPA locally.
Uses /health and /generate (PDF only, no external API).
"""
import os
import json
import requests
from pathlib import Path

with open("visa_applicant_data.json", "r", encoding="utf-8") as f:
    application_data = json.load(f)

# Use PORT 5001 so Lebanon doesn't conflict with Egypt (5000)
BASE_URL = os.environ.get("LEBANON_RPA_URL", "http://localhost:5001")
# Default 5001 to avoid conflict with Egypt (5000). Or: python app.py (uses PORT env or 5000)

print("=" * 60)
print("TESTING LEBANON VISA RPA LOCALLY")
print("=" * 60)
print("\n1. Start the server: python app.py")
print("2. Then run this script.")
print("=" * 60)

# Test 1: Health
print("\n[Test 1] Health check...")
try:
    r = requests.get(f"{BASE_URL}/health", timeout=5)
    if r.status_code == 200:
        print("[OK] Health check passed:", r.json())
    else:
        print("[FAIL] Health:", r.status_code)
except Exception as e:
    print("[FAIL] Cannot reach server:", e)
    print("  Run 'python app.py' in this folder first.")
    exit(1)

# Test 2: Generate PDF (no external API)
print("\n[Test 2] Generate PDF...")
try:
    r = requests.post(
        f"{BASE_URL}/generate",
        json=application_data,
        timeout=60,
    )
    if r.status_code == 200:
        out = Path("test_lebanon_visa_output.pdf")
        out.write_bytes(r.content)
        print("[OK] PDF saved:", out, "({:.1f} KB)".format(len(r.content) / 1024))
    else:
        print("[FAIL]", r.status_code, r.text[:200])
except Exception as e:
    print("[FAIL]", e)

print("\n" + "=" * 60)
print("DONE")
print("=" * 60)
