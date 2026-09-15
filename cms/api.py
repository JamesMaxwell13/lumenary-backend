from django.conf import settings
from django.core.cache import cache
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes
from rest_framework.decorators import api_view
from rest_framework.response import Response

from cms.models import ContactSettings, FooterSettings, HomePage, MainPageSectionSettings
from services.models import ServiceBlock


def image_url(image):
    return image.file.url if image else None


def cached_response(key, builder):
    data = cache.get(key)
    if data is None:
        data = builder()
        cache.set(key, data, settings.CACHE_TIMEOUT)
    return Response(data)


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
def home_page(request):
    page = HomePage.objects.live().public().first()
    section_settings = MainPageSectionSettings.for_request(request)
    services = ServiceBlock.objects.filter(is_active=True).order_by("sort_order", "id")
    if not page:
        return Response({})
    return Response(
        {
            "hero": {
                "title": page.hero_title,
                "text": page.hero_text,
                "tags": page.hero_tags,
                "image": image_url(page.hero_image),
                "video_url": page.hero_video_url,
            },
            "navigation": {
                "about": page.nav_about_label,
                "services": page.nav_services_label,
                "projects": page.nav_projects_label,
                "rental": page.nav_rental_label,
                "contacts": page.nav_contacts_label,
            },
            "services": {
                "title": section_settings.services_title,
                "intro": section_settings.services_intro,
                "items": [
                    {"title": item.title, "text": item.text, "sort_order": item.sort_order}
                    for item in services
                ],
            },
            "projects": {
                "title": section_settings.projects_title,
            },
            "rental": {
                "title": section_settings.rental_title,
                "search_label": section_settings.rental_search_label,
            },
        }
    )


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
def services_page(request):
    def build():
        services = ServiceBlock.objects.filter(is_active=True).order_by("sort_order", "id")
        return {
            "items": [
                {"title": item.title, "text": item.text, "sort_order": item.sort_order}
                for item in services
            ],
        }

    return cached_response("api:pages:services", build)


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
def contacts_settings(request):
    def build():
        contact_settings = ContactSettings.for_request(request)
        return {
            "section_title": contact_settings.section_title,
            "email": contact_settings.email,
            "phone": contact_settings.phone,
            "address": contact_settings.address,
            "telegram": contact_settings.telegram,
            "instagram": contact_settings.instagram,
            "youtube": contact_settings.youtube,
            "form": {
                "title": contact_settings.form_title,
                "fields": {
                    "name": {
                        "label": contact_settings.form_name_label,
                        "placeholder": contact_settings.form_name_placeholder,
                    },
                    "phone": {
                        "label": contact_settings.form_phone_label,
                        "placeholder": contact_settings.form_phone_placeholder,
                    },
                    "email": {
                        "label": contact_settings.form_email_label,
                        "placeholder": contact_settings.form_email_placeholder,
                    },
                    "message": {
                        "label": contact_settings.form_message_label,
                        "placeholder": contact_settings.form_message_placeholder,
                    },
                },
            },
        }

    return cached_response("api:settings:contacts", build)


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
def footer_settings(request):
    def build():
        footer_settings = FooterSettings.for_request(request)
        return {
            "details_text": footer_settings.details_text,
            "contacts_text": footer_settings.contacts_text,
        }

    return cached_response("api:settings:footer", build)
