import requests
from bs4 import BeautifulSoup
import re

# Получение рецептов с сайта Povar.ru
def recipes_povar(URL): 
    response = requests.get(URL)

    recipes_dict = {} # Словарь для хранения данных

    if response.status_code == 200:
        soap = BeautifulSoup(response.text, "html.parser")

        # Получаем все необходимые блоки с контентом
        recipes_povar = soap.find("div", id="megaContainer")
        recipe_container = recipes_povar.find("div", id="container")
        recipe_wrap = recipe_container.find("div", id="mainWrapper")
        recipe_area = recipe_wrap.find("div", class_="cont_area hrecipe")

        # Название рецепта
        recipe_name = recipe_area.find("h1", class_="detailed").text.strip()

        # Поиск изображения
        recipe_img_area = recipe_area.find("div", class_="bigImgBox")
        recipe_link_img = recipe_img_area.find("a")
        recipe_img = recipe_link_img.find("img", class_="photo")
        img_src = recipe_img.get('src')

        # Ингредиенты
        recipe_ingr = recipe_area.find("div", class_="ingredients_wrapper")
        recipe_ingr_name = recipe_ingr.find("h2", class_="span").text.strip()

        # Получаем все ингредиенты
        ingrs = recipe_ingr.find("ul", class_="detailed_ingredients no_dots")
        ingr_list = []

        # Находим все <li> с ингредиентами
        ingr_uls = ingrs.find_all("li", class_="ingredient flex-dot-line")
        for ingr_ul in ingr_uls:
            ingr_name = ingr_ul.find("span", class_="name").text.strip()  # Название ингредиента

            # Проверяем наличие значения и единицы измерения
            ingr_value = ingr_ul.find("span", class_="value")
            ingr_value = ingr_value.text.strip() if ingr_value else ""

            ingr_unit = ingr_ul.find("span", class_="u-unit-name")
            ingr_unit = ingr_unit.text.strip() if ingr_unit else ""

            # Добавляем ингредиент в список
            ingr_list.append({
                "name": ingr_name,
                "quantity": ingr_value,
                "unit": ingr_unit
            })

        # Поиск заголовка с названием "Как приготовить"
        recipe_cook = recipe_area.find("h2", string=re.compile(r'Как приготовить')).text.strip()

        recipe_prepare = recipe_area.find("div", class_="instructions")
        recipe_steps = recipe_prepare.find_all("div", class_="instruction")

        # Список для хранения шагов с изображениями и текстом
        steps_info = []

        # Проход по всем шагам
        for step in recipe_steps:
            # Пытаемся найти изображение
            step_img = step.find("div", class_="detailed_step_photo_big")
            
            if step_img:  # Если изображение есть
                img_link = step_img.find("a", class_="stepphotos")
                if img_link:
                    step_src = img_link.find("img", class_="photo")
                    if step_src:
                        step_link = step_src.get('src')
                    else:
                        step_link = None
                else:
                    step_link = None
            else:
                # Если изображений нет, ищем номер шага
                step_number = step.find("div", class_="stepNumber")
                if step_number:
                    step_link = f"Шаг {step_number.text.strip()}"
                else:
                    step_link = "Нет изображения и номера шага"

            # Получаем текст шага
            recipe_text = step.find("div", class_="detailed_step_description_big").text.strip() if step.find("div", class_="detailed_step_description_big") else "Нет описания"

            # Добавляем шаг в список
            steps_info.append({"image_or_step": step_link, "text": recipe_text})



        # Собираем все данные в словарь
        recipes_dict = {
            "recipe": recipe_name,
            "img": img_src,
            recipe_ingr_name : ingr_list,
            "cook" : recipe_cook,
            "steps_info" : steps_info

        }

    else:
        recipes_dict['Ошибка'] = f"Ошибка при запросе: {response.status_code}"

    return recipes_dict


result = recipes_povar("https://povar.ru/recipes/kulebyaka_s_myasom-54393.html")
print(result)

