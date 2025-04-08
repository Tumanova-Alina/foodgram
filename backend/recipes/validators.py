import re

from api.constants import (MAX_COOKING_TIME, MAX_COOKING_TIME_WARNING,
                           MAX_INGREDIENT_AMOUNT,
                           MAX_INGREDIENT_AMOUNT_WARNING, MIN_COOKING_TIME,
                           MIN_COOKING_TIME_WARNING, MIN_INGREDIENT_AMOUNT,
                           MIN_INGREDIENT_AMOUNT_WARNING,
                           NOT_ALLOWED_SUMBOLS_IN_USERNAME,
                           UNIQUE_INGREDIENTS_WARNING, USERNAME_NOT_ALLOWED)
from django.core.exceptions import ValidationError
from foodgram_backend.settings import USER_PROFILE


def min_time_validator(time):
    """Валидатор проверки времени приготовления."""
    if time < MIN_COOKING_TIME:
        raise ValidationError(MIN_COOKING_TIME_WARNING)
    elif time > MAX_COOKING_TIME:
        raise ValidationError(MAX_COOKING_TIME_WARNING)
    return time


def ingredient_amount_validator(data):
    """Валидатор проверки количества ингредиента."""
    for ingredient in data['ingredients']:
        amount = int(ingredient['amount'])
        if amount < MIN_INGREDIENT_AMOUNT:
            raise ValidationError(MIN_INGREDIENT_AMOUNT_WARNING)
        elif amount > MAX_INGREDIENT_AMOUNT:
            raise ValidationError(MAX_INGREDIENT_AMOUNT_WARNING)
    return data


def validate_username(username):
    """Валидатор проверки username."""
    if username == USER_PROFILE:
        raise ValidationError(USERNAME_NOT_ALLOWED)

    pattern = re.findall(r'[^\w.@+-]', username)
    if pattern:
        raise ValidationError(NOT_ALLOWED_SUMBOLS_IN_USERNAME)
    return username


def unique_ingredients_validator(data):
    """Валидатор уникальности ингредиентов."""
    ingredients = data['ingredients']
    unique_ingredients = []

    for ingredient in ingredients:
        if ingredient['id'] in unique_ingredients:
            raise ValidationError(UNIQUE_INGREDIENTS_WARNING)
        unique_ingredients.append(ingredient['id'])

    return data
