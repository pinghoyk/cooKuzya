import requests
from bs4 import BeautifulSoup
import re

# Получение рецептов с сайта Povar
def get_recipe_from_povar(url): 
    response = requests.get(url)

    recipe_data = {}  # Словарь для хранения данных рецепта

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")

        # Получаем блок с контентом рецепта
        mega_container = soup.find("div", id="megaContainer")
        container = mega_container.find("div", id="container")
        main_wrapper = container.find("div", id="mainWrapper")
        recipe_section = main_wrapper.find("div", class_="cont_area hrecipe")

        # Название рецепта
        recipe_title = recipe_section.find("h1", class_="detailed").text.strip()

        # Изображение рецепта
        image_section = recipe_section.find("div", class_="bigImgBox")
        image_link = image_section.find("a")
        image = image_link.find("img", class_="photo")
        image_src = image.get('src')

        # Ингредиенты
        ingredients_wrapper = recipe_section.find("div", class_="ingredients_wrapper")
        ingredients_title = ingredients_wrapper.find("h2", class_="span").text.strip()

        # Список ингредиентов
        ingredients_list = ingredients_wrapper.find("ul", class_="detailed_ingredients no_dots")
        ingredients = []

        # Находим все ингредиенты
        ingredient_items = ingredients_list.find_all("li", class_="ingredient flex-dot-line")
        for ingredient_item in ingredient_items:
            ingredient_name = ingredient_item.find("span", class_="name").text.strip()

            # Проверка наличия значения и единицы измерения
            ingredient_quantity = ingredient_item.find("span", class_="value")
            ingredient_quantity = ingredient_quantity.text.strip() if ingredient_quantity else ""

            ingredient_unit = ingredient_item.find("span", class_="u-unit-name")
            ingredient_unit = ingredient_unit.text.strip() if ingredient_unit else ""

            # Добавляем ингредиент в список
            ingredients.append({
                "name": ingredient_name,
                "quantity": ingredient_quantity,
                "unit": ingredient_unit
            })

        # Заголовок с "Как приготовить"
        cook_instruction_title = recipe_section.find("h2", string=re.compile(r'Как приготовить')).text.strip()

        instruction_section = recipe_section.find("div", class_="instructions")
        instruction_steps = instruction_section.find_all("div", class_="instruction")

        # Список шагов с изображениями и описанием
        steps_info = []

        # Проход по всем шагам
        for step in instruction_steps:
            # Пытаемся найти изображение шага
            step_image_section = step.find("div", class_="detailed_step_photo_big")
            
            if step_image_section:  # Если изображение есть
                image_link = step_image_section.find("a", class_="stepphotos")
                if image_link:
                    step_image = image_link.find("img", class_="photo")
                    step_image_src = step_image.get('src') if step_image else None
                else:
                    step_image_src = None
            else:
                # Если изображения нет, находим номер шага
                step_number = step.find("div", class_="stepNumber")
                step_image_src = f"Шаг {step_number.text.strip()}" if step_number else "Нет изображения и номера шага"

            # Описание шага
            step_description = step.find("div", class_="detailed_step_description_big").text.strip() if step.find("div", class_="detailed_step_description_big") else "Нет описания"

            # Добавляем шаг в список
            steps_info.append({"image_or_step": step_image_src, "description": step_description})

        # Собираем все данные в словарь
        recipe_data = {
            "recipe_name": recipe_title,
            "image_url": image_src,
            ingredients_title: ingredients,
            "instructions_title": cook_instruction_title,
            "steps": steps_info
        }

    else:
        recipe_data['error'] = f"Ошибка при запросе: {response.status_code}"

    return recipe_data


result = get_recipe_from_povar("https://povar.ru/recipes/kulebyaka_s_myasom-54393.html")
print(result)
