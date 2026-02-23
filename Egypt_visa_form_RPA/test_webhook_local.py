"""
Test the webhook locally before deploying to Railway
"""

import requests
import json
from pathlib import Path

# Load sample application data
with open('data/sample_application.json', 'r') as f:
    application_data = json.load(f)

print("="*80)
print("TESTING WEBHOOK LOCALLY")
print("="*80)
print("\n1. Start the Flask server first:")
print("   python app.py")
print("\n2. Then run this test script")
print("="*80)

# Test endpoints
BASE_URL = "http://localhost:5000"

# Test 1: Health check
print("\n[Test 1] Health Check...")
try:
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    if response.status_code == 200:
        print("[OK] Health check passed")
        print(f"  Response: {response.json()}")
    else:
        print(f"[FAIL] Health check failed: {response.status_code}")
except Exception as e:
    print(f"[FAIL] Could not connect to server: {e}")
    print("  Make sure to run 'python app.py' in another terminal first!")
    exit(1)

# Test 2: API documentation
print("\n[Test 2] API Documentation...")
try:
    response = requests.get(f"{BASE_URL}/", timeout=5)
    if response.status_code == 200:
        print("[OK] API docs accessible")
        docs = response.json()
        print(f"  Service: {docs['service']}")
        print(f"  Version: {docs['version']}")
    else:
        print(f"[FAIL] API docs failed: {response.status_code}")
except Exception as e:
    print(f"[FAIL] Error: {e}")

# Test 3: Generate PDF
print("\n[Test 3] Generate PDF (this will take ~40 seconds)...")
try:
    print("  Sending application data...")
    response = requests.post(
        f"{BASE_URL}/generate-visa-pdf",
        json=application_data,
        timeout=120
    )
    
    if response.status_code == 200:
        # Save PDF
        output_path = Path('test_webhook_output.pdf')
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        file_size = output_path.stat().st_size / 1024
        print(f"[OK] PDF generated successfully!")
        print(f"  Saved to: {output_path}")
        print(f"  Size: {file_size:.1f} KB")
    else:
        error = response.json()
        print(f"[FAIL] PDF generation failed: {response.status_code}")
        print(f"  Error: {error}")
        
except Exception as e:
    print(f"[FAIL] Error: {e}")

print("\n" + "="*80)
print("TESTING COMPLETE")
print("="*80)
print("\nIf all tests passed, you're ready to deploy to Railway!")
print("See RAILWAY_DEPLOYMENT.md for deployment instructions.")
print("="*80)

