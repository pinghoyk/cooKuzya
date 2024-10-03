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


def now_time():
    return datetime.now(pytz.timezone('Europe/Moscow')).strftime("%Y-%m-%d %H:%M:%S")


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    username = message.chat.username
    first_name = message.from_user.first_name

    user = SQL_request("SELECT * FROM users WHERE user_id = ?", (user_id,))
    if user is None:
        SQL_request('INSERT INTO users (user_id, message, username, first_name, time_registration) VALUES (?, ?, ?, ?, ?)',
                    (user_id, message.message_id, username, first_name, now_time()))
        bot.send_message(user_id, f"Добро пожаловать {first_name}!", reply_markup=keyboard_main)
        print(f"{LOG}Зарегистрирован новый пользователь")
    else:
        SQL_request("UPDATE users SET message = ? WHERE user_id = ?", (message.message_id, user_id))
        bot.send_message(user_id, f"С возвращением! {first_name}!", reply_markup=keyboard_main)
        print(f"{LOG}Пользователь уже существует")


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    print(f"Вызов: {call.data}")


init_db()  # Инициализируем базу данных
print(f"{LOG}Бот запущен...")
bot.polling(none_stop=True)
