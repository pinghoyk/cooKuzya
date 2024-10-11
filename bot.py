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

recipe_data = {}
current_steps = {}


# Кнопки
buttons_main = [
    InlineKeyboardButton(text=" 📖 Мои рецепты", callback_data="my_recipe"),
    # InlineKeyboardButton(text="🥕 По ингредиентам", callback_data="recipe_ingredients"),
    # InlineKeyboardButton(text="💡 Советы", callback_data="culinary_tips"),
    # InlineKeyboardButton(text="📂 Категории", callback_data="recipe_category"),   
    # InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
    # InlineKeyboardButton(text="🎲 Случайные", callback_data="recipe_random"),
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
                users_id INTEGER PRIMARY KEY AUTOINCREMENT,
                messages_id INTEGER,
                tg_id INTEGER,
                tg_username TEXT,
                tg_first_name TEXT,
                time_registration TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS local_recipes (
                local_recipes_id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_name TEXT,
                ingredients TEXT,
                instructions TEXT,
                tg_id INTEGER,
                FOREIGN KEY (tg_id) REFERENCES users (tg_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS internet_recipes (
                internet_recipes_id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                tg_id INTEGER,
                FOREIGN KEY (tg_id) REFERENCES users (tg_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS favorite_recipes (
                favorite_id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_id INTEGER,
                recipe_id INTEGER,
                recipe_type TEXT,
                FOREIGN KEY (tg_id) REFERENCES users (tg_id)
            );

        """)
        
        conn.commit()
    print(f"{LOG}База данных успешно инициализирована!")
except sqlite3.Error as e:
    print(f"{LOG}Ошибка при работе с базой данных: {e}")


# ФУНКЦИИ
# Подключение к бд
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


# Получение приветствия в зависимости от времени суток
def get_greeting(first_name):
    current_hour = datetime.now(pytz.timezone('Asia/Yekaterinburg')).hour
    if 5 <= current_hour < 12:
        return f"Доброе утро, {first_name}!"
    elif 12 <= current_hour < 18:
        return f"Добрый день, {first_name}!"
    elif 18 <= current_hour < 23:
        return f"Добрый вечер, {first_name}!"
    else:
        return f"Доброй ночи, {first_name}!"

# Получение времени
def now_time():
    return datetime.now(pytz.timezone('Asia/Yekaterinburg')).strftime("%Y-%m-%d %H:%M:%S")


# Получаем название рецепта
def handle_name(message, message_id):
    recipe_name = message.text
    tg_id = message.chat.id

    # Попытка удалить сообщение пользователя, если оно существует
    try:
        bot.delete_message(chat_id=tg_id, message_id=message.message_id)
    except telebot.apihelper.ApiTelegramException as e:
        print(f"Ошибка при удалении сообщения: {str(e)}")

    # Сохраняем название рецепта в словаре
    recipe_data[tg_id] = {"name": recipe_name}

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="✏️ Изменить", callback_data="change_name"))

    new_message_text = f"Название рецепта: {recipe_data[tg_id]['name']}\n\nВведите состав:"

    # Попытка редактирования сообщения
    try:
        bot.edit_message_text(
            new_message_text,
            chat_id=tg_id,
            message_id=message_id,
            reply_markup=markup
        )
    except telebot.apihelper.ApiTelegramException as e:
        print(f"Ошибка при редактировании сообщения: {str(e)}")

    bot.register_next_step_handler_by_chat_id(tg_id, handle_ingredients, message_id)

# Получаем состав рецепта
def handle_ingredients(message, message_id):
    tg_id = message.chat.id
    ingredients = message.text

    try:
        bot.delete_message(chat_id=tg_id, message_id=message.message_id)
    except telebot.apihelper.ApiTelegramException as e:
        print(f"Ошибка при удалении сообщения: {str(e)}")

    # Сохраняем ингредиенты в словаре
    recipe_data[tg_id]["ingredients"] = ingredients

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="✏️ Изменить", callback_data="change_ingredients"))

    try:
        bot.edit_message_text(
            f"Название рецепта: {recipe_data[tg_id]['name']}\nСостав: {recipe_data[tg_id]['ingredients']}\n\nУкажите шаги приготовления, записывая каждый шаг на новой строке:",
            chat_id=tg_id,
            message_id=message_id,
            reply_markup=markup
        )
    except telebot.apihelper.ApiTelegramException as e:
        print(f"Ошибка при редактировании сообщения: {str(e)}")

    bot.register_next_step_handler_by_chat_id(tg_id, handle_steps, message_id)

# Получаем шаги рецепта
def handle_steps(message, message_id):
    tg_id = message.chat.id
    steps = message.text

    try:
        bot.delete_message(chat_id=tg_id, message_id=message.message_id)
    except telebot.apihelper.ApiTelegramException as e:
        print(f"Ошибка при удалении сообщения: {str(e)}")

    # Разделяем шаги по новой строке и убираем лишние пробелы
    steps = steps.strip().split("\n")
    
    if len(steps) < 2:
        try:
            bot.edit_message_text(
                chat_id=tg_id, 
                message_id=message_id, 
                text="Пожалуйста, введите хотя бы два шага."
            )
        except telebot.apihelper.ApiTelegramException as e:
            print(f"Ошибка при редактировании сообщения: {str(e)}")
        
        bot.register_next_step_handler_by_chat_id(tg_id, handle_steps, message_id)
        return
    
    # Сохраняем шаги в словаре
    recipe_data[tg_id]["steps"] = [f"Шаг {i+1}: {step.strip()}" for i, step in enumerate(steps)]

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(text="✏️ Изменить", callback_data="change_steps")
    )
    markup.add(
        InlineKeyboardButton(text="✅ Сохранить", callback_data="save_recipe"),
        InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_recipe")
    )

    try:
        bot.edit_message_text(
            chat_id=tg_id, 
            message_id=message_id,
            text=f"Рецепт: {recipe_data[tg_id]['name']}\n\nСостав:\n{recipe_data[tg_id]['ingredients']}\n\nОписание приготовления:\n" + "\n".join(recipe_data[tg_id]["steps"]),
            reply_markup=markup
        )
    except telebot.apihelper.ApiTelegramException as e:
        print(f"Ошибка при редактировании сообщения: {str(e)}")







# Функция для получения рецептов с пагинацией
def show_recipes_with_pagination(user_id, call, page=1):
    global recipe_keyboard  

    limit = 5
    offset = (page - 1) * limit

    user_recipes = SQL_request("SELECT id, recipe_name FROM recipes WHERE user_id = ? LIMIT ? OFFSET ?", (user_id, limit, offset))
    
    total_recipes = SQL_request("SELECT COUNT(*) FROM recipes WHERE user_id = ?", (user_id,))[0][0]  # Всего рецептов
    total_pages = (total_recipes + limit - 1) // limit 

    if user_recipes:
        markup_recipes = InlineKeyboardMarkup()

        # Добавляем рецепты текущей страницы в кнопки
        for recipe in user_recipes:
            recipe_id = recipe[0]
            recipe_name = recipe[1]
            markup_recipes.add(InlineKeyboardButton(text=recipe_name, callback_data=f"view_recipe_{recipe_id}"))

        # Добавляем кнопки "Назад" и "Вперед" для пагинации
        navigation_buttons = []
        if page > 1:
            navigation_buttons.append(InlineKeyboardButton(text=" ◀️  Назад", callback_data=f"recipes_page_{page - 1}"))
        else:
            navigation_buttons.append(InlineKeyboardButton(text=" ◀️  Назад", callback_data="btn_back"))

        if page < total_pages:
            navigation_buttons.append(InlineKeyboardButton(text=" ▶️ Вперед", callback_data=f"recipes_page_{page + 1}"))

        markup_recipes.row(*navigation_buttons)
        recipe_keyboard = markup_recipes

        bot.edit_message_text("Ваши рецепты:", user_id, call.message.message_id, reply_markup=markup_recipes)
    else:
        bot.edit_message_text("У вас нет сохраненных рецептов:(", user_id, call.message.message_id, reply_markup=keyboard_markup)


def show_favorites_with_pagination(user_id, call, page=1):
    global favorite_keyboard  

    limit = 5
    offset = (page - 1) * limit

    user_favorites = SQL_request("""
            SELECT f.id, r.id AS recipe_id, r.recipe_name 
            FROM favorites f 
            JOIN recipes r ON f.recipe_id = r.id 
            WHERE f.user_id = ? 
            LIMIT ? OFFSET ?
    """, (user_id, limit, offset))
    
    total_favorites = SQL_request("SELECT COUNT(*) FROM favorites WHERE user_id = ?", (user_id,))[0][0]
    total_pages = (total_favorites + limit - 1) // limit 

    if user_favorites:
        markup_favorites = InlineKeyboardMarkup()

        # Добавляем рецепты текущей страницы в кнопки
        for favorite in user_favorites:
            favorite_id = favorite[0]
            recipe_id = favorite[1]
            recipe_name = favorite[2]
            markup_favorites.add(InlineKeyboardButton(text=recipe_name, callback_data=f"view_favorite_recipe_{recipe_id}"))

        navigation_buttons = []
        if page > 1:
            navigation_buttons.append(InlineKeyboardButton(text=" ◀️  Назад", callback_data=f"favorites_page_{page - 1}"))
        else:
            navigation_buttons.append(InlineKeyboardButton(text=" ◀️  Назад", callback_data="btn_back"))

        if page < total_pages:
            navigation_buttons.append(InlineKeyboardButton(text=" ▶️ Вперед", callback_data=f"favorites_page_{page + 1}"))

        markup_favorites.row(*navigation_buttons)

        bot.edit_message_text("Ваши избранные рецепты:", user_id, call.message.message_id, reply_markup=markup_favorites)
    else:
        bot.edit_message_text("У вас нет избранных рецептов:(", user_id, call.message.message_id, reply_markup=keyboard_markup)





# Функция для получения рецепта
def get_recipe(recipe_id):
    return SQL_request("SELECT recipe_name, instructions FROM recipes WHERE id = ?", (recipe_id,))

# Функция для обновления сообщения с шагом рецепта и кнопками
def update_recipe_message(chat_id, message_id, recipe_name, steps, current_step, total_steps, recipe_id):
    buttons = []

    if current_step == 0:
        buttons.append(InlineKeyboardButton(text=" ◀️ Назад", callback_data=f"view_recipe_{recipe_id}"))
    else:
        buttons.append(InlineKeyboardButton(text=" ◀️ Назад", callback_data=f"step_prev_{recipe_id}_{current_step - 1}"))

    if current_step + 1 < total_steps:
        buttons.append(InlineKeyboardButton(text=" ▶ Далее", callback_data=f"step_next_{recipe_id}_{current_step + 1}"))
    else:
        buttons.append(InlineKeyboardButton(text="✅ Готово", callback_data="create_recipe"))

    bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=f"{recipe_name}\n\nШаг {current_step + 1}/{total_steps}:\n\n{steps[current_step]}",
        reply_markup=InlineKeyboardMarkup().add(*buttons)
    )







@bot.message_handler(commands=['start'])
def start(message):
      user_id = message.chat.id
      username = message.chat.username
      first_name = message.from_user.first_name

      # Проверяем, существует ли пользователь в базе данных
      user = SQL_request("SELECT * FROM users WHERE user_id = ?", (user_id,), fetchone=True)
      
      # Если пользователь не найден, регистрируем его
      if not user:
          SQL_request('INSERT INTO users (user_id, message, username, first_name, time_registration) VALUES (?, ?, ?, ?, ?)',
                      (user_id, message.message_id, username, first_name, now_time()))
          bot.send_message(user_id, f"Добро пожаловать, {first_name}!", reply_markup=keyboard_main)
          print(f"{LOG} Зарегистрирован новый пользователь")
      else:
          # Если пользователь найден, обновляем его данные
          SQL_request("UPDATE users SET message = ? WHERE user_id = ?", (message.message_id, user_id))
          greeting = get_greeting(first_name)
          bot.send_message(user_id, greeting, reply_markup=keyboard_main)
          print(f"{LOG} Пользователь уже существует")


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    print(f"Вызов: {call.data}")

    user_id = call.message.chat.id
    message_id = call.message.message_id
    first_name = call.message.chat.first_name

    if call.data == 'my_recipe':
        bot.edit_message_text("Ваши рецепты:", user_id, message_id, reply_markup=keyboard_recipes)

    elif call.data == "btn_back":
        bot.edit_message_text("Ваши рецепты:", user_id, message_id, reply_markup=keyboard_recipes)


    if call.data == "add_recipe":
        initial_message = bot.edit_message_text("Введите название рецепта:", chat_id=user_id, message_id=message_id, reply_markup=keyboard_markup)
        bot.register_next_step_handler(call.message, handle_name, initial_message.message_id)

    elif call.data == "save_recipe":
        if user_id in recipe_data:
            recipe = recipe_data[user_id]
            
            # Проверьте, есть ли все необходимые данные
            if 'name' in recipe and 'ingredients' in recipe and 'steps' in recipe:
                try:
                    SQL_request(
                        "INSERT INTO recipes (user_id, recipe_name, ingredients, instructions) VALUES (?, ?, ?, ?)",
                        (user_id, recipe['name'], recipe['ingredients'], "\n".join(recipe['steps']))
                    )

                    bot.edit_message_text(chat_id=user_id, message_id=message_id, text="Рецепт сохранен!")

                    bot.edit_message_text(chat_id=user_id, message_id=message_id, text="Ваши рецепты:", reply_markup=keyboard_recipes)

                except Exception as e:
                    print(f"Произошла ошибка при сохранении рецепта: {str(e)}")
            else:
                # Сообщение, если данные рецепта неполные
                bot.edit_message_text(chat_id=user_id, message_id=message_id, text="Недостаточно данных для сохранения рецепта.")
        else:
            # Если нет данных о рецепте для пользователя
            bot.edit_message_text(chat_id=user_id, message_id=message_id, reply_markup=keyboard_markup, text="Произошла ошибка сохранения. Пожалуйста, попробуйте снова.\n\nВведите название рецепта")
            bot.register_next_step_handler(call.message, handle_name, initial_message.message_id)

    elif call.data == "cancel_recipe":
        bot.edit_message_text(chat_id=user_id, message_id=message_id, text="Сохранение рецепта отменено.", reply_markup=keyboard_markup)

    elif call.data == "change_name":
        bot.edit_message_text(chat_id=user_id, message_id=message_id, text="Введите новое название рецепта:")
        bot.register_next_step_handler_by_chat_id(user_id, lambda message: handle_name(message, message_id))

    elif call.data == "change_ingredients":
        bot.edit_message_text(chat_id=user_id, message_id=message_id, text="Введите новый состав рецепта:")
        bot.register_next_step_handler_by_chat_id(user_id, lambda message: handle_ingredients(message, message_id))

    elif call.data == "change_steps":
        bot.edit_message_text(chat_id=user_id, message_id=message_id, text="Введите шаги приготовления (по одному на строку):")
        bot.register_next_step_handler_by_chat_id(user_id, lambda message: handle_steps(message, message_id))

    elif call.data == "back_recipe":
        greeting = get_greeting(first_name)
        bot.edit_message_text(greeting, chat_id=user_id, message_id=call.message.message_id, reply_markup=keyboard_main)


    if call.data == "create_recipe":
        show_recipes_with_pagination(user_id, call, page=1)

    elif call.data.startswith("recipes_page_"):
        page = int(call.data.split("_")[2])
        show_recipes_with_pagination(user_id, call, page)

    elif call.data.startswith("view_recipe_"):
        recipe_id = int(call.data.split("_")[2])
        recipe = SQL_request("SELECT recipe_name, ingredients, instructions FROM recipes WHERE id = ?", (recipe_id,))

        if recipe:
            recipe_name, ingredients, instructions = recipe[0]
            steps = instructions.split('\n')
            current_steps[user_id] = (recipe_id, 0)  # Начинаем с шага 0


            markup = InlineKeyboardMarkup(row_width=2)
            markup.add(InlineKeyboardButton(text=" 🤍 В избранное", callback_data="favorite"))
            markup.add(InlineKeyboardButton(text=" 🗑 Удалить", callback_data=f"delete_recipe_{recipe_id}"))

            markup.add(
                InlineKeyboardButton(text=" ◀️ Назад", callback_data=f"recipes_page_1"),
                InlineKeyboardButton(text=" ▶️ Далее", callback_data=f"start_recipe_{recipe_id}")
                )

            bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id, text=f"Рецепт: {recipe_name}\n\nСостав:\n{ingredients}\n\n", reply_markup=markup
            )
        else:
            bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id, text="Рецепт не найден.")

    # Обработка начала рецепта
    if call.data.startswith("start_recipe_"):
        recipe_id = int(call.data.split("_")[2])
        recipe = get_recipe(recipe_id)

        if recipe:
            recipe_name, instructions = recipe[0]
            steps = instructions.split('\n')
            total_steps = len(steps)

            # Отправляем сообщение с первым шагом
            bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=f"{recipe_name}\n\nШаг 1/{total_steps}:\n\n{steps[0]}",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton(text=" ◀️ Назад", callback_data=f"view_recipe_{recipe_id}"),
                    InlineKeyboardButton(text=" ▶ Далее", callback_data=f"step_next_{recipe_id}_1")
                )
            )

    # Обработка переходов по шагам рецепта
    elif call.data.startswith("step_next_") or call.data.startswith("step_prev_"):
        recipe_id, current_step = map(int, call.data.split("_")[2:])
        recipe = get_recipe(recipe_id)

        if recipe:
            recipe_name, instructions = recipe[0]
            steps = instructions.split('\n')
            total_steps = len(steps)

            if 0 <= current_step < total_steps:
                # Обновляем сообщение с текущим шагом
                update_recipe_message(user_id, message_id, recipe_name, steps, current_step, total_steps, recipe_id)
            else:
                bot.answer_callback_query(call.id, text="Некорректный шаг!")


    elif call.data.startswith("delete_recipe_"):
        try:
            recipe_id = int(call.data.split("_")[2])
            SQL_request("DELETE FROM recipes WHERE id = ?", (recipe_id,))

            bot.edit_message_text(chat_id=user_id, message_id=message_id, text="Рецепт удален!")

            # Проверяем, остались ли еще рецепты у пользователя
            remaining_recipes = SQL_request("SELECT COUNT(*) FROM recipes WHERE user_id = ?", (user_id,))[0][0]

            if remaining_recipes > 0:
                show_recipes_with_pagination(user_id, call)
            else:
                bot.edit_message_text(chat_id=user_id, message_id=message_id, text="У вас нет сохраненных рецептов :(", reply_markup=keyboard_markup)

        except (IndexError, ValueError):
            # Обрабатываем ошибку, если ID не найден или произошла другая ошибка
            bot.answer_callback_query(call.id, text="Ошибка удаления рецепта.")


            


print(f"{LOG}Бот запущен...")
bot.polling(none_stop=True)