import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _actor_id_for_url(actor_id: str) -> str:
    return actor_id.replace("/", "~")


def _replace_template_values(value: Any, url: str) -> Any:
    if isinstance(value, str):
        return value.replace("{url}", url)
    if isinstance(value, list):
        return [_replace_template_values(item, url) for item in value]
    if isinstance(value, dict):
        return {key: _replace_template_values(item, url) for key, item in value.items()}
    return value


def build_apify_actor_input(url: str) -> dict:
    template = os.getenv("APIFY_AMAZON_INPUT_TEMPLATE_JSON", "").strip()
    if template:
        return _replace_template_values(json.loads(template), url)

    return {
        "urls": [url],
        "startUrls": [{"url": url}],
        "country": os.getenv("APIFY_AMAZON_COUNTRY", "US"),
        "maxItems": int(os.getenv("APIFY_AMAZON_MAX_ITEMS", "1")),
        "includeReviews": True,
        "maxReviews": int(os.getenv("APIFY_AMAZON_MAX_REVIEWS", "10")),
    }


def _first_value(item: dict, keys: list[str]) -> Any:
    for key in keys:
        value = item.get(key)
        if value not in (None, "", [], {}):
            return value
    return ""


def _as_list(value: Any) -> list:
    if value in (None, "", {}):
        return []
    if isinstance(value, list):
        return value
    return [value]


def _normalize_review_item(value: Any) -> dict:
    if isinstance(value, str):
        return {"text": value}
    if not isinstance(value, dict):
        return {"text": str(value)}

    title = _first_value(value, ["title", "reviewTitle", "name", "summary"])
    text = _first_value(value, ["text", "body", "content", "reviewText", "reviewDescription", "description"])
    rating = _first_value(value, ["rating", "stars", "score"])

    return {
        key: val
        for key, val in {
            "title": title,
            "text": text,
            "rating": rating,
        }.items()
        if val
    }


def normalize_apify_item(item: dict, input_url: str) -> dict:
    title = _first_value(item, ["product_title", "title", "name", "productName"])
    price = _first_value(item, ["price", "currentPrice", "priceValue", "dealPrice"])
    rating = _first_value(item, ["rating", "stars", "score", "averageRating"])
    review_count = _first_value(item, ["review_count", "reviewCount", "reviewsCount", "ratingsCount", "ratingsTotal"])
    category_hint = _first_value(item, ["category_hint", "category", "categoryName", "breadCrumbs", "breadcrumbs"])

    bullets = []
    for key in ["bullet_points", "bulletPoints", "bullets", "features", "aboutThisItem"]:
        bullets.extend(_as_list(item.get(key)))

    reviews = []
    for key in ["review_items", "reviews", "customerReviews", "reviewItems", "comments"]:
        reviews.extend(_normalize_review_item(review) for review in _as_list(item.get(key)))

    return {
        "input_url": input_url,
        "final_url": _first_value(item, ["url", "productUrl", "canonicalUrl"]) or input_url,
        "product_title": str(title or ""),
        "price": str(price or ""),
        "rating": str(rating or ""),
        "review_count": str(review_count or ""),
        "category_hint": category_hint if isinstance(category_hint, str) else " > ".join(map(str, _as_list(category_hint))),
        "bullet_points": [str(value) for value in bullets if value],
        "review_items": [review for review in reviews if review.get("text") or review.get("title")],
        "provider": "apify",
        "raw_item_keys": sorted(item.keys()),
    }


def _extract_first_dataset_item(payload: Any) -> dict:
    if isinstance(payload, list):
        return payload[0] if payload else {}
    if isinstance(payload, dict):
        for key in ["items", "data", "results", "products"]:
            value = payload.get(key)
            if isinstance(value, list) and value:
                return value[0]
        return payload
    return {}


def fetch_apify_amazon_payload(url: str) -> dict:
    token = os.getenv("APIFY_TOKEN", "").strip()
    actor_id = os.getenv("APIFY_AMAZON_ACTOR_ID", "junglee/amazon-crawler").strip()

    if not token:
        raise RuntimeError("APIFY_TOKEN is required.")
    if not actor_id:
        raise RuntimeError("APIFY_AMAZON_ACTOR_ID is required.")

    actor_url_id = _actor_id_for_url(actor_id)
    endpoint = (
        f"https://api.apify.com/v2/acts/{actor_url_id}/run-sync-get-dataset-items"
        f"?token={token}&format=json&clean=true"
    )

    response = requests.post(
        endpoint,
        json=build_apify_actor_input(url),
        headers={"Content-Type": "application/json"},
        timeout=float(os.getenv("APIFY_AMAZON_TIMEOUT_SECONDS", "180")),
    )

    if response.status_code >= 400:
        raise RuntimeError(f"Apify actor returned HTTP {response.status_code}: {response.text[:300]}")

    payload = response.json()
    item = _extract_first_dataset_item(payload)
    if not item:
        raise RuntimeError("Apify actor returned no dataset items.")

    return normalize_apify_item(item, url)


class ApifyAmazonCrawlerHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/amazon":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", "0") or "0")
        raw_body = self.rfile.read(length).decode("utf-8") if length else "{}"

        try:
            body = json.loads(raw_body or "{}")
            url = body.get("url", "")
            if not url:
                raise ValueError("Missing url")
            payload = fetch_apify_amazon_payload(url)
            self._send_json(200, payload)
        except Exception as exc:
            self._send_json(
                502,
                {
                    "error": str(exc),
                    "provider": "apify",
                    "input_url": body.get("url", "") if isinstance(body, dict) else "",
                },
            )

    def _send_json(self, status_code: int, payload: dict) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format, *args):
        return


def main() -> None:
    port = int(os.getenv("APIFY_AMAZON_CRAWLER_PORT", "8766"))
    server = HTTPServer(("127.0.0.1", port), ApifyAmazonCrawlerHandler)
    print(f"apify_amazon_crawler_worker: http://127.0.0.1:{port}/amazon")
    print("requires: APIFY_TOKEN")
    print(f"actor: {os.getenv('APIFY_AMAZON_ACTOR_ID', 'junglee/amazon-crawler')}")
    server.serve_forever()


if __name__ == "__main__":
    main()
