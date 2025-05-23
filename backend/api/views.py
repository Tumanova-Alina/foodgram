import os

from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.serializers import SetPasswordSerializer
from recipes.models import Ingredient, Recipe, Tag, User
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed, NotFound
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .constants import (AMOUNT_KEY, HAVE_NO_AVATAR, METHOD_NOT_ALLOWED,
                        NAME_KEY, NO_RECIPES_TO_GENERATE_SHOPPING_LIST,
                        NOT_SUBSCRIBED, RECIPE_NOT_IN_FAVORITES,
                        RECIPE_NOT_IN_SHOPPING_LIST,
                        SUCCESSFULLY_ADDED_TO_SHOPPING_LIST,
                        SUCCESSFULLY_DELETED_FAVORITE,
                        SUCCESSFULLY_DELETED_FROM_SHOPPING_LIST,
                        SUCCESSFULLY_DELETED_SUBSCRIPTION,
                        SUCCESSFULLY_FAVORITED, TOTAL_KEY,
                        UNEXPECTED_FORMAT_OF_DATA, UNIT_KEY)
from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAdminAuthorOrReadOnly
from .serializers import (CreateRecipeSerializer, CreateUserSerializer,
                          CurrentUserPhotoSerializer, FavoriteSerializer,
                          FollowSerializer, IngredientSerializer,
                          RecipeSerializer, ShoppingListSerializer,
                          TagSerializer, UserSerializer)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Tag."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Ingredient."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    search_fields = ('^name',)


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet для пользователей и подписок."""

    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    pagination_class = LimitOffsetPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateUserSerializer
        return UserSerializer

    @action(
        detail=False,
        url_path='me',
        url_name='me',
        permission_classes=(IsAuthenticated,)
    )
    def user_profile(self, request):
        """Профиль пользователя."""
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=('put', 'delete'),
        url_path='me/avatar',
        url_name='me/avatar',
        permission_classes=(IsAuthenticated,)
    )
    def avatar(self, request):
        """Добавление/удаление аватара."""
        user = request.user
        if request.method == 'PUT':
            serializer = CurrentUserPhotoSerializer(
                user, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {'avatar': request.build_absolute_uri(user.avatar.url)}
            )
        elif request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            raise NotFound(HAVE_NO_AVATAR)
        raise MethodNotAllowed(request.method, detail=METHOD_NOT_ALLOWED)

    @action(
        methods=('post',),
        detail=False,
        url_path='set_password',
        url_name='set_password',
        permission_classes=(IsAuthenticated,)
    )
    def set_password(self, request, *args, **kwargs):
        """Изменение пароля."""
        serializer = SetPasswordSerializer(
            data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        self.request.user.set_password(
            serializer.validated_data['new_password'])
        self.request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='subscriptions',
        url_name='subscriptions',
    )
    def subscriptions(self, request):
        """Создание страницы подписок."""
        queryset = request.user.follower.all()
        pages = self.paginate_queryset(queryset)
        context = self.get_serializer_context()
        serializer = FollowSerializer(pages, many=True, context=context)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
        url_path='subscribe',
        url_name='subscribe',
    )
    def subscribe(self, request, pk):
        """Управление подписками."""
        user = request.user
        self.lookup_url_kwarg = 'pk'
        self.lookup_field = 'id'
        author = self.get_object()

        if request.method == 'POST':
            serializer = FollowSerializer(
                data={'author': author},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(user=self.request.user)
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)

        deleted, _ = user.follower.filter(author=author).delete()
        if deleted:
            return Response(
                SUCCESSFULLY_DELETED_SUBSCRIPTION.format(author=author),
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(NOT_SUBSCRIBED, status=status.HTTP_400_BAD_REQUEST)


class RecipeViewSet(ModelViewSet):
    """ViewSet для рецептов."""

    queryset = Recipe.objects.all().select_related(
        'author'
    ).prefetch_related(
        'ingredients', 'tags'
    )
    permission_classes = (IsAdminAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        """Вызов сериализатора."""
        if self.action in ('list', 'retrieve'):
            return RecipeSerializer
        elif self.action in ('create', 'partial_update'):
            return CreateRecipeSerializer

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
        self.lookup_url_kwarg = 'pk'
        self.lookup_field = 'id'
        recipe = self.get_object()

        if request.method == 'POST':
            serializer = FavoriteSerializer(
                data={'user': user.id, 'recipe': recipe.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                SUCCESSFULLY_FAVORITED.format(recipe=recipe),
                status=status.HTTP_201_CREATED
            )

        deleted, _ = user.favorites.filter(recipe=recipe).delete()
        if deleted:
            return Response(
                SUCCESSFULLY_DELETED_FAVORITE.format(recipe=recipe),
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            RECIPE_NOT_IN_FAVORITES, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        url_path='get-link',
        url_name='get-link',
    )
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        recipes_url = os.getenv('RECIPES_URL', 'recipes')
        short_link = f'{frontend_url}/{recipes_url}/{recipe.id}/'
        return Response({'short-link': short_link})

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
        url_path='shopping_cart',
        url_name='shopping_cart',
    )
    def shopping_list(self, request, pk):
        """Управление списком покупок."""
        user = request.user
        self.lookup_url_kwarg = 'pk'
        self.lookup_field = 'id'
        recipe = self.get_object()

        if request.method == 'POST':
            serializer = ShoppingListSerializer(
                data={'user': user.id, 'recipe': recipe.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                SUCCESSFULLY_ADDED_TO_SHOPPING_LIST.format(recipe=recipe),
                status=status.HTTP_201_CREATED
            )

        deleted, _ = user.shopping_list.filter(recipe=recipe).delete()
        if deleted:
            return Response(
                SUCCESSFULLY_DELETED_FROM_SHOPPING_LIST.format(recipe=recipe),
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            RECIPE_NOT_IN_SHOPPING_LIST, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def get_shopping_list(ingredients):
        """Создание списка для загрузки."""
        shopping_list_header = ('Список покупок:\n',)

        try:
            shopping_list_body = (
                "{} - {} ({})\n".format(
                    ingredient.get(NAME_KEY, 'Не указано'),
                    ingredient.get(TOTAL_KEY, 'Не указано'),
                    ingredient.get(UNIT_KEY, 'Не указано')
                )
                for ingredient in ingredients
            )
        except (TypeError, AttributeError) as error:
            raise ValueError(
                UNEXPECTED_FORMAT_OF_DATA) from error

        return ''.join((*shopping_list_header, *shopping_list_body))

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='download_shopping_cart',
        url_name='download_shopping_cart',
    )
    def download_shopping_list(self, request):
        """Загрузка файла с ингредиентами."""
        user = request.user
        ingredients = user.shopping_list.values(
            NAME_KEY,
            UNIT_KEY,
        ).annotate(
            total=Sum(AMOUNT_KEY)
        ).order_by(NAME_KEY)
        if not ingredients.exists():
            return Response(
                {"error": NO_RECIPES_TO_GENERATE_SHOPPING_LIST},
                status=status.HTTP_400_BAD_REQUEST
            )
        shopping_list = self.get_shopping_list(ingredients)
        response = HttpResponse(
            shopping_list, content_type='text/plain; charset=UTF-8')
        response['Content-Disposition'
                 ] = 'attachment; filename="shopping_list.txt"'
        return response
