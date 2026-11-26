"""Authentication routes."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.accounts import views

router = DefaultRouter()
router.register("users", views.UserViewSet, basename="user")
router.register("roles", views.CustomRoleViewSet, basename="role")
router.register("admin-invitations", views.AdminInvitationViewSet, basename="admin-invitation")

urlpatterns = [
    path("csrf/", views.csrf_token, name="csrf-token"),
    path("capabilities/", views.capabilities, name="capabilities"),
    path("register/", views.register, name="register"),
    path("learner-lookup/", views.learner_lookup, name="learner-lookup"),
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    path("me/", views.me, name="me"),
    path("onboarding/me/", views.onboarding_me, name="onboarding-me"),
    path("password/change/", views.password_change, name="password-change"),
    path("password/reset/", views.password_reset_request, name="password-reset"),
    path("password/reset/confirm/", views.password_reset_confirm, name="password-reset-confirm"),
    path("", include(router.urls)),
]
