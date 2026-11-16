from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import mixins, permissions, viewsets
from rest_framework.exceptions import ValidationError

from .models import Comment, Contributor, Issue, Project
from .permissions import (
    IsAuthorOrReadOnly,
    IsProjectAuthorForContributorManagement,
    IsProjectContributor,
)
from .serializers import (
    CommentSerializer,
    ContributorSerializer,
    IssueSerializer,
    ProjectSerializer,
)


class ProjectViewSet(viewsets.ModelViewSet):
    """Fournit les opérations CRUD sur les projets."""

    serializer_class = ProjectSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        IsProjectContributor,
        IsAuthorOrReadOnly,
    ]

    def get_queryset(self):
        return (
            Project.objects.filter(contributors__user=self.request.user)
            .select_related("author")
            .distinct()
        )

    @transaction.atomic
    def perform_create(self, serializer):
        project = serializer.save(author=self.request.user)
        Contributor.objects.create(project=project, user=self.request.user)


class ContributorViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Liste, ajoute, consulte et retire les contributeurs d'un projet."""

    serializer_class = ContributorSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        IsProjectContributor,
        IsProjectAuthorForContributorManagement,
    ]

    def get_project(self):
        if not hasattr(self, "_project"):
            self._project = get_object_or_404(
                Project.objects.select_related("author"),
                pk=self.kwargs["project_pk"],
            )
        return self._project

    def get_queryset(self):
        return Contributor.objects.filter(project=self.get_project()).select_related(
            "user",
            "project",
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["project"] = self.get_project()
        return context

    def perform_create(self, serializer):
        serializer.save(project=self.get_project())

    def perform_destroy(self, instance):
        if instance.user_id == instance.project.author_id:
            raise ValidationError(
                "L'auteur doit rester contributeur de son propre projet."
            )
        instance.delete()


class IssueViewSet(viewsets.ModelViewSet):
    """Fournit le CRUD des issues d'un projet."""

    serializer_class = IssueSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        IsProjectContributor,
        IsAuthorOrReadOnly,
    ]

    def get_project(self):
        if not hasattr(self, "_project"):
            self._project = get_object_or_404(
                Project.objects.select_related("author"),
                pk=self.kwargs["project_pk"],
            )
        return self._project

    def get_queryset(self):
        return Issue.objects.filter(project=self.get_project()).select_related(
            "project",
            "author",
            "assignee",
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["project"] = self.get_project()
        return context

    def perform_create(self, serializer):
        serializer.save(
            project=self.get_project(),
            author=self.request.user,
        )


class CommentViewSet(viewsets.ModelViewSet):
    """Fournit le CRUD des commentaires d'une issue."""

    serializer_class = CommentSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        IsProjectContributor,
        IsAuthorOrReadOnly,
    ]

    def get_issue(self):
        if not hasattr(self, "_issue"):
            self._issue = get_object_or_404(
                Issue.objects.select_related("project"),
                pk=self.kwargs["issue_pk"],
                project_id=self.kwargs["project_pk"],
            )
        return self._issue

    def get_queryset(self):
        return Comment.objects.filter(issue=self.get_issue()).select_related(
            "issue",
            "author",
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["issue"] = self.get_issue()
        return context

    def perform_create(self, serializer):
        serializer.save(
            issue=self.get_issue(),
            author=self.request.user,
        )
