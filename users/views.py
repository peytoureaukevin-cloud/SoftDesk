from django.contrib.auth import get_user_model
from rest_framework import generics, mixins, permissions, viewsets

from .serializers import UserSerializer

User = get_user_model()


class UserRegistrationView(generics.CreateAPIView):
    """Permet à une personne non connectée de créer son compte."""

    queryset = User.objects.all().order_by("id")
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]


class UserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Permet à l'utilisateur connecté de gérer uniquement son profil."""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(pk=self.request.user.pk).order_by("id")
