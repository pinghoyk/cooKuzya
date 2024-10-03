import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
import sqlite3
import pytz
import config

bot = telebot.TeleBot(config.API)

# Глобальные переменные
DB_PATH = "cook.db"
LOG = "Логи: "

# Кнопки
buttons_main = [
    InlineKeyboardButton(text="📜 Мои рецепты", callback_data="my_recipe"),
    InlineKeyboardButton(text="📂 Категории", callback_data="recipe_category"),
    InlineKeyboardButton(text="🥕 По ингредиентам", callback_data="recipe_ingredients"),
    InlineKeyboardButton(text="🎲 Случайные", callback_data="recipe_random"),
    InlineKeyboardButton(text="💡 Советы", callback_data="culinary_tips"),
    InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
]

# Клавиатура
keyboard_main = InlineKeyboardMarkup(row_width=2)
keyboard_main.add(*buttons_main)  # Добавляем все кнопки за один раз


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id_col INTEGER PRIMARY KEY AUTOINCREMENT,
                message INTEGER,
                user_id INTEGER,
                username TEXT,
                first_name TEXT,
                time_registration TIMESTAMP
            )
        """)
    print(f"{LOG}База данных создана!")


def SQL_request(request, params=()):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(request, params)
        if request.strip().lower().startswith('select'):
            return cursor.fetchone()
