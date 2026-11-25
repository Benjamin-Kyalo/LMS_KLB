"""Regression tests for safe public error responses."""
from unittest.mock import patch

from django.db import DatabaseError
from django.urls import reverse
from rest_framework.test import APITestCase


class HealthCheckSecurityTests(APITestCase):
    def test_database_failure_does_not_expose_driver_details(self):
        with patch(
            "apps.core.views.connection.cursor",
            side_effect=DatabaseError("host=secret-db password=secret"),
        ):
            response = self.client.get(reverse("health-check"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data["error"], "Database unavailable")
        self.assertNotIn("secret-db", str(response.data))
        self.assertNotIn("password", str(response.data))
