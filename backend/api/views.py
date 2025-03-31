from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import (
    AllowAny, IsAuthenticatedOrReadOnly, IsAuthenticated
)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.mixins import DestroyModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet

from recipes.models import (
    Ingredient, Tag, Recipe, Favorite, ShoppingList, Follow,
    RecipeIngredient,
)
from recipes.models import User
from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAdminAuthorOrReadOnly
from .serializers import (
    TagSerializer, IngredientSerializer,
    RecipeSerializer, UserSerializer, CreateRecipeSerializer,
    FollowSerializer, FavoriteSerializer, CurrentUserPhotoSerializer
)

HAVE_NO_SUBSCRIPTIONS = ('У вас нет подписок')
CANT_SUBSCRIBE_TO_YOURSELF = ('Нельзя подписаться на самого себя')
ALREADY_SUBSCRIBED = ('Подписка уже существует')
SUCCESSFULLY_SUBSCRIBED = ('Вы успешно подписались на пользователя')
SUCCESSFULLY_DELETED_SUBSCRIBTION = ('Вы успешно отписались от пользователя')
NOT_SUBSCRIBED = ('Такой подписки нет')
RECIPE_ALREADY_EXISTS_IN_FAVORITES = (
    'Рецепт \"{recipe.name}\" уже есть в избранном')
RECIPE_ALREADY_EXISTS_IN_SHOPPING_LIST = (
    'Рецепт \"{recipe.name}\" уже есть в списке покупок')
RECIPE_NOT_IN_FAVORITES = ('Рецепта \"{recipe.name}\" нет в избранном')
RECIPE_NOT_IN_SHOPPING_LIST = (
    'Рецепта \"{recipe.name}\" нет в списке покупок')


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Tag."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Ingredient."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    search_fields = ('^name',)


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet для пользователей и подписки на авторов."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = LimitOffsetPagination

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated, ),
        url_path='subscriptions',
        url_name='subscriptions',
    )
    def subscriptions(self, request):
        """Создание страницы подписок."""
        queryset = User.objects.filter(follow__user=self.request.user)
        if queryset:
            pages = self.paginate_queryset(queryset)
            serializer = FollowSerializer(pages, many=True,
                                          context={'request': request})
            return self.get_paginated_response(serializer.data)
        return Response(HAVE_NO_SUBSCRIPTIONS,
                        status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
        url_path='subscribe',
        url_name='subscribe',
    )
    def subscribe(self, request, id):
        """Управление подписками."""
        user = request.user
        author = get_object_or_404(User, id=id)
        change_subscription_status = Follow.objects.filter(
            user=user.id, author=author.id
        )
        if request.method == 'POST':
            if user == author:
                return Response(CANT_SUBSCRIBE_TO_YOURSELF,
                                status=status.HTTP_400_BAD_REQUEST)
            if change_subscription_status.exists():
                return Response(ALREADY_SUBSCRIBED,
                                status=status.HTTP_400_BAD_REQUEST)
            subscribe = Follow.objects.create(
                user=user,
                author=author
            )
            subscribe.save()
            return Response(SUCCESSFULLY_SUBSCRIBED,
                            status=status.HTTP_201_CREATED)
        if change_subscription_status.exists():
            change_subscription_status.delete()
            return Response(SUCCESSFULLY_DELETED_SUBSCRIBTION,
                            status=status.HTTP_204_NO_CONTENT)
        return Response(NOT_SUBSCRIBED,
                        status=status.HTTP_400_BAD_REQUEST)


class RecipeViewSet(ModelViewSet):
    """ViewSet для рецептов."""

    queryset = Recipe.objects.all()
    permission_classes = (IsAdminAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        """Вызов сериализатора."""
        if self.action in ('list', 'retrieve'):
            return RecipeSerializer
        elif self.action in ('create', 'partial_update'):
            return CreateRecipeSerializer

    def get_serializer_context(self):
        """Передача контекста."""
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
        url_path='favorite',
        url_name='favorite',
    )
    def favorite(self, request, pk):
        """Управление избранным."""
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        favorite, created = Favorite.objects.get_or_create(
            user=user, recipe=recipe)
        if request.method == 'POST':
            if not created:
                return Response(
                    {'errors': RECIPE_ALREADY_EXISTS_IN_FAVORITES},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = FavoriteSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if created:
                favorite.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'errors': RECIPE_NOT_IN_FAVORITES},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
        url_path='shopping_list',
        url_name='shopping_list',
    )
    def shopping_list(self, request, pk):
        """Управление списком покупок."""
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        shopping_list, created = ShoppingList.objects.get_or_create(
            user=user, recipe=recipe)

        if request.method == 'POST':
            if not created:
                return Response(
                    {'errors': RECIPE_ALREADY_EXISTS_IN_SHOPPING_LIST},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = FavoriteSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if created:
                shopping_list.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'errors': RECIPE_NOT_IN_SHOPPING_LIST},
                status=status.HTTP_400_BAD_REQUEST
            )

    @staticmethod
    def ingredients_to_txt(ingredients):
        """Создание списка для загрузки."""
        shopping_list = ''
        for ingredient in ingredients:
            shopping_list += (
                f"{ingredient['ingredient__name']}  - "
                f"{ingredient['sum']}"
                f"({ingredient['ingredient__measurement_unit']})\n"
            )
        return shopping_list

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        url_path='download_shopping_list',
        url_name='download_shopping_list',
    )
    def download_shopping_list(self, request):
        """Загрузка файла с ингредиентами."""
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_recipe__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(sum=Sum('amount'))
        shopping_list = self.ingredients_to_txt(ingredients)
        return HttpResponse(shopping_list, content_type='text/plain')


class CurrentUserPhoto(UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    serializer_class = CurrentUserPhotoSerializer
    permission_classes = (IsAdminAuthorOrReadOnly,)

    def get_object(self):
        return self.request.user

    def perform_destroy(self, instance):
        instance.profile_image.delete()
