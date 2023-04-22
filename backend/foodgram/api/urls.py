from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import IngredientViewSet, TagViewSet, RecipeViewSet, CustUserViewSet


router = DefaultRouter()

router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'users', CustUserViewSet, basename='users')

urlpatterns = [
    path('recipes/<int:id>/favorite/',
         RecipeViewSet.as_view({'post': 'add_to_favorites', 'delete': 'remove_from_favorites'})),
    path('recipes/download_shopping_cart/',
         RecipeViewSet.as_view({'get': 'download_shopping_list'})),
    path('recipes/<int:id>/shopping_cart/',
         RecipeViewSet.as_view({'post': 'add_to_shopping_list', 'delete': 'remove_from_shopping_list'})),
    path('users/subscriptions/', CustUserViewSet.as_view({'get': 'subscriptions'})),
    path('users/<int:id>/subscribe/',
         CustUserViewSet.as_view({'post': 'subscribe', 'delete': 'remove_from_subscribe'})),
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
