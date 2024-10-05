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
    # InlineKeyboardButton(text="🥕 По ингредиентам", callback_data="recipe_ingredients"),
    # InlineKeyboardButton(text="💡 Советы", callback_data="culinary_tips"),
    # InlineKeyboardButton(text="📂 Категории", callback_data="recipe_category"),   
    # InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
    # InlineKeyboardButton(text="🎲 Случайные", callback_data="recipe_random"),
]

buttons_recipe = [
    InlineKeyboardButton(text=" ➕ Добавить рецепт", callback_data="add_recipe"),
    # InlineKeyboardButton(text=" 💾 Сохраненные рецепты", callback_data="save_recipe"),
]

# Клавиатура
keyboard_main = InlineKeyboardMarkup(row_width=2)
keyboard_main.add(*buttons_main)  # Добавляем все кнопки за один раз

keyboard_recipes = InlineKeyboardMarkup(row_width=1)
keyboard_recipes.add(*buttons_recipe)


# ФУНКЦИИ
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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                recipe_name TEXT,
                ingredients TEXT,
                instructions TEXT
            )
        """)
    print(f"{LOG}База данных создана!")


def SQL_request(request, params=()):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(request, params)
        if request.strip().lower().startswith('select'):
            return cursor.fetchall()


def now_time():
    return datetime.now(pytz.timezone('Europe/Moscow')).strftime("%Y-%m-%d %H:%M:%S")


# Удаляет все предыдущие сообщения
def delete_previous_messages(user_id, message_id, count=2):
    for i in range(count):
        try:
            bot.delete_message(user_id, message_id - i)
        except:
            pass  # Если сообщение не удается удалить, игнорируем ошибку (добавить обработку)


# Процесс добавления рецепта
def update_message(user_id, message_id, step, text, callback_next, callback_change):
    recipe_data[user_id][step] = text
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="Далее", callback_data=callback_next))
    markup.add(InlineKeyboardButton(text="Изменить", callback_data=callback_change))
    bot.edit_message_text(f"{step.capitalize()}: {text}", user_id, message_id, reply_markup=markup)


def handle_name(message):
    user_id = message.chat.id
    recipe_data[user_id] = {"name": message.text}
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="Далее", callback_data="next_ingredients"))
    markup.add(InlineKeyboardButton(text="Изменить", callback_data="change_name")) 

    # Удаляем предыдущие сообщения
    delete_previous_messages(user_id, message.message_id)
    
    bot.send_message(user_id, f"Название: {recipe_data[user_id]['name']}", reply_markup=markup)


def handle_ingredients(message):
    user_id = message.chat.id
    recipe_data[user_id]["ingredients"] = message.text
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="Далее", callback_data="next_instructions"))
    markup.add(InlineKeyboardButton(text="Изменить", callback_data="change_ingredients"))  # Добавлено изменение ингредиентов

    # Удаляем предыдущие сообщения
    delete_previous_messages(user_id, message.message_id)
    
    bot.send_message(user_id, f"Ингредиенты: {recipe_data[user_id]['ingredients']}", reply_markup=markup)


def handle_instructions(message, step, call_message):
    user_id = message.chat.id
    if "instructions" not in recipe_data[user_id]:
        recipe_data[user_id]["instructions"] = []
        
    recipe_data[user_id]["instructions"].append(f"Шаг {step}: {message.text}")

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="Добавить шаг", callback_data=f"next_step_{step + 1}"))
    markup.add(InlineKeyboardButton(text="Закончить", callback_data="finish_recipe"))

    # Удаляем сообщение с вводом шага
    delete_previous_messages(user_id, message.message_id)

    bot.send_message(user_id, f"Шаг {step}: {message.text}", reply_markup=markup)


def get_user_recipes(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT recipe_name, ingredients, instructions FROM recipes WHERE user_id = ?", (user_id,))
        return cursor.fetchall()


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
        bot.send_message(user_id, f"С возвращением, {first_name}!", reply_markup=keyboard_main)
        print(f"{LOG}Пользователь уже существует")


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    print(f"Вызов: {call.data}")

    if call.data == 'my_recipe':
        recipes = get_user_recipes(user_id)
        bot.edit_message_text("Ваши рецепты:", user_id, message_id, reply_markup=keyboard_recipes)


init_db()  # Инициализируем базу данных
print(f"{LOG}Бот запущен...")
bot.polling(none_stop=True)