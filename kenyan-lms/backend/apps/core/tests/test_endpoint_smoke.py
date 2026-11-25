"""Smoke-test every list endpoint so a wiring bug cannot reach production."""
from django.contrib.auth import get_user_model
from django.urls import get_resolver, reverse
from rest_framework.test import APIClient, APITestCase

from apps.core.constants import Roles
from apps.institutions.models import Institution, InstitutionType

User = get_user_model()


def list_url_names(patterns):
    names = []
    for pattern in patterns:
        if hasattr(pattern, "url_patterns"):
            names.extend(list_url_names(pattern.url_patterns))
            continue
        name = getattr(pattern, "name", None)
        if name and name.endswith("-list"):
            names.append(name)
    return sorted(set(names))


class EndpointSmokeTests(APITestCase):
    def setUp(self):
        kind = InstitutionType.objects.create(name="Primary", code="PRI")
        school = Institution.objects.create(name="Smoke School", code="SMK", institution_type=kind)
        self.admin = User.objects.create_user(
            username="smoke_admin", password="StrongPass123!",
            role=Roles.ADMIN, institution=school,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_all_list_endpoints_return_a_client_error_or_success(self):
        names = list_url_names(get_resolver().url_patterns)
        self.assertGreater(len(names), 25, "Router discovery unexpectedly found no endpoints.")
        for name in names:
            with self.subTest(endpoint=name):
                response = self.client.get(reverse(name))
                self.assertLess(
                    response.status_code, 500,
                    f"{name} ({reverse(name)}) returned {response.status_code}: {response.data}",
                )
