import requests
from settings import settings


def get_calories(ingredient):
    search_url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {"api_key": settings.FOOD_DATA_API_KEY, "query": ingredient, "pageSize": 1}

    res = requests.get(search_url, params=params).json()

    if "foods" not in res or len(res["foods"]) == 0:
        return None

    food = res["foods"][0]

    # Find the 'Energy' field (calories)
    for nutrient in food["foodNutrients"]:
        if nutrient.get("nutrientName") in ("Energy", "Energy (Atwater General Factors)"):
            return nutrient.get("value")

    return None


ingredients = ["apple", "chicken breast", "olive oil", "rice"]

calories = {item: get_calories(item) for item in ingredients}

print(calories)
