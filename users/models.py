from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class User(AbstractUser):
    """Utilisateur SoftDesk avec les informations de consentement RGPD."""

    age = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(15), MaxValueValidator(120)]
    )
    can_be_contacted = models.BooleanField(default=False)
    can_data_be_shared = models.BooleanField(default=False)
    created_time = models.DateTimeField(auto_now_add=True)

    REQUIRED_FIELDS = ["age"]

    def __str__(self):
        return self.username
