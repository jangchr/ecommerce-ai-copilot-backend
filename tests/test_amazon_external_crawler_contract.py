import os
import threading
import unittest
from source_adapters.amazon_crawler import ExternalAmazonCrawler
from http.server import HTTPServer

from scripts.run_fake_amazon_crawler_worker import FakeAmazonCrawlerHandler
from source_adapters.amazon_review_adapter import AmazonReviewAdapter


class AmazonExternalCrawlerContractTest(unittest.TestCase):
    def test_external_crawler_contract_smoke_with_local_worker(self):
        server = HTTPServer(("127.0.0.1", 0), FakeAmazonCrawlerHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        old_mode = os.environ.get("AMAZON_CRAWLER_MODE")
        old_url = os.environ.get("AMAZON_EXTERNAL_CRAWLER_URL")

        try:
            os.environ["AMAZON_CRAWLER_MODE"] = "external"
            os.environ["AMAZON_EXTERNAL_CRAWLER_URL"] = f"http://127.0.0.1:{server.server_port}/amazon"

            evidence = AmazonReviewAdapter().fetch(
                "https://www.amazon.com/dp/B000FAKE01",
                "amazon_product",
            )

            self.assertEqual(evidence.source_type, "amazon_review_api")
            self.assertEqual(evidence.metadata["product_title"], "Fake Worker Silicone Can Strainer")
            self.assertEqual(evidence.metadata["price"], "$9.99")
            self.assertEqual(evidence.metadata["rating"], "4.7")
            self.assertEqual(evidence.review_count, 321)
            self.assertGreaterEqual(len(evidence.reviews), 3)
            combined = " ".join(review.text for review in evidence.reviews)
            self.assertIn("keeps beans from falling", combined)
            self.assertIn("Small enough to store", combined)
            self.assertNotIn("sparse_reviews", evidence.data_warnings)
        finally:
            if old_mode is None:
                os.environ.pop("AMAZON_CRAWLER_MODE", None)
            else:
                os.environ["AMAZON_CRAWLER_MODE"] = old_mode

            if old_url is None:
                os.environ.pop("AMAZON_EXTERNAL_CRAWLER_URL", None)
            else:
                os.environ["AMAZON_EXTERNAL_CRAWLER_URL"] = old_url

            server.shutdown()
            server.server_close()



    def test_external_crawler_reads_timeout_from_environment(self):
        old_timeout = os.environ.get("AMAZON_EXTERNAL_CRAWLER_TIMEOUT_SECONDS")
        try:
            os.environ["AMAZON_EXTERNAL_CRAWLER_TIMEOUT_SECONDS"] = "90"
            crawler = ExternalAmazonCrawler(endpoint_url="http://127.0.0.1:8767/amazon")
            self.assertEqual(crawler.timeout_seconds, 90.0)
        finally:
            if old_timeout is None:
                os.environ.pop("AMAZON_EXTERNAL_CRAWLER_TIMEOUT_SECONDS", None)
            else:
                os.environ["AMAZON_EXTERNAL_CRAWLER_TIMEOUT_SECONDS"] = old_timeout

    def test_external_crawler_constructor_timeout_overrides_environment(self):
        old_timeout = os.environ.get("AMAZON_EXTERNAL_CRAWLER_TIMEOUT_SECONDS")
        try:
            os.environ["AMAZON_EXTERNAL_CRAWLER_TIMEOUT_SECONDS"] = "90"
            crawler = ExternalAmazonCrawler(
                endpoint_url="http://127.0.0.1:8767/amazon",
                timeout_seconds=7,
            )
            self.assertEqual(crawler.timeout_seconds, 7.0)
        finally:
            if old_timeout is None:
                os.environ.pop("AMAZON_EXTERNAL_CRAWLER_TIMEOUT_SECONDS", None)
            else:
                os.environ["AMAZON_EXTERNAL_CRAWLER_TIMEOUT_SECONDS"] = old_timeout


    def test_external_debug_review_sign_in_metadata_is_preserved(self):
        from source_adapters.amazon_crawler import _append_external_debug_meta_html, _external_payload_to_html
        from source_adapters.amazon_review_adapter import AmazonReviewAdapter

        payload = {
            "product_title": "Debug Product",
            "price": "$4.22",
            "rating": "4.6",
            "review_count": "485",
            "bullet_points": ["Useful kitchen item"],
            "review_items": [],
            "provider": "local_playwright",
            "debug": {
                "provider": "local_playwright",
                "review_access_status": "sign_in_required",
                "sign_in_required": True,
                "review_selector_found": False,
                "review_body_count": 0,
                "review_page_final_urls": [
                    "https://www.amazon.com/ap/signin?openid.return_to=reviews"
                ],
            },
        }

        html = _append_external_debug_meta_html(_external_payload_to_html(payload), payload)
        evidence = AmazonReviewAdapter().parse_html(
            html,
            "https://www.amazon.com/dp/B00QIIMCCW",
            "amazon_product",
        )

        self.assertIn("review_sign_in_required", evidence.data_warnings)
        self.assertEqual(evidence.metadata["external_crawler_provider"], "local_playwright")
        self.assertEqual(evidence.metadata["review_access_status"], "sign_in_required")
        self.assertTrue(evidence.metadata["sign_in_required"])
        self.assertEqual(evidence.metadata["review_body_count"], 0)
        self.assertEqual(
            evidence.metadata["review_page_final_urls"],
            ["https://www.amazon.com/ap/signin?openid.return_to=reviews"],
        )

if __name__ == "__main__":
    unittest.main()
