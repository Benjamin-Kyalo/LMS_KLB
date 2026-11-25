"""Security regression tests for authentication and password recovery."""
import re
import time

from django.core import mail
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.test import override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.accounts.models import LoginAttempt, PasswordResetUse
from apps.core.constants import Roles
from apps.institutions.models import Institution, InstitutionType

User = get_user_model()


class LoginSecurityTests(APITestCase):
    def _user(self, username="secureuser", password="StrongPass123!"):
        return User.objects.create_user(
            username=username, password=password, role=Roles.LEARNER
        )

    def test_password_is_stored_with_pbkdf2_not_plain_text(self):
        # conftest.py uses a fast hasher for speed; explicitly check the
        # production hasher here so this security guarantee is still covered.
        with override_settings(
            PASSWORD_HASHERS=["django.contrib.auth.hashers.PBKDF2PasswordHasher"]
        ):
            user = self._user()
        self.assertNotEqual(user.password, "StrongPass123!")
        self.assertTrue(user.password.startswith("pbkdf2_sha256$"))

    def test_failed_logins_trigger_a_temporary_lockout(self):
        self._user("lockme")
        payload = {"username": "lockme", "password": "wrong-password"}
        for _ in range(5):
            response = self.client.post(reverse("login"), payload)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        locked = self.client.post(reverse("login"), payload)
        self.assertEqual(locked.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Too many sign-in attempts", str(locked.data))
        self.assertTrue(LoginAttempt.objects.filter(username="lockme").exists())

        correct = self.client.post(reverse("login"), {
            "username": "lockme", "password": "StrongPass123!"
        })
        self.assertEqual(correct.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(TRUSTED_PROXY_IPS=[])
    def test_rotating_forwarded_header_cannot_bypass_lockout(self):
        self._user("xffuser")
        for index in range(5):
            self.client.post(
                reverse("login"),
                {"username": "xffuser", "password": "wrong"},
                HTTP_X_FORWARDED_FOR=f"10.0.0.{index + 1}",
            )
        response = self.client.post(
            reverse("login"),
            {"username": "xffuser", "password": "wrong"},
            HTTP_X_FORWARDED_FOR="10.0.0.99",
        )
        self.assertIn("Too many sign-in attempts", str(response.data))

    def test_successful_login_clears_the_failure_counter(self):
        self._user("recovery")
        self.client.post(reverse("login"), {"username": "recovery", "password": "wrong"})
        self.client.post(reverse("login"), {
            "username": "recovery", "password": "StrongPass123!"
        })
        self.assertFalse(LoginAttempt.objects.filter(username="recovery").exists())

    def test_logout_invalidates_the_session(self):
        self._user("logoutuser")
        self.client.post(reverse("login"), {
            "username": "logoutuser", "password": "StrongPass123!"
        })
        self.assertEqual(self.client.get(reverse("me")).status_code, status.HTTP_200_OK)
        self.client.post(reverse("logout"))
        self.assertEqual(self.client.get(reverse("me")).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_session_writes_require_a_csrf_token(self):
        self._user("csrfuser")
        strict_client = APIClient(enforce_csrf_checks=True)
        login = strict_client.post(reverse("login"), {
            "username": "csrfuser", "password": "StrongPass123!"
        })
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        csrf_token = strict_client.cookies["csrftoken"].value

        blocked = strict_client.patch(
            reverse("me"), {"first_name": "Blocked"}, format="json"
        )
        self.assertEqual(blocked.status_code, status.HTTP_403_FORBIDDEN)

        allowed = strict_client.patch(
            reverse("me"), {"first_name": "Allowed"}, format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(allowed.status_code, status.HTTP_200_OK)

    def test_csrf_endpoint_sets_cookie_for_anonymous_visitors(self):
        response = self.client.get(reverse("csrf-token"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("csrftoken", response.cookies)


class PasswordResetTests(APITestCase):
    def setUp(self):
        kind = InstitutionType.objects.create(name="Primary", code="PRST")
        school = Institution.objects.create(name="Reset School", code="RS1", institution_type=kind)
        self.user = User.objects.create_user(
            username="resetuser", email="reset@example.invalid",
            password="OldStrongPass123!", role=Roles.LEARNER, institution=school,
        )

    def _request_link(self):
        response = self.client.post(reverse("password-reset"), {"email": self.user.email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = mail.outbox[-1].body
        match = re.search(r"/reset-password/([^/]+)/([^/\s]+)/", body)
        self.assertIsNotNone(match)
        return match.group(1), match.group(2)

    def test_reset_request_does_not_reveal_unknown_emails(self):
        known = self.client.post(reverse("password-reset"), {"email": self.user.email})
        unknown = self.client.post(reverse("password-reset"), {"email": "missing@example.invalid"})
        self.assertEqual(known.data, unknown.data)
        self.assertEqual(len(mail.outbox), 1)

    def test_repeated_legitimate_reset_requests_do_not_lock_the_flow(self):
        for _ in range(5):
            response = self.client.post(reverse("password-reset"), {"email": self.user.email})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 5)

    def test_reset_token_works_once_only(self):
        uid, token = self._request_link()
        payload = {
            "uid": uid, "token": token, "new_password": "NewStrongPass123!"
        }
        first = self.client.post(reverse("password-reset-confirm"), payload)
        self.assertEqual(first.status_code, status.HTTP_200_OK, first.data)
        self.assertTrue(
            self.client.login(username="resetuser", password="NewStrongPass123!")
        )

        second = self.client.post(reverse("password-reset-confirm"), payload)
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already been used", str(second.data))
        self.assertEqual(PasswordResetUse.objects.filter(user=self.user).count(), 1)

    def test_expired_reset_token_is_rejected(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        old_timestamp = format(int(time.time()) - 100000, "x")
        expired_token = f"{old_timestamp}-{token.split('-', 1)[1]}"
        response = self.client.post(reverse("password-reset-confirm"), {
            "uid": uid, "token": expired_token, "new_password": "AnotherStrongPass123!"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("expired", str(response.data))


@override_settings(
    SECURITY_HEADERS={
        "Content-Security-Policy": "default-src 'self'",
        "Permissions-Policy": "camera=()",
    }
)
class SecurityHeaderTests(APITestCase):
    def test_configured_headers_are_added_to_responses(self):
        response = self.client.get(reverse("health-check"))
        self.assertEqual(response["Content-Security-Policy"], "default-src 'self'")
        self.assertEqual(response["Permissions-Policy"], "camera=()")

    def test_authenticated_api_responses_are_not_cached(self):
        user = User.objects.create_user(username="headeruser", password="StrongPass123!")
        self.client.force_authenticate(user=user)
        response = self.client.get(reverse("me"))
        self.assertEqual(response["Cache-Control"], "no-store")


class ProfileValidationTests(APITestCase):
    def setUp(self):
        kind = InstitutionType.objects.create(name="Primary", code="PRF")
        school = Institution.objects.create(
            name="Profile School", code="PRF1", institution_type=kind
        )
        self.user = User.objects.create_user(
            username="profileuser", password="StrongPass123!",
            role=Roles.LEARNER, institution=school,
        )
        self.client.force_authenticate(user=self.user)

    def test_profile_patch_validates_email_and_lengths(self):
        invalid = self.client.patch(reverse("me"), {"email": "not-an-email"})
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)

        too_long = self.client.patch(reverse("me"), {"first_name": "x" * 200})
        self.assertEqual(too_long.status_code, status.HTTP_400_BAD_REQUEST)

        self.user.refresh_from_db()
        self.assertNotEqual(self.user.email, "not-an-email")

    def test_learner_cannot_enumerate_user_accounts(self):
        User.objects.create_user(
            username="someone-else", password="StrongPass123!",
            role=Roles.LEARNER, institution=self.user.institution,
        )
        response = self.client.get(reverse("user-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([row["id"] for row in response.data["results"]], [self.user.pk])


@override_settings(
    DEFAULT_THROTTLE_RATES={"auth_login": "2/minute"},
    LOGIN_FAIL_MAX=100,
)
class LoginThrottleTests(APITestCase):
    def setUp(self):
        cache.clear()
        User.objects.create_user(username="throttled", password="StrongPass123!")

    def tearDown(self):
        cache.clear()

    def test_login_throttle_returns_429_after_the_configured_limit(self):
        payload = {"username": "throttled", "password": "StrongPass123!"}
        for _ in range(2):
            self.assertEqual(
                self.client.post(reverse("login"), payload).status_code,
                status.HTTP_200_OK,
            )
        self.assertEqual(
            self.client.post(reverse("login"), payload).status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
        )
