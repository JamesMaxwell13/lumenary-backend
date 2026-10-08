from django.conf import settings
from django.core.cache import cache
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from cms.media import video_status
from cms.models import ContactSettings, HomePage, MainPageSectionSettings
from cms.videos import video_metadata
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
    if not page:
        return Response(
            {"detail": "Главная страница ещё не опубликована."},
            status=status.HTTP_404_NOT_FOUND,
        )
    section_settings = MainPageSectionSettings.for_request(request)
    services = ServiceBlock.objects.filter(is_active=True).order_by("sort_order", "id")
    hero_video = video_metadata(page.hero_video_file, page.hero_video_url)
    return Response(
        {
            "hero": {
                "title": page.hero_title,
                "title_mobile": page.hero_title_mobile,
                "text": page.hero_text,
                "tags": page.hero_tags,
                "image": image_url(page.hero_image),
                "video_url": hero_video["url"],
                "video_provider": hero_video["provider"],
                "video_embed_url": hero_video["embed_url"],
                "video_status": video_status(page.hero_video_file, page.hero_video_url),
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
                "page_intro": section_settings.projects_page_intro,
                "cta_title": section_settings.projects_cta_title,
                "cta_text": section_settings.projects_cta_text,
            },
            "rental": {
                "title": section_settings.rental_title,
                "search_label": section_settings.rental_search_label,
                "page_intro": section_settings.rental_page_intro,
                "cta_title": section_settings.rental_cta_title,
                "cta_text": section_settings.rental_cta_text,
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
            "section_intro": contact_settings.section_intro,
            "email": contact_settings.email,
            "phone": contact_settings.phone,
            "address": contact_settings.address,
            "telegram": contact_settings.telegram,
            "instagram": contact_settings.instagram,
            "youtube": contact_settings.youtube,
            "footer_legal_text": contact_settings.footer_legal_text,
        }

    return cached_response("api:settings:contacts", build)
