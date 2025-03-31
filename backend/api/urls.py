from django.urls import include, path
from rest_framework import routers

from .views import (
    IngredientViewSet, TagViewSet, RecipeViewSet,
    UserViewSet, CurrentUserPhoto
)

app_name = 'api'

router_v1 = routers.DefaultRouter()
router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register('ingredients', IngredientViewSet, basename='ingredients')
router_v1.register('recipes', RecipeViewSet, basename='recipes')
router_v1.register('users', UserViewSet, basename='users')


urlpatterns = [
    path('v1/', include(router_v1.urls)),
    path('me/profile_image/', CurrentUserPhoto.as_view({
        'put': 'update',
        'delete': 'destroy'
    })),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
