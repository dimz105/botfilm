import logging
import os
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, Filters
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

    def handle_message(update: Update, context: CallbackContext) -> None:
        movie_name = update.message.text
        db.insert({"type": "movie", "name": movie_name})
        update.message.reply_text(f"Фільм '{movie_name}' додано до списку.")
        context.bot.remove_handler_by_name("message_handler")

    context.bot.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message), name="message_handler")

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

    def handle_message(update: Update, context: CallbackContext) -> None:
        movie_name = update.message.text
        response = requests.get(
            f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={movie_name}"
        )
        if response.status_code != 200:
            update.message.reply_text("Не вдалося виконати пошук. Спробуйте пізніше.")
            return

        results = response.json().get("results", [])
        if not results:
            update.message.reply_text("Фільм не знайдено.")
        else:
            message = "Результати пошуку:\n" + "\n".join(f"- {movie['title']} ({movie['release_date']})" for movie in results[:5])
            update.message.reply_text(message)
        context.bot.remove_handler_by_name("message_handler")

    context.bot.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message), name="message_handler")

# Function to set a reminder
def set_reminder(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    query.edit_message_text("Вкажіть назву фільму та дату нагадування у форматі YYYY-MM-DD.")

    def handle_reminder(update: Update, context: CallbackContext) -> None:
        data = update.message.text.split(' ', 1)
        if len(data) != 2:
            update.message.reply_text("Невірний формат. Використовуйте: <назва фільму> <YYYY-MM-DD>")
            return
        movie_name, reminder_date = data
        scheduler.add_job(
            lambda: update.message.reply_text(f"⏰ Нагадування: перегляньте '{movie_name}'!"),
            trigger=CronTrigger.from_crontab(f"0 9 {reminder_date}"),
        )
        update.message.reply_text(f"Нагадування на '{movie_name}' встановлено на {reminder_date}.")
        context.bot.remove_handler_by_name("reminder_handler")

    context.bot.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_reminder), name="reminder_handler")

# Function to remove a movie
def remove_movie(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    query.edit_message_text("Введіть назву фільму для видалення.")

    def handle_remove(update: Update, context: CallbackContext) -> None:
        movie_name = update.message.text
        db.remove((User.type == 'movie') & (User.name == movie_name))
        update.message.reply_text(f"Фільм '{movie_name}' видалено зі списку.")
        context.bot.remove_handler_by_name("remove_handler")

    context.bot.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_remove), name="remove_handler")

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
    elif query.data == 'set_reminder':
        set_reminder(update, context)
    elif query.data == 'remove_movie':
        remove_movie(update, context)
    elif query.data == 'filmix_popular':
        filmix_popular(update, context)

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
    dispatcher.add_handler(CallbackQueryHandler(button_handler))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
