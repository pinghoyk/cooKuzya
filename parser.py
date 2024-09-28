import requests
from bs4 import BeautifulSoup
import re

url = URL

# Функция для отправки запросов и получения данных
def sending_requests(URL):
    try:
        response = requests.get(URL)
        response.raise_for_status()  # Выбрасывает исключение для статусов ошибок (4xx, 5xx)
        return response  # Возвращает объект response для дальнейшего использования
    except requests.exceptions.RequestException as e:
        return None, f"Ошибка при запросе: {e}"








# Получение рецептов с сайта Povar.ru
def recipes_povar(URL):

    response = sending_requests(URL)  # Получаем response с помощью функции

    recipes_dict = {}  # Словарь для хранения данных

    if response is None:
        recipes_dict['Ошибка'] = "Не удалось получить данные"  # Если ошибка в запросе
    else:
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
                "steps_info" : steps_info,
            }
        else:
            recipes_dict['Ошибка'] = f"Ошибка при запросе: {response.status_code}"

        


    return recipes_dict


# олучение рецептов с сайта 1000menu
def recipes_menu(URL):
    response = sending_requests(URL)  # Получаем response с помощью функции

    recipes_menu_dict = {}  # Словарь для хранения данных

    if response is None:
        recipes_menu_dict['Ошибка'] = "Не удалось получить данные"  # Если ошибка в запросе
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

            # Итерируем по каждому элементу в списке ингредиентов
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



                # Добавляем ингредиент в ingredients_dict
                ingredients_dict.append({
                    "Ингредиент": div_link,
                    "Количество": div_kol,
                    "Единица": unit_name,
                    "Граммы": div_gr
                })

            # Заполняем recipes_menu_dict
            recipes_menu_dict[menu_zagolovok] = {
                "Изображение": menu_link,
                "Ингредиенты": ingredients_dict
            }
        else:
            recipes_menu_dict['Ошибка'] = f"Ошибка при запросе: {response.status_code}"

    return recipes_menu_dict 

# Запускаем функцию
result = recipes_menu("https://1000.menu/cooking/43425-kurica-po-taiski")
print(result)


# result = recipes_povar("https://povar.ru/recipes/kulebyaka_s_myasom-54393.html")
# print(result)

