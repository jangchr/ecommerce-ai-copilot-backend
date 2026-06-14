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
        packet = data["llm_evidence_packet"]
        self.assertEqual(packet["packet_version"], "review_workspace_v1")
        self.assertEqual(packet["intended_model_use"], "creative_brief_generation")
        for section in ["product", "review_stats", "evidence", "generation_constraints"]:
            with self.subTest(packet_section=section):
                self.assertIn(section, packet)
        self.assertEqual(packet["product"]["title"], "Silicone Can Strainer A")
        self.assertEqual(packet["product"]["asin"], "AAA")
        self.assertEqual(packet["product"]["source_type"], "review_workspace")
        self.assertEqual(packet["product"]["product_count"], 2)
        self.assertEqual(packet["review_stats"]["total_reviews"], 3)
        self.assertEqual(packet["review_stats"]["unique_analyzed_reviews"], 3)
        self.assertEqual(packet["review_stats"]["high_signal_reviews"], data["high_signal_review_count"])
        self.assertTrue(packet["evidence"]["buyer_objections"])
        self.assertTrue(packet["evidence"]["positive_signals"])
        self.assertTrue(packet["evidence"]["quotes"])
        self.assertTrue(packet["evidence"]["source_groups"])
        constraints = "\n".join(packet["generation_constraints"])
        self.assertIn("Do not generalize one variant/color/size issue", constraints)
        self.assertIn("Keep main product / variant / competitor source boundaries visible", constraints)

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

    def test_analyze_review_workspace_reports_raw_unique_and_duplicate_counts(self):
        duplicate_text = "The lid cracked during shipping and leaked vinegar all over the box."
        payload = {
            "workspace_id": "raw-unique-counts",
            "source": "unit_test",
            "output_language": "zh-CN",
            "products": [
                {
                    "platform": "amazon",
                    "asin": "RAW001",
                    "title": "Balsamic Vinegar Main",
                    "reviews": [
                        {
                            "rating": 1,
                            "text": duplicate_text,
                            "source_section": "amazon_visible_review",
                        },
                        {
                            "rating": 4,
                            "text": "The flavor is rich and works well for salad dressing.",
                            "source_section": "amazon_visible_review",
                        },
                    ],
                },
                {
                    "platform": "amazon",
                    "asin": "RAW002",
                    "title": "Balsamic Vinegar Variant",
                    "reviews": [
                        {
                            "rating": 2,
                            "text": duplicate_text,
                            "source_section": "amazon_visible_review",
                        }
                    ],
                },
            ],
        }

        response = self.client.post("/api/v1/analyze-review-workspace", json=payload)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total_reviews"], 2)
        self.assertEqual(data["source_breakdown"]["total_reviews"], 2)
        self.assertEqual(data["source_breakdown"]["raw_review_count"], 3)
        self.assertEqual(data["source_breakdown"]["duplicate_review_count"], 1)
        note = data["sample_interpretation"]["sample_size_note"]
        self.assertIn("3 \u6761\u53ef\u89c1\u8bc4\u8bba", note)
        self.assertIn("\u53bb\u91cd\u540e 2 \u6761\u8fdb\u5165\u5206\u6790", note)
        self.assertIn("1 \u6761\u4e3a\u91cd\u590d\u8bc4\u8bba", note)




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

    def test_balsamic_value_and_spout_signals_are_not_misclassified(self):
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.post(
            "/api/v1/analyze-review-workspace",
            json={
                "workspace_id": "balsamic_value_spout_smoke",
                "source": "unit_test",
                "output_language": "en",
                "products": [
                    {
                        "platform": "amazon",
                        "url": "https://www.amazon.com/dp/B00QIIMCCW",
                        "title": "Colavita Balsamic Vinegar - 17 oz",
                        "brand": "Colavita",
                        "reviews": [
                            {
                                "rating": "5 out of 5 stars",
                                "text": "Amy Worth the price and Cannot beat the price for this quality.",
                                "source_section": "amazon_visible_review",
                            },
                            {
                                "rating": "5 out of 5 stars",
                                "text": "retired303 Quality item. Value priced and excellent flavor.",
                                "source_section": "amazon_visible_review",
                            },
                            {
                                "rating": "4 out of 5 stars",
                                "text": "analogkid Yes it's pricy but personally I think it's worth it.",
                                "source_section": "amazon_visible_review",
                            },
                            {
                                "rating": "3 out of 5 stars",
                                "text": "Amazon Customer However, there is not lid to go over the spout, so air is ever present and oxidation is a concern.",
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
        objection_text = "\n".join(
            quote
            for item in body["buyer_objections"]
            for quote in item.get("evidence_quotes", [])
        )
        positive_text = "\n".join(
            quote
            for item in body["liked_points"]
            for quote in item.get("evidence_quotes", [])
        )
        all_quote_text = "\n".join(
            quote
            for section in ["common_pain_points", "buyer_objections", "liked_points", "use_cases"]
            for item in body.get(section, [])
            for quote in item.get("evidence_quotes", [])
        )

        self.assertIn("packaging / spout concern", objection_labels)
        self.assertNotIn("size / quantity mismatch", objection_labels)
        self.assertNotIn("quantity / size uncertainty", objection_labels)
        self.assertNotIn("Cannot beat the price", objection_text)
        self.assertNotIn("Value priced", objection_text)
        self.assertIn("pricy", objection_text)
        self.assertIn("Cannot beat the price", positive_text)
        self.assertIn("Value priced", positive_text)
        for reviewer_name in ["Amy", "retired303", "analogkid", "Amazon Customer"]:
            self.assertNotIn(reviewer_name, all_quote_text)



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





    def test_review_workspace_strips_amazon_review_chrome_from_quotes(self):
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.post(
            "/api/v1/analyze-review-workspace",
            json={
                "workspace_id": "amazon_review_chrome_cleanup_smoke",
                "source": "unit_test",
                "output_language": "zh-CN",
                "products": [
                    {
                        "platform": "amazon",
                        "asin": "B0CLEAN01",
                        "url": "https://www.amazon.co.jp/-/zh/product-reviews/B0CLEAN01",
                        "title": "Summer shirt",
                        "reviews": [
                            {
                                "rating": "3.0",
                                "text": "A\u30ab\u30b9\u30bf\u30de\u30fc 3 \u661f\uff08\u6700\u9ad8 5 \u661f\uff09 \u808c\u89e6\u308a 2025\u5e7411\u670813\u65e5\u5728\u65e5\u672c\u53d1\u5e03\u8bc4\u8bba \u989c\u8272: #06:\u6d45\u7070\u8272\u5c3a\u5bf8: M \u5df2\u786e\u8ba4\u8d2d\u4e70 \u3042\u307e\u308a\u671f\u5f85\u3057\u306a\u3044\u3067\u304f\u3060\u3055\u3044\u3002 4 \u4f4d\u4f7f\u7528\u8005\u8ba4\u4e3a\u6b64\u8bc4\u8bba\u6709\u7528 \u6709\u7528 \u4e3e\u62a5 \u5c06\u8bc4\u8bba\u7ffb\u8bd1\u6210\u4e2d\u6587",
                                "source_section": "amazon_visible_review",
                            },
                            {
                                "rating": "5 out of 5 stars",
                                "text": "Reviewer 5 out of 5 stars Great value Reviewed in the United States on May 1, 2025 Size: 8.45 Fl Oz Verified Purchase Cannot beat the price for this quality 2 people found this helpful Helpful Report",
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
        for group in body.get("source_breakdown", {}).get("source_groups", []):
            quotes.extend(group.get("evidence_quotes", []))
        for section in ["common_pain_points", "buyer_objections", "liked_points", "use_cases"]:
            for item in body.get(section, []):
                quotes.extend(item.get("evidence_quotes", []))

        joined = "\n".join(quotes)

        self.assertIn("\u3042\u307e\u308a\u671f\u5f85\u3057\u306a\u3044\u3067\u304f\u3060\u3055\u3044", joined)
        self.assertIn("Cannot beat the price for this quality", joined)

        for noisy in [
            "A\u30ab\u30b9\u30bf\u30de\u30fc",
            "\u5df2\u786e\u8ba4\u8d2d\u4e70",
            "\u4f4d\u4f7f\u7528\u8005\u8ba4\u4e3a\u6b64\u8bc4\u8bba\u6709\u7528",
            "\u6709\u7528 \u4e3e\u62a5",
            "\u5c06\u8bc4\u8bba\u7ffb\u8bd1\u6210\u4e2d\u6587",
            "Reviewed in ",
            "Verified Purchase",
            "people found this helpful",
            "Helpful Report",
        ]:
            self.assertNotIn(noisy, joined)




    def test_review_workspace_drops_mid_word_extraction_fragments(self):
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.post(
            "/api/v1/analyze-review-workspace",
            json={
                "workspace_id": "mid_word_fragment_cleanup_smoke",
                "source": "unit_test",
                "output_language": "zh-CN",
                "products": [
                    {
                        "platform": "amazon",
                        "asin": "B0FRAGMENT01",
                        "title": "Balsamic Vinegar",
                        "description": "Balsamic vinegar, glaze, dressing, cooking.",
                        "reviews": [
                            {
                                "rating": "4 out of 5 stars",
                                "text": "r to the glaze but the taste is a nice combination of both with a better quality taste of ingredients",
                                "source_section": "amazon_visible_review",
                            },
                            {
                                "rating": "5 out of 5 stars",
                                "text": "Cannot beat the price for this quality",
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
        for group in body.get("source_breakdown", {}).get("source_groups", []):
            quotes.extend(group.get("evidence_quotes", []))
        for section in ["common_pain_points", "buyer_objections", "liked_points", "use_cases"]:
            for item in body.get(section, []):
                quotes.extend(item.get("evidence_quotes", []))

        joined = "\n".join(quotes)
        self.assertNotIn("r to the glaze", joined)
        self.assertIn("Cannot beat the price for this quality", joined)




    def test_review_workspace_drops_amazon_report_modal_chrome(self):
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.post(
            "/api/v1/analyze-review-workspace",
            json={
                "workspace_id": "report_modal_cleanup_smoke",
                "source": "unit_test",
                "output_language": "zh-CN",
                "products": [
                    {
                        "platform": "amazon",
                        "asin": "B0REPORT01",
                        "title": "Balsamic Vinegar",
                        "description": "Balsamic vinegar, glaze, dressing, cooking.",
                        "reviews": [
                            {
                                "rating": "3 out of 5 stars",
                                "text": "Submit a A few common reasons customers reviews:Harassment, profanitySpam, advertisement, promotionsGiven in exchange for cash, discountsWhen we get your , we'll check if the review meets our Community guidelines",
                                "source_section": "amazon_visible_review",
                            },
                            {
                                "rating": "5 out of 5 stars",
                                "text": "Cannot beat the price for this quality",
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
        for group in body.get("source_breakdown", {}).get("source_groups", []):
            quotes.extend(group.get("evidence_quotes", []))
        for section in ["common_pain_points", "buyer_objections", "liked_points", "use_cases"]:
            for item in body.get(section, []):
                quotes.extend(item.get("evidence_quotes", []))

        joined = "\n".join(quotes).lower()
        self.assertNotIn("common reasons customers reviews", joined)
        self.assertNotIn("harassment, profanity", joined)
        self.assertNotIn("community guidelines", joined)
        self.assertIn("cannot beat the price for this quality", joined)




    def test_review_workspace_source_groups_include_structured_metadata_summary(self):
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.post(
            "/api/v1/analyze-review-workspace",
            json={
                "workspace_id": "metadata_summary_smoke",
                "source": "unit_test",
                "output_language": "zh-CN",
                "products": [
                    {
                        "platform": "amazon",
                        "asin": "B0META01",
                        "url": "https://www.amazon.co.jp/-/zh/product-reviews/B0META01",
                        "title": "Summer shirt",
                        "reviews": [
                            {
                                "rating": "3.0",
                                "text": "A\u30ab\u30b9\u30bf\u30de\u30fc 3 \u661f\uff08\u6700\u9ad8 5 \u661f\uff09 \u808c\u89e6\u308a 2025\u5e7411\u670813\u65e5\u5728\u65e5\u672c\u53d1\u5e03\u8bc4\u8bba \u989c\u8272: #06:\u6d45\u7070\u8272\u5c3a\u5bf8: M \u5df2\u786e\u8ba4\u8d2d\u4e70 \u3042\u307e\u308a\u671f\u5f85\u3057\u306a\u3044\u3067\u304f\u3060\u3055\u3044\u3002 4 \u4f4d\u4f7f\u7528\u8005\u8ba4\u4e3a\u6b64\u8bc4\u8bba\u6709\u7528",
                                "source_section": "amazon_visible_review",
                            },
                            {
                                "rating": "5 out of 5 stars",
                                "text": "Reviewer 5 out of 5 stars Great value Reviewed in the United States on May 1, 2025 Size: 8.45 Fl Oz Verified Purchase Cannot beat the price for this quality 2 people found this helpful",
                                "source_section": "amazon_visible_review",
                            },
                        ],
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        groups = body.get("source_breakdown", {}).get("source_groups", [])
        self.assertTrue(groups)

        metadata_summaries = [group.get("metadata_summary", {}) for group in groups]
        joined = str(metadata_summaries)

        self.assertTrue(any(summary.get("verified_purchase_count", 0) >= 1 for summary in metadata_summaries))
        self.assertIn("#06:\u6d45\u7070\u8272", joined)
        self.assertIn("M", joined)
        self.assertIn("2025\u5e7411\u670813\u65e5", joined)
        self.assertIn("May 1, 2025", joined)
        self.assertTrue(any(summary.get("helpful_vote_review_count", 0) >= 1 for summary in metadata_summaries))



class ReviewWorkspaceCreativeOutputQualityTest(unittest.TestCase):
    def test_review_workspace_generates_evidence_backed_creative_output(self):
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.post(
            "/api/v1/analyze-review-workspace",
            json={
                "workspace_id": "creative_output_quality_smoke",
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
                                "text": "Verified Purchase Now this is listed as 8 1/2 oz for $4.99 but what came was a 17 oz bottle - still only $4.99. So it is probably listed and priced wrong.",
                                "source_section": "amazon_visible_review",
                            },
                            {
                                "rating": "1 out of 5 stars",
                                "text": "Verified Purchase This is the wateriest, most flavorless balsamic I have ever encountered. Makes terrible vinaigrette.",
                                "source_section": "amazon_visible_review",
                            },
                        ],
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()

        angles = body["creative_angles"]
        hooks = body["hooks"]

        self.assertTrue(any("Copy-ready angle:" in angle for angle in angles))
        self.assertTrue(all("Turn the repeated complaint around" not in angle for angle in angles))
        self.assertTrue(any("POV:" in hook or "Watch this before you buy" in hook or "flavor warning" in hook for hook in hooks))
        self.assertEqual(len(hooks), len(set(hooks)))
        self.assertTrue(all("Use it to support great" not in angle for angle in angles))
        self.assertTrue(all("Use it to support love" not in angle for angle in angles))
        self.assertTrue(all("?" not in angle and "?" not in angle for angle in angles))
        self.assertTrue(all("buyers highlighting buyers" not in hook for hook in hooks))
        self.assertTrue(all("Why are buyers highlighting buyers" not in hook for hook in hooks))



    def test_review_workspace_does_not_turn_positive_two_pack_reassurance_into_pain(self):
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.post(
            "/api/v1/analyze-review-workspace",
            json={
                "workspace_id": "positive_two_pack_reassurance_smoke",
                "source": "unit_test",
                "output_language": "en",
                "products": [
                    {
                        "platform": "amazon",
                        "asin": "B0TWOPACK01",
                        "title": "Due Vittorie Oro Gold Balsamic Vinegar",
                        "description": "Barrel aged balsamic vinegar for salads, gifts, cooking, and dressing.",
                        "reviews": [
                            {
                                "rating": "5 out of 5 stars",
                                "text": "Verified Purchase If you are concerned about the two-pack, give the second bottle to a friend, who will truly appreciate the gift, and your thoughtfulness.",
                                "source_section": "amazon_visible_review",
                            },
                            {
                                "rating": "5 out of 5 stars",
                                "text": "Verified Purchase Cannot beat the price for this quality.",
                                "source_section": "amazon_visible_review",
                            },
                            {
                                "rating": "5 out of 5 stars",
                                "text": "Verified Purchase Yes it is pricy but personally I think it is worth it.",
                                "source_section": "amazon_visible_review",
                            },
                        ],
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()

        pain_and_objection_labels = " ".join(
            item.get("label", "").lower()
            for section in ["common_pain_points", "buyer_objections"]
            for item in body.get(section, [])
        )
        pain_and_objection_quotes = "\n".join(
            quote.lower()
            for section in ["common_pain_points", "buyer_objections"]
            for item in body.get(section, [])
            for quote in item.get("evidence_quotes", [])
        )

        self.assertNotIn("price / value concern", pain_and_objection_labels)
        self.assertNotIn("price / value uncertainty", pain_and_objection_labels)
        self.assertNotIn("size / quantity mismatch", pain_and_objection_labels)
        self.assertNotIn("quantity / size uncertainty", pain_and_objection_labels)
        self.assertNotIn("give the second bottle", pain_and_objection_quotes)
        self.assertNotIn("cannot beat the price", pain_and_objection_quotes)

        # Keep the positive value proof somewhere in the response, but do not require
        # the tiny smoke-test payload to always produce a liked_points theme.
        all_response_text = str(body).lower()
        self.assertIn("cannot beat the price", all_response_text)




    def test_review_workspace_does_not_turn_exceptional_positive_praise_into_objection(self):
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.post(
            "/api/v1/analyze-review-workspace",
            json={
                "workspace_id": "positive_praise_not_objection_smoke",
                "source": "unit_test",
                "output_language": "zh-CN",
                "products": [
                    {
                        "platform": "amazon",
                        "asin": "B0PRAISE01",
                        "title": "Due Vittorie Oro Gold Balsamic Vinegar",
                        "description": "Barrel aged balsamic vinegar for salads and gifts.",
                        "reviews": [
                            {
                                "rating": "5 out of 5 stars",
                                "text": "Verified Purchase Exceptional - the Due Vittorie Oro balsamic is an Elixir of the Gods.",
                                "source_section": "amazon_visible_review",
                            },
                            {
                                "rating": "5 out of 5 stars",
                                "text": "Verified Purchase Cannot beat the price for this quality.",
                                "source_section": "amazon_visible_review",
                            },
                            {
                                "rating": "5 out of 5 stars",
                                "text": "Verified Purchase This is the best balsamic vinegar I have ever had.",
                                "source_section": "amazon_visible_review",
                            },
                        ],
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()

        objection_text = "\n".join(
            quote.lower()
            for item in body.get("buyer_objections", [])
            for quote in item.get("evidence_quotes", [])
        )
        objection_labels = " ".join(
            item.get("label", "").lower()
            for item in body.get("buyer_objections", [])
        )

        self.assertNotIn("elixir of the gods", objection_text)
        self.assertNotIn("cannot beat the price", objection_text)
        self.assertNotIn("tradeoff", objection_labels)
        self.assertNotIn("hesitation", objection_labels)
        self.assertNotIn("??", objection_labels)
        self.assertNotIn("??", objection_labels)

        response_text = str(body).lower()
        self.assertIn("elixir of the gods", response_text)
        self.assertIn("cannot beat the price", response_text)





    def test_review_workspace_positive_zh_hooks_use_quote_specific_copy(self):
        from types import SimpleNamespace
        from main import _rw_hooks, _rw_positive_hook_from_theme_zh

        price_theme = SimpleNamespace(
            label="liked signal: great",
            evidence_quotes=["Cannot beat the price for this quality"],
            evidence_count=1,
        )
        gift_theme = SimpleNamespace(
            label="liked signal: recommend",
            evidence_quotes=[
                "If you are concerned about the two-pack, give the second bottle to a friend, who will truly appreciate the gift."
            ],
            evidence_count=1,
        )
        praise_theme = SimpleNamespace(
            label="liked signal: perfect",
            evidence_quotes=["This is the best balsamic vinegar I have ever had."],
            evidence_count=1,
        )

        hooks = "\n".join(
            [
                _rw_positive_hook_from_theme_zh(price_theme),
                _rw_positive_hook_from_theme_zh(gift_theme),
                _rw_positive_hook_from_theme_zh(praise_theme),
                *_rw_hooks([], [price_theme, gift_theme, praise_theme], 'zh-CN'),
            ]
        )

        self.assertNotIn("\u4e3a\u4ec0\u4e48\u4e70\u5bb6\u4f1a\u53cd\u590d\u63d0\u5230\uff1a\u4e70\u5bb6\u8ba4\u4e3a\u4f53\u9a8c\u5f88\u597d\uff1f", hooks)
        self.assertNotIn("\u4e3a\u4ec0\u4e48\u4e70\u5bb6\u4f1a\u53cd\u590d\u63d0\u5230\uff1a\u4e70\u5bb6\u8868\u793a\u559c\u6b22\uff1f", hooks)
        self.assertIn("\u5148\u770b\u8fd9\u53e5\u4e70\u5bb6\u539f\u8bdd", hooks)
        self.assertIn("\u4e24\u74f6\u88c5\u4e0d\u53ea\u662f\u591a\u4e70\u4e00\u74f6", hooks)
        self.assertIn("\u4e3a\u4ec0\u4e48\u6709\u4e70\u5bb6\u628a\u8fd9\u74f6\u9999\u918b\u5938\u5230\u8fd9\u79cd\u7a0b\u5ea6", hooks)

    def test_review_workspace_positive_zh_hook_fallback_uses_evidence_quote_and_dedupes_same_quote(self):
        from types import SimpleNamespace
        from main import _rw_hooks, _rw_positive_hook_from_theme_zh

        quote = "Not as sharp as Barq's, but smoother, greater flavor than A&W."
        great_theme = SimpleNamespace(
            label="liked signal: great",
            evidence_quotes=[quote],
            evidence_count=1,
        )
        love_theme = SimpleNamespace(
            label="liked signal: love",
            evidence_quotes=[quote],
            evidence_count=1,
        )

        hook = _rw_positive_hook_from_theme_zh(great_theme)
        hooks = _rw_hooks([], [great_theme, love_theme], "zh-CN")

        self.assertIn(quote, hook)
        self.assertNotEqual(
            hook,
            "\u8fd9\u6761\u6b63\u5411\u8bc1\u636e\u80fd\u600e\u4e48\u53d8\u6210\u5e7f\u544a\u5f00\u5934\uff1f\u5148\u770b\u4e00\u6761\u5177\u4f53\u4e70\u5bb6\u539f\u8bdd\uff1a\u4e70\u5bb6\u8ba4\u4e3a\u4f53\u9a8c\u5f88\u597d",
        )
        self.assertEqual(len(hooks), 1)
        self.assertIn(quote, hooks[0])

class ReviewWorkspaceSampleInterpretationAndScriptPackTest(unittest.TestCase):
    def test_review_workspace_returns_sample_interpretation_and_video_script_pack(self):
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.post(
            "/api/v1/analyze-review-workspace",
            json={
                "workspace_id": "sample_interpretation_script_pack_smoke",
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
                                "text": "Now this is listed as 8 1/2 oz for $4.99 but what came was a 17 oz bottle - still only $4.99. Great product for salads.",
                                "source_section": "amazon_visible_review",
                            },
                            {
                                "rating": "1 out of 5 stars",
                                "text": "This is the wateriest, most flavorless balsamic I have ever encountered. Makes terrible vinaigrette.",
                                "source_section": "amazon_visible_review",
                            },
                            {
                                "rating": "5 out of 5 stars",
                                "text": "I love using it for cooking and salads. This stuff is cheaper than buying it at my local grocery store.",
                                "source_section": "amazon_visible_review",
                            },
                        ],
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()

        sample = body["sample_interpretation"]
        self.assertIn("visible", sample["sample_type"].lower())
        self.assertTrue(sample["sample_size_note"])
        self.assertTrue(sample["suitable_for"])
        self.assertTrue(sample["not_suitable_for"])
        self.assertTrue(sample["strongest_signals"])
        self.assertTrue(sample["recommended_creative_directions"])
        self.assertTrue(sample["evidence_usage_summary"])

        pack = body["video_script_pack"]
        self.assertTrue(pack["positioning_note"])
        self.assertEqual({script["duration_label"] for script in pack["scripts"]}, {"15s", "30s"})
        for script in pack["scripts"]:
            self.assertTrue(script["hook"])
            self.assertTrue(script["voiceover"])
            self.assertTrue(script["on_screen_text"])
            self.assertTrue(script["cta"])

    def test_review_workspace_video_script_pack_uses_root_beer_quotes_instead_of_templates(self):
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.post(
            "/api/v1/analyze-review-workspace",
            json={
                "workspace_id": "root_beer_script_quality",
                "source": "unit_test",
                "output_language": "zh-CN",
                "products": [
                    {
                        "platform": "amazon",
                        "url": "https://www.amazon.com/dp/ROOTBEER01",
                        "title": "Craft Root Beer Variety Pack",
                        "brand": "Craft Soda",
                        "description": "Premium root beer for chilled pours and taste comparisons.",
                        "reviews": [
                            {
                                "rating": "3 out of 5 stars",
                                "text": "It tastes good, however it is too expensive for root beer and not worth the high price.",
                                "source_section": "amazon_visible_review",
                            },
                            {
                                "rating": "5 out of 5 stars",
                                "text": "Not as sharp as Barq's, but smoother, greater flavor than A&W.",
                                "source_section": "amazon_visible_review",
                            },
                        ],
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        pack_text = str(body["video_script_pack"])

        self.assertIn("too expensive for root beer", pack_text)
        self.assertIn("Not as sharp as Barq's", pack_text)
        self.assertIn("Craft Root Beer", pack_text)
        self.assertNotIn("\u5c55\u793a\u4e00\u4e2a\u80fd\u8bc1\u660e\u4ea7\u54c1\u5982\u4f55\u89e3\u51b3\u8fd9\u4e2a\u987e\u8651\u7684\u753b\u9762", pack_text)
        self.assertNotIn("\u4ea7\u54c1\u753b\u9762\uff1a\u62cd\u4e00\u4e2a\u6e05\u695a\u7684\u4f7f\u7528\u77ac\u95f4", pack_text)

    def test_review_workspace_keeps_root_beer_positive_quotes_out_of_objections_and_dedupes(self):
        from fastapi.testclient import TestClient
        from main import app

        positive_quote = "Love it and will continue to purchase. Great flavor."
        best_quote = "This is the best Rootbeer I have ever had and order it frequently."

        client = TestClient(app)
        response = client.post(
            "/api/v1/analyze-review-workspace",
            json={
                "workspace_id": "root_beer_positive_signal_quality",
                "source": "unit_test",
                "output_language": "zh-CN",
                "products": [
                    {
                        "platform": "amazon",
                        "url": "https://www.amazon.com/dp/ROOTBEER02",
                        "title": "1919 Draft Root Beer 16oz Can, Real Sugar, Real Vanilla, Cla...",
                        "brand": "1919",
                        "description": "Classic root beer for chilled pours and taste comparisons.",
                        "reviews": [
                            {
                                "rating": "3 out of 5 stars",
                                "text": "It tastes good, however it is too expensive for root beer and not worth the high price.",
                                "source_section": "amazon_visible_review",
                            },
                            {
                                "rating": "5 out of 5 stars",
                                "text": positive_quote,
                                "source_section": "amazon_visible_review",
                            },
                            {
                                "rating": "5 out of 5 stars",
                                "text": best_quote,
                                "source_section": "amazon_visible_review",
                            },
                            {
                                "rating": "5 out of 5 stars",
                                "text": "Not as sharp as Barq's, but smoother, greater flavor than A&W.",
                                "source_section": "amazon_visible_review",
                            },
                        ],
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()

        objection_text = "\n".join(
            quote.lower()
            for item in body.get("buyer_objections", [])
            for quote in item.get("evidence_quotes", [])
        )
        objection_labels = [
            item.get("label", "").strip().lower()
            for item in body.get("buyer_objections", [])
        ]

        self.assertNotIn("love it and will continue to purchase", objection_text)
        self.assertNotIn("best rootbeer", objection_text)
        self.assertNotIn("order it frequently", objection_text)
        self.assertNotIn("not as sharp as barq", objection_text)
        self.assertNotIn("hard", objection_labels)

        liked_quotes = [
            quote
            for item in body.get("liked_points", [])
            for quote in item.get("evidence_quotes", [])
        ]
        self.assertEqual(len(liked_quotes), len(set(liked_quotes)))
        self.assertTrue(any("Love it and will continue to purchase" in quote for quote in liked_quotes))
        self.assertTrue(any(best_quote.rstrip(".") in quote for quote in liked_quotes))

        creative_angles = body.get("creative_angles", [])
        hooks = body.get("hooks", [])
        self.assertLessEqual(sum(positive_quote in item for item in creative_angles), 1)
        self.assertLessEqual(sum(positive_quote in item for item in hooks), 1)

        pack_text = str(body["video_script_pack"])
        self.assertIn("1919 Draft Root Beer", pack_text)
        self.assertNotIn("Cla...", pack_text)
        self.assertNotIn("Real Vanilla, Cla", pack_text)


    def test_review_workspace_polishes_root_beer_labels_counts_angles_and_scripts(self):
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.post(
            "/api/v1/analyze-review-workspace",
            json={
                "workspace_id": "root_beer_output_polish",
                "source": "unit_test",
                "output_language": "zh-CN",
                "products": [
                    {
                        "platform": "amazon",
                        "asin": "B0DYLDYHXW",
                        "url": "https://www.amazon.com/dp/B0DYLDYHXW",
                        "title": "1919 Draft Root Beer 16oz Can, Real Sugar, Real Vanilla, Cla...",
                        "brand": "1919",
                        "description": "Premium root beer for chilled pours and taste comparisons.",
                        "reviews": [
                            {
                                "rating": "3 out of 5 stars",
                                "text": "Good root beer, just not worth the high price over something like IBC, which is half the price.",
                                "source_section": "amazon_visible_review",
                            },
                            {
                                "rating": "5 out of 5 stars",
                                "text": "Love it and will continue to purchase.",
                                "source_section": "amazon_visible_review",
                            },
                            {
                                "rating": "5 out of 5 stars",
                                "text": "This is the best Rootbeer I have ever had and order it frequently.",
                                "source_section": "amazon_visible_review",
                            },
                            {
                                "rating": "5 out of 5 stars",
                                "text": "If you know you know..not as sharpe as Barqs, but smother, greater flavor than A&W.",
                                "source_section": "amazon_visible_review",
                            },
                            {
                                "rating": "5 out of 5 stars",
                                "text": "Best root beer and unfortunately not available on the West coast.",
                                "source_section": "amazon_visible_review",
                            },
                        ],
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()

        liked_items = body.get("liked_points", [])
        liked_text = str(liked_items)
        self.assertIn("repeat purchase intent", liked_text)
        self.assertIn("best root beer praise", liked_text)
        self.assertIn("root beer flavor comparison", liked_text)
        self.assertNotIn("use case: for", str(body))
        self.assertNotIn("best root beer'", liked_text)

        repeat_items = [
            item for item in liked_items
            if "Love it and will continue to purchase" in " ".join(item.get("evidence_quotes", []))
        ]
        self.assertTrue(repeat_items)
        self.assertTrue(any("repeat purchase intent" in item.get("label", "") for item in repeat_items))

        use_case_text = str(body.get("use_cases", []))
        self.assertNotIn("Love it and will continue to purchase", use_case_text)
        self.assertIn("West coast", use_case_text)

        sample_usage = "\n".join(body["sample_interpretation"]["evidence_usage_summary"])
        self.assertIn("\u6b63\u5411\u8bc1\u636e\u8bc4\u8bba", sample_usage)
        self.assertNotIn("\u6b63\u5411\u8bc1\u636e\uff1a26 \u6761\u4fe1\u53f7", sample_usage)

        angles = body.get("creative_angles", [])
        self.assertLessEqual(len(angles), 3)
        self.assertTrue(any("\u98ce\u5473\u5bf9\u6bd4" in angle or "\u4ef7\u683c" in angle for angle in angles), angles)

        pack_text = str(body["video_script_pack"])
        self.assertIn("\u7b2c\u4e00\u955c", pack_text)
        self.assertIn("\u7b2c\u4e8c\u955c", pack_text)
        self.assertIn("\u7b2c\u4e09\u955c", pack_text)
        self.assertIn("Good root beer, just not worth the high price", pack_text)
        self.assertTrue("Barqs" in pack_text or "A&W" in pack_text)
        self.assertIn("1919 Draft Root Beer", pack_text)
        self.assertNotIn("Cla...", pack_text)


    def test_review_workspace_sample_interpretation_respects_chinese_output_language(self):
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.post(
            "/api/v1/analyze-review-workspace",
            json={
                "workspace_id": "sample_interpretation_script_pack_zh_smoke",
                "source": "unit_test",
                "output_language": "zh-CN",
                "products": [
                    {
                        "platform": "amazon",
                        "title": "Colavita Balsamic Vinegar",
                        "reviews": [
                            {
                                "rating": "5 out of 5 stars",
                                "text": "I love using it for cooking and salads, but the listing size can be confusing.",
                                "source_section": "amazon_visible_review",
                            }
                        ],
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("\u6837\u672c", body["sample_interpretation"]["sample_type"])
        self.assertIn("\u811a\u672c", body["video_script_pack"]["positioning_note"])


    def test_review_workspace_detects_apparel_japanese_signals(self):
        from fastapi.testclient import TestClient
        from main import app

        payload = {
            "workspace_id": "apparel-japanese-signals",
            "source": "browser_extension",
            "output_language": "en",
            "products": [
                {
                    "platform": "amazon",
                    "asin": "B0APPAREL01",
                    "url": "https://www.amazon.co.jp/-/zh/product-reviews/B0APPAREL01",
                    "title": "Summer shirt",
                    "reviews": [
                        {
                            "rating": "3.0",
                            "title": "size and sewing concern",
                            "text": "\u30b5\u30a4\u30ba\u304c\u5c0f\u3055\u3044\u3002\u7e2b\u88fd\u306e\u54c1\u8cea\u306b\u3082\u554f\u984c\u304c\u3042\u308a\u3001\u30dc\u30bf\u30f3\u7a74\u304c\u307b\u3064\u308c\u3066\u3044\u307e\u3057\u305f\u3002",
                            "source_section": "amazon_visible_review",
                        },
                        {
                            "rating": "4.0",
                            "title": "fabric comfort",
                            "text": "\u7d20\u6750\u306e\u808c\u89e6\u308a\u304c\u67d4\u3089\u304b\u304f\u3001\u590f\u3067\u3082\u6dbc\u3057\u304f\u7740\u3089\u308c\u307e\u3059\u3002",
                            "source_section": "amazon_visible_review",
                        },
                    ],
                }
            ],
        }

        client = TestClient(app)
        response = client.post("/api/v1/analyze-review-workspace", json=payload)
        self.assertEqual(response.status_code, 200)

        body = response.json()
        labels = " ".join(item["label"] for item in body["common_pain_points"])
        self.assertTrue(
            "sewing or QC concern" in labels
            or "sewing / quality control issue" in labels
            or "size / fit issue" in labels
            or "summer fabric comfort" in labels,
            labels,
        )
        self.assertTrue(body["common_pain_points"])


class ReviewWorkspaceCreativeDecisionPackTest(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient
        from main import app

        self.client = TestClient(app)

    def test_review_workspace_returns_evidence_grounded_creative_decision_pack(self):
        response = self.client.post(
            "/api/v1/analyze-review-workspace",
            json={
                "workspace_id": "creative-decision-pack",
                "source": "browser_extension",
                "output_language": "en",
                "products": [
                    {
                        "platform": "amazon",
                        "asin": "BLENDER01",
                        "title": "Portable Mini Blender",
                        "description": "Compact rechargeable blender for travel and single servings.",
                        "reviews": [
                            {
                                "rating": "2 out of 5 stars",
                                "text": "Hard to clean after one smoothie and pulp gets stuck under the blade.",
                                "source_section": "amazon_visible_review",
                            },
                            {
                                "rating": "3 out of 5 stars",
                                "text": "Too loud for early mornings in my apartment.",
                                "source_section": "amazon_visible_review",
                            },
                            {
                                "rating": "3 out of 5 stars",
                                "text": "Small enough for travel but the cup sometimes leaks in my bag.",
                                "source_section": "amazon_visible_review",
                            },
                            {
                                "rating": "5 out of 5 stars",
                                "text": "Perfect for one protein shake at work and I use it every day.",
                                "source_section": "amazon_visible_review",
                            },
                        ],
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        pack = body["creative_decision_pack"]

        self.assertEqual(pack["pack_version"], "creative_decision_pack_v1")
        for section in ["top_ad_angles", "evidence_brief", "video_prompt_pack", "quality_checks"]:
            with self.subTest(section=section):
                self.assertIn(section, pack)

        self.assertEqual(len(pack["top_ad_angles"]), 3)
        for angle in pack["top_ad_angles"]:
            with self.subTest(angle_id=angle["angle_id"]):
                for field in [
                    "title",
                    "target_audience",
                    "hook",
                    "script_outline",
                    "first_scene",
                    "second_scene",
                    "third_scene",
                    "cta",
                    "evidence_strength",
                    "risk_note",
                    "copy_ready_text",
                ]:
                    self.assertTrue(angle[field], field)
                self.assertTrue(angle["proof_quote"] or angle["missing_quote"])
                self.assertTrue(angle["proof_source"])
                for field in [
                    "angle_rank",
                    "is_recommended",
                    "recommendation_reason",
                    "evidence_strength_score",
                    "evidence_coverage",
                    "evidence_gaps",
                    "angle_cluster",
                    "duplicate_angle_note",
                    "tiktok_script",
                    "copy_readiness",
                    "claim_safety_level",
                ]:
                    self.assertIn(field, angle)
                self.assertGreaterEqual(angle["evidence_strength_score"], 0)
                self.assertLessEqual(angle["evidence_strength_score"], 100)
                self.assertEqual(
                    set(angle["tiktok_script"]),
                    {"hook", "scenes", "cta", "proof_quote", "risk_note"},
                )
                self.assertEqual(len(angle["tiktok_script"]["scenes"]), 3)

        self.assertTrue(any(angle["is_recommended"] for angle in pack["top_ad_angles"]))
        self.assertTrue(pack["recommended_angle_id"])
        self.assertTrue(pack["recommended_angle_title"])
        self.assertTrue(pack["decision_reason"])
        self.assertTrue(pack["angle_ranking_summary"])
        for field in [
            "weak_evidence_count",
            "missing_quote_count",
            "ready_to_copy_script_count",
            "duplicate_angle_count",
        ]:
            self.assertIn(field, pack)
            self.assertGreaterEqual(pack[field], 0)
        self.assertTrue(pack["creative_next_actions"])
        self.assertTrue(all(action["guidance_only"] for action in pack["creative_next_actions"]))
        feedback = pack["creative_feedback_runtime"]
        summary = feedback["feedback_summary"]
        for field in ["recommended_angle_id", "overall_readiness", "recommended_next_step"]:
            self.assertIn(field, summary)
        self.assertEqual(summary["recommended_angle_id"], pack["recommended_angle_id"])
        self.assertTrue(feedback["angle_feedback_cards"])
        for card in feedback["angle_feedback_cards"]:
            for field in ["feedback_status", "suggested_user_action", "copy_target"]:
                self.assertIn(field, card)
        script_review = feedback["script_readiness_review"]
        self.assertIn("recommended_script_ready", script_review)
        self.assertIn("copy_recommended_script_available", script_review)
        self.assertTrue(feedback["workspace_flow_hints"])
        self.assertEqual(
            feedback["safety_reminders"],
            {
                "provider_disabled": True,
                "video_generation_disabled": True,
                "llm_api_disabled": True,
                "media_upload_disabled": True,
                "paid_operation_disabled": True,
                "registry_write_disabled": True,
            },
        )

        evidence_brief = pack["evidence_brief"]
        self.assertTrue(evidence_brief["high_signal_quotes"])
        self.assertTrue(evidence_brief["source_breakdown_summary"])
        self.assertTrue(evidence_brief["sample_size_note"])

        video_pack = pack["video_prompt_pack"]
        self.assertTrue(video_pack["keyframe_prompt"])
        self.assertEqual(len(video_pack["shot_list"]), 3)
        self.assertTrue(video_pack["do_not_claim"])
        self.assertTrue(video_pack["evidence_links"])
        self.assertFalse(video_pack["provider_call_enabled"])
        self.assertFalse(video_pack["video_generation_performed"])

        checks = pack["quality_checks"]
        self.assertFalse(checks["unsafe_provider_action"])
        self.assertFalse(checks["provider_call_enabled"])
        self.assertFalse(checks["video_generation_performed"])
        self.assertFalse(checks["media_uploaded_or_downloaded"])
        self.assertFalse(checks["paid_operation_enabled"])
        self.assertEqual(checks["evidence_count"], len(evidence_brief["high_signal_quotes"]))
        self.assertTrue(checks["recommendation"])
        self.assertTrue(all(value is False for value in pack["safety_boundaries"].values()))

    def test_creative_decision_pack_prioritizes_realistic_review_evidence(self):
        response = self.client.post(
            "/api/v1/analyze-review-workspace",
            json={
                "workspace_id": "creative-decision-realistic-qa",
                "source": "browser_extension",
                "output_language": "en",
                "products": [
                    {
                        "platform": "amazon",
                        "asin": "BLENDER-QA-01",
                        "title": "Portable Mini Blender",
                        "description": "Compact rechargeable blender for travel, work, and single servings.",
                        "reviews": [
                            {
                                "rating": "2 out of 5 stars",
                                "text": "Hard to clean after one smoothie because pulp gets stuck under the blade.",
                                "source_section": "amazon_visible_review",
                            },
                            {
                                "rating": "2 out of 5 stars",
                                "text": "Cleaning under the blade takes longer than making the protein shake.",
                                "source_section": "amazon_visible_review",
                            },
                            {
                                "rating": "3 out of 5 stars",
                                "text": "The motor is too loud for early mornings in my apartment.",
                                "source_section": "amazon_visible_review",
                            },
                            {
                                "rating": "2 out of 5 stars",
                                "text": "The cup leaked in my gym bag during the commute.",
                                "source_section": "amazon_visible_review",
                            },
                            {
                                "rating": "5 out of 5 stars",
                                "text": "Perfect for one protein shake at the office and I use it every day.",
                                "source_section": "amazon_visible_review",
                            },
                            {
                                "rating": "5 out of 5 stars",
                                "text": "Small enough for travel and easy to rinse after a single serving.",
                                "source_section": "amazon_visible_review",
                            },
                            {
                                "rating": "5 out of 5 stars",
                                "text": "Nice product.",
                                "source_section": "amazon_visible_review",
                            },
                        ],
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        pack = body["creative_decision_pack"]
        angles = pack["top_ad_angles"]
        recommended = next(angle for angle in angles if angle["is_recommended"])

        self.assertEqual(len(angles), 3)
        self.assertEqual(pack["recommended_angle_id"], recommended["angle_id"])
        self.assertGreaterEqual(recommended["evidence_strength_score"], 65)
        self.assertTrue(recommended["proof_quote"])
        self.assertTrue(recommended["recommendation_reason"])
        self.assertNotIn("flavor praise", str(pack).lower())
        self.assertTrue(
            any(
                signal in str(body["common_pain_points"]).lower()
                for signal in ["clean", "noise", "leak", "mess"]
            )
        )
        self.assertTrue(
            any(
                signal in str(body["liked_points"] + body["use_cases"]).lower()
                for signal in ["travel", "office", "gym", "single-serving", "rinse"]
            )
        )

        script = recommended["tiktok_script"]
        self.assertTrue(script["hook"])
        self.assertEqual(len(script["scenes"]), 3)
        self.assertTrue(all(scene for scene in script["scenes"]))
        self.assertTrue(script["cta"])
        self.assertEqual(script["proof_quote"], recommended["proof_quote"])
        self.assertIn("visible sample", script["risk_note"])
        copy_ready_text = recommended["copy_ready_text"]
        copy_parts = [
            "Hook:",
            "Scene 1:",
            "Scene 2:",
            "Scene 3:",
            "CTA:",
            "Proof quote:",
            "Risk note:",
        ]
        copy_positions = [copy_ready_text.index(part) for part in copy_parts]
        self.assertEqual(copy_positions, sorted(copy_positions))
        self.assertIn(recommended["proof_quote"], copy_ready_text)
        self.assertIn(script["risk_note"], copy_ready_text)
        self.assertFalse(
            any(
                old_template in " ".join(script["scenes"])
                for old_template in [
                    "Show Portable Mini Blender in a real use context",
                    "Respond to",
                    "with a visible choice or comparison",
                ]
            )
        )
        self.assertTrue(
            any(
                concrete_term in " ".join(script["scenes"]).lower()
                for concrete_term in ["blade", "motor", "lid", "seal", "bag", "office", "gym"]
            )
        )

        video_pack = pack["video_prompt_pack"]
        self.assertEqual(len(video_pack["shot_list"]), 3)
        self.assertTrue(video_pack["keyframe_prompt"])
        self.assertTrue(
            any("leak-proof, quiet, or easy to clean" in item for item in video_pack["do_not_claim"])
        )
        self.assertIn("Keyframe prompt:", video_pack["copy_ready_text"])
        self.assertIn("Shot 1:", video_pack["copy_ready_text"])
        self.assertIn("Shot 2:", video_pack["copy_ready_text"])
        self.assertIn("Shot 3:", video_pack["copy_ready_text"])
        self.assertIn("Do not claim:", video_pack["copy_ready_text"])
        self.assertTrue(
            any(recommended["title"] in item for item in video_pack["do_not_claim"])
        )
        self.assertTrue(pack["creative_feedback_runtime"]["feedback_summary"]["recommended_next_step"])
        self.assertLessEqual(pack["weak_evidence_count"], len(angles))
        self.assertLessEqual(pack["missing_quote_count"], len(angles))
        self.assertTrue(all(value is False for value in pack["safety_boundaries"].values()))

    def test_review_workspace_marks_weak_evidence_instead_of_inventing_angles(self):
        response = self.client.post(
            "/api/v1/analyze-review-workspace",
            json={
                "workspace_id": "creative-decision-pack-weak-evidence",
                "source": "manual",
                "output_language": "en",
                "products": [
                    {
                        "platform": "manual",
                        "title": "Desk Lamp",
                        "reviews": [
                            {
                                "rating": "3",
                                "text": "The light feels too harsh late at night.",
                                "source_section": "visible_review",
                            }
                        ],
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        pack = response.json()["creative_decision_pack"]
        self.assertLess(len(pack["top_ad_angles"]), 3)
        self.assertTrue(pack["quality_checks"]["weak_evidence"])
        self.assertTrue(pack["weak_evidence_reason"])
        self.assertIn("Weak evidence", pack["decision_reason"])
        self.assertFalse(pack["recommended_angle_id"])
        self.assertFalse(any(angle["is_recommended"] for angle in pack["top_ad_angles"]))
        self.assertFalse(
            any(
                action["action_type"] in {"use_recommended_angle", "copy_video_prompt"}
                for action in pack["creative_next_actions"]
            )
        )
        self.assertTrue(
            all(angle["proof_quote"] or angle["missing_quote"] for angle in pack["top_ad_angles"])
        )
        feedback = pack["creative_feedback_runtime"]
        self.assertIn(
            feedback["feedback_summary"]["recommended_next_step"],
            {"collect_more_reviews", "lower_claim_strength"},
        )
        self.assertTrue(feedback["evidence_gap_actions"])
        self.assertTrue(
            all(
                action["suggested_action"] in {
                    "collect_more_reviews",
                    "lower_claim_strength",
                    "use_conservative_script",
                }
                for action in feedback["evidence_gap_actions"]
            )
        )

    def test_creative_decision_pack_dedupes_repeated_signal_clusters(self):
        response = self.client.post(
            "/api/v1/analyze-review-workspace",
            json={
                "workspace_id": "creative-decision-pack-dedupe",
                "source": "manual",
                "output_language": "en",
                "products": [
                    {
                        "platform": "manual",
                        "title": "Portable Blender",
                        "reviews": [
                            {"rating": "2", "text": "Hard to clean after a smoothie."},
                            {"rating": "2", "text": "Hard to clean because pulp stays under the blade."},
                            {"rating": "5", "text": "Small enough to carry to work every day."},
                            {"rating": "3", "text": "The cup leaks in my bag during travel."},
                        ],
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        pack = response.json()["creative_decision_pack"]
        clusters = [angle["angle_cluster"] for angle in pack["top_ad_angles"]]
        self.assertEqual(len(clusters), len(set(clusters)))
        self.assertGreaterEqual(pack["duplicate_angle_count"], 0)

    def test_creative_quality_checks_detect_unsupported_claims(self):
        from main import _rw_creative_quality_checks

        checks = _rw_creative_quality_checks(
            [
                {
                    "angle_id": "angle_risky",
                    "proof_quote": "It is convenient for one smoothie.",
                    "missing_quote": False,
                    "evidence_strength": "moderate",
                    "hook": "This is 100% guaranteed to work for everyone.",
                    "script_outline": "Show the product.",
                    "first_scene": "Show the product.",
                    "second_scene": "Show the use case.",
                    "third_scene": "Show the quote.",
                    "cta": "Review the supplied buyer evidence before deciding.",
                }
            ],
            evidence_count=1,
        )

        self.assertTrue(checks["unsupported_claim"])
        self.assertIn("100% guaranteed", checks["unsupported_claim_terms"])
        self.assertIn("Remove unsupported absolute claims", checks["recommendation"])
        self.assertFalse(checks["unsafe_provider_action"])


if __name__ == "__main__":
    unittest.main()


    def test_analyze_review_workspace_returns_source_breakdown(self):
        payload = {
            "workspace_id": "source-breakdown-test",
            "source": "browser_extension",
            "output_language": "zh-CN",
            "products": [
                {
                    "platform": "amazon",
                    "asin": "MAINASIN01",
                    "url": "https://www.amazon.co.jp/-/zh/product-reviews/MAINASIN01?reviewerType=all_reviews&pageNumber=1",
                    "title": "Main shirt",
                    "reviews": [
                        {
                            "rating": "5.0",
                            "title": "Light and cool",
                            "text": "Light fabric and very comfortable for summer daily wear.",
                            "source_section": "amazon_visible_review",
                        }
                    ],
                },
                {
                    "platform": "amazon",
                    "asin": "VARIANT001",
                    "url": "https://www.amazon.co.jp/-/zh/product-reviews/VARIANT001?reviewerType=avp_only_reviews&pageNumber=1&filterByStar=critical&sortBy=recent",
                    "title": "Variant shirt",
                    "reviews": [
                        {
                            "rating": "2.0",
                            "title": "Size concern",
                            "text": "The size was too small and the buyer had to return it.",
                            "source_section": "amazon_visible_review",
                        }
                    ],
                },
            ],
        }

        response = self.client.post("/api/v1/analyze-review-workspace", json=payload)
        self.assertEqual(response.status_code, 200)

        breakdown = response.json()["source_breakdown"]
        self.assertEqual(breakdown["total_reviews"], 2)
        self.assertEqual(breakdown["main_product_reviews"], 1)
        self.assertEqual(breakdown["variant_reviews"], 1)
        self.assertEqual(breakdown["low_star_reviews"], 1)
        self.assertEqual(breakdown["verified_purchase_reviews"], 1)
        self.assertEqual(breakdown["recent_reviews"], 1)
        self.assertIn("MAINASIN01", breakdown["asin_review_counts"])
        self.assertTrue(breakdown["source_groups"])
        self.assertTrue(breakdown["guidance"])
