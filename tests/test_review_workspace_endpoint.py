import unittest

from fastapi.testclient import TestClient

from main import app


class ReviewWorkspaceEndpointTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_analyze_review_workspace_returns_cross_product_insights(self):
        payload = {
            "workspace_id": "silicone_kitchen_tools",
            "source": "chrome_extension",
            "output_language": "en",
            "products": [
                {
                    "platform": "amazon",
                    "url": "https://www.amazon.com/dp/AAA",
                    "asin": "AAA",
                    "title": "Silicone Can Strainer A",
                    "price": "$8.99",
                    "rating": "4.4",
                    "review_count": 1200,
                    "bullet_points": ["Easy to clean", "Fits most cans"],
                    "reviews": [
                        {
                            "rating": 2,
                            "title": "Too small",
                            "text": "It slips off wider cans and spills liquid into the sink. I wish the opening was bigger.",
                            "helpful_count": 12,
                            "source_section": "critical_review",
                        },
                        {
                            "rating": 5,
                            "title": "Easy cleanup",
                            "text": "I love how easy this is to clean after draining beans for dinner.",
                            "helpful_count": 8,
                            "source_section": "top_review",
                        },
                    ],
                },
                {
                    "platform": "amazon",
                    "url": "https://www.amazon.com/dp/BBB",
                    "asin": "BBB",
                    "title": "Silicone Can Strainer B",
                    "price": "$10.99",
                    "rating": "4.2",
                    "review_count": 880,
                    "reviews": [
                        {
                            "rating": 3,
                            "title": "Messy",
                            "text": "It can leak if the can is too wide, but it is still convenient for a small kitchen.",
                            "helpful_count": 5,
                            "source_section": "recent_review",
                        }
                    ],
                },
            ],
        }

        response = self.client.post("/api/v1/analyze-review-workspace", json=payload)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["workspace_id"], "silicone_kitchen_tools")
        self.assertEqual(data["product_count"], 2)
        self.assertEqual(data["total_reviews"], 3)
        self.assertGreaterEqual(data["high_signal_review_count"], 2)
        self.assertTrue(data["common_pain_points"])
        self.assertTrue(data["buyer_objections"])
        self.assertTrue(data["liked_points"])
        self.assertTrue(data["creative_angles"])
        self.assertTrue(data["hooks"])
        self.assertEqual(len(data["product_summaries"]), 2)

    def test_analyze_review_workspace_handles_empty_workspace(self):
        response = self.client.post(
            "/api/v1/analyze-review-workspace",
            json={"workspace_id": "empty", "products": []},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["workspace_id"], "empty")
        self.assertEqual(data["product_count"], 0)
        self.assertEqual(data["total_reviews"], 0)
        self.assertEqual(data["high_signal_review_count"], 0)
        self.assertTrue(data["recommended_next_actions"])


if __name__ == "__main__":
    unittest.main()
