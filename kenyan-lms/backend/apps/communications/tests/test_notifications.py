"""Notification inbox and preference checks."""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.communications.models import Notification, NotificationPreference
from apps.communications.services import notify_user
from apps.core.constants import Roles
from apps.institutions.models import Institution, InstitutionType

User = get_user_model()


class NotificationCentreTests(APITestCase):
    def setUp(self):
        kind = InstitutionType.objects.create(name="Notice Primary", code="NTP")
        school = Institution.objects.create(
            name="Notice School", code="NOTC", institution_type=kind
        )
        self.user = User.objects.create_user(
            username="demo_user", role=Roles.ADMIN, institution=school
        )
        self.other = User.objects.create_user(
            username="demo_other", role=Roles.TEACHER, institution=school
        )
        self.notification = notify_user(
            self.user, "Welcome", "A test alert", "SYSTEM", "/admin"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_inbox_is_private_and_mark_read_actions_work(self):
        foreign = notify_user(self.other, "Private", "Not for you", "SYSTEM")
        response = self.client.get(reverse("notification-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        ids = [row["id"] for row in response.data["results"]]
        self.assertIn(self.notification.pk, ids)
        self.assertNotIn(foreign.pk, ids)

        count = self.client.get(reverse("notification-unread-count"))
        self.assertEqual(count.data["count"], 1)
        blocked = self.client.post(reverse("notification-mark-read", args=[foreign.pk]))
        self.assertEqual(blocked.status_code, status.HTTP_404_NOT_FOUND)

        marked = self.client.post(reverse("notification-mark-read", args=[self.notification.pk]))
        self.assertEqual(marked.status_code, status.HTTP_200_OK, marked.data)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)
        self.assertEqual(self.client.get(reverse("notification-unread-count")).data["count"], 0)

    def test_clients_cannot_create_or_delete_notifications(self):
        self.assertEqual(
            self.client.post(reverse("notification-list"), {"title": "Fake"}).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        self.assertEqual(
            self.client.delete(reverse("notification-detail", args=[self.notification.pk])).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        self.client.post(reverse("notification-mark-all-read"))
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_preferences_suppress_in_app_notifications(self):
        NotificationPreference.objects.create(user=self.user, in_app=False)
        self.assertIsNone(notify_user(self.user, "Suppressed", "No inbox row"))
        NotificationPreference.objects.filter(user=self.user).update(
            in_app=True, types=["ACADEMIC"]
        )
        self.assertIsNone(notify_user(self.user, "Wrong type", "No inbox row", "SYSTEM"))
        self.assertIsNotNone(notify_user(self.user, "Allowed", "Inbox row", "ACADEMIC"))
        self.assertEqual(Notification.objects.filter(recipient=self.user).count(), 2)
