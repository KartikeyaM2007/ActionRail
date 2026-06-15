"""
Capture demo screenshots using Selenium + Edge WebDriver.
Performs the full demo workflow: login, preflight, approve, execute,
receipt, writeback, blocked, needs-evidence, evidence pack, replay,
risk monitor, audit log, admin dashboard, and agent integration docs.

Usage:
    python scripts/capture_demo_screenshots.py

Requires: selenium (already in environment), Edge browser, msedgedriver on PATH or auto-managed.
"""
import json
import os
import sys
import time
import urllib.request

# Selenium imports
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://127.0.0.1:8000"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "demo_captures")

# Transaction IDs discovered during the workflow
TXN_APPROVAL = None  # set after preflight
TXN_BLOCKED = None
TXN_EVIDENCE = None


def check_server():
    """Verify the server is running."""
    try:
        resp = urllib.request.urlopen(f"{BASE_URL}/health", timeout=5)
        data = json.loads(resp.read())
        if data.get("status") == "ok":
            print("Server health: OK")
            return True
    except Exception as e:
        print(f"Server not reachable: {e}")
    return False


def create_driver():
    """Create a headless Edge WebDriver."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1280,900")
    options.add_argument("--hide-scrollbars")
    options.add_argument("--force-device-scale-factor=1")

    try:
        driver = webdriver.Edge(options=options)
        driver.set_page_load_timeout(15)
        return driver
    except Exception as e:
        print(f"Failed to create Edge WebDriver: {e}")
        print("Trying with explicit service...")
        try:
            service = Service()
            driver = webdriver.Edge(service=service, options=options)
            driver.set_page_load_timeout(15)
            return driver
        except Exception as e2:
            print(f"Also failed: {e2}")
            return None


def save_screenshot(driver, filename):
    """Save a screenshot and report the result."""
    path = os.path.join(OUTPUT_DIR, filename)
    try:
        # For full page, set window size to page height
        total_height = driver.execute_script("return document.body.scrollHeight")
        viewport_width = 1280
        # Cap height to avoid enormous images
        capture_height = min(total_height + 100, 3000)
        driver.set_window_size(viewport_width, capture_height)
        time.sleep(0.3)  # let layout settle

        driver.save_screenshot(path)
        size = os.path.getsize(path)
        print(f"  OK  {filename} ({size:,} bytes)")
        return True
    except Exception as e:
        print(f"  FAIL {filename}: {e}")
        return False


def login(driver, email="admin@example.local", password="admin123"):
    """Login via the login form."""
    driver.get(f"{BASE_URL}/login")
    time.sleep(0.5)

    try:
        email_field = driver.find_element(By.NAME, "email")
        pass_field = driver.find_element(By.NAME, "password")
        email_field.clear()
        email_field.send_keys(email)
        pass_field.clear()
        pass_field.send_keys(password)

        # Find and click submit
        submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
        submit.click()
        time.sleep(1)

        # Check we landed on dashboard
        if "/dashboard" in driver.current_url or "/login" not in driver.current_url:
            print(f"  Logged in as {email}")
            return True
        else:
            print(f"  Login may have failed, current URL: {driver.current_url}")
            return False
    except Exception as e:
        print(f"  Login error: {e}")
        return False


def create_preflight(idempotency_key, json_file):
    """Create a preflight transaction via the API and return the response."""
    json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), json_file)
    with open(json_path, "r") as f:
        payload = f.read().encode("utf-8")

    req = urllib.request.Request(
        f"{BASE_URL}/actions/preflight",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Idempotency-Key": idempotency_key,
        },
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        txn_id = data.get("transaction_id", "")
        decision = data.get("decision", "")
        risk = data.get("risk", "")
        print(f"  Preflight: txn={txn_id}, decision={decision}, risk={risk}")
        return data
    except Exception as e:
        print(f"  Preflight error: {e}")
        return None


def approve_via_api(txn_id):
    """Approve a transaction via the JSON API."""
    payload = json.dumps({"approver_id": "controller_001", "note": "Demo approval"}).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/approvals/{txn_id}/approve",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        print(f"  Approved: status={data.get('status', '')}")
        return data
    except Exception as e:
        print(f"  Approve error: {e}")
        return None


def execute_via_api(txn_id):
    """Execute a transaction via the JSON API."""
    req = urllib.request.Request(
        f"{BASE_URL}/actions/{txn_id}/execute",
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        print(f"  Executed: status={data.get('status', '')}")
        return data
    except Exception as e:
        print(f"  Execute error: {e}")
        return None


def main():
    global TXN_APPROVAL, TXN_BLOCKED, TXN_EVIDENCE

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not check_server():
        print("ERROR: Server not running. Start with: uvicorn app.main:app --reload")
        sys.exit(1)

    results = {}

    # --- Step 1: Create transactions via API ---
    print("\n=== Creating demo transactions via API ===")

    print("\n1a. Approval-required transaction")
    resp = create_preflight("demo-capture-001", "examples/invoice_approval_required.json")
    if resp:
        TXN_APPROVAL = resp["transaction_id"]
    else:
        print("FATAL: Could not create approval transaction")
        sys.exit(1)

    print("\n1b. Approve transaction via API")
    approve_via_api(TXN_APPROVAL)

    print("\n1c. Execute transaction via API")
    execute_via_api(TXN_APPROVAL)

    print("\n1d. Blocked duplicate transaction")
    resp = create_preflight("demo-capture-002", "examples/invoice_duplicate_blocked.json")
    if resp:
        TXN_BLOCKED = resp["transaction_id"]

    print("\n1e. Missing evidence transaction")
    resp = create_preflight("demo-capture-003", "examples/invoice_missing_evidence.json")
    if resp:
        TXN_EVIDENCE = resp["transaction_id"]

    # --- Step 2: Create WebDriver and capture screenshots ---
    print("\n=== Starting Edge WebDriver ===")
    driver = create_driver()
    if not driver:
        print("FATAL: Could not create WebDriver")
        sys.exit(1)

    try:
        # 00 - Health check (no auth needed)
        print("\n--- 00: Health check ---")
        driver.get(f"{BASE_URL}/health")
        time.sleep(0.5)
        results["00-health-check.png"] = save_screenshot(driver, "00-health-check.png")

        # 02 - Login page (before login)
        print("\n--- 02: Login page ---")
        driver.get(f"{BASE_URL}/login")
        time.sleep(0.5)
        results["02-login-page.png"] = save_screenshot(driver, "02-login-page.png")

        # Login as admin
        print("\n--- Logging in as admin ---")
        login(driver, "admin@example.local", "admin123")

        # 03 - Dashboard with transaction
        print("\n--- 03: Dashboard with transaction ---")
        driver.get(f"{BASE_URL}/dashboard")
        time.sleep(1)
        results["03-dashboard-with-transaction.png"] = save_screenshot(driver, "03-dashboard-with-transaction.png")

        # 04 - Transaction detail (executed transaction)
        if TXN_APPROVAL:
            print("\n--- 04: Transaction detail ---")
            driver.get(f"{BASE_URL}/dashboard/transactions/{TXN_APPROVAL}")
            time.sleep(1)
            results["04-transaction-detail.png"] = save_screenshot(driver, "04-transaction-detail.png")

            # 07 - Signed receipt
            print("\n--- 07: Signed receipt ---")
            driver.get(f"{BASE_URL}/dashboard/transactions/{TXN_APPROVAL}/receipt")
            time.sleep(1)
            results["07-signed-receipt.png"] = save_screenshot(driver, "07-signed-receipt.png")

            # 08 - Accounting writeback (create it first via dashboard POST)
            print("\n--- 08: Accounting writeback ---")
            driver.get(f"{BASE_URL}/dashboard/transactions/{TXN_APPROVAL}/writeback/accounting-sandbox")
            time.sleep(1)
            # If this is a POST-then-redirect, we may need to POST first
            # Try clicking the create button if it exists
            try:
                create_btn = driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], form button")
                if create_btn:
                    create_btn[0].click()
                    time.sleep(1)
            except:
                pass
            results["08-accounting-writeback.png"] = save_screenshot(driver, "08-accounting-writeback.png")

            # 11 - Evidence pack (capture the detail page with the download button visible)
            print("\n--- 11: Evidence pack download ---")
            driver.get(f"{BASE_URL}/dashboard/transactions/{TXN_APPROVAL}")
            time.sleep(1)
            results["11-evidence-pack-download.png"] = save_screenshot(driver, "11-evidence-pack-download.png")

            # 12 - Policy replay
            print("\n--- 12: Policy replay ---")
            driver.get(f"{BASE_URL}/dashboard/transactions/{TXN_APPROVAL}/replay")
            time.sleep(1)
            results["12-policy-replay.png"] = save_screenshot(driver, "12-policy-replay.png")

        # 09 - Blocked duplicate
        if TXN_BLOCKED:
            print("\n--- 09: Blocked duplicate ---")
            driver.get(f"{BASE_URL}/dashboard/transactions/{TXN_BLOCKED}")
            time.sleep(1)
            results["09-blocked-duplicate.png"] = save_screenshot(driver, "09-blocked-duplicate.png")

        # 10 - Needs evidence
        if TXN_EVIDENCE:
            print("\n--- 10: Needs evidence ---")
            driver.get(f"{BASE_URL}/dashboard/transactions/{TXN_EVIDENCE}")
            time.sleep(1)
            results["10-needs-evidence.png"] = save_screenshot(driver, "10-needs-evidence.png")

        # 13 - Risk monitor
        print("\n--- 13: Risk monitor ---")
        driver.get(f"{BASE_URL}/dashboard/risk")
        time.sleep(1)
        results["13-risk-monitor.png"] = save_screenshot(driver, "13-risk-monitor.png")

        # 14 - Audit log
        print("\n--- 14: Audit log ---")
        driver.get(f"{BASE_URL}/dashboard/audit")
        time.sleep(1)
        results["14-audit-log.png"] = save_screenshot(driver, "14-audit-log.png")

        # 15 - Admin dashboard
        print("\n--- 15: Admin dashboard ---")
        driver.get(f"{BASE_URL}/dashboard/admin")
        time.sleep(1)
        results["15-admin-dashboard.png"] = save_screenshot(driver, "15-admin-dashboard.png")

    finally:
        driver.quit()
        print("\nWebDriver closed.")

    # --- Step 3: Handle screenshots that can't be browser-captured ---

    # 01 - Preflight response: This is a terminal/API response, not a web page.
    # Mark as pending terminal capture.
    results["01-preflight-response.png"] = False
    print("\n01-preflight-response.png: PENDING (terminal/API output, not a web page)")

    # 05 - Approved transaction: We approved+executed in one pass via API.
    # The transaction went straight to executed. Mark pending.
    results["05-approved-transaction.png"] = False
    print("05-approved-transaction.png: PENDING (approval was done via API, not dashboard)")

    # 06 - Executed transaction: Same as 04 (transaction detail shows executed state)
    # Copy the 04 screenshot as 06 since the transaction IS executed
    src = os.path.join(OUTPUT_DIR, "04-transaction-detail.png")
    dst = os.path.join(OUTPUT_DIR, "06-executed-transaction.png")
    if os.path.exists(src):
        import shutil
        shutil.copy2(src, dst)
        results["06-executed-transaction.png"] = True
        print(f"06-executed-transaction.png: Copied from 04 (same txn in executed state)")
    else:
        results["06-executed-transaction.png"] = False

    # 16 - Agent integration docs: These are local files, not web pages.
    # We'll capture a listing of the files as proof they exist.
    results["16-agent-integration-docs.png"] = False
    print("16-agent-integration-docs.png: PENDING (local files, not web pages)")

    # --- Summary ---
    print("\n" + "=" * 60)
    print("SCREENSHOT CAPTURE SUMMARY")
    print("=" * 60)

    captured = []
    pending = []
    for filename in sorted(results.keys()):
        status = "Captured" if results[filename] else "Pending"
        path = os.path.join(OUTPUT_DIR, filename)
        exists = os.path.exists(path)
        size = os.path.getsize(path) if exists else 0
        marker = "✓" if exists else "✗"
        print(f"  {marker} {filename}: {status}" + (f" ({size:,} bytes)" if exists else ""))
        if exists:
            captured.append(filename)
        else:
            pending.append(filename)

    print(f"\nCaptured: {len(captured)}/17")
    print(f"Pending:  {len(pending)}/17")
    if pending:
        print(f"Pending files: {', '.join(pending)}")

    # Print transaction IDs for reference
    print(f"\nTransaction IDs:")
    print(f"  Approval: {TXN_APPROVAL}")
    print(f"  Blocked:  {TXN_BLOCKED}")
    print(f"  Evidence: {TXN_EVIDENCE}")


if __name__ == "__main__":
    main()
