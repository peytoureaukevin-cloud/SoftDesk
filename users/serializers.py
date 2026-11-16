"""Transformation et validation des utilisateurs de l'API."""

from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Valide les utilisateurs et protège leur mot de passe."""

    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "password",
            "age",
            "can_be_contacted",
            "can_data_be_shared",
            "created_time",
        )
        read_only_fields = ("id", "created_time")

    def validate(self, attrs):
        if self.instance is None and not attrs.get("password"):
            raise serializers.ValidationError(
                {"password": "Un mot de passe est obligatoire."}
            )
        return attrs

    def validate_password(self, password):
        candidate = self.instance
        if candidate is None:
            candidate = User(username=self.initial_data.get("username", ""))
        try:
            password_validation.validate_password(password, candidate)
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.messages) from error
        return password

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save(update_fields=["password"])
        return instance
