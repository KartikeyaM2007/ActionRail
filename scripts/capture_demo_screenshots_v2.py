"""
Capture remaining demo screenshots with session-safe re-login.
"""
import json
import os
import sys
import time
import urllib.request

from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By

BASE_URL = "http://127.0.0.1:8000"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "demo_captures")

TXN_APPROVAL = "txn_4aae6eab2e0f"
TXN_BLOCKED = "txn_defe70a23026"
TXN_EVIDENCE = "txn_790f40f13554"


def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1280,900")
    options.add_argument("--hide-scrollbars")
    options.add_argument("--force-device-scale-factor=1")
    driver = webdriver.Edge(options=options)
    driver.set_page_load_timeout(15)
    return driver


def save_screenshot(driver, filename, max_height=4000):
    path = os.path.join(OUTPUT_DIR, filename)
    total_height = driver.execute_script("return document.body.scrollHeight")
    capture_height = min(total_height + 100, max_height)
    driver.set_window_size(1280, capture_height)
    time.sleep(0.5)
    driver.save_screenshot(path)
    size = os.path.getsize(path)
    print(f"  OK  {filename} ({size:,} bytes)")
    return size


def login(driver, email="admin@example.local", password="admin123"):
    """Login, handling the case where we might already be logged in."""
    driver.get(f"{BASE_URL}/login")
    time.sleep(0.5)

    # Check if we're already on dashboard (already logged in)
    if "/dashboard" in driver.current_url:
        # Logout first to start fresh
        driver.get(f"{BASE_URL}/logout")
        time.sleep(0.5)
        driver.get(f"{BASE_URL}/login")
        time.sleep(0.5)

    # Now we should be on the login page
    try:
        email_field = driver.find_element(By.NAME, "email")
        pass_field = driver.find_element(By.NAME, "password")
        email_field.clear()
        email_field.send_keys(email)
        pass_field.clear()
        pass_field.send_keys(password)
        submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
        submit.click()
        time.sleep(1)
        if "/dashboard" in driver.current_url:
            print(f"  Logged in as {email}")
            return True
        print(f"  Login issue, URL: {driver.current_url}")
        return False
    except Exception as e:
        print(f"  Login error: {e}")
        # Maybe we're already logged in somehow
        return "/dashboard" in driver.current_url


def is_login_page(driver):
    try:
        return "/login" in driver.current_url
    except:
        return False


def capture_page(driver, url, filename):
    """Navigate to URL and capture, checking for login redirect."""
    print(f"\n--- {filename} ---")
    driver.get(url)
    time.sleep(1.5)

    if is_login_page(driver):
        print(f"  Redirected to login. Re-authenticating...")
        login(driver)
        driver.get(url)
        time.sleep(1.5)
        if is_login_page(driver):
            print(f"  FAIL: Still on login page")
            return False

    return save_screenshot(driver, filename)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    driver = create_driver()
    results = {}

    try:
        # Login once
        login(driver)

        # Capture blocked duplicate
        results["09-blocked-duplicate.png"] = capture_page(
            driver, f"{BASE_URL}/dashboard/transactions/{TXN_BLOCKED}", "09-blocked-duplicate.png"
        )

        # Capture needs evidence
        results["10-needs-evidence.png"] = capture_page(
            driver, f"{BASE_URL}/dashboard/transactions/{TXN_EVIDENCE}", "10-needs-evidence.png"
        )

        # Capture evidence pack page (transaction detail with download button visible)
        results["11-evidence-pack-download.png"] = capture_page(
            driver, f"{BASE_URL}/dashboard/transactions/{TXN_APPROVAL}", "11-evidence-pack-download.png"
        )

        # Capture policy replay
        results["12-policy-replay.png"] = capture_page(
            driver, f"{BASE_URL}/dashboard/transactions/{TXN_APPROVAL}/replay", "12-policy-replay.png"
        )

        # Capture risk monitor
        results["13-risk-monitor.png"] = capture_page(
            driver, f"{BASE_URL}/dashboard/risk", "13-risk-monitor.png"
        )

        # Capture audit log
        results["14-audit-log.png"] = capture_page(
            driver, f"{BASE_URL}/dashboard/audit", "14-audit-log.png"
        )

        # Capture admin dashboard
        results["15-admin-dashboard.png"] = capture_page(
            driver, f"{BASE_URL}/dashboard/admin", "15-admin-dashboard.png"
        )

        # Handle accounting writeback
        print("\n--- 08: Accounting writeback ---")
        driver.get(f"{BASE_URL}/dashboard/transactions/{TXN_APPROVAL}")
        time.sleep(1)

        if is_login_page(driver):
            login(driver)
            driver.get(f"{BASE_URL}/dashboard/transactions/{TXN_APPROVAL}")
            time.sleep(1)

        # Find and click writeback link/button
        try:
            links = driver.find_elements(By.TAG_NAME, "a")
            for link in links:
                href = link.get_attribute("href") or ""
                text = link.text.upper()
                if "ACCOUNTING" in text or "WRITEBACK" in text:
                    print(f"  Found link: {text} -> {href}")
                    link.click()
                    time.sleep(1.5)
                    break

            # Check if we're on a writeback page or need to submit a form
            if "writeback" in driver.current_url.lower():
                # Try submitting any form
                forms = driver.find_elements(By.TAG_NAME, "form")
                for form in forms:
                    buttons = form.find_elements(By.CSS_SELECTOR, "button[type='submit']")
                    if buttons:
                        buttons[0].click()
                        time.sleep(1)
                        break

                if not is_login_page(driver):
                    results["08-accounting-writeback.png"] = save_screenshot(driver, "08-accounting-writeback.png")
                else:
                    print("  Redirected to login after form submission")
                    login(driver)
                    driver.get(f"{BASE_URL}/dashboard/transactions/{TXN_APPROVAL}/writeback/accounting-sandbox")
                    time.sleep(1)
                    results["08-accounting-writeback.png"] = save_screenshot(driver, "08-accounting-writeback.png")
            else:
                # Maybe the button uses a form POST on the detail page
                buttons = driver.find_elements(By.TAG_NAME, "button")
                for btn in buttons:
                    if "ACCOUNTING" in btn.text.upper() or "WRITEBACK" in btn.text.upper():
                        btn.click()
                        time.sleep(1.5)
                        break
                results["08-accounting-writeback.png"] = save_screenshot(driver, "08-accounting-writeback.png")

        except Exception as e:
            print(f"  Writeback error: {e}")
            results["08-accounting-writeback.png"] = False

    finally:
        driver.quit()

    # Final summary
    print("\n" + "=" * 60)
    print("RE-CAPTURE SUMMARY")
    print("=" * 60)
    for fn in sorted(results.keys()):
        path = os.path.join(OUTPUT_DIR, fn)
        exists = os.path.exists(path)
        size = os.path.getsize(path) if exists else 0
        is_real = exists and size > 40000  # login page is ~36873 bytes
        marker = "✓" if is_real else ("⚠" if exists else "✗")
        print(f"  {marker} {fn}: ({size:,} bytes)")

    # Final file listing
    print(f"\nAll files in {OUTPUT_DIR}:")
    for f in sorted(os.listdir(OUTPUT_DIR)):
        size = os.path.getsize(os.path.join(OUTPUT_DIR, f))
        print(f"  {f}: {size:,} bytes")


if __name__ == "__main__":
    main()
