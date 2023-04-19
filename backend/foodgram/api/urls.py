from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (IngredientViewSet, TagViewSet, RecipeViewSet,
                       SubscriptionView, SubscriptionGetView, FavoritesListView,
                       ShoppingListView, download_shopping_list)


router = DefaultRouter()

router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'recipes', RecipeViewSet, basename='recipes')


urlpatterns = [
    path('recipes/<int:id>/favorite/', FavoritesListView.as_view()),
    path('recipes/download_shopping_cart/', download_shopping_list),
    path('recipes/<int:id>/shopping_cart/', ShoppingListView.as_view()),
    path('users/subscriptions/', SubscriptionGetView.as_view()),
    path('users/<int:id>/subscribe/', SubscriptionView.as_view()),
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
