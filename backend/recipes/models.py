from api.constants import (MAX_COLOR_LENGTH, MAX_EMAIL_LENGTH,
                           MAX_LENGTH_FIRST_NAME, MAX_LENGTH_LAST_NAME,
                           MAX_LENGTH_NAME, MAX_LENGTH_SLUG,
                           MAX_LENGTH_USERNAME, MAX_MEASUREMENT_UNIT_LENGTH)
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q

from .validators import min_time_validator, validate_username

USER = 'user'
ADMIN = 'admin'

ROLES = (
    (ADMIN, 'Администратор'),
    (USER, 'Пользователь'),
)


class User(AbstractUser):
    """Пользователь."""

    username = models.CharField(
        verbose_name='Ник',
        max_length=MAX_LENGTH_USERNAME,
        unique=True,
        validators=(validate_username,
                    )
    )
    email = models.EmailField(
        verbose_name='Электронная почта',
        unique=True,
        max_length=MAX_EMAIL_LENGTH,
    )
    is_subscribed = models.BooleanField(
        default=False,
        verbose_name='О подписке',
    )
    role = models.CharField(
        verbose_name='Роль',
        choices=ROLES,
        default=USER,
        max_length=max(len(role) for role, _ in ROLES)
    )
    first_name = models.CharField(
        max_length=MAX_LENGTH_FIRST_NAME,
        blank=True,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=MAX_LENGTH_LAST_NAME,
        blank=True,
        verbose_name='Фамилия'
    )
    avatar = models.ImageField(
        upload_to='users/',
        null=True,
        verbose_name='Фото профиля'
    )

    @property
    def is_admin(self):
        return self.role == ADMIN or self.is_superuser

    class Meta(AbstractUser.Meta):
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Tag(models.Model):
    """Тег."""

    name = models.CharField(
        max_length=MAX_LENGTH_NAME,
        unique=True,
        verbose_name='Название',
    )
    color = models.CharField(
        max_length=MAX_COLOR_LENGTH,
        unique=True,
        verbose_name='Цвет')
    slug = models.SlugField(
        max_length=MAX_LENGTH_SLUG,
        unique=True,
        db_index=True,
        verbose_name='Идентификатор')

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Ингредиент."""

    name = models.CharField(
        max_length=MAX_LENGTH_NAME,
        verbose_name='Название ингредиента'
    )
    measurement_unit = models.CharField(
        max_length=MAX_MEASUREMENT_UNIT_LENGTH,
        verbose_name='Единица измерения')

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты',
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredient'
            )
        ]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Рецепт."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта',
    )
    name = models.CharField(
        max_length=MAX_LENGTH_NAME,
        verbose_name='Название рецепта'
    )
    image = models.ImageField(
        verbose_name='Фотография рецепта',
        upload_to='recipes/images/',
    )
    text = models.TextField(
        verbose_name='Описание рецепта',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Список ингредиентов',
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=(min_time_validator,),
        verbose_name='Время приготовления блюда в минутах')
    pub_date = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True,
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'author'),
                name='unique_name_author'
            )
        ]

    def __str__(self):
        return self.name


class RecipeTag(models.Model):
    """Модель тегов рецепта."""

    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name='Теги',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Тег рецепта'
        verbose_name_plural = 'Теги рецепта'
        constraints = [
            models.UniqueConstraint(
                fields=('tag', 'recipe'),
                name='unique_recipe_tag')
        ]

    def __str__(self):
        return f'Тег {self.tag} добавлен к рецепту \"{self.recipe}\"'


class RecipeIngredient(models.Model):
    """Количество ингредиента в рецепте."""

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe',
        verbose_name='Ингредиент'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients', verbose_name='Рецепт')
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        blank=False,
    )

    class Meta:
        verbose_name = 'Ингредиент для рецепта'
        verbose_name_plural = 'Ингредиенты для рецепта',
        constraints = [
            models.UniqueConstraint(
                fields=('ingredient', 'recipe'),
                name='unique_ingredient_in_recipe'
            ),
        ]

    def __str__(self):
        return (f'{self.ingredient.name} - '
                f'{self.amount} {self.ingredient.measurement_unit}')


class Follow(models.Model):
    """Подписка на авторов."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Дата подписки',
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'), name='unique_follow'),
            models.CheckConstraint(
                check=~Q(user=models.F('author')),
                name='prevent_self_follow')
        ]

    def __str__(self):
        return f'{self.user} подписан на {self.author}'


class Favorite(models.Model):
    """Избранное."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Понравившийся рецепт'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Дата добавления',
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное',
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'{self.user} добавил в избранное рецепт \"{self.recipe}\"'


class ShoppingList(models.Model):
    """Список покупок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_list',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='shopping_list',
        verbose_name='Рецепт'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Дата добавления',
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок',
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_shopping_list'
            )
        ]

    def __str__(self):
        return f'{self.user} добавил в список покупок рецепт \"{self.recipe}\"'
