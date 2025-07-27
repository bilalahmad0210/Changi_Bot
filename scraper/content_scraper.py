import json
import requests
import time
import logging
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from tqdm import tqdm

# --- Settings ---
INPUT_LINKS_FILE = "data/all_discovered_links.json"
OUTPUT_DATA_FILE = "data/changi_jewel_cleaned.json"
REQUEST_DELAY = 1.5  # seconds
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Utilities ---
def is_valid_english_url(url):
    return (
        '/en/' in url and                    # Must contain English path
        not any(x in url for x in ['/zh/', '/cn/', '/jp/', '/ko/']) and
        not url.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png', '.gif', '.svg', '.zip')) and
        not 'mailto:' in url
    )

def clean_html_text(html):
    soup = BeautifulSoup(html, 'html.parser')

    # Remove unwanted tags
    for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
        tag.decompose()

    # Get clean text
    text = soup.get_text(separator=' ', strip=True)
    return text if len(text) > 50 else ""

def fetch_page_text(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return clean_html_text(response.text)
    except Exception as e:
        logging.warning(f"[ERROR] Failed to fetch {url} => {e}")
        return ""

# --- Main ---
def main():
    # Load all discovered links
    with open(INPUT_LINKS_FILE, "r", encoding="utf-8") as f:
        all_links = json.load(f)

    logging.info(f"Total links discovered: {len(all_links)}")

    # Filter only English HTML links
    filtered_links = sorted(set(filter(is_valid_english_url, all_links)))
    logging.info(f" English HTML pages to scrape: {len(filtered_links)}")

    scraped_data = []

    for url in tqdm(filtered_links, desc="Scraping English pages"):
        content = fetch_page_text(url)
        if content:
            scraped_data.append({
                "url": url,
                "content": content
            })
        time.sleep(REQUEST_DELAY)

    # Save to file
    with open(OUTPUT_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(scraped_data, f, indent=2, ensure_ascii=False)

    logging.info(f"Scraped and saved {len(scraped_data)} pages to {OUTPUT_DATA_FILE}")

if __name__ == "__main__":
    main()
