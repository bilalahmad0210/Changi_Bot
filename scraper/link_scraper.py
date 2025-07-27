import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
import time
import json

# --- Config ---
BASE_URLS = [
    "https://www.changiairport.com/",
    "https://www.jewelchangiairport.com/"
]
SITEMAP_URLS = [
    "https://www.changiairport.com/sitemap.xml",
    "https://www.jewelchangiairport.com/sitemap.xml"
]
BLOCKED_EXTENSIONS = ('.pdf', '.jpg', '.jpeg', '.png', '.gif', '.zip', '.docx', '.xlsx', '.svg', '.ico')
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
}
REQUEST_DELAY = 1

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_links_from_sitemap(sitemap_url):
    links = []
    try:
        res = requests.get(sitemap_url, headers=HEADERS)
        if res.status_code == 200:
            soup = BeautifulSoup(res.content, 'xml')
            links = [loc.text.strip() for loc in soup.find_all('loc')]
            logger.info(f"Found {len(links)} links in sitemap: {sitemap_url}")
    except Exception as e:
        logger.warning(f"Failed to parse sitemap {sitemap_url}: {e}")
    return links


def get_links_from_html(base_url, max_pages=500):
    visited = set()
    to_visit = [base_url]
    internal_links = set()

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue
        visited.add(url)

        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            if res.status_code != 200:
                continue
            soup = BeautifulSoup(res.text, 'html.parser')
            for tag in soup.find_all('a', href=True):
                href = tag['href']
                full_url = urljoin(base_url, href)
                if urlparse(full_url).netloc != urlparse(base_url).netloc:
                    continue
                if full_url.endswith(BLOCKED_EXTENSIONS) or full_url.startswith(('mailto:', 'javascript:')):
                    continue
                if full_url not in internal_links:
                    internal_links.add(full_url)
                    to_visit.append(full_url)
            logger.info(f"[{len(visited)}] Fetched: {url} | Found: {len(internal_links)} links")
            time.sleep(REQUEST_DELAY)
        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")

    return list(internal_links)

def save_links_to_json(all_links, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_links, f, indent=2)
    logger.info(f"Saved {len(all_links)} total links to {filename}")


if __name__ == '__main__':
    final_links = set()

    for base_url, sitemap_url in zip(BASE_URLS, SITEMAP_URLS):
        logger.info(f"\n--- Processing {base_url} ---")

        sitemap_links = get_links_from_sitemap(sitemap_url)
        html_links = get_links_from_html(base_url, max_pages=500)

        all = set(sitemap_links) | set(html_links)
        logger.info(f"Total unique links collected from {base_url}: {len(all)}")

        final_links.update(all)

    save_links_to_json(list(final_links), "data/all_discovered_links.json")
