import unittest

from fastapi.testclient import TestClient

from main import app


class PastedReviewWorkspaceEndpointTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_analyze_pasted_review_workspace_returns_parsed_and_analysis(self):
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
            "/api/v1/analyze-pasted-review-workspace",
            json={
                "workspace_id": "paste_combo_test",
                "raw_text": raw_text,
                "platform": "amazon",
                "product_title": "Silicone Can Strainer",
                "url": "https://www.amazon.com/dp/AAA",
                "asin": "AAA",
                "output_language": "en",
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["parsed"]["review_count"], 2)
        self.assertGreaterEqual(data["parsed"]["high_signal_review_count"], 2)
        self.assertEqual(data["parsed"]["workspace_product"]["title"], "Silicone Can Strainer")
        self.assertEqual(data["analysis"]["workspace_id"], "paste_combo_test")
        self.assertEqual(data["analysis"]["product_count"], 1)
        self.assertEqual(data["analysis"]["total_reviews"], 2)
        self.assertTrue(data["analysis"]["common_pain_points"])
        self.assertTrue(data["analysis"]["creative_angles"])
        self.assertTrue(data["analysis"]["hooks"])

    def test_analyze_pasted_review_workspace_handles_empty_input(self):
        response = self.client.post(
            "/api/v1/analyze-pasted-review-workspace",
            json={
                "workspace_id": "empty_combo",
                "raw_text": "",
                "platform": "manual",
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["parsed"]["review_count"], 0)
        self.assertIn("empty_input", data["parsed"]["data_warnings"])
        self.assertEqual(data["analysis"]["workspace_id"], "empty_combo")
        self.assertEqual(data["analysis"]["total_reviews"], 0)


if __name__ == "__main__":
    unittest.main()
