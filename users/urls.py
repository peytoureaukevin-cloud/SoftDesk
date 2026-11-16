"""Routes d'inscription et de gestion du profil utilisateur."""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import UserRegistrationView, UserViewSet

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")

urlpatterns = [
    path("signup/", UserRegistrationView.as_view(), name="signup"),
] + router.urls
