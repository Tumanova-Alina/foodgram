from foodgram_backend.settings import USER_PROFILE

MAX_LENGTH_USERNAME = 150
MAX_LENGTH_FIRST_NAME = 150
MAX_LENGTH_LAST_NAME = 150
MAX_LENGTH_NAME = 256
MAX_LENGTH_SLUG = 200
MAX_EMAIL_LENGTH = 254
MAX_COLOR_LENGTH = 7
MAX_MEASUREMENT_UNIT_LENGTH = 200

COLOR_HAVE_NO_NAME = 'У этого цвета нет имени'
MIN_COOKING_TIME = 1
MAX_COOKING_TIME = 20000
MIN_COOKING_TIME_WARNING = 'Блюдо не может готовиться меньше 1 минуты'
MAX_COOKING_TIME_WARNING = 'Блюдо не может готовиться так долго'
USERNAME_NOT_ALLOWED = (f'Запрещено использовать username "{USER_PROFILE}".')
MIN_INGREDIENT_AMOUNT = 1
MAX_INGREDIENT_AMOUNT = 20000
MIN_INGREDIENT_AMOUNT_WARNING = 'Количество продукта не может быть меньше 1'
MAX_INGREDIENT_AMOUNT_WARNING = (
    'Количество продукта не может быть таким большим')
UNIQUE_INGREDIENTS_WARNING = 'Ингредиенты должны быть уникальными'
NOT_ALLOWED_SUMBOLS_IN_USERNAME = (
    'Имя пользователя содержит недопустимые символы'
    'Разрешены только буквы, цифры и @/./+/-/_'
)

HAVE_NO_SUBSCRIPTIONS = {'У вас нет подписок'}
CANT_SUBSCRIBE_TO_YOURSELF = 'Нельзя подписаться на самого себя'
ALREADY_SUBSCRIBED = 'Подписка на "{author}" уже существует'
SUCCESSFULLY_SUBSCRIBED = 'Вы успешно подписались на пользователя "{author}"'
SUCCESSFULLY_DELETED_SUBSCRIPTION = (
    'Вы успешно отписались от пользователя "{author}"')
NOT_SUBSCRIBED = 'Такой подписки нет'
RECIPE_ALREADY_EXISTS_IN_FAVORITES = (
    'Рецепт "{recipe}" уже есть в избранном')
RECIPE_ALREADY_EXISTS_IN_SHOPPING_LIST = (
    'Рецепт "{recipe}" уже есть в списке покупок')
RECIPE_NOT_IN_FAVORITES = 'Рецепта "{recipe}" нет в избранном'
RECIPE_NOT_IN_SHOPPING_LIST = 'Рецепта "{recipe}" нет в списке покупок'
NO_RECIPES_TO_GENERATE_SHOPPING_LIST = (
    'У вас нет рецептов для генерации списка покупок.')
INVALID_PASSWORD = 'Неправильный пароль'
HAVE_NO_AVATAR = 'Аватар не установлен.'
METHOD_NOT_ALLOWED = 'Этот метод запрещен.'
