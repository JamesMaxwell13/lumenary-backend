import re
from urllib.parse import parse_qs, urlencode, urlparse

from django.core.exceptions import ValidationError


YOUTUBE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
VIMEO_ID_RE = re.compile(r"^\d+$")
VIMEO_HASH_RE = re.compile(r"^[A-Za-z0-9]+$")


def external_video(url):
    """Return canonical playback metadata or raise a user-facing validation error."""
    if not url:
        return {"provider": "none", "url": "", "embed_url": None}

    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValidationError("Укажите полную HTTP(S)-ссылку на YouTube, Vimeo или MP4-файл.")

    host = parsed.hostname.lower().rstrip(".")
    path_parts = [part for part in parsed.path.split("/") if part]

    youtube_id = _youtube_id(host, path_parts, parse_qs(parsed.query))
    if youtube_id:
        return {
            "provider": "youtube",
            "url": url.strip(),
            "embed_url": f"https://www.youtube-nocookie.com/embed/{youtube_id}",
        }

    vimeo = _vimeo_video(host, path_parts, parse_qs(parsed.query))
    if vimeo:
        video_id, private_hash = vimeo
        params = {"dnt": "1"}
        if private_hash:
            params["h"] = private_hash
        return {
            "provider": "vimeo",
            "url": url.strip(),
            "embed_url": f"https://player.vimeo.com/video/{video_id}?{urlencode(params)}",
        }

    if parsed.path.lower().endswith(".mp4"):
        return {"provider": "direct_mp4", "url": url.strip(), "embed_url": None}

    raise ValidationError("Поддерживаются ссылки YouTube, Vimeo и прямые ссылки на MP4-файлы.")


def video_metadata(file_field=None, external_url=""):
    if file_field:
        return {"provider": "file", "url": file_field.url, "embed_url": None}
    return external_video(external_url)


def validate_external_video_url(url):
    if url:
        external_video(url)


def _youtube_id(host, path_parts, query):
    video_id = None
    if host == "youtu.be":
        video_id = path_parts[0] if path_parts else None
    elif host == "youtube.com" or host.endswith(".youtube.com") or host == "youtube-nocookie.com" or host.endswith(".youtube-nocookie.com"):
        if path_parts and path_parts[0] == "watch":
            video_id = query.get("v", [None])[0]
        elif len(path_parts) >= 2 and path_parts[0] in {"embed", "shorts", "live"}:
            video_id = path_parts[1]
    return video_id if video_id and YOUTUBE_ID_RE.fullmatch(video_id) else None


def _vimeo_video(host, path_parts, query):
    if not (host == "vimeo.com" or host.endswith(".vimeo.com")):
        return None

    video_index = next((index for index, part in enumerate(path_parts) if VIMEO_ID_RE.fullmatch(part)), None)
    if video_index is None:
        return None

    video_id = path_parts[video_index]
    private_hash = query.get("h", [None])[0]
    if not private_hash and len(path_parts) > video_index + 1:
        candidate = path_parts[video_index + 1]
        if VIMEO_HASH_RE.fullmatch(candidate):
            private_hash = candidate
    if private_hash and not VIMEO_HASH_RE.fullmatch(private_hash):
        return None
    return video_id, private_hash
