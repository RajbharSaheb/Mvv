import requests
from bs4 import BeautifulSoup
import random

BASE_URL = "https://themoviesverse.com.pl"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# Cache (used in /download)
search_cache = {}

def scrape_movies(query):
    url = f"{BASE_URL}/?s={query.replace(' ', '+')}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        return []
    soup = BeautifulSoup(r.text, 'html.parser')
    results = []
    for item in soup.select("article")[:5]:
        tag = item.select_one("h2 a")
        if tag:
            results.append({"title": tag.text.strip(), "link": tag["href"]})
    return results

def scrape_download_links(page_url):
    r = requests.get(page_url, headers=HEADERS)
    if r.status_code != 200:
        return []
    soup = BeautifulSoup(r.text, 'html.parser')
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.text.strip()
        if any(x in href.lower() for x in ["drive", "mega", "mediafire", "zippy", "clicknupload", "1fichier"]):
            links.append(f"🔗 {text}: {href}")
    return links or ["⚠️ No download links found."]

def scrape_latest_movies():
    r = requests.get(BASE_URL, headers=HEADERS)
    if r.status_code != 200:
        return []
    soup = BeautifulSoup(r.text, 'html.parser')
    results = []
    for item in soup.select("article")[:5]:
        tag = item.select_one("h2 a")
        if tag:
            results.append({"title": tag.text.strip(), "link": tag["href"]})
    return results

def scrape_random_movie():
    r = requests.get(BASE_URL, headers=HEADERS)
    if r.status_code != 200:
        return None
    soup = BeautifulSoup(r.text, 'html.parser')
    items = soup.select("article")
    if not items:
        return None
    item = random.choice(items)
    tag = item.select_one("h2 a")
    if tag:
        return {"title": tag.text.strip(), "link": tag["href"]}
    return None
