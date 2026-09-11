from django.conf import settings
from django.core.cache import cache
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes
from rest_framework.decorators import api_view
from rest_framework.response import Response

from cms.models import ContactSettings, FooterSettings, HomePage
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
            "services": {
                "intro": page.services_intro,
                "items": [
                    {"title": item.title, "text": item.text, "sort_order": item.sort_order}
                    for item in services
                ],
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
            "email": contact_settings.email,
            "phone": contact_settings.phone,
            "address": contact_settings.address,
            "telegram": contact_settings.telegram,
            "instagram": contact_settings.instagram,
            "youtube": contact_settings.youtube,
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
