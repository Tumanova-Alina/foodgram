from django.contrib.admin import ModelAdmin, TabularInline, register

from .models import (Favorite, Follow, Ingredient, Recipe, RecipeIngredient,
                     ShoppingList, Tag, User)


class RecipeIngredientInLine(TabularInline):
    model = Recipe.ingredients.through
    min_num = 1


@register(User)
class UserAdmin(ModelAdmin):
    list_display = ('id', 'username', 'email', 'first_name', 'last_name',)
    list_filter = ('username', 'email')
    search_fields = ('username', 'email')
    empty_value_display = 'Пусто'


@register(Recipe)
class RecipeAdmin(ModelAdmin):
    list_display = ('id', 'name', 'author', 'favorites_count',
                    )
    search_fields = ('name',)
    list_filter = ('name', 'author', 'tags')
    empty_value_display = 'Пусто'
    inlines = (RecipeIngredientInLine,)

    def favorites_count(self, obj):
        recipe = Recipe.objects.get(id=obj.id)
        return recipe.favorites.count()


@register(Follow)
class FollowAdmin(ModelAdmin):
    list_display = ('id', 'user', 'author')
    list_filter = ('user', 'author')
    empty_value_display = 'Пусто'


class FavoriteShoppingListBaseAdmin(ModelAdmin):
    list_display = ('id', 'user', 'recipe',)
    list_filter = ('user', 'recipe')
    empty_value_display = 'Пусто'


@register(Favorite)
class FavoriteAdmin(FavoriteShoppingListBaseAdmin):
    pass


@register(ShoppingList)
class ShoppingListAdmin(FavoriteShoppingListBaseAdmin):
    pass


@register(Ingredient)
class IngredientAdmin(ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit',)
    list_filter = ('name',)
    search_fields = ('name', 'measurement_unit',)
    empty_value_display = 'Пусто'


@register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ('id', 'name', 'color', 'slug')
    empty_value_display = 'Пусто'


@register(RecipeIngredient)
class RecipeIngredientAdmin(ModelAdmin):
    list_display = ('id', 'ingredient', 'amount',)
    empty_value_display = 'Пусто'
