import requests
from bs4 import BeautifulSoup
import re

# url = URL

# Функция для отправки запросов и получения данных
def sending_requests(URL):
    try:
        response = requests.get(URL)
        response.raise_for_status()  # Выбрасывает исключение для статусов ошибок (4xx, 5xx)
        return response  # Возвращает объект response для дальнейшего использования
    except requests.exceptions.RequestException as e:
        return None, f"Ошибка при запросе: {e}"


# Получение рецептов с сайта Povar.ru
def get_recipes_povar(URL):
    response = sending_requests(URL)

    povar_dict = {}  # Словарь для хранения данных

    if response is None:
        povar_dict['Ошибка'] = "Не удалось получить данные"
    else:
        if response.status_code == 200:
            soap = BeautifulSoup(response.text, "html.parser")

            # Получаем все необходимые блоки с контентом
            povar_megaContainer = soap.find("div", id="megaContainer")
            povar_container = povar_megaContainer.find("div", id="container")
            povar_wrap = povar_container.find("div", id="mainWrapper")
            povar_area = povar_wrap.find("div", class_="cont_area hrecipe")

            # Название рецепта
            recipe_name = povar_area.find("h1", class_="detailed").text.strip()

            # Поиск изображения
            povar_img_area = povar_area.find("div", class_="bigImgBox")
            povar_link_img = povar_img_area.find("a")
            povar_img = povar_link_img.find("img", class_="photo")
            img_src = povar_img.get('src')

            # Ингредиенты
            povar_ingr = povar_area.find("div", class_="ingredients_wrapper")
            recipe_ingr_name = povar_ingr.find("h2", class_="span").text.strip()

            # Получаем все ингредиенты
            ingrs = povar_ingr.find("ul", class_="detailed_ingredients no_dots")
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
            recipe_cook = povar_area.find("h2", string=re.compile(r'Как приготовить')).text.strip()

            recipe_prepare = povar_area.find("div", class_="instructions")
            recipe_steps = recipe_prepare.find_all("div", class_="instruction")

            # Список для хранения шагов с изображениями и текстом
            steps_info = []

            # Проход по всем шагам
            for step in recipe_steps:
                # Пытаемся найти изображение
                step_img = step.find("div", class_="detailed_step_photo_big")
                
                if step_img:
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
            # povar_dict = {
            #     "recipe": recipe_name,
            #     "img": img_src,
            #     recipe_ingr_name : ingr_list,
            #     "how_cook" : recipe_cook,
            #     "steps_info" : steps_info,
            # }
        else:
            povar_dict['Ошибка'] = f"Ошибка при запросе: {response.status_code}"
    return povar_dict


# Получение рецептов с сайта 1000.menu
def get_recipes_menu(URL):
    response = sending_requests(URL)

    menu_dict = {}  # Словарь для хранения данных

    if response is None:
        menu_dict['Ошибка'] = "Не удалось получить данные"
    else:
        if response.status_code == 200:
            soap = BeautifulSoup(response.text, "html.parser")

            # Перехожу в сам рецепт
            menu_block = soap.find("div", id="main")
            menu_container = menu_block.find("div", class_="container")
            menu_main = menu_container.find("main", class_="column")

            # Название рецепта
            menu_zagolovok = menu_main.find("h1").text.strip()

            # Перехожу в блок с картинками и составом
            menu_content = menu_main.find("div", class_="content")
            menu_section = menu_content.find("section", id="pt_info")
            menu_recipe = menu_section.find("div", class_="recipe-top columns")

            # Получаю два блока
            menu_halfs = menu_recipe.find_all("div", class_="column is-half clf")

            # Получаю картинку
            container_photo = menu_halfs[0]
            carousel_photo = container_photo.find("div", class_="carousel-wrap wide-box is-flex pb-2 noprint")
            menu_img = carousel_photo.find("a", class_="foto_gallery bl")
            menu_link = menu_img.get("href")

            # Получаю рецепт
            container_recipe = menu_halfs[1]
            ingr_menu = container_recipe.find("div", id="ingredients")

            # Создаем список для хранения ингредиентов
            ingredients_dict = []

            # Находим все <div> с ингредиентами
            div_ingr = ingr_menu.find_all("div", class_="ingredient list-item")

            for ingredient in div_ingr:
                # Получение названия ингредиента
                div_name = ingredient.find("div", class_="list-column align-top")
                div_link = div_name.find("a", class_="name").text.strip()

                # Получение количества продукта
                span_kol = div_name.find("span", class_="ingredient-info mr-1")
                div_kol = span_kol.text.strip() if span_kol else None

                # Получение единицы измерения
                div_unit = ingredient.find("div", class_="list-column no-shrink")
                unit_name = div_unit.find("span", class_="squant value").text.strip() if div_unit else None

                change_gr = div_unit.find("select", class_="recalc_s_num") if div_unit else None
                if change_gr:
                    ingr_gr = change_gr.find("option", attrs={"selected": True})
                    div_gr = ingr_gr.text.strip() if ingr_gr else None
                else:
                    div_gr = None

                # Добавляем ингредиент в список
                ingredients_dict.append({
                    "ingr": div_link,
                    "addition": div_kol,
                    "col": unit_name,
                    "unit": div_gr
                })

                menu_sectionSteps = menu_section.find("section", id="pt_steps")

                zagolovok_step = menu_sectionSteps.find("h2").text.strip()

                menu_instr = menu_sectionSteps.find("ol", class_="instructions")
                menu_li = menu_instr.find_all("li")

                steps = []  # Список для хранения всех шагов

            








            # Заполняем recipes_menu_dict
            menu_dict[menu_zagolovok] = {
                "Изображение": menu_link,
                "Ингредиенты": ingredients_dict
            }
        else:
            menu_dict['Ошибка'] = f"Ошибка при запросе: {response.status_code}"

    return menu_dict 

# Запускаем функцию
result = get_recipes_menu("https://1000.menu/cooking/43425-kurica-po-taiski")
print(result)


# result = get_recipes_povar("https://povar.ru/recipes/kulebyaka_s_myasom-54393.html")
# print(result)

