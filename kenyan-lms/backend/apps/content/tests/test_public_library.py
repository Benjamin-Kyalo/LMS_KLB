"""Public library serializers expose safe artwork URLs only."""
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.content.models import ContentResource, DigitalTextbook, Publisher
from apps.core.constants import ContentStatus, ResourceAccessScope, ResourceDelivery


class PublicLibraryArtworkTests(APITestCase):
    def test_public_catalogues_return_local_artwork_urls(self):
        publisher = Publisher.objects.create(name="Open Library", code="OPENLIB")
        book = DigitalTextbook.objects.create(
            publisher=publisher,
            title="Open Biology",
            cover_image="/images/library/covers/cover-biology.png",
            license_type="OPEN",
            status=ContentStatus.PUBLISHED,
            published_at=timezone.now(),
        )
        resource = ContentResource.objects.create(
            title="Open biology reading",
            delivery=ResourceDelivery.LINK,
            external_url="https://openstax.org/books/biology-2e/pages/1-introduction",
            thumbnail_image="/images/library/thumbnails/thumb-science.png",
            status=ContentStatus.PUBLISHED,
            access_scope=ResourceAccessScope.PUBLIC,
            published_at=timezone.now(),
        )

        books = self.client.get(reverse("public-book-list"))
        self.assertEqual(books.status_code, status.HTTP_200_OK, books.data)
        row = next(item for item in books.data["results"] if item["id"] == book.id)
        self.assertEqual(row["cover_url"], "/images/library/covers/cover-biology.png")
        self.assertNotIn("cover_image", row)

        resources = self.client.get(reverse("public-resource-list"))
        self.assertEqual(resources.status_code, status.HTTP_200_OK, resources.data)
        item = next(row for row in resources.data["results"] if row["id"] == resource.id)
        self.assertEqual(item["thumbnail_url"], "/images/library/thumbnails/thumb-science.png")
        self.assertNotIn("thumbnail_image", item)
