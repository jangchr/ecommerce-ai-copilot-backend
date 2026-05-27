from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import unquote, urlparse


SUPPORTED_AMAZON_HOSTS = {"amazon.com", "www.amazon.com"}
ASIN_PATTERN = re.compile(r"^[A-Za-z0-9]{10}$")


@dataclass(frozen=True)
class AmazonURLIntake:
    input_url: str
    is_supported: bool
    asin: str = ""
    normalized_url: str = ""
    reason: str = ""
    source_type: str = "amazon_product_url"


def normalize_amazon_product_url(url: str) -> AmazonURLIntake:
    raw = (url or "").strip()
    if not raw:
        return AmazonURLIntake(
            input_url=raw,
            is_supported=False,
            reason="missing_url",
            source_type="unsupported_url",
        )

    candidate = raw if "://" in raw else f"https://{raw}"
    parsed = urlparse(candidate)
    host = (parsed.hostname or "").lower()

    if host not in SUPPORTED_AMAZON_HOSTS:
        return AmazonURLIntake(
            input_url=raw,
            is_supported=False,
            reason="non_amazon_com_url",
            source_type="unsupported_url",
        )

    asin = extract_amazon_asin_from_path(parsed.path)
    if not asin:
        return AmazonURLIntake(
            input_url=raw,
            is_supported=False,
            reason="not_amazon_product_detail_url",
            source_type="unsupported_url",
        )

    return AmazonURLIntake(
        input_url=raw,
        is_supported=True,
        asin=asin,
        normalized_url=f"https://www.amazon.com/dp/{asin}",
        reason="",
        source_type="amazon_product_url",
    )


def extract_amazon_asin_from_path(path: str) -> str:
    segments = [unquote(part).strip() for part in (path or "").split("/") if part.strip()]

    for index, segment in enumerate(segments[:-1]):
        current = segment.lower()
        candidate = segments[index + 1].split("?")[0].strip()

        if current == "dp" and _is_asin(candidate):
            return candidate.upper()

        if current == "product" and index > 0 and segments[index - 1].lower() == "gp" and _is_asin(candidate):
            return candidate.upper()

    return ""


def _is_asin(value: str) -> bool:
    return bool(ASIN_PATTERN.match(value or ""))
