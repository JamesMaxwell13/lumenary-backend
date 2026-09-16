from django.conf import settings
from django.core.cache import cache
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes
from rest_framework.decorators import api_view
from rest_framework.response import Response

from cms.models import ContactSettings, HomePage, MainPageSectionSettings
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
                "title_mobile": page.hero_title_mobile,
                "text": page.hero_text,
                "tags": page.hero_tags,
                "image": image_url(page.hero_image),
                "video_preview": image_url(page.hero_video_preview),
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
        }

    return cached_response("api:settings:contacts", build)
