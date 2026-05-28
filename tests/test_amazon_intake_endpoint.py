import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app
from schemas.source_contract import ReviewRecord, SourceEvidence


class AmazonIntakeEndpointTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_unsupported_url_does_not_fetch_and_returns_fallback(self):
        with patch("main.source_probe_registry.fetch", side_effect=AssertionError("must not fetch")):
            response = self.client.post(
                "/api/v1/amazon-intake",
                json={"url": "https://example.com/product"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        data = payload["data"]
        self.assertFalse(data["is_supported"])
        self.assertEqual(data["provider_status"], "unsupported")
        self.assertTrue(data["fallback_required"])
        self.assertEqual(data["review_insights"]["pain_points"], [])
        self.assertIn("unsupported_amazon_url", data["data_warnings"])
        self.assertEqual(data["metadata"]["intake_reason"], "non_amazon_com_url")

    def test_supported_url_fetches_normalized_url_and_returns_summary(self):
        evidence = SourceEvidence(
            source_type="amazon_review_api",
            source_url="https://www.amazon.com/dp/B000TEST00",
            product_category="amazon_product",
            confidence=0.82,
            review_confidence=0.82,
            review_count=1234,
            reviews=[
                ReviewRecord(
                    text="The cap cracked during shipping.",
                    source="amazon_review_snippet",
                    rating=4,
                    title="Cap cracked",
                )
            ],
            evidence_quotes=["The cap cracked during shipping."],
            data_warnings=[],
            metadata={
                "asin": "B000TEST00",
                "normalized_url": "https://www.amazon.com/dp/B000TEST00",
                "intake_status": "supported",
                "intake_source_type": "amazon_product_url",
                "product_title": "Premium Balsamic Glaze",
                "rating": "4.4",
                "review_count": "1,234",
                "price": "$14.99",
                "category_hint": "Grocery & Gourmet Food > Vinegars",
                "bullet_points": ["Thick glaze for salads and cheese boards."],
            },
        )

        with patch("main.source_probe_registry.fetch", return_value=evidence) as fetch:
            response = self.client.post(
                "/api/v1/amazon-intake",
                json={
                    "url": "https://www.amazon.com/Premium-Product-Name/dp/B000TEST00?tag=demo",
                    "product_category": "balsamic_vinegar",
                },
            )

        self.assertEqual(response.status_code, 200)
        fetch.assert_called_once_with(
            "amazon_review_api",
            "https://www.amazon.com/dp/B000TEST00",
            "balsamic_vinegar",
        )

        data = response.json()["data"]
        self.assertTrue(data["is_supported"])
        self.assertEqual(data["asin"], "B000TEST00")
        self.assertEqual(data["normalized_url"], "https://www.amazon.com/dp/B000TEST00")
        self.assertEqual(data["provider_status"], "success")
        self.assertEqual(data["source_confidence"], 0.82)
        self.assertFalse(data["fallback_required"])
        self.assertEqual(data["fallback_message"], "")
        self.assertEqual(data["product_title"], "Premium Balsamic Glaze")
        self.assertEqual(data["rating"], "4.4")
        self.assertEqual(data["review_count"], "1,234")
        self.assertEqual(data["price"], "$14.99")
        self.assertIn("Thick glaze", data["bullet_points"][0])
        self.assertIn("cap cracked", data["evidence_preview"][0])
        self.assertIn("cap cracked", data["review_items"][0]["text"])
        self.assertEqual(data["review_items"][0]["source"], "amazon_review_snippet")
        self.assertEqual(data["review_items"][0]["rating"], 4)
        self.assertEqual(data["review_items"][0]["title"], "Cap cracked")
        self.assertIn("cap cracked", " ".join(data["review_insights"]["pain_points"]))
        self.assertIn("cap cracked", " ".join(data["review_insights"]["buyer_objections"]))
        self.assertIn("cap cracked", " ".join(data["review_insights"]["evidence_quotes"]))

    def test_supported_url_fetch_unavailable_returns_fallback(self):
        evidence = SourceEvidence(
            source_type="unavailable",
            confidence=0.0,
            evidence_quotes=[],
            data_warnings=["blocked"],
            metadata={
                "asin": "B000TEST00",
                "normalized_url": "https://www.amazon.com/dp/B000TEST00",
                "intake_status": "supported",
                "error": "blocked",
            },
        )

        with patch("main.source_probe_registry.fetch", return_value=evidence):
            response = self.client.post(
                "/api/v1/amazon-intake",
                json={"url": "https://www.amazon.com/dp/B000TEST00"},
            )

        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["provider_status"], "unavailable")
        self.assertTrue(data["fallback_required"])
        self.assertIn("Paste 3-5 Amazon reviews", data["fallback_message"])
        self.assertIn("blocked", data["data_warnings"])

    def test_fetch_exception_returns_safe_fallback(self):
        with patch("main.source_probe_registry.fetch", side_effect=RuntimeError("blocked")):
            response = self.client.post(
                "/api/v1/amazon-intake",
                json={"url": "https://www.amazon.com/dp/B000TEST00"},
            )

        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["provider_status"], "error")
        self.assertTrue(data["fallback_required"])
        self.assertEqual(data["error"], "blocked")
        self.assertIn("amazon_fetch_error", data["data_warnings"])



    def test_amazon_intake_fallback_message_mentions_sign_in(self):
        from main import _amazon_intake_fallback_message

        message = _amazon_intake_fallback_message(["review_sign_in_required"])

        self.assertIn("Amazon reviews require sign-in", message)
        self.assertIn("Paste 3-5 Amazon reviews", message)

if __name__ == "__main__":
    unittest.main()
