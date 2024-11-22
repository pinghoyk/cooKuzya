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


# ФУНКЦИИ
# Подключение к бд
def SQL_request(request, params=(), fetchone=False):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(request, params)
        if fetchone:
            result = cursor.fetchone()
        else:
            result = cursor.fetchall()
        cursor.close()
        return result


# Получение приветствия в зависимости от времени суток
def get_greeting(name):
    current_hour = datetime.now(pytz.timezone('Asia/Yekaterinburg')).hour
    if 5 <= current_hour < 12:
        return f"Доброе утро, {name}!"
    elif 12 <= current_hour < 18:
        return f"Добрый день, {name}!"
    elif 18 <= current_hour < 23:
        return f"Добрый вечер, {name}!"
    else:
        return f"Доброй ночи, {name}!"


# Получение времени
def now_time():
    return datetime.now(pytz.timezone('Asia/Yekaterinburg')).strftime("%Y-%m-%d %H:%M:%S")





# Получение названия рецепта
def handle_name(message, message_id, recipe_id=None, edit_mode=False):
    user_id = message.chat.id
    recipe_name = message.text.strip()

    if recipe_name.lower() == '/start':
        start(message)
        return

    if edit_mode:
        SQL_request("UPDATE local_recipes SET recipe_name=? WHERE lr_id=?", (recipe_name, recipe_id))
        current_step = SQL_request("SELECT current_step FROM local_recipes WHERE lr_id=?", (recipe_id,), fetchone=True)

        if current_step:
            current_step = current_step[0]
            if current_step == 2:
                bot.register_next_step_handler(message, handle_ingredients, message_id, recipe_id)
            elif current_step == 3:
                bot.register_next_step_handler(message, handle_steps, message_id, recipe_id)
        return

    recipe = SQL_request("SELECT lr_id, current_step FROM local_recipes WHERE id=? AND is_filled=0", (user_id,), fetchone=True)

    if recipe:
        # Если рецепт существует, обновляем его название и сбрасываем шаг на 1
        recipe_id, current_step = recipe
        SQL_request("UPDATE local_recipes SET recipe_name=?, current_step=1 WHERE lr_id=?", (recipe_name, recipe_id))
    else:
        # Если рецепта нет, создаем новый
        SQL_request("INSERT INTO local_recipes (recipe_name, id, is_filled, current_step) VALUES (?, ?, 0, 1)",(recipe_name, user_id))
        recipe_id = SQL_request("SELECT last_insert_rowid()", fetchone=True)[0]

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="✍️ Перезаписать название", callback_data=f"change_name_{recipe_id}"))

    bot.edit_message_text(text=f"Название: <b>{recipe_name}</b>\n\nКузя записывает состав:", chat_id=user_id, message_id=message_id, reply_markup=markup, parse_mode="HTML")

    recipe_id = SQL_request("SELECT lr_id FROM local_recipes WHERE id=? AND is_filled=0", (user_id,), fetchone=True)[0]
    bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    bot.register_next_step_handler(message, handle_ingredients, message_id, recipe_id)


# Получение состава рецепта
def handle_ingredients(message, message_id, recipe_id, edit_mode=False):
    user_id = message.chat.id
    ingredients = message.text.strip()

    if ingredients.lower() == '/start':
        start(message)
        return

    if edit_mode:
        SQL_request("UPDATE local_recipes SET ingredients=? WHERE lr_id=?", (ingredients, recipe_id))
        bot.register_next_step_handler(message, handle_steps, message_id, recipe_id)
        return

    recipe = SQL_request("SELECT lr_id, current_step FROM local_recipes WHERE lr_id=? AND is_filled=0", (recipe_id,), fetchone=True)

    if recipe:
        # Если рецепт найден, обновляем ингредиенты
        SQL_request("UPDATE local_recipes SET ingredients=?, current_step=2 WHERE lr_id=?", (ingredients, recipe_id))

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(text="✍️ Перезаписать состав", callback_data=f"change_ingredients_{recipe_id}"))

        bot.edit_message_text(f"<b>Состав:</b> {ingredients}\n\nКузя готов записать шаги! Введите их, каждый на новой строке:", chat_id=user_id, message_id=message_id, reply_markup=markup,parse_mode="HTML")
        bot.delete_message(message.chat.id, message.message_id)
        bot.register_next_step_handler(message, handle_steps, message_id, recipe_id)


# Получение шагов рецепта
def handle_steps(message, message_id, recipe_id, edit_mode=False, attempt=1):
    try:
        user_id = message.chat.id
        instructions = message.text.strip() if message.text else ""
        steps = [step.strip() for step in instructions.split("\n") if step.strip()]

        if instructions.lower() == '/start':
            start(message)
            return

        # Проверяем на минимальное количество шагов и их корректность
        if len(steps) < 2:
            response_text = (
                "Кузя ждет хотя бы два шага! Введите их снова (каждый шаг с новой строки):"
                if attempt == 1 else
                "Кузя снова напоминает: нужно хотя бы два шага! Попробуйте еще раз:"
            )
            msg = bot.edit_message_text(chat_id=user_id, message_id=message_id, text=response_text)
            bot.delete_message(chat_id=user_id, message_id=message.message_id)
            bot.register_next_step_handler(msg, handle_steps, message_id, recipe_id, edit_mode, attempt + 1)
            return

        formatted_instructions = "\n".join(steps)

        if edit_mode:
            # Обновляем шаги в базе данных
            SQL_request("UPDATE local_recipes SET instructions=? WHERE lr_id=?", (formatted_instructions, recipe_id))

            markup = InlineKeyboardMarkup(row_width=1)
            markup.add(
                InlineKeyboardButton(text="✍️ Перезаписать шаги", callback_data=f"change_steps_{recipe_id}"),
                InlineKeyboardButton(text="📔 Показать рецепт", callback_data=f"show_recipe_{recipe_id}")
            )

            bot.edit_message_text(chat_id=user_id, message_id=message_id, text=f"<b>Шаги:</b>\n{formatted_instructions}", reply_markup=markup, parse_mode="HTML")
        else:
            # Добавляем новые шаги и помечаем рецепт как завершенный
            SQL_request("UPDATE local_recipes SET instructions=?, is_filled=1, current_step=3 WHERE lr_id=?", (formatted_instructions, recipe_id))

            markup = InlineKeyboardMarkup(row_width=1)
            markup.add(
                InlineKeyboardButton(text="✍️ Перезаписать шаги", callback_data=f"change_steps_{recipe_id}"),
                InlineKeyboardButton(text="📔 Показать рецепт", callback_data=f"show_recipe_{recipe_id}")
            )

            bot.edit_message_text(chat_id=user_id, message_id=message_id, text=f"<b>Шаги:</b>\n{formatted_instructions}\n\nКузя вздохнул... рецепт писать больше не нужно было!", reply_markup=markup, parse_mode="HTML")

        # Удаляем сообщение пользователя
        if message and message.message_id:
            bot.delete_message(chat_id=user_id, message_id=message.message_id)
    except Exception as e:
        print(f"Ошибка в handle_steps: {e}")


# Клавиатуры для продолжения рецепта
def get_name_keyboard(recipe_id):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="✍️ Перезаписать название", callback_data=f"change_name_{recipe_id}"))
    return markup


def get_ingredients_keyboard(recipe_id):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="✍️ Перезаписать состав", callback_data=f"change_ingredients_{recipe_id}"))
    return markup


def get_steps_keyboard(recipe_id):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(text="✍️ Перезаписать шаги", callback_data=f"change_steps_{recipe_id}"),
        InlineKeyboardButton(text="📖 Показать рецепт", callback_data=f"show_recipe_{recipe_id}")
        )
    return markup



@bot.message_handler(commands=['start'])  # обработка команды start
def start(message):
    user_id = message.chat.id
    message_id = message.message_id
    username = message.chat.username
    name = message.chat.first_name

    times = now_time()
    greeting = get_greeting(name)


    user = SQL_request("SELECT * FROM users WHERE id = ?", (user_id,))

    if not user:
        SQL_request("""INSERT INTO users (id, message, username, name, time_registration) 
            VALUES (?, ?, ?, ?, ?)""", (user_id, message_id+1, username, name, times))
        bot.send_message(user_id, text=f"Добро пожаловать, {name}!", reply_markup=keyboard_main)
        print(f"{LOG} Зарегистрирован новый пользователь")
    else:
        menu_id = SQL_request("SELECT message FROM users WHERE id = ?", (user_id,))  # получение id меню
        try: bot.delete_message(message.chat.id, menu_id[0])  # обработка ошибки, если чат пустой, но пользователь есть в базе
        except Exception as e: print(f"Ошибка: {e}")  # вывод текста ошибки
        SQL_request("""UPDATE users SET message = ? WHERE id = ?""", (message_id+1, user_id))  # добавление id нового меню
        bot.send_message(user_id, greeting, reply_markup=keyboard_main)
        print(f"{LOG} Пользователь уже существует")
    bot.delete_message(message.chat.id, message.message_id)