import logging
import os
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, Filters
from tinydb import TinyDB, Query
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from pytube import YouTube
from random import choice

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
scheduler = BackgroundScheduler()
scheduler.start()
db = TinyDB('movies_db.json')
User = Query()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")  # Add your TMDB API key to the environment variables
ADMIN_ID = int(os.getenv("ADMIN_ID"))  # Telegram ID of the bot administrator

# Define start command
def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("➕ Додати фільм", callback_data='add_movie')],
        [InlineKeyboardButton("📜 Списки фільмів", callback_data='list_movies')],
        [InlineKeyboardButton("🔍 Пошук фільму", callback_data='search_movie')],
        [InlineKeyboardButton("⭐ Оцінити фільм", callback_data='rate_movie')],
        [InlineKeyboardButton("⏰ Нагадування", callback_data='set_reminder')],
        [InlineKeyboardButton("🕒 Історія переглядів", callback_data='view_history')],
        [InlineKeyboardButton("❌ Видалити фільм", callback_data='remove_movie')],
        [InlineKeyboardButton("🎬 Популярне на Filmix", callback_data='filmix_popular')],
        [InlineKeyboardButton("ℹ️ Допомога", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(
        "Привіт! Я бот для управління твоїми списками фільмів. Обери дію з меню:",
        reply_markup=reply_markup
    )

# Fetch popular movies from Filmix
def filmix_popular(update: Update, context: CallbackContext) -> None:
    url = "https://filmix.my/popular/"
    response = requests.get(url)
    if response.status_code != 200:
        update.message.reply_text("Не вдалося отримати популярні фільми з Filmix. Спробуйте пізніше.")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    movies = soup.find_all('div', class_='shortstory')[:5]

    if not movies:
        update.message.reply_text("Не знайдено популярних фільмів на Filmix.")
        return

    message = "🎬 Популярні фільми на Filmix:\n"
    for movie in movies:
        title = movie.find('a', class_='shortstory__title').text.strip()
        link = movie.find('a', class_='shortstory__title')['href']
        message += f"- [{title}]({link})\n"

    update.message.reply_text(message, parse_mode="Markdown")

# Admin-only command to add moderators
def addmoderator(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("Ви не маєте прав адміністратора для цієї команди.")
        return

    if not context.args:
        update.message.reply_text("Вкажіть ID користувача для додавання в модератори.")
        return

    moderator_id = int(context.args[0])
    db.insert({"user_id": moderator_id, "role": "moderator"})
    update.message.reply_text(f"Користувача з ID {moderator_id} додано в модератори.")

# Admin-only command to view statistics
def stats(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("Ви не маєте прав адміністратора для цієї команди.")
        return

    total_users = len({record['user_id'] for record in db.all()})
    total_movies = len(db.all())

    update.message.reply_text(
        f"Статистика бота:\n"
        f"👥 Кількість користувачів: {total_users}\n"
        f"🎥 Кількість фільмів у базі: {total_movies}"
    )

# Main function
def main() -> None:
    # Initialize bot
    updater = Updater(os.getenv("TELEGRAM_BOT_TOKEN"))

    dispatcher = updater.dispatcher

    # Command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("filmix", filmix_popular))
    dispatcher.add_handler(CommandHandler("stats", stats))
    dispatcher.add_handler(CommandHandler("addmoderator", addmoderator))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
