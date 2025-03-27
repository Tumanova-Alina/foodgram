from django_filters.rest_framework import filters, FilterSet, CharFilter
from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(FilterSet):
    """Поиск по ингредиенту."""

    name = CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name', )


class RecipeFilter(FilterSet):
    """Избранное и список покупок."""

    is_favorite = filters.BooleanFilter(
        method='get_is_favorite'
    )
    is_in_shopping_list = filters.BooleanFilter(
        method='get_is_in_shopping_list'
    )
    tags = filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug',
    )

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorite', 'is_in_shopping_list')

    def get_is_favorite(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def get_is_in_shopping_list(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(shopping_list__user=self.request.user)
        return queryset
