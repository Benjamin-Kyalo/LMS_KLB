"""Read-only OneRoster-shaped routes and explicit protocol rejections."""
from django.urls import path

from apps.integration import views

urlpatterns = [
    path(
        "oneroster/v1p1/courses/", views.CoursesView.as_view(),
        name="oneroster-courses",
    ),
    path(
        "oneroster/v1p1/classes/", views.ClassesView.as_view(),
        name="oneroster-classes",
    ),
    path(
        "oneroster/v1p1/users/", views.UsersView.as_view(),
        name="oneroster-users",
    ),
    path(
        "oneroster/v1p1/enrollments/", views.EnrollmentsView.as_view(),
        name="oneroster-enrollments",
    ),
    path(
        "oneroster/v1p1/orgs/", views.OrgsView.as_view(),
        name="oneroster-orgs",
    ),
    path(
        "lti/launch/", views.unsupported_integration,
        {"feature": "lti_1_3_launch"}, name="integration-lti-unsupported",
    ),
    path(
        "oidc/", views.unsupported_integration,
        {"feature": "oidc"}, name="integration-oidc-unsupported",
    ),
    path(
        "jwks/", views.unsupported_integration,
        {"feature": "jwks"}, name="integration-jwks-unsupported",
    ),
    path(
        "oauth/token/", views.unsupported_integration,
        {"feature": "oauth_token"}, name="integration-oauth-unsupported",
    ),
]
