"""Transformation et validation des projets et contributeurs."""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Comment, Contributor, Issue, Project

User = get_user_model()


class ProjectSerializer(serializers.ModelSerializer):
    """Valide et représente un projet SoftDesk."""

    author_id = serializers.IntegerField(source="author.id", read_only=True)
    author_username = serializers.CharField(
        source="author.username",
        read_only=True,
    )

    class Meta:
        model = Project
        fields = [
            "id",
            "title",
            "description",
            "type",
            "author_id",
            "author_username",
            "created_time",
        ]
        read_only_fields = ["id", "created_time"]


class ContributorSerializer(serializers.ModelSerializer):
    """Valide et représente la participation d'un utilisateur à un projet."""

    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="user",
    )
    username = serializers.CharField(source="user.username", read_only=True)
    project_id = serializers.IntegerField(source="project.id", read_only=True)

    def validate_user_id(self, user):
        project = self.context["project"]
        if Contributor.objects.filter(project=project, user=user).exists():
            raise serializers.ValidationError(
                "Cet utilisateur contribue déjà à ce projet."
            )
        return user

    class Meta:
        model = Contributor
        fields = ["id", "project_id", "user_id", "username", "created_time"]
        read_only_fields = ["id", "project_id", "created_time"]


class IssueSerializer(serializers.ModelSerializer):
    """Valide et représente une issue rattachée à un projet."""

    project_id = serializers.IntegerField(source="project.id", read_only=True)
    author_id = serializers.IntegerField(source="author.id", read_only=True)
    author_username = serializers.CharField(
        source="author.username",
        read_only=True,
    )
    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="assignee",
        allow_null=True,
        required=False,
    )
    assignee_username = serializers.SerializerMethodField()

    def validate_assignee_id(self, assignee):
        if assignee is None:
            return assignee
        project = self.context["project"]
        if not Contributor.objects.filter(project=project, user=assignee).exists():
            raise serializers.ValidationError(
                "La personne assignée doit contribuer au projet."
            )
        return assignee

    def get_assignee_username(self, issue):
        if issue.assignee is None:
            return None
        return issue.assignee.username

    class Meta:
        model = Issue
        fields = [
            "id",
            "project_id",
            "title",
            "description",
            "tag",
            "priority",
            "status",
            "author_id",
            "author_username",
            "assignee_id",
            "assignee_username",
            "created_time",
        ]
        read_only_fields = ["id", "project_id", "created_time"]


class CommentSerializer(serializers.ModelSerializer):
    """Valide et représente un commentaire rattaché à une issue."""

    issue_id = serializers.IntegerField(source="issue.id", read_only=True)
    author_id = serializers.IntegerField(source="author.id", read_only=True)
    author_username = serializers.CharField(
        source="author.username",
        read_only=True,
    )

    class Meta:
        model = Comment
        fields = [
            "id",
            "issue_id",
            "description",
            "author_id",
            "author_username",
            "created_time",
        ]
        read_only_fields = ["id", "issue_id", "created_time"]
