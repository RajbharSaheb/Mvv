import os
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
    soup = BeautifulSoup(r.text, 'html.parser')
    results = []
    for post in soup.select("div#content article")[:5]:
        title = post.select_one("h2 a").text.strip()
        link = post.select_one("h2 a")['href']
        results.append({"title": title, "link": link})
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
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from dotenv import load_dotenv

from movies_scraper import (
    scrape_movies,
    scrape_download_links,
    search_cache,
    scrape_latest_movies,
    scrape_random_movie
)

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "👋 Welcome to Movie Bot!\nUse /help to see commands."
    )

def help_cmd(update: Update, context: CallbackContext):
    msg = (
        "🤖 *Movie Bot Commands:*\n\n"
        "/start – Welcome message\n"
        "/search <movie> – Search for a movie\n"
        "/download <number> – Get download links\n"
        "/latest – Latest movie uploads\n"
        "/random – Random movie\n"
        "/help – Show this help message"
    )
    update.message.reply_text(msg, parse_mode="Markdown")

def search(update: Update, context: CallbackContext):
    q = " ".join(context.args)
    if not q:
        return update.message.reply_text("❗ Usage: /search <movie name>")
    results = scrape_movies(q)
    if not results:
        return update.message.reply_text("❌ No results found.")
    search_cache[update.effective_user.id] = results
    msg = "🔍 *Search Results:*\n\n"
    for i, m in enumerate(results, 1):
        msg += f"{i}. [{m['title']}]({m['link']})\n"
    msg += "\nSend /download <number> to get download links."
    update.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=True)

def download(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in search_cache:
        return update.message.reply_text("❗ Use /search first.")
    try:
        index = int(context.args[0]) - 1
    except:
        return update.message.reply_text("❗ Usage: /download <number>")
    results = search_cache[user_id]
    if index < 0 or index >= len(results):
        return update.message.reply_text("❌ Invalid number.")
    movie = results[index]
    update.message.reply_text(f"🔄 Fetching links for: *{movie['title']}*", parse_mode="Markdown")
    links = scrape_download_links(movie['link'])
    update.message.reply_text("\n".join(links), disable_web_page_preview=True)

def latest(update: Update, context: CallbackContext):
    results = scrape_latest_movies()
    if not results:
        return update.message.reply_text("❌ Couldn't fetch latest movies.")
    msg = "🆕 *Latest Movies:*\n\n"
    for i, movie in enumerate(results, 1):
        msg += f"{i}. [{movie['title']}]({movie['link']})\n"
    update.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=True)

def random_movie(update: Update, context: CallbackContext):
    movie = scrape_random_movie()
    if not movie:
        return update.message.reply_text("❌ Couldn't fetch random movie.")
    msg = f"🎲 *Random Pick:*\n\n[{movie['title']}]({movie['link']})"
    update.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=True)

def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_cmd))
    dp.add_handler(CommandHandler("search", search))
    dp.add_handler(CommandHandler("download", download))
    dp.add_handler(CommandHandler("latest", latest))
    dp.add_handler(CommandHandler("random", random_movie))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
