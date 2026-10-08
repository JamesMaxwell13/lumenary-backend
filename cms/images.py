def image_rendition_url(image, spec):
    if not image:
        return None

    try:
        return image.get_rendition(spec).url
    except Exception:
        return image.file.url


def image_original_url(image):
    return image.file.url if image else None
