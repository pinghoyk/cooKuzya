import requests
from bs4 import BeautifulSoup
import re



# Функция поиска рецептов по запросу
def search_recipes(keyword, max_pages=40):
  recipes = []
  base_url = "https://povar.ru/xmlsearch"
  response =  requests.get(base_url)

  for page in range(1, max_pages + 1):
      params = {
          "query": keyword,
          "page": page
      }

  if response.status_code == 200:
      soup = BeautifulSoup(response.text, 'html.parser')

      recipe_elements = soup.find_all('div', class_='recipe')    # поиск блоков с рецептами

      for element in recipe_elements:
        title_element = element.find('a', class_='listRecipieTitle')    # извлекаем название рецепта и ссылку
        title = title_element.text.strip()
        link = "https://povar.ru" + title_element['href']

        image_element = element.find('span', class_='thumb').find('img')    # извлекаем ссылку на изображение
        image_link = image_element['src'] if image_element else "Изображение не найдено"

        cook_time_element = element.find('div', class_='cook-time').find('span', class_='value')    # извлекаем время приготовления
        cook_time = cook_time_element.text.strip() if cook_time_element else "Не указано"

        owner_element = element.find('div', class_='owner').find('span')    # извлекаем автора
        author = owner_element.text.strip() if owner_element else "Не указано"

        # Добавляем данные в список
        recipes.append({
            "title": title,
            "link": link,
            "image_link": image_link,
            "cook_time": cook_time,
            "author": author
        })
  else:
        recipes['Ошибка'] = f"Ошибка при запросе: {response.status_code}"

  return recipes


# Функция показа рецепта
def get_recipes_povar(URL):
    url = URL
    response = requests.get(url)
    povar_dict = {}

    if response.status_code == 200:
        soap = BeautifulSoup(response.text, "html.parser")

        povar_megaContainer = soap.find("div", id="megaContainer")    # поиск блоков с рецептами
        povar_container = povar_megaContainer.find("div", id="container") if povar_megaContainer else None
        povar_wrap = povar_container.find("div", id="mainWrapper") if povar_container else None
        povar_area = povar_wrap.find("div", class_="cont_area hrecipe") if povar_wrap else None

        if not povar_area:
            return {"Ошибка": "Структура страницы изменилась, не удалось найти рецепт"}

        recipe_name = povar_area.find("h1", class_="detailed").text.strip() if povar_area.find("h1", class_="detailed") else "Название не найдено"    # название рецепта

        povar_img_area = povar_area.find("div", class_="bigImgBox")    # изображение рецепта
        povar_link_img = povar_img_area.find("a") if povar_img_area else None
        povar_img = povar_link_img.find("img", class_="photo") if povar_link_img else None
        img_src = povar_img.get('src') if povar_img else None

        povar_ingr = povar_area.find("div", class_="ingredients_wrapper")    # ингредиенты
        recipe_ingr_name = povar_ingr.find("h2", class_="span").text.strip() if povar_ingr else "Ингредиенты"

        ingr_list = []
        ingrs = povar_ingr.find("ul", class_="detailed_ingredients no_dots") if povar_ingr else None
        if ingrs:
            ingr_uls = ingrs.find_all("li", class_="ingredient flex-dot-line")
            for ingr_ul in ingr_uls:
                ingr_name = ingr_ul.find("span", class_="name").text.strip() if ingr_ul.find("span", class_="name") else "Нет названия"
                ingr_value = ingr_ul.find("span", class_="value")
                ingr_value = ingr_value.text.strip() if ingr_value else ""
                ingr_unit = ingr_ul.find("span", class_="u-unit-name")
                ingr_unit = ingr_unit.text.strip() if ingr_unit else ""
                ingr_list.append({"name": ingr_name, "quantity": ingr_value, "unit": ingr_unit})

        # Шаги приготовления
        recipe_cook = povar_area.find("h2", string=re.compile(r'Как приготовить')).text.strip() if povar_area.find("h2", string=re.compile(r'Как приготовить')) else "Как приготовить"
        
        recipe_prepare = povar_area.find("div", class_="instructions")
        recipe_steps = recipe_prepare.find_all("div", class_="instruction") if recipe_prepare else []
        
        steps_info = []
        for step in recipe_steps:
            step_img = step.find("div", class_="detailed_step_photo_big")
            step_link = None

            if step_img:
                img_link = step_img.find("a", class_="stepphotos")
                step_src = img_link.find("img", class_="photo") if img_link else None
                step_link = step_src.get('src') if step_src else None

            if not step_link:
                step_number = step.find("div", class_="stepNumber")
                step_link = f"Шаг {step_number.text.strip()}" if step_number else "Нет изображения и номера шага"

            recipe_text = step.find("div", class_="detailed_step_description_big").text.strip() if step.find("div", class_="detailed_step_description_big") else "Нет описания"
            steps_info.append({"image_or_step": step_link, "text": recipe_text})

        # Блок видео
        video_block = povar_wrap.find("div", id="ytplayer") if povar_wrap else None
        video_info = {}

        if video_block:
            video_thumbnail = video_block.find("img", class_="lazy-load")
            video_src = video_thumbnail.get('data-src') if video_thumbnail else None
            video_url = f"https://www.youtube.com/watch?v={video_src.split('/')[-2]}" if video_src else None

            video_info = {
                "thumbnail": video_src,
                "video_url": video_url
            }

        # Сбор данных в словарь
        povar_dict = {
            "recipe": recipe_name,
            "img": img_src,
            recipe_ingr_name: ingr_list,
            "how_cook": recipe_cook,
            "steps_info": steps_info,
            "video_info": video_info
        }

    else:
        povar_dict['Ошибка'] = f"Ошибка при запросе: {response.status_code}"

    return povar_dict


