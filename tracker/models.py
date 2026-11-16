import uuid

from django.conf import settings
from django.db import models


class Project(models.Model):
    """Projet de développement suivi par SoftDesk."""

    class Type(models.TextChoices):
        BACK_END = "BACK_END", "Back-end"
        FRONT_END = "FRONT_END", "Front-end"
        IOS = "IOS", "iOS"
        ANDROID = "ANDROID", "Android"

    title = models.CharField(max_length=128)
    description = models.TextField()
    type = models.CharField(max_length=10, choices=Type.choices)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="authored_projects",
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="Contributor",
        related_name="contributed_projects",
    )
    created_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_time"]

    def __str__(self):
        return self.title


class Contributor(models.Model):
    """Lien entre un utilisateur et un projet auquel il participe."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="contributions",
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="contributors",
    )
    created_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "project"],
                name="unique_contributor_per_project",
            )
        ]
        ordering = ["created_time"]

    def __str__(self):
        return f"{self.user.username} - {self.project.title}"


class Issue(models.Model):
    """Problème, amélioration ou tâche appartenant à un projet."""

    class Tag(models.TextChoices):
        BUG = "BUG", "Bug"
        FEATURE = "FEATURE", "Amélioration"
        TASK = "TASK", "Tâche"

    class Priority(models.TextChoices):
        LOW = "LOW", "Faible"
        MEDIUM = "MEDIUM", "Moyenne"
        HIGH = "HIGH", "Élevée"

    class Status(models.TextChoices):
        TO_DO = "TO_DO", "À faire"
        IN_PROGRESS = "IN_PROGRESS", "En cours"
        FINISHED = "FINISHED", "Terminé"

    title = models.CharField(max_length=128)
    description = models.TextField()
    tag = models.CharField(max_length=7, choices=Tag.choices)
    priority = models.CharField(max_length=6, choices=Priority.choices)
    status = models.CharField(
        max_length=11,
        choices=Status.choices,
        default=Status.TO_DO,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="issues",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="authored_issues",
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="assigned_issues",
        null=True,
        blank=True,
    )
    created_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_time"]

    def __str__(self):
        return self.title


class Comment(models.Model):
    """Commentaire rattaché à une issue."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description = models.TextField()
    issue = models.ForeignKey(
        Issue,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="authored_comments",
    )
    created_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_time"]

    def __str__(self):
        return f"Commentaire {self.id} sur {self.issue.title}"
