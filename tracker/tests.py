import uuid

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Comment, Contributor, Issue, Project

User = get_user_model()
PASSWORD = "MotDePasseSolide2026!"


class ProjectContributorApiTests(APITestCase):
    """Vérifie le CRUD, l'isolation et la gestion des contributeurs."""

    def setUp(self):
        self.author = User.objects.create_user(
            username="project-author",
            password=PASSWORD,
            age=35,
        )
        self.contributor = User.objects.create_user(
            username="project-contributor",
            password=PASSWORD,
            age=28,
        )
        self.outsider = User.objects.create_user(
            username="project-outsider",
            password=PASSWORD,
            age=31,
        )
        self.project = Project.objects.create(
            title="API interne",
            description="Projet utilisé par les tests.",
            type=Project.Type.BACK_END,
            author=self.author,
        )
        Contributor.objects.create(project=self.project, user=self.author)
        Contributor.objects.create(project=self.project, user=self.contributor)
        self.client.force_authenticate(user=self.author)

    def contributor_list_url(self):
        return reverse(
            "contributor-list",
            kwargs={"project_pk": self.project.pk},
        )

    def test_project_creation_uses_connected_user_as_author_and_contributor(self):
        response = self.client.post(
            reverse("project-list"),
            {
                "title": "Application mobile",
                "description": "Projet Android.",
                "type": Project.Type.ANDROID,
                "author_id": self.outsider.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        project = Project.objects.get(pk=response.data["id"])
        self.assertEqual(project.author, self.author)
        self.assertTrue(
            Contributor.objects.filter(project=project, user=self.author).exists()
        )

    def test_project_author_can_use_crud(self):
        list_response = self.client.get(reverse("project-list"))
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data["count"], 1)

        detail_url = reverse("project-detail", kwargs={"pk": self.project.pk})
        detail_response = self.client.get(detail_url)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)

        update_response = self.client.patch(
            detail_url,
            {"title": "API interne modifiée"},
            format="json",
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)

        delete_response = self.client.delete(detail_url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

    def test_rejects_unknown_project_type(self):
        response = self.client.post(
            reverse("project-list"),
            {
                "title": "Type incorrect",
                "description": "Ce projet doit être refusé.",
                "type": "DESKTOP",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_project_author_can_add_and_remove_contributor(self):
        create_response = self.client.post(
            self.contributor_list_url(),
            {"user_id": self.outsider.id},
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

        detail_url = reverse(
            "contributor-detail",
            kwargs={
                "project_pk": self.project.pk,
                "pk": create_response.data["id"],
            },
        )
        delete_response = self.client.delete(detail_url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

    def test_rejects_duplicate_contributor(self):
        response = self.client.post(
            self.contributor_list_url(),
            {"user_id": self.author.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_author_cannot_be_removed_from_contributors(self):
        author_contribution = Contributor.objects.get(
            project=self.project,
            user=self.author,
        )
        response = self.client.delete(
            reverse(
                "contributor-detail",
                kwargs={
                    "project_pk": self.project.pk,
                    "pk": author_contribution.pk,
                },
            )
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_user_is_rejected(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(reverse("project-list"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_contributor_can_read_but_cannot_modify_project(self):
        self.client.force_authenticate(user=self.contributor)
        detail_url = reverse("project-detail", kwargs={"pk": self.project.pk})

        read_response = self.client.get(detail_url)
        update_response = self.client.patch(
            detail_url,
            {"title": "Modification interdite"},
            format="json",
        )

        self.assertEqual(read_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_outsider_cannot_see_project(self):
        self.client.force_authenticate(user=self.outsider)

        list_response = self.client.get(reverse("project-list"))
        detail_response = self.client.get(
            reverse("project-detail", kwargs={"pk": self.project.pk})
        )

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data["count"], 0)
        self.assertEqual(detail_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_non_author_cannot_manage_contributors(self):
        self.client.force_authenticate(user=self.contributor)

        response = self.client.post(
            self.contributor_list_url(),
            {"user_id": self.outsider.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_project_list_is_limited_to_ten_results_per_page(self):
        for number in range(10):
            project = Project.objects.create(
                title=f"Projet {number}",
                description="Projet créé pour vérifier la pagination.",
                type=Project.Type.BACK_END,
                author=self.author,
            )
            Contributor.objects.create(project=project, user=self.author)

        response = self.client.get(reverse("project-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 11)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIsNotNone(response.data["next"])


class IssueCommentApiTests(APITestCase):
    """Vérifie les relations, les auteurs et les permissions imbriquées."""

    def setUp(self):
        self.author = User.objects.create_user(
            username="issue-author",
            password=PASSWORD,
            age=34,
        )
        self.contributor = User.objects.create_user(
            username="issue-contributor",
            password=PASSWORD,
            age=29,
        )
        self.outsider = User.objects.create_user(
            username="issue-outsider",
            password=PASSWORD,
            age=31,
        )
        self.project = Project.objects.create(
            title="Portail client",
            description="Projet des issues et commentaires.",
            type=Project.Type.FRONT_END,
            author=self.author,
        )
        Contributor.objects.create(project=self.project, user=self.author)
        Contributor.objects.create(project=self.project, user=self.contributor)
        self.issue = Issue.objects.create(
            title="Corriger la connexion",
            description="Le message d'erreur doit être clarifié.",
            tag=Issue.Tag.BUG,
            priority=Issue.Priority.HIGH,
            status=Issue.Status.TO_DO,
            project=self.project,
            author=self.author,
            assignee=self.contributor,
        )
        self.client.force_authenticate(user=self.author)

    def issue_list_url(self):
        return reverse("issue-list", kwargs={"project_pk": self.project.pk})

    def issue_detail_url(self):
        return reverse(
            "issue-detail",
            kwargs={"project_pk": self.project.pk, "pk": self.issue.pk},
        )

    def comment_list_url(self):
        return reverse(
            "comment-list",
            kwargs={
                "project_pk": self.project.pk,
                "issue_pk": self.issue.pk,
            },
        )

    def comment_detail_url(self, comment):
        return reverse(
            "comment-detail",
            kwargs={
                "project_pk": self.project.pk,
                "issue_pk": self.issue.pk,
                "pk": comment.pk,
            },
        )

    def test_create_issue_uses_connected_user_as_author(self):
        response = self.client.post(
            self.issue_list_url(),
            {
                "title": "Ajouter un filtre",
                "description": "Filtrer les résultats par date.",
                "tag": Issue.Tag.FEATURE,
                "priority": Issue.Priority.MEDIUM,
                "author_id": self.outsider.id,
                "assignee_id": self.contributor.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        issue = Issue.objects.get(pk=response.data["id"])
        self.assertEqual(issue.author, self.author)
        self.assertEqual(issue.status, Issue.Status.TO_DO)
        self.assertEqual(issue.assignee, self.contributor)

    def test_rejects_assignee_who_is_not_a_contributor(self):
        response = self.client.post(
            self.issue_list_url(),
            {
                "title": "Assignation incorrecte",
                "description": "Cette issue doit être refusée.",
                "tag": Issue.Tag.TASK,
                "priority": Issue.Priority.LOW,
                "assignee_id": self.outsider.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_issue_author_can_use_crud(self):
        list_response = self.client.get(self.issue_list_url())
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data["count"], 1)

        detail_response = self.client.get(self.issue_detail_url())
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)

        update_response = self.client.patch(
            self.issue_detail_url(),
            {"status": Issue.Status.FINISHED},
            format="json",
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)

        delete_response = self.client.delete(self.issue_detail_url())
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

    def test_contributor_can_read_but_cannot_modify_other_authors_issue(self):
        self.client.force_authenticate(user=self.contributor)

        read_response = self.client.get(self.issue_detail_url())
        update_response = self.client.patch(
            self.issue_detail_url(),
            {"status": Issue.Status.FINISHED},
            format="json",
        )

        self.assertEqual(read_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_outsider_cannot_access_issues(self):
        self.client.force_authenticate(user=self.outsider)

        response = self.client.get(self.issue_list_url())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_comment_uses_connected_user_and_uuid(self):
        self.client.force_authenticate(user=self.contributor)

        response = self.client.post(
            self.comment_list_url(),
            {
                "description": "Je prends cette correction en charge.",
                "author_id": self.outsider.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        comment = Comment.objects.get(pk=response.data["id"])
        self.assertIsInstance(comment.pk, uuid.UUID)
        self.assertEqual(comment.issue, self.issue)
        self.assertEqual(comment.author, self.contributor)

    def test_comment_author_can_use_crud(self):
        comment = Comment.objects.create(
            issue=self.issue,
            author=self.contributor,
            description="Première version.",
        )
        self.client.force_authenticate(user=self.contributor)
        comment_url = self.comment_detail_url(comment)

        list_response = self.client.get(self.comment_list_url())
        detail_response = self.client.get(comment_url)
        update_response = self.client.patch(
            comment_url,
            {"description": "Version corrigée."},
            format="json",
        )
        delete_response = self.client.delete(comment_url)

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

    def test_non_author_cannot_modify_comment(self):
        comment = Comment.objects.create(
            issue=self.issue,
            author=self.contributor,
            description="Commentaire du contributeur.",
        )

        response = self.client.patch(
            self.comment_detail_url(comment),
            {"description": "Modification interdite."},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_outsider_cannot_access_comments(self):
        self.client.force_authenticate(user=self.outsider)

        response = self.client.get(self.comment_list_url())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_comment_url_checks_project_and_issue_relationship(self):
        other_project = Project.objects.create(
            title="Autre projet",
            description="Projet sans rapport avec l'issue.",
            type=Project.Type.IOS,
            author=self.author,
        )
        Contributor.objects.create(project=other_project, user=self.author)

        response = self.client.get(
            reverse(
                "comment-list",
                kwargs={
                    "project_pk": other_project.pk,
                    "issue_pk": self.issue.pk,
                },
            )
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
