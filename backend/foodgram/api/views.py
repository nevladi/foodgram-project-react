from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from api.filters import RecipeFilter, IngredientFilter
from recipes.models import (Ingredient, Tag, RecipeIngredient, Recipe,
                            ShoppingList, FavoritesList)
from users.models import Subscription, User
from api.serializers import (TagSerializer, IngredientSerializer, UserSubscriptionSerializer,
                             SubscriptionSerializer, FavoritesListSerializer,
                             ShoppingListSerializer, RecipeSerializer, RecipePostSerializer)
from rest_framework.pagination import PageNumberPagination
from api.permissions import IsAdminAuthorOrReadOnly


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
    search_fields = ['^name']
    pagination_class = None


class SubscriptionGetView(ListAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get(self, request):
        user = request.user
        queryset = User.objects.filter(author__user=user)
        serializer = UserSubscriptionSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)


class SubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        data = {'user': request.user.pk, 'author': pk}
        serializer = SubscriptionSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk):
        author = get_object_or_404(User, pk=pk)
        sub_filter = Subscription.objects.filter(user=request.user, author=author)
        if sub_filter.exists():
            subscription = get_object_or_404(Subscription, user=request.user, author=author)
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)


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


class FavoritesListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def post(self, request, pk):
        data = {'user': request.user.pk, 'recipe': pk}
        if not FavoritesList.objects.filter(user=request.user, recipe__pk=pk).exists():
            serializer = FavoritesListSerializer(data=data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        fav_filter = FavoritesList.objects.filter(user=request.user, recipe=recipe)
        if fav_filter.exists():
            fav_filter.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class ShoppingListView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        data = {'user': request.user.pk, 'recipe': pk}
        recipe = get_object_or_404(Recipe, pk=pk)
        if not ShoppingList.objects.filter(user=request.user, recipe=recipe).exists():
            serializer = ShoppingListSerializer(data=data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        shop_filter = ShoppingList.objects.filter(user=request.user, recipe=recipe)
        if shop_filter.exists():
            shop_filter.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def download_shopping_list(request):
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
    response = JsonResponse({'ingredient_list': ingredient_list})
    response['Content-Disposition'] = 'attachment; filename="shopping_list.json"'
    return response
