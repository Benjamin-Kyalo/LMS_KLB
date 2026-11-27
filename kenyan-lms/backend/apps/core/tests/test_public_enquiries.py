"""Public contact-form and platform review-queue checks."""
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.audit import SENSITIVE_FIELDS
from apps.core.constants import Roles
from apps.core.models import AuditLog, PublicEnquiry

User = get_user_model()

VALID_ENQUIRY = {
    "full_name": "Amina Hassan",
    "email": "amina@example.co.ke",
    "phone": "+254700000000",
    "organisation": "Example School",
    "category": "School registration",
    "subject": "Registration details",
    "message": "Please tell me what is needed to register our school.",
}


@override_settings(DEFAULT_THROTTLE_RATES={"public_enquiry": "1000/hour"})
class PublicEnquiryTests(APITestCase):
    def test_anonymous_submission_stores_a_reference_without_pii_in_audit(self):
        response = self.client.post(
            reverse("core-public-enquiry-submit"), VALID_ENQUIRY, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        enquiry = PublicEnquiry.objects.get()
        self.assertTrue(enquiry.reference.startswith("ENQ-"))
        self.assertEqual(response.data["reference"], enquiry.reference)
        self.assertEqual(enquiry.full_name, "Amina Hassan")
        self.assertEqual(enquiry.status, "NEW")

        audit = AuditLog.objects.get(action="public_enquiry.received")
        self.assertIsNone(audit.user)
        self.assertIsNone(audit.institution)
        self.assertEqual(audit.details["reference"], enquiry.reference)
        self.assertNotIn("full_name", audit.details)
        self.assertNotIn("email", audit.details)
        for field in SENSITIVE_FIELDS:
            self.assertNotIn(field, audit.details)

    def test_submission_requires_the_promised_fields(self):
        payload = dict(VALID_ENQUIRY)
        payload["subject"] = "   "
        response = self.client.post(
            reverse("core-public-enquiry-submit"), payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertIn("subject", response.data)
        self.assertFalse(PublicEnquiry.objects.exists())
        self.assertFalse(AuditLog.objects.exists())

    def test_unknown_fields_are_ignored(self):
        payload = dict(VALID_ENQUIRY, status="RESOLVED", reference="FAKE-1")
        response = self.client.post(
            reverse("core-public-enquiry-submit"), payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        enquiry = PublicEnquiry.objects.get()
        self.assertNotEqual(enquiry.reference, "FAKE-1")
        self.assertEqual(enquiry.status, "NEW")

    def test_review_queue_is_platform_admin_only(self):
        self.client.post(reverse("core-public-enquiry-submit"), VALID_ENQUIRY, format="json")
        enquiry = PublicEnquiry.objects.get()
        list_url = reverse("publicenquiry-list")

        self.assertEqual(
            self.client.get(list_url).status_code, status.HTTP_401_UNAUTHORIZED
        )

        school_admin = User.objects.create_user(
            username="school_admin", role=Roles.ADMIN
        )
        self.client.force_authenticate(user=school_admin)
        self.assertEqual(self.client.get(list_url).status_code, status.HTTP_403_FORBIDDEN)

        platform = User.objects.create_user(
            username="platform", role=Roles.SUPER_ADMIN
        )
        self.client.force_authenticate(user=platform)
        listed = self.client.get(list_url)
        self.assertEqual(listed.status_code, status.HTTP_200_OK, listed.data)
        self.assertEqual(listed.data["count"], 1)
        self.assertEqual(
            listed.data["results"][0]["reference"], enquiry.reference
        )

        detail_url = reverse("publicenquiry-detail", args=[enquiry.pk])
        updated = self.client.patch(detail_url, {"status": "IN_REVIEW"}, format="json")
        self.assertEqual(updated.status_code, status.HTTP_200_OK, updated.data)
        enquiry.refresh_from_db()
        self.assertEqual(enquiry.status, "IN_REVIEW")
        self.assertTrue(AuditLog.objects.filter(
            action="public_enquiry.status_changed", user=platform,
        ).exists())
