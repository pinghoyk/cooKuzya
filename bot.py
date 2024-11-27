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
                id INTEGER PRIMARY KEY,
                message INTEGER,
                username TEXT,
                name TEXT,
                time_registration TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS local_recipes (
                lr_id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_name TEXT,
                ingredients TEXT,
                instructions TEXT,
                user_id INTEGER,
                is_filled INTEGER DEFAULT 0,
                current_step INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS favorite_recipes (
                f_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                recipe_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id)
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
        SQL_request("UPDATE local_recipes SET recipe_name=? WHERE lr_id=? AND user_id=?", (recipe_name, recipe_id, user_id))
        current_step = SQL_request("SELECT current_step FROM local_recipes WHERE lr_id=? AND user_id=?", (recipe_id, user_id), fetchone=True)
        
        if current_step:
            current_step = current_step[0]
            if current_step == 2:
                bot.register_next_step_handler(message, handle_ingredients, message_id, recipe_id)
            elif current_step == 3:
                bot.register_next_step_handler(message, handle_steps, message_id, recipe_id)
        return

    # Проверка, что рецепт принадлежит пользователю
    recipe = SQL_request("SELECT lr_id, current_step FROM local_recipes WHERE user_id=? AND is_filled=0", (user_id,), fetchone=True)

    if recipe:
        # Если рецепт существует, обновляем его название и сбрасываем шаг на 1
        recipe_id, current_step = recipe
        SQL_request("UPDATE local_recipes SET recipe_name=?, current_step=1 WHERE lr_id=? AND user_id=?", (recipe_name, recipe_id, user_id))
    else:
        # Если рецепта нет, создаем новый
        SQL_request("INSERT INTO local_recipes (recipe_name, user_id, is_filled, current_step) VALUES (?, ?, 0, 1)", (recipe_name, user_id))
        recipe_id = SQL_request("SELECT last_insert_rowid()", fetchone=True)[0]

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="✍️ Перезаписать название", callback_data=f"change_name_{recipe_id}"))

    bot.edit_message_text(text=f"Название: <b>{recipe_name}</b>\n\nКузя записывает состав:", chat_id=user_id, message_id=message_id, reply_markup=markup, parse_mode="HTML")

    recipe_id = SQL_request("SELECT lr_id FROM local_recipes WHERE user_id=? AND is_filled=0", (user_id,), fetchone=True)[0]
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
        SQL_request("UPDATE local_recipes SET ingredients=? WHERE lr_id=? AND user_id=?", (ingredients, recipe_id, user_id))
        bot.register_next_step_handler(message, handle_steps, message_id, recipe_id)
        return

    recipe = SQL_request("SELECT lr_id, current_step FROM local_recipes WHERE lr_id=? AND user_id=? AND is_filled=0", (recipe_id, user_id), fetchone=True)

    if recipe:
        SQL_request("UPDATE local_recipes SET ingredients=?, current_step=2 WHERE lr_id=? AND user_id=?", (ingredients, recipe_id, user_id))

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(text="✍️ Перезаписать состав", callback_data=f"change_ingredients_{recipe_id}"))

        bot.edit_message_text(f"<b>Состав:</b> {ingredients}\n\nКузя готов записать шаги! Введите их, каждый на новой строке:", chat_id=user_id, message_id=message_id, reply_markup=markup, parse_mode="HTML")

        bot.delete_message(chat_id=user_id, message_id=message.message_id)
        bot.register_next_step_handler(message, handle_steps, message_id, recipe_id)


# Получение шагов рецепта
def handle_steps(message, message_id, recipe_id, edit_mode=False, attempt=1):
    user_id = message.chat.id
    instructions = message.text.strip()

    if instructions.lower() == '/start':
        start(message)
        return

    steps = [step.strip() for step in instructions.split("\n") if step.strip()]

    if len(steps) < 2:
        response_text = (
            "Кузя ждет хотя бы два шага! Введите их снова (каждый шаг с новой строки):"
            if attempt == 1 else
            "Кузя снова напоминает: нужно хотя бы два шага! Попробуйте еще раз:"
        )
        bot.edit_message_text(chat_id=user_id, message_id=message_id, text=response_text)
        bot.register_next_step_handler(message, handle_steps, message_id, recipe_id, edit_mode, attempt + 1)
        return

    formatted_instructions = "\n".join(steps)

    if edit_mode:
        SQL_request("UPDATE local_recipes SET instructions=? WHERE lr_id=? AND user_id=?", (formatted_instructions, recipe_id, user_id))
    else:
        SQL_request("UPDATE local_recipes SET instructions=?, is_filled=1, current_step=3 WHERE lr_id=? AND user_id=?", (formatted_instructions, recipe_id, user_id))

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(text="✍️ Перезаписать шаги", callback_data=f"change_steps_{recipe_id}"),
        InlineKeyboardButton(text="📔 Показать рецепт", callback_data=f"show_recipe_{recipe_id}")
    )

    bot.edit_message_text(f"<b>Шаги:</b>\n{formatted_instructions}\n\nКузя выдохнул... рецепт писать больше не нужно было!", chat_id=user_id, message_id=message_id, reply_markup=markup, parse_mode="HTML")
    bot.delete_message(chat_id=user_id, message_id=message.message_id)


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


# Создает меню для показа рецептов с пагинацией
def generate_recipe_menu(user_id, page=1, limit=10, show_favorites=False):
    offset = (page - 1) * limit

    if show_favorites:
        # Запрос для получения списка избранных рецептов
        query = """
            SELECT lr.lr_id, lr.recipe_name 
            FROM favorite_recipes fr 
            JOIN local_recipes lr ON fr.recipe_id = lr.lr_id 
            WHERE fr.user_id = ? AND lr.is_filled = 1 
            LIMIT ? OFFSET ?
        """
        recipes = SQL_request(query, (user_id, limit, offset))
        
        # Запрос для подсчета общего количества избранных рецептов
        total_recipes_query = """
            SELECT COUNT(*) 
            FROM favorite_recipes fr 
            JOIN local_recipes lr ON fr.recipe_id = lr.lr_id 
            WHERE fr.user_id = ? AND lr.is_filled = 1
        """
        total_recipes = SQL_request(total_recipes_query, (user_id,), fetchone=True)[0]
    else:
        # Запрос для получения обычных рецептов
        query = """
            SELECT lr_id, recipe_name 
            FROM local_recipes 
            WHERE is_filled = 1 AND user_id = ? 
            LIMIT ? OFFSET ?
        """
        recipes = SQL_request(query, (user_id, limit, offset))
        
        # Запрос для подсчета общего количества обычных рецептов
        total_recipes_query = """
            SELECT COUNT(*) 
            FROM local_recipes 
            WHERE is_filled = 1 AND user_id = ?
        """
        total_recipes = SQL_request(total_recipes_query, (user_id,), fetchone=True)[0]


    if not recipes:
        return None

    total_pages = (total_recipes + limit - 1) // limit  # Вычисляем общее количество страниц
    keyboard = InlineKeyboardMarkup(row_width=3)

    for recipe_id, recipe_name in recipes:
        keyboard.add(InlineKeyboardButton(text=recipe_name, callback_data=f"recipe_{recipe_id}"))

    pagination_buttons = []

    if total_pages > 1:
        if page == 1:
            pagination_buttons.append(InlineKeyboardButton("«", callback_data="btn_back"))
        if page > 1:
            pagination_buttons.append(InlineKeyboardButton("«", callback_data=f"page_{page-1}"))
        pagination_buttons.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="zaglushka"))
        if page < total_pages:
            pagination_buttons.append(InlineKeyboardButton("»", callback_data=f"page_{page+1}"))
        if page == total_pages:
            pagination_buttons.append(InlineKeyboardButton("»", callback_data=f"btn_back"))
    else:
        if page == 1:
            pagination_buttons.append(InlineKeyboardButton("«", callback_data="btn_back"))
        if page > 1:
            pagination_buttons.append(InlineKeyboardButton("«", callback_data=f"page_{page-1}"))
        pagination_buttons.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="zaglushka"))
        if page < total_pages:
            pagination_buttons.append(InlineKeyboardButton("»", callback_data=f"page_{page+1}"))


    if pagination_buttons:
        keyboard.row(*pagination_buttons)

    return keyboard


def send_recipe_menu(call, user_id, show_favorites=False, page=1):
    keyboard = generate_recipe_menu(user_id, page=page, limit=10, show_favorites=show_favorites)
    if keyboard:
        text = "Ваши избранные рецепты:" if show_favorites else "Ваши рецепты:"
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=keyboard)
    else:
        text = "Кузя взял тетрадь, но она пуста! 😅" if not show_favorites else "Кузе ничего не нравится!"
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=keyboard_markup)


# Показ содержимого рецепта
def generate_recipe_screen(recipe_id, user_id, step=0):
    query = "SELECT recipe_name, ingredients, instructions FROM local_recipes WHERE lr_id = ? AND user_id = ?"
    recipe = SQL_request(query, (recipe_id, user_id), fetchone=True)

    if not recipe:
        return None, "Рецепт не найден."

    recipe_name, ingredients, instructions = recipe
    instructions = instructions.split("\n")  # Разделяем шаги на список
    total_steps = len(instructions)
    keyboard = InlineKeyboardMarkup(row_width=1)


    # Первый экран: название и состав
    if step == 0:
        text = f"Рецепт: <b>{recipe_name}</b>\n\n<b>Ингредиенты:</b>\n{ingredients}"
        
        # Проверяем, есть ли рецепт в избранном
        query = "SELECT 1 FROM favorite_recipes WHERE user_id = ? AND recipe_id = ?"
        is_favorite = SQL_request(query, (user_id, recipe_id), fetchone=True) is not None
        favorite_button_text = "❤️ В избранном" if is_favorite else "🤍 В избранное"
        
        # Добавляем кнопку "В избранное" или "Удалить из избранного"
        keyboard.add(InlineKeyboardButton(favorite_button_text, callback_data=f"fav_{recipe_id}_{int(is_favorite)}"),)

        if not is_favorite:
            keyboard.add(InlineKeyboardButton("✍️ Изменить", callback_data=f"edit_{recipe_id}"))
        if is_favorite: # Если рецепт в избранном, назад ведет к меню избранных
            keyboard.row(
                InlineKeyboardButton("«", callback_data="favorite_recipe"),  # Возврат в меню избранных рецептов
                InlineKeyboardButton("»", callback_data=f"step_{recipe_id}_1")
            )
        else: # Если рецепт не в избранном, назад ведет к меню создания рецепта
            keyboard.row(
                InlineKeyboardButton("«", callback_data="create_recipe"),  # Возврат на создание рецепта
                InlineKeyboardButton("»", callback_data=f"step_{recipe_id}_1")
            )

    else:
        current_step = instructions[step - 1]
        text = f"Шаг {step}/{total_steps}:\n{current_step}"
        nav_buttons = []
        if step == 1:
            nav_buttons.append(InlineKeyboardButton("«", callback_data=f"step_{recipe_id}_{step - 1}"))
        if step > 1:
            nav_buttons.append(InlineKeyboardButton("«", callback_data=f"step_{recipe_id}_{step - 1}"))
        if step < total_steps:
            nav_buttons.append(InlineKeyboardButton("»", callback_data=f"step_{recipe_id}_{step + 1}"))
        else:
            nav_buttons.append(InlineKeyboardButton("Готово ✅", callback_data="btn_back"))
        keyboard.row(*nav_buttons)

    return keyboard, text


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


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    print(f"Вызов: {call.data}")
    user_id = call.message.chat.id
    name = call.message.chat.first_name
    message_id = call.message.message_id

    if call.data == 'my_recipe':
        bot.edit_message_text(chat_id=user_id, message_id=message_id, text="Ваши рецепты", reply_markup=keyboard_recipes)


    elif call.data == "btn_back":
        bot.edit_message_text(chat_id=user_id, message_id=message_id, text="Ваши рецепты", reply_markup=keyboard_recipes)

    if call.data == "add_recipe":
        unfinished_recipe = SQL_request("SELECT lr_id FROM local_recipes WHERE user_id=? AND is_filled=0", (user_id,), fetchone=True)

        if unfinished_recipe:
            recipe_id = unfinished_recipe[0]
            
            markup = InlineKeyboardMarkup(row_width=2)
            markup.add(
                InlineKeyboardButton(text="🖊 Дописать", callback_data=f"continue_recipe_{recipe_id}"),
                InlineKeyboardButton(text="🗑 Стереть", callback_data=f"cancel_recipe_{recipe_id}")
            )
            
            bot.edit_message_text("Кузя не дописал рецепт. Что с ним сделать?", chat_id=user_id, message_id=message_id, reply_markup=markup)
        else:
            # Если нет незавершенных рецептов, начинаем новый
            bot.edit_message_text("Кузя записывает название рецепта:", chat_id=user_id, message_id=message_id, reply_markup=keyboard_markup)
            bot.register_next_step_handler(call.message, handle_name, message_id)


    elif call.data.startswith("continue_recipe_"):
        try:
            user_id = call.message.chat.id
            message_id = call.message.message_id
            recipe_id = int(call.data.split("_")[2])

            # Загружаем текущий шаг рецепта
            current_step = SQL_request("SELECT current_step FROM local_recipes WHERE lr_id=?", (recipe_id,), fetchone=True)
            current_step = current_step[0]

            if current_step == 1:
                # Получаем название рецепта
                recipe_name = SQL_request("SELECT recipe_name FROM local_recipes WHERE lr_id=?", (recipe_id,), fetchone=True)[0]
                markup = get_name_keyboard(recipe_id)  # Клавиатура для этапа ввода названия

                bot.edit_message_text(text=f"Название: <b>{recipe_name}</b>\n\nКузя записывает состав:", chat_id=user_id, message_id=message_id, reply_markup=markup, parse_mode="HTML")
                bot.register_next_step_handler(call.message, handle_ingredients, message_id, recipe_id)

            elif current_step == 2:
                # Получаем список ингредиентов
                ingredients = SQL_request("SELECT ingredients FROM local_recipes WHERE lr_id=?", (recipe_id,), fetchone=True)[0]
                markup = get_ingredients_keyboard(recipe_id)  # Клавиатура для этапа ввода ингредиентов

                bot.edit_message_text(
                    text=f"<b>Состав:</b> {ingredients}\n\nКузя готов записать шаги! Введите их, каждый на новой строке:", chat_id=user_id, message_id=message_id, reply_markup=markup, parse_mode="HTML")
                bot.register_next_step_handler(call.message, handle_steps, message_id, recipe_id)

            elif current_step == 3:
                # Получаем шаги рецепта
                formatted_instructions = SQL_request("SELECT instructions FROM local_recipes WHERE lr_id=?", (recipe_id,), fetchone=True)[0]
                markup = get_steps_keyboard(recipe_id)  # Клавиатура для этапа завершения рецепта

                bot.edit_message_text(text=f"<b>Шаги:</b>\n{formatted_instructions}\n\nРецепт завершен!", chat_id=user_id, message_id=message_id, reply_markup=markup, parse_mode="HTML")

        except Exception as e:
            print(f"Ошибка в обработке continue_recipe_: {e}")


    elif call.data.startswith("change_name"):
        recipe_id = int(call.data.split("_")[2])
        bot.edit_message_text("Кузя забыл название рецепта, введи заново!", chat_id=user_id, message_id=message_id, reply_markup=keyboard_markup)
        bot.register_next_step_handler(call.message, handle_name, message_id, recipe_id)


    elif call.data.startswith("change_ingredients"):
        recipe_id = int(call.data.split("_")[2])
        bot.edit_message_text("Кузя забыл состав рецепта, введи заново!", chat_id=user_id, message_id=message_id, reply_markup=keyboard_markup)
        bot.register_next_step_handler(call.message, handle_ingredients, message_id, recipe_id)


    if call.data.startswith("change_steps"):
        recipe_id = int(call.data.split("_")[2])
        current_steps = SQL_request("SELECT instructions FROM local_recipes WHERE lr_id=?", (recipe_id,), fetchone=True)[0]
        bot.edit_message_text(f"Кузя не может вспомнить шаги! Введи их (минимум два шага, каждый с новой строки):",chat_id=user_id, message_id=message_id)
        bot.register_next_step_handler(call.message, handle_steps, message_id=message_id, recipe_id=recipe_id, edit_mode=True)


    elif call.data.startswith("show_recipe"):
        recipe_id = int(call.data.split("_")[2])
        recipe = SQL_request("SELECT recipe_name, instructions, ingredients FROM local_recipes WHERE lr_id=? AND user_id=?", (recipe_id, user_id), fetchone=True)

        if recipe:
            recipe_name, ingredients, instructions = recipe

            markup = InlineKeyboardMarkup(row_width=1)
            markup.add(
                InlineKeyboardButton(text="💾 Записать", callback_data=f"save_recipe_{recipe_id}"),
                InlineKeyboardButton(text="🗑 Стереть", callback_data=f"cancel_recipe_{recipe_id}")
            )

            bot.edit_message_text(chat_id=user_id, message_id=message_id, text=f"Готовый рецепт!\n\n<b>{recipe_name}</b>\n\n<b>Состав:</b>\n{instructions}\n\n<b>Описание:</b>\n{ingredients}", reply_markup=markup,parse_mode="HTML")


    elif call.data.startswith("cancel_recipe_"):
        try:
            recipe_id = int(call.data.split("_")[2])
            SQL_request("DELETE FROM local_recipes WHERE lr_id=? AND user_id=?", (recipe_id, user_id))

            # Уведомляем пользователя об успешной отмене
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Кузя передумал, рецепт не сохранен!")
            bot.edit_message_text(chat_id=user_id, message_id=message_id, text="Ваши рецепты", reply_markup=keyboard_recipes)

        except Exception as e:
            print(f"Ошибка при удалении рецепта: {e}")


    elif call.data.startswith("save_recipe_"):
        try:
            recipe_id = int(call.data.split("_")[2])
            SQL_request("UPDATE local_recipes SET current_step=3, is_filled=1 WHERE lr_id=? AND user_id=?", (recipe_id, user_id))
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Рецепт сохранен, Кузя доволен!")
            bot.edit_message_text(chat_id=user_id, message_id=message_id, text="Ваши рецепты", reply_markup=keyboard_recipes)
        except Exception as e:
            print(f"Ошибка при сохранении рецепта: {e}")


    if call.data.startswith("page_"):
        page = int(call.data.split("_")[1])
        send_recipe_menu(call, user_id=call.from_user.id, show_favorites=False, page=page)


    if call.data.startswith("recipe_"):
        recipe_id = int(call.data.split("_")[1])
        keyboard, text = generate_recipe_screen(recipe_id, user_id=call.from_user.id, step=0)
        if keyboard:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=keyboard, parse_mode="HTML")
        else:
            print(call.id, "Рецепт не найден.")


    if call.data == "create_recipe":
        send_recipe_menu(call, user_id=call.from_user.id)


    if call.data == "favorite_recipe":
        send_recipe_menu(call, user_id=call.from_user.id, show_favorites=True, page=1)


    if call.data.startswith("step_"):
        _, recipe_id, step = call.data.split("_")
        recipe_id, step = int(recipe_id), int(step)
        keyboard, text = generate_recipe_screen(recipe_id, user_id=call.from_user.id, step=step)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=keyboard, parse_mode="HTML")


    if call.data.startswith("fav_"):
        parts = call.data.split("_")
        if len(parts) != 3:
            raise ValueError("Invalid callback data format. Expected format: fav_<recipe_id>_<is_favorite>")

        _, recipe_id, is_favorite = parts
        recipe_id = int(recipe_id)  # Преобразуем ID рецепта в число
        is_favorite = bool(int(is_favorite))  # Преобразуем статус в булево значение

        # Работа с базой данных: добавление или удаление рецепта из избранного
        if is_favorite:
            query = "DELETE FROM favorite_recipes WHERE user_id = ? AND recipe_id = ?"
            SQL_request(query, (call.from_user.id, recipe_id))
            is_favorite = False  # После удаления, состояние изменяется
        else:
            query = "INSERT INTO favorite_recipes (user_id, recipe_id) VALUES (?, ?)"
            SQL_request(query, (call.from_user.id, recipe_id))
            is_favorite = True  # После добавления, состояние изменяется

        # Генерируем текст для кнопки
        favorite_button_text = "❤️ В избранном" if is_favorite else "🤍 В избранное"
        # Получаем текущую клавиатуру
        current_keyboard = call.message.reply_markup.keyboard

        # Заменяем только кнопку "В избранное" на обновленную
        for row in current_keyboard:
            for button in row:
                if button.callback_data and button.callback_data.startswith("fav_"):
                    button.text = favorite_button_text
                    button.callback_data = f"fav_{recipe_id}_{int(is_favorite)}"

        # Обновляем клавиатуру
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=InlineKeyboardMarkup(current_keyboard))


    if call.data == "zaglushka":
        bot.answer_callback_query(call.id, text="Ты что, серьезно? Нажал сюда... и что теперь? 😅")


    # edit budet!
    if call.data.startswith("edit_"):
        try:
            recipe_id = int(call.data.split("_")[1])
            user_id = call.message.chat.id

            # Получаем текущие данные рецепта
            recipe = SQL_request("SELECT recipe_name, ingredients, instructions FROM local_recipes WHERE lr_id=?", (recipe_id,), fetchone=True)
            if not recipe:
                bot.answer_callback_query(call.id, "Рецепт не найден!")
                return

            name, ingredients, instructions = recipe

            # Показываем меню выбора редактирования
            markup = InlineKeyboardMarkup(row_width=1)
            markup.add(
                InlineKeyboardButton("✏️ Название", callback_data=f"change_name_{recipe_id}"),
                InlineKeyboardButton("📋 Состав", callback_data=f"change_ingredients_{recipe_id}"),
                InlineKeyboardButton("📝 Шаги", callback_data=f"change_steps_{recipe_id}"),
                InlineKeyboardButton("🗑 Стереть", callback_data=f"cancel_recipe_{recipe_id}"),
                InlineKeyboardButton(text=" ◀️ Назад", callback_data="btn_back")
            )
            bot.edit_message_text(
                f"<b>Что изменить?</b>",
                chat_id=user_id,
                message_id=call.message.message_id,
                reply_markup=markup,
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Ошибка в edit_recipe: {e}")


    if call.data == "back_recipe":
        greeting = get_greeting(name)
        bot.edit_message_text(chat_id=user_id, message_id=message_id, text=greeting, reply_markup=keyboard_main)


print(f"{LOG}Бот запущен...")
bot.polling(none_stop=True)