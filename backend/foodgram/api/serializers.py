import base64

from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (FavoritesList, Ingredient, Recipe,
                            RecipeIngredient, ShoppingList, Tag)
from users.models import Subscription, User


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(imgstr), name='temp.' + ext
            )

        return super().to_internal_value(data)


class SignUpSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = ['email', 'id', 'username', 'first_name',
                  'last_name', 'password']


class CustUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed']

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (request.user.is_authenticated
                and Subscription.objects.filter(
                    user=request.user, author=obj).exists())


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'slug']


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(
        source='ingredient.id', read_only=True
    )
    name = serializers.CharField(
        source='ingredient.name', read_only=True
    )
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'measurement_unit', 'amount']


class RecipeIngredientPostSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source='ingredient'
    )
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'amount']


class InfoRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class RecipeSerializer(serializers.ModelSerializer):
    author = CustUserSerializer()
    tags = TagSerializer(many=True)
    ingredients = RecipeIngredientSerializer(
        many=True, read_only=True, source='recipe_ingr'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ['id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time']

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return FavoritesList.objects.filter(
            user=request.user, recipe_id=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return ShoppingList.objects.filter(
            user=request.user, recipe_id=obj
        ).exists()


class RecipePostSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientPostSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ['ingredients', 'tags', 'image',
                  'name', 'text', 'cooking_time']

    def validate_ingredients(self, ingredients):
        ingredient_list = [
            ingredient['ingredient'].id for ingredient in ingredients
        ]
        if len(set(ingredient_list)) != len(ingredient_list):
            raise serializers.ValidationError(
                'Ингредиенты должны быть уникальными!'
            )
        return ingredients

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        author = self.context.get('request').user
        recipe = Recipe.objects.create(author=author, **validated_data)
        for ingredient in ingredients:
            RecipeIngredient.objects.create(recipe=recipe, **ingredient)
        recipe.tags.set(tags_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)
        if ingredients_data is not None:
            instance.ingredients.clear()
            for ingredient in ingredients_data:
                RecipeIngredient.objects.create(
                    recipe=instance, **ingredient
                )
        if tags_data is not None:
            instance.tags.set(tags_data)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeSerializer(
            instance, context={'request': self.context.get('request')}
        ).data


class UserSubscriptionSerializer(CustUserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count')
        read_only_fields = ('email', 'username', 'first_name', 'last_name',
                            'is_subscribed', 'recipes', 'recipes_count')

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = None
        if request:
            recipes_limit = request.query_params.get('recipes_limit')
        recipes = Recipe.objects.filter(author__id=obj.id)
        if recipes_limit:
            recipes = Recipe.objects.filter(
                author__id=obj.id
            )[:int(recipes_limit)]
        return InfoRecipeSerializer(recipes, many=True, read_only=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author__id=obj.id).count()


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'author'),
                message='Вы уже подписаны на этого пользователя'
            )
        ]

    def validate(self, data):
        request = self.context.get('request')
        if request.user == data['author']:
            raise serializers.ValidationError(
                'Нельзя подписываться на самого себя!'
            )
        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        return UserSubscriptionSerializer(
            instance.author, context={'request': request}
        ).data


class ShoppingListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingList
        fields = ['user', 'recipe']

    def to_representation(self, instance):
        return InfoRecipeSerializer(
            instance.recipe, context={
                'request': self.context.get('request')}
        ).data


class FavoritesListSerializer(serializers.ModelSerializer):
    class Meta:
        model = FavoritesList
        fields = ['user', 'recipe']

    def to_representation(self, instance):
        return InfoRecipeSerializer(
            instance.recipe, context={
                'request': self.context.get('request')}
        ).data
