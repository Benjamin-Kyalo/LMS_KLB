"""Content routes."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.content import views

router = DefaultRouter()
router.register("publishers", views.PublisherInfoViewSet, basename="publisher")
router.register("textbooks", views.DigitalTextbookViewSet, basename="digitaltextbook")
router.register("chapters", views.ChapterViewSet, basename="chapter")
router.register("resources", views.ContentResourceViewSet, basename="contentresource")
router.register("collections", views.ResourceCollectionViewSet, basename="resourcecollection")
router.register("embed-providers", views.EmbedProviderViewSet, basename="embedprovider")
router.register("exercises", views.ExerciseViewSet, basename="exercise")
router.register("exercise-attempts", views.ExerciseAttemptViewSet, basename="exerciseattempt")
router.register("access", views.ContentAccessViewSet, basename="contentaccess")
router.register("available", views.AvailableTextbookViewSet, basename="availabletextbook")

urlpatterns = [
    path("facets/", views.ResourceFacetsView.as_view(), name="resource-facets"),
    path("public/books/", views.PublicTextbookCatalogueView.as_view(), name="public-book-list"),
    path("public/resources/", views.PublicResourceCatalogueView.as_view(), name="public-resource-list"),
    path("portal/resources/", views.PortalResourceCatalogueView.as_view(), name="portal-resource-list"),
    path("portal/documents/", views.PortalDocumentCatalogueView.as_view(), name="portal-document-list"),
    path("", include(router.urls)),
]
