import html as html_lib
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from urllib.error import HTTPError, URLError

import requests


@dataclass
class AmazonCrawlerResult:
    url: str
    html: str
    status_code: int = 0
    final_url: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    crawler_name: str = ""


class AmazonCrawlerError(RuntimeError):
    def __init__(self, message: str, error_type: str = "crawler_error"):
        super().__init__(message)
        self.error_type = error_type


class BaseAmazonCrawler(ABC):
    crawler_name = "base_amazon_crawler"

    @abstractmethod
    def fetch_html(self, url: str) -> AmazonCrawlerResult:
        raise NotImplementedError


class RequestsAmazonCrawler(BaseAmazonCrawler):
    crawler_name = "requests_amazon_crawler"

    def __init__(self, timeout_seconds: float = 12.0):
        self.timeout_seconds = timeout_seconds

    def fetch_html(self, url: str) -> AmazonCrawlerResult:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
        }

        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=self.timeout_seconds,
                allow_redirects=True,
            )
        except requests.Timeout as exc:
            raise TimeoutError(str(exc)) from exc
        except requests.ConnectionError as exc:
            raise URLError(exc) from exc
        except requests.RequestException as exc:
            raise URLError(str(exc)) from exc

        if response.status_code >= 400:
            raise HTTPError(
                response.url or url,
                response.status_code,
                response.reason,
                hdrs=response.headers,
                fp=None,
            )

        return AmazonCrawlerResult(
            url=url,
            html=response.text or "",
            status_code=response.status_code,
            final_url=response.url or url,
            headers=dict(response.headers or {}),
            crawler_name=self.crawler_name,
        )


class PlaywrightAmazonCrawler(BaseAmazonCrawler):
    crawler_name = "playwright_amazon_crawler"

    def __init__(self, timeout_seconds: float = 18.0):
        self.timeout_seconds = timeout_seconds

    def fetch_html(self, url: str) -> AmazonCrawlerResult:
        try:
            from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
            from playwright.sync_api import sync_playwright
        except Exception as exc:
            raise AmazonCrawlerError(
                "Playwright crawler requested but playwright is not installed.",
                error_type="playwright_not_installed",
            ) from exc

        try:
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
                    page = context.new_page()
                    page.route(
                        "**/*",
                        lambda route: (
                            route.abort()
                            if route.request.resource_type in {"image", "font", "media"}
                            else route.continue_()
                        ),
                    )

                    response = page.goto(
                        url,
                        wait_until="domcontentloaded",
                        timeout=int(self.timeout_seconds * 1000),
                    )
                    self._settle_page(page, url)
                    html = page.content()

                    return AmazonCrawlerResult(
                        url=url,
                        html=html or "",
                        status_code=response.status if response else 0,
                        final_url=page.url or url,
                        crawler_name=self.crawler_name,
                    )
                finally:
                    browser.close()
        except PlaywrightTimeoutError as exc:
            raise TimeoutError(str(exc)) from exc

    def _settle_page(self, page, url: str) -> None:
        selectors = [
            "#productTitle",
            "#acrCustomerReviewText",
            "[data-hook='review-body']",
            "[data-hook='review-title']",
            ".review-text-content",
        ]
        for selector in selectors:
            try:
                page.wait_for_selector(selector, timeout=3500)
                break
            except Exception:
                continue

        try:
            page.wait_for_timeout(800)
            page.mouse.wheel(0, 1200)
            page.wait_for_timeout(900)
            page.mouse.wheel(0, 1800)
            page.wait_for_timeout(700)
        except Exception:
            pass

        if "product-reviews" in url or "reviews-render" in url:
            for selector in [
                "[data-hook='expand-collapse-read-more-less']",
                ".cr-see-more",
                "text=Read more",
            ]:
                try:
                    for button in page.locator(selector).all()[:6]:
                        try:
                            button.click(timeout=600)
                        except Exception:
                            continue
                except Exception:
                    continue
            try:
                page.wait_for_selector("[data-hook='review-body']", timeout=2500)
            except Exception:
                pass



class ExternalAmazonCrawler(BaseAmazonCrawler):
    crawler_name = "external_amazon_crawler"

    def __init__(
        self,
        endpoint_url: str | None = None,
        api_token: str | None = None,
        timeout_seconds: float = 30.0,
    ):
        self.endpoint_url = (endpoint_url or os.getenv("AMAZON_EXTERNAL_CRAWLER_URL", "")).strip()
        self.api_token = api_token or os.getenv("AMAZON_EXTERNAL_CRAWLER_TOKEN", "")
        self.timeout_seconds = timeout_seconds

    def fetch_html(self, url: str) -> AmazonCrawlerResult:
        if not self.endpoint_url:
            raise AmazonCrawlerError(
                "External Amazon crawler endpoint is not configured.",
                error_type="external_crawler_not_configured",
            )

        headers = {"Content-Type": "application/json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"

        try:
            response = requests.post(
                self.endpoint_url,
                json={"url": url},
                headers=headers,
                timeout=self.timeout_seconds,
            )
        except requests.Timeout as exc:
            raise TimeoutError(str(exc)) from exc
        except requests.RequestException as exc:
            raise AmazonCrawlerError(str(exc), error_type="external_crawler_request_failed") from exc

        if response.status_code >= 400:
            raise AmazonCrawlerError(
                f"External Amazon crawler returned HTTP {response.status_code}.",
                error_type="external_crawler_http_error",
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise AmazonCrawlerError(
                "External Amazon crawler returned non-JSON response.",
                error_type="external_crawler_invalid_json",
            ) from exc

        if not isinstance(payload, dict):
            raise AmazonCrawlerError(
                "External Amazon crawler returned invalid payload.",
                error_type="external_crawler_invalid_payload",
            )

        html = payload.get("html") or _external_payload_to_html(payload)
        if not html:
            raise AmazonCrawlerError(
                "External Amazon crawler returned empty content.",
                error_type="external_crawler_empty",
            )

        return AmazonCrawlerResult(
            url=url,
            html=html,
            status_code=response.status_code,
            final_url=payload.get("final_url") or url,
            headers=dict(response.headers or {}),
            crawler_name=self.crawler_name,
        )


class HybridAmazonCrawler(BaseAmazonCrawler):
    crawler_name = "hybrid_amazon_crawler"

    def __init__(self, primary: BaseAmazonCrawler, fallback: BaseAmazonCrawler):
        self.primary = primary
        self.fallback = fallback

    def fetch_html(self, url: str) -> AmazonCrawlerResult:
        try:
            result = self.primary.fetch_html(url)
            if result.html and not _looks_like_blocked_amazon_html(result.html):
                return result
        except Exception:
            pass

        return self.fallback.fetch_html(url)


def _external_payload_to_html(payload: dict) -> str:
    product_title = payload.get("product_title") or payload.get("title") or payload.get("name") or ""
    price = payload.get("price") or ""
    rating = payload.get("rating") or ""
    review_count = payload.get("review_count") or payload.get("ratings_count") or ""
    category_hint = payload.get("category_hint") or payload.get("category") or ""
    bullet_points = payload.get("bullet_points") or payload.get("bullets") or []
    review_items = payload.get("review_items") or payload.get("reviews") or []

    def esc(value) -> str:
        return html_lib.escape(str(value or ""), quote=True)

    bullet_html = "".join(f"<li><span>{esc(item)}</span></li>" for item in bullet_points if item)

    review_html_parts = []
    for item in review_items:
        if isinstance(item, dict):
            text = item.get("text") or item.get("body") or item.get("content") or ""
            title = item.get("title") or ""
        else:
            text = str(item or "")
            title = ""
        if title:
            review_html_parts.append(f'<span data-hook="review-title">{esc(title)}</span>')
        if text:
            review_html_parts.append(f'<span data-hook="review-body">{esc(text)}</span>')

    return "\n".join(
        part
        for part in [
            f'<span id="productTitle">{esc(product_title)}</span>' if product_title else "",
            f'<span class="a-offscreen">{esc(price)}</span>' if price else "",
            f'<span class="a-icon-alt">{esc(rating)} out of 5 stars</span>' if rating else "",
            f'<span id="acrCustomerReviewText">{esc(review_count)} ratings</span>' if review_count else "",
            f'<div id="wayfinding-breadcrumbs_feature_div">{esc(category_hint)}</div>' if category_hint else "",
            f'<div id="feature-bullets"><ul>{bullet_html}</ul></div>' if bullet_html else "",
            "\n".join(review_html_parts),
        ]
        if part
    )


def _looks_like_blocked_amazon_html(html: str) -> bool:
    lowered = (html or "").lower()
    blocked_markers = [
        "robot check",
        "enter the characters you see below",
        "sorry, we just need to make sure",
        "captcha",
        "automated access",
    ]
    return any(marker in lowered for marker in blocked_markers)



def build_amazon_crawler(mode: str | None = None) -> BaseAmazonCrawler:
    crawler_mode = (mode or os.getenv("AMAZON_CRAWLER_MODE", "requests")).strip().lower()
    if crawler_mode == "playwright":
        return PlaywrightAmazonCrawler()
    if crawler_mode == "external":
        return ExternalAmazonCrawler()
    if crawler_mode in {"hybrid", "hybrid_external", "requests_external"}:
        return HybridAmazonCrawler(RequestsAmazonCrawler(), ExternalAmazonCrawler())
    return RequestsAmazonCrawler()
