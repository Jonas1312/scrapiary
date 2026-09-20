from __future__ import annotations

from urllib.parse import parse_qsl, urldefrag, urlencode, urljoin, urlsplit, urlunsplit

TRACKING_PARAMETERS = {"fbclid", "gclid", "mc_cid", "mc_eid"}


def canonicalize_url(base_url: str, href: str) -> str:
    absolute, _fragment = urldefrag(urljoin(base_url, href))
    split = urlsplit(absolute)
    query = urlencode(
        [
            (key, value)
            for key, value in parse_qsl(split.query, keep_blank_values=True)
            if not _is_tracking_parameter(key)
        ],
        doseq=True,
    )
    return urlunsplit((split.scheme.lower(), split.netloc.lower(), split.path, query, ""))


def _is_tracking_parameter(name: str) -> bool:
    lowered = name.lower()
    return lowered.startswith("utm_") or lowered in TRACKING_PARAMETERS
