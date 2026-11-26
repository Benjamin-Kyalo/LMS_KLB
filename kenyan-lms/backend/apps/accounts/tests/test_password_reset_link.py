"""Password-reset emails link to the configured frontend origin."""
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

User = get_user_model()


class PasswordResetLinkTests(TestCase):
    def setUp(self):
        cache.clear()

    @override_settings(FRONTEND_BASE_URL="https://lms.example.com")
    def test_reset_link_uses_frontend_origin(self):
        User.objects.create_user(
            username="resetmail", password="StrongPass123!",
            email="resetmail@example.com",
        )
        response = self.client.post(
            reverse("password-reset"), {"email": "resetmail@example.com"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(
            "https://lms.example.com/reset-password/", mail.outbox[0].body
        )
