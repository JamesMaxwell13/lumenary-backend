from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from wagtail.models import Locale, Page, Site

from cms.models import ContactSettings, HomePage, MainPageSectionSettings
from projects.models import ProjectCategory
from rental.models import PublishStatus, RentalCategory, RentalItem, RentalStatus
from services.models import ServiceBlock


HOME_PAGE_COPY = {
    "title": "Lumenary",
    "slug": "Lumenary",
    "hero_title": "ПРОДАКШН\nДЛЯ КИНО И\nРЕКЛАМЫ",
    "hero_title_mobile": "ПРОДАКШН\nДЛЯ КИНО\nИ РЕКЛАМЫ",
    "hero_text": (
        "Снимаем рекламу, клипы, сериалы, документальные и художественные фильмы. \n"
        "Ведём полный цикл проектов, включающий подготовку, съемки и постпродакшн."
    ),
    "hero_tags": "кино / клипы / реклама / промо / reels /\nсъёмка / аренда /постпродакшн",
    "nav_about_label": "О НАС",
    "nav_services_label": "УСЛУГИ",
    "nav_projects_label": "ПРОЕКТЫ",
    "nav_rental_label": "АРЕНДА",
    "nav_contacts_label": "КОНТАКТЫ",
}

SECTION_COPY = {
    "services_title": "УСЛУГИ",
    "services_intro": (
        "Собираем индивидуальную команду под каждый проект. \n"
        "Помогаем воплотить любую вашу идею в жизнь"
    ),
    "projects_title": "НАШИ ПРОЕКТЫ",
    "rental_title": "АРЕНДА",
    "rental_search_label": "ПОИСК",
}

CONTACT_COPY = {
    "section_title": "КОНТАКТЫ",
    "email": "red.queen.by@gmail.com",
    "phone": "+37529123456",
    "address": "ул. Розы Люксембург 95\nг.Минск",
    "telegram": "@Lumenary_By",
    "instagram": "@Lumenary_By",
    "youtube": "@Lumenary_By",
    "form_title": "СВЯЗАТЬСЯ С НАМИ",
    "form_name_label": "Имя",
    "form_name_placeholder": "Как к вам обращаться?",
    "form_phone_label": "Телефон",
    "form_phone_placeholder": "+375-XX-XXXXXX",
    "form_email_label": "Email",
    "form_email_placeholder": "email@mail.com",
    "form_message_label": "Сообщение",
    "form_message_placeholder": "Ваш текст",
}

SERVICES = [
    (
        "ПРЕ-ПРОДАКШН",
        "Считаем смету, собираем команду, утверждаем график, локации, логистику, технику и расходные материалы. Создаем календарно-постановочный план.",
    ),
    (
        "СЪЁМКА",
        "Организуем съёмочный процесс в соотвестсвии с календарно-постановочным планом, решаем текущие проблемы и вопросы на площадке.",
    ),
    (
        "ПОСТ-\nПРОДАКШН",
        "Делаем монтаж, цветокоррекцию, обработку звука, графику и финальные версии под необходимые платформы. Готовим фильмы к прокату в кинотеатрах.",
    ),
    (
        "АРЕНДА",
        "Подбираем технику, свет, костюмы и реквизит под задачи съёмки. Помогаем собрать комплект, согласовать сроки, стоимость и условия использования на площадке.",
    ),
]

PROJECT_CATEGORIES = [
    ("КИНО", "film"),
    ("КЛИПЫ", "music-videos"),
    ("РЕКЛАМА", "commercials"),
    ("ПРОМО", "promo"),
    ("REELS", "reels"),
]

RENTAL_CATEGORIES = [
    ("КАМЕРНОЕ ОБОРУДОВАНИЕ", "camera-equipment", None),
    ("СВЕТОВОЕ ОБОРУДОВАНИЕ", "lighting-equipment", None),
    ("КОСТЮМЫ", "costumes", None),
    ("РЕКВИЗИТ", "props", None),
    ("Камеры", "cameras", "camera-equipment"),
    ("Стойки, железо", "stands-grip", "lighting-equipment"),
    ("Флаги, рамы, плоскости", "flags-frames-surfaces", "lighting-equipment"),
    ("Костюмы", "costumes-filter", "costumes"),
]

RENTAL_ITEMS = [
    {
        "category_slug": "stands-grip",
        "title": "Avenger A2033FCB C-Stand 33 Black",
        "slug": "avenger-a2033fcb-c-stand-33-black",
        "short_description": "Черная стальная C-стойка 3,3 м с grip head и boom arm.",
        "search_aliases": "c stand c-stand си стенд с-стенд авенджер стойка грип железо avenger a2033fcb",
        "description": "Классическая стойка для света, флагов и grip-задач на съемочной площадке.",
        "price": 25,
        "price_unit": "сутки",
    },
    {
        "category_slug": "stands-grip",
        "title": "Manfrotto 1004BAC Master Stand",
        "slug": "manfrotto-1004bac-master-stand",
        "short_description": "Алюминиевая стойка до 3,66 м для приборов и легких насадок.",
        "search_aliases": "manfrotto 1004bac мастер стенд стойка манфротто световая стойка",
        "description": "Надежная складная стойка для мобильных световых комплектов и небольших площадок.",
        "price": 18,
        "price_unit": "сутки",
    },
    {
        "category_slug": "flags-frames-surfaces",
        "title": "Avenger I650 Butterfly Frame 6x6",
        "slug": "avenger-i650-butterfly-frame-6x6",
        "short_description": "Рама butterfly 6x6 футов для рассеивания, отражения и затемнения.",
        "search_aliases": "butterfly frame 6x6 баттерфляй рама флаг авенджер avenger i650",
        "description": "Универсальная рама для работы со светом на улице и в павильоне.",
        "price": 35,
        "price_unit": "сутки",
    },
    {
        "category_slug": "flags-frames-surfaces",
        "title": "Matthews Floppy Cutter 48x48",
        "slug": "matthews-floppy-cutter-48x48",
        "short_description": "Флоппи-флаг 48x48 дюймов для контроля паразитного света.",
        "search_aliases": "matthews floppy cutter flag флоппи каттер флаг мэтьюс затемнение",
        "description": "Плотный черный флаг для отсечения света и быстрой постановки контраста.",
        "price": 20,
        "price_unit": "сутки",
    },
]


class Command(BaseCommand):
    help = "Seed Wagtail/admin content with visible copy from the Figma web-main design."

    @transaction.atomic
    def handle(self, *args, **options):
        home_page = self.seed_home_page()
        self.ensure_default_site(home_page)
        self.seed_section_settings()
        self.seed_contacts()
        self.seed_services()
        self.seed_project_categories()
        self.seed_rental_categories()
        self.seed_rental_items()
        self.stdout.write(self.style.SUCCESS(f"Seeded Figma content for HomePage #{home_page.pk}."))

    def seed_home_page(self):
        home_page = HomePage.objects.first()
        if home_page is None:
            Locale.objects.get_or_create(language_code=settings.LANGUAGE_CODE)
            Locale.objects.get_or_create(language_code=settings.LANGUAGE_CODE.split("-")[0])
            root = Page.get_first_root_node() or Page.add_root(title="Root", slug="root")
            home_page = HomePage(**HOME_PAGE_COPY)
            root.add_child(instance=home_page)
            home_page.save_revision().publish()
        else:
            for field, value in HOME_PAGE_COPY.items():
                setattr(home_page, field, value)
            home_page.save_revision().publish()
        return home_page

    def ensure_default_site(self, home_page):
        default_site = Site.objects.filter(is_default_site=True).first()
        if default_site:
            if default_site.root_page_id != home_page.pk:
                default_site.root_page = home_page
                default_site.save(update_fields=["root_page"])
            return
        Site.objects.create(hostname="localhost", port=8000, root_page=home_page, is_default_site=True)

    def seed_section_settings(self):
        for site in Site.objects.all():
            section_settings, _ = MainPageSectionSettings.objects.get_or_create(site=site)
            for field, value in SECTION_COPY.items():
                setattr(section_settings, field, value)
            section_settings.save()

    def seed_contacts(self):
        for site in Site.objects.all():
            contact_settings, _ = ContactSettings.objects.get_or_create(site=site)
            for field, value in CONTACT_COPY.items():
                setattr(contact_settings, field, value)
            contact_settings.save()

    def seed_services(self):
        for sort_order, (title, text) in enumerate(SERVICES, start=1):
            ServiceBlock.objects.update_or_create(
                title=title,
                defaults={"text": text, "sort_order": sort_order, "is_active": True},
            )

    def seed_project_categories(self):
        for sort_order, (title, slug) in enumerate(PROJECT_CATEGORIES, start=1):
            ProjectCategory.objects.update_or_create(
                slug=slug,
                defaults={"title": title, "sort_order": sort_order, "is_active": True},
            )

    def seed_rental_categories(self):
        categories_by_slug = {category.slug: category for category in RentalCategory.objects.all()}
        for sort_order, (title, slug, parent_slug) in enumerate(RENTAL_CATEGORIES, start=1):
            category = categories_by_slug.get(slug)
            parent = categories_by_slug.get(parent_slug) if parent_slug else None
            if category is None:
                if parent:
                    category = parent.add_child(title=title, slug=slug, sort_order=sort_order, is_active=True)
                else:
                    category = RentalCategory.add_root(title=title, slug=slug, sort_order=sort_order, is_active=True)
                categories_by_slug[slug] = category
                continue
            category.title = title
            category.sort_order = sort_order
            category.is_active = True
            category.save(update_fields=["title", "sort_order", "is_active"])

    def seed_rental_items(self):
        categories_by_slug = {category.slug: category for category in RentalCategory.objects.all()}
        for sort_order, item in enumerate(RENTAL_ITEMS, start=1):
            category = categories_by_slug[item["category_slug"]]
            RentalItem.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    "category": category,
                    "title": item["title"],
                    "short_description": item["short_description"],
                    "search_aliases": item["search_aliases"],
                    "description": item["description"],
                    "price": item["price"],
                    "price_unit": item["price_unit"],
                    "status": RentalStatus.AVAILABLE,
                    "publication_status": PublishStatus.PUBLISHED,
                    "sort_order": sort_order,
                    "is_active": True,
                    "published_at": timezone.now(),
                },
            )
