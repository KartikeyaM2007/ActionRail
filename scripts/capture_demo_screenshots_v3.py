"""Capture approved transaction and agent integration docs screenshots."""
import os, time, json
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By

BASE_URL = "http://127.0.0.1:8000"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "demo_captures")
TXN_APPROVED = "txn_a4cf574bdc36"

def main():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1280,900")
    options.add_argument("--hide-scrollbars")
    options.add_argument("--force-device-scale-factor=1")
    driver = webdriver.Edge(options=options)
    driver.set_page_load_timeout(15)

    try:
        # Login
        driver.get(f"{BASE_URL}/login")
        time.sleep(0.5)
        driver.find_element(By.NAME, "email").send_keys("admin@example.local")
        driver.find_element(By.NAME, "password").send_keys("admin123")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)
        print(f"Logged in, URL: {driver.current_url}")

        # 05 - Approved transaction (not yet executed)
        driver.get(f"{BASE_URL}/dashboard/transactions/{TXN_APPROVED}")
        time.sleep(1.5)
        total_height = driver.execute_script("return document.body.scrollHeight")
        driver.set_window_size(1280, min(total_height + 100, 4000))
        time.sleep(0.5)
        path = os.path.join(OUTPUT_DIR, "05-approved-transaction.png")
        driver.save_screenshot(path)
        size = os.path.getsize(path)
        print(f"05-approved-transaction.png: {size:,} bytes")

        # 16 - Agent integration docs (render the AGENT_INTEGRATION.md as a local page)
        # Since these are local files, we'll capture the examples/ directory listing
        # and the agent_client.py file content as proof they exist
        # Actually let's use a file:// URL to display the markdown
        agent_docs_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "docs", "AGENT_INTEGRATION.md"
        )
        driver.get(f"file:///{agent_docs_path.replace(os.sep, '/')}")
        time.sleep(1)
        total_height = driver.execute_script("return document.body.scrollHeight")
        driver.set_window_size(1280, min(total_height + 100, 4000))
        time.sleep(0.5)
        path = os.path.join(OUTPUT_DIR, "16-agent-integration-docs.png")
        driver.save_screenshot(path)
        size = os.path.getsize(path)
        print(f"16-agent-integration-docs.png: {size:,} bytes")

    finally:
        driver.quit()

    # Clean temp files
    for f in ["temp_approve.json", "temp_approve_body.json"]:
        fp = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), f)
        if os.path.exists(fp):
            os.remove(fp)
            print(f"Cleaned up {f}")

    # Final listing
    print(f"\nAll files in {OUTPUT_DIR}:")
    for f in sorted(os.listdir(OUTPUT_DIR)):
        size = os.path.getsize(os.path.join(OUTPUT_DIR, f))
        print(f"  {f}: {size:,} bytes")

if __name__ == "__main__":
    main()
