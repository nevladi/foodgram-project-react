from django.db import models
from django.contrib.auth.models import User


class Ingredient(models.Model):
    name = models.CharField(
        verbose_name='Ингредиент',
        max_length=100
    )
    unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=20
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} {self.unit}'


class Tag(models.Model):
    name = models.CharField(
        verbose_name='Тэг',
        max_length=100,
        unique=True
    )
    color = models.CharField(
        verbose_name='Цвет',
        max_length=7
    )
    slug = models.SlugField(
        verbose_name='slug',
        max_length=100,
        unique=True
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE
    )
    title = models.CharField(
        verbose_name='Название',
        max_length=200
    )
    image = models.ImageField(
        verbose_name='Изображение',
        upload_to='recipes/images/',
    )
    description = models.TextField(
        verbose_name='Описание'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты',
        through='RecipeIngredient',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Ингредиенты',
        related_name='recipes',
        through='RecipeTag',
    )
    cooking_time = models.IntegerField(
        'Время готовки'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-id']

    def __str__(self):
        return self.title


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingr',
        blank=True,
        null=True
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingr',
        blank=True,
        null=True
    )
    quantity = models.FloatField()

    class Meta:
        verbose_name = 'Рецепт с ингредиентом'
        verbose_name_plural = 'Рецепты с игридиентами'

    def __str__(self):
        return f"{self.recipe} {self.ingredient} - {self.quantity}"


class RecipeTag(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'Рецепт с тегом'
        verbose_name_plural = 'Рецепты с тегами'

    def __str__(self):
        return f"{self.recipe} - {self.tag}"


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='author',
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'


class FavoritesList(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Список избранного'
        verbose_name_plural = 'Списки избранного'

    def __str__(self):
        return f"{self.recipe} {self.user}"


class ShoppingList(models.Model):
    class PurchaseList(models.Model):
        user = models.ForeignKey(
            User,
            on_delete=models.CASCADE,
            related_name='shopping',
            verbose_name='Пользователь'
        )
        recipe = models.ForeignKey(
            Recipe,
            on_delete=models.CASCADE,
            related_name='shopping',
            verbose_name='Покупка'
        )

        class Meta:
            verbose_name = 'Список покупок'
            verbose_name_plural = 'Списки покупок'

        def __str__(self):
            return f"{self.recipe} {self.user}"
