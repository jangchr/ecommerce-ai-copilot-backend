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




class ReviewWorkspaceAnalysisQualityTest(unittest.TestCase):
    def test_food_review_workspace_uses_food_relevant_labels(self):
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.post(
            "/api/v1/analyze-review-workspace",
            json={
                "workspace_id": "food_label_quality_smoke",
                "source": "unit_test",
                "output_language": "en",
                "products": [
                    {
                        "platform": "amazon",
                        "url": "https://www.amazon.com/dp/B00QIIMCCW",
                        "title": "Colavita Balsamic Vinegar - 8.5 oz",
                        "brand": "Colavita",
                        "description": "Balsamic vinegar for salad dressing and cooking.",
                        "reviews": [
                            {
                                "rating": "1 out of 5 stars",
                                "text": "This is the wateriest, most flavorless balsamic I have ever encountered. Makes terrible vinaigrette.",
                                "source_section": "amazon_visible_review",
                            },
                            {
                                "rating": "4 out of 5 stars",
                                "text": "The stated size is wrong. I received the regular size bottle, which is good as long as they do not send the half size.",
                                "source_section": "amazon_visible_review",
                            },
                            {
                                "rating": "5 out of 5 stars",
                                "text": "I love this stuff. It tastes great and is cheaper than buying it at my local grocery store.",
                                "source_section": "amazon_visible_review",
                            },
                        ],
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()

        pain_labels = {item["label"] for item in body["common_pain_points"]}
        objection_labels = {item["label"] for item in body["buyer_objections"]}

        self.assertIn("taste / flavor concern", pain_labels)
        self.assertIn("size / quantity mismatch", pain_labels)
        self.assertNotIn("size / fit issue", pain_labels)
        self.assertNotIn("hard to clean", pain_labels)
        self.assertNotIn("leak / mess risk", pain_labels)
        self.assertTrue(all("?" not in label for label in pain_labels | objection_labels))



class ReviewWorkspaceEvidenceQualityTest(unittest.TestCase):
    def test_review_workspace_compacts_evidence_and_refines_objections(self):
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.post(
            "/api/v1/analyze-review-workspace",
            json={
                "workspace_id": "evidence_quality_smoke",
                "source": "unit_test",
                "output_language": "en",
                "products": [
                    {
                        "platform": "amazon",
                        "url": "https://www.amazon.com/dp/B00QIIMCCW",
                        "title": "Colavita Balsamic Vinegar - 8.5 oz",
                        "brand": "Colavita",
                        "description": "Balsamic vinegar for salad dressing and cooking.",
                        "reviews": [
                            {
                                "rating": "4 out of 5 stars",
                                "text": "Peter M. Ross, Ph.D. 4 out of 5 stars the stated size is wrong Reviewed in the United States on February 28, 2021 Size: 17 Fl Oz (Pack of 1) Verified Purchase I like the flavor and have used colavita balsamic for many years. I received the regular size bottle, so this is good as long as they do not send the half size.",
                                "source_section": "amazon_visible_review",
                            },
                            {
                                "rating": "5 out of 5 stars",
                                "text": "T 5 out of 5 stars Not sold by the single bottle Reviewed in Canada on April 2, 2024 Size: 17 Fl Oz (Pack of 1) Verified Purchase When I purchased the balsamic vinegar it only came in a 2-pack so you might want to substitute for something else if you do not use it often.",
                                "source_section": "amazon_visible_review",
                            },
                        ],
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()

        objection_labels = {item["label"] for item in body["buyer_objections"]}
        self.assertIn("quantity / size uncertainty", objection_labels)
        self.assertNotIn("objection: but", objection_labels)
        self.assertNotIn("objection: not", objection_labels)
        self.assertTrue(all(not label.startswith("objection:") for label in objection_labels))

        all_quotes = []
        for section in ["common_pain_points", "buyer_objections", "liked_points", "use_cases"]:
            for item in body.get(section, []):
                all_quotes.extend(item.get("evidence_quotes", []))

        self.assertTrue(all(len(quote) <= 280 for quote in all_quotes))
        self.assertTrue(all("Reviewed in " not in quote for quote in all_quotes))
        self.assertTrue(all("Verified Purchase" not in quote for quote in all_quotes))



class ReviewWorkspaceEvidenceSentenceTest(unittest.TestCase):
    def test_review_workspace_extracts_key_evidence_sentence(self):
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.post(
            "/api/v1/analyze-review-workspace",
            json={
                "workspace_id": "evidence_sentence_smoke",
                "source": "unit_test",
                "output_language": "en",
                "products": [
                    {
                        "platform": "amazon",
                        "url": "https://www.amazon.com/dp/B00QIIMCCW",
                        "title": "Colavita Balsamic Vinegar - 8.5 oz",
                        "brand": "Colavita",
                        "description": "Balsamic vinegar for salad dressing and cooking.",
                        "reviews": [
                            {
                                "rating": "5 out of 5 stars",
                                "text": "Larry Langdon 5 out of 5 stars Great tasting balsamic vinegar Reviewed in the United States on December 18, 2020 Size: 17 Fl Oz (Pack of 1) Verified Purchase Revised 5/26/21 - Now this is listed as 8 1/2 oz for $4.99 but what came was a 17 oz bottle - still only $4.99! So it's probably listed and priced wrong. Still Great product!!! I bought this after reading reviews in both whole foods and amazon sections.",
                                "source_section": "amazon_visible_review",
                            },
                        ],
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()

        quotes = []
        for item in body.get("common_pain_points", []):
            quotes.extend(item.get("evidence_quotes", []))

        joined = "\n".join(quotes)
        self.assertIn("listed as 8 1/2 oz", joined)
        self.assertIn("what came was a 17 oz bottle", joined)
        self.assertNotIn("I bought this after reading reviews", joined)
        self.assertTrue(all(len(quote) <= 240 for quote in quotes))



class ReviewWorkspaceEvidenceFragmentCleanupTest(unittest.TestCase):
    def test_review_workspace_drops_broken_fragments_and_positive_objection_noise(self):
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.post(
            "/api/v1/analyze-review-workspace",
            json={
                "workspace_id": "evidence_fragment_cleanup_smoke",
                "source": "unit_test",
                "output_language": "en",
                "products": [
                    {
                        "platform": "amazon",
                        "url": "https://www.amazon.com/dp/B00QIIMCCW",
                        "title": "Colavita Balsamic Vinegar - 8.5 oz",
                        "brand": "Colavita",
                        "description": "Balsamic vinegar for salad dressing and cooking.",
                        "reviews": [
                            {
                                "rating": "4 out of 5 stars",
                                "text": "Peter M. Ross, Ph.D. 4 out of 5 stars the stated size is wrong Reviewed in the United States on February 28, 2021 Size: 17 Fl Oz (Pack of 1) Verified Purchase I like the flavor and have used colavita balsamic for many years. I ordered this because I was out. I received the regular size (16 oz?) colavita, so this is good as long as they do not send the half size (8 oz).",
                                "source_section": "amazon_visible_review",
                            },
                            {
                                "rating": "4 out of 5 stars",
                                "text": "Peter M. Ross, Ph.D. 4 out of 5 stars I have used this product for years. Reviewed in Canada on July 13, 2024 Size: 17 Fl Oz (Pack of 1) Verified Purchase Consistent good quality in my opinion. Not super complex, but great for cooking.",
                                "source_section": "amazon_visible_review",
                            },
                        ],
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()

        all_quotes = []
        for section in ["common_pain_points", "buyer_objections", "liked_points", "use_cases"]:
            for item in body.get(section, []):
                all_quotes.extend(item.get("evidence_quotes", []))

        # Do not allow the old broken fragment that started mid-parenthesis,
        # but allow normal text such as "(16 oz?) colavita".
        self.assertTrue(all(not quote.lstrip().startswith(") colavita") for quote in all_quotes))

        objection_quotes = []
        for item in body.get("buyer_objections", []):
            objection_quotes.extend(item.get("evidence_quotes", []))

        # Positive cooking praise can appear elsewhere, but it should not be treated
        # as a buyer objection.
        self.assertTrue(all("great for cooking" not in quote for quote in objection_quotes))
        self.assertTrue(all(not quote.lower().startswith("but great") for quote in objection_quotes))


if __name__ == "__main__":
    unittest.main()
