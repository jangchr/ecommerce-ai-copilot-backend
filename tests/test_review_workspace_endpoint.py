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

    def test_review_workspace_returns_review_import_pack_for_mixed_intake(self):
        duplicate_text = "The handle cracked after two uses and made the product feel unsafe."
        payload = {
            "workspace_id": "review-import-mixed",
            "source": "manual_import",
            "output_language": "en",
            "products": [
                {
                    "platform": "amazon",
                    "url": "https://www.amazon.com/dp/MAIN001",
                    "asin": "MAIN001",
                    "title": "Manual Import Main Product",
                    "reviews": [
                        {
                            "rating": 2,
                            "title": "Cracked handle",
                            "text": duplicate_text,
                            "source_section": "amazon_visible_review",
                            "helpful_count": 6,
                        },
                        {
                            "rating": 2,
                            "title": "Same issue",
                            "text": duplicate_text,
                            "source_section": "amazon_visible_review",
                        },
                    ],
                },
                {
                    "platform": "unknown",
                    "title": "Manual Import Main Product",
                    "reviews": [
                        {
                            "title": "Manual short row",
                            "text": "Bad.",
                            "source_section": "manual_review",
                        },
                        {
                            "rating": 5,
                            "title": "Manual liked point",
                            "text": "I use it every morning and it cleans up quickly after breakfast.",
                            "source_section": "manual_review",
                        },
                    ],
                },
                {
                    "platform": "csv",
                    "title": "CSV Rows",
                    "reviews": [
                        {
                            "rating": 4,
                            "title": "CSV good row",
                            "text": "CSV row says the product works well for travel but the lid is tight.",
                            "source_section": "csv_row",
                        },
                        {
                            "rating": 5,
                            "title": "CSV empty row",
                            "text": "",
                            "source_section": "csv_row",
                        },
                    ],
                },
                {
                    "platform": "competitor",
                    "title": "Competitor Product",
                    "reviews": [
                        {
                            "rating": 3,
                            "title": "Competitor comparison",
                            "text": "Compared with a competitor, this one is easier to rinse but feels less sturdy.",
                            "source_section": "competitor_review",
                        }
                    ],
                },
            ],
        }

        response = self.client.post("/api/v1/analyze-review-workspace", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        pack = body["creative_decision_pack"]["review_import_pack"]
        summary = pack["import_summary"]
        self.assertEqual(pack["pack_version"], "review_import_pack_v1")
        self.assertEqual(summary["raw_import_count"], 7)
        self.assertEqual(summary["normalized_review_count"], 7)
        self.assertEqual(summary["duplicate_review_count"], 1)
        self.assertGreaterEqual(summary["usable_review_count"], 1)
        self.assertEqual(
            summary["source_type_counts"],
            {
                "amazon_visible": 2,
                "competitor": 1,
                "csv": 2,
                "manual": 2,
            },
        )
        self.assertFalse(pack["import_quality_checks"]["ready_as_strong_evidence"])
        self.assertIn("weak_review_sample", pack["quality_warnings"])
        self.assertIn("empty_review_text", pack["quality_warnings"])
        self.assertIn("missing_rating", pack["quality_warnings"])
        self.assertIn("duplicate_review", pack["quality_warnings"])
        self.assertIn("very_short_review", pack["quality_warnings"])

        normalized = pack["normalized_reviews"]
        self.assertEqual(len(normalized), 7)
        first_review = normalized[0]
        duplicate_review = normalized[1]
        self.assertEqual(first_review["review_text"], duplicate_text)
        self.assertEqual(first_review["normalized_text"], duplicate_text)
        self.assertFalse(first_review["is_duplicate"])
        self.assertTrue(duplicate_review["is_duplicate"])
        self.assertEqual(duplicate_review["duplicate_of"], first_review["review_id"])
        self.assertIn(duplicate_review["quality_tier"], {"weak", "empty"})
        for review in normalized:
            self.assertIn("quality_score", review)
            self.assertIn("quality_tier", review)
            self.assertIn("detected_signals", review)

        self.assertEqual(pack["source_breakdown"]["raw_review_count"], 7)
        self.assertEqual(pack["source_breakdown"]["total_reviews"], body["source_breakdown"]["total_reviews"])
        self.assertEqual(pack["source_breakdown"]["duplicate_review_count"], body["source_breakdown"]["duplicate_review_count"])
        self.assertEqual(pack["duplicate_report"]["duplicate_review_count"], 1)
        self.assertTrue(pack["duplicate_report"]["duplicate_pairs"])

        boundaries = pack["safety_boundaries"]
        for key in [
            "provider_calls_enabled",
            "llm_api_enabled",
            "video_generation_enabled",
            "media_upload_enabled",
            "media_download_enabled",
            "paid_operation_enabled",
            "registry_write_enabled",
            "rollback_enabled",
        ]:
            with self.subTest(boundary=key):
                self.assertFalse(boundaries[key])

    def test_review_import_pack_normalizes_csv_style_rows_without_changing_review_text(self):
        payload = {
            "workspace_id": "review-import-csv",
            "source": "csv_upload",
            "output_language": "en",
            "products": [
                {
                    "platform": "csv",
                    "title": "CSV Import Product",
                    "reviews": [
                        {
                            "rating": "1 out of 5 stars",
                            "title": "CSV row 1",
                            "text": "  CSV row: the seal leaked in my backpack, but customer support replaced it.  ",
                            "source_section": "csv_row",
                        },
                        {
                            "rating": "5",
                            "title": "CSV row 2",
                            "text": "CSV row: easy to clean after lunch and useful for travel.",
                            "source_section": "csv_row",
                        },
                    ],
                }
            ],
        }

        response = self.client.post("/api/v1/analyze-review-workspace", json=payload)

        self.assertEqual(response.status_code, 200)
        pack = response.json()["creative_decision_pack"]["review_import_pack"]
        summary = pack["import_summary"]
        self.assertEqual(summary["source_type_counts"], {"csv": 2})
        self.assertEqual(summary["raw_import_count"], 2)
        self.assertEqual(summary["duplicate_review_count"], 0)
        self.assertEqual(pack["normalized_reviews"][0]["review_text"], payload["products"][0]["reviews"][0]["text"])
        self.assertEqual(
            pack["normalized_reviews"][0]["normalized_text"],
            "CSV row: the seal leaked in my backpack, but customer support replaced it.",
        )
        self.assertEqual(pack["normalized_reviews"][0]["source_type"], "csv")
        self.assertGreater(pack["normalized_reviews"][0]["quality_score"], 0)
        self.assertIn(pack["normalized_reviews"][0]["quality_tier"], {"usable", "strong"})

    def test_competitor_review_comparison_pack_uses_competitor_reviews_only(self):
        payload = {
            "workspace_id": "competitor-comparison",
            "source": "manual_import",
            "output_language": "en",
            "products": [
                {
                    "platform": "amazon",
                    "title": "Own Travel Bottle",
                    "reviews": [
                        {
                            "rating": 5,
                            "title": "Easy cleaning",
                            "text": "Our bottle is easy to clean after lunch and feels sturdy in a backpack.",
                            "source_section": "amazon_visible_review",
                        },
                        {
                            "rating": 4,
                            "title": "Travel use",
                            "text": "I use it for travel because the cap is simple to rinse and convenient.",
                            "source_section": "manual_review",
                        },
                    ],
                },
                {
                    "platform": "competitor",
                    "title": "Competitor Bottle",
                    "reviews": [
                        {
                            "rating": 2,
                            "title": "Competitor leaks",
                            "text": "The competitor bottle leaked in my backpack and was hard to clean after coffee.",
                            "source_section": "competitor_review",
                        },
                        {
                            "rating": 3,
                            "title": "Competitor sturdy but messy",
                            "text": "Competitor feels sturdy, but the lid is tight and cleaning takes too long.",
                            "source_section": "competitor_review",
                        },
                    ],
                },
            ],
        }

        response = self.client.post("/api/v1/analyze-review-workspace", json=payload)

        self.assertEqual(response.status_code, 200)
        creative_pack = response.json()["creative_decision_pack"]
        self.assertIn("competitor_review_comparison_pack", creative_pack)
        pack = creative_pack["competitor_review_comparison_pack"]
        summary = pack["comparison_summary"]
        self.assertEqual(pack["pack_version"], "competitor_review_comparison_pack_v1")
        self.assertIn(summary["comparison_readiness"], {"ready", "weak_competitor_sample"})
        self.assertGreater(pack["competitor_review_profile"]["competitor_review_count"], 0)
        self.assertEqual(summary["source_type_counts"]["competitor"], 2)
        self.assertGreaterEqual(len(pack["gap_opportunity_cards"]), 1)
        self.assertGreaterEqual(len(pack["differentiation_angle_cards"]), 1)
        gap = pack["gap_opportunity_cards"][0]
        angle = pack["differentiation_angle_cards"][0]
        self.assertTrue(gap.get("evidence_quote") or gap.get("weak_evidence"))
        self.assertTrue(angle.get("competitor_evidence_quote") or angle.get("weak_evidence"))
        self.assertTrue(gap["risk_note"])
        self.assertTrue(angle["risk_note"])
        self.assertTrue(gap["do_not_claim"])
        self.assertTrue(angle["do_not_claim"])
        self.assertIn("Do not use competitor reviews as proof of own-product performance.", pack["do_not_claim"])
        self.assertNotEqual(summary["claim_safety_level"], "high")
        self.assertFalse(pack["comparison_quality_checks"]["high_claim_safety_allowed"])
        self.assertTrue(pack["competitor_risk_notes"])
        self.assertTrue(pack["recommended_competitor_actions"])

        boundaries = pack["safety_boundaries"]
        for key in [
            "provider_calls_enabled",
            "llm_api_enabled",
            "video_generation_enabled",
            "media_upload_enabled",
            "media_download_enabled",
            "paid_operation_enabled",
            "registry_write_enabled",
            "rollback_enabled",
            "external_scraping_enabled",
            "database_persistence_enabled",
        ]:
            with self.subTest(boundary=key):
                self.assertFalse(boundaries[key])

    def test_competitor_review_comparison_pack_requires_competitor_reviews(self):
        payload = {
            "workspace_id": "competitor-comparison-no-data",
            "source": "manual_import",
            "output_language": "en",
            "products": [
                {
                    "platform": "amazon",
                    "title": "Own Product Only",
                    "reviews": [
                        {
                            "rating": 4,
                            "title": "Own product review",
                            "text": "The product is easy to clean and useful for travel.",
                            "source_section": "amazon_visible_review",
                        }
                    ],
                }
            ],
        }

        response = self.client.post("/api/v1/analyze-review-workspace", json=payload)

        self.assertEqual(response.status_code, 200)
        pack = response.json()["creative_decision_pack"]["competitor_review_comparison_pack"]
        summary = pack["comparison_summary"]
        self.assertEqual(summary["comparison_readiness"], "needs_competitor_reviews")
        self.assertNotEqual(summary["comparison_readiness"], "ready")
        self.assertEqual(pack["competitor_review_profile"]["competitor_review_count"], 0)
        self.assertEqual(pack["comparison_cards"], [])
        self.assertEqual(pack["gap_opportunity_cards"], [])
        self.assertEqual(pack["differentiation_angle_cards"], [])
        self.assertFalse(pack["comparison_quality_checks"]["ready_for_comparison"])
        self.assertFalse(pack["comparison_quality_checks"]["high_claim_safety_allowed"])
        self.assertEqual(summary["claim_safety_level"], "low")
        self.assertIn("needs_competitor_reviews", summary["comparison_readiness"])




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

        variant_pack = pack["creative_variant_pack"]
        self.assertEqual(variant_pack["pack_version"], "creative_variant_pack_v1")
        self.assertEqual(len(variant_pack["variants"]), 5)
        self.assertTrue(variant_pack["recommended_variant_id"])
        self.assertEqual(
            {
                "ugc_testimonial",
                "problem_solution",
                "direct_demo",
                "objection_reversal",
                "short_hook",
            },
            {variant["variant_type"] for variant in variant_pack["variants"]},
        )
        for variant in variant_pack["variants"]:
            with self.subTest(variant_id=variant["variant_id"]):
                for field in [
                    "variant_id",
                    "variant_type",
                    "variant_title",
                    "source_angle_id",
                    "source_angle_title",
                    "target_platform",
                    "target_length_seconds",
                    "creative_style",
                    "hook",
                    "scene_1",
                    "scene_2",
                    "scene_3",
                    "cta",
                    "risk_note",
                    "video_prompt",
                    "copy_ready_script",
                    "variant_reason",
                ]:
                    self.assertTrue(variant[field], field)
                self.assertTrue(variant["proof_quote"] or variant["missing_quote"])
                self.assertEqual(len(variant["shot_list"]), 3)
                self.assertTrue(variant["do_not_claim"])
                self.assertIn(variant["proof_quote"], variant["copy_ready_script"])
                self.assertIn(variant["risk_note"], variant["copy_ready_script"])
        checks = variant_pack["variant_quality_checks"]
        for field in [
            "unsupported_claim",
            "missing_quote",
            "weak_evidence",
            "unsafe_provider_action",
        ]:
            self.assertIn(field, checks)
        self.assertFalse(checks["unsafe_provider_action"])
        self.assertTrue(variant_pack["variant_copy_export"]["variant_scripts"])
        self.assertTrue(variant_pack["variant_copy_export"]["variant_video_prompts"])
        self.assertTrue(all(value is False for value in variant_pack["safety_boundaries"].values()))
        selection_pack = variant_pack["variant_selection_pack"]
        self.assertEqual(selection_pack["pack_version"], "variant_selection_pack_v1")
        self.assertTrue(selection_pack["recommended_first_variant_id"])
        pair = selection_pack["recommended_ab_pair"]
        self.assertTrue(pair["variant_a_id"])
        self.assertTrue(pair["variant_b_id"])
        self.assertNotEqual(pair["variant_a_id"], pair["variant_b_id"])
        self.assertGreaterEqual(len(selection_pack["selection_cards"]), 5)
        self.assertTrue(
            {
                "best_for_tiktok",
                "best_for_ugc",
                "best_for_direct_response",
                "best_for_low_evidence_safe_use",
            }.issubset({card["best_for"] for card in selection_pack["selection_cards"]})
        )
        for card in selection_pack["selection_cards"]:
            with self.subTest(selection_id=card["selection_id"]):
                for field in [
                    "selection_reason",
                    "test_hypothesis",
                    "success_metric",
                    "recommended_next_action",
                ]:
                    self.assertTrue(card[field], field)
                self.assertTrue(card["proof_quote"] or card["evidence_fit"] == "missing_quote")
                self.assertTrue(card["do_not_claim"])
        ab_plan = selection_pack["ab_test_plan"]
        for field in [
            "hypothesis",
            "primary_metric",
            "what_to_change",
            "what_to_keep_constant",
        ]:
            self.assertTrue(ab_plan[field], field)
        self.assertTrue(selection_pack["selection_quality_checks"]["distinct_ab_pair"])
        for boundary in [
            "provider_enabled",
            "llm_api_enabled",
            "video_generation_enabled",
            "media_operation_enabled",
            "paid_operation_enabled",
            "registry_operation_enabled",
        ]:
            self.assertFalse(selection_pack["safety_boundaries"][boundary])
        feedback_pack = variant_pack["creative_test_feedback_pack"]
        self.assertEqual(
            feedback_pack["pack_version"],
            "creative_test_feedback_pack_v1",
        )
        variant_ids = {variant["variant_id"] for variant in variant_pack["variants"]}
        self.assertIn(feedback_pack["recommended_winner_variant_id"], variant_ids)
        self.assertGreaterEqual(len(feedback_pack["variant_feedback_cards"]), 3)
        for card in feedback_pack["variant_feedback_cards"]:
            with self.subTest(feedback_id=card["feedback_id"]):
                self.assertIn(card["variant_id"], variant_ids)
                for field in [
                    "performance_tier",
                    "keep_or_change",
                    "what_worked",
                    "what_to_improve",
                    "recommended_next_action",
                ]:
                    self.assertTrue(card[field], field)
        action_types = {
            action["action_type"] for action in feedback_pack["iteration_actions"]
        }
        self.assertTrue({"keep_winner", "revise_hook", "revise_cta"}.issubset(action_types))
        next_iteration = feedback_pack["recommended_next_iteration"]
        for field in [
            "hook_direction",
            "scene_direction",
            "cta_direction",
            "proof_quote_direction",
        ]:
            self.assertTrue(next_iteration[field], field)
        for field in [
            "missing_metric",
            "weak_evidence",
            "unsupported_claim",
            "unsafe_provider_action",
        ]:
            self.assertIn(field, feedback_pack["feedback_quality_checks"])
        for boundary in [
            "provider_enabled",
            "llm_api_enabled",
            "video_generation_enabled",
            "media_operation_enabled",
            "paid_operation_enabled",
            "registry_operation_enabled",
        ]:
            self.assertFalse(feedback_pack["safety_boundaries"][boundary])
        iteration_pack = pack["creative_iteration_pack"]
        self.assertEqual(iteration_pack["pack_version"], "creative_iteration_pack_v1")
        self.assertIn(iteration_pack["source_winner_variant_id"], variant_ids)
        self.assertTrue(iteration_pack["recommended_iteration_variant_id"])
        self.assertGreaterEqual(len(iteration_pack["iteration_variants"]), 3)
        for iteration_variant in iteration_pack["iteration_variants"]:
            with self.subTest(
                iteration_variant_id=iteration_variant["iteration_variant_id"]
            ):
                for field in [
                    "revised_hook",
                    "revised_scene_1",
                    "revised_scene_2",
                    "revised_scene_3",
                    "revised_cta",
                    "revised_video_prompt",
                    "revised_risk_note",
                ]:
                    self.assertTrue(iteration_variant[field], field)
                self.assertEqual(len(iteration_variant["revised_shot_list"]), 3)
                self.assertTrue(iteration_variant["revised_do_not_claim"])
                script = iteration_variant["copy_ready_v2_script"]
                for label in [
                    "Hook:",
                    "Scene 1:",
                    "Scene 2:",
                    "Scene 3:",
                    "CTA:",
                    "Proof quote:",
                    "Risk note:",
                    "Do not claim:",
                ]:
                    self.assertIn(label, script)
        self.assertTrue(iteration_pack["original_vs_revised_diff"])
        self.assertTrue(
            any(
                diff["field_name"] in {"hook", "cta", "scene_1", "scene_2", "scene_3"}
                for diff in iteration_pack["original_vs_revised_diff"]
            )
        )
        self.assertTrue(iteration_pack["iteration_quality_checks"])
        for boundary in [
            "provider_enabled",
            "llm_api_enabled",
            "video_generation_enabled",
            "media_operation_enabled",
            "paid_operation_enabled",
            "registry_operation_enabled",
        ]:
            self.assertFalse(iteration_pack["safety_boundaries"][boundary])
        version_pack = pack["creative_version_control_pack"]
        self.assertEqual(
            version_pack["pack_version"],
            "creative_version_control_pack_v1",
        )
        lineage = version_pack["version_lineage"]
        self.assertTrue(lineage)
        self.assertEqual({1, 2}, {version["version_round"] for version in lineage})
        lineage_ids = {version["version_id"] for version in lineage}
        self.assertIn(
            version_pack["recommended_next_test_version_id"],
            lineage_ids,
        )
        for version in lineage:
            with self.subTest(version_id=version["version_id"]):
                for field in [
                    "variant_type",
                    "hook",
                    "scene_1",
                    "scene_2",
                    "scene_3",
                    "cta",
                    "risk_note",
                    "copy_ready_script",
                ]:
                    self.assertTrue(version[field], field)
                self.assertTrue(version["proof_quote"] or version["missing_quote"])
                self.assertTrue(version["do_not_claim"])
                if version["version_round"] == 2:
                    self.assertIn(version["parent_version_id"], lineage_ids)
        comparisons = version_pack["version_comparison_cards"]
        self.assertGreaterEqual(len(comparisons), 1)
        for comparison in comparisons:
            with self.subTest(comparison_id=comparison["comparison_id"]):
                self.assertIn(comparison["base_version_id"], lineage_ids)
                self.assertIn(comparison["revised_version_id"], lineage_ids)
                for field in [
                    "comparison_title",
                    "what_changed",
                    "why_it_changed",
                    "expected_benefit",
                    "risk_delta",
                    "evidence_delta",
                    "copy_readiness_delta",
                    "best_for",
                    "recommended_next_action",
                    "risk_note",
                ]:
                    self.assertTrue(comparison[field], field)
                self.assertTrue(
                    comparison["proof_quote"] or comparison["missing_quote"]
                )
                self.assertTrue(comparison["do_not_claim"])
        risk_summary = version_pack["version_risk_summary"]
        for field in [
            "lowest_risk_version_id",
            "highest_readiness_version_id",
            "best_tiktok_version_id",
            "best_direct_response_version_id",
            "low_evidence_safe_version_id",
            "highest_copy_readiness_version_id",
            "best_for_tiktok_version_id",
            "best_for_direct_response_version_id",
            "best_for_low_evidence_safe_use_version_id",
        ]:
            self.assertIn(risk_summary[field], lineage_ids)
        self.assertTrue(version_pack["version_export_snapshot"])
        self.assertTrue(
            version_pack["version_quality_checks"]["lineage_complete"]
        )
        self.assertTrue(
            version_pack["version_quality_checks"]["recommended_version_exists"]
        )
        self.assertTrue(
            version_pack["version_quality_checks"]["do_not_claim_preserved"]
        )
        self.assertFalse(
            version_pack["version_quality_checks"]["unsupported_claim_added"]
        )
        self.assertTrue(
            all(value is False for value in version_pack["safety_boundaries"].values())
        )
        asset_pack = pack["creative_asset_pack"]
        self.assertEqual(asset_pack["pack_version"], "creative_asset_pack_v1")
        self.assertIn(asset_pack["source_version_id"], lineage_ids)
        self.assertTrue(asset_pack["recommended_asset_pack_id"])
        self.assertGreaterEqual(len(asset_pack["asset_packs"]), 1)
        recommended_asset = next(
            item
            for item in asset_pack["asset_packs"]
            if item["asset_pack_id"] == asset_pack["recommended_asset_pack_id"]
        )
        for field in [
            "source_version_id",
            "source_version_label",
            "asset_pack_title",
            "target_platform",
            "target_format",
            "target_length_seconds",
            "shooting_script",
            "shot_list",
            "keyframe_prompts",
            "subtitle_lines",
            "b_roll_notes",
            "thumbnail_prompt",
            "caption_variants",
            "on_screen_text",
            "voiceover_script",
            "product_context",
            "risk_notes",
            "do_not_claim",
            "asset_readiness",
            "evidence_strength_score",
            "recommended_next_action",
        ]:
            self.assertTrue(recommended_asset[field], field)
        shooting_script = recommended_asset["shooting_script"]
        for field in [
            "hook",
            "scene_1",
            "scene_2",
            "scene_3",
            "cta",
            "risk_note",
            "do_not_claim",
        ]:
            self.assertTrue(shooting_script[field], field)
        self.assertTrue(
            shooting_script["proof_quote"] or shooting_script["missing_quote"]
        )
        self.assertGreaterEqual(len(recommended_asset["keyframe_prompts"]), 3)
        for keyframe in recommended_asset["keyframe_prompts"]:
            self.assertTrue(keyframe["prompt"])
            self.assertTrue(keyframe["visual_style"])
            self.assertTrue(keyframe["evidence_link"])
            self.assertTrue(keyframe["do_not_claim"])
        self.assertGreaterEqual(len(recommended_asset["subtitle_lines"]), 3)
        self.assertEqual(
            {
                "short_caption",
                "benefit_caption",
                "proof_caption",
                "safe_claim_caption",
            },
            set(recommended_asset["caption_variants"]),
        )
        self.assertFalse(asset_pack["asset_quality_checks"]["unsupported_claim"])
        self.assertFalse(asset_pack["asset_quality_checks"]["unsafe_provider_action"])
        self.assertTrue(
            asset_pack["asset_quality_checks"]["do_not_claim_preserved"]
        )
        self.assertTrue(
            all(value is False for value in asset_pack["safety_boundaries"].values())
        )
        multi_platform_pack = pack["multi_platform_asset_pack"]
        self.assertEqual(
            multi_platform_pack["pack_version"],
            "multi_platform_asset_pack_v1",
        )
        self.assertIn(
            multi_platform_pack["source_asset_pack_id"],
            {item["asset_pack_id"] for item in asset_pack["asset_packs"]},
        )
        self.assertTrue(multi_platform_pack["recommended_platform_pack_id"])
        platform_packs = multi_platform_pack["platform_packs"]
        self.assertGreaterEqual(len(platform_packs), 9)
        self.assertEqual(
            {"tiktok", "instagram_reels", "youtube_shorts"},
            {item["platform"] for item in platform_packs},
        )
        self.assertEqual(
            {15, 30, 45},
            {item["duration_seconds"] for item in platform_packs},
        )
        for platform_pack in platform_packs:
            with self.subTest(platform_pack_id=platform_pack["platform_pack_id"]):
                for field in [
                    "opening_hook",
                    "shooting_script",
                    "shot_list",
                    "keyframe_prompts",
                    "subtitle_lines",
                    "caption_variants",
                    "thumbnail_prompt",
                    "do_not_claim",
                ]:
                    self.assertTrue(platform_pack[field], field)
                self.assertEqual(
                    platform_pack["proof_quotes"],
                    recommended_asset["proof_quotes"],
                )
                self.assertTrue(
                    set(recommended_asset["do_not_claim"]).issubset(
                        set(platform_pack["do_not_claim"])
                    )
                )
        tiktok_15 = next(
            item
            for item in platform_packs
            if item["platform"] == "tiktok"
            and item["duration_seconds"] == 15
        )
        self.assertLessEqual(len(tiktok_15["shooting_script"]["scenes"]), 2)
        self.assertIn("Fast pacing", tiktok_15["pacing_strategy"])
        for long_pack in [
            item for item in platform_packs if item["duration_seconds"] == 45
        ]:
            self.assertEqual(long_pack["proof_quotes"], recommended_asset["proof_quotes"])
            self.assertTrue(
                set(recommended_asset["do_not_claim"]).issubset(
                    set(long_pack["do_not_claim"])
                )
            )
        quality = multi_platform_pack["platform_quality_checks"]
        self.assertFalse(quality["unsupported_claim"])
        self.assertFalse(quality["unsafe_provider_action"])
        self.assertFalse(quality["missing_platform_variant"])
        self.assertFalse(quality["missing_duration_variant"])
        self.assertTrue(quality["do_not_claim_preserved"])
        self.assertTrue(
            all(
                value is False
                for value in multi_platform_pack["safety_boundaries"].values()
            )
        )
        quality_gate = pack["asset_quality_gate_pack"]
        self.assertEqual(
            quality_gate["pack_version"],
            "asset_quality_gate_pack_v1",
        )
        self.assertTrue(quality_gate["recommended_ready_pack_id"])
        quality_cards = quality_gate["quality_cards"]
        self.assertGreaterEqual(len(quality_cards), 9)
        self.assertEqual(
            {"tiktok", "instagram_reels", "youtube_shorts"},
            {card["platform"] for card in quality_cards},
        )
        self.assertEqual(
            {15, 30, 45},
            {card["duration_seconds"] for card in quality_cards},
        )
        for card in quality_cards:
            with self.subTest(quality_card_id=card["quality_card_id"]):
                for score_name in [
                    "overall_quality_score",
                    "completeness_score",
                    "script_readiness_score",
                    "video_prompt_readiness_score",
                    "evidence_coverage_score",
                    "safety_score",
                ]:
                    self.assertGreaterEqual(card[score_name], 0)
                    self.assertLessEqual(card[score_name], 100)
                self.assertTrue(card["delivery_readiness"])
                self.assertTrue(card["quality_tier"])
                self.assertIsInstance(card["missing_items"], list)
                self.assertIsInstance(card["risk_items"], list)
                self.assertIsInstance(card["fix_recommendations"], list)
        self.assertEqual(
            1,
            sum(card["is_recommended_ready_pack"] for card in quality_cards),
        )
        self.assertIsInstance(quality_gate["missing_asset_checklist"], list)
        self.assertIsInstance(quality_gate["recommended_fix_actions"], list)
        self.assertTrue(quality_gate["quality_export_snapshot"])
        self.assertFalse(quality_gate["quality_checks"]["unsupported_claim"])
        self.assertFalse(quality_gate["quality_checks"]["unsafe_provider_action"])
        self.assertTrue(
            all(
                value is False
                for value in quality_gate["safety_boundaries"].values()
            )
        )
        campaign = pack["campaign_export_pack"]
        self.assertEqual(
            campaign["pack_version"],
            "campaign_export_pack_v1",
        )
        self.assertTrue(campaign["recommended_campaign_id"])
        campaign_summary = campaign["campaign_summary"]
        for field in [
            "recommended_version_id",
            "recommended_platform_pack_id",
            "recommended_ready_pack_id",
        ]:
            self.assertTrue(campaign_summary[field], field)

        campaign_brief = campaign["campaign_brief"]
        for field in [
            "buyer_pain",
            "buyer_objection",
            "creative_angle",
            "proof_quote",
            "risk_note",
            "do_not_claim",
        ]:
            self.assertIn(field, campaign_brief)
        self.assertTrue(campaign_brief["creative_angle"])
        self.assertTrue(campaign_brief["proof_quote"])
        self.assertTrue(campaign_brief["risk_note"])
        self.assertTrue(campaign_brief["do_not_claim"])

        evidence_section = campaign["evidence_section"]
        for field in [
            "proof_quotes",
            "evidence_warnings",
            "source_breakdown_summary",
        ]:
            self.assertIn(field, evidence_section)
        self.assertTrue(evidence_section["proof_quotes"])
        self.assertTrue(evidence_section["source_breakdown_summary"])

        creative_section = campaign["creative_section"]
        for field in [
            "copy_ready_script",
            "recommended_hook",
            "scene_1",
            "scene_2",
            "scene_3",
            "cta",
        ]:
            self.assertTrue(creative_section[field], field)

        platform_assets = campaign["platform_assets_section"]
        for field in [
            "shooting_script",
            "shot_list",
            "keyframe_prompts",
            "subtitle_lines",
            "caption_variants",
            "thumbnail_prompt",
        ]:
            self.assertTrue(platform_assets[field], field)

        quality_section = campaign["quality_gate_section"]
        self.assertEqual(
            quality_section["recommended_ready_pack_id"],
            quality_gate["recommended_ready_pack_id"],
        )
        recommended_quality_card = next(
            card
            for card in quality_cards
            if card["platform_pack_id"]
            == quality_gate["recommended_ready_pack_id"]
        )
        self.assertEqual(
            quality_section["overall_quality_score"],
            recommended_quality_card["overall_quality_score"],
        )
        self.assertEqual(
            quality_section["fix_recommendations"],
            recommended_quality_card["fix_recommendations"],
        )

        test_plan = campaign["test_plan_section"]
        for field in [
            "ab_test_hypothesis",
            "primary_metric",
            "safe_launch_note",
        ]:
            self.assertTrue(test_plan[field], field)
        self.assertTrue(campaign["safety_section"]["disabled_real_operations"])

        export_manifest = campaign["export_manifest"]
        self.assertTrue(export_manifest["included_sections"])
        self.assertTrue(export_manifest["markdown_export_ready"])
        self.assertTrue(export_manifest["json_export_ready"])
        self.assertTrue(campaign["campaign_quality_checks"])
        for boundary in [
            "provider_enabled",
            "llm_api_enabled",
            "video_generation_enabled",
            "media_operation_enabled",
            "paid_operation_enabled",
            "registry_operation_enabled",
        ]:
            self.assertFalse(campaign["safety_boundaries"][boundary])

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
        variant_pack = pack["creative_variant_pack"]
        self.assertEqual(len(variant_pack["variants"]), 5)
        self.assertFalse(variant_pack["recommended_variant_id"])
        self.assertTrue(variant_pack["variant_quality_checks"]["weak_evidence"])
        self.assertTrue(all(variant["weak_evidence"] for variant in variant_pack["variants"]))
        selection_pack = variant_pack["variant_selection_pack"]
        self.assertTrue(selection_pack["recommended_first_variant_id"])
        recommended_card = next(
            card
            for card in selection_pack["selection_cards"]
            if card["variant_id"] == selection_pack["recommended_first_variant_id"]
        )
        self.assertEqual(recommended_card["best_for"], "best_for_low_evidence_safe_use")
        self.assertEqual(recommended_card["claim_safety_level"], "conservative")
        self.assertNotEqual(recommended_card["copy_readiness"], "ready")
        self.assertTrue(selection_pack["selection_quality_checks"]["weak_evidence"])
        self.assertFalse(
            selection_pack["selection_quality_checks"][
                "high_claim_safety_recommended_without_quote"
            ]
        )
        feedback_pack = variant_pack["creative_test_feedback_pack"]
        action_types = {
            action["action_type"] for action in feedback_pack["iteration_actions"]
        }
        self.assertTrue(
            {"lower_claim_strength", "collect_more_reviews"}.intersection(action_types)
        )
        self.assertTrue(feedback_pack["feedback_quality_checks"]["weak_evidence"])
        self.assertTrue(
            all(
                card["recommended_next_action"]
                in {"lower_claim_strength", "collect_more_reviews"}
                for card in feedback_pack["variant_feedback_cards"]
            )
        )
        self.assertFalse(
            any(
                card["claim_safety_level"] == "evidence_grounded"
                for card in selection_pack["selection_cards"]
            )
        )
        iteration_pack = pack["creative_iteration_pack"]
        self.assertTrue(iteration_pack["iteration_quality_checks"]["weak_evidence"])
        self.assertTrue(
            all(
                variant["claim_safety_level"] == "conservative"
                for variant in iteration_pack["iteration_variants"]
            )
        )
        self.assertTrue(
            all(
                variant["copy_readiness"] == "needs_evidence"
                for variant in iteration_pack["iteration_variants"]
            )
        )
        self.assertTrue(
            all(
                variant["recommended_next_action"]
                in {"collect_more_reviews", "lower_claim_strength"}
                for variant in iteration_pack["iteration_variants"]
            )
        )
        version_pack = pack["creative_version_control_pack"]
        lineage = version_pack["version_lineage"]
        lineage_ids = {version["version_id"] for version in lineage}
        self.assertIn(
            version_pack["recommended_next_test_version_id"],
            lineage_ids,
        )
        v2_versions = [
            version for version in lineage if version["version_round"] == 2
        ]
        self.assertTrue(v2_versions)
        self.assertTrue(
            all(version["claim_safety_level"] == "conservative" for version in v2_versions)
        )
        self.assertTrue(all(version["weak_evidence"] for version in v2_versions))
        self.assertTrue(
            all(
                comparison["recommended_next_action"]
                in {"collect_more_reviews", "lower_claim_strength"}
                for comparison in version_pack["version_comparison_cards"]
            )
        )
        self.assertTrue(version_pack["version_quality_checks"]["weak_evidence"])
        self.assertFalse(
            version_pack["version_quality_checks"]["unsupported_claim_added"]
        )
        self.assertTrue(
            all(value is False for value in version_pack["safety_boundaries"].values())
        )
        asset_pack = pack["creative_asset_pack"]
        self.assertIn(asset_pack["source_version_id"], lineage_ids)
        self.assertTrue(asset_pack["asset_packs"])
        recommended_asset = asset_pack["asset_packs"][0]
        self.assertEqual(recommended_asset["asset_readiness"], "needs_evidence")
        self.assertIn(
            recommended_asset["recommended_next_action"],
            {"collect_more_reviews", "lower_claim_strength"},
        )
        self.assertEqual(
            recommended_asset["proof_quotes"],
            ["The light feels too harsh late at night"],
        )
        self.assertFalse(asset_pack["asset_quality_checks"]["missing_quote"])
        self.assertTrue(asset_pack["asset_quality_checks"]["weak_evidence"])
        self.assertFalse(asset_pack["asset_quality_checks"]["unsupported_claim"])
        self.assertTrue(
            all(value is False for value in asset_pack["safety_boundaries"].values())
        )
        multi_platform_pack = pack["multi_platform_asset_pack"]
        self.assertEqual(len(multi_platform_pack["platform_packs"]), 9)
        self.assertTrue(
            all(
                item["asset_readiness"] == "needs_evidence"
                for item in multi_platform_pack["platform_packs"]
            )
        )
        self.assertTrue(
            all(
                item["claim_safety_level"] == "conservative"
                for item in multi_platform_pack["platform_packs"]
            )
        )
        self.assertTrue(
            all(
                item["recommended_next_action"]
                in {"collect_more_reviews", "lower_claim_strength"}
                for item in multi_platform_pack["platform_packs"]
            )
        )
        self.assertTrue(
            multi_platform_pack["platform_quality_checks"]["weak_evidence"]
        )
        self.assertFalse(
            multi_platform_pack["platform_quality_checks"]["unsupported_claim"]
        )
        self.assertTrue(
            all(
                value is False
                for value in multi_platform_pack["safety_boundaries"].values()
            )
        )
        quality_gate = pack["asset_quality_gate_pack"]
        self.assertFalse(quality_gate["recommended_ready_pack_id"])
        self.assertTrue(quality_gate["quality_checks"]["weak_evidence"])
        self.assertTrue(
            quality_gate["quality_checks"]["low_evidence_marked_not_ready"]
        )
        self.assertTrue(
            all(
                card["delivery_readiness"] != "ready_for_human_review"
                for card in quality_gate["quality_cards"]
            )
        )
        self.assertTrue(
            all(
                card["safety_score"] <= 60
                for card in quality_gate["quality_cards"]
            )
        )
        self.assertTrue(
            {
                "strengthen_proof_quote",
                "lower_claim_strength",
            }.intersection(
                {
                    action["action_type"]
                    for action in quality_gate["recommended_fix_actions"]
                }
            )
        )
        self.assertTrue(
            all(
                value is False
                for value in quality_gate["safety_boundaries"].values()
            )
        )
        campaign = pack["campaign_export_pack"]
        self.assertNotEqual(
            campaign["campaign_summary"]["campaign_readiness"],
            "ready_to_launch",
        )
        self.assertTrue(campaign["campaign_quality_checks"]["weak_evidence"])
        self.assertTrue(
            campaign["campaign_quality_checks"][
                "ready_to_launch_requires_strong_evidence"
            ]
        )
        self.assertTrue(campaign["safety_section"]["disabled_real_operations"])
        for boundary in [
            "provider_enabled",
            "llm_api_enabled",
            "video_generation_enabled",
            "media_operation_enabled",
            "paid_operation_enabled",
            "registry_operation_enabled",
        ]:
            self.assertFalse(campaign["safety_boundaries"][boundary])
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
