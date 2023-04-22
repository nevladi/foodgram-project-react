from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from api.filters import RecipeFilter, IngredientFilter
from recipes.models import (Ingredient, Tag, RecipeIngredient, Recipe,
                            ShoppingList, FavoritesList)
from users.models import Subscription, User
from api.serializers import (TagSerializer, IngredientSerializer, UserSubscriptionSerializer,
                             FavoritesListSerializer, ShoppingListSerializer, RecipeSerializer,
                             RecipePostSerializer, CustUserSerializer)
from api.permissions import IsAdminAuthorOrReadOnly


class CustUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustUserSerializer
    pagination_class = PageNumberPagination

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        user = request.user
        queryset = User.objects.filter(author__user=user)
        serializer = UserSubscriptionSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def subscribe(self, request, **kwargs):
        user = request.user
        author_id = self.kwargs.get('id')
        author = get_object_or_404(User, id=author_id)
        if request.method == 'POST':
            serializer = UserSubscriptionSerializer(
                author, data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            Subscription.objects.create(user=user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def remove_from_subscribe(self, request, **kwargs):
        user = request.user
        author_id = self.kwargs.get('id')
        author = get_object_or_404(User, id=author_id)
        if request.method == 'DELETE':
            subscription = get_object_or_404(Subscription, user=user, author=author)
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filter_backends = [IngredientFilter]
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAdminAuthorOrReadOnly]
    pagination_class = PageNumberPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeSerializer
        return RecipePostSerializer

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def add_to_favorites(self, request, id):
        recipe = get_object_or_404(Recipe, pk=id)
        data = {'user': request.user.pk, 'recipe': recipe.pk}
        serializer = FavoritesListSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def remove_from_favorites(self, request, id):
        recipe = get_object_or_404(Recipe, pk=id)
        fav_filter = FavoritesList.objects.filter(user=request.user, recipe=recipe)
        if fav_filter.exists():
            fav_filter.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def add_to_shopping_list(self, request, id):
        recipe = get_object_or_404(Recipe, pk=id)
        data = {'user': request.user.pk, 'recipe': recipe.pk}
        serializer = ShoppingListSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def remove_from_shopping_list(self, request, id):
        recipe = get_object_or_404(Recipe, pk=id)
        shop_filter = ShoppingList.objects.filter(user=request.user, recipe=recipe)
        if shop_filter.exists():
            shop_filter.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def download_shopping_list(self, request):
        ingredients = RecipeIngredient.objects.filter(recipe__shopping__user=request.user).values(
            'ingredient__name', 'ingredient__measurement_unit').annotate(quantity=Sum('quantity'))
        shop_list = []
        for ingredient in ingredients:
            name = ingredient['ingredient__name']
            quantity = ingredient['quantity']
            measurement_unit = ingredient['ingredient__measurement_unit']
            shop_list.append(f"{name} - {quantity} {measurement_unit}")

        ingredient_list = "Список покупок:\n"
        ingredient_list += ",\n".join(shop_list)
        response = HttpResponse(ingredient_list, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response
