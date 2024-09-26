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
