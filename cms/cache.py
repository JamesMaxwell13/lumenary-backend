from django.core.cache import cache


PUBLIC_API_CACHE_KEYS = (
    "api:settings:contacts",
    "api:projects:categories",
    "api:rental:categories",
)


def clear_public_api_cache():
    cache.delete_many(PUBLIC_API_CACHE_KEYS)
