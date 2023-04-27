from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (CustUserViewSet, IngredientViewSet, RecipeViewSet,
                       TagViewSet)

router = DefaultRouter()

router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'users', CustUserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
