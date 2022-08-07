from django.contrib import admin
from django.shortcuts import get_object_or_404

from recipes.models import (
    Favorite,
    Ingredient,
    IngredientRecipe,
    Recipe,
    ShoppingCart,
    Tag,
)
from users.models import User


class IngredientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "measurement_unit")
    search_fields = ("name",)
    list_filter = ("measurement_unit",)


class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "color")
    search_fields = ("name", "slug")


class RecipeIngredientInline(admin.TabularInline):
    model = Recipe.ingredients.through
    extra = 1


class RecipeAdmin(admin.ModelAdmin):
    readonly_fields = ("favourite_count",)
    inlines = (RecipeIngredientInline,)
    list_display = ("id", "name", "author", "email")
    search_fields = ("name", "author__username", "author__email")
    list_filter = ("author", "tags")

    def email(self, obj):
        user = get_object_or_404(User, pk=obj.author.pk)
        return user.email

    def favourite_count(self, obj):
        return Favorite.objects.filter(recipe=obj).count()

    favourite_count.short_description = "Общее число добавлений в избранное"


class IngredientRecipeAdmin(admin.ModelAdmin):
    list_display = ("recipe", "ingredient", "amount")
    search_fields = ("ingredient__name", "recipe__name")


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ("user", "email", "recipe")
    search_fields = ("user__username", "user__email", "recipe__name")

    def email(self, obj):
        user = get_object_or_404(User, pk=obj.user.pk)
        return user.email


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "email", "recipe")
    search_fields = ("user__username", "user__email", "recipe__name")

    def email(self, obj):
        user = get_object_or_404(User, pk=obj.user.pk)
        return user.email


admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(IngredientRecipe, IngredientRecipeAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
