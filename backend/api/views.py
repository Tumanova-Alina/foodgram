import os
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.serializers import SetPasswordSerializer
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
from rest_framework.serializers import ValidationError

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
    FollowSerializer, FavoriteSerializer, CurrentUserPhotoSerializer,
    CreateUserSerializer
)
from .constants import (
    HAVE_NO_SUBSCRIPTIONS, CANT_SUBSCRIBE_TO_YOURSELF,
    ALREADY_SUBSCRIBED, SUCCESSFULLY_SUBSCRIBED,
    SUCCESSFULLY_DELETED_SUBSCRIPTION, NOT_SUBSCRIBED,
    RECIPE_ALREADY_EXISTS_IN_FAVORITES, RECIPE_ALREADY_EXISTS_IN_SHOPPING_LIST,
    RECIPE_NOT_IN_FAVORITES, RECIPE_NOT_IN_SHOPPING_LIST,
    NO_RECIPES_TO_GENERATE_SHOPPING_LIST
)


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
    """ViewSet для пользователей и подписки на авторов."""

    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    pagination_class = LimitOffsetPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateUserSerializer
        return UserSerializer

    # def perform_create(self, serializer):
    #     try:
    #         serializer.save()
    #     except ValidationError as e:
    #         return Response(
    #             {'error': e.detail}, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=('get',),
        detail=False,
        url_path='me',
        permission_classes=(AllowAny,)
    )
    def user_profile(self, request):
        """Профиль пользователя."""
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # @action(
    #     methods=('post',),
    #     detail=False,
    #     url_path='set_password',
    #     permission_classes=(IsAuthenticated,)
    # )
    # def set_password(self, request, *args, **kwargs):
    #     """Изменение пароля."""
    #     serializer = SetPasswordSerializer(request.data)
    #     current_password = serializer.data['current_password']
    #     is_password_valid = self.request.user.check_password(current_password)
    #     if is_password_valid:
    #         self.request.user.set_password(serializer.data['new_password'])
    #         self.request.user.save()
    #         return Response(status=status.HTTP_204_NO_CONTENT)
    #     else:
    #         raise ValidationError('invalid_password')

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated, ),
        url_path='subscriptions',
        url_name='subscriptions',
    )
    def subscriptions(self, request):
        """Создание страницы подписок."""
        queryset = User.objects.filter(following__user=self.request.user)
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
    def subscribe(self, request, pk):
        """Управление подписками."""
        user = request.user
        author = get_object_or_404(User, id=pk)
        change_subscription_status = Follow.objects.filter(
            user=user.id, author=author.id
        )
        if request.method == 'POST':
            if user == author:
                return Response(CANT_SUBSCRIBE_TO_YOURSELF,
                                status=status.HTTP_400_BAD_REQUEST)
            if change_subscription_status.exists():
                return Response(ALREADY_SUBSCRIBED.format(author=author),
                                status=status.HTTP_400_BAD_REQUEST)
            subscribe = Follow.objects.create(
                user=user,
                author=author
            )
            subscribe.save()
            return Response(SUCCESSFULLY_SUBSCRIBED.format(author=author),
                            status=status.HTTP_201_CREATED)
        if change_subscription_status.exists():
            change_subscription_status.delete()
            return Response(
                SUCCESSFULLY_DELETED_SUBSCRIPTION.format(author=author),
                status=status.HTTP_204_NO_CONTENT)
        return Response(NOT_SUBSCRIBED,
                        status=status.HTTP_400_BAD_REQUEST)


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
        recipe = get_object_or_404(Recipe, id=pk)
        favorite = Favorite.objects.filter(recipe=recipe)

        if request.method == 'POST':
            if favorite.exists():
                return Response(
                    {'error': RECIPE_ALREADY_EXISTS_IN_FAVORITES.format(
                        recipe=recipe)}, status=status.HTTP_400_BAD_REQUEST)
            Favorite.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeSerializer(recipe, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            if not favorite.exists():
                return Response(
                    {'error': RECIPE_NOT_IN_FAVORITES.format(recipe=recipe)},
                    status=status.HTTP_400_BAD_REQUEST)
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True,
            url_path='get-link')
    def get_link(self, request, pk=None):
        recipe_id = self.kwargs[self.lookup_field]
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        url_to_recipes = os.getenv('URL_TO_RECIPES', 'recipes')
        short_link = f'{frontend_url}/{url_to_recipes}/{recipe_id}/'
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
        recipe = get_object_or_404(Recipe, id=pk)
        shopping_list, created = ShoppingList.objects.get_or_create(
            user=user, recipe=recipe)

        if request.method == 'POST':
            if not created:
                return Response(
                    {'errors': RECIPE_ALREADY_EXISTS_IN_SHOPPING_LIST.format(
                        recipe=recipe)}, status=status.HTTP_400_BAD_REQUEST
                )
            serializer = FavoriteSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if created:
                shopping_list.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'errors': RECIPE_NOT_IN_SHOPPING_LIST.format(recipe=recipe)},
                status=status.HTTP_400_BAD_REQUEST
            )

    # @action(
    #     detail=False,
    #     methods=('get',),
    #     permission_classes=(IsAuthenticated,),
    #     url_path='cart',
    #     url_name='cart',
    # )
    # def get_shopping_list(self, request):
    #     """Получение текущего списка покупок."""
    #     user = request.user
    #     shopping_list = ShoppingList.objects.filter(
    #         user=user).select_related('recipe')

    #     data = []
    #     for item in shopping_list:
    #         ingredients = RecipeIngredient.objects.filter(
    #             recipe=item.recipe).values(
    #             'ingredient__name', 'ingredient__measurement_unit', 'amount'
    #         ).annotate(sum=Sum('amount'))
    #         data.append({
    #             'recipe': item.recipe.name,
    #             'ingredients': list(ingredients)
    #         })
    #     return Response(data)

    @staticmethod
    def ingredients_to_txt(ingredients):
        """Создание списка для загрузки."""
        shopping_list = 'Список покупок:\n'
        for ingredient in ingredients:
            shopping_list += (
                f"{ingredient['ingredient__name']} - "
                f"{ingredient['total']}"
                f"({ingredient['ingredient__measurement_unit']})\n"
            )
        return shopping_list

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        url_path='download_shopping_cart',
        url_name='download_shopping_cart',
    )
    def download_shopping_list(self, request):
        """Загрузка файла с ингредиентами."""
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_list__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(total=Sum('amount')).order_by('ingredient__name')
        if not ingredients:
            return Response(
                {"error": NO_RECIPES_TO_GENERATE_SHOPPING_LIST},
                status=status.HTTP_400_BAD_REQUEST
            )
        shopping_list = self.ingredients_to_txt(ingredients)
        return HttpResponse(
            shopping_list, content_type='text/plain; charset=UTF-8')


class CurrentUserPhoto(UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    serializer_class = CurrentUserPhotoSerializer
    permission_classes = (IsAdminAuthorOrReadOnly,)

    def get_object(self):
        return self.request.user

    def perform_destroy(self, instance):
        instance.avatar.delete()
