import mimetypes
import os

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse, StreamingHttpResponse
from django.utils._os import safe_join


CHUNK_SIZE = 8192


def ranged_media_response(request, path):
    try:
        full_path = safe_join(settings.MEDIA_ROOT, path)
    except ValueError as exc:
        raise Http404 from exc

    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        raise Http404

    file_size = os.path.getsize(full_path)
    content_type = mimetypes.guess_type(full_path)[0] or "application/octet-stream"
    range_header = request.headers.get("Range")

    if not range_header:
        response = FileResponse(open(full_path, "rb"), content_type=content_type)
        response["Accept-Ranges"] = "bytes"
        response["Content-Length"] = str(file_size)
        return response

    start, end = parse_range_header(range_header, file_size)
    if start is None:
        response = HttpResponse(status=416)
        response["Content-Range"] = f"bytes */{file_size}"
        response["Accept-Ranges"] = "bytes"
        return response

    length = end - start + 1
    response = StreamingHttpResponse(
        file_iterator(full_path, start, length),
        status=206,
        content_type=content_type,
    )
    response["Accept-Ranges"] = "bytes"
    response["Content-Length"] = str(length)
    response["Content-Range"] = f"bytes {start}-{end}/{file_size}"
    return response


def parse_range_header(range_header, file_size):
    if not range_header.startswith("bytes="):
        return None, None

    byte_range = range_header.removeprefix("bytes=").split(",", 1)[0].strip()
    if "-" not in byte_range:
        return None, None

    start_text, end_text = byte_range.split("-", 1)
    try:
        if start_text:
            start = int(start_text)
            end = int(end_text) if end_text else file_size - 1
        else:
            suffix_length = int(end_text)
            start = max(file_size - suffix_length, 0)
            end = file_size - 1
    except ValueError:
        return None, None

    if start < 0 or end < start or start >= file_size:
        return None, None
    return start, min(end, file_size - 1)


def file_iterator(full_path, start, length):
    remaining = length
    with open(full_path, "rb") as file:
        file.seek(start)
        while remaining > 0:
            chunk = file.read(min(CHUNK_SIZE, remaining))
            if not chunk:
                break
            remaining -= len(chunk)
            yield chunk
