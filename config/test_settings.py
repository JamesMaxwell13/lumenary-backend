from config.settings import *  # noqa: F403


class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "lumenary-tests",
    }
}

MIGRATION_MODULES = DisableMigrations()
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
