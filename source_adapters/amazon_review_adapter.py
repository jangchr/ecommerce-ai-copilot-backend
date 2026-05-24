import html
import re
import urllib.request
from html.parser import HTMLParser
from typing import Optional

from schemas.source_contract import SourceEvidence
from source_adapters.base import BaseSourceAdapter


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

    def fetch(self, url: str, product_category: str) -> SourceEvidence:
        if not url:
            return self._unavailable(
                url,
                product_category,
                "missing_amazon_url",
            )
        if "amazon." not in url.lower():
            return self._unavailable(
                url,
                product_category,
                "non_amazon_url",
            )

        try:
            html_text = self._fetch_html(url)
            evidence = self.parse_html(html_text, url, product_category)
        except Exception as exc:
            return self._unavailable(
                url,
                product_category,
                "amazon_fetch_failed",
                error=str(exc),
            )

        if evidence.evidence_quotes or evidence.metadata.get("product_title"):
            return evidence
        return self._unavailable(
            url,
            product_category,
            "amazon_parse_empty",
        )

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
            content_type = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(content_type, errors="replace")

    def parse_html(self, html_text: str, url: str, product_category: str) -> SourceEvidence:
        parser = _AmazonHTMLTextParser()
        parser.feed(html_text)

        title = _first(parser.fields["product_title"]) or _meta_content(html_text, "og:title")
        rating = _first_match(parser.fields["rating"], r"\d+(?:\.\d+)?")
        review_count = _first_match(parser.fields["review_count"], r"[\d,]+")
        price = _first(parser.fields["price"]) or _meta_content(html_text, "product:price:amount")
        bullets = _unique(parser.fields["bullet_points"], limit=6)
        snippets = _unique(parser.fields["review_snippets"], limit=6)
        category_hint = _clean_text(
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
                "product_title": title,
                "rating": rating,
                "review_count": review_count,
                "price": price,
                "category_hint": category_hint,
                "bullet_points": bullets,
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
    ) -> SourceEvidence:
        metadata = {"adapter": self.__class__.__name__}
        if error:
            metadata["error"] = error
        return SourceEvidence(
            source_type="unavailable",
            source_url=url,
            product_category=product_category,
            confidence=0.0,
            review_confidence=0.0,
            review_count=0,
            evidence_quotes=[],
            data_warnings=[warning],
            metadata=metadata,
        )


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value or "")).strip()


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
