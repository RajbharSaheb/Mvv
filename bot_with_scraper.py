import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import requests
from bs4 import BeautifulSoup

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
BASE_URL = "https://mkvcinemas.kiwi"
HEADERS = {"User-Agent": "Mozilla/5.0"}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def search_movies(query):
    url = f"{BASE_URL}/?s={query.replace(' ', '+')}"
    r = requests.get(url, headers=HEADERS)
    print("[DEBUG HTML] ", r.text[:800])
    soup = BeautifulSoup(r.text, 'html.parser')
    results = []
    for item in soup.select("article, div.post, div.entry")[:5]:
        a = item.select_one("a")
        if a:
            results.append({"title": a.text.strip(), "link": a["href"]})
    print("[DEBUG Results]", results)
    return results
    
def get_download_link(movie_url):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)
    wait = WebDriverWait(driver, 20)
    driver.get(movie_url)

    try:
        wait.until(EC.element_to_be_clickable((By.ID, "soralink-human-verif-main"))).click()
        wait.until(EC.element_to_be_clickable((By.ID, "generater"))).click()
        wait.until(EC.element_to_be_clickable((By.ID, "showlink"))).click()
        driver.switch_to.window(driver.window_handles[-1])
        final_url = driver.current_url
    except Exception:
        final_url = "❌ Error while scraping link"
    finally:
        driver.quit()

    return final_url

def start(update: Update, context: CallbackContext):
    update.message.reply_text("👋 Welcome! Use /search <movie name> to get started.")

def search(update: Update, context: CallbackContext):
    query = ' '.join(context.args)
    if not query:
        return update.message.reply_text("❗ Usage: /search <movie name>")

    update.message.reply_text("🔍 Searching...")
    movies = search_movies(query)
    if not movies:
        return update.message.reply_text("❌ No movies found.")

    for idx, movie in enumerate(movies, start=1):
        btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Get Download Link", callback_data=f"dl_{movie['link']}")]
        ])
        update.message.reply_text(f"{idx}. {movie['title']}", reply_markup=btn)

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    if query.data.startswith("dl_"):
        movie_url = query.data[3:]
        query.edit_message_text("⏳ Scraping download link...")
        link = get_download_link(movie_url)
        query.edit_message_text(f"✅ Download Link:\n{link}")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("search", search))
    dp.add_handler(CallbackQueryHandler(button_handler))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
