import parser
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
import sqlite3
import pytz
import config
import os

bot = telebot.TeleBot(config.API)

# Глобальные переменные
DB_NAME = "cook.db"
LOG = "Логи: "


# Кнопки
buttons_main = [
    InlineKeyboardButton(text=" 📖 Мои рецепты", callback_data="my_recipe")
]

buttons_recipe = [
    InlineKeyboardButton(text=" 🩷 Избранное", callback_data="favorite_recipe"),
    InlineKeyboardButton(text=" 🗃 Личные рецепты", callback_data="create_recipe"),
    InlineKeyboardButton(text=" ➕ Добавить рецепт", callback_data="add_recipe"),
    InlineKeyboardButton(text=" ◀️ Назад", callback_data="back_recipe")
]

btn_back = InlineKeyboardButton(text=" ◀️ Назад", callback_data="btn_back")

# Клавиатура
keyboard_main = InlineKeyboardMarkup(row_width=2).add(*buttons_main)
keyboard_recipes = InlineKeyboardMarkup(row_width=1).add(*buttons_recipe)
keyboard_markup = InlineKeyboardMarkup().add(btn_back)


# ПРОВЕРКА
if not os.path.exists(DB_NAME):
    print(f"{LOG}База данных не найдена, создана новая!")
try:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER,
                message INTEGER,
                username TEXT,
                name TEXT,
                time_registration TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS local_recipes (
                lr_id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_name TEXT,
                ingredients TEXT,
                instructions TEXT,
                id INTEGER,
                is_filled INTEGER DEFAULT 0,  -- 0 - не заполнен, 1 - полностью заполнен
                current_step INTEGER DEFAULT 0,  -- 0 - нет заполнения, 1 - заполнено название, 2 - ингредиенты и т.д.
                FOREIGN KEY (id) REFERENCES users (id)
            );
        """)
        
        conn.commit()
    print(f"{LOG}База данных успешно инициализирована!")
except sqlite3.Error as e:
    print(f"{LOG}Ошибка при работе с базой данных: {e}")
