"""Authentication routes."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.accounts import views

router = DefaultRouter()
router.register("users", views.UserViewSet, basename="user")
router.register("admin-invitations", views.AdminInvitationViewSet, basename="admin-invitation")

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    path("me/", views.me, name="me"),
    path("password/change/", views.password_change, name="password-change"),
    path("password/reset/", views.password_reset_request, name="password-reset"),
    path("password/reset/confirm/", views.password_reset_confirm, name="password-reset-confirm"),
    path("", include(router.urls)),
]
