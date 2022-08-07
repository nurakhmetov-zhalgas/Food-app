from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.http import HttpResponse
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models.aggregates import Sum
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404


from .serializers import (
    TagSerializer,
    IngredientSerializer,
    RecipeSerializer,
    FollowRecipeSerializer,
)
from .models import Tag, Ingredient, Recipe, Favorite, ShoppingCart, IngredientRecipe
from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthenticatedOwnerOrReadOnly


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    pagination_class = None
    permission_classes = (AllowAny,)
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    pagination_class = None
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (IngredientFilter,)
    search_fields = ("^name",)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthenticatedOwnerOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @staticmethod
    def favorite_shopping(request, pk, work_model, errors):
        if request.method == "POST":
            if work_model.objects.filter(user=request.user, recipe__id=pk).exists():
                return Response(
                    {"errors": errors["recipe_in"]}, status=status.HTTP_400_BAD_REQUEST
                )
            recipe = get_object_or_404(Recipe, id=pk)
            work_model.objects.create(user=request.user, recipe=recipe)
            serializer = FollowRecipeSerializer(recipe, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        recipe = work_model.objects.filter(user=request.user, recipe__id=pk)
        if recipe.exists():
            work_model.objects.filter(user=request.user, recipe__id=pk).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {"errors": errors["recipe_not_in"]}, status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        methods=["post", "delete"], permission_classes=[IsAuthenticated], detail=True
    )
    def favorite(self, request, pk):
        return self.favorite_shopping(
            request,
            pk,
            Favorite,
            {
                "recipe_in": "Рецепт уже был добавлен в избранное",
                "recipe_not_in": "Этого рецепта нет в избранных",
            },
        )

    @action(
        methods=["post", "delete"], permission_classes=[IsAuthenticated], detail=True
    )
    def shopping_cart(self, request, pk):
        return self.favorite_shopping(
            request,
            pk,
            ShoppingCart,
            {
                "recipe_in": "Рецепт уже был добавлен в корзину",
                "recipe_not_in": "Этого рецепта нет в корзине",
            },
        )

    @action(methods=["get"], permission_classes=[IsAuthenticated], detail=False)
    def download_shopping_cart(self, request):
        ingredientrecipe_list = (
            IngredientRecipe.objects.filter(recipe__carts__user=request.user)
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(sum_amount=Sum("amount"))
        )
        content = ""
        if ingredientrecipe_list:
            for index, item in enumerate(ingredientrecipe_list, start=1):
                content += (
                    f'{index}. {item["ingredient__name"]} - '
                    f'{item["sum_amount"]} '
                    f'{item["ingredient__measurement_unit"]}'
                )
        else:
            content += "Список покупок пуст"
        return HttpResponse(
            content,
            content_type="text/plai, charset=utf8",
            headers={"Content-Disposition": "attachment; filename=shopping_cart.txt"},
        )
