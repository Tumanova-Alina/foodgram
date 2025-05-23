from django.db import transaction
from djoser.serializers import UserCreateSerializer
from djoser.serializers import UserSerializer as BaseUserSerializer
from recipes.models import (Favorite, Follow, Ingredient, Recipe,
                            RecipeIngredient, ShoppingList, Tag, User)
from recipes.validators import (ingredient_amount_validator,
                                unique_ingredients_validator)
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.serializers import ModelSerializer, ValidationError

from .constants import (ALREADY_SUBSCRIBED, CANT_SUBSCRIBE_TO_YOURSELF,
                        INVALID_PASSWORD, RECIPE_ALREADY_EXISTS_IN_FAVORITES,
                        RECIPE_ALREADY_EXISTS_IN_SHOPPING_LIST)
from .serializers_fields import Base64ImageField, Hex2NameColor


class TagSerializer(ModelSerializer):
    """Сериализатор тегов."""

    color = Hex2NameColor()

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(ModelSerializer):
    """Сериализатор ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class UserSerializer(BaseUserSerializer):
    """Сериализатор пользователей."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'avatar', 'is_subscribed')

    def get_is_subscribed(self, author):
        """Проверка подписки."""
        user = self.context['request'].user
        return (
            not user.is_anonymous and user.follower.filter(
                author=author).exists()
        )


class CreateUserSerializer(UserCreateSerializer):
    """Сериализатор для создания пользователя.

    Без проверки на подписку.
    """

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'password')

    def create(self, validated_data):
        user = super().create(validated_data)
        Token.objects.create(user=user)
        return user


class SetPasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise ValidationError(INVALID_PASSWORD)
        return value

    def validate(self, data):
        if data['current_password'] == data['new_password']:
            raise ValidationError(
                'Новый пароль не должен совпадать с текущим.')
        return data


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов в рецепте."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов."""

    tags = TagSerializer(many=True)
    author = UserSerializer()
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients', many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'tags', 'author', 'image',
                  'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'text', 'cooking_time'
                  )

    def get_is_favorited(self, recipe):
        """Проверка на добавление в избранное."""
        request = self.context['request']
        user = request.user
        if request is None or request.user.is_anonymous:
            return False
        return user.favorites.filter(recipe=recipe).exists()

    def get_is_in_shopping_cart(self, recipe):
        """Проверка на присутствие в корзине."""
        request = self.context['request']
        user = request.user
        if request is None or request.user.is_anonymous:
            return False
        return user.shopping_list.filter(recipe=recipe).exists()


class CreateRecipeIngredientsSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов в рецептах."""

    id = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class CreateRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор создания рецептов."""

    ingredients = serializers.ListField(
        child=serializers.DictField(), write_only=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    image = Base64ImageField(use_url=True)

    class Meta:
        model = Recipe
        fields = ('name', 'ingredients', 'tags',
                  'image', 'text', 'cooking_time')

    def validate(self, data):
        data = unique_ingredients_validator(data)
        return ingredient_amount_validator(data)

    def create_ingredients(self, ingredients, recipe):
        """Создание ингредиентов."""
        ingredients_data = {
            ingredient['id']: ingredient
            for ingredient in ingredients
            if 'id' in ingredient
        }
        existing_ingredients = Ingredient.objects.filter(
            id__in=ingredients_data.keys()
        )

        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient,
                amount=ingredients_data[ingredient.id].get('amount')
            )
            for ingredient in existing_ingredients
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def create_tags(self, tags, recipe):
        """Добавление тега."""
        recipe.tags.set(tags)

    @transaction.atomic
    def create(self, validated_data):
        """Создание модели."""
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        user = self.context['request'].user
        recipe = Recipe.objects.create(**validated_data, author=user)
        self.create_ingredients(ingredients, recipe)
        self.create_tags(tags, recipe)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Обновление модели."""
        instance.ingredients.clear()
        instance.tags.clear()

        self.create_ingredients(validated_data.pop('ingredients'), instance)
        self.create_tags(validated_data.pop('tags'), instance)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Представление модели."""
        serializer = RecipeSerializer(
            instance,
            context={
                'request': self.context['request']
            }
        )
        return serializer.data


class AnotherRecipeSerializer(serializers.ModelSerializer):
    """Дополнительный сериализатор рецептов."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор для оформления подписки."""

    user = serializers.SlugRelatedField(
        slug_field='email',
        read_only=True,
        default=serializers.CurrentUserDefault()
    )
    author = serializers.SlugRelatedField(
        slug_field='username',
        queryset=User.objects.all(),
        required=True
    )

    class Meta:
        model = Follow
        fields = ('user', 'author')

    def validate(self, data):
        user = self.context['request'].user
        author = data['author']

        if user == author:
            raise ValidationError(CANT_SUBSCRIBE_TO_YOURSELF)
        if user.following.filter(author=author).exists():
            raise ValidationError(ALREADY_SUBSCRIBED)
        return data

    def to_representation(self, instance):
        return FollowReadSerializer(
            instance=instance.author, context=self.context).data


class FollowReadSerializer(UserSerializer):
    """Сериализатор подписок."""

    recipes = serializers.SerializerMethodField(
        method_name='get_recipes')
    recipes_count = serializers.IntegerField(
        source='recipes.count',
        read_only=True
    )
    # avatar = serializers.ImageField(source='author.avatar', read_only=True)

    class Meta(UserSerializer.Meta):
        # model = User
        fields = UserSerializer.Meta.fields + (
            'recipes',
            'recipes_count',
        )

    def get_recipes(self, obj):
        """Получение рецептов."""
        request = self.context.get('request')
        recipes = obj.recipes.all()
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return AnotherRecipeSerializer(recipes, context={
            'request': self.context['request']}, many=True).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Добавление в избранное."""

    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, data):
        user = self.context['request'].user
        recipe = data['recipe']

        if user.favorites.filter(recipe=recipe).exists():
            raise ValidationError(RECIPE_ALREADY_EXISTS_IN_FAVORITES)
        return data


class CurrentUserPhotoSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=False)

    class Meta:
        model = User
        fields = ('avatar',)


class ShoppingListSerializer(serializers.ModelSerializer):
    """"Сериализатор для модели списка покупок."""

    class Meta:
        model = ShoppingList
        fields = ('user', 'recipe')

    def validate(self, data):
        user = self.context['request'].user
        recipe = data['recipe']

        if user.shopping_list.filter(recipe=recipe).exists():
            raise ValidationError(RECIPE_ALREADY_EXISTS_IN_SHOPPING_LIST)
        return data
