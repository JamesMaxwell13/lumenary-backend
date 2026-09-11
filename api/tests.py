from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from notifications.models import NotificationEvent, NotificationStatus
from projects.models import Project, ProjectCategory, PublishStatus as ProjectPublishStatus
from rental.models import (
    AttributeType,
    PublishStatus as RentalPublishStatus,
    RentalAttribute,
    RentalAttributeValue,
    RentalCategory,
    RentalItem,
    RentalStatus,
)
from services.models import ServiceBlock


TEST_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "luminary-tests",
    }
}


@override_settings(
    CACHES=TEST_CACHES,
    CACHE_TIMEOUT=60,
    TELEGRAM_BOT_TOKEN="",
    TELEGRAM_CHAT_ID="",
)
class PublicApiTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

    def test_services_page_is_cached(self):
        ServiceBlock.objects.create(title="Preproduction", text="Planning", sort_order=1, is_active=True)

        first_response = self.client.get("/api/v1/pages/services/")
        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(len(first_response.data["items"]), 1)

        ServiceBlock.objects.create(title="Rental", text="Gear selection", sort_order=2, is_active=True)
        second_response = self.client.get("/api/v1/pages/services/")

        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(len(second_response.data["items"]), 1)

    def test_project_list_and_detail_return_only_published_projects(self):
        category = ProjectCategory.objects.create(title="Commercial", slug="commercial", is_active=True)
        published = Project.objects.create(
            category=category,
            title="Published project",
            slug="published-project",
            status=ProjectPublishStatus.PUBLISHED,
            published_at=timezone.now(),
        )
        Project.objects.create(
            category=category,
            title="Draft project",
            slug="draft-project",
            status=ProjectPublishStatus.DRAFT,
            published_at=timezone.now(),
        )

        list_response = self.client.get("/api/v1/projects/")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual([item["slug"] for item in list_response.data["results"]], [published.slug])

        detail_response = self.client.get(f"/api/v1/projects/{published.slug}/")
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.data["slug"], published.slug)

    def test_rental_categories_are_returned_as_tree(self):
        root = RentalCategory.add_root(title="Equipment", slug="equipment", is_active=True)
        root.add_child(title="Cameras", slug="cameras", is_active=True)

        response = self.client.get("/api/v1/rental/categories/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["slug"], "equipment")
        self.assertEqual(response.data[0]["children"][0]["slug"], "cameras")

    def test_rental_items_support_public_filters_and_attribute_filters(self):
        category = RentalCategory.add_root(title="Lights", slug="lights", is_active=True)
        power = RentalAttribute.objects.create(name="Power", slug="power", type=AttributeType.NUMBER)
        color = RentalAttribute.objects.create(name="Color", slug="color", type=AttributeType.CHOICE)
        first = self.create_rental_item(category, "Light 300", "light-300", price=100)
        second = self.create_rental_item(category, "Light 600", "light-600", price=300)
        unavailable = self.create_rental_item(
            category,
            "Unavailable light",
            "unavailable-light",
            price=200,
            status=RentalStatus.UNAVAILABLE,
        )
        RentalAttributeValue.objects.create(item=first, attribute=power, value_number=300)
        RentalAttributeValue.objects.create(item=first, attribute=color, value_choice="black")
        RentalAttributeValue.objects.create(item=second, attribute=power, value_number=600)
        RentalAttributeValue.objects.create(item=second, attribute=color, value_choice="silver")
        RentalAttributeValue.objects.create(item=unavailable, attribute=power, value_number=900)

        list_response = self.client.get("/api/v1/rental/items/")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(
            {item["slug"] for item in list_response.data["results"]},
            {"light-300", "light-600", "unavailable-light"},
        )

        status_response = self.client.get("/api/v1/rental/items/", {"status": RentalStatus.AVAILABLE})
        self.assertEqual({item["slug"] for item in status_response.data["results"]}, {"light-300", "light-600"})

        price_response = self.client.get("/api/v1/rental/items/", {"price_min": 200})
        self.assertEqual({item["slug"] for item in price_response.data["results"]}, {"light-600", "unavailable-light"})

        min_response = self.client.get("/api/v1/rental/items/", {"attributes.power_min": 400})
        self.assertEqual({item["slug"] for item in min_response.data["results"]}, {"light-600", "unavailable-light"})

        exact_response = self.client.get("/api/v1/rental/items/", {"attributes.color": "black"})
        self.assertEqual([item["slug"] for item in exact_response.data["results"]], ["light-300"])

        detail_response = self.client.get("/api/v1/rental/items/light-300/")
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.data["slug"], "light-300")

    def test_rental_filters_endpoint_returns_price_range_and_filterable_attributes(self):
        category = RentalCategory.add_root(title="Cameras", slug="cameras", is_active=True)
        RentalAttribute.objects.create(name="Mount", slug="mount", type=AttributeType.CHOICE, filterable=True)
        self.create_rental_item(category, "Camera", "camera", price=50)

        response = self.client.get("/api/v1/rental/filters/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["price"]["min"], 50)
        self.assertEqual(response.data["price"]["max"], 50)
        self.assertEqual(response.data["attributes"][0]["slug"], "mount")

    def test_contact_lead_creates_skipped_notification_without_telegram_settings(self):
        response = self.client.post(
            "/api/v1/leads/",
            {"name": "Ada", "phone": "+375291234567", "email": "ada@example.com", "message": "Hello"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        event = NotificationEvent.objects.get()
        self.assertEqual(event.status, NotificationStatus.SKIPPED)

    def test_rental_lead_accepts_only_published_active_items(self):
        category = RentalCategory.add_root(title="Props", slug="props", is_active=True)
        published = self.create_rental_item(category, "Chair", "chair", price=10)
        draft = self.create_rental_item(
            category,
            "Draft chair",
            "draft-chair",
            price=10,
            publication_status=RentalPublishStatus.DRAFT,
        )

        success_response = self.client.post(
            "/api/v1/rental/leads/",
            {
                "name": "Ada",
                "phone": "+375291234567",
                "items": [{"rental_item": published.slug, "quantity": 2}],
            },
            format="json",
        )
        self.assertEqual(success_response.status_code, 201)

        rejected_response = self.client.post(
            "/api/v1/rental/leads/",
            {
                "name": "Ada",
                "phone": "+375291234567",
                "items": [{"rental_item": draft.slug, "quantity": 1}],
            },
            format="json",
        )
        self.assertEqual(rejected_response.status_code, 400)

    def test_video_file_and_external_url_are_mutually_exclusive(self):
        project_category = ProjectCategory.objects.create(title="Film", slug="film")
        project = Project(
            category=project_category,
            title="Case",
            slug="case",
            video_file="project-videos/case.mp4",
            external_video_url="https://example.com/video",
        )
        with self.assertRaises(ValidationError):
            project.clean()

        rental_category = RentalCategory.add_root(title="Equipment", slug="equipment")
        rental_item = RentalItem(
            category=rental_category,
            title="Camera",
            slug="camera",
            video_file="rental-videos/camera.mp4",
            external_video_url="https://example.com/video",
        )
        with self.assertRaises(ValidationError):
            rental_item.clean()

    def test_openapi_and_docs_urls_are_available(self):
        self.assertEqual(self.client.get("/api/schema/").status_code, 200)
        self.assertEqual(self.client.get("/api/docs/").status_code, 200)

    def create_rental_item(
        self,
        category,
        title,
        slug,
        *,
        price,
        status=RentalStatus.AVAILABLE,
        publication_status=RentalPublishStatus.PUBLISHED,
    ):
        return RentalItem.objects.create(
            category=category,
            title=title,
            slug=slug,
            price=price,
            status=status,
            publication_status=publication_status,
            is_active=True,
            published_at=timezone.now(),
        )
