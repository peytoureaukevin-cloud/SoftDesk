"""Permissions métier appliquées aux ressources SoftDesk."""

from rest_framework import permissions

from .models import Comment, Contributor, Issue, Project


def get_project_from_object(obj):
    """Retrouve le projet auquel appartient une ressource."""

    if isinstance(obj, Project):
        return obj
    if isinstance(obj, (Contributor, Issue)):
        return obj.project
    if isinstance(obj, Comment):
        return obj.issue.project
    return None


class IsProjectContributor(permissions.BasePermission):
    """Réserve les ressources d'un projet à ses contributeurs."""

    message = "Vous devez contribuer à ce projet pour accéder à cette ressource."

    def has_permission(self, request, view):
        project_pk = view.kwargs.get("project_pk")
        if project_pk is None:
            return True
        return Contributor.objects.filter(
            project_id=project_pk,
            user=request.user,
        ).exists()

    def has_object_permission(self, request, view, obj):
        project = get_project_from_object(obj)
        return (
            project is not None
            and Contributor.objects.filter(
                project=project,
                user=request.user,
            ).exists()
        )


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Autorise la lecture aux contributeurs et l'écriture au seul auteur."""

    message = "Seul l'auteur peut modifier ou supprimer cette ressource."

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author_id == request.user.id


class IsProjectAuthorForContributorManagement(permissions.BasePermission):
    """Réserve l'ajout et le retrait de contributeurs à l'auteur du projet."""

    message = "Seul l'auteur du projet peut gérer ses contributeurs."

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return Project.objects.filter(
            pk=view.kwargs.get("project_pk"),
            author=request.user,
        ).exists()

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.project.author_id == request.user.id
