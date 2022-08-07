from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from drf_base64.fields import Base64ImageField

from users.models import Follow
from .models import Tag, Ingredient, Recipe, IngredientRecipe, ShoppingCart

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("id", "name", "color", "slug")
        model = Tag
        read_only_fields = ("id", "name", "color", "slug")


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("id", "name", "measurement_unit")
        model = Ingredient
        read_only_fields = ("id", "name", "measurement_unit")


class AuthorSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if request.user.is_anonymous:
            return False
        return Follow.objects.filter(user=request.user, author=obj.pk).exists()

    class Meta:
        model = User
        fields = ("id", "email", "username", "first_name", "last_name", "is_subscribed")


class IngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = IngredientRecipe
        fields = ("id", "amount")


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source="ingredient.id", queryset=Ingredient.objects.all()
    )
    measurement_unit = serializers.CharField(
        source="ingredient.measurement_unit", read_only=True
    )
    name = serializers.CharField(source="ingredient.name", read_only=True)

    class Meta:
        model = IngredientRecipe
        fields = ("id", "name", "measurement_unit", "amount")
        validators = [
            UniqueTogetherValidator(
                queryset=IngredientRecipe.objects.all(), fields=("ingredient", "recipe")
            )
        ]


class RecipeListSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    tags = TagSerializer(many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    def get_ingredients(self, obj):
        queryset = IngredientRecipe.objects.filter(recipe=obj)
        return IngredientRecipeSerializer(queryset, many=True).data

    def get_is_favorited(self, obj):
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return Recipe.objects.filter(favorites_recipe__user=user, id=obj.id).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(user=user.id, recipe=obj.id).exists()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )


class RecipeSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())
    image = Base64ImageField()
    ingredients = IngredientCreateSerializer(many=True)

    def to_representation(self, instance):
        request = self.context.get("request")
        serializer = RecipeListSerializer(instance, context={"request": request})
        return serializer.data

    @transaction.atomic
    def create(self, validated_data):
        ingredients = (
            validated_data.pop("ingredients") if "ingredients" in validated_data else {}
        )
        tags = validated_data.pop("tags") if "tags" in validated_data else {}
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        for ingredient in ingredients:
            IngredientRecipe.objects.get_or_create(
                recipe=recipe, ingredient=ingredient["id"], amount=ingredient["amount"]
            )
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = (
            validated_data.pop("ingredients") if "ingredients" in validated_data else {}
        )
        tags = validated_data.pop("tags") if "tags" in validated_data else {}
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.tags.set(tags)
        instance.image = validated_data.get("image", instance.image)
        instance.ingredients.clear()
        for ingredient in ingredients:
            IngredientRecipe.objects.get_or_create(
                recipe=instance,
                ingredient=ingredient["id"],
                amount=ingredient["amount"],
            )
        return super().update(instance, validated_data)

    def validate(self, data):
        ingredient_data = self.initial_data.get("ingredients")
        ingredient_in_recipe = set()
        for ingredient in ingredient_data:
            ingredient_obj = get_object_or_404(Ingredient, id=ingredient["id"])
            if ingredient_obj in ingredient_in_recipe:
                raise serializers.ValidationError("Дубликат ингредиента")
            ingredient_in_recipe.add(ingredient_obj)
        return data

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
        )


class FollowRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")
