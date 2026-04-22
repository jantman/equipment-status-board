"""Text helpers."""

import re
import unicodedata
from urllib.parse import urlsplit


def slugify_filename(name: str) -> str:
    """Produce a filesystem-safe slug from a human name for use in download filenames.

    Transliterates Unicode to ASCII via NFKD decomposition (so "Café" → "Cafe"
    rather than "Caf"), then collapses any run of non [A-Za-z0-9-] characters to
    a single hyphen, strips leading/trailing hyphens, truncates to 50 chars, and
    falls back to 'equipment' if the result is empty.
    """
    ascii_name = unicodedata.normalize('NFKD', name or '').encode('ascii', 'ignore').decode('ascii')
    # Collapse non-alnum-hyphen runs to single '-', truncate, then strip again so
    # truncation that lands on a hyphen doesn't leave a trailing '-'.
    slug = re.sub(r'[^A-Za-z0-9-]+', '-', ascii_name).strip('-')[:50].strip('-')
    return slug or 'equipment'


def get_normalized_base_url(raw: str) -> str:
    """Validate and normalize ESB_BASE_URL for use as a QR code target prefix.

    Strips whitespace and trailing slashes; rejects empty values, embedded
    whitespace, non-ASCII characters, non-http(s) schemes, missing host,
    embedded credentials, and any path/query/fragment. Returns the bare
    scheme://host[:port] form with the scheme lowercased.

    Raises:
        ValueError: with a specific human-readable message for each failure mode.
    """
    # rstrip('/') BEFORE urlsplit so 'http://host///' normalizes cleanly rather
    # than landing in urlsplit as path='///' and failing the no-path check below.
    stripped = (raw or '').strip().rstrip('/')
    if not stripped:
        raise ValueError('ESB_BASE_URL is not configured')
    # Reject non-ASCII and any embedded whitespace (covers zero-width spaces,
    # tabs, internal spaces). URLs are ASCII-only per RFC 3986.
    if not stripped.isascii() or any(c.isspace() for c in stripped):
        raise ValueError('ESB_BASE_URL must be ASCII with no embedded whitespace')
    try:
        parts = urlsplit(stripped)
    except ValueError as exc:
        raise ValueError(f'ESB_BASE_URL is malformed: {exc}') from exc
    if parts.scheme not in ('http', 'https'):
        raise ValueError('ESB_BASE_URL must be an http(s) URL')
    if not parts.hostname:
        raise ValueError('ESB_BASE_URL must include a host')
    if parts.username or parts.password:
        raise ValueError('ESB_BASE_URL must not contain embedded credentials')
    if parts.path or parts.query or parts.fragment:
        raise ValueError('ESB_BASE_URL must not include a path, query, or fragment')
    # Accessing .port validates the port range (0-65535); raises ValueError otherwise.
    try:
        parts.port
    except ValueError as exc:
        raise ValueError(f'ESB_BASE_URL has an invalid port: {exc}') from exc
    return f'{parts.scheme}://{parts.netloc}'
