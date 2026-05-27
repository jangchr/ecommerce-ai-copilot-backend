import html
import re
import socket
import urllib.request
from html.parser import HTMLParser
from typing import Optional
from urllib.error import HTTPError, URLError

from schemas.source_contract import SourceEvidence
from source_adapters.amazon_url_utils import normalize_amazon_product_url
from source_adapters.base import BaseSourceAdapter


class InvalidAmazonDetailURL(ValueError):
    pass


class _AmazonHTMLTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._stack: list[dict] = []
        self._capture: Optional[dict] = None
        self._capture_text: list[str] = []
        self.fields = {
            "product_title": [],
            "rating": [],
            "review_count": [],
            "price": [],
            "bullet_points": [],
            "review_snippets": [],
            "category_hint": [],
        }

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        attr_map = {key: value or "" for key, value in attrs}
        node = {
            "tag": tag,
            "id": attr_map.get("id", ""),
            "class": attr_map.get("class", ""),
            "data_hook": attr_map.get("data-hook", ""),
        }
        self._stack.append(node)
        target = self._target_for_node(node)
        if target and self._capture is None:
            self._capture = {"tag": tag, "field": target, "depth": 1}
            self._capture_text = []
        elif self._capture:
            self._capture["depth"] += 1

    def handle_endtag(self, tag: str) -> None:
        if self._capture:
            self._capture["depth"] -= 1
            if self._capture["depth"] <= 0:
                text = _clean_text(" ".join(self._capture_text))
                if text:
                    self.fields[self._capture["field"]].append(text)
                self._capture = None
                self._capture_text = []
        if self._stack:
            self._stack.pop()

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._capture_text.append(data)

    def _target_for_node(self, node: dict) -> Optional[str]:
        node_id = node["id"]
        class_name = node["class"]
        data_hook = node["data_hook"]

        if node_id == "productTitle":
            return "product_title"
        if node_id == "acrCustomerReviewText":
            return "review_count"
        if node_id == "wayfinding-breadcrumbs_feature_div":
            return "category_hint"
        if data_hook in {"rating-out-of-text", "average-star-rating"}:
            return "rating"
        if data_hook in {"total-review-count", "cr-filter-info-review-rating-count"}:
            return "review_count"
        if data_hook in {"review-body", "review-collapsed"}:
            return "review_snippets"
        if "a-icon-alt" in class_name:
            return "rating"
        if "a-price" in class_name and "a-offscreen" in class_name:
            return "price"
        if "review-text" in class_name:
            return "review_snippets"
        if self._inside_feature_bullets(node):
            return "bullet_points"
        return None

    def _inside_feature_bullets(self, node: dict) -> bool:
        if node["tag"] != "li":
            return False
        return any(parent["id"] == "feature-bullets" for parent in self._stack)


class AmazonReviewAdapter(BaseSourceAdapter):
    source_type = "amazon_review_api"
    max_retries = 1

    def fetch(self, url: str, product_category: str) -> SourceEvidence:
        if not url:
            return self._unavailable(
                url,
                product_category,
                "missing_amazon_url",
                error_type="missing_url",
            )
        if "amazon." not in url.lower():
            return self._unavailable(
                url,
                product_category,
                "non_amazon_url",
                error_type="invalid_or_redirected_url",
            )
        if not self._is_amazon_detail_url(url):
            return self._unavailable(
                url,
                product_category,
                "invalid_amazon_detail_url",
                error_type="invalid_or_redirected_url",
            )

        try:
            html_text, retry_count = self._fetch_html_with_retry(url)
            if self._is_blocked_html(html_text):
                return self._unavailable(
                    url,
                    product_category,
                    "blocked",
                    error="Amazon returned a blocked, robot check or captcha page.",
                    error_type="blocked",
                    retry_count=retry_count,
                )
            evidence = self.parse_html(html_text, url, product_category)
            evidence.metadata["retry_count"] = retry_count
        except Exception as exc:
            error_type = self._classify_error(exc)
            return self._unavailable(
                url,
                product_category,
                error_type,
                error=str(exc),
                error_type=error_type,
                retry_count=getattr(exc, "retry_count", 0),
            )

        if evidence.evidence_quotes or evidence.metadata.get("product_title"):
            return evidence
        return self._unavailable(
            url,
            product_category,
            "parse_empty",
            error_type="parse_empty",
            retry_count=evidence.metadata.get("retry_count", 0),
        )

    def _fetch_html_with_retry(self, url: str) -> tuple[str, int]:
        retry_count = 0
        while True:
            try:
                return self._fetch_html(url), retry_count
            except Exception as exc:
                if retry_count < self.max_retries and self._is_transient_error(exc):
                    retry_count += 1
                    continue
                setattr(exc, "retry_count", retry_count)
                raise

    def _fetch_html(self, url: str) -> str:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0 Safari/537.36"
                ),
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
        with urllib.request.urlopen(request, timeout=8) as response:
            final_url = response.geturl()
            if final_url and not self._is_amazon_detail_url(final_url):
                raise InvalidAmazonDetailURL(f"Invalid or redirected Amazon URL: {final_url}")
            content_type = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(content_type, errors="replace")

    def _is_amazon_detail_url(self, url: str) -> bool:
        lowered = (url or "").lower()
        return bool(re.search(r"/(?:dp|gp/product)/[a-z0-9]{10}", lowered))

    def _is_transient_error(self, exc: Exception) -> bool:
        error_type = self._classify_error(exc)
        return error_type in {"connection_refused", "transient_connection_reset", "timeout"}

    def _classify_error(self, exc: Exception) -> str:
        text_parts = [
            str(exc),
            repr(exc),
            type(exc).__name__,
        ]

        reason = getattr(exc, "reason", None)
        if reason is not None:
            text_parts.extend([
                str(reason),
                repr(reason),
                type(reason).__name__,
            ])

            for attr in ("errno", "winerror", "strerror"):
                value = getattr(reason, attr, None)
                if value is not None:
                    text_parts.append(str(value))

        for attr in ("errno", "winerror", "strerror"):
            value = getattr(exc, attr, None)
            if value is not None:
                text_parts.append(str(value))

        text = " | ".join(text_parts).lower()

        if isinstance(exc, HTTPError):
            if exc.code == 404:
                return "not_found"
            if exc.code in {403, 429, 503}:
                return "blocked"
            return "http_error"
        if isinstance(exc, InvalidAmazonDetailURL):
            return "invalid_or_redirected_url"

        if (
            "winerror 10061" in text
            or "10061" in text
            or "connection refused" in text
            or "actively refused" in text
            or "actively rejected" in text
        ):
            return "connection_refused"

        if (
            "winerror 10054" in text
            or "10054" in text
            or "connection reset" in text
            or "connectionreseterror" in text
            or "connection closed" in text
            or "forcibly closed" in text
        ):
            return "transient_connection_reset"

        if "timed out" in text or "timeout" in text:
            return "timeout"

        if isinstance(exc, URLError):
            return "url_error"

        return "unknown_error"

    def _is_blocked_html(self, html_text: str) -> bool:
        lowered = (html_text or "").lower()
        blocked_markers = [
            "captcha",
            "robot check",
            "enter the characters you see below",
            "sorry, we just need to make sure you're not a robot",
            "automated access",
        ]
        return any(marker in lowered for marker in blocked_markers)

    def parse_html(self, html_text: str, url: str, product_category: str) -> SourceEvidence:
        parser = _AmazonHTMLTextParser()
        parser.feed(html_text)

        title = _first(parser.fields["product_title"]) or _meta_content(html_text, "og:title")
        rating = _first_match(parser.fields["rating"], r"\d+(?:\.\d+)?")
        review_count = _first_match(parser.fields["review_count"], r"[\d,]+")
        price = _first(parser.fields["price"]) or _meta_content(html_text, "product:price:amount")
        bullets = _unique(parser.fields["bullet_points"], limit=6)
        snippets = _unique(parser.fields["review_snippets"], limit=6)
        category_hint = _clean_category_text(
            _first(parser.fields["category_hint"])
            or _meta_content(html_text, "product:category")
            or product_category
        )

        evidence_quotes = [_short_quote(snippet) for snippet in snippets if _short_quote(snippet)]
        if not evidence_quotes:
            evidence_quotes = [
                _short_quote(text)
                for text in [
                    title,
                    f"Rating visible on page: {rating}" if rating else "",
                    f"Review count visible on page: {review_count}" if review_count else "",
                ]
                if _short_quote(text)
            ][:3]

        confidence = self._confidence(title, rating, review_count, evidence_quotes)
        source_type = "amazon_review_api" if confidence > 0 else "unavailable"
        warnings = [] if source_type == "amazon_review_api" else ["amazon_parse_empty"]

        return SourceEvidence(
            source_type=source_type,
            source_url=url,
            product_category=product_category,
            confidence=confidence,
            review_confidence=confidence,
            review_count=_safe_int(review_count),
            evidence_quotes=evidence_quotes[:6],
            data_warnings=warnings,
            metadata={
                "adapter": self.__class__.__name__,
                **_intake_metadata(url),
                "product_title": title,
                "rating": rating,
                "review_count": review_count,
                "price": price,
                "category_hint": category_hint,
                "bullet_points": bullets,
                "retry_count": 0,
            },
        )

    def _confidence(
        self,
        title: str,
        rating: str,
        review_count: str,
        evidence_quotes: list[str],
    ) -> float:
        score = 0.0
        if title:
            score += 0.20
        if rating:
            score += 0.15
        if review_count:
            score += 0.15
        if evidence_quotes:
            score += 0.35
        if len(evidence_quotes) >= 2:
            score += 0.10
        return min(score, 0.85)

    def _unavailable(
        self,
        url: str,
        product_category: str,
        warning: str,
        error: str = "",
        error_type: str = "",
        retry_count: int = 0,
    ) -> SourceEvidence:
        metadata = {
            "adapter": self.__class__.__name__,
            **_intake_metadata(url),
            "error_type": error_type or warning,
            "retry_count": retry_count,
        }
        if error:
            metadata["error"] = error
        warnings = [warning]
        if metadata["error_type"] not in warnings:
            warnings.append(metadata["error_type"])
        return SourceEvidence(
            source_type="unavailable",
            source_url=url,
            product_category=product_category,
            confidence=0.0,
            review_confidence=0.0,
            review_count=0,
            evidence_quotes=[],
            data_warnings=warnings,
            metadata=metadata,
        )


def _intake_metadata(url: str) -> dict:
    intake = normalize_amazon_product_url(url)
    if intake.is_supported:
        return {
            "asin": intake.asin,
            "normalized_url": intake.normalized_url,
            "intake_status": "supported",
            "intake_source_type": intake.source_type,
        }

    return {
        "asin": "",
        "normalized_url": "",
        "intake_status": "unsupported",
        "intake_reason": intake.reason,
        "intake_source_type": intake.source_type,
    }


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value or "")).strip()


def _clean_category_text(value: str) -> str:
    text = _clean_text(value)
    separators = [
        chr(0x203A),
        chr(0x00E2) + chr(0x00BA),
        chr(0x00E2) + chr(0x20AC) + chr(0x00BA),
    ]
    for separator in separators:
        text = text.replace(separator, " > ")
    text = re.sub(r"\s*>\s*", " > ", text)
    return text.strip(" >")


def _first(values: list[str]) -> str:
    for value in values:
        cleaned = _clean_text(value)
        if cleaned:
            return cleaned
    return ""


def _first_match(values: list[str], pattern: str) -> str:
    for value in values:
        match = re.search(pattern, value or "")
        if match:
            return match.group(0)
    return ""


def _meta_content(html_text: str, name: str) -> str:
    patterns = [
        rf'<meta[^>]+property=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']+)["\']',
        rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']{re.escape(name)}["\']',
        rf'<meta[^>]+name=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']+)["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, html_text, flags=re.IGNORECASE)
        if match:
            return _clean_text(match.group(1))
    return ""


def _unique(values: list[str], limit: int) -> list[str]:
    seen = set()
    result = []
    for value in values:
        cleaned = _clean_text(value)
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        result.append(cleaned)
        if len(result) >= limit:
            break
    return result


def _short_quote(value: str) -> str:
    cleaned = _clean_text(value)
    if len(cleaned) <= 240:
        return cleaned
    return cleaned[:237].rstrip() + "..."


def _safe_int(value: str) -> int:
    digits = re.sub(r"\D", "", value or "")
    return int(digits) if digits else 0
