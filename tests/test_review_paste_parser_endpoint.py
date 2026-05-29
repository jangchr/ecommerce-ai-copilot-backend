import unittest

from fastapi.testclient import TestClient

from main import app


class ReviewPasteParserEndpointTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_parse_amazon_style_messy_paste(self):
        raw_text = """
5.0 out of 5 stars Easy cleanup
Reviewed in the United States on May 1, 2026
Verified Purchase
I love how easy this is to clean after draining beans for dinner.
8 people found this helpful

2.0 out of 5 stars Too small
Reviewed in the United States on May 2, 2026
Verified Purchase
It slips off wider cans and spills liquid into the sink. I wish the opening was bigger.
12 people found this helpful
"""

        response = self.client.post(
            "/api/v1/parse-review-paste",
            json={
                "raw_text": raw_text,
                "platform": "amazon",
                "product_title": "Silicone Can Strainer",
                "url": "https://www.amazon.com/dp/AAA",
                "asin": "AAA",
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["review_count"], 2)
        self.assertGreaterEqual(data["high_signal_review_count"], 2)
        self.assertEqual(data["workspace_product"]["title"], "Silicone Can Strainer")
        self.assertEqual(len(data["workspace_product"]["reviews"]), 2)
        self.assertEqual(data["reviews"][0]["rating"], "5.0")
        self.assertIn("easy this is to clean", data["reviews"][0]["text"])
        self.assertIn("spills liquid", data["reviews"][1]["text"])

    def test_parse_generic_paragraph_paste(self):
        raw_text = """
This product is useful for a small kitchen, but I wish it fit wider cans without leaking.
Works well for quick dinners and makes cleanup easier than using a full strainer.
"""

        response = self.client.post(
            "/api/v1/parse-review-paste",
            json={"raw_text": raw_text, "platform": "manual"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["review_count"], 2)
        self.assertGreaterEqual(data["high_signal_review_count"], 1)

    def test_parse_empty_paste_returns_warning(self):
        response = self.client.post(
            "/api/v1/parse-review-paste",
            json={"raw_text": ""},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["review_count"], 0)
        self.assertIn("empty_input", data["data_warnings"])
        self.assertIn("no_reviews_detected", data["data_warnings"])


if __name__ == "__main__":
    unittest.main()
