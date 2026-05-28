import os
import unittest
from unittest.mock import patch

from scripts.run_local_playwright_amazon_crawler_worker import (
    amazon_review_urls,
    asin_from_url,
    build_external_payload_from_html,
    detect_page_debug,
)


class LocalPlaywrightAmazonCrawlerWorkerTest(unittest.TestCase):
    def test_asin_and_review_urls_are_built_for_amazon_product(self):
        url = "https://www.amazon.com/dp/B000TEST00?th=1"
        self.assertEqual(asin_from_url(url), "B000TEST00")

        review_urls = amazon_review_urls(url)

        self.assertGreaterEqual(len(review_urls), 3)
        self.assertTrue(any("/product-reviews/B000TEST00" in item for item in review_urls))
        self.assertTrue(any("/hz/reviews-render/" in item for item in review_urls))

    def test_detect_page_debug_classifies_blocked_and_review_pages(self):
        blocked = "<html><title>Robot Check</title><body>Enter the characters you see below</body></html>"
        review_html = '<span data-hook="review-body">This review is useful.</span>'

        blocked_debug = detect_page_debug(blocked, final_url="https://www.amazon.com/errors/validateCaptcha", page_title="Robot Check")
        review_debug = detect_page_debug(review_html, final_url="https://www.amazon.com/product-reviews/B000TEST00", page_title="Reviews")

        self.assertTrue(blocked_debug["blocked_detected"])
        self.assertTrue(blocked_debug["captcha_detected"])
        self.assertFalse(blocked_debug["review_selector_found"])

        self.assertFalse(review_debug["blocked_detected"])
        self.assertTrue(review_debug["review_selector_found"])
        self.assertEqual(review_debug["review_body_count"], 1)

    def test_build_external_payload_from_html_maps_to_external_contract(self):
        html = """
        <span id="productTitle">Free Local Worker Product</span>
        <span class="a-offscreen">$7.99</span>
        <span class="a-icon-alt">4.5 out of 5 stars</span>
        <span id="acrCustomerReviewText">77 ratings</span>
        <div id="feature-bullets"><ul><li><span>Clips onto cans.</span></li></ul></div>
        <span data-hook="review-title">Useful</span>
        <span data-hook="review-body">This keeps beans from falling into the sink.</span>
        <span data-hook="review-body">Small enough to store in a drawer.</span>
        """

        payload = build_external_payload_from_html(
            {"detail": html},
            "https://www.amazon.com/dp/B000TEST00",
            page_debugs=[
                {
                    "label": "detail",
                    "final_url": "https://www.amazon.com/dp/B000TEST00",
                    "page_title": "Product",
                    "blocked_detected": False,
                    "captcha_detected": False,
                    "review_selector_found": True,
                    "review_body_count": 2,
                    "debug_html_path": "",
                }
            ],
        )

        self.assertEqual(payload["product_title"], "Free Local Worker Product")
        self.assertEqual(payload["price"], "$7.99")
        self.assertEqual(payload["rating"], "4.5")
        self.assertEqual(payload["review_count"], "77")
        self.assertEqual(payload["provider"], "local_playwright")
        self.assertEqual(payload["debug"]["review_body_count"], 2)
        self.assertGreaterEqual(len(payload["review_items"]), 2)
        combined = " ".join(item["text"] for item in payload["review_items"])
        self.assertIn("keeps beans from falling", combined)


if __name__ == "__main__":
    unittest.main()
