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
