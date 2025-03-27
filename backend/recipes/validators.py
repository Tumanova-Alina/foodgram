import re

from django.core.exceptions import ValidationError

from foodgram_backend.settings import USER_PROFILE


def min_time_validator(time):
    """Валидатор проверки времени приготовления."""
    if time < 1:
        raise ValidationError(
            'Блюдо не может готовиться меньше 1 минуты'
        )
    elif time > 20000:
        raise ValidationError(
            'Блюдо не может готовиться так долго'
        )
    return time


def ingredient_amount_validator(amount):
    """Валидатор проверки количества ингредиента."""
    if amount < 1:
        raise ValidationError(
            'Количество продукта не может быть меньше 1'
        )
    elif amount > 20000:
        raise ValidationError(
            'Количество продукта не может быть таким большим'
        )
    return amount


def validate_username(username):
    """Валидатор проверки username."""
    if username == USER_PROFILE:
        raise ValidationError(
            f'Запрещено использовать username "{USER_PROFILE}".'
        )

    pattern = re.findall(r'[^\w.@+-]', username)
    if pattern:
        raise ValidationError(
            'Имя пользователя содержит недопустимые символы'
            'Разрешены только буквы, цифры и @/./+/-/_'
        )
    return username


def unique_ingredients_validator(self, data):
    """Валидатор уникальности ингредиентов."""
    ingredients = self.initial_data.get('ingredients')
    unique_ingredients = []

    for ingredient in ingredients:
        if ingredient['id'] in unique_ingredients:
            raise ValidationError(
                'Ингредиенты должны быть уникальными'
            )
        unique_ingredients.append(ingredient['id'])

    return data
