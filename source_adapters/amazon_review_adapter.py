import html
import re
import socket
import urllib.request
from html.parser import HTMLParser
from typing import Optional
from urllib.error import HTTPError, URLError

from schemas.source_contract import ReviewRecord, SourceEvidence
from source_adapters.amazon_crawler import BaseAmazonCrawler, build_amazon_crawler
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

    def __init__(self, crawler: Optional[BaseAmazonCrawler] = None):
        self.crawler = crawler or build_amazon_crawler()

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
        html_parts = []
        for index, candidate_url in enumerate([url, *_amazon_reviews_urls(url)]):
            try:
                result = self.crawler.fetch_html(candidate_url)
            except Exception:
                if index == 0:
                    raise
                continue
            if result.html:
                html_parts.append(result.html)

        return "\n".join(part for part in html_parts if part)

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

        title_candidates = (
            parser.fields["product_title"]
            + [_meta_content(html_text, "og:title"), _meta_content(html_text, "title")]
            + _json_scalar_values(html_text, "name")
            + _regex_values(
                html_text,
                [
                    r'<[^>]+id=["\']productTitle["\'][^>]*>(.*?)</[^>]+>',
                    r'<title[^>]*>(.*?)</title>',
                ],
            )
        )
        rating_candidates = (
            parser.fields["rating"]
            + _json_scalar_values(html_text, "ratingValue")
            + _regex_values(
                html_text,
                [
                    r'title=["\'](\d+(?:\.\d+)?)\s+out\s+of\s+5\s+stars["\']',
                    r'(\d+(?:\.\d+)?)\s+out\s+of\s+5\s+stars',
                ],
            )
        )
        review_count_candidates = (
            parser.fields["review_count"]
            + _json_scalar_values(html_text, "reviewCount")
            + _regex_values(
                html_text,
                [
                    r'<[^>]+id=["\']acrCustomerReviewText["\'][^>]*>(.*?)</[^>]+>',
                    r'<[^>]+data-hook=["\']total-review-count["\'][^>]*>(.*?)</[^>]+>',
                    r'([\d,]+)\s+(?:global\s+)?ratings?',
                    r'([\d,]+)\s+reviews?',
                ],
            )
        )
        price_candidates = (
            parser.fields["price"]
            + _regex_values(
                html_text,
                [
                    r'<[^>]+class=["\'][^"\']*a-offscreen[^"\']*["\'][^>]*>(.*?)</[^>]+>',
                    r'<[^>]+id=["\']priceblock_(?:ourprice|dealprice|saleprice)["\'][^>]*>(.*?)</[^>]+>',
                ],
            )
            + [_meta_content(html_text, "product:price:amount")]
            + _json_scalar_values(html_text, "price")
        )

        title = _clean_product_title(_first(title_candidates))
        rating = _first_match(rating_candidates, r"\d+(?:\.\d+)?")
        review_count = _first_match(review_count_candidates, r"[\d,]+")
        price = _clean_price_text(_first(price_candidates))

        bullets = _unique(
            parser.fields["bullet_points"] + _feature_bullet_values(html_text),
            limit=8,
        )
        snippets = _unique(
            parser.fields["review_snippets"] + _review_snippet_values(html_text),
            limit=10,
        )
        category_hint = _clean_category_text(
            _first(parser.fields["category_hint"])
            or _meta_content(html_text, "product:category")
            or _breadcrumb_text(html_text)
            or product_category
        )

        cleaned_review_snippets = [
            _clean_review_snippet(snippet)
            for snippet in snippets
            if _clean_review_snippet(snippet)
        ]
        review_records = [
            ReviewRecord(
                text=_short_quote(snippet),
                source="amazon_review_snippet",
            )
            for snippet in cleaned_review_snippets
            if _short_quote(snippet)
        ][:6]
        evidence_quotes = [review.text for review in review_records if review.text]
        if not evidence_quotes:
            evidence_quotes = [
                _short_quote(text)
                for text in [
                    title,
                    f"Rating visible on page: {rating}" if rating else "",
                    f"Review count visible on page: {review_count}" if review_count else "",
                    f"Product bullet visible on page: {bullets[0]}" if bullets else "",
                ]
                if _short_quote(text)
            ][:4]

        confidence = self._confidence(title, rating, review_count, evidence_quotes)
        source_type = "amazon_review_api" if confidence > 0 else "unavailable"

        external_crawler_provider = _meta_content(html_text, "amazon-external-crawler-provider")
        external_review_access_status = _meta_content(html_text, "amazon-review-access-status")
        external_sign_in_required = _meta_content(html_text, "amazon-sign-in-required").lower() == "true"
        external_review_page_final_urls = _meta_content(html_text, "amazon-review-page-final-urls")
        external_review_body_count = _meta_content(html_text, "amazon-review-body-count")
        external_review_selector_found = _meta_content(html_text, "amazon-review-selector-found").lower() == "true"

        warnings = _amazon_parse_warnings(
            source_type=source_type,
            title=title,
            rating=rating,
            review_count=review_count,
            price=price,
            bullets=bullets,
            review_records=review_records,
            snippets=snippets,
            cleaned_review_snippets=cleaned_review_snippets,
        )

        if external_sign_in_required or external_review_access_status == "sign_in_required":
            warnings = _unique(["review_sign_in_required", *warnings], limit=10)

        return SourceEvidence(
            source_type=source_type,
            source_url=url,
            product_category=product_category,
            confidence=confidence,
            review_confidence=confidence,
            review_count=_safe_int(review_count),
            reviews=review_records,
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
                "external_crawler_provider": external_crawler_provider,
                "review_access_status": external_review_access_status,
                "sign_in_required": external_sign_in_required,
                "review_page_final_urls": [
                    item.strip()
                    for item in external_review_page_final_urls.split(" | ")
                    if item.strip()
                ],
                "review_body_count": _safe_int(external_review_body_count),
                "review_selector_found": external_review_selector_found,
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




def _amazon_reviews_urls(url: str) -> list[str]:
    metadata = _intake_metadata(url)
    asin = metadata.get("asin") or ""
    if not asin:
        return []
    return [
        f"https://www.amazon.com/product-reviews/{asin}/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews&sortBy=recent&pageNumber=1",
        f"https://www.amazon.com/product-reviews/{asin}?reviewerType=all_reviews&sortBy=recent&pageNumber=1",
        f"https://www.amazon.com/hz/reviews-render/ajax/reviews/get/ref=cm_cr_getr_d_paging_btm_next_1?ie=UTF8&reviewerType=all_reviews&pageNumber=1&sortBy=recent&asin={asin}",
    ]

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


def _clean_review_snippet(value: str) -> str:
    text = _clean_text(value)
    noise_phrases = [
        "Brief content visible, double tap to read full content.",
        "Full content visible, double tap to read brief content.",
        "Read more Read less",
    ]
    for phrase in noise_phrases:
        text = text.replace(phrase, " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text.strip(" -")


def _clean_category_text(value: str) -> str:
    text = _clean_text(value)
    separators = [
        chr(0x203A),
        chr(0x00E2) + chr(0x00BA),
        chr(0x00E2) + chr(0x0080) + chr(0x00BA),
        chr(0x00E2) + chr(0x20AC) + chr(0x00BA),
    ]
    for separator in separators:
        text = text.replace(separator, " > ")
    text = re.sub(r"\s*>\s*", " > ", text)
    return text.strip(" >")



def _strip_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", " ", value or "")


def _regex_values(html_text: str, patterns: list[str]) -> list[str]:
    values = []
    for pattern in patterns:
        for match in re.finditer(pattern, html_text or "", flags=re.IGNORECASE | re.S):
            values.append(_clean_text(_strip_tags(match.group(1))))
    return [value for value in values if value]


def _json_scalar_values(html_text: str, key: str) -> list[str]:
    escaped_key = re.escape(key)
    return _regex_values(
        html_text,
        [
            rf'"{escaped_key}"\s*:\s*"([^"]+)"',
            rf'"{escaped_key}"\s*:\s*([0-9]+(?:\.[0-9]+)?)',
        ],
    )


def _feature_bullet_values(html_text: str) -> list[str]:
    containers = _regex_values(
        html_text,
        [
            r'<div[^>]+id=["\']feature-bullets["\'][^>]*>(.*?)</div>',
            r'<ul[^>]+class=["\'][^"\']*a-unordered-list[^"\']*a-vertical[^"\']*["\'][^>]*>(.*?)</ul>',
        ],
    )
    values = []
    for container in containers:
        values.extend(_regex_values(container, [r"<li[^>]*>(.*?)</li>", r"<span[^>]*>(.*?)</span>"]))
    return values


def _review_snippet_values(html_text: str) -> list[str]:
    return _regex_values(
        html_text,
        [
            r'<[^>]+data-hook=["\']review-body["\'][^>]*>(.*?)</(?:span|div)>',
            r'<[^>]+data-hook=["\']review-collapsed["\'][^>]*>(.*?)</(?:span|div)>',
            r'<[^>]+data-hook=["\']review-title["\'][^>]*>(.*?)</(?:span|a|div)>',
            r'<[^>]+class=["\'][^"\']*review-text-content[^"\']*["\'][^>]*>(.*?)</(?:span|div)>',
        ],
    )


def _breadcrumb_text(html_text: str) -> str:
    values = _regex_values(
        html_text,
        [
            r'<[^>]+id=["\']wayfinding-breadcrumbs_feature_div["\'][^>]*>(.*?)</div>',
            r'<[^>]+aria-label=["\']Breadcrumb["\'][^>]*>(.*?)</(?:ul|div|nav)>',
        ],
    )
    return _first(values)


def _clean_product_title(value: str) -> str:
    title = _clean_text(value)
    title = re.sub(r"\s*:\s*Amazon\.[A-Za-z.]+:.*$", "", title).strip()
    return title


def _clean_price_text(value: str) -> str:
    price = _clean_text(value)
    if not price:
        return ""
    match = re.search(r"[$??]\s*\d+(?:[.,]\d{2})?", price)
    if match:
        return match.group(0).replace(" ", "")
    match = re.search(r"\d+(?:[.,]\d{2})", price)
    return match.group(0) if match else price


def _amazon_parse_warnings(
    source_type: str,
    title: str,
    rating: str,
    review_count: str,
    price: str,
    bullets: list[str],
    review_records: list[ReviewRecord],
    snippets: list[str],
    cleaned_review_snippets: list[str],
) -> list[str]:
    if source_type != "amazon_review_api":
        return ["amazon_parse_empty"]

    warnings = []
    if not title:
        warnings.append("missing_product_title")
    if not rating:
        warnings.append("missing_rating")
    if not review_count:
        warnings.append("missing_review_count")
    if not price:
        warnings.append("missing_price")
    if not bullets:
        warnings.append("missing_bullet_points")
    if len(review_records) < 2:
        warnings.append("sparse_reviews")
    if snippets and len(cleaned_review_snippets) < len(snippets):
        warnings.append("low_review_text_quality")
    if warnings:
        warnings.append("partial_parse")
    return _unique(warnings, limit=10)


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
