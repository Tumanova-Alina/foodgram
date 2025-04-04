import re

from django.core.exceptions import ValidationError

from foodgram_backend.settings import USER_PROFILE
from api.constants import (
    MIN_COOKING_TIME, MAX_COOKING_TIME,
    MAX_COOKING_TIME_WARNING, MIN_COOKING_TIME_WARNING,
    USERNAME_NOT_ALLOWED, MIN_INGREDIENT_AMOUNT, MAX_INGREDIENT_AMOUNT,
    MAX_INGREDIENT_AMOUNT_WARNING, MIN_INGREDIENT_AMOUNT_WARNING,
    UNIQUE_INGREDIENTS_WARNING, NOT_ALLOWED_SUMBOLS_IN_USERNAME
)


def min_time_validator(time):
    """Валидатор проверки времени приготовления."""
    if time < MIN_COOKING_TIME:
        raise ValidationError(MIN_COOKING_TIME_WARNING)
    elif time > MAX_COOKING_TIME:
        raise ValidationError(MAX_COOKING_TIME_WARNING)
    return time


def ingredient_amount_validator(amount):
    """Валидатор проверки количества ингредиента."""
    if amount < MIN_INGREDIENT_AMOUNT:
        raise ValidationError(MIN_INGREDIENT_AMOUNT_WARNING)
    elif amount > MAX_INGREDIENT_AMOUNT:
        raise ValidationError(MAX_INGREDIENT_AMOUNT_WARNING)
    return amount


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
    ingredients = data.get('ingredients')
    unique_ingredients = []

    for ingredient in ingredients:
        if ingredient['id'] in unique_ingredients:
            raise ValidationError(UNIQUE_INGREDIENTS_WARNING)
        unique_ingredients.append(ingredient['id'])

    return data
