from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from wagtail.admin.menu import MenuItem
from wagtail.snippets.models import get_snippet_models

from cms.models import ContactSettings, HomePage, MainPageSectionSettings
from cms.wagtail_hooks import (
    PortfolioGroup,
    RentalCategoryForm,
    RentalGroup,
    ServicesGroup,
    arrange_main_menu,
    register_contacts_menu_item,
)
from projects.models import Project, ProjectCategory, PublishStatus as ProjectPublishStatus
from rental.api import search_variants
from rental.models import (
    PublishStatus as RentalPublishStatus,
    RentalCategory,
    RentalItem,
    RentalStatus,
)
from services.models import ServiceBlock


TEST_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "Lumenary-tests",
    }
}


@override_settings(CACHES=TEST_CACHES, CACHE_TIMEOUT=60)
class PublicApiTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

    def test_services_page_cache_is_invalidated_when_content_changes(self):
        ServiceBlock.objects.create(title="Preproduction", text="Planning", sort_order=1, is_active=True)

        first_response = self.client.get("/api/v1/pages/services/")
        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(len(first_response.data["items"]), 1)

        ServiceBlock.objects.create(title="Rental", text="Gear selection", sort_order=2, is_active=True)
        second_response = self.client.get("/api/v1/pages/services/")

        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(len(second_response.data["items"]), 2)

    def test_wagtail_registers_content_snippets_only(self):
        snippet_models = set(get_snippet_models())
        self.assertTrue({ServiceBlock, ProjectCategory, Project, RentalCategory, RentalItem} <= snippet_models)

    def test_content_snippet_indexes_are_available_to_superuser(self):
        user = get_user_model().objects.create_superuser(
            username="editor",
            email="editor@example.com",
            password="test-password",
        )
        self.client.force_login(user)
        for model in (ServiceBlock, ProjectCategory, Project, RentalCategory, RentalItem):
            with self.subTest(model=model.__name__):
                response = self.client.get(reverse(model.snippet_viewset.get_url_name("list")))
                self.assertEqual(response.status_code, 200)

    def test_wagtail_content_admin_groups_use_plain_russian_labels(self):
        self.assertEqual(ServicesGroup.menu_label, "Услуги")
        self.assertEqual(PortfolioGroup.menu_label, "Проекты")
        self.assertEqual(RentalGroup.menu_label, "Аренда")
        self.assertEqual(Project.snippet_viewset.menu_label, "Проекты")
        self.assertEqual(RentalItem.snippet_viewset.menu_label, "Позиции аренды")

    def test_wagtail_main_menu_matches_site_order_before_default_items(self):
        contacts_item = register_contacts_menu_item()
        menu_items = [
            MenuItem("Страницы", "/admin/pages/", name="explorer", order=100),
            MenuItem("Изображения", "/admin/images/", name="images", order=300),
            MenuItem("Главная", "/admin/pages/1/edit/", name="home", order=90),
            MenuItem("Услуги", "/admin/services/", name="services-content", order=100),
            MenuItem("Проекты", "/admin/projects/", name="portfolio", order=200),
            MenuItem("Аренда", "/admin/rental/", name="rental-content", order=300),
            contacts_item,
        ]

        arrange_main_menu(None, menu_items)
        ordered_names = [item.name for item in sorted(menu_items, key=lambda item: item.order)]

        self.assertNotIn("explorer", ordered_names)
        self.assertEqual(
            ordered_names[:5],
            ["home", "services-content", "portfolio", "rental-content", "contacts"],
        )
        self.assertGreater(next(item.order for item in menu_items if item.name == "images"), 500)
        self.assertEqual(contacts_item.url, "/admin/settings/cms/contactsettings/")

    def test_rental_category_form_creates_nested_categories(self):
        root_form = RentalCategoryForm(
            data={"title": "Equipment", "slug": "equipment", "parent": "", "sort_order": 0, "is_active": True}
        )
        self.assertTrue(root_form.is_valid(), root_form.errors)
        root = root_form.save()

        child_form = RentalCategoryForm(
            data={"title": "Cameras", "slug": "cameras", "parent": root.pk, "sort_order": 0, "is_active": True}
        )
        self.assertTrue(child_form.is_valid(), child_form.errors)
        child = child_form.save()
        self.assertEqual(child.get_parent(), root)

        move_form = RentalCategoryForm(
            instance=child,
            data={"title": "Cameras", "slug": "cameras", "parent": "", "sort_order": 0, "is_active": True},
        )
        self.assertTrue(move_form.is_valid(), move_form.errors)
        moved_child = move_form.save()
        moved_child.refresh_from_db()
        self.assertIsNone(moved_child.get_parent())

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
        self.assertIn("video_preview", list_response.data["results"][0])

        detail_response = self.client.get(f"/api/v1/projects/{published.slug}/")
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.data["slug"], published.slug)
        self.assertIn("video_preview", detail_response.data)

    def test_rental_categories_are_returned_as_tree(self):
        root = RentalCategory.add_root(title="Equipment", slug="equipment", is_active=True)
        root.add_child(title="Cameras", slug="cameras", is_active=True)

        response = self.client.get("/api/v1/rental/categories/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["slug"], "equipment")
        self.assertEqual(response.data[0]["children"][0]["slug"], "cameras")

    def test_rental_items_support_category_browsing_and_search(self):
        lights = RentalCategory.add_root(title="СВЕТОВОЕ ОБОРУДОВАНИЕ", slug="lighting-equipment", is_active=True)
        stands = lights.add_child(title="Стойки, железо", slug="stands-grip", is_active=True)
        flags = lights.add_child(title="Флаги, рамы, плоскости", slug="flags-frames-surfaces", is_active=True)
        stand = self.create_rental_item(
            stands,
            "Avenger A2033FCB C-Stand 33 Black",
            "avenger-a2033fcb-c-stand-33-black",
            search_aliases="c stand c-stand си стенд с-стенд авенджер стойка грип железо",
        )
        flag = self.create_rental_item(
            flags,
            "Matthews Floppy Cutter 48x48",
            "matthews-floppy-cutter-48x48",
            search_aliases="matthews floppy cutter flag флоппи каттер флаг",
        )

        category_response = self.client.get("/api/v1/rental/items/", {"category": "lighting-equipment"})
        self.assertEqual({item["slug"] for item in category_response.data["results"]}, {stand.slug, flag.slug})

        for query in ("c stand", "си стенд", "СИ СТЕНД", "с-стенд", "avenger"):
            with self.subTest(query=query):
                search_response = self.client.get("/api/v1/rental/items/", {"search": query})
                self.assertEqual([item["slug"] for item in search_response.data["results"]], [stand.slug])

        detail_response = self.client.get(f"/api/v1/rental/items/{stand.slug}/")
        self.assertEqual(detail_response.status_code, 200)
        self.assertNotIn("video_url", detail_response.data)

    def test_search_variants_cover_latin_cyrillic_and_wrong_keyboard_layout(self):
        variants = search_variants("c stand")
        self.assertIn("си стенд", variants)
        self.assertIn("с ыефтв", variants)

        variants = search_variants("с-стенд")
        self.assertIn("c-stand", variants)

    def test_rental_filters_and_lead_routes_are_removed(self):
        self.assertEqual(self.client.get("/api/v1/rental/filters/").status_code, 404)
        self.assertEqual(self.client.post("/api/v1/leads/", {}).status_code, 404)
        self.assertEqual(self.client.post("/api/v1/rental/leads/", {}).status_code, 404)

    def test_contacts_endpoint_returns_contact_copy_without_lead_wording(self):
        call_command("seed_figma_content", verbosity=0)

        response = self.client.get("/api/v1/pages/contacts/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["section_title"], "КОНТАКТЫ")
        self.assertEqual(response.data["form"]["title"], "СВЯЗАТЬСЯ С НАМИ")
        self.assertEqual(response.data["form"]["fields"]["message"]["label"], "Сообщение")

    def test_project_video_file_and_external_url_are_mutually_exclusive(self):
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

    def test_openapi_and_docs_urls_are_available(self):
        self.assertEqual(self.client.get("/api/schema/").status_code, 200)
        self.assertEqual(self.client.get("/api/docs/").status_code, 200)

    def test_seed_figma_content_is_idempotent(self):
        call_command("seed_figma_content", verbosity=0)
        call_command("seed_figma_content", verbosity=0)

        home_page = HomePage.objects.get()
        self.assertEqual(home_page.hero_title, "ПРОДАКШН\nДЛЯ КИНО И\nРЕКЛАМЫ")
        self.assertEqual(home_page.hero_title_mobile, "ПРОДАКШН\nДЛЯ КИНО\nИ РЕКЛАМЫ")
        self.assertFalse(hasattr(home_page, "projects_title"))

        section_settings = MainPageSectionSettings.objects.get()
        self.assertEqual(section_settings.projects_title, "НАШИ ПРОЕКТЫ")

        contact_settings = ContactSettings.objects.get()
        self.assertEqual(contact_settings.email, "red.queen.by@gmail.com")
        self.assertEqual(contact_settings.form_message_placeholder, "Ваш текст")

        home_response = self.client.get("/api/v1/pages/home/")
        self.assertEqual(home_response.status_code, 200)
        self.assertIn("video_preview", home_response.data["hero"])

        self.assertEqual(ServiceBlock.objects.filter(title="АРЕНДА").count(), 1)
        self.assertEqual(ProjectCategory.objects.filter(slug="music-videos", title="КЛИПЫ").count(), 1)
        self.assertEqual(RentalCategory.objects.filter(slug="camera-equipment").count(), 1)
        self.assertEqual(RentalItem.objects.filter(slug="avenger-a2033fcb-c-stand-33-black").count(), 1)

    def create_rental_item(
        self,
        category,
        title,
        slug,
        *,
        search_aliases="",
        price=100,
        status=RentalStatus.AVAILABLE,
        publication_status=RentalPublishStatus.PUBLISHED,
    ):
        return RentalItem.objects.create(
            category=category,
            title=title,
            slug=slug,
            short_description="",
            search_aliases=search_aliases,
            price=price,
            status=status,
            publication_status=publication_status,
            is_active=True,
            published_at=timezone.now(),
        )
