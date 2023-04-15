from django.contrib import admin

from .models import FavoritesList, Ingredient, Recipe, ShoppingList, Tag, RecipeIngredient


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ['pk', 'name', 'measurement_unit']
    search_fields = ['name']
    list_filter = ['name']
    empty_value_display = '-----'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['pk', 'name', 'color', 'slug']
    search_fields = ['name', 'color', 'slug']
    list_filter = ['name', 'color', 'slug']
    empty_value_display = '-----'


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ['pk', 'name', 'author', 'favorites']
    search_fields = ['name', 'author']
    list_filter = ['name', 'author', 'tags']
    empty_value_display = '-----'
    inlines = [
        RecipeIngredientInline,
    ]

    def favorites(self, obj):
        return FavoritesList.objects.filter(recipe=obj).count()


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ['pk', 'recipe', 'ingredient', 'quantity']
    empty_value_display = '-----'


@admin.register(ShoppingList)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'recipe']
    search_fields = ['user__username', 'user__email']
    empty_value_display = '-----'


@admin.register(FavoritesList)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'recipe']
    search_fields = ['user__username', 'user__email']
    empty_value_display = '-----'
