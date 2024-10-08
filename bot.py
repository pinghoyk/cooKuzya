import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
import sqlite3
import pytz
import config
import os

bot = telebot.TeleBot(config.API)

# Глобальные переменные
DB_PATH = "cook.db"
LOG = "Логи: "
recipe_data = {}
current_steps = {}


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
    InlineKeyboardButton(text=" 🗃 Личные рецепты", callback_data="create_recipe"),
    InlineKeyboardButton(text=" ⬅️ Назад", callback_data="back_recipe")
]


btn_back = InlineKeyboardButton(text=" ⬅️ Назад", callback_data="btn_back")

# Клавиатура
keyboard_main = InlineKeyboardMarkup(row_width=2).add(*buttons_main)

keyboard_recipes = InlineKeyboardMarkup(row_width=1).add(*buttons_recipe)

keyboard_markup = InlineKeyboardMarkup().add(btn_back)


# ФУНКЦИИ
# Функция для создания бд
def init_db():
    if not os.path.exists(DB_PATH):
        print(f"{LOG}База данных не найдена, будет создана новая.")
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id_col INTEGER PRIMARY KEY AUTOINCREMENT,
                    message INTEGER,
                    user_id INTEGER UNIQUE,  -- Уникальный идентификатор для предотвращения дублирования
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
            conn.commit()
        print(f"{LOG}База данных успешно инициализирована!")
    except sqlite3.Error as e:
        print(f"{LOG}Ошибка при работе с базой данных: {e}")


# Функция для подключения к бд
def SQL_request(request, params=(), fetchone=False):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(request, params)
        if fetchone:
            result = cursor.fetchone()
        else:
            result = cursor.fetchall()

        cursor.close()
        return result


# Функция для получения приветствия в зависимости от времени суток
def get_greeting(first_name):
    current_hour = datetime.now(pytz.timezone('Europe/Moscow')).hour
    if 5 <= current_hour < 12:
        return f"Доброе утро, {first_name}!"
    elif 12 <= current_hour < 18:
        return f"Добрый день, {first_name}!"
    elif 18 <= current_hour < 23:
        return f"Добрый вечер, {first_name}!"
    else:
        return f"Доброй ночи, {first_name}!"


# Функция для получения времени
def now_time():
    return datetime.now(pytz.timezone('Europe/Moscow')).strftime("%Y-%m-%d %H:%M:%S")


# Функция для удаления всех предыдущич сообщений
def delete_previous_messages(user_id, message_id, count=2):
    for i in range(count):
        try:
            bot.delete_message(user_id, message_id - i)
        except telebot.apihelper.ApiException as e:
            print(f"Ошибка при удалении сообщения {message_id - i}: {e}")
        except Exception as e:
            print(f"Неизвестная ошибка при удалении сообщения {message_id - i}: {e}")


# Функции для процесса добавления рецепта
def update_message(user_id, message_id, step, text, callback_next, callback_change):
    recipe_data[user_id][step] = text

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
           InlineKeyboardButton(text=" ➡️ Далее", callback_data=callback_next),
           InlineKeyboardButton(text=" ✏️ Изменить", callback_data=callback_change)
       )

    bot.edit_message_text(f"{step.capitalize()}: {text}", user_id, message_id, reply_markup=markup)

def handle_name(message):
    user_id = message.chat.id
    recipe_data[user_id] = {"name": message.text}
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
           InlineKeyboardButton(text=" ➡️ Далее", callback_data="next_ingredients"),
           InlineKeyboardButton(text=" ✏️ Изменить", callback_data="change_name")
       )

    delete_previous_messages(user_id, message.message_id)
    
    bot.send_message(user_id, f"Название рецепта: {recipe_data[user_id]['name']}", reply_markup=markup)

def handle_ingredients(message):
    user_id = message.chat.id
    recipe_data[user_id]["ingredients"] = message.text
    markup = InlineKeyboardMarkup()
    markup.add(
           InlineKeyboardButton(text=" ➡️ Далее", callback_data="next_instructions"),
           InlineKeyboardButton(text=" ✏️ Изменить", callback_data="change_ingredients")
       )

    delete_previous_messages(user_id, message.message_id)
    
    bot.send_message(user_id, f"Ингредиенты: {recipe_data[user_id]['ingredients']}", reply_markup=markup)

def handle_instructions(message, step, call_message):
    user_id = message.chat.id
    if "instructions" not in recipe_data[user_id]:
        recipe_data[user_id]["instructions"] = []
        
    recipe_data[user_id]["instructions"].append(f"Шаг {step}: {message.text}")
    markup = InlineKeyboardMarkup()

    markup.add(
       InlineKeyboardButton(text=" ✏️ Добавить шаг", callback_data=f"next_step_{step + 1}"),
       InlineKeyboardButton(text=" ✅  Закончить", callback_data="finish_recipe")
    )
    
    delete_previous_messages(user_id, message.message_id)

    bot.send_message(user_id, f"Шаг {step}: {message.text}", reply_markup=markup)


# Функция для получения рецептов от конкретного пользователя
def get_recipe_user(user_id):
    recipes = SQL_request("SELECT id, recipe_name, ingredients, instructions FROM recipes WHERE user_id = ?", (user_id,))
    return recipes if recipes else []


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
        greeting = get_greeting(first_name)
        bot.send_message(user_id, greeting, reply_markup=keyboard_main)
        print(f"{LOG}Пользователь уже существует")


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    print(f"Вызов: {call.data}")
    user_id = call.message.chat.id
    message_id = call.message.message_id

    if call.data == 'my_recipe':
        recipe = SQL_request("SELECT recipe_name, ingredients, instructions FROM recipes WHERE user_id = ?", (user_id,))
        bot.edit_message_text("Ваши рецепты:", user_id, message_id, reply_markup=keyboard_recipes)

    elif call.data == "add_recipe":
        bot.edit_message_text("Введите название рецепта:", user_id, message_id, reply_markup=keyboard_markup)
        bot.register_next_step_handler_by_chat_id(user_id, handle_name)

    elif call.data == "next_ingredients":
        bot.edit_message_text("Введите ингредиенты:", user_id, message_id)
        bot.register_next_step_handler_by_chat_id(user_id, handle_ingredients)

    elif call.data == "next_instructions":
        bot.edit_message_text("Введите описание к шагу 1:", user_id, message_id)
        bot.register_next_step_handler_by_chat_id(user_id, lambda msg: handle_instructions(msg, 1, call.message))

    elif call.data.startswith("next_step_"):
        step = int(call.data.split("_")[-1])
        bot.edit_message_text(f"Введите описание к шагу {step}:", user_id, message_id)
        bot.register_next_step_handler_by_chat_id(user_id, lambda msg: handle_instructions(msg, step, call.message))

    elif call.data == "finish_recipe":
        recipe = recipe_data[user_id]
        ingredients = recipe.get("ingredients", "")
        instructions = "\n".join(recipe.get("instructions", []))
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
               InlineKeyboardButton(text=" ✅ Сохранить", callback_data="save_recipe"),
               InlineKeyboardButton(text=" ✏️ Изменить", callback_data="edit_recipe")
           )
        markup.add(InlineKeyboardButton(text=" ❌ Отмена", callback_data="cancel"))
        bot.edit_message_text(f"Ваш рецепт:\n\nНазвание: {recipe['name']}\n\nСостав: {ingredients}\n\nОписание приготовления:\n{instructions}", user_id, message_id, reply_markup=markup)

    elif call.data == "save_recipe":
        recipe = recipe_data[user_id]
        SQL_request("INSERT INTO recipes (user_id, recipe_name, ingredients, instructions) VALUES (?, ?, ?, ?)",
                    (user_id, recipe['name'], recipe['ingredients'], "\n".join(recipe['instructions'])))
        
        
        bot.edit_message_text("Рецепт успешно сохранён!", user_id, message_id, reply_markup=keyboard_markup)

    elif call.data == "edit_recipe":
        bot.edit_message_text("Редактируем рецепт. Введите новое название:", user_id, message_id)
        bot.register_next_step_handler_by_chat_id(user_id, handle_name)

    elif call.data == "change_name":
        bot.edit_message_text("Введите новое название рецепта:", user_id, message_id)
        bot.register_next_step_handler_by_chat_id(user_id, handle_name)

    elif call.data == "change_ingredients":
        bot.edit_message_text("Введите новые ингредиенты:", user_id, message_id)
        bot.register_next_step_handler_by_chat_id(user_id, handle_ingredients)

    elif call.data == "btn_back":
        bot.edit_message_text("Ваши рецепты:", user_id, message_id, reply_markup=keyboard_recipes)

    elif call.data == "back_recipe":
        user_id = call.message.chat.id
        first_name = call.message.chat.first_name
        greeting = get_greeting(first_name)  # Определяем greeting
        bot.edit_message_text(greeting, chat_id=user_id, message_id=call.message.message_id, reply_markup=keyboard_main)

    elif call.data == "cancel":
        bot.edit_message_text("Ваши рецепты:", user_id, message_id, reply_markup=keyboard_recipes)







init_db()  # Инициализируем базу данных
print(f"{LOG}Бот запущен...")
bot.polling(none_stop=True)