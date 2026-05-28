import os
import unittest
from unittest.mock import patch

from scripts.run_apify_amazon_crawler_worker import (
    build_apify_actor_input,
    fetch_apify_amazon_payload,
    normalize_apify_item,
)


class ApifyAmazonCrawlerWorkerTest(unittest.TestCase):
    def test_normalize_apify_item_maps_product_and_reviews_to_external_contract(self):
        payload = normalize_apify_item(
            {
                "title": "Apify Worker Product",
                "currentPrice": "$12.49",
                "stars": "4.8",
                "reviewsCount": "456",
                "category": "Kitchen > Tools",
                "features": ["Clips onto cans", "Easy to rinse"],
                "reviews": [
                    {"reviewTitle": "Useful", "reviewText": "This keeps beans from falling into the sink."},
                    {"text": "Small enough to store in a drawer."},
                ],
                "url": "https://www.amazon.com/dp/B000APIFY1",
            },
            "https://www.amazon.com/dp/B000APIFY1",
        )

        self.assertEqual(payload["product_title"], "Apify Worker Product")
        self.assertEqual(payload["price"], "$12.49")
        self.assertEqual(payload["rating"], "4.8")
        self.assertEqual(payload["review_count"], "456")
        self.assertEqual(payload["category_hint"], "Kitchen > Tools")
        self.assertEqual(len(payload["bullet_points"]), 2)
        self.assertEqual(len(payload["review_items"]), 2)
        self.assertIn("keeps beans", payload["review_items"][0]["text"])

    def test_build_actor_input_supports_template_json(self):
        old_template = os.environ.get("APIFY_AMAZON_INPUT_TEMPLATE_JSON")
        try:
            os.environ["APIFY_AMAZON_INPUT_TEMPLATE_JSON"] = '{"startUrls":[{"url":"{url}"}],"country":"US","maxItems":1}'
            payload = build_apify_actor_input("https://www.amazon.com/dp/B000APIFY1")
            self.assertEqual(payload["startUrls"][0]["url"], "https://www.amazon.com/dp/B000APIFY1")
            self.assertEqual(payload["country"], "US")
        finally:
            if old_template is None:
                os.environ.pop("APIFY_AMAZON_INPUT_TEMPLATE_JSON", None)
            else:
                os.environ["APIFY_AMAZON_INPUT_TEMPLATE_JSON"] = old_template

    def test_fetch_apify_payload_calls_sync_dataset_items_endpoint(self):
        old_token = os.environ.get("APIFY_TOKEN")
        old_actor = os.environ.get("APIFY_AMAZON_ACTOR_ID")
        try:
            os.environ["APIFY_TOKEN"] = "test-token"
            os.environ["APIFY_AMAZON_ACTOR_ID"] = "junglee/amazon-crawler"

            with patch("scripts.run_apify_amazon_crawler_worker.requests.post") as post:
                response = post.return_value
                response.status_code = 200
                response.json.return_value = [
                    {
                        "name": "Dataset Product",
                        "price": "$8.00",
                        "rating": "4.6",
                        "reviewCount": "123",
                        "bulletPoints": ["Dataset bullet"],
                        "customerReviews": [{"body": "Dataset review body"}],
                    }
                ]

                payload = fetch_apify_amazon_payload("https://www.amazon.com/dp/B000APIFY1")

            called_url = post.call_args.args[0]
            self.assertIn("/v2/acts/junglee~amazon-crawler/run-sync-get-dataset-items", called_url)
            self.assertEqual(payload["product_title"], "Dataset Product")
            self.assertEqual(payload["price"], "$8.00")
            self.assertEqual(payload["review_items"][0]["text"], "Dataset review body")
        finally:
            if old_token is None:
                os.environ.pop("APIFY_TOKEN", None)
            else:
                os.environ["APIFY_TOKEN"] = old_token

            if old_actor is None:
                os.environ.pop("APIFY_AMAZON_ACTOR_ID", None)
            else:
                os.environ["APIFY_AMAZON_ACTOR_ID"] = old_actor


if __name__ == "__main__":
    unittest.main()
