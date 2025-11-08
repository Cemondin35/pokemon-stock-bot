import os
import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime

WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Railway'e eklenecek ortam değişkeni

URLS = [
    "https://oryx.ie/collections/pokemon-sealed-product",
    "https://gadgetman.ie/339-pokemon-ireland",
    "https://finneganscorner.com/pokemon/",
    "https://toysdirect.ie/collections/pokemon",
    "https://toyful.ie/collections/pokemon",
    "https://eirehobbies.com/collections/pokemon",
    "https://www.tcgireland.com/all-products",
    "https://www.easons.com/5637150827/all/games-and-toys/leading-brands/pokemon",
    "https://murphystoymaster.ie/?s=pokemon&post_type=product&type_aws=true&wpf_filter_cat_2=988&wpf_fbv=1",
    "https://mcgillicuddystoyshop.ie/shop/collectibles",
    "https://toycorner.ie/collections/pokemon-tcg",
    "https://oconnortoys.ie/product-category/pokemon/",
    "https://www.beattys.ie/search?options%5Bprefix%5D=last&q=pokemon",
    "https://totallytoys.ie/collections/pokemon",
    "https://kenblack.ie/search?sort_by=relevance&q=pokemon&type=product&filter.v.availability=1&filter.v.price.gte=&filter.v.price.lte=&filter.p.m.custom.brand=Pokemon",
    "https://www.toytown.ie/search?options%5Bprefix%5D=last&q=pokemon"
]

DATA_FILE = "products.json"

def load_previous_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def send_discord_message(title, link, site, change_type):
    if not WEBHOOK_URL:
        print("WEBHOOK_URL not set. Skipping message.")
        return
    message = {
        "embeds": [
            {
                "title": f"{change_type} Pokémon Product Detected!",
                "description": f"**{title}**\n[{site}]({link})",
                "footer": {"text": f"Detected at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
            }
        ]
    }
    try:
        requests.post(WEBHOOK_URL, json=message, timeout=15)
    except Exception as e:
        print("Error sending Discord message:", e)

def scrape_site(url):
    headers = {"User-Agent": "Mozilla/5.0 (X11; Windows NT 10.0; Win64; x64)"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        products = {}
        for a in soup.find_all("a", href=True):
            name = a.get_text(strip=True)
            href = a["href"]
            if not name:
                continue
            if "pokemon" in name.lower() or "pokemon" in href.lower():
                full_link = href if href.startswith("http") else (url.rstrip("/") + "/" + href.lstrip("/"))
                products[name] = full_link
        return products
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return {}

def main():
    data = load_previous_data()
    while True:
        print(f"Checking for updates... {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        for url in URLS:
            site_name = url.split("/")[2]
            new_products = scrape_site(url)
            old_products = data.get(site_name, {})

            added = {k:v for k,v in new_products.items() if k not in old_products}
            removed = {k:v for k,v in old_products.items() if k not in new_products}

            for name, link in added.items():
                print("🆕 New:", name)
                send_discord_message(name, link, site_name, "🆕 New")

            for name, link in removed.items():
                print(♻️ Removed or out of stock:", name)
                send_discord_message(name, link, site_name, "♻️ Stock Update")

            data[site_name] = new_products

        save_data(data)
        print("Sleeping 15 minutes...\n")
        time.sleep(900)

if __name__ == "__main__":
    main()
