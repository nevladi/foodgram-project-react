from django.urls import include, path
from rest_framework.routers import DefaultRouter


router = DefaultRouter()

router.register(r'ingredients', ..., basename='ingredients')
router.register(r'tags', ..., basename='tags')
router.register(r'recipes', ..., basename='recipes')


urlpatterns = [
    path(
        'recipes/download_shopping_cart/', ...,
        name='download_shopping_cart'),
    path('recipes/<int:id>/shopping_cart/', ...,
        name='shopping_cart'),
    path('recipes/<int:id>/favorite/', ...,
        name='favorite'),
    path('users/<int:id>/subscribe/', ...,
        name='subscribe'),
    path('users/subscriptions/', ...,
        name='subscriptions'),
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),

]
