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
