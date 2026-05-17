from __future__ import annotations

import re
from datetime import UTC, datetime
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

try:
    import tldextract
except ImportError:  # pragma: no cover - exercised only without optional dependency
    tldextract = None


TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "fbclid",
    "gclid",
}

INVALID_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|]')
WHITESPACE = re.compile(r"\s+")


def normalize_title(title: str) -> str:
    cleaned = INVALID_FILENAME_CHARS.sub("", title or "")
    cleaned = WHITESPACE.sub(" ", cleaned).strip()
    return cleaned or "Untitled"


def normalize_url(url: str) -> str:
    parts = urlsplit((url or "").strip())
    scheme = "https" if parts.scheme in {"http", "https"} else parts.scheme
    netloc = parts.netloc.lower()

    if netloc.endswith(":80") and scheme == "http":
        netloc = netloc[:-3]
    if netloc.endswith(":443") and scheme == "https":
        netloc = netloc[:-4]

    path = parts.path
    if path != "/":
        path = path.rstrip("/")
    else:
        path = ""

    query_pairs = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key.lower() not in TRACKING_PARAMS
    ]
    query = urlencode(query_pairs, doseq=True)
    return urlunsplit((scheme, netloc, path, query, parts.fragment))


def extract_domain(url: str) -> str:
    host = urlsplit(url).hostname or ""
    host = host.lower()
    if host.startswith("www."):
        host = host[4:]

    if tldextract is None:
        return host

    extracted = tldextract.extract(host)
    registered = extracted.top_domain_under_public_suffix
    return registered or host


def epoch_to_date(value: str | None, fallback: datetime | None = None) -> str:
    if value:
        try:
            return datetime.fromtimestamp(int(value), tz=UTC).date().isoformat()
        except (TypeError, ValueError, OSError, OverflowError):
            pass

    fallback = fallback or datetime.now(tz=UTC)
    return fallback.date().isoformat()


def slugify_filename(title: str, max_length: int = 90) -> str:
    slug = normalize_title(title)
    slug = slug.replace("#", "").strip(". ")
    slug = WHITESPACE.sub(" ", slug)
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip()
    return slug or "Untitled"
