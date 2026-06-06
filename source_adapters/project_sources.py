"""Project-scoped source normalization and evidence artifacts.

The public URL adapters intentionally use ordinary HTTP only. They do not use
cookies, browser automation, proxies, retries, or anti-bot bypass techniques.
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from hashlib import sha256
from html import unescape
from html.parser import HTMLParser
from io import StringIO
import json
import re
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen


DEFAULT_PROJECT_ID = "demo_project_default"
SOURCE_TYPES = {
    "manual",
    "pasted_reviews",
    "amazon_url",
    "shopify_url",
    "csv_reviews",
    "text_review_batch",
    "uploaded_asset",
    "demo",
}
PUBLIC_SOURCE_TYPES = {"amazon_url", "shopify_url"}
TRACKING_QUERY_KEYS = {
    "ref",
    "ref_",
    "tag",
    "linkcode",
    "psc",
    "th",
    "qid",
    "sr",
    "utm_source",
    "utm_medium",
    "utm_campaign",
}
SAFETY_BOUNDARIES = {
    "external_video_api_called": False,
    "cost_incurred_by_crossgrowth": False,
    "llm_autonomous_decision_enabled": False,
    "anti_bot_bypass_used": False,
    "requires_manual_review": True,
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _clean_text(value: Any, limit: int = 6000) -> str:
    text = unescape(re.sub(r"<[^>]+>", " ", str(value or "")))
    return " ".join(text.split())[:limit]


def _stable_id(prefix: str, *parts: Any) -> str:
    payload = json.dumps(parts, ensure_ascii=False, sort_keys=True, default=str)
    return f"{prefix}_{sha256(payload.encode('utf-8')).hexdigest()[:20]}"


class _PublicPageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.title_parts: list[str] = []
        self.meta: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {str(key).lower(): str(value or "") for key, value in attrs}
        if tag.lower() == "title":
            self.in_title = True
        if tag.lower() != "meta":
            return
        key = (
            attributes.get("property")
            or attributes.get("name")
            or attributes.get("itemprop")
            or ""
        ).lower()
        content = attributes.get("content", "")
        if key and content:
            self.meta[key] = _clean_text(content, 1200)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title and data.strip():
            self.title_parts.append(data.strip())

    @property
    def title(self) -> str:
        return _clean_text(" ".join(self.title_parts), 500)


def normalize_project_source_url(url: str) -> str:
    raw = str(url or "").strip()
    if not raw:
        return ""
    if "://" not in raw:
        raw = f"https://{raw}"
    parsed = urlsplit(raw)
    scheme = "https" if parsed.scheme.lower() in {"http", "https"} else parsed.scheme.lower()
    host = (parsed.hostname or "").lower()
    port = f":{parsed.port}" if parsed.port and parsed.port not in {80, 443} else ""
    query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key.lower() not in TRACKING_QUERY_KEYS
    ]
    return urlunsplit((scheme, f"{host}{port}", parsed.path or "/", urlencode(query), ""))


def detect_source_type_from_url(url: str) -> str:
    parsed = urlsplit(normalize_project_source_url(url))
    host = (parsed.hostname or "").lower()
    if host == "amazon.com" or host.startswith("amazon.") or ".amazon." in host or host.startswith("smile.amazon."):
        return "amazon_url"
    if re.search(r"/products/[^/?#]+", parsed.path, flags=re.IGNORECASE):
        return "shopify_url"
    return "manual"


def parse_amazon_asin(url: str) -> str:
    path = urlsplit(normalize_project_source_url(url)).path
    match = re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})(?:[/?]|$)", path, flags=re.IGNORECASE)
    return match.group(1).upper() if match else ""


def parse_shopify_handle(url: str) -> str:
    path = urlsplit(normalize_project_source_url(url)).path
    match = re.search(r"/products/([^/?#]+)", path, flags=re.IGNORECASE)
    return match.group(1).removesuffix(".js") if match else ""


def build_source_adapter_warning(code: str, detail: str = "") -> dict[str, str]:
    return {"code": str(code or "source_warning"), "detail": _clean_text(detail, 280)}


def fetch_public_source_url(url: str, timeout: float = 8.0) -> dict[str, Any]:
    normalized_url = normalize_project_source_url(url)
    request = Request(
        normalized_url,
        headers={
            "User-Agent": "CrossGrowth-Source-Adapter/1.0 (+public source preview)",
            "Accept": "application/json,text/html;q=0.9,*/*;q=0.5",
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read(512_000).decode(
                response.headers.get_content_charset() or "utf-8",
                errors="replace",
            )
            return {
                "succeeded": True,
                "status_code": int(response.status or 200),
                "content_type": str(response.headers.get("Content-Type") or ""),
                "body": body,
                "final_url": normalize_project_source_url(response.geturl()),
                "error_type": "",
                "error": "",
            }
    except HTTPError as exc:
        return {
            "succeeded": False,
            "status_code": int(exc.code or 0),
            "content_type": "",
            "body": "",
            "final_url": normalized_url,
            "error_type": "http_error",
            "error": _clean_text(f"HTTP {exc.code}: {exc.reason}", 240),
        }
    except (URLError, TimeoutError, OSError) as exc:
        text = _clean_text(str(getattr(exc, "reason", exc)), 240)
        error_type = "timeout" if "timed out" in text.lower() or "timeout" in text.lower() else "network_error"
        return {
            "succeeded": False,
            "status_code": 0,
            "content_type": "",
            "body": "",
            "final_url": normalized_url,
            "error_type": error_type,
            "error": text,
        }


def _html_public_fields(body: str) -> dict[str, Any]:
    parser = _PublicPageParser()
    try:
        parser.feed(body or "")
    except Exception:
        pass
    return {
        "title": parser.meta.get("og:title") or parser.meta.get("twitter:title") or parser.title,
        "description": parser.meta.get("og:description") or parser.meta.get("description") or "",
        "image_reference_urls": [
            value
            for value in [parser.meta.get("og:image"), parser.meta.get("twitter:image")]
            if value
        ],
    }


def parse_source_result(
    source_type: str,
    source_url: str,
    fetch_result: dict[str, Any] | None,
) -> dict[str, Any]:
    result = dict(fetch_result or {})
    normalized_url = normalize_project_source_url(source_url)
    if not result.get("succeeded"):
        return {}
    body = str(result.get("body") or "")
    if source_type == "shopify_url" and (
        "json" in str(result.get("content_type") or "").lower()
        or str(result.get("final_url") or "").endswith(".js")
    ):
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = {}
        if isinstance(payload, dict):
            return {
                "title": _clean_text(payload.get("title"), 500),
                "description": _clean_text(payload.get("description") or payload.get("body_html")),
                "vendor": _clean_text(payload.get("vendor"), 200),
                "product_type": _clean_text(payload.get("type") or payload.get("product_type"), 200),
                "variants_count": len(payload.get("variants") or []),
                "image_reference_urls": [
                    str(item.get("src") or item)
                    for item in (payload.get("images") or [])[:8]
                    if item
                ],
                "handle": _clean_text(payload.get("handle") or parse_shopify_handle(normalized_url), 200),
            }
    return _html_public_fields(body)


def _review_text(record: Any) -> str:
    if isinstance(record, dict):
        return _clean_text(record.get("review") or record.get("text"), 1000)
    return _clean_text(record, 1000)


def normalize_review_batch(value: Any, source_type: str = "text_review_batch") -> list[dict[str, Any]]:
    if isinstance(value, list):
        records = value
    else:
        text = str(value or "").strip()
        records: list[Any] = []
        if source_type == "csv_reviews" and text:
            try:
                rows = list(csv.DictReader(StringIO(text)))
            except (csv.Error, UnicodeError):
                rows = []
            if rows and any("review" in {str(key or "").strip().lower() for key in row} for row in rows):
                records = [
                    {
                        "review": row.get("review") or row.get("Review") or row.get("text") or "",
                        "rating": row.get("rating") or row.get("Rating") or "",
                        "date": row.get("date") or row.get("Date") or "",
                        "verified": row.get("verified") or row.get("Verified") or "",
                        "variant": row.get("variant") or row.get("Variant") or "",
                        "source": row.get("source") or row.get("Source") or "",
                    }
                    for row in rows
                ]
            else:
                records = [line for line in text.replace("\r", "\n").split("\n") if line.strip()]
        else:
            records = [line for line in text.replace("\r", "\n").split("\n") if line.strip()]

    normalized: list[dict[str, Any]] = []
    for record in records:
        item = dict(record) if isinstance(record, dict) else {"review": record}
        text = _review_text(item)
        if not text or len(text) < 4:
            continue
        normalized.append(
            {
                "review": text,
                "rating": item.get("rating", ""),
                "date": _clean_text(item.get("date"), 80),
                "verified": item.get("verified", ""),
                "variant": _clean_text(item.get("variant"), 160),
                "source": _clean_text(item.get("source"), 160),
            }
        )
    return normalized


def dedupe_review_snippets(reviews: list[dict[str, Any]] | list[str]) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    for review in reviews or []:
        item = dict(review) if isinstance(review, dict) else {"review": str(review or "")}
        text = _review_text(item)
        key = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", text.lower())
        if not key or key in seen:
            continue
        seen.add(key)
        item["review"] = text
        unique.append(item)
    return unique


def classify_review_snippet(review: dict[str, Any] | str) -> dict[str, Any]:
    item = dict(review) if isinstance(review, dict) else {"review": str(review or "")}
    text = _review_text(item)
    lowered = text.lower()
    categories: list[str] = []
    marker_groups = [
        ("shipping_or_fulfillment", ["shipping", "delivery", "arrived", "damaged", "late", "package"]),
        ("buyer_objection", ["too expensive", "pricey", "not worth", "hesitate", "concern", "return"]),
        ("pain_point", ["hard to", "difficult", "leak", "broke", "noisy", "loud", "mess", "problem", "hate"]),
        ("positive_signal", ["love", "best", "great", "excellent", "worth it", "recommend", "perfect"]),
        ("usage_context", ["use it", "at work", "travel", "morning", "daily", "gym", "kitchen"]),
        ("product_quality", ["quality", "durable", "flavor", "taste", "material", "battery", "build"]),
    ]
    for category, markers in marker_groups:
        if any(marker in lowered for marker in markers):
            categories.append(category)
    if item.get("variant"):
        categories.append("variant_specific")
    if not categories:
        categories.append("unclear")
    verified_value = str(item.get("verified") or "").strip().lower()
    explicitly_verified = verified_value in {"true", "1", "yes", "verified", "verified purchase"}
    return {
        "text": text,
        "categories": list(dict.fromkeys(categories)),
        "rating": item.get("rating", ""),
        "date": item.get("date", ""),
        "verified_purchase": explicitly_verified,
        "variant": item.get("variant", ""),
        "source": item.get("source", ""),
    }


def classify_source_fetch_result(
    source_type: str,
    fetch_result: dict[str, Any] | None,
    review_count: int,
    product_signal_count: int,
) -> str:
    if source_type not in SOURCE_TYPES:
        return "failed"
    if source_type in PUBLIC_SOURCE_TYPES:
        if review_count:
            return "parsed"
        if fetch_result and fetch_result.get("succeeded") and product_signal_count:
            return "partial"
        return "fallback_required"
    return "parsed" if review_count or product_signal_count else "created"


def _adapter_id(source_type: str) -> str:
    return {
        "amazon_url": "amazon_public_url_v1",
        "shopify_url": "shopify_public_url_v1",
        "manual": "manual_source_v1",
        "pasted_reviews": "pasted_reviews_v1",
        "csv_reviews": "csv_reviews_v1",
        "text_review_batch": "text_review_batch_v1",
        "uploaded_asset": "uploaded_asset_v1",
        "demo": "demo_source_v1",
    }.get(source_type, "manual_source_v1")


def build_source_evidence_artifact(
    source: dict[str, Any],
    adapter_result: dict[str, Any],
    reviews: list[dict[str, Any]],
    review_classifications: list[dict[str, Any]],
) -> dict[str, Any]:
    extracted = dict(adapter_result.get("extracted_fields") or {})
    quotes = [_review_text(item) for item in reviews if _review_text(item)][:12]
    product_signals = [
        value
        for value in [
            extracted.get("title"),
            extracted.get("description"),
            extracted.get("vendor"),
            extracted.get("product_type"),
        ]
        if value
    ][:8]
    return {
        "artifact_version": "source_evidence_artifact_v1",
        "artifact_id": _stable_id("source_artifact", source.get("source_id"), quotes, product_signals),
        "project_id": source.get("project_id", DEFAULT_PROJECT_ID),
        "source_id": source.get("source_id", ""),
        "source_type": source.get("source_type", ""),
        "source_agent_id": "evidence_agent",
        "product_name": source.get("product_name", ""),
        "product_category": source.get("product_category", ""),
        "product_description": source.get("product_description", ""),
        "source_url": source.get("normalized_url") or source.get("source_url", ""),
        "asin": extracted.get("asin", ""),
        "shopify_handle": extracted.get("handle", ""),
        "evidence_quotes": quotes,
        "review_snippets": reviews[:20],
        "review_classifications": review_classifications[:20],
        "product_signals": product_signals,
        "asset_refs": list(extracted.get("uploaded_asset_ids") or []),
        "source_confidence": source.get("source_confidence", 0.0),
        "quality_gate": {},
        "warnings": list(source.get("warnings") or []),
        "manual_fallback_needed": bool((source.get("source_summary") or {}).get("manual_fallback_needed")),
        "safety_boundaries": dict(SAFETY_BOUNDARIES),
    }


def build_source_quality_gate(
    source: dict[str, Any],
    evidence_artifact: dict[str, Any],
) -> dict[str, Any]:
    review_count = len(evidence_artifact.get("evidence_quotes") or [])
    product_signal_count = len(evidence_artifact.get("product_signals") or [])
    source_type = source.get("source_type", "")
    warnings = list(dict.fromkeys((source.get("warnings") or []) + (evidence_artifact.get("warnings") or [])))
    if source_type not in SOURCE_TYPES:
        status = "blocked"
        readiness = "insufficient"
        action = "Choose a supported source type."
        allows_run = False
    elif review_count >= 3:
        status = "warning" if warnings else "passed"
        readiness = "ready"
        action = "Review evidence classifications, then continue to Evidence Agent."
        allows_run = True
    elif review_count:
        status = "warning"
        readiness = "ready"
        action = "Use the limited review sample carefully and keep claims conservative."
        allows_run = True
    elif product_signal_count:
        status = "fallback_required" if source_type in PUBLIC_SOURCE_TYPES else "warning"
        readiness = "product_only"
        action = "Paste customer reviews before review-grounded creative generation."
        allows_run = False
    else:
        status = "fallback_required"
        readiness = "needs_manual_reviews"
        action = "Add product details and at least one customer feedback snippet."
        allows_run = False
    return {
        "gate_version": "source_quality_gate_v1",
        "source_agent_id": "source_quality_agent",
        "target_agent_id": "evidence_agent",
        "status": status,
        "source_confidence": float(source.get("source_confidence") or 0.0),
        "evidence_readiness": readiness,
        "warnings": warnings,
        "recommended_next_action": action,
        "allows_agent_run": allows_run,
        "requires_manual_review": True,
        "safety_boundaries": dict(SAFETY_BOUNDARIES),
    }


def build_source_snapshot(
    source: dict[str, Any],
    evidence_artifact: dict[str, Any],
    quality_gate: dict[str, Any],
) -> dict[str, Any]:
    summary = source.get("source_summary") or {}
    return {
        "snapshot_version": "source_snapshot_v1",
        "project_id": source.get("project_id", DEFAULT_PROJECT_ID),
        "source_id": source.get("source_id", ""),
        "source_type": source.get("source_type", ""),
        "source_status": source.get("source_status", ""),
        "source_confidence": source.get("source_confidence", 0.0),
        "quality_gate_status": quality_gate.get("status", ""),
        "review_count": summary.get("review_count", 0),
        "unique_review_count": summary.get("unique_review_count", 0),
        "warnings": list(source.get("warnings") or []),
        "manual_fallback_needed": summary.get("manual_fallback_needed", False),
        "created_artifact_ids": [evidence_artifact.get("artifact_id", "")],
        "created_at": _utc_now_iso(),
    }


def _fetch_for_source(
    source_type: str,
    normalized_url: str,
    fetcher: Callable[[str, float], dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    if source_type == "shopify_url":
        handle = parse_shopify_handle(normalized_url)
        shopify_json_url = normalized_url
        if handle and not urlsplit(normalized_url).path.endswith(".js"):
            parsed = urlsplit(normalized_url)
            shopify_json_url = urlunsplit((parsed.scheme, parsed.netloc, f"/products/{handle}.js", "", ""))
        fetch_result = fetcher(shopify_json_url, 8.0)
        extracted = parse_source_result(source_type, shopify_json_url, fetch_result)
        if not fetch_result.get("succeeded"):
            page_result = fetcher(normalized_url, 8.0)
            page_fields = parse_source_result(source_type, normalized_url, page_result)
            extracted = {**page_fields, **{key: value for key, value in extracted.items() if value}}
            fetch_result = page_result
        extracted.setdefault("handle", handle)
        return fetch_result, extracted
    fetch_result = fetcher(normalized_url, 8.0)
    extracted = parse_source_result(source_type, normalized_url, fetch_result)
    if source_type == "amazon_url":
        extracted["asin"] = parse_amazon_asin(normalized_url)
    return fetch_result, extracted


def build_project_source(
    payload: dict[str, Any],
    *,
    fetcher: Callable[[str, float], dict[str, Any]] | None = None,
    network_fetch: bool = True,
) -> dict[str, Any]:
    data = dict(payload or {})
    safe_fetcher = fetcher or fetch_public_source_url
    source_type = str(data.get("source_type") or "").strip()
    source_url = str(data.get("source_url") or "").strip()
    if not source_type and source_url:
        source_type = detect_source_type_from_url(source_url)
    source_type = source_type or "manual"
    if source_type not in SOURCE_TYPES:
        raise ValueError("unsupported source_type")
    normalized_url = normalize_project_source_url(source_url)
    detected_type = detect_source_type_from_url(normalized_url) if normalized_url else source_type
    if source_type in PUBLIC_SOURCE_TYPES and detected_type != source_type:
        raise ValueError(f"source_url is not a valid {source_type} product URL")
    if source_type == "amazon_url" and not parse_amazon_asin(normalized_url):
        raise ValueError("Amazon source URL must include a /dp/ASIN or /gp/product/ASIN path")
    if source_type == "shopify_url" and not parse_shopify_handle(normalized_url):
        raise ValueError("Shopify source URL must include /products/{handle}")

    review_input = (
        data.get("manual_reviews")
        or data.get("pasted_reviews")
        or data.get("csv_text")
        or ""
    )
    review_source_type = source_type if source_type in {"csv_reviews", "text_review_batch"} else "text_review_batch"
    raw_reviews = normalize_review_batch(review_input, review_source_type)
    reviews = dedupe_review_snippets(raw_reviews)
    review_classifications = [classify_review_snippet(item) for item in reviews]

    fetch_result: dict[str, Any] = {}
    extracted: dict[str, Any] = {}
    if source_type in PUBLIC_SOURCE_TYPES and normalized_url and network_fetch:
        fetch_result, extracted = _fetch_for_source(
            source_type,
            normalized_url,
            safe_fetcher,
        )
    if source_type == "amazon_url":
        extracted.setdefault("asin", parse_amazon_asin(normalized_url))
    if source_type == "shopify_url":
        extracted.setdefault("handle", parse_shopify_handle(normalized_url))
    extracted["uploaded_asset_ids"] = list(data.get("uploaded_asset_ids") or [])

    product_name = _clean_text(
        data.get("product_name")
        or data.get("manual_product_name")
        or extracted.get("title"),
        500,
    )
    product_category = _clean_text(
        data.get("product_category")
        or data.get("manual_product_category")
        or extracted.get("product_type"),
        240,
    )
    product_description = _clean_text(
        data.get("product_description")
        or data.get("manual_product_description")
        or extracted.get("description")
    )
    warnings: list[str] = []
    if source_type == "amazon_url":
        warnings.extend(["amazon_public_fetch_limited", "no_verified_purchase_classification"])
    if source_type in PUBLIC_SOURCE_TYPES and not reviews:
        warnings.append("manual_reviews_recommended")
    if source_type in PUBLIC_SOURCE_TYPES:
        warnings.append("unverified_public_source")
    if source_type == "csv_reviews" and review_input and not reviews:
        warnings.extend(["csv_parse_partial", "missing_review_column"])
    if source_type in {"csv_reviews", "text_review_batch"}:
        warnings.append("manual_review_classification_recommended")
    if fetch_result and not fetch_result.get("succeeded"):
        warnings.append(f"public_fetch_{fetch_result.get('error_type') or 'failed'}")
    warnings = list(dict.fromkeys(warnings))

    product_signal_count = sum(
        bool(value)
        for value in [
            product_name,
            product_category,
            product_description,
            extracted.get("vendor"),
            extracted.get("product_type"),
            extracted.get("asin"),
            extracted.get("handle"),
        ]
    )
    confidence = 0.82 if len(reviews) >= 3 else 0.68 if reviews else 0.55 if product_signal_count else 0.2
    manual_fallback = source_type in PUBLIC_SOURCE_TYPES and not reviews
    status = classify_source_fetch_result(source_type, fetch_result, len(reviews), product_signal_count)
    now = _utc_now_iso()
    project_id = str(data.get("project_id") or DEFAULT_PROJECT_ID)
    source_id = _stable_id(
        "source",
        project_id,
        source_type,
        normalized_url,
        product_name,
        [_review_text(item) for item in reviews],
    )
    source = {
        "source_version": "project_source_v1",
        "source_id": source_id,
        "project_id": project_id,
        "source_type": source_type,
        "source_status": status,
        "source_url": source_url,
        "normalized_url": normalized_url,
        "domain": (urlsplit(normalized_url).hostname or "") if normalized_url else "",
        "product_name": product_name,
        "product_category": product_category,
        "product_description": product_description,
        "source_confidence": confidence,
        "source_quality_score": confidence,
        "warnings": warnings,
        "created_at": now,
        "updated_at": now,
        "source_summary": {
            "review_count": len(raw_reviews),
            "unique_review_count": len(reviews),
            "duplicate_review_count": max(0, len(raw_reviews) - len(reviews)),
            "product_signal_count": product_signal_count,
            "has_product_url": bool(normalized_url),
            "has_customer_feedback": bool(reviews),
            "manual_fallback_needed": manual_fallback,
        },
        "safety_boundaries": dict(SAFETY_BOUNDARIES),
        "source_notes": _clean_text(data.get("source_notes"), 1000),
    }
    adapter_result = {
        "adapter_version": "source_adapter_v1",
        "adapter_id": _adapter_id(source_type),
        "source_type": source_type,
        "fetch_mode": (
            "public_url_fetch"
            if source_type in PUBLIC_SOURCE_TYPES
            else "csv_text"
            if source_type == "csv_reviews"
            else "pasted_text"
            if source_type in {"pasted_reviews", "text_review_batch"}
            else "manual_input"
        ),
        "network_fetch_attempted": bool(source_type in PUBLIC_SOURCE_TYPES and network_fetch),
        "network_fetch_succeeded": bool(fetch_result.get("succeeded")),
        "anti_bot_bypass_used": False,
        "requires_manual_fallback": manual_fallback,
        "extracted_fields": extracted,
        "warnings": warnings,
    }
    artifact = build_source_evidence_artifact(source, adapter_result, reviews, review_classifications)
    gate = build_source_quality_gate(source, artifact)
    artifact["quality_gate"] = gate
    snapshot = build_source_snapshot(source, artifact, gate)
    return {
        "project_source": source,
        "adapter_result": adapter_result,
        "source_evidence_artifact": artifact,
        "source_quality_gate": gate,
        "source_snapshot": snapshot,
        "warnings": warnings,
    }
