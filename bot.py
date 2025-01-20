import discord
from discord.ext import commands
from discord.ui import Button, View
import sqlite3
import os
import requests
import io
from dotenv import load_dotenv
from PIL import Image

# Завантаження змінних середовища з .env файлу (якщо є)
load_dotenv()

# Отримуємо токен з середовища
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Налаштування бота
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Створення або підключення до бази даних
def setup_db():
    conn = sqlite3.connect('movies.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS movies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    status TEXT,
                    rating INTEGER,
                    genre TEXT,
                    description TEXT,
                    release_year INTEGER,
                    poster BLOB,
                    user_id INTEGER)''')
    conn.commit()
    conn.close()

# Клас для кнопок
class MovieButtons(View):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id

    @discord.ui.button(label="Додати фільм", style=discord.ButtonStyle.primary)
    async def add_movie_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"{interaction.user.mention}, будь ласка, введіть назву фільму.", ephemeral=True)
        await interaction.user.send("Щоб додати фільм, надішліть мені назву фільму.")

    @discord.ui.button(label="Переглянути фільми", style=discord.ButtonStyle.success)
    async def my_movies_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        conn = sqlite3.connect('movies.db')
        c = conn.cursor()
        c.execute("SELECT title, status, rating, genre, description, release_year FROM movies WHERE user_id = ?", (user_id,))
        movies = c.fetchall()
        conn.close()

        if movies:
            response = "Ваші фільми:\n"
            for movie in movies:
                response += f"• {movie[0]} - Статус: {movie[1]}, Оцінка: {movie[2]}, Жанр: {movie[3]}, Опис: {movie[4]}, Рік: {movie[5]}\n"
        else:
            response = "У вас немає фільмів у списку."

        await interaction.response.send_message(response)

# Створення команди для перегляду кнопок
@bot.command()
async def movie_menu(ctx):
    view = MovieButtons(ctx.author.id)
    await ctx.send("Виберіть одну з опцій:", view=view)

# Функція для додавання фільму
@bot.command()
async def add_movie(ctx):
    await ctx.send("Будь ласка, введіть назву фільму.")
    
    def check(msg):
        return msg.author == ctx.author

    msg = await bot.wait_for('message', check=check)
    title = msg.content

    # Перевірка, чи фільм уже є в базі
    conn = sqlite3.connect('movies.db')
    c = conn.cursor()
    c.execute("SELECT * FROM movies WHERE title = ? AND user_id = ?", (title, ctx.author.id))
    existing_movie = c.fetchone()
    
    if existing_movie:
        await ctx.send("Цей фільм уже є в базі даних. Ви хочете оновити інформацію? (Так/Ні)")
        msg = await bot.wait_for('message', check=check)
        if msg.content.lower() != "так":
            await ctx.send("Операція скасована.")
            return
    
    await ctx.send("Будь ласка, введіть статус фільму (наприклад, 'Подивився', 'Хочу подивитися').")
    status_msg = await bot.wait_for('message', check=check)
    status = status_msg.content
    
    await ctx.send("Будь ласка, введіть оцінку фільму (від 1 до 10).")
    rating_msg = await bot.wait_for('message', check=check)
    rating = int(rating_msg.content)
    
    await ctx.send("Будь ласка, введіть жанр фільму (наприклад, 'Драма', 'Бойовик').")
    genre_msg = await bot.wait_for('message', check=check)
    genre = genre_msg.content
    
    await ctx.send("Будь ласка, введіть опис фільму.")
    description_msg = await bot.wait_for('message', check=check)
    description = description_msg.content
    
    await ctx.send("Будь ласка, введіть рік випуску фільму.")
    release_year_msg = await bot.wait_for('message', check=check)
    release_year = int(release_year_msg.content)
    
    await ctx.send("Будь ласка, надішліть постер фільму (URL зображення).")
    def check_img(msg):
        return msg.author == ctx.author and msg.attachments

    msg = await bot.wait_for('message', check=check_img)
    poster_url = msg.attachments[0].url
    response = requests.get(poster_url)
    img = Image.open(io.BytesIO(response.content))
    img_byte_array = io.BytesIO()
    img.save(img_byte_array, format='PNG')
    img_byte_array.seek(0)

    # Зберігаємо фільм в базу даних
    user_id = ctx.author.id
    if existing_movie:
        c.execute("UPDATE movies SET status = ?, rating = ?, genre = ?, description = ?, release_year = ?, poster = ? WHERE title = ? AND user_id = ?", 
                  (status, rating, genre, description, release_year, img_byte_array.read(), title, user_id))
    else:
        c.execute("INSERT INTO movies (title, status, rating, genre, description, release_year, poster, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                  (title, status, rating, genre, description, release_year, img_byte_array.read(), user_id))
    
    conn.commit()
    conn.close()

    await ctx.send(f"Фільм '{title}' додано до списку з статусом '{status}', оцінкою {rating}, жанром {genre}, описом: {description}, роком випуску {release_year}, і постером!")

# Запуск бота
setup_db()
bot.run(DISCORD_TOKEN)
