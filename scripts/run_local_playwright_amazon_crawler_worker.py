import json
import os
import re
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from source_adapters.amazon_crawler import AmazonCrawlerResult
from source_adapters.amazon_review_adapter import AmazonReviewAdapter


class StaticHTMLCrawler:
    def __init__(self, html: str):
        self.html = html

    def fetch_html(self, url: str) -> AmazonCrawlerResult:
        return AmazonCrawlerResult(url=url, html=self.html, status_code=200, final_url=url)


def asin_from_url(url: str) -> str:
    match = re.search(r"/(?:dp|gp/product|product)/([A-Z0-9]{10})(?:[/?#]|$)", url or "", flags=re.I)
    if match:
        return match.group(1).upper()
    match = re.search(r"\b([A-Z0-9]{10})\b", url or "", flags=re.I)
    return match.group(1).upper() if match else ""


def amazon_review_urls(url: str) -> list[str]:
    asin = asin_from_url(url)
    if not asin:
        return []
    return [
        f"https://www.amazon.com/product-reviews/{asin}/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews&sortBy=recent&pageNumber=1",
        f"https://www.amazon.com/product-reviews/{asin}?reviewerType=all_reviews&sortBy=recent&pageNumber=1",
        f"https://www.amazon.com/hz/reviews-render/ajax/reviews/get/ref=cm_cr_getr_d_paging_btm_next_1?ie=UTF8&reviewerType=all_reviews&pageNumber=1&sortBy=recent&asin={asin}",
    ]


def _blocked_detected(html: str) -> bool:
    lowered = (html or "").lower()
    return any(
        marker in lowered
        for marker in [
            "robot check",
            "enter the characters you see below",
            "sorry, we just need to make sure",
            "captcha",
            "automated access",
        ]
    )


def _captcha_detected(html: str) -> bool:
    lowered = (html or "").lower()
    return "captcha" in lowered or "enter the characters you see below" in lowered


def _review_selector_found(html: str) -> bool:
    lowered = (html or "").lower()
    return (
        'data-hook="review-body"' in lowered
        or "data-hook='review-body'" in lowered
        or "review-text-content" in lowered
    )


def _review_body_count(html: str) -> int:
    lowered = html or ""
    return len(re.findall(r"data-hook=[\"']review-body[\"']", lowered, flags=re.I)) + len(
        re.findall(r"review-text-content", lowered, flags=re.I)
    )


def detect_page_debug(html: str, final_url: str = "", page_title: str = "") -> dict[str, Any]:
    return {
        "final_url": final_url,
        "page_title": page_title,
        "blocked_detected": _blocked_detected(html),
        "captcha_detected": _captcha_detected(html),
        "review_selector_found": _review_selector_found(html),
        "review_body_count": _review_body_count(html),
    }


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", value or "").strip("_")
    return slug[:80] or "amazon_page"


def save_debug_html(label: str, url: str, html: str) -> str:
    if os.getenv("LOCAL_AMAZON_DEBUG_HTML", "1").strip() in {"0", "false", "False"}:
        return ""
    try:
        asin = asin_from_url(url) or "unknown"
        out_dir = ROOT / "storage" / "amazon_crawler_debug"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{int(time.time())}_{asin}_{_safe_slug(label)}.html"
        path.write_text(html or "", encoding="utf-8")
        return str(path)
    except OSError:
        return ""


def build_external_payload_from_html(
    html_by_label: dict[str, str],
    input_url: str,
    page_debugs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    combined_html = "\n".join(value for value in html_by_label.values() if value)
    adapter = AmazonReviewAdapter(crawler=StaticHTMLCrawler(combined_html))
    evidence = adapter.parse_html(combined_html, input_url, "amazon_product")
    metadata = evidence.metadata or {}

    debug_pages = page_debugs or [
        {
            "label": label,
            **detect_page_debug(html, final_url=input_url, page_title=""),
        }
        for label, html in html_by_label.items()
    ]

    debug = {
        "provider": "local_playwright",
        "asin": asin_from_url(input_url),
        "blocked_detected": any(page.get("blocked_detected") for page in debug_pages),
        "captcha_detected": any(page.get("captcha_detected") for page in debug_pages),
        "review_selector_found": any(page.get("review_selector_found") for page in debug_pages),
        "review_body_count": sum(int(page.get("review_body_count") or 0) for page in debug_pages),
        "pages": debug_pages,
    }

    return {
        "input_url": input_url,
        "final_url": debug_pages[0].get("final_url") if debug_pages else input_url,
        "product_title": metadata.get("product_title") or "",
        "price": metadata.get("price") or "",
        "rating": metadata.get("rating") or "",
        "review_count": metadata.get("review_count") or str(evidence.review_count or ""),
        "category_hint": metadata.get("category_hint") or "",
        "bullet_points": metadata.get("bullet_points") or [],
        "review_items": [
            {"text": review.text, "source": review.source}
            for review in evidence.reviews
            if review.text
        ],
        "provider": "local_playwright",
        "debug": debug,
    }


def _settle_page(page, url: str) -> None:
    selectors = [
        "#productTitle",
        "#acrCustomerReviewText",
        "[data-hook='review-body']",
        "[data-hook='review-title']",
        ".review-text-content",
    ]

    for selector in selectors:
        try:
            page.wait_for_selector(selector, timeout=3000)
            break
        except Exception:
            continue

    try:
        for _ in range(int(os.getenv("LOCAL_PLAYWRIGHT_SCROLL_ROUNDS", "4"))):
            page.mouse.wheel(0, 1500)
            page.wait_for_timeout(700)
    except Exception:
        pass

    if "product-reviews" in url or "reviews-render" in url:
        for selector in [
            "[data-hook='expand-collapse-read-more-less']",
            ".cr-see-more",
            "text=Read more",
            "text=See more",
        ]:
            try:
                for button in page.locator(selector).all()[:8]:
                    try:
                        button.click(timeout=700)
                    except Exception:
                        continue
            except Exception:
                continue
        try:
            page.wait_for_selector("[data-hook='review-body']", timeout=2500)
        except Exception:
            pass


def _fetch_page(context, url: str, label: str) -> tuple[str, dict[str, Any]]:
    page = context.new_page()
    try:
        response = page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=int(float(os.getenv("LOCAL_PLAYWRIGHT_TIMEOUT_SECONDS", "20")) * 1000),
        )
        _settle_page(page, url)
        html = page.content() or ""
        final_url = page.url or url
        title = ""
        try:
            title = page.title()
        except Exception:
            title = ""

        debug = {
            "label": label,
            "status_code": response.status if response else 0,
            **detect_page_debug(html, final_url=final_url, page_title=title),
        }
        debug["debug_html_path"] = save_debug_html(label, url, html)
        return html, debug
    finally:
        page.close()


def crawl_with_local_playwright(url: str) -> dict[str, Any]:
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        raise RuntimeError("Playwright is not installed. Run: python -m pip install playwright && python -m playwright install chromium") from exc

    html_by_label: dict[str, str] = {}
    page_debugs: list[dict[str, Any]] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ],
        )
        try:
            context = browser.new_context(
                viewport={"width": 1366, "height": 900},
                locale="en-US",
                timezone_id="America/New_York",
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0 Safari/537.36"
                ),
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "Cache-Control": "no-cache",
                },
            )
            context.route(
                "**/*",
                lambda route: (
                    route.abort()
                    if route.request.resource_type in {"image", "font", "media"}
                    else route.continue_()
                ),
            )

            html, debug = _fetch_page(context, url, "detail")
            html_by_label["detail"] = html
            page_debugs.append(debug)

            for index, reviews_url in enumerate(amazon_review_urls(url), start=1):
                try:
                    html, debug = _fetch_page(context, reviews_url, f"reviews_{index}")
                except PlaywrightTimeoutError:
                    continue
                except Exception:
                    continue
                html_by_label[f"reviews_{index}"] = html
                page_debugs.append(debug)
                if debug.get("review_body_count", 0) > 0:
                    break

            return build_external_payload_from_html(html_by_label, url, page_debugs)
        finally:
            browser.close()


class LocalPlaywrightAmazonCrawlerHandler(BaseHTTPRequestHandler):
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
            payload = crawl_with_local_playwright(url)
            self._send_json(200, payload)
        except Exception as exc:
            self._send_json(
                502,
                {
                    "error": str(exc),
                    "provider": "local_playwright",
                    "input_url": body.get("url", "") if isinstance(body, dict) else "",
                },
            )

    def _send_json(self, status_code: int, payload: dict) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format, *args):
        return


def main() -> None:
    port = int(os.getenv("LOCAL_PLAYWRIGHT_AMAZON_CRAWLER_PORT", "8767"))
    server = HTTPServer(("127.0.0.1", port), LocalPlaywrightAmazonCrawlerHandler)
    print(f"local_playwright_amazon_crawler_worker: http://127.0.0.1:{port}/amazon")
    print("free local mode: no paid provider required")
    print("debug html: storage/amazon_crawler_debug")
    server.serve_forever()


if __name__ == "__main__":
    main()
