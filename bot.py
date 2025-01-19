import discord
from discord.ext import commands
import sqlite3
import os

# Налаштування бота
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Створення або підключення до бази даних
def setup_db():
    conn = sqlite3.connect('movies.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS movies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    status TEXT,
                    rating INTEGER,
                    user_id INTEGER)''')
    conn.commit()
    conn.close()

# Додавання фільма
@bot.command()
async def add_movie(ctx, title: str, status: str, rating: int):
    user_id = ctx.author.id
    conn = sqlite3.connect('movies.db')
    c = conn.cursor()
    c.execute("INSERT INTO movies (title, status, rating, user_id) VALUES (?, ?, ?, ?)", 
              (title, status, rating, user_id))
    conn.commit()
    conn.close()
    await ctx.send(f"Фільм '{title}' додано до списку з статусом '{status}' і оцінкою {rating}.")

# Показати всі фільми користувача
@bot.command()
async def my_movies(ctx):
    user_id = ctx.author.id
    conn = sqlite3.connect('movies.db')
    c = conn.cursor()
    c.execute("SELECT title, status, rating FROM movies WHERE user_id = ?", (user_id,))
    movies = c.fetchall()
    conn.close()
    
    if movies:
        response = "Ваші фільми:\n"
        for movie in movies:
            response += f"• {movie[0]} - {movie[1]} - Оцінка: {movie[2]}\n"
    else:
        response = "У вас немає фільмів у списку."
    
    await ctx.send(response)

# Оцінка фільма
@bot.command()
async def rate_movie(ctx, title: str, rating: int):
    user_id = ctx.author.id
    conn = sqlite3.connect('movies.db')
    c = conn.cursor()
    c.execute("UPDATE movies SET rating = ? WHERE title = ? AND user_id = ?", 
              (rating, title, user_id))
    conn.commit()
    conn.close()
    await ctx.send(f"Оцінка фільма '{title}' оновлена на {rating}.")

# Запуск бота
setup_db()
bot.run(os.getenv('DISCORD_TOKEN'))
