from django.db import transaction
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer
from djoser.serializers import UserSerializer as BaseUserSerializer
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.serializers import ModelSerializer

from recipes.models import (Favorite, Follow, Ingredient, Recipe,
                            RecipeIngredient, RecipeTag, ShoppingList, Tag,
                            User)
from recipes.validators import (ingredient_amount_validator,
                                unique_ingredients_validator)

from .utils import Base64ImageField, Hex2NameColor


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

    def get_is_subscribed(self, obj):
        """Проверка подписки."""
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, author=obj.id).exists()


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

    def get_is_favorited(self, obj):
        """Проверка на добавление в избранное."""
        request = self.context['request']
        if request is None or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(
            user=request.user, recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        """Проверка на присутствие в корзине."""
        request = self.context['request']
        if request is None or request.user.is_anonymous:
            return False
        return ShoppingList.objects.filter(
            user=request.user, recipe=obj
        ).exists()


class CreateRecipeIngredientsSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов в рецептах."""

    id = serializers.IntegerField()
    amount = serializers.IntegerField()

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
        all_ingredients = []
        for ingredient in ingredients:
            current_ingredient = get_object_or_404(
                Ingredient, id=ingredient['id'])
            amount = ingredient['amount']
            all_ingredients.append(
                RecipeIngredient(
                    recipe=recipe,
                    ingredient=current_ingredient,
                    amount=amount
                )
            )
        RecipeIngredient.objects.bulk_create(all_ingredients)

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
        RecipeIngredient.objects.filter(recipe=instance).delete()
        RecipeTag.objects.filter(recipe=instance).delete()

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


class FollowSerializer(UserSerializer):
    """Сериализатор подписок."""

    recipes = serializers.SerializerMethodField(
        read_only=True,
        method_name='get_recipes')
    recipes_count = serializers.SerializerMethodField(
        read_only=True
    )

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count',)

    def get_recipes(self, obj):
        """Получение рецептов."""
        request = self.context['request']
        recipes = obj.recipes.all()
        recipes_limit = request.query_params['recipes_limit']
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return AnotherRecipeSerializer(recipes, many=True).data

    @staticmethod
    def get_recipes_count(obj):
        """Получение количества рецептов."""
        return obj.recipes.count()


class FavoriteSerializer(serializers.ModelSerializer):
    """Добавление в избранное."""

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)


class CurrentUserPhotoSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=False)

    class Meta:
        model = User
        fields = ('avatar',)
