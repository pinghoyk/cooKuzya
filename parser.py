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
