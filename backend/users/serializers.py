from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import serializers


from .models import Follow

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        if "request" not in self.context or self.context["request"].user.is_anonymous:
            return False
        return Follow.objects.filter(
            author=obj, user=self.context["request"].user
        ).exists()

    class Meta:
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "password",
            "is_subscribed",
        )
        extra_kwargs = {"password": {"write_only": True}}
        model = User

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class FollowSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source="recipes.count", read_only=True)

    def get_recipes(self, obj):
        # TODO implement after creating "recipes" app
        pass

    def get_is_subscribed(self, obj):
        if self.context["request"].user.is_anonymous:
            return False
        return Follow.objects.filter(
            author=obj, user=self.context["request"].user
        ).exists()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )
