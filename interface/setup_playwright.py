"""import subprocess
import sys

# One-time setup for playwright (runs 'playwright install' in terminal)
subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
subprocess.run(["playwright", "install"], check=True)
subprocess.run(["playwright", "install-deps"], check=True)"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://bofip.impots.gouv.fr/bofip/1380-PGP.html/identifiant%3DBOI-TVA-LIQ-10-20250514", timeout=60000)
    page.wait_for_load_state("networkidle") # Wait for JS content to load
    content = page.content()
    browser.close()

#print(content)
soup_content = BeautifulSoup(content, 'html.parser')
actual_content = soup_content.find(class_ = "field--name-body")
if actual_content:
    clean_text = actual_content.get_text(separator="\n", strip=True)
    print(clean_text)


