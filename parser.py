import requests
from bs4 import BeautifulSoup
import re

def recipes_povar(URL): # получение рецептов с 1 сайта
	response = requests.get(URL)

	recipes_dict = {}

	if response.status_code == 200:
		soap = BeautifulSoup(response.text, "html.parser")

		recipes_povar = soap.find("div", id="megaContainer") # весь контент на странице
		recipe_container = recipes_povar.find("div", id="container")
		recipe_wrap = recipe_container.find("div", id="mainWrapper")
		recipe_area = recipe_wrap.find("div", class_="cont_area hrecipe")

		recipe_name = recipe_area.find("h1", class_="detailed").text.strip() # название рецепта

		recipe_img_area = recipe_area.find("div", class_="bigImgBox")  # поиск изображения
		recipe_link_img = recipe_img_area.find("a")
		recipe_img = recipe_link_img.find("img", class_="photo") # здесь я обращаюсь к тегу img
		img_src = recipe_img.get('src') # здесь получаю ссылку с тега


		recipe_ingr = recipe_area.find("div", class_="ingredients_wrapper") # ингедиенты с ненужнойц хуйней
		recipe_ingr_name = recipe_ingr.find("h2", class_="span").text.strip() # название состав и бла-бла

		ingr = recipe_ingr.find("ul", class_="detailed_ingredients no_dots") # список ингедиентов
		ingr_ul = ingr.find("li", class_="ingredient flex-dot-line") # наименование ингредиентв
		ingr_name = ingr_ul.find("span", class_="name").text.strip() # что написано, сколько и граммы
		ingr_value = ingr_ul.find("span", class_="value").text.strip()
		ingr_unit = ingr_ul.find("span", class_="u-unit-name").text.strip()
