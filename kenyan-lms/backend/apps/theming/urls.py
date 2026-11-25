from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.theming import views

router = DefaultRouter()
router.register("palettes", views.ThemePaletteViewSet, basename="theme-palette")

urlpatterns = [
    path("active/", views.active_theme, name="theme-active"),
    path(
        "site-content/image/",
        views.SiteImageView.as_view(),
        name="site-image",
    ),
    path(
        "site-content/image/<str:slot>/reset/",
        views.SiteImageResetView.as_view(),
        name="site-image-reset",
    ),
    path(
        "site-content/image/<str:slot>/",
        views.SiteImageSlotView.as_view(),
        name="site-image-slot",
    ),
    path(
        "site-content/hero-image/",
        views.SiteHeroImageView.as_view(),
        name="site-hero-image",
    ),
    path("site-content/", views.SiteContentView.as_view(), name="site-content"),
    path("", include(router.urls)),
]
