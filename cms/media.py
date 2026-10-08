from django.core.exceptions import SuspiciousFileOperation
from django.core.files.storage import default_storage


def file_status(file_field):
    if not file_field:
        return {
            "source": "none",
            "storage": storage_name(),
            "exists": False,
            "size": 0,
            "upload_percent": 0,
            "is_complete": False,
        }

    try:
        exists = default_storage.exists(file_field.name)
        size = file_field.size if exists else 0
    except (OSError, SuspiciousFileOperation):
        exists = False
        size = 0

    is_complete = exists and size > 0
    return {
        "source": "file",
        "storage": storage_name(),
        "exists": exists,
        "size": size,
        "upload_percent": 100 if is_complete else 0,
        "is_complete": is_complete,
    }


def external_video_status(url):
    return {
        "source": "external" if url else "none",
        "storage": "external" if url else storage_name(),
        "exists": bool(url),
        "size": None,
        "upload_percent": 100 if url else 0,
        "is_complete": bool(url),
    }


def video_status(file_field, external_url=""):
    if file_field:
        return file_status(file_field)
    return external_video_status(external_url)


def storage_name():
    module = default_storage.__class__.__module__
    class_name = default_storage.__class__.__name__
    if "s3" in module.lower():
        return "s3"
    if "filesystem" in module.lower():
        return "local"
    return class_name
