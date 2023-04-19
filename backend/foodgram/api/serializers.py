from rest_framework import serializers
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (Ingredient, Tag, RecipeIngredient, Recipe,
                            RecipeTag, ShoppingList, FavoritesList)
from users.models import Subscription, User


class SignUpSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = ['email', 'username', 'first_name', 'last_name', 'password']


class CastUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'is_subscribed']

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(user=request.user, author=obj).exists()


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'slug']


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    name = serializers.ReadOnlyField()
    measurement_unit = serializers.ReadOnlyField()

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'quantity', 'measurement_unit']


class InfoRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeSerializer(serializers.ModelSerializer):
    author = SignUpSerializer(read_only=True)
    tags = TagSerializer(many=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_shopping_list = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'title', 'image', 'text', 'ingredients',
                  'cooking_time', 'is_favorited', 'is_shopping_list')

    def get_ingredients(self, obj):
        ingredients = RecipeIngredient.objects.filter(recipe=obj)
        return RecipeIngredientSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return FavoritesList.objects.filter(user=user).exists()
        return False

    def get_is_shopping_list(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return ShoppingList.objects.filter(user=user).exists()
        return False


class IngredientRecipePostSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    quantity = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'quantity']


class RecipePostSerializer(serializers.ModelSerializer):
    ingredients = IngredientRecipePostSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ['ingredients', 'tags', 'image', 'name', 'text', 'cooking_time']

    def validate(self, data):
        ingredients = self.initial_data.get('ingredients')
        ingredient_list = [ingredient['id'] for ingredient in ingredients]
        for ingredient in ingredients:
            quantity = int(ingredient['quantity'])
            if quantity < 1:
                raise serializers.ValidationError('Количество не может быть меньше 1!')
            if ingredient_list.count(ingredient['id']) > 1:
                raise serializers.ValidationError('Ингредиенты должны быть уникальными!')
        return data

    def create_ingredients(self, ingredients, recipe):
        ingredients = [RecipeIngredient(
                ingredient=Ingredient.objects.get(id=ingredient['id']),
                quantity=ingredient['quantity'],
                recipe=recipe,
            ) for ingredient in ingredients]
        RecipeIngredient.objects.bulk_create(ingredients)

    def create_tags(self, tags, recipe):
        tags = [RecipeTag(tag=tag, recipe=recipe) for tag in tags]
        RecipeTag.objects.bulk_create(tags)

    def create(self, validated_data):
        request = self.context.get('request')
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(author=request.user, **validated_data)
        self.create_ingredients(ingredients, recipe)
        self.create_tags(tags, recipe)
        return recipe

    def update(self, instance, validated_data):
        RecipeTag.objects.filter(recipe=instance).delete()
        RecipeIngredient.objects.filter(recipe=instance).delete()
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        self.create_ingredients(ingredients, instance)
        self.create_tags(tags, instance)
        instance.name = validated_data.pop('name')
        instance.text = validated_data.pop('text')
        if validated_data.get('image'):
            instance.image = validated_data.pop('image')
        instance.cooking_time = validated_data.pop('cooking_time')
        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeSerializer(instance, context={'request': self.context.get('request')}).data


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['user', 'author']
        validators = [
            UniqueTogetherValidator(queryset=Subscription.objects.all(), fields=('user', 'author'))]

    def validate(self, data):
        if data['user'] == data['author']:
            raise serializers.ValidationError('Нельзя подпиcаться на самого себя!')
        return data


class UserSubscriptionSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'is_subscribed', 'recipes', 'recipes_count']

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(user=request.user, author=obj).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = None
        if request:
            limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = obj.recipes.all()[:int(limit)]
        return InfoRecipeSerializer(recipes, many=True, context={'request': request}).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()


class ShoppingListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingList
        fields = ['user', 'recipe']

    def to_representation(self, instance):
        return InfoRecipeSerializer(instance.recipe, context={'request': self.context.get('request')}).data


class FavoritesListSerializer(serializers.ModelSerializer):
    class Meta:
        model = FavoritesList
        fields = ['user', 'recipe']

    def to_representation(self, instance):
        return InfoRecipeSerializer(instance.recipe, context={'request': self.context.get('request')}).data
