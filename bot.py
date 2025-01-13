import logging
import os
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler
from tinydb import TinyDB, Query
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
scheduler = BackgroundScheduler()
scheduler.start()
db = TinyDB('movies_db.json')
User = Query()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")  # Add your TMDB API key to the environment variables
ADMIN_ID = 558387  # Telegram ID of the bot administrator

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

# Function to add a movie
def add_movie(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    query.edit_message_text("Введіть назву фільму, який ви хочете додати.")

# Function to list movies
def list_movies(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    movies = db.search(User.type == 'movie')
    if not movies:
        query.edit_message_text("Ваш список фільмів порожній.")
    else:
        message = "Ваш список фільмів:\n" + "\n".join(f"- {movie['name']}" for movie in movies)
        query.edit_message_text(message)

# Function to search for a movie
def search_movie(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    query.edit_message_text("Введіть назву фільму для пошуку.")

# Function to rate a movie
def rate_movie(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    query.edit_message_text("Оберіть фільм для оцінювання.")

# Function to set a reminder
def set_reminder(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    query.edit_message_text("Вкажіть назву фільму та дату для нагадування (у форматі YYYY-MM-DD).")

# Function to view history
def view_history(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    history = db.search(User.type == 'history')
    if not history:
        query.edit_message_text("Ваша історія переглядів порожня.")
    else:
        message = "Ваша історія переглядів:\n" + "\n".join(f"- {item['name']}" for item in history)
        query.edit_message_text(message)

# Function to remove a movie
def remove_movie(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    query.edit_message_text("Введіть назву фільму для видалення зі списку.")

# Fetch popular movies from Filmix
def filmix_popular(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    url = "https://filmix.my/popular/"
    response = requests.get(url)
    if response.status_code != 200:
        query.edit_message_text("Не вдалося отримати популярні фільми з Filmix. Спробуйте пізніше.")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    movies = soup.find_all('div', class_='shortstory')[:5]

    if not movies:
        query.edit_message_text("Не знайдено популярних фільмів на Filmix.")
        return

    message = "🎬 Популярні фільми на Filmix:\n"
    for movie in movies:
        title = movie.find('a', class_='shortstory__title').text.strip()
        link = movie.find('a', class_='shortstory__title')['href']
        message += f"- [{title}]({link})\n"

    query.edit_message_text(message, parse_mode="Markdown")

# Function to show help
def show_help(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    query.edit_message_text("Список доступних команд:\n/start\n/filmix\n/stats\n/addmoderator")

# Button handler
def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()  # Acknowledge the callback

    # Actions based on callback_data
    if query.data == 'add_movie':
        add_movie(update, context)
    elif query.data == 'list_movies':
        list_movies(update, context)
    elif query.data == 'search_movie':
        search_movie(update, context)
    elif query.data == 'rate_movie':
        rate_movie(update, context)
    elif query.data == 'set_reminder':
        set_reminder(update, context)
    elif query.data == 'view_history':
        view_history(update, context)
    elif query.data == 'remove_movie':
        remove_movie(update, context)
    elif query.data == 'filmix_popular':
        filmix_popular(update, context)
    elif query.data == 'help':
        show_help(update, context)

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
    # Check TELEGRAM_BOT_TOKEN
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN не встановлено. Додайте токен у змінні середовища.")

    # Initialize bot
    updater = Updater(token)

    dispatcher = updater.dispatcher

    # Command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("stats", stats))
    dispatcher.add_handler(CommandHandler("addmoderator", addmoderator))
    dispatcher.add_handler(CallbackQueryHandler(button_handler))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
