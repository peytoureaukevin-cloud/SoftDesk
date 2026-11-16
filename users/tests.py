from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from tracker.models import Comment, Contributor, Issue, Project

User = get_user_model()


class UserAuthenticationApiTests(APITestCase):
    """Vérifie l'inscription, JWT et la confidentialité des profils."""

    def setUp(self):
        self.password = "MotDePasseSolide2026!"
        self.user = User.objects.create_user(
            username="alice",
            password=self.password,
            age=30,
        )

    def test_signup_hashes_password_and_hides_it(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "bob",
                "password": self.password,
                "age": 25,
                "can_be_contacted": True,
                "can_data_be_shared": False,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="bob")
        self.assertTrue(user.check_password(self.password))
        self.assertNotIn("password", response.data)

    def test_signup_rejects_user_younger_than_fifteen(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "too-young",
                "password": self.password,
                "age": 14,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="too-young").exists())

    def test_token_pair_and_refresh_are_returned(self):
        token_response = self.client.post(
            reverse("token_obtain_pair"),
            {"username": self.user.username, "password": self.password},
            format="json",
        )

        self.assertEqual(token_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", token_response.data)
        self.assertIn("refresh", token_response.data)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )
        profile_response = self.client.get(reverse("user-list"))
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)

        self.client.credentials()

        refresh_response = self.client.post(
            reverse("token_refresh"),
            {"refresh": token_response.data["refresh"]},
            format="json",
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", refresh_response.data)

    def test_profile_endpoints_require_authentication(self):
        response = self.client.get(reverse("user-list"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_can_read_update_and_delete_own_profile(self):
        self.client.force_authenticate(user=self.user)

        list_response = self.client.get(reverse("user-list"))
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data["count"], 1)
        self.assertEqual(list_response.data["results"][0]["id"], self.user.id)

        detail_url = reverse("user-detail", kwargs={"pk": self.user.pk})
        detail_response = self.client.get(detail_url)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)

        update_response = self.client.patch(
            detail_url,
            {"can_be_contacted": True},
            format="json",
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.can_be_contacted)

        delete_response = self.client.delete(detail_url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())

    def test_user_cannot_access_another_profile(self):
        other_user = User.objects.create_user(
            username="other-user",
            password=self.password,
            age=27,
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.get(reverse("user-detail", kwargs={"pk": other_user.pk}))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_password_update_is_hashed(self):
        self.client.force_authenticate(user=self.user)
        new_password = "NouveauMotDePasse2026!"

        response = self.client.patch(
            reverse("user-detail", kwargs={"pk": self.user.pk}),
            {"password": new_password},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_password))
        self.assertNotIn("password", response.data)

    def test_account_deletion_removes_authored_resources(self):
        project = Project.objects.create(
            title="Projet à supprimer",
            description="Données liées au compte.",
            type=Project.Type.BACK_END,
            author=self.user,
        )
        Contributor.objects.create(project=project, user=self.user)
        issue = Issue.objects.create(
            title="Issue à supprimer",
            description="Donnée liée au projet.",
            tag=Issue.Tag.TASK,
            priority=Issue.Priority.LOW,
            project=project,
            author=self.user,
        )
        Comment.objects.create(
            issue=issue,
            author=self.user,
            description="Commentaire à supprimer.",
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.delete(
            reverse("user-detail", kwargs={"pk": self.user.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Project.objects.filter(pk=project.pk).exists())
        self.assertFalse(Issue.objects.filter(pk=issue.pk).exists())
        self.assertFalse(Comment.objects.exists())
