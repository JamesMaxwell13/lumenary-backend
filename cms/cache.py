from django.core.cache import cache


PUBLIC_API_CACHE_KEYS = (
    "api:pages:services",
    "api:settings:contacts",
    "api:settings:footer",
    "api:projects:categories",
    "api:rental:categories",
    "api:rental:filters",
)


def clear_public_api_cache():
    cache.delete_many(PUBLIC_API_CACHE_KEYS)
