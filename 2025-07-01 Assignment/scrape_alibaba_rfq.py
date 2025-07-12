from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import csv
from datetime import datetime
import os

# === CONFIGURATION ===
CHROMEDRIVER_PATH = r"your_path"
URL = "https://sourcing.alibaba.com/rfq/rfq_search_list.htm?country=AE&recently=Y"
OUTPUT_FILE = "rfq_data.csv"

# === SETUP CHROMEDRIVER ===
if not os.path.exists(CHROMEDRIVER_PATH):
    raise FileNotFoundError(f"ChromeDriver not found at: {CHROMEDRIVER_PATH}")

options = Options()
options.add_argument("--start-maximized")
# options.add_argument("--headless=new")  # Optional for background run
service = Service(CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=options)

# === OPEN PAGE ===
driver.get(URL)

# === WAIT FOR RFQ CARDS ===
try:
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.card-list-item"))
    )
    print("RFQ cards loaded.")
except Exception as e:
    driver.save_screenshot("load_error.png")
    with open("page_dump.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print("Cards not found. Screenshot and page dump saved.")
    driver.quit()
    raise SystemExit("Exiting: Could not find RFQ cards.")

cards = driver.find_elements(By.CSS_SELECTOR, "div.card-list-item")
print(f"🔍 Found {len(cards)} RFQs")

# === CSV SETUP ===
header = [
    "RFQ ID", "Title", "Buyer Name", "Buyer Image", "Inquiry Time", "Quotes Left", "Country",
    "Quantity Required", "Email Confirmed", "Experienced Buyer", "Complete Order via RFQ",
    "Typical Replies", "Interactive User", "Inquiry URL", "Inquiry Date", "Scraping Date"
]
rows = []

# === SCRAPE EACH CARD ===
for i, card in enumerate(cards):
    try:
        rfq_id = card.get_attribute("data-id") or "N/A"

        # Basic fields
        title_el = card.find_element(By.CSS_SELECTOR, "div.rfq-title > a")
        title = title_el.text.strip()
        inquiry_url = title_el.get_attribute("href")

        buyer_name = card.find_element(By.CLASS_NAME, "user-name").text.strip()

        try:
            buyer_img = card.find_element(By.CSS_SELECTOR, "img.user-img").get_attribute("src")
        except:
            buyer_img = ""

        inquiry_time = card.find_element(By.CLASS_NAME, "time-text").text.strip()
        quotes_left = card.find_element(By.CLASS_NAME, "quote-left").text.strip()
        country = card.find_element(By.CLASS_NAME, "country-name").text.strip()

        # Quantity Required from full block
        quantity_block = card.find_element(By.CLASS_NAME, "quantity-text").text.strip()

        # Flags
        full_card_text = card.text
        email_confirmed = "Yes" if "Email Confirmed" in full_card_text else "No"
        experienced_buyer = "Yes" if "Experienced Buyer" in full_card_text else "No"
        complete_order = "Yes" if "Complete Order via RFQ" in full_card_text else "No"
        typical_replies = "Yes" if "Typically replies" in full_card_text else "No"
        interactive_user = "Yes" if "Interactive Buyer" in full_card_text else "No"

        # Dates
        today = datetime.now().strftime("%d-%m-%Y")
        inquiry_date = today
        scrape_date = today

        rows.append([
            rfq_id, title, buyer_name, buyer_img, inquiry_time, quotes_left, country,
            quantity_block, email_confirmed, experienced_buyer, complete_order,
            typical_replies, interactive_user, inquiry_url, inquiry_date, scrape_date
        ])

    except Exception as e:
        print(f"⚠️ Skipped card #{i+1}: {e}")

# === WRITE TO CSV ===
if rows:
    with open(OUTPUT_FILE, "w", newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    print(f" Scraping complete. {len(rows)} records saved to {OUTPUT_FILE}")
else:
    print(" No data was scraped. Check if login or page structure changed.")

# === FINAL SCREENSHOT ===
driver.save_screenshot("final_result.png")
driver.quit()
