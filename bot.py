import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, InputText
import sqlite3
import os
from PIL import Image
import io
import requests

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
        # Створюємо форму для додавання фільму
        await interaction.response.send_message(f"{interaction.user.mention}, будь ласка, введіть назву фільму та інші деталі!", ephemeral=True)
        await interaction.user.send("Щоб додати фільм, надішліть мені текстові деталі.")

    @discord.ui.button(label="Переглянути фільми", style=discord.ButtonStyle.success)
    async def my_movies_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Отримуємо список фільмів користувача
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

# Створення функції для додавання фільму
@bot.command()
async def add_movie(ctx, title: str, status: str, rating: int, genre: str, description: str, release_year: int):
    # Отримання зображення (постера) через URL
    await ctx.send("Будь ласка, надішліть постер фільму (URL зображення).")
    
    # Очікуємо на відповідь з постером
    def check(msg):
        return msg.author == ctx.author and msg.attachments

    msg = await bot.wait_for('message', check=check)
    
    # Завантажуємо постер
    poster_url = msg.attachments[0].url
    response = requests.get(poster_url)
    img = Image.open(io.BytesIO(response.content))
    img_byte_array = io.BytesIO()
    img.save(img_byte_array, format='PNG')
    img_byte_array.seek(0)
    
    # Зберігаємо фільм в базу даних
    user_id = ctx.author.id
    conn = sqlite3.connect('movies.db')
    c = conn.cursor()
    c.execute("INSERT INTO movies (title, status, rating, genre, description, release_year, poster, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
              (title, status, rating, genre, description, release_year, img_byte_array.read(), user_id))
    conn.commit()
    conn.close()

    await ctx.send(f"Фільм '{title}' додано до списку з статусом '{status}', оцінкою {rating}, жанром {genre}, описом: {description}, роком випуску {release_year}, і постером!")

# Запуск бота
setup_db()
bot.run('YOUR_BOT_TOKEN')
