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


def build_amazon_crawler(mode: str | None = None) -> BaseAmazonCrawler:
    crawler_mode = (mode or os.getenv("AMAZON_CRAWLER_MODE", "requests")).strip().lower()
    if crawler_mode == "playwright":
        return PlaywrightAmazonCrawler()
    return RequestsAmazonCrawler()
