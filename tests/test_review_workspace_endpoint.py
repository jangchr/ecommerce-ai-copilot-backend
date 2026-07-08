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

    def test_llm_assist_dry_run_pack_is_evidence_bound_and_never_executes(self):
        payload = {
            "workspace_id": "llm-assist-dry-run",
            "source": "manual_import",
            "output_language": "en",
            "products": [
                {
                    "platform": "amazon",
                    "title": "Own Travel Bottle",
                    "reviews": [
                        {
                            "rating": 2,
                            "title": "Leaked in a bag",
                            "text": "The lid leaked in my backpack during a commute and was difficult to clean after coffee.",
                            "source_section": "amazon_visible_review",
                        },
                        {
                            "rating": 5,
                            "title": "Useful for travel",
                            "text": "I use this bottle for travel because it feels sturdy and is easy to rinse after lunch.",
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
                            "title": "Competitor lid",
                            "text": "The competitor lid is tight and the bottle leaked in my backpack.",
                            "source_section": "competitor_review",
                        }
                    ],
                },
            ],
        }

        response = self.client.post("/api/v1/analyze-review-workspace", json=payload)

        self.assertEqual(response.status_code, 200)
        creative_pack = response.json()["creative_decision_pack"]
        self.assertIn("review_import_pack", creative_pack)
        self.assertIn("competitor_review_comparison_pack", creative_pack)
        self.assertIn("llm_assist_dry_run_pack", creative_pack)
        pack = creative_pack["llm_assist_dry_run_pack"]
        self.assertEqual(pack["pack_version"], "llm_assist_dry_run_pack_v1")
        self.assertIn("dry_run", pack["dry_run_summary"]["mode"])
        self.assertEqual(pack["dry_run_summary"]["real_call_status"], "disabled")
        self.assertEqual(pack["prompt_plan"]["prompt_type"], "evidence_bound_dry_run")
        self.assertIn(
            "EVIDENCE-BOUND LLM ASSIST DRY-RUN PROMPT",
            pack["prompt_plan"]["user_prompt_preview"],
        )
        self.assertTrue(pack["evidence_bundle"])
        self.assertTrue(pack["evidence_bundle"]["evidence_brief"])
        self.assertIn("allowed_claims", pack)
        self.assertTrue(pack["do_not_claim"])
        self.assertFalse(pack["mock_llm_response"]["is_real_llm_output"])
        self.assertEqual(
            pack["mock_llm_response"]["response_type"],
            "deterministic_placeholder",
        )
        self.assertIn("No real LLM", pack["mock_llm_response"]["message"])
        self.assertTrue(pack["approval_gate"]["approval_required"])
        self.assertFalse(pack["approval_gate"]["real_llm_call_allowed"])
        self.assertFalse(pack["approval_gate"]["provider_call_allowed"])
        self.assertFalse(pack["output_contract"]["high_confidence_allowed"])
        self.assertTrue(pack["risk_checks"])

        boundaries = pack["safety_boundaries"]
        for key in [
            "provider_calls_enabled",
            "llm_api_enabled",
            "api_key_or_secret_read_enabled",
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

    def test_llm_assist_dry_run_pack_lowers_readiness_without_quotes(self):
        response = self.client.post(
            "/api/v1/analyze-review-workspace",
            json={"workspace_id": "llm-dry-run-empty", "products": []},
        )

        self.assertEqual(response.status_code, 200)
        creative_pack = response.json()["creative_decision_pack"]
        pack = creative_pack["llm_assist_dry_run_pack"]
        self.assertNotEqual(pack["dry_run_summary"]["readiness"], "ready_to_call")
        self.assertIn(
            pack["dry_run_summary"]["readiness"],
            {"needs_stronger_evidence", "needs_evidence_quotes"},
        )
        self.assertTrue(pack["dry_run_summary"]["weak_evidence"])
        self.assertTrue(pack["dry_run_summary"]["missing_quotes"])
        self.assertFalse(pack["output_contract"]["high_confidence_allowed"])
        self.assertFalse(pack["approval_gate"]["real_llm_call_allowed"])
        self.assertEqual(pack["mock_llm_response"]["status"], "not_executed")

    def test_video_provider_orchestration_dry_run_pack_never_executes(self):
        payload = {
            "workspace_id": "video-provider-orchestration-dry-run",
            "source": "manual_import",
            "output_language": "en",
            "products": [
                {
                    "platform": "amazon",
                    "title": "Travel Bottle",
                    "reviews": [
                        {
                            "rating": 2,
                            "title": "Leaked during commute",
                            "text": "The lid leaked in my backpack during a commute and was difficult to clean after coffee.",
                            "source_section": "amazon_visible_review",
                        },
                        {
                            "rating": 5,
                            "title": "Easy travel cleanup",
                            "text": "I use it for travel because it feels sturdy and is easy to rinse after lunch.",
                            "source_section": "manual_review",
                        },
                    ],
                }
            ],
        }

        response = self.client.post("/api/v1/analyze-review-workspace", json=payload)

        self.assertEqual(response.status_code, 200)
        creative_pack = response.json()["creative_decision_pack"]
        for existing_pack in [
            "review_import_pack",
            "competitor_review_comparison_pack",
            "llm_assist_dry_run_pack",
            "video_provider_orchestration_dry_run_pack",
        ]:
            with self.subTest(existing_pack=existing_pack):
                self.assertIn(existing_pack, creative_pack)
        pack = creative_pack["video_provider_orchestration_dry_run_pack"]
        self.assertEqual(
            pack["pack_version"],
            "video_provider_orchestration_dry_run_pack_v1",
        )
        self.assertIn("dry_run", pack["dry_run_summary"]["mode"])
        self.assertEqual(pack["dry_run_summary"]["real_call_status"], "disabled")
        self.assertTrue(pack["video_job_plan"])
        self.assertFalse(pack["video_job_plan"]["job_execution_performed"])
        self.assertTrue(pack["provider_capability_plan"])
        self.assertFalse(pack["provider_capability_plan"]["provider_catalog_queried"])
        self.assertFalse(pack["provider_capability_plan"]["provider_call_performed"])
        self.assertTrue(pack["input_asset_bundle"])
        self.assertIn("input_validation", pack["input_asset_bundle"])
        self.assertTrue(pack["platform_delivery_specs"])

        cost = pack["cost_estimate_placeholder"]
        self.assertEqual(cost["estimate_type"], "deterministic_placeholder")
        self.assertFalse(cost["is_real_quote"])
        self.assertFalse(cost["provider_pricing_queried"])
        self.assertIn("not a real quote", cost["message"])
        mock = pack["mock_provider_response"]
        self.assertEqual(mock["response_type"], "deterministic_placeholder")
        self.assertFalse(mock["is_real_provider_output"])
        self.assertFalse(mock["provider_called"])
        self.assertFalse(mock["video_generated"])
        self.assertIn("No real video provider", mock["message"])

        self.assertTrue(pack["approval_gate"]["approval_required"])
        self.assertFalse(pack["approval_gate"]["real_video_call_allowed"])
        self.assertFalse(pack["approval_gate"]["provider_call_allowed"])
        self.assertFalse(pack["approval_gate"]["paid_operation_allowed"])
        self.assertEqual(pack["abort_plan"]["plan_mode"], "dry_run_only")
        self.assertFalse(pack["abort_plan"]["abort_executed"])
        self.assertEqual(pack["rollback_plan"]["plan_mode"], "dry_run_only")
        self.assertFalse(pack["rollback_plan"]["rollback_executed"])
        self.assertTrue(pack["risk_checks"])

        boundaries = pack["safety_boundaries"]
        for key in [
            "provider_calls_enabled",
            "llm_api_enabled",
            "api_key_or_secret_read_enabled",
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

    def test_video_provider_dry_run_blocks_ready_to_run_without_prompt(self):
        response = self.client.post(
            "/api/v1/analyze-review-workspace",
            json={"workspace_id": "video-provider-dry-run-empty", "products": []},
        )

        self.assertEqual(response.status_code, 200)
        pack = response.json()["creative_decision_pack"][
            "video_provider_orchestration_dry_run_pack"
        ]
        summary = pack["dry_run_summary"]
        self.assertNotEqual(summary["readiness"], "ready_to_run")
        self.assertIn(
            summary["readiness"],
            {"needs_stronger_evidence", "needs_video_prompt"},
        )
        self.assertTrue(summary["weak_evidence"])
        self.assertTrue(summary["missing_video_prompt"])
        self.assertFalse(pack["approval_gate"]["real_video_call_allowed"])
        self.assertFalse(pack["mock_provider_response"]["is_real_provider_output"])
        self.assertEqual(pack["abort_plan"]["plan_mode"], "dry_run_only")
        self.assertEqual(pack["rollback_plan"]["plan_mode"], "dry_run_only")

    def test_workspace_session_snapshot_pack_is_stable_and_never_persists(self):
        payload = {
            "workspace_id": "workspace-session-snapshot",
            "source": "manual_import",
            "output_language": "en",
            "products": [
                {
                    "platform": "amazon",
                    "asin": "SNAP001",
                    "title": "Snapshot Travel Bottle",
                    "reviews": [
                        {
                            "rating": 2,
                            "title": "Leaked during commute",
                            "text": "The lid leaked in my backpack during a commute and was difficult to clean after coffee.",
                            "source_section": "amazon_visible_review",
                        },
                        {
                            "rating": 5,
                            "title": "Easy travel cleanup",
                            "text": "I use it for travel because it feels sturdy and is easy to rinse after lunch.",
                            "source_section": "manual_review",
                        },
                    ],
                }
            ],
        }

        first_response = self.client.post(
            "/api/v1/analyze-review-workspace",
            json=payload,
        )
        second_response = self.client.post(
            "/api/v1/analyze-review-workspace",
            json=payload,
        )

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        creative_pack = first_response.json()["creative_decision_pack"]
        second_creative_pack = second_response.json()["creative_decision_pack"]
        for existing_pack in [
            "review_import_pack",
            "competitor_review_comparison_pack",
            "llm_assist_dry_run_pack",
            "video_provider_orchestration_dry_run_pack",
            "campaign_export_pack",
            "workspace_session_snapshot_pack",
        ]:
            with self.subTest(existing_pack=existing_pack):
                self.assertIn(existing_pack, creative_pack)

        pack = creative_pack["workspace_session_snapshot_pack"]
        second_pack = second_creative_pack["workspace_session_snapshot_pack"]
        self.assertEqual(
            pack["pack_version"],
            "workspace_session_snapshot_pack_v1",
        )
        run_identity = pack["run_identity"]
        self.assertTrue(run_identity["run_id"])
        self.assertTrue(run_identity["run_id"].startswith("wsrun_"))
        self.assertEqual(
            run_identity["run_id"],
            second_pack["run_identity"]["run_id"],
        )
        self.assertTrue(run_identity["stable_for_same_input"])
        self.assertFalse(run_identity["timestamp_included_in_identity"])
        self.assertTrue(pack["input_source_summary"])
        self.assertEqual(pack["input_source_summary"]["product_count"], 1)
        self.assertEqual(pack["input_source_summary"]["raw_review_count"], 2)

        inventory = {
            item["pack_name"]: item
            for item in pack["pack_inventory"]
        }
        for pack_name in [
            "review_import_pack",
            "competitor_review_comparison_pack",
            "llm_assist_dry_run_pack",
            "video_provider_orchestration_dry_run_pack",
            "campaign_export_pack",
        ]:
            with self.subTest(inventory_pack=pack_name):
                self.assertIn(pack_name, inventory)
                self.assertTrue(inventory[pack_name]["present"])
                self.assertTrue(inventory[pack_name]["snapshot_included"])

        manifest = pack["export_manifest"]
        self.assertEqual(
            manifest["manifest_type"],
            "exportable_workspace_snapshot",
        )
        self.assertTrue(manifest["exportable_snapshot"])
        self.assertFalse(manifest["is_persisted_record"])
        self.assertFalse(manifest["database_write_performed"])
        self.assertFalse(manifest["history_write_performed"])
        self.assertIn("workspace_session_snapshot_pack", manifest["included_packs"])

        restore_plan = pack["restore_plan"]
        self.assertEqual(restore_plan["plan_mode"], "dry_run_preview")
        self.assertFalse(restore_plan["restore_executed"])
        self.assertFalse(restore_plan["restore_allowed"])
        history = pack["history_entry_preview"]
        self.assertTrue(history["preview_only"])
        self.assertFalse(history["history_written"])
        self.assertFalse(history["database_written"])
        self.assertTrue(pack["quality_checks"])
        self.assertTrue(pack["quality_checks"]["run_id_deterministic"])
        self.assertTrue(pack["risk_notes"])

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
            "user_account_read_enabled",
            "user_history_write_enabled",
        ]:
            with self.subTest(boundary=key):
                self.assertFalse(boundaries[key])

    def test_workspace_run_compare_pack_uses_safe_current_only_baseline(self):
        payload = {
            "workspace_id": "workspace-run-compare",
            "source": "manual_import",
            "output_language": "en",
            "products": [
                {
                    "platform": "amazon",
                    "asin": "COMPARE001",
                    "title": "Compare Travel Bottle",
                    "reviews": [
                        {
                            "rating": 2,
                            "title": "Leaked during commute",
                            "text": "The lid leaked in my backpack during a commute and was difficult to clean after coffee.",
                            "source_section": "amazon_visible_review",
                        },
                        {
                            "rating": 5,
                            "title": "Easy travel cleanup",
                            "text": "I use it for travel because it feels sturdy and is easy to rinse after lunch.",
                            "source_section": "manual_review",
                        },
                    ],
                }
            ],
        }

        response = self.client.post("/api/v1/analyze-review-workspace", json=payload)

        self.assertEqual(response.status_code, 200)
        creative_pack = response.json()["creative_decision_pack"]
        for existing_pack in [
            "review_import_pack",
            "competitor_review_comparison_pack",
            "llm_assist_dry_run_pack",
            "video_provider_orchestration_dry_run_pack",
            "campaign_export_pack",
            "workspace_session_snapshot_pack",
            "workspace_run_compare_pack",
        ]:
            with self.subTest(existing_pack=existing_pack):
                self.assertIn(existing_pack, creative_pack)

        pack = creative_pack["workspace_run_compare_pack"]
        self.assertEqual(pack["pack_version"], "workspace_run_compare_pack_v1")
        summary = pack["compare_summary"]
        self.assertTrue(summary)
        self.assertEqual(summary["comparison_mode"], "no_previous_snapshot")
        self.assertNotEqual(summary["comparison_mode"], "real_history_compare")
        self.assertFalse(summary["previous_snapshot_available"])
        self.assertFalse(summary["real_history_compare_performed"])
        self.assertTrue(pack["current_run_identity"]["run_id"])
        self.assertEqual(pack["previous_run_identity"]["status"], "not_provided")
        self.assertFalse(pack["previous_run_identity"]["available"])

        inventory = {
            item["pack_name"]: item
            for item in pack["pack_inventory_delta"]
        }
        for pack_name in [
            "review_import_pack",
            "competitor_review_comparison_pack",
            "llm_assist_dry_run_pack",
            "video_provider_orchestration_dry_run_pack",
            "workspace_session_snapshot_pack",
        ]:
            with self.subTest(inventory_pack=pack_name):
                self.assertIn(pack_name, inventory)
                self.assertTrue(inventory[pack_name]["current_present"])
                self.assertIsNone(inventory[pack_name]["previous_present"])
                self.assertEqual(inventory[pack_name]["delta_status"], "baseline_only")

        self.assertTrue(pack["input_delta"])
        self.assertTrue(pack["readiness_delta"])
        self.assertTrue(pack["risk_delta"])
        self.assertTrue(pack["export_delta"])
        self.assertTrue(pack["recommended_follow_up_actions"])
        self.assertTrue(pack["compare_quality_checks"])
        self.assertFalse(pack["compare_quality_checks"]["database_history_queried"])
        self.assertFalse(pack["compare_quality_checks"]["restore_executed"])

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
            "real_restore_enabled",
        ]:
            with self.subTest(boundary=key):
                self.assertFalse(boundaries[key])

        previous_snapshot = creative_pack["workspace_session_snapshot_pack"]
        compare_payload = {
            **payload,
            "previous_workspace_snapshot": previous_snapshot,
        }
        compare_response = self.client.post(
            "/api/v1/analyze-review-workspace",
            json=compare_payload,
        )
        self.assertEqual(compare_response.status_code, 200)
        compared_pack = compare_response.json()["creative_decision_pack"][
            "workspace_run_compare_pack"
        ]
        self.assertEqual(
            compared_pack["compare_summary"]["comparison_mode"],
            "provided_snapshot_compare_preview",
        )
        self.assertTrue(
            compared_pack["compare_summary"]["previous_snapshot_available"]
        )
        self.assertEqual(
            compared_pack["previous_run_identity"]["run_id"],
            previous_snapshot["run_identity"]["run_id"],
        )
        self.assertFalse(
            compared_pack["compare_quality_checks"]["database_history_queried"]
        )
        self.assertFalse(compared_pack["safety_boundaries"]["real_restore_enabled"])

    def test_workspace_action_queue_pack_is_deterministic_and_never_executes(self):
        payload = {
            "workspace_id": "workspace-action-queue",
            "source": "manual_import",
            "output_language": "en",
            "products": [
                {
                    "platform": "manual",
                    "asin": "QUEUE001",
                    "title": "Compact Travel Mug",
                    "reviews": [
                        {
                            "rating": 2,
                            "title": "Short review",
                            "text": "Leaks.",
                            "source_section": "manual_review",
                        }
                    ],
                }
            ],
        }

        response = self.client.post("/api/v1/analyze-review-workspace", json=payload)

        self.assertEqual(response.status_code, 200)
        creative_pack = response.json()["creative_decision_pack"]
        for existing_pack in [
            "review_import_pack",
            "competitor_review_comparison_pack",
            "llm_assist_dry_run_pack",
            "video_provider_orchestration_dry_run_pack",
            "campaign_export_pack",
            "workspace_session_snapshot_pack",
            "workspace_run_compare_pack",
            "workspace_action_queue_pack",
        ]:
            with self.subTest(existing_pack=existing_pack):
                self.assertIn(existing_pack, creative_pack)

        pack = creative_pack["workspace_action_queue_pack"]
        self.assertEqual(pack["pack_version"], "workspace_action_queue_pack_v1")
        self.assertTrue(pack["queue_summary"])
        self.assertEqual(
            pack["queue_summary"]["mode"],
            "deterministic_recommendation_queue",
        )
        self.assertFalse(pack["queue_summary"]["real_execution_allowed"])
        actions = pack["recommended_actions"]
        self.assertGreaterEqual(len(actions), 1)
        required_action_fields = [
            "action_id",
            "action_title",
            "action_type",
            "priority",
            "source_pack",
            "reason",
            "evidence_reference",
            "expected_user_value",
            "blocked_by",
            "requires_approval",
            "real_execution_allowed",
            "recommended_next_step",
            "risk_note",
            "do_not_claim",
        ]
        for action in actions:
            with self.subTest(action=action["action_id"]):
                for field in required_action_fields:
                    self.assertIn(field, action)
                self.assertTrue(action["action_id"])
                self.assertTrue(action["action_type"])
                self.assertTrue(action["priority"])
                self.assertTrue(action["source_pack"])
                self.assertTrue(action["reason"])
                self.assertTrue(action["requires_approval"])
                self.assertFalse(action["real_execution_allowed"])

        self.assertTrue(pack["blocked_actions"])
        self.assertTrue(
            pack["evidence_gap_actions"] or pack["safety_review_actions"]
        )
        self.assertTrue(pack["export_follow_up_actions"])
        export_types = {
            action["action_type"]
            for action in pack["export_follow_up_actions"]
        }
        self.assertIn("export_campaign_pack", export_types)
        self.assertIn("compare_run_snapshot", export_types)
        self.assertTrue(
            all(
                not action["real_execution_allowed"]
                for action in pack["ready_actions"]
            )
        )
        checks = pack["queue_quality_checks"]
        self.assertTrue(checks["actions_present"])
        self.assertTrue(checks["action_ids_unique"])
        self.assertTrue(checks["weak_evidence_routed_to_review"])
        self.assertTrue(checks["all_real_execution_disabled"])
        self.assertFalse(checks["queue_execution_performed"])
        self.assertFalse(checks["database_write_performed"])

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
            "real_restore_enabled",
            "real_execution_enabled",
        ]:
            with self.subTest(boundary=key):
                self.assertFalse(boundaries[key])

    def test_workspace_action_ticket_pack_is_traceable_and_never_executes(self):
        payload = {
            "workspace_id": "workspace-action-ticket",
            "source": "manual_import",
            "output_language": "en",
            "products": [
                {
                    "platform": "manual",
                    "asin": "TICKET001",
                    "title": "Compact Travel Mug",
                    "reviews": [
                        {
                            "rating": 2,
                            "title": "Too short",
                            "text": "Leaks.",
                            "source_section": "manual_review",
                        }
                    ],
                }
            ],
        }

        response = self.client.post("/api/v1/analyze-review-workspace", json=payload)

        self.assertEqual(response.status_code, 200)
        creative_pack = response.json()["creative_decision_pack"]
        for existing_pack in [
            "review_import_pack",
            "competitor_review_comparison_pack",
            "llm_assist_dry_run_pack",
            "video_provider_orchestration_dry_run_pack",
            "campaign_export_pack",
            "workspace_session_snapshot_pack",
            "workspace_run_compare_pack",
            "workspace_action_queue_pack",
            "workspace_action_ticket_pack",
        ]:
            with self.subTest(existing_pack=existing_pack):
                self.assertIn(existing_pack, creative_pack)

        pack = creative_pack["workspace_action_ticket_pack"]
        self.assertEqual(pack["pack_version"], "workspace_action_ticket_pack_v1")
        summary = pack["ticket_summary"]
        self.assertTrue(summary)
        self.assertEqual(
            summary["mode"],
            "deterministic_approval_packet_preview",
        )
        self.assertFalse(summary["real_execution_allowed"])
        self.assertEqual(summary["approved_to_execute_count"], 0)

        tickets = pack["action_tickets"]
        queue_actions = creative_pack["workspace_action_queue_pack"][
            "recommended_actions"
        ]
        self.assertGreaterEqual(len(tickets), 1)
        self.assertEqual(len(tickets), len(queue_actions))
        source_action_ids = {action["action_id"] for action in queue_actions}
        required_ticket_fields = [
            "ticket_id",
            "source_action_id",
            "ticket_title",
            "ticket_type",
            "priority",
            "source_pack",
            "approval_status",
            "requires_human_review",
            "real_execution_allowed",
            "preconditions",
            "validation_steps",
            "abort_conditions",
            "expected_user_value",
            "risk_note",
            "do_not_claim",
            "audit_note",
        ]
        for ticket in tickets:
            with self.subTest(ticket=ticket["ticket_id"]):
                for field in required_ticket_fields:
                    self.assertIn(field, ticket)
                self.assertTrue(ticket["ticket_id"])
                self.assertIn(ticket["source_action_id"], source_action_ids)
                self.assertTrue(ticket["ticket_type"])
                self.assertTrue(ticket["priority"])
                self.assertIn(
                    ticket["approval_status"],
                    {"pending_review", "review_required", "blocked"},
                )
                self.assertTrue(ticket["requires_human_review"])
                self.assertFalse(ticket["real_execution_allowed"])
                self.assertTrue(ticket["preconditions"])
                self.assertTrue(ticket["validation_steps"])
                self.assertTrue(ticket["abort_conditions"])

        ticket_types = {ticket["ticket_type"] for ticket in tickets}
        self.assertTrue(
            {"evidence_gap_ticket", "safety_review_ticket"}
            & ticket_types
        )
        self.assertTrue(pack["approval_checklist"])
        self.assertFalse(
            pack["approval_checklist"]["approved_to_execute_allowed"]
        )
        self.assertTrue(pack["pre_execution_requirements"])
        self.assertTrue(pack["validation_plan"])
        self.assertTrue(pack["abort_conditions"])
        self.assertTrue(pack["blocked_ticket_notes"])

        audit = pack["audit_trail_preview"]
        self.assertTrue(audit["preview_only"])
        self.assertFalse(audit["audit_record_written"])
        self.assertFalse(audit["database_write_performed"])
        self.assertFalse(audit["registry_write_performed"])
        self.assertFalse(audit["history_write_performed"])
        self.assertEqual(len(audit["entries"]), len(tickets))

        checks = pack["ticket_quality_checks"]
        self.assertTrue(checks["ticket_count_matches_source_actions"])
        self.assertTrue(checks["ticket_ids_unique"])
        self.assertTrue(checks["all_tickets_trace_to_source_action"])
        self.assertTrue(checks["all_tickets_require_human_review"])
        self.assertTrue(checks["all_real_execution_disabled"])
        self.assertTrue(checks["no_ticket_approved_to_execute"])
        self.assertTrue(checks["evidence_and_safety_actions_ticketed"])
        self.assertFalse(checks["database_write_performed"])
        self.assertFalse(checks["ticket_queue_persisted"])

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
            "real_restore_enabled",
            "real_execution_enabled",
        ]:
            with self.subTest(boundary=key):
                self.assertFalse(boundaries[key])

    def test_workspace_approval_decision_pack_is_gated_and_never_executes(self):
        payload = {
            "workspace_id": "workspace-approval-decision",
            "source": "manual_import",
            "output_language": "en",
            "products": [
                {
                    "platform": "manual",
                    "asin": "DECISION001",
                    "title": "Compact Travel Mug",
                    "reviews": [
                        {
                            "rating": 2,
                            "title": "Too short",
                            "text": "Leaks.",
                            "source_section": "manual_review",
                        }
                    ],
                }
            ],
        }

        response = self.client.post("/api/v1/analyze-review-workspace", json=payload)

        self.assertEqual(response.status_code, 200)
        creative_pack = response.json()["creative_decision_pack"]
        for existing_pack in [
            "review_import_pack",
            "competitor_review_comparison_pack",
            "llm_assist_dry_run_pack",
            "video_provider_orchestration_dry_run_pack",
            "campaign_export_pack",
            "workspace_session_snapshot_pack",
            "workspace_run_compare_pack",
            "workspace_action_queue_pack",
            "workspace_action_ticket_pack",
            "workspace_approval_decision_pack",
        ]:
            with self.subTest(existing_pack=existing_pack):
                self.assertIn(existing_pack, creative_pack)

        pack = creative_pack["workspace_approval_decision_pack"]
        self.assertEqual(
            pack["pack_version"],
            "workspace_approval_decision_pack_v1",
        )
        summary = pack["approval_summary"]
        self.assertTrue(summary)
        self.assertEqual(
            summary["mode"],
            "deterministic_approval_gate_preview",
        )
        self.assertEqual(summary["approved_for_real_execution_count"], 0)
        self.assertTrue(summary["human_review_required"])
        self.assertFalse(summary["real_execution_allowed"])

        decisions = pack["decision_ledger"]
        source_tickets = creative_pack["workspace_action_ticket_pack"][
            "action_tickets"
        ]
        self.assertGreaterEqual(len(decisions), 1)
        self.assertEqual(len(decisions), len(source_tickets))
        source_ticket_ids = {ticket["ticket_id"] for ticket in source_tickets}
        required_decision_fields = [
            "decision_id",
            "source_ticket_id",
            "decision_title",
            "decision_type",
            "priority",
            "source_pack",
            "ticket_approval_status",
            "gate_status",
            "decision_status",
            "human_review_required",
            "real_execution_allowed",
            "approval_reason",
            "blocking_reasons",
            "required_evidence",
            "validation_required",
            "risk_note",
            "do_not_claim",
            "audit_note",
        ]
        for decision in decisions:
            with self.subTest(decision=decision["decision_id"]):
                for field in required_decision_fields:
                    self.assertIn(field, decision)
                self.assertTrue(decision["decision_id"])
                self.assertIn(decision["source_ticket_id"], source_ticket_ids)
                self.assertTrue(decision["decision_type"])
                self.assertTrue(decision["gate_status"])
                self.assertIn(
                    decision["decision_status"],
                    {"pending_review", "blocked", "review_ready"},
                )
                self.assertTrue(decision["human_review_required"])
                self.assertFalse(decision["real_execution_allowed"])
                self.assertTrue(decision["required_evidence"])
                self.assertTrue(decision["validation_required"])

        self.assertIsInstance(pack["pending_decisions"], list)
        self.assertIsInstance(pack["blocked_decisions"], list)
        self.assertIsInstance(pack["review_ready_decisions"], list)
        self.assertTrue(pack["blocked_decisions"])
        self.assertTrue(pack["review_ready_decisions"])
        self.assertTrue(
            all(
                decision["gate_status"] == "ready_for_human_review"
                and not decision["real_execution_allowed"]
                for decision in pack["review_ready_decisions"]
            )
        )
        gated_types = {
            decision["decision_type"]
            for decision in pack["blocked_decisions"]
        }
        self.assertTrue(
            {"evidence_gap_decision", "safety_review_decision"}
            & gated_types
        )

        self.assertTrue(pack["human_review_requirements"])
        self.assertTrue(pack["gate_checks"])
        self.assertFalse(pack["gate_checks"]["gate_execution_performed"])
        audit = pack["decision_audit_preview"]
        self.assertTrue(audit["preview_only"])
        self.assertFalse(audit["decision_record_written"])
        self.assertFalse(audit["approval_record_written"])
        self.assertFalse(audit["database_write_performed"])
        self.assertFalse(audit["registry_write_performed"])
        self.assertFalse(audit["history_write_performed"])
        self.assertEqual(len(audit["entries"]), len(decisions))

        checks = pack["approval_quality_checks"]
        self.assertTrue(checks["decision_count_matches_source_tickets"])
        self.assertTrue(checks["decision_ids_unique"])
        self.assertTrue(checks["all_decisions_trace_to_source_ticket"])
        self.assertTrue(checks["all_decisions_require_human_review"])
        self.assertTrue(checks["all_real_execution_disabled"])
        self.assertTrue(checks["no_decision_approved_for_real_execution"])
        self.assertTrue(checks["evidence_and_safety_tickets_gated"])
        self.assertTrue(checks["blocked_tickets_remain_blocked"])
        self.assertFalse(checks["database_write_performed"])
        self.assertFalse(checks["decision_ledger_persisted"])

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
            "real_restore_enabled",
            "real_execution_enabled",
        ]:
            with self.subTest(boundary=key):
                self.assertFalse(boundaries[key])

    def test_workspace_execution_readiness_pack_keeps_launch_locked(self):
        payload = {
            "workspace_id": "workspace-execution-readiness",
            "source": "manual_import",
            "output_language": "en",
            "products": [
                {
                    "platform": "manual",
                    "asin": "READY001",
                    "title": "Compact Travel Mug",
                    "reviews": [
                        {
                            "rating": 2,
                            "title": "Too short",
                            "text": "Leaks.",
                            "source_section": "manual_review",
                        }
                    ],
                }
            ],
        }

        response = self.client.post("/api/v1/analyze-review-workspace", json=payload)

        self.assertEqual(response.status_code, 200)
        creative_pack = response.json()["creative_decision_pack"]
        for existing_pack in [
            "review_import_pack",
            "competitor_review_comparison_pack",
            "llm_assist_dry_run_pack",
            "video_provider_orchestration_dry_run_pack",
            "campaign_export_pack",
            "workspace_session_snapshot_pack",
            "workspace_run_compare_pack",
            "workspace_action_queue_pack",
            "workspace_action_ticket_pack",
            "workspace_approval_decision_pack",
            "workspace_execution_readiness_pack",
        ]:
            with self.subTest(existing_pack=existing_pack):
                self.assertIn(existing_pack, creative_pack)

        pack = creative_pack["workspace_execution_readiness_pack"]
        self.assertEqual(
            pack["pack_version"],
            "workspace_execution_readiness_pack_v1",
        )
        summary = pack["readiness_summary"]
        self.assertTrue(summary)
        for field in [
            "readiness_status",
            "launch_lock_status",
            "total_decisions",
            "blocked_count",
            "review_ready_count",
            "manual_review_required_count",
            "recommended_next_action",
            "real_execution_allowed",
        ]:
            with self.subTest(summary_field=field):
                self.assertIn(field, summary)
        self.assertFalse(summary["real_execution_allowed"])
        self.assertGreaterEqual(summary["blocked_count"], 1)
        self.assertTrue(summary["weak_evidence"] or summary["missing_quote"])

        launch_lock = pack["launch_lock"]
        self.assertTrue(launch_lock["lock_id"])
        self.assertIn(
            launch_lock["lock_status"],
            {"locked", "blocked", "dry_run_only"},
        )
        self.assertNotEqual(
            launch_lock["lock_status"],
            "unlocked_for_real_execution",
        )
        self.assertTrue(launch_lock["lock_reason"])
        self.assertTrue(launch_lock["unlock_requirements"])
        self.assertFalse(launch_lock["real_execution_allowed"])
        self.assertTrue(launch_lock["dry_run_only"])
        self.assertTrue(launch_lock["human_approval_required"])
        self.assertFalse(launch_lock["unlock_performed"])

        self.assertTrue(pack["preflight_checklist"])
        self.assertFalse(pack["preflight_checklist"]["preflight_executed"])
        self.assertIsInstance(pack["blocked_execution_reasons"], list)
        self.assertTrue(pack["blocked_execution_reasons"])
        self.assertTrue(pack["manual_review_requirements"])
        self.assertTrue(
            pack["manual_review_requirements"]["manual_review_required"]
        )
        enforcement = pack["dry_run_enforcement"]
        self.assertTrue(enforcement["dry_run_only"])
        for key in [
            "real_execution_allowed",
            "launch_allowed",
            "provider_call_allowed",
            "llm_call_allowed",
            "video_generation_allowed",
            "media_operation_allowed",
            "paid_operation_allowed",
            "registry_write_allowed",
            "database_write_allowed",
            "restore_allowed",
            "rollback_allowed",
            "external_scraping_allowed",
        ]:
            with self.subTest(enforcement=key):
                self.assertFalse(enforcement[key])

        self.assertIsInstance(pack["approved_for_review_items"], list)
        self.assertIsInstance(pack["not_approved_items"], list)
        self.assertTrue(pack["approved_for_review_items"])
        self.assertTrue(pack["not_approved_items"])
        for item in pack["approved_for_review_items"]:
            self.assertEqual(item["approval_scope"], "human_review_only")
            self.assertEqual(item["gate_status"], "ready_for_human_review")
            self.assertFalse(item["real_execution_allowed"])
        for item in pack["not_approved_items"]:
            self.assertFalse(item["real_execution_allowed"])

        self.assertTrue(pack["execution_risk_register"])
        self.assertTrue(
            all(
                not risk["real_execution_allowed"]
                for risk in pack["execution_risk_register"]
            )
        )
        checks = pack["readiness_quality_checks"]
        self.assertTrue(checks["approval_decision_pack_present"])
        self.assertTrue(checks["action_ticket_pack_present"])
        self.assertTrue(checks["action_queue_pack_present"])
        self.assertTrue(checks["decision_count_consistent"])
        self.assertTrue(checks["lock_id_present"])
        self.assertTrue(checks["launch_lock_closed"])
        self.assertTrue(checks["all_review_items_human_review_only"])
        self.assertTrue(checks["all_not_approved_items_execution_disabled"])
        self.assertTrue(checks["risk_register_complete"])
        self.assertTrue(checks["blocked_reasons_capture_evidence_risk"])
        self.assertTrue(checks["real_execution_disabled"])
        self.assertFalse(checks["database_write_performed"])
        self.assertFalse(checks["launch_unlock_performed"])

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
            "real_restore_enabled",
            "real_execution_enabled",
        ]:
            with self.subTest(boundary=key):
                self.assertFalse(boundaries[key])

    def test_workspace_execution_rehearsal_pack_is_preview_only(self):
        payload = {
            "workspace_id": "workspace-execution-rehearsal",
            "source": "manual_import",
            "output_language": "en",
            "products": [
                {
                    "platform": "manual",
                    "asin": "REHEARSE001",
                    "title": "Compact Travel Mug",
                    "reviews": [
                        {
                            "rating": 2,
                            "title": "Too short",
                            "text": "Leaks.",
                            "source_section": "manual_review",
                        }
                    ],
                }
            ],
        }

        response = self.client.post(
            "/api/v1/analyze-review-workspace", json=payload
        )

        self.assertEqual(response.status_code, 200)
        creative_pack = response.json()["creative_decision_pack"]
        for existing_pack in [
            "review_import_pack",
            "competitor_review_comparison_pack",
            "llm_assist_dry_run_pack",
            "video_provider_orchestration_dry_run_pack",
            "campaign_export_pack",
            "workspace_session_snapshot_pack",
            "workspace_run_compare_pack",
            "workspace_action_queue_pack",
            "workspace_action_ticket_pack",
            "workspace_approval_decision_pack",
            "workspace_execution_readiness_pack",
            "workspace_execution_rehearsal_pack",
        ]:
            with self.subTest(existing_pack=existing_pack):
                self.assertIn(existing_pack, creative_pack)

        pack = creative_pack["workspace_execution_rehearsal_pack"]
        self.assertEqual(
            pack["pack_version"],
            "workspace_execution_rehearsal_pack_v1",
        )
        summary = pack["rehearsal_summary"]
        self.assertTrue(summary)
        self.assertIn("dry_run", summary["mode"])
        self.assertIn("rehearsal", summary["mode"])
        self.assertFalse(summary["real_execution_allowed"])
        self.assertEqual(summary["launch_lock_status"], "locked")

        runbook = pack["rehearsal_runbook"]
        self.assertTrue(runbook)
        self.assertTrue(runbook["launch_lock_required"])
        self.assertTrue(runbook["launch_lock_observed"])
        self.assertFalse(runbook["execution_state_changes_allowed"])

        steps = pack["step_sequence"]
        self.assertTrue(steps)
        expected_step_types = {
            "verify_evidence",
            "review_approval_gate",
            "preview_llm_prompt",
            "preview_video_provider_plan",
            "validate_export_manifest",
            "confirm_launch_lock",
            "simulate_abort",
            "simulate_rollback",
            "manual_review_checkpoint",
        }
        self.assertTrue(expected_step_types.issubset({
            step["step_type"] for step in steps
        }))
        for step in steps:
            for field in [
                "step_id",
                "step_type",
                "dry_run_action",
                "validation_check",
            ]:
                with self.subTest(step=step["step_type"], field=field):
                    self.assertTrue(step[field])
            self.assertTrue(step["preconditions"])
            self.assertTrue(step["abort_trigger"])
            self.assertFalse(step["real_execution_allowed"])

        self.assertTrue(pack["checkpoint_plan"])
        timeline = pack["mock_execution_timeline"]
        self.assertEqual(
            timeline["timeline_type"], "deterministic_mock_timeline"
        )
        self.assertFalse(timeline["is_real_execution_log"])
        self.assertIn("not a real execution log", timeline["note"])
        self.assertTrue(timeline["events"])
        self.assertTrue(
            all(
                not event["real_execution_performed"]
                for event in timeline["events"]
            )
        )

        self.assertTrue(pack["expected_outputs"])
        failure_checks = pack["failure_injection_checks"]
        self.assertTrue(failure_checks["checks"])
        self.assertFalse(
            failure_checks["real_failure_injection_performed"]
        )
        self.assertTrue(pack["abort_triggers"])
        rollback_plan = pack["rollback_rehearsal_plan"]
        self.assertTrue(rollback_plan["steps"])
        self.assertFalse(rollback_plan["rollback_executed"])
        self.assertFalse(rollback_plan["restore_executed"])
        self.assertIn("never executes rollback", rollback_plan["note"])
        self.assertTrue(pack["operator_notes"])

        checks = pack["rehearsal_quality_checks"]
        self.assertTrue(checks["readiness_pack_present"])
        self.assertTrue(checks["approval_pack_present"])
        self.assertTrue(checks["ticket_pack_present"])
        self.assertTrue(checks["queue_pack_present"])
        self.assertTrue(checks["llm_dry_run_pack_present"])
        self.assertTrue(checks["video_dry_run_pack_present"])
        self.assertTrue(checks["launch_lock_closed"])
        self.assertTrue(checks["step_sequence_present"])
        self.assertTrue(checks["all_steps_traceable"])
        self.assertTrue(checks["all_steps_execution_disabled"])
        self.assertTrue(checks["mock_timeline_not_real"])
        self.assertTrue(checks["failure_injection_not_performed"])
        self.assertTrue(checks["rollback_not_performed"])
        self.assertFalse(checks["database_write_performed"])
        self.assertFalse(checks["real_execution_performed"])

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
            "real_restore_enabled",
            "real_execution_enabled",
        ]:
            with self.subTest(boundary=key):
                self.assertFalse(boundaries[key])

    def test_workspace_rehearsal_result_pack_requires_operator_review(self):
        payload = {
            "workspace_id": "workspace-rehearsal-result",
            "source": "manual_import",
            "output_language": "en",
            "products": [
                {
                    "platform": "manual",
                    "asin": "RESULT001",
                    "title": "Compact Travel Mug",
                    "reviews": [
                        {
                            "rating": 2,
                            "title": "Too short",
                            "text": "Leaks.",
                            "source_section": "manual_review",
                        }
                    ],
                }
            ],
        }

        response = self.client.post(
            "/api/v1/analyze-review-workspace", json=payload
        )

        self.assertEqual(response.status_code, 200)
        creative_pack = response.json()["creative_decision_pack"]
        for existing_pack in [
            "review_import_pack",
            "competitor_review_comparison_pack",
            "llm_assist_dry_run_pack",
            "video_provider_orchestration_dry_run_pack",
            "campaign_export_pack",
            "workspace_session_snapshot_pack",
            "workspace_run_compare_pack",
            "workspace_action_queue_pack",
            "workspace_action_ticket_pack",
            "workspace_approval_decision_pack",
            "workspace_execution_readiness_pack",
            "workspace_execution_rehearsal_pack",
            "workspace_rehearsal_result_pack",
        ]:
            with self.subTest(existing_pack=existing_pack):
                self.assertIn(existing_pack, creative_pack)

        pack = creative_pack["workspace_rehearsal_result_pack"]
        self.assertEqual(
            pack["pack_version"],
            "workspace_rehearsal_result_pack_v1",
        )
        summary = pack["result_summary"]
        self.assertTrue(summary["result_id"])
        self.assertIn("rehearsal_result", summary["mode"])
        self.assertIn("preview", summary["mode"])
        self.assertEqual(summary["launch_lock_status"], "locked")
        self.assertTrue(summary["dry_run_only"])
        self.assertFalse(summary["real_execution_allowed"])

        source_steps = creative_pack["workspace_execution_rehearsal_pack"][
            "step_sequence"
        ]
        step_results = pack["step_result_cards"]
        self.assertTrue(step_results)
        self.assertEqual(len(step_results), len(source_steps))
        source_step_ids = {step["step_id"] for step in source_steps}
        for result in step_results:
            for field in [
                "step_id",
                "step_type",
                "simulated_status",
                "validation_result",
            ]:
                with self.subTest(step=result["step_type"], field=field):
                    self.assertTrue(result[field])
            self.assertIn(result["step_id"], source_step_ids)
            self.assertIn(
                result["simulated_status"],
                {
                    "deterministic_simulated_pass",
                    "review_required",
                    "blocked",
                },
            )
            self.assertIn(
                "Deterministic rehearsal placeholder",
                result["observed_placeholder"],
            )
            self.assertFalse(result["real_execution_allowed"])

        checkpoint_results = pack["checkpoint_results"]
        self.assertTrue(checkpoint_results)
        self.assertFalse(
            checkpoint_results["opening_checkpoint"][
                "real_checkpoint_executed"
            ]
        )
        self.assertFalse(
            checkpoint_results["closing_checkpoint"][
                "real_execution_performed"
            ]
        )
        self.assertTrue(checkpoint_results["step_results"])

        self.assertIsInstance(pack["failure_findings"], list)
        self.assertTrue(pack["failure_findings"])
        self.assertTrue(
            all(
                not finding["real_failure_triggered"]
                for finding in pack["failure_findings"]
            )
        )
        self.assertTrue(pack["operator_review_items"])
        self.assertIsInstance(pack["blocked_follow_up_items"], list)
        self.assertTrue(pack["blocked_follow_up_items"])
        self.assertTrue(pack["next_rehearsal_recommendations"])

        checks = pack["result_quality_checks"]
        self.assertTrue(checks["execution_rehearsal_pack_present"])
        self.assertTrue(checks["step_count_consistent"])
        self.assertTrue(checks["all_step_results_traceable"])
        self.assertTrue(checks["all_statuses_are_simulated"])
        self.assertTrue(checks["all_real_execution_disabled"])
        self.assertTrue(checks["launch_lock_preserved"])
        self.assertTrue(checks["checkpoint_results_present"])
        self.assertTrue(checks["failure_findings_are_preview_only"])
        self.assertTrue(checks["rollback_not_performed"])
        self.assertTrue(checks["restore_not_performed"])
        self.assertFalse(checks["database_write_performed"])
        self.assertFalse(checks["operator_log_persisted"])
        self.assertFalse(checks["real_execution_performed"])

        audit = pack["audit_preview"]
        self.assertTrue(audit["result_id"])
        self.assertFalse(audit["is_real_operator_log"])
        self.assertFalse(audit["database_write_performed"])
        self.assertFalse(audit["audit_persisted"])
        self.assertIn("not persisted", audit["note"])

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
            "real_restore_enabled",
            "real_execution_enabled",
        ]:
            with self.subTest(boundary=key):
                self.assertFalse(boundaries[key])

    def test_workspace_rehearsal_remediation_pack_is_dry_run_only(self):
        payload = {
            "workspace_id": "workspace-rehearsal-remediation",
            "source": "manual_import",
            "output_language": "en",
            "products": [
                {
                    "platform": "manual",
                    "asin": "REMEDIATE001",
                    "title": "Compact Travel Mug",
                    "reviews": [
                        {
                            "rating": 2,
                            "title": "Too short",
                            "text": "Leaks.",
                            "source_section": "manual_review",
                        }
                    ],
                }
            ],
        }

        response = self.client.post(
            "/api/v1/analyze-review-workspace", json=payload
        )

        self.assertEqual(response.status_code, 200)
        creative_pack = response.json()["creative_decision_pack"]
        for existing_pack in [
            "review_import_pack",
            "competitor_review_comparison_pack",
            "llm_assist_dry_run_pack",
            "video_provider_orchestration_dry_run_pack",
            "campaign_export_pack",
            "workspace_session_snapshot_pack",
            "workspace_run_compare_pack",
            "workspace_action_queue_pack",
            "workspace_action_ticket_pack",
            "workspace_approval_decision_pack",
            "workspace_execution_readiness_pack",
            "workspace_execution_rehearsal_pack",
            "workspace_rehearsal_result_pack",
            "workspace_rehearsal_remediation_pack",
        ]:
            with self.subTest(existing_pack=existing_pack):
                self.assertIn(existing_pack, creative_pack)

        pack = creative_pack["workspace_rehearsal_remediation_pack"]
        self.assertEqual(
            pack["pack_version"],
            "workspace_rehearsal_remediation_pack_v1",
        )
        summary = pack["remediation_summary"]
        self.assertTrue(summary["remediation_id"])
        self.assertIn("remediation_plan", summary["mode"])
        self.assertIn("dry_run_follow_up", summary["mode"])
        self.assertIn("preview", summary["mode"])
        self.assertEqual(summary["launch_lock_status"], "locked")
        self.assertFalse(summary["real_execution_allowed"])

        actions = pack["remediation_action_items"]
        self.assertTrue(actions)
        source_results = creative_pack["workspace_rehearsal_result_pack"][
            "step_result_cards"
        ]
        source_step_ids = {result["step_id"] for result in source_results}
        for action in actions:
            for field in [
                "action_id",
                "source_step_id",
                "issue_type",
                "validation_before_retry",
            ]:
                with self.subTest(
                    action=action["action_id"], field=field
                ):
                    self.assertTrue(action[field])
            self.assertIn(action["source_step_id"], source_step_ids)
            self.assertTrue(action["source_pack"])
            self.assertTrue(action["required_input"])
            self.assertEqual(action["owner"], "human_operator")
            self.assertFalse(action["retry_eligible"])
            self.assertFalse(action["real_execution_allowed"])

        retry_plan = pack["retry_plan"]
        self.assertIn("dry_run", retry_plan["mode"])
        self.assertEqual(
            retry_plan["retry_type"], "dry_run_rehearsal_only"
        )
        self.assertTrue(retry_plan["pre_retry_requirements"])
        self.assertTrue(retry_plan["retry_sequence"])
        self.assertFalse(retry_plan["real_retry_executed"])
        self.assertFalse(retry_plan["real_execution_allowed"])

        self.assertIsInstance(pack["evidence_gap_fixes"], list)
        self.assertTrue(pack["evidence_gap_fixes"])
        self.assertTrue(
            all(
                not fix["fix_applied"]
                and not fix["real_execution_allowed"]
                and "do not scrape" in fix["collection_boundary"]
                for fix in pack["evidence_gap_fixes"]
            )
        )
        follow_up = pack["operator_follow_up_plan"]
        self.assertEqual(
            follow_up["plan_mode"], "human_review_preview_only"
        )
        self.assertFalse(follow_up["real_ticket_created"])
        self.assertFalse(follow_up["operator_log_written"])
        self.assertFalse(follow_up["real_execution_allowed"])

        blocked_plan = pack["blocked_item_resolution_plan"]
        self.assertIsInstance(blocked_plan, list)
        self.assertTrue(blocked_plan)
        self.assertTrue(
            all(
                item["resolution_status"]
                == "not_started_preview_only"
                and not item["retry_eligible"]
                and not item["real_execution_allowed"]
                for item in blocked_plan
            )
        )
        next_plan = pack["next_rehearsal_plan"]
        self.assertEqual(
            next_plan["mode"], "next_dry_run_rehearsal_preview"
        )
        self.assertTrue(next_plan["entry_criteria"])
        self.assertFalse(next_plan["next_rehearsal_started"])
        self.assertFalse(next_plan["real_execution_allowed"])
        self.assertTrue(pack["remediation_priority_rationale"])

        checks = pack["remediation_quality_checks"]
        self.assertTrue(checks["rehearsal_result_pack_present"])
        self.assertTrue(checks["all_actions_traceable"])
        self.assertTrue(checks["all_actions_execution_disabled"])
        self.assertTrue(checks["blocked_items_have_resolution_preview"])
        self.assertTrue(checks["review_required_steps_have_actions"])
        self.assertTrue(checks["retry_plan_is_dry_run_only"])
        self.assertTrue(checks["evidence_collection_not_performed"])
        self.assertFalse(checks["real_ticket_created"])
        self.assertFalse(checks["database_write_performed"])
        self.assertFalse(checks["remediation_executed"])
        self.assertFalse(checks["real_retry_executed"])
        self.assertFalse(checks["real_execution_performed"])

        audit = pack["audit_preview"]
        self.assertTrue(audit["remediation_id"])
        self.assertFalse(audit["is_real_ticket_log"])
        self.assertFalse(audit["database_write_performed"])
        self.assertFalse(audit["audit_persisted"])
        self.assertIn("no ticket", audit["note"])
        self.assertIn("no ticket, operator log, fix, retry", audit["note"])

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
            "real_restore_enabled",
            "real_execution_enabled",
        ]:
            with self.subTest(boundary=key):
                self.assertFalse(boundaries[key])

    def test_workspace_remediation_verification_pack_is_preview_only(self):
        payload = {
            "workspace_id": "workspace-remediation-verification",
            "source": "manual_import",
            "output_language": "en",
            "products": [
                {
                    "platform": "manual",
                    "asin": "VERIFY001",
                    "title": "Compact Travel Mug",
                    "reviews": [
                        {
                            "rating": 2,
                            "title": "Too short",
                            "text": "Leaks.",
                            "source_section": "manual_review",
                        }
                    ],
                }
            ],
        }

        response = self.client.post(
            "/api/v1/analyze-review-workspace", json=payload
        )

        self.assertEqual(response.status_code, 200)
        creative_pack = response.json()["creative_decision_pack"]
        for existing_pack in [
            "review_import_pack",
            "competitor_review_comparison_pack",
            "llm_assist_dry_run_pack",
            "video_provider_orchestration_dry_run_pack",
            "campaign_export_pack",
            "workspace_session_snapshot_pack",
            "workspace_run_compare_pack",
            "workspace_action_queue_pack",
            "workspace_action_ticket_pack",
            "workspace_approval_decision_pack",
            "workspace_execution_readiness_pack",
            "workspace_execution_rehearsal_pack",
            "workspace_rehearsal_result_pack",
            "workspace_rehearsal_remediation_pack",
            "workspace_remediation_verification_pack",
        ]:
            with self.subTest(existing_pack=existing_pack):
                self.assertIn(existing_pack, creative_pack)

        pack = creative_pack["workspace_remediation_verification_pack"]
        self.assertEqual(
            pack["pack_version"],
            "workspace_remediation_verification_pack_v1",
        )
        summary = pack["verification_summary"]
        self.assertTrue(summary["verification_run_id"])
        self.assertIn("remediation_verification", summary["mode"])
        self.assertIn("retry_readiness_preview", summary["mode"])
        self.assertIn("dry_run_only", summary["mode"])
        self.assertFalse(summary["ready_for_real_execution"])
        self.assertFalse(summary["real_execution_allowed"])

        source_actions = creative_pack[
            "workspace_rehearsal_remediation_pack"
        ]["remediation_action_items"]
        cards = pack["action_verification_cards"]
        self.assertTrue(cards)
        self.assertEqual(len(cards), len(source_actions))
        source_action_ids = {
            action["action_id"] for action in source_actions
        }
        for card in cards:
            for field in [
                "verification_id",
                "source_action_id",
                "verification_status",
                "validation_before_retry",
            ]:
                with self.subTest(
                    card=card["verification_id"], field=field
                ):
                    self.assertTrue(card[field])
            self.assertIn(card["source_action_id"], source_action_ids)
            self.assertTrue(card["source_step_id"])
            self.assertTrue(card["required_input"])
            self.assertFalse(card["input_available"])
            self.assertFalse(card["retry_eligible"])
            self.assertTrue(card["remaining_gap"])
            self.assertTrue(card["operator_review_required"])
            self.assertFalse(card["real_execution_allowed"])

        gate = pack["retry_readiness_gate"]
        self.assertEqual(
            gate["gate_mode"],
            "next_dry_run_rehearsal_readiness_preview",
        )
        self.assertEqual(gate["gate_status"], "blocked_for_next_dry_run")
        self.assertFalse(gate["ready_for_next_dry_run"])
        self.assertFalse(gate["ready_for_real_execution"])
        self.assertFalse(gate["real_execution_gate"])
        self.assertFalse(gate["real_execution_allowed"])

        self.assertIsInstance(pack["remaining_blockers"], list)
        self.assertTrue(pack["remaining_blockers"])
        self.assertTrue(
            all(
                blocker["blocks_real_execution"]
                and not blocker["real_execution_allowed"]
                for blocker in pack["remaining_blockers"]
            )
        )
        required_inputs = pack["required_inputs_checklist"]
        self.assertIsInstance(required_inputs, list)
        self.assertTrue(required_inputs)
        self.assertTrue(
            all(
                not item["input_available"]
                and not item["external_collection_allowed"]
                and not item["real_execution_allowed"]
                for item in required_inputs
            )
        )

        evidence = pack["evidence_readiness_review"]
        self.assertEqual(
            evidence["review_mode"], "evidence_readiness_preview_only"
        )
        self.assertFalse(evidence["external_data_collected"])
        self.assertFalse(evidence["real_execution_allowed"])
        signoff = pack["operator_signoff_preview"]
        self.assertEqual(
            signoff["signoff_mode"], "human_signoff_preview_only"
        )
        self.assertFalse(signoff["approval_created"])
        self.assertFalse(signoff["ticket_created"])
        self.assertFalse(signoff["operator_log_written"])
        self.assertFalse(signoff["signoff_persisted"])
        self.assertFalse(signoff["real_execution_allowed"])

        scope = pack["next_retry_scope"]
        self.assertEqual(
            scope["scope_mode"],
            "next_dry_run_rehearsal_scope_preview",
        )
        self.assertEqual(scope["retry_type"], "dry_run_rehearsal_only")
        self.assertFalse(scope["next_retry_started"])
        self.assertFalse(scope["real_execution_allowed"])
        self.assertIn("only to a future dry-run rehearsal", scope["note"])

        checks = pack["verification_quality_checks"]
        self.assertTrue(checks["remediation_pack_present"])
        self.assertTrue(checks["action_count_consistent"])
        self.assertTrue(checks["all_cards_traceable"])
        self.assertTrue(checks["all_cards_execution_disabled"])
        self.assertTrue(checks["unready_actions_have_blockers"])
        self.assertTrue(checks["required_inputs_are_not_invented"])
        self.assertTrue(checks["retry_gate_is_dry_run_only"])
        self.assertFalse(checks["ready_for_real_execution"])
        self.assertFalse(checks["external_data_collected"])
        self.assertFalse(checks["approval_created"])
        self.assertFalse(checks["ticket_created"])
        self.assertFalse(checks["database_write_performed"])
        self.assertFalse(checks["verification_persisted"])
        self.assertFalse(checks["real_execution_performed"])

        audit = pack["audit_preview"]
        self.assertTrue(audit["verification_run_id"])
        self.assertFalse(audit["is_real_ticket_status"])
        self.assertFalse(audit["is_real_remediation_completion"])
        self.assertFalse(audit["database_write_performed"])
        self.assertFalse(audit["audit_persisted"])

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
            "real_restore_enabled",
            "real_execution_enabled",
        ]:
            with self.subTest(boundary=key):
                self.assertFalse(boundaries[key])


    def test_workspace_retry_rehearsal_plan_pack_is_second_pass_preview(self):
        payload = {
            "workspace_id": "workspace-retry-rehearsal-plan",
            "source": "manual_import",
            "output_language": "en",
            "products": [{
                "platform": "manual",
                "asin": "RETRY001",
                "title": "Compact Travel Mug",
                "reviews": [{
                    "rating": 2,
                    "title": "Too short",
                    "text": "Leaks.",
                    "source_section": "manual_review",
                }],
            }],
        }
        response = self.client.post(
            "/api/v1/analyze-review-workspace", json=payload
        )
        self.assertEqual(response.status_code, 200)
        creative_pack = response.json()["creative_decision_pack"]
        for existing_pack in [
            "review_import_pack", "competitor_review_comparison_pack",
            "llm_assist_dry_run_pack",
            "video_provider_orchestration_dry_run_pack",
            "campaign_export_pack", "workspace_session_snapshot_pack",
            "workspace_run_compare_pack", "workspace_action_queue_pack",
            "workspace_action_ticket_pack",
            "workspace_approval_decision_pack",
            "workspace_execution_readiness_pack",
            "workspace_execution_rehearsal_pack",
            "workspace_rehearsal_result_pack",
            "workspace_rehearsal_remediation_pack",
            "workspace_remediation_verification_pack",
            "workspace_retry_rehearsal_plan_pack",
        ]:
            with self.subTest(existing_pack=existing_pack):
                self.assertIn(existing_pack, creative_pack)

        pack = creative_pack["workspace_retry_rehearsal_plan_pack"]
        self.assertEqual(
            pack["pack_version"],
            "workspace_retry_rehearsal_plan_pack_v1",
        )
        summary = pack["retry_rehearsal_summary"]
        self.assertTrue(summary["retry_plan_id"])
        self.assertIn("retry_rehearsal_plan", summary["mode"])
        self.assertIn("second_pass_dry_run", summary["mode"])
        self.assertIn("preview", summary["mode"])
        self.assertFalse(summary["real_retry_allowed"])
        self.assertFalse(summary["real_execution_allowed"])

        scope = pack["retry_scope"]
        self.assertEqual(
            scope["scope_mode"],
            "second_pass_dry_run_rehearsal_scope_preview",
        )
        self.assertEqual(
            scope["retry_type"], "next_dry_run_rehearsal_only"
        )
        self.assertFalse(scope["real_retry_started"])
        self.assertFalse(scope["real_execution_allowed"])

        source_cards = creative_pack[
            "workspace_remediation_verification_pack"
        ]["action_verification_cards"]
        steps = pack["second_pass_step_sequence"]
        self.assertTrue(steps)
        self.assertEqual(len(steps), len(source_cards))
        verification_ids = {
            card["verification_id"] for card in source_cards
        }
        for step in steps:
            for field in [
                "retry_step_id", "source_verification_id", "step_type",
                "dry_run_retry_action", "tightened_validation_check",
            ]:
                with self.subTest(step=step["retry_step_id"], field=field):
                    self.assertTrue(step[field])
            self.assertIn(step["source_verification_id"], verification_ids)
            self.assertTrue(step["source_action_id"])
            self.assertTrue(step["preconditions"])
            self.assertTrue(step["expected_observation"])
            self.assertTrue(step["abort_trigger"])
            self.assertFalse(step["real_execution_allowed"])

        blockers = pack["carry_forward_blockers"]
        self.assertIsInstance(blockers, list)
        self.assertTrue(blockers)
        self.assertTrue(
            all(not blocker["real_execution_allowed"] for blocker in blockers)
        )
        checkpoints = pack["tightened_checkpoint_plan"]
        self.assertTrue(checkpoints["opening_checks"])
        self.assertTrue(checkpoints["step_checkpoints"])
        self.assertTrue(checkpoints["closing_checks"])
        self.assertFalse(checkpoints["checkpoint_execution_performed"])

        matrix = pack["retry_validation_matrix"]
        self.assertEqual(len(matrix), len(steps))
        self.assertTrue(
            all(
                row["validation_condition"]
                and row["failure_handling"]
                and not row["real_execution_allowed"]
                for row in matrix
            )
        )
        review = pack["operator_review_before_retry"]
        self.assertTrue(review["operator_review_required"])
        self.assertFalse(review["review_completed"])
        self.assertFalse(review["approval_created"])
        self.assertFalse(review["ticket_created"])
        self.assertFalse(review["operator_log_written"])
        self.assertFalse(review["real_execution_allowed"])

        timeline = pack["mock_retry_timeline"]
        self.assertEqual(
            timeline["timeline_type"],
            "deterministic_mock_second_pass_timeline",
        )
        self.assertFalse(timeline["is_real_execution_log"])
        self.assertFalse(timeline["is_real_retry_log"])
        self.assertIn("not a real retry or execution log", timeline["note"])
        abort = pack["retry_abort_plan"]
        self.assertTrue(abort["abort_triggers"])
        self.assertFalse(abort["real_abort_executed"])
        self.assertFalse(abort["real_restore_executed"])
        self.assertFalse(abort["real_rollback_executed"])
        self.assertFalse(abort["real_execution_allowed"])

        checks = pack["retry_quality_checks"]
        for key in [
            "remediation_verification_pack_present", "step_count_consistent",
            "all_steps_traceable", "all_steps_are_dry_run_actions",
            "all_steps_execution_disabled", "blockers_carried_forward",
            "validation_matrix_complete", "mock_timeline_not_real",
            "operator_review_not_completed",
        ]:
            with self.subTest(check=key):
                self.assertTrue(checks[key])
        for key in [
            "external_data_collected", "approval_created", "ticket_created",
            "database_write_performed", "real_retry_performed",
            "real_execution_performed",
        ]:
            with self.subTest(check=key):
                self.assertFalse(checks[key])

        audit = pack["audit_preview"]
        self.assertTrue(audit["retry_plan_id"])
        self.assertFalse(audit["is_real_retry_log"])
        self.assertFalse(audit["is_real_execution_log"])
        self.assertFalse(audit["database_write_performed"])
        self.assertFalse(audit["audit_persisted"])

        boundaries = pack["safety_boundaries"]
        for key in [
            "provider_calls_enabled", "llm_api_enabled",
            "video_generation_enabled", "media_upload_enabled",
            "media_download_enabled", "paid_operation_enabled",
            "registry_write_enabled", "rollback_enabled",
            "external_scraping_enabled", "database_persistence_enabled",
            "real_restore_enabled", "real_execution_enabled",
        ]:
            with self.subTest(boundary=key):
                self.assertFalse(boundaries[key])

    def test_workspace_retry_rehearsal_result_pack_is_preview_only(self):
        payload = {
            "workspace_id": "workspace-retry-rehearsal-result",
            "source": "manual_import",
            "output_language": "en",
            "products": [{
                "platform": "manual",
                "asin": "RETRYRESULT001",
                "title": "Compact Travel Mug",
                "reviews": [{
                    "rating": 2,
                    "title": "Still leaks",
                    "text": "Leaks.",
                    "source_section": "manual_review",
                }],
            }],
        }
        response = self.client.post(
            "/api/v1/analyze-review-workspace", json=payload
        )
        self.assertEqual(response.status_code, 200)
        creative_pack = response.json()["creative_decision_pack"]
        for existing_pack in [
            "review_import_pack", "competitor_review_comparison_pack",
            "llm_assist_dry_run_pack",
            "video_provider_orchestration_dry_run_pack",
            "campaign_export_pack", "workspace_session_snapshot_pack",
            "workspace_run_compare_pack", "workspace_action_queue_pack",
            "workspace_action_ticket_pack",
            "workspace_approval_decision_pack",
            "workspace_execution_readiness_pack",
            "workspace_execution_rehearsal_pack",
            "workspace_rehearsal_result_pack",
            "workspace_rehearsal_remediation_pack",
            "workspace_remediation_verification_pack",
            "workspace_retry_rehearsal_plan_pack",
            "workspace_retry_rehearsal_result_pack",
        ]:
            with self.subTest(existing_pack=existing_pack):
                self.assertIn(existing_pack, creative_pack)

        plan_pack = creative_pack["workspace_retry_rehearsal_plan_pack"]
        pack = creative_pack["workspace_retry_rehearsal_result_pack"]
        self.assertEqual(
            pack["pack_version"],
            "workspace_retry_rehearsal_result_pack_v1",
        )
        summary = pack["retry_result_summary"]
        self.assertTrue(summary["retry_result_id"])
        self.assertIn("retry_rehearsal_result", summary["mode"])
        self.assertIn("second_pass_dry_run_result", summary["mode"])
        self.assertIn("preview", summary["mode"])
        self.assertEqual(
            summary["source_retry_plan_id"],
            plan_pack["retry_rehearsal_summary"]["retry_plan_id"],
        )
        self.assertFalse(summary["real_retry_performed"])
        self.assertFalse(summary["real_execution_allowed"])

        results = pack["second_pass_step_results"]
        source_steps = plan_pack["second_pass_step_sequence"]
        self.assertTrue(results)
        self.assertEqual(len(results), len(source_steps))
        source_step_ids = {step["retry_step_id"] for step in source_steps}
        for result in results:
            for field in [
                "result_id", "source_retry_step_id",
                "source_verification_id", "source_action_id",
                "simulated_retry_status",
                "tightened_validation_result",
            ]:
                with self.subTest(result=result["result_id"], field=field):
                    self.assertTrue(result[field])
            self.assertIn(result["source_retry_step_id"], source_step_ids)
            self.assertIn(
                result["simulated_retry_status"],
                [
                    "deterministic_simulated_pass",
                    "review_required",
                    "blocked_pending_operator_review",
                ],
            )
            self.assertIn(
                result["tightened_validation_result"],
                [
                    "blocked_by_remaining_gap",
                    "deterministic_simulated_validation_pass",
                ],
            )
            self.assertTrue(result["observed_placeholder"])
            self.assertFalse(result["real_execution_allowed"])

        checkpoint_results = pack["retry_checkpoint_results"]
        self.assertTrue(checkpoint_results)
        self.assertFalse(
            checkpoint_results["checkpoint_execution_performed"]
        )
        self.assertFalse(checkpoint_results["real_execution_allowed"])
        self.assertEqual(
            len(checkpoint_results["step_checkpoints"]), len(results)
        )

        blocker_results = pack["carry_forward_blocker_results"]
        self.assertIsInstance(blocker_results, list)
        self.assertTrue(blocker_results)
        self.assertTrue(
            all(
                not blocker["real_execution_allowed"]
                for blocker in blocker_results
            )
        )
        findings = pack["retry_failure_findings"]
        self.assertIsInstance(findings, list)
        self.assertTrue(findings)
        self.assertTrue(
            all(not finding["real_failure_triggered"] for finding in findings)
        )
        review = pack["operator_review_after_retry"]
        self.assertTrue(review["operator_review_required"])
        self.assertFalse(review["approval_created"])
        self.assertFalse(review["ticket_created"])
        self.assertFalse(review["operator_log_written"])
        self.assertFalse(review["database_write_performed"])
        self.assertFalse(review["real_execution_allowed"])

        gaps = pack["remaining_retry_gaps"]
        self.assertIsInstance(gaps, list)
        self.assertTrue(gaps)
        self.assertTrue(
            all(gap["blocks_real_execution"] for gap in gaps)
        )
        recommendations = pack["next_cycle_recommendations"]
        self.assertTrue(recommendations)
        self.assertTrue(
            all(
                not item["real_execution_allowed"]
                for item in recommendations
            )
        )

        checks = pack["retry_result_quality_checks"]
        for key in [
            "retry_rehearsal_plan_pack_present",
            "step_result_count_consistent",
            "all_results_traceable",
            "all_results_execution_disabled",
            "checkpoint_results_are_preview_only",
            "mock_timeline_was_not_executed",
            "abort_plan_not_executed",
            "operator_review_not_persisted",
        ]:
            with self.subTest(check=key):
                self.assertTrue(checks[key])
        for key in [
            "database_write_performed", "real_retry_performed",
            "real_execution_performed",
        ]:
            with self.subTest(check=key):
                self.assertFalse(checks[key])

        audit = pack["audit_preview"]
        self.assertTrue(audit["retry_result_id"])
        self.assertFalse(audit["is_real_retry_log"])
        self.assertFalse(audit["is_real_execution_log"])
        self.assertFalse(audit["database_write_performed"])
        self.assertFalse(audit["audit_persisted"])

        boundaries = pack["safety_boundaries"]
        for key in [
            "provider_calls_enabled", "llm_api_enabled",
            "video_generation_enabled", "media_upload_enabled",
            "media_download_enabled", "paid_operation_enabled",
            "registry_write_enabled", "rollback_enabled",
            "external_scraping_enabled", "database_persistence_enabled",
            "real_restore_enabled", "real_execution_enabled",
        ]:
            with self.subTest(boundary=key):
                self.assertFalse(boundaries[key])

    def test_workspace_retry_cycle_decision_pack_is_preview_only(self):
        payload = {
            "workspace_id": "workspace-retry-cycle-decision",
            "source": "manual_import",
            "output_language": "en",
            "products": [{
                "platform": "manual",
                "asin": "RETRYCYCLE001",
                "title": "Compact Travel Mug",
                "reviews": [{
                    "rating": 2,
                    "title": "Still leaks",
                    "text": "Leaks.",
                    "source_section": "manual_review",
                }],
            }],
        }
        response = self.client.post(
            "/api/v1/analyze-review-workspace", json=payload
        )
        self.assertEqual(response.status_code, 200)
        creative_pack = response.json()["creative_decision_pack"]
        for existing_pack in [
            "review_import_pack", "competitor_review_comparison_pack",
            "llm_assist_dry_run_pack",
            "video_provider_orchestration_dry_run_pack",
            "campaign_export_pack", "workspace_session_snapshot_pack",
            "workspace_run_compare_pack", "workspace_action_queue_pack",
            "workspace_action_ticket_pack",
            "workspace_approval_decision_pack",
            "workspace_execution_readiness_pack",
            "workspace_execution_rehearsal_pack",
            "workspace_rehearsal_result_pack",
            "workspace_rehearsal_remediation_pack",
            "workspace_remediation_verification_pack",
            "workspace_retry_rehearsal_plan_pack",
            "workspace_retry_rehearsal_result_pack",
            "workspace_retry_cycle_decision_pack",
        ]:
            with self.subTest(existing_pack=existing_pack):
                self.assertIn(existing_pack, creative_pack)

        result_pack = creative_pack["workspace_retry_rehearsal_result_pack"]
        pack = creative_pack["workspace_retry_cycle_decision_pack"]
        self.assertEqual(
            pack["pack_version"],
            "workspace_retry_cycle_decision_pack_v1",
        )

        summary = pack["cycle_decision_summary"]
        self.assertTrue(summary["cycle_decision_id"])
        self.assertIn("retry_cycle_decision", summary["mode"])
        self.assertIn("next_cycle_control", summary["mode"])
        self.assertIn("preview", summary["mode"])
        self.assertEqual(
            summary["source_retry_result_id"],
            result_pack["retry_result_summary"]["retry_result_id"],
        )
        self.assertFalse(summary["real_execution_allowed"])

        options = pack["decision_options"]
        self.assertTrue(options)
        option_types = {option["option_type"] for option in options}
        for expected_type in [
            "continue_dry_run_cycle", "return_to_remediation",
            "hold_for_manual_review", "keep_blocked",
            "close_cycle_preview",
        ]:
            with self.subTest(option_type=expected_type):
                self.assertIn(expected_type, option_types)
        for option in options:
            for field in [
                "option_id", "option_type", "rationale",
                "allowed_next_state",
            ]:
                with self.subTest(option=option["option_id"], field=field):
                    self.assertTrue(option[field])
            self.assertEqual(
                option["source_pack"],
                "workspace_retry_rehearsal_result_pack",
            )
            self.assertFalse(option["real_execution_allowed"])
        self.assertTrue(any(option["recommended"] for option in options))

        recommended = pack["recommended_cycle_action"]
        self.assertTrue(recommended)
        self.assertTrue(recommended["preview_recommendation_only"])
        self.assertFalse(recommended["real_execution_allowed"])
        self.assertIn(
            recommended["action_type"],
            [
                "continue_dry_run_cycle",
                "return_to_remediation",
                "hold_for_manual_review",
            ],
        )

        cycle_gate = pack["cycle_gate"]
        self.assertTrue(cycle_gate)
        self.assertIn("preview", cycle_gate["gate_mode"])
        self.assertFalse(cycle_gate["real_execution_gate"])
        self.assertFalse(cycle_gate["ready_for_real_execution"])
        self.assertFalse(cycle_gate["real_execution_allowed"])
        self.assertFalse(cycle_gate["database_write_performed"])
        self.assertFalse(cycle_gate["approval_created"])

        carry_forward_items = pack["carry_forward_items"]
        self.assertIsInstance(carry_forward_items, list)
        self.assertTrue(carry_forward_items)
        self.assertTrue(
            all(item["blocks_real_execution"] for item in carry_forward_items)
        )
        self.assertTrue(
            all(
                not item["real_execution_allowed"]
                for item in carry_forward_items
            )
        )

        blocked_items = pack["blocked_or_review_required_items"]
        self.assertIsInstance(blocked_items, list)
        self.assertTrue(blocked_items)
        self.assertTrue(
            all(item["manual_review_required"] for item in blocked_items)
        )
        self.assertTrue(
            all(not item["real_execution_allowed"] for item in blocked_items)
        )

        next_scope = pack["next_cycle_scope"]
        self.assertIn("dry_run", next_scope["scope_mode"])
        self.assertFalse(next_scope["can_execute_retry"])
        self.assertFalse(next_scope["can_collect_external_data"])
        self.assertFalse(next_scope["can_write_database"])
        self.assertFalse(next_scope["real_execution_allowed"])

        manual_review = pack["manual_review_packet"]
        self.assertIn("preview", manual_review["packet_mode"])
        self.assertTrue(manual_review["operator_review_required"])
        self.assertFalse(manual_review["approval_created"])
        self.assertFalse(manual_review["ticket_created"])
        self.assertFalse(manual_review["operator_log_written"])
        self.assertFalse(manual_review["database_write_performed"])
        self.assertFalse(manual_review["real_execution_allowed"])

        checks = pack["decision_quality_checks"]
        for key in [
            "retry_rehearsal_result_pack_present",
            "all_options_trace_to_retry_result",
            "all_options_execution_disabled",
            "recommended_option_present",
            "cycle_gate_is_preview_only",
            "checkpoint_results_are_preview_only",
            "manual_review_packet_not_persisted",
            "audit_preview_not_persisted",
        ]:
            with self.subTest(check=key):
                self.assertTrue(checks[key])
        for key in [
            "database_write_performed", "real_retry_performed",
            "real_execution_performed",
        ]:
            with self.subTest(check=key):
                self.assertFalse(checks[key])

        audit = pack["audit_preview"]
        self.assertTrue(audit["cycle_decision_id"])
        self.assertFalse(audit["is_real_cycle_control_log"])
        self.assertFalse(audit["database_write_performed"])
        self.assertFalse(audit["audit_persisted"])

        boundaries = pack["safety_boundaries"]
        for key in [
            "provider_calls_enabled", "llm_api_enabled",
            "video_generation_enabled", "media_upload_enabled",
            "media_download_enabled", "paid_operation_enabled",
            "registry_write_enabled", "rollback_enabled",
            "external_scraping_enabled", "database_persistence_enabled",
            "real_restore_enabled", "real_execution_enabled",
        ]:
            with self.subTest(boundary=key):
                self.assertFalse(boundaries[key])

    def test_workspace_cycle_history_timeline_pack_is_preview_only(self):
        payload = {
            "workspace_id": "workspace-cycle-history-timeline",
            "source": "manual_import",
            "output_language": "en",
            "products": [{
                "platform": "manual",
                "asin": "CYCLETIME001",
                "title": "Compact Travel Mug",
                "reviews": [{
                    "rating": 2,
                    "title": "Still leaks",
                    "text": "Leaks.",
                    "source_section": "manual_review",
                }],
            }],
        }
        response = self.client.post(
            "/api/v1/analyze-review-workspace", json=payload
        )
        self.assertEqual(response.status_code, 200)
        creative_pack = response.json()["creative_decision_pack"]
        for existing_pack in [
            "review_import_pack", "competitor_review_comparison_pack",
            "llm_assist_dry_run_pack",
            "video_provider_orchestration_dry_run_pack",
            "campaign_export_pack", "workspace_session_snapshot_pack",
            "workspace_run_compare_pack", "workspace_action_queue_pack",
            "workspace_action_ticket_pack",
            "workspace_approval_decision_pack",
            "workspace_execution_readiness_pack",
            "workspace_execution_rehearsal_pack",
            "workspace_rehearsal_result_pack",
            "workspace_rehearsal_remediation_pack",
            "workspace_remediation_verification_pack",
            "workspace_retry_rehearsal_plan_pack",
            "workspace_retry_rehearsal_result_pack",
            "workspace_retry_cycle_decision_pack",
            "workspace_cycle_history_timeline_pack",
        ]:
            with self.subTest(existing_pack=existing_pack):
                self.assertIn(existing_pack, creative_pack)

        cycle_pack = creative_pack["workspace_retry_cycle_decision_pack"]
        pack = creative_pack["workspace_cycle_history_timeline_pack"]
        self.assertEqual(
            pack["pack_version"],
            "workspace_cycle_history_timeline_pack_v1",
        )
        summary = pack["timeline_summary"]
        self.assertTrue(summary["timeline_id"])
        self.assertIn("cycle_history_preview", summary["mode"])
        self.assertIn("decision_timeline", summary["mode"])
        self.assertIn("dry_run_audit_preview", summary["mode"])
        self.assertEqual(
            summary["source_cycle_decision_id"],
            cycle_pack["cycle_decision_summary"]["cycle_decision_id"],
        )
        self.assertFalse(summary["real_execution_allowed"])

        events = pack["timeline_events"]
        self.assertGreaterEqual(len(events), 8)
        event_types = {event["event_type"] for event in events}
        for expected_type in [
            "readiness_lock", "execution_rehearsal_plan",
            "rehearsal_result", "remediation_plan",
            "remediation_verification", "retry_rehearsal_plan",
            "retry_rehearsal_result", "retry_cycle_decision",
            "manual_review_checkpoint", "blocked_or_carry_forward",
        ]:
            with self.subTest(event_type=expected_type):
                self.assertIn(expected_type, event_types)
        for index, event in enumerate(events, start=1):
            self.assertEqual(event["event_order"], index)
            for field in [
                "event_id", "event_type", "event_title",
                "source_pack", "cycle_phase", "decision_or_status",
                "summary",
            ]:
                with self.subTest(event=event["event_id"], field=field):
                    self.assertTrue(event[field])
            self.assertIsInstance(event["source_keys"], list)
            self.assertIsInstance(event["input_refs"], list)
            self.assertIsInstance(event["output_refs"], list)
            self.assertFalse(event["real_execution_allowed"])

        lineage = pack["pack_lineage_map"]
        self.assertTrue(lineage)
        for pack_name in [
            "workspace_execution_readiness_pack",
            "workspace_execution_rehearsal_pack",
            "workspace_rehearsal_result_pack",
            "workspace_rehearsal_remediation_pack",
            "workspace_remediation_verification_pack",
            "workspace_retry_rehearsal_plan_pack",
            "workspace_retry_rehearsal_result_pack",
            "workspace_retry_cycle_decision_pack",
        ]:
            with self.subTest(lineage_pack=pack_name):
                self.assertIn(pack_name, lineage)
                self.assertIn("direct_upstream", lineage[pack_name])
                self.assertIn("direct_downstream", lineage[pack_name])
                self.assertFalse(lineage[pack_name]["derived_from_real_history"])
                self.assertFalse(lineage[pack_name]["database_read_performed"])
                self.assertFalse(lineage[pack_name]["database_write_performed"])

        decision_trace = pack["decision_trace_map"]
        self.assertEqual(
            decision_trace["cycle_decision_id"],
            cycle_pack["cycle_decision_summary"]["cycle_decision_id"],
        )
        self.assertTrue(decision_trace["source_retry_result_id"])
        self.assertIsInstance(decision_trace["source_retry_result_ids"], list)
        self.assertIsInstance(decision_trace["source_blocker_ids"], list)
        self.assertIsInstance(decision_trace["source_remaining_gap_ids"], list)
        self.assertIsInstance(decision_trace["source_recommendation_ids"], list)
        self.assertFalse(decision_trace["real_execution_allowed"])

        transitions = pack["cycle_state_transitions"]
        self.assertTrue(transitions)
        self.assertTrue(
            all(
                transition["transition_type"] == "preview_state_transition"
                for transition in transitions
            )
        )
        self.assertTrue(
            all(
                not transition["state_change_persisted"]
                for transition in transitions
            )
        )
        self.assertTrue(
            all(
                not transition["real_execution_allowed"]
                for transition in transitions
            )
        )

        carry_trace = pack["carry_forward_trace"]
        self.assertIsInstance(carry_trace, list)
        self.assertTrue(carry_trace)
        self.assertTrue(
            all(
                trace["origin_pack"] == "workspace_retry_rehearsal_result_pack"
                for trace in carry_trace
            )
        )
        self.assertTrue(
            all(not trace["real_execution_allowed"] for trace in carry_trace)
        )

        operator_trace = pack["operator_review_trace"]
        self.assertIsInstance(operator_trace, list)
        self.assertTrue(operator_trace)
        self.assertTrue(
            all(not trace["approval_created"] for trace in operator_trace)
        )
        self.assertTrue(
            all(
                not trace["operator_log_written"]
                for trace in operator_trace
            )
        )
        self.assertTrue(
            all(
                not trace["database_write_performed"]
                for trace in operator_trace
            )
        )
        self.assertTrue(
            all(not trace["real_execution_allowed"] for trace in operator_trace)
        )

        audit = pack["audit_timeline_preview"]
        self.assertTrue(audit["timeline_id"])
        self.assertFalse(audit["is_real_history_record"])
        self.assertFalse(audit["real_history_table_read_performed"])
        self.assertFalse(audit["database_write_performed"])
        self.assertFalse(audit["audit_persisted"])

        checks = pack["timeline_quality_checks"]
        for key in [
            "source_packs_present", "timeline_events_present",
            "event_order_is_sequential",
            "all_events_execution_disabled",
            "pack_lineage_map_present",
            "decision_trace_map_present",
            "cycle_state_transitions_are_preview_only",
            "operator_review_trace_not_persisted",
        ]:
            with self.subTest(check=key):
                self.assertTrue(checks[key])
        for key in [
            "real_history_table_read_performed",
            "database_write_performed",
            "real_execution_performed",
        ]:
            with self.subTest(check=key):
                self.assertFalse(checks[key])

        boundaries = pack["safety_boundaries"]
        for key in [
            "provider_calls_enabled", "llm_api_enabled",
            "video_generation_enabled", "media_upload_enabled",
            "media_download_enabled", "paid_operation_enabled",
            "registry_write_enabled", "rollback_enabled",
            "external_scraping_enabled", "database_persistence_enabled",
            "real_restore_enabled", "real_execution_enabled",
        ]:
            with self.subTest(boundary=key):
                self.assertFalse(boundaries[key])

    def test_workspace_control_center_pack_is_preview_only(self):
        payload = {
            "workspace_id": "workspace-control-center",
            "source": "manual_import",
            "output_language": "en",
            "products": [{
                "platform": "manual",
                "asin": "CONTROL001",
                "title": "Compact Travel Mug",
                "reviews": [{
                    "rating": 2,
                    "title": "Still leaks",
                    "text": "Leaks.",
                    "source_section": "manual_review",
                }],
            }],
        }
        response = self.client.post(
            "/api/v1/analyze-review-workspace", json=payload
        )
        self.assertEqual(response.status_code, 200)
        creative_pack = response.json()["creative_decision_pack"]
        for existing_pack in [
            "review_import_pack", "competitor_review_comparison_pack",
            "llm_assist_dry_run_pack",
            "video_provider_orchestration_dry_run_pack",
            "campaign_export_pack", "workspace_session_snapshot_pack",
            "workspace_run_compare_pack", "workspace_action_queue_pack",
            "workspace_action_ticket_pack",
            "workspace_approval_decision_pack",
            "workspace_execution_readiness_pack",
            "workspace_execution_rehearsal_pack",
            "workspace_rehearsal_result_pack",
            "workspace_rehearsal_remediation_pack",
            "workspace_remediation_verification_pack",
            "workspace_retry_rehearsal_plan_pack",
            "workspace_retry_rehearsal_result_pack",
            "workspace_retry_cycle_decision_pack",
            "workspace_cycle_history_timeline_pack",
            "workspace_control_center_pack",
        ]:
            with self.subTest(existing_pack=existing_pack):
                self.assertIn(existing_pack, creative_pack)

        cycle_pack = creative_pack["workspace_retry_cycle_decision_pack"]
        timeline_pack = creative_pack["workspace_cycle_history_timeline_pack"]
        pack = creative_pack["workspace_control_center_pack"]
        self.assertEqual(
            pack["pack_version"],
            "workspace_control_center_pack_v1",
        )
        summary = pack["control_center_summary"]
        self.assertTrue(summary["control_center_id"])
        self.assertIn("operator_cockpit_preview", summary["mode"])
        self.assertIn("control_center_preview", summary["mode"])
        self.assertIn("dry_run_only", summary["mode"])
        self.assertFalse(summary["real_execution_allowed"])

        cards = pack["system_status_cards"]
        self.assertGreaterEqual(len(cards), 2)
        for card in cards:
            for field in [
                "card_id", "card_type", "card_title",
                "source_pack", "status",
            ]:
                with self.subTest(card=card["card_id"], field=field):
                    self.assertTrue(card[field])
            self.assertIn("recommended_operator_action", card)
            self.assertFalse(card["real_execution_allowed"])

        queue = pack["operator_priority_queue"]
        self.assertTrue(queue)
        for item in queue:
            for field in [
                "queue_id", "priority", "source_pack",
                "next_action_preview",
            ]:
                with self.subTest(queue=item["queue_id"], field=field):
                    self.assertTrue(item[field])
            self.assertIn("blocked_by", item)
            self.assertTrue(item["required_review"])
            self.assertFalse(item["real_execution_allowed"])

        snapshot = pack["current_decision_snapshot"]
        self.assertTrue(snapshot)
        self.assertEqual(
            snapshot["source_retry_cycle_decision_id"],
            cycle_pack["cycle_decision_summary"]["cycle_decision_id"],
        )
        self.assertEqual(
            snapshot["source_timeline_id"],
            timeline_pack["timeline_summary"]["timeline_id"],
        )
        self.assertEqual(
            snapshot["recommended_cycle_action"]["action_type"],
            cycle_pack["recommended_cycle_action"]["action_type"],
        )
        self.assertFalse(snapshot["real_execution_allowed"])

        next_actions = pack["next_best_actions"]
        self.assertTrue(next_actions)
        self.assertTrue(
            all(action["preview_action_only"] for action in next_actions)
        )
        self.assertTrue(
            all(not action["real_execution_allowed"] for action in next_actions)
        )

        risk = pack["risk_and_blocker_overview"]
        self.assertTrue(risk)
        self.assertTrue(risk["safety_lock_active"])
        self.assertFalse(risk["real_execution_allowed"])
        self.assertIsInstance(risk["unresolved_blockers"], list)

        inventory = pack["pack_readiness_inventory"]
        inventory_by_name = {item["pack_name"]: item for item in inventory}
        for pack_name in [
            "workspace_execution_readiness_pack",
            "workspace_execution_rehearsal_pack",
            "workspace_rehearsal_result_pack",
            "workspace_rehearsal_remediation_pack",
            "workspace_remediation_verification_pack",
            "workspace_retry_rehearsal_plan_pack",
            "workspace_retry_rehearsal_result_pack",
            "workspace_retry_cycle_decision_pack",
            "workspace_cycle_history_timeline_pack",
        ]:
            with self.subTest(inventory_pack=pack_name):
                self.assertIn(pack_name, inventory_by_name)
                self.assertIn("present", inventory_by_name[pack_name])
                self.assertEqual(
                    inventory_by_name[pack_name]["source"],
                    "creative_decision_pack",
                )
                self.assertFalse(
                    inventory_by_name[pack_name]["real_execution_allowed"]
                )

        lock = pack["capability_lock_status"]
        self.assertTrue(lock["all_real_capabilities_disabled"])
        self.assertFalse(lock["real_execution_allowed"])
        for capability in [
            "provider", "llm", "video", "media", "paid", "registry",
            "rollback", "external_scraping", "database_persistence",
            "real_restore", "real_execution",
        ]:
            with self.subTest(capability=capability):
                self.assertFalse(lock["capabilities"][capability])

        checks = pack["control_quality_checks"]
        for key in [
            "all_required_packs_have_inventory_status",
            "system_status_cards_present",
            "all_cards_execution_disabled",
            "operator_priority_queue_present",
            "all_queue_items_execution_disabled",
            "current_decision_references_retry_cycle_or_timeline",
            "next_best_actions_preview_only",
            "capability_lock_status_all_disabled",
            "audit_preview_not_persisted",
        ]:
            with self.subTest(check=key):
                self.assertTrue(checks[key])
        for key in [
            "database_write_performed", "operator_task_created",
            "real_history_table_read_performed", "real_execution_performed",
        ]:
            with self.subTest(check=key):
                self.assertFalse(checks[key])

        audit = pack["audit_preview"]
        self.assertTrue(audit["control_center_id"])
        self.assertFalse(audit["is_real_control_center"])
        self.assertFalse(audit["database_write_performed"])
        self.assertFalse(audit["operator_task_created"])
        self.assertFalse(audit["real_history_table_read_performed"])
        self.assertFalse(audit["audit_persisted"])

        boundaries = pack["safety_boundaries"]
        for key in [
            "provider_calls_enabled", "llm_api_enabled",
            "video_generation_enabled", "media_upload_enabled",
            "media_download_enabled", "paid_operation_enabled",
            "registry_write_enabled", "rollback_enabled",
            "external_scraping_enabled", "database_persistence_enabled",
            "real_restore_enabled", "real_execution_enabled",
        ]:
            with self.subTest(boundary=key):
                self.assertFalse(boundaries[key])

    def test_workspace_agent_run_ledger_pack_is_preview_only(self):
        payload = {
            "workspace_id": "workspace-agent-run-ledger",
            "source": "manual_import",
            "output_language": "en",
            "products": [{
                "platform": "manual",
                "asin": "LEDGER001",
                "title": "Compact Travel Mug",
                "reviews": [{
                    "rating": 2,
                    "title": "Still leaks",
                    "text": "Leaks.",
                    "source_section": "manual_review",
                }],
            }],
        }
        response = self.client.post(
            "/api/v1/analyze-review-workspace", json=payload
        )
        self.assertEqual(response.status_code, 200)
        creative_pack = response.json()["creative_decision_pack"]
        for existing_pack in [
            "review_import_pack", "competitor_review_comparison_pack",
            "llm_assist_dry_run_pack",
            "video_provider_orchestration_dry_run_pack",
            "campaign_export_pack", "workspace_session_snapshot_pack",
            "workspace_run_compare_pack", "workspace_action_queue_pack",
            "workspace_action_ticket_pack",
            "workspace_approval_decision_pack",
            "workspace_execution_readiness_pack",
            "workspace_execution_rehearsal_pack",
            "workspace_rehearsal_result_pack",
            "workspace_rehearsal_remediation_pack",
            "workspace_remediation_verification_pack",
            "workspace_retry_rehearsal_plan_pack",
            "workspace_retry_rehearsal_result_pack",
            "workspace_retry_cycle_decision_pack",
            "workspace_cycle_history_timeline_pack",
            "workspace_control_center_pack",
            "workspace_agent_run_ledger_pack",
        ]:
            with self.subTest(existing_pack=existing_pack):
                self.assertIn(existing_pack, creative_pack)

        control_pack = creative_pack["workspace_control_center_pack"]
        pack = creative_pack["workspace_agent_run_ledger_pack"]
        self.assertEqual(
            pack["pack_version"],
            "workspace_agent_run_ledger_pack_v1",
        )
        summary = pack["ledger_summary"]
        self.assertTrue(summary["ledger_id"])
        self.assertIn("agent_run_ledger_preview", summary["mode"])
        self.assertIn("traceability_preview", summary["mode"])
        self.assertIn("dry_run_only", summary["mode"])
        self.assertEqual(
            summary["source_control_center_id"],
            control_pack["control_center_summary"]["control_center_id"],
        )
        self.assertFalse(summary["real_execution_allowed"])

        cards = pack["agent_run_cards"]
        self.assertGreaterEqual(len(cards), 2)
        roles = {card["agent_role"] for card in cards}
        for expected_role in [
            "creative_decision_agent",
            "readiness_gate_agent",
            "rehearsal_planner_agent",
            "operator_review_agent",
            "remediation_agent",
            "verification_agent",
            "retry_control_agent",
            "timeline_agent",
            "control_center_agent",
        ]:
            with self.subTest(agent_role=expected_role):
                self.assertIn(expected_role, roles)
        for card in cards:
            for field in [
                "run_id", "agent_role", "workflow_phase",
                "source_pack", "status",
            ]:
                with self.subTest(card=card["run_id"], field=field):
                    self.assertTrue(card[field])
            self.assertIsInstance(card["input_refs"], list)
            self.assertIsInstance(card["output_refs"], list)
            self.assertIsInstance(card["handoff_to"], list)
            self.assertIsInstance(card["evidence_refs"], list)
            self.assertIsInstance(card["decision_refs"], list)
            self.assertIn("preview", card["capability_mode"])
            self.assertFalse(card["real_execution_allowed"])

        handoffs = pack["handoff_trace"]
        self.assertGreaterEqual(len(handoffs), 2)
        for handoff in handoffs:
            for field in [
                "handoff_id", "from_agent", "to_agent",
                "from_pack", "to_pack",
            ]:
                with self.subTest(handoff=handoff["handoff_id"], field=field):
                    self.assertTrue(handoff[field])
            self.assertIsInstance(handoff["input_refs"], list)
            self.assertIsInstance(handoff["output_refs"], list)
            self.assertIsInstance(handoff["blocked_by"], list)
            self.assertFalse(handoff["real_execution_allowed"])

        io_trace = pack["input_output_trace_map"]
        self.assertTrue(io_trace)
        for pack_name in [
            "creative_decision_pack",
            "workspace_execution_readiness_pack",
            "workspace_execution_rehearsal_pack",
            "workspace_rehearsal_result_pack",
            "workspace_rehearsal_remediation_pack",
            "workspace_remediation_verification_pack",
            "workspace_retry_rehearsal_plan_pack",
            "workspace_retry_rehearsal_result_pack",
            "workspace_retry_cycle_decision_pack",
            "workspace_cycle_history_timeline_pack",
            "workspace_control_center_pack",
        ]:
            with self.subTest(io_pack=pack_name):
                self.assertIn(pack_name, io_trace)
                self.assertIsInstance(io_trace[pack_name]["input_refs"], list)
                self.assertIsInstance(io_trace[pack_name]["output_refs"], list)
                self.assertFalse(io_trace[pack_name]["real_execution_allowed"])

        evidence_trace = pack["evidence_trace"]
        self.assertIsInstance(evidence_trace, list)
        self.assertTrue(evidence_trace)
        self.assertTrue(
            all(not trace["real_execution_allowed"] for trace in evidence_trace)
        )

        decision_trace = pack["decision_trace"]
        self.assertTrue(decision_trace)
        self.assertTrue(
            all(
                not trace["real_execution_allowed"]
                for trace in decision_trace
            )
        )
        self.assertTrue(
            any(
                trace["source_pack"] == "workspace_retry_cycle_decision_pack"
                for trace in decision_trace
            )
        )

        capabilities = pack["capability_usage_preview"]
        self.assertTrue(capabilities)
        capability_by_name = {item["capability"]: item for item in capabilities}
        for capability in [
            "provider", "llm", "video", "media", "paid", "registry",
            "rollback", "external_scraping", "database_persistence",
            "real_restore", "real_execution", "agent_runtime",
            "real_log_read", "operator_task",
        ]:
            with self.subTest(capability=capability):
                self.assertIn(capability, capability_by_name)
                self.assertIn(
                    "preview",
                    capability_by_name[capability]["usage_mode"],
                )
                self.assertFalse(
                    capability_by_name[capability]["real_capability_enabled"]
                )
                self.assertFalse(
                    capability_by_name[capability]["real_execution_allowed"]
                )

        checks = pack["ledger_quality_checks"]
        for key in [
            "agent_run_cards_present",
            "all_cards_execution_disabled",
            "handoff_trace_present",
            "all_handoffs_execution_disabled",
            "input_output_trace_map_present",
            "evidence_trace_present_or_empty_state",
            "decision_trace_present",
            "all_capabilities_preview_only",
            "audit_preview_not_persisted",
        ]:
            with self.subTest(check=key):
                self.assertTrue(checks[key])
        for key in [
            "database_write_performed", "real_log_read_performed",
            "real_history_table_read_performed", "agent_runtime_invoked",
            "operator_task_created", "real_execution_performed",
        ]:
            with self.subTest(check=key):
                self.assertFalse(checks[key])

        audit = pack["audit_preview"]
        self.assertTrue(audit["ledger_id"])
        self.assertFalse(audit["is_real_agent_runtime_log"])
        self.assertFalse(audit["real_log_read_performed"])
        self.assertFalse(audit["real_history_table_read_performed"])
        self.assertFalse(audit["database_write_performed"])
        self.assertFalse(audit["operator_task_created"])
        self.assertFalse(audit["audit_persisted"])

        boundaries = pack["safety_boundaries"]
        for key in [
            "provider_calls_enabled", "llm_api_enabled",
            "video_generation_enabled", "media_upload_enabled",
            "media_download_enabled", "paid_operation_enabled",
            "registry_write_enabled", "rollback_enabled",
            "external_scraping_enabled", "database_persistence_enabled",
            "real_restore_enabled", "real_execution_enabled",
        ]:
            with self.subTest(boundary=key):
                self.assertFalse(boundaries[key])

    def test_workspace_human_review_queue_pack_is_preview_only(self):
        payload = {
            "workspace_id": "workspace-human-review-queue",
            "source": "manual_import",
            "output_language": "en",
            "products": [{
                "platform": "manual",
                "asin": "REVIEWQUEUE001",
                "title": "Compact Travel Mug",
                "reviews": [{
                    "rating": 2,
                    "title": "Still leaks",
                    "text": "Leaks.",
                    "source_section": "manual_review",
                }],
            }],
        }
        response = self.client.post(
            "/api/v1/analyze-review-workspace", json=payload
        )
        self.assertEqual(response.status_code, 200)
        creative_pack = response.json()["creative_decision_pack"]
        for existing_pack in [
            "review_import_pack", "competitor_review_comparison_pack",
            "llm_assist_dry_run_pack",
            "video_provider_orchestration_dry_run_pack",
            "campaign_export_pack", "workspace_session_snapshot_pack",
            "workspace_run_compare_pack", "workspace_action_queue_pack",
            "workspace_action_ticket_pack",
            "workspace_approval_decision_pack",
            "workspace_execution_readiness_pack",
            "workspace_execution_rehearsal_pack",
            "workspace_rehearsal_result_pack",
            "workspace_rehearsal_remediation_pack",
            "workspace_remediation_verification_pack",
            "workspace_retry_rehearsal_plan_pack",
            "workspace_retry_rehearsal_result_pack",
            "workspace_retry_cycle_decision_pack",
            "workspace_cycle_history_timeline_pack",
            "workspace_control_center_pack",
            "workspace_agent_run_ledger_pack",
            "workspace_human_review_queue_pack",
        ]:
            with self.subTest(existing_pack=existing_pack):
                self.assertIn(existing_pack, creative_pack)

        control_pack = creative_pack["workspace_control_center_pack"]
        ledger_pack = creative_pack["workspace_agent_run_ledger_pack"]
        pack = creative_pack["workspace_human_review_queue_pack"]
        self.assertEqual(
            pack["pack_version"],
            "workspace_human_review_queue_pack_v1",
        )
        summary = pack["review_queue_summary"]
        self.assertTrue(summary["queue_id"])
        self.assertIn("human_review_queue_preview", summary["mode"])
        self.assertIn("operator_task_preview", summary["mode"])
        self.assertIn("dry_run_only", summary["mode"])
        self.assertEqual(
            summary["source_control_center_id"],
            control_pack["control_center_summary"]["control_center_id"],
        )
        self.assertEqual(
            summary["source_agent_run_ledger_id"],
            ledger_pack["ledger_summary"]["ledger_id"],
        )
        self.assertFalse(summary["real_execution_allowed"])

        review_items = pack["review_queue_items"]
        self.assertGreaterEqual(len(review_items), 2)
        review_types = {item["review_type"] for item in review_items}
        self.assertTrue(
            review_types.intersection({
                "evidence_gap_review",
                "manual_approval_review",
                "risk_blocker_review",
                "retry_cycle_review",
                "capability_lock_review",
                "operator_signoff_review",
            })
        )
        for item in review_items:
            for field in [
                "review_id", "priority", "review_type",
                "source_pack", "why_review_is_needed",
            ]:
                with self.subTest(review=item["review_id"], field=field):
                    self.assertTrue(item[field])
            self.assertIsInstance(item["source_refs"], list)
            self.assertIsInstance(item["required_inputs"], list)
            self.assertIsInstance(item["blocked_by"], list)
            self.assertTrue(item["operator_decision_needed"])
            self.assertIn("allowed_decisions", item)
            self.assertFalse(item["real_execution_allowed"])

        task_cards = pack["operator_task_cards"]
        self.assertTrue(task_cards)
        review_ids = {item["review_id"] for item in review_items}
        for card in task_cards:
            for field in [
                "task_id", "task_type", "source_review_id",
                "task_status",
            ]:
                with self.subTest(task=card["task_id"], field=field):
                    self.assertTrue(card[field])
            self.assertIn(card["source_review_id"], review_ids)
            self.assertEqual(card["assignee_role"], "human_operator_reviewer")
            self.assertTrue(card["required_review"])
            self.assertIsInstance(card["completion_criteria"], list)
            self.assertIsInstance(card["blocked_by"], list)
            self.assertFalse(card["real_execution_allowed"])

        self.assertTrue(pack["review_priority_rationale"])
        inputs = pack["required_inputs_overview"]
        self.assertIn("required_inputs", inputs)
        self.assertFalse(inputs["real_execution_allowed"])

        blocked_items = pack["blocked_review_items"]
        self.assertIsInstance(blocked_items, list)
        self.assertTrue(blocked_items)
        self.assertTrue(
            all(not item["real_execution_allowed"] for item in blocked_items)
        )

        dependency_map = pack["review_dependency_map"]
        self.assertTrue(dependency_map)
        for item in review_items:
            with self.subTest(dependency=item["review_id"]):
                self.assertIn(item["review_id"], dependency_map)
                self.assertEqual(
                    dependency_map[item["review_id"]]["source_pack"],
                    item["source_pack"],
                )
                self.assertFalse(
                    dependency_map[item["review_id"]]["real_execution_allowed"]
                )

        decision_options = pack["operator_decision_options"]
        self.assertTrue(decision_options)
        labels = " ".join(
            option["decision_label"] + " " + option["decision_scope"]
            for option in decision_options
        )
        self.assertNotIn("real execution approval", labels.lower())
        self.assertNotIn("approved_for_real_execution", labels.lower())
        self.assertNotIn("real_execution_approval", labels.lower())
        for option in decision_options:
            self.assertFalse(option["creates_real_approval"])
            self.assertFalse(option["real_execution_allowed"])

        checks = pack["review_quality_checks"]
        for key in [
            "control_center_pack_present",
            "agent_run_ledger_pack_present",
            "review_queue_items_present",
            "operator_task_cards_present",
            "all_review_items_execution_disabled",
            "all_task_cards_execution_disabled",
            "blocked_review_items_present_or_empty_state",
            "dependency_map_present",
            "operator_decision_options_preview_only",
            "audit_preview_not_persisted",
        ]:
            with self.subTest(check=key):
                self.assertTrue(checks[key])
        for key in [
            "database_write_performed", "real_log_read_performed",
            "real_history_table_read_performed", "agent_runtime_invoked",
            "operator_task_created", "real_approval_created",
            "real_execution_performed",
        ]:
            with self.subTest(check=key):
                self.assertFalse(checks[key])

        audit = pack["audit_preview"]
        self.assertTrue(audit["queue_id"])
        self.assertFalse(audit["is_real_human_review_system"])
        self.assertFalse(audit["database_write_performed"])
        self.assertFalse(audit["operator_task_created"])
        self.assertFalse(audit["real_approval_created"])
        self.assertFalse(audit["real_log_read_performed"])
        self.assertFalse(audit["real_history_table_read_performed"])
        self.assertFalse(audit["audit_persisted"])

        boundaries = pack["safety_boundaries"]
        for key in [
            "provider_calls_enabled", "llm_api_enabled",
            "video_generation_enabled", "media_upload_enabled",
            "media_download_enabled", "paid_operation_enabled",
            "registry_write_enabled", "rollback_enabled",
            "external_scraping_enabled", "database_persistence_enabled",
            "real_restore_enabled", "real_execution_enabled",
        ]:
            with self.subTest(boundary=key):
                self.assertFalse(boundaries[key])

    def test_workspace_capability_permission_matrix_pack_is_preview_only(self):
        payload = {
            "workspace_id": "workspace-capability-permission-matrix",
            "source": "manual_import",
            "output_language": "en",
            "products": [{
                "platform": "manual",
                "asin": "PERMISSION001",
                "title": "Compact Travel Mug",
                "reviews": [{
                    "rating": 2,
                    "title": "Leaks during commute",
                    "text": "Leaks.",
                    "source_section": "manual_review",
                }],
            }],
        }
        response = self.client.post(
            "/api/v1/analyze-review-workspace", json=payload
        )
        self.assertEqual(response.status_code, 200)
        creative_pack = response.json()["creative_decision_pack"]
        for existing_pack in [
            "review_import_pack", "competitor_review_comparison_pack",
            "llm_assist_dry_run_pack",
            "video_provider_orchestration_dry_run_pack",
            "campaign_export_pack", "workspace_session_snapshot_pack",
            "workspace_run_compare_pack", "workspace_action_queue_pack",
            "workspace_action_ticket_pack",
            "workspace_approval_decision_pack",
            "workspace_execution_readiness_pack",
            "workspace_execution_rehearsal_pack",
            "workspace_rehearsal_result_pack",
            "workspace_rehearsal_remediation_pack",
            "workspace_remediation_verification_pack",
            "workspace_retry_rehearsal_plan_pack",
            "workspace_retry_rehearsal_result_pack",
            "workspace_retry_cycle_decision_pack",
            "workspace_cycle_history_timeline_pack",
            "workspace_control_center_pack",
            "workspace_agent_run_ledger_pack",
            "workspace_human_review_queue_pack",
            "workspace_capability_permission_matrix_pack",
        ]:
            with self.subTest(existing_pack=existing_pack):
                self.assertIn(existing_pack, creative_pack)

        pack = creative_pack["workspace_capability_permission_matrix_pack"]
        self.assertEqual(
            pack["pack_version"],
            "workspace_capability_permission_matrix_pack_v1",
        )
        summary = pack["permission_matrix_summary"]
        self.assertTrue(summary["matrix_id"])
        self.assertIn("permission_matrix_preview", summary["mode"])
        self.assertIn("policy_gate_preview", summary["mode"])
        self.assertIn("dry_run_only", summary["mode"])
        self.assertFalse(summary["real_execution_allowed"])

        required_capabilities = {
            "llm_generation", "video_provider", "media_upload",
            "media_download", "paid_operation", "provider_registry",
            "rollback_restore", "external_scraping",
            "database_persistence", "real_execution", "human_approval",
            "operator_task_creation", "secret_access",
        }
        cards = pack["capability_permission_cards"]
        self.assertEqual(
            {card["capability_id"] for card in cards},
            required_capabilities,
        )
        for card in cards:
            for field in [
                "capability_id", "current_status", "permission_level",
                "allowed_modes", "disallowed_modes",
            ]:
                with self.subTest(
                    capability=card["capability_id"], field=field
                ):
                    self.assertTrue(card[field])
            self.assertIn(card["current_status"], {
                "disabled_preview_only",
                "policy_violation_blocked",
            })
            self.assertIn("preview", card["allowed_modes"])
            self.assertIn("dry_run", card["allowed_modes"])
            self.assertIn("real_execution", card["disallowed_modes"])
            self.assertFalse(card["real_execution_allowed"])
            self.assertNotIn("granted", card["permission_level"].lower())

        gates = pack["policy_gate_results"]
        self.assertTrue(gates)
        self.assertEqual(
            {gate["capability_id"] for gate in gates},
            required_capabilities,
        )
        for gate in gates:
            for field in [
                "gate_id", "capability_id", "gate_status", "gate_reason",
            ]:
                with self.subTest(gate=gate["gate_id"], field=field):
                    self.assertTrue(gate[field])
            self.assertIn("preview", gate["gate_status"])
            self.assertFalse(gate["real_execution_allowed"])
            self.assertNotIn("approved_for_real_execution", str(gate).lower())

        unlock_requirements = pack["unlock_requirements"]
        self.assertTrue(unlock_requirements)
        for requirement in unlock_requirements:
            self.assertFalse(requirement["unlocks_real_capability_now"])
            self.assertFalse(requirement["real_execution_allowed"])

        denied = pack["denied_capability_reasons"]
        self.assertEqual(
            {item["capability_id"] for item in denied},
            required_capabilities,
        )
        self.assertTrue(all(not item["real_execution_allowed"] for item in denied))

        human_approval = pack["human_approval_requirements"]
        self.assertIn("preview_only", human_approval["mode"])
        self.assertFalse(human_approval["creates_real_approval"])
        self.assertFalse(human_approval["real_execution_allowed"])

        dependency_map = pack["capability_dependency_map"]
        self.assertEqual(set(dependency_map), required_capabilities)
        for capability_id, dependency in dependency_map.items():
            with self.subTest(dependency=capability_id):
                self.assertIn("source_pack", dependency)
                self.assertIn("depends_on_reviews", dependency)
                self.assertIn("depends_on_gates", dependency)
                self.assertIn("depends_on_evidence", dependency)
                self.assertFalse(dependency["real_execution_allowed"])

        checks = pack["permission_quality_checks"]
        for key in [
            "control_center_pack_present",
            "human_review_queue_pack_present",
            "agent_run_ledger_pack_present",
            "retry_cycle_decision_pack_present",
            "execution_readiness_pack_present",
            "cycle_history_timeline_pack_present",
            "all_required_capabilities_present",
            "all_capabilities_execution_disabled",
            "all_policy_gates_execution_disabled",
            "unlock_requirements_do_not_unlock_now",
            "human_approval_preview_only",
            "audit_preview_not_persisted",
        ]:
            with self.subTest(check=key):
                self.assertTrue(checks[key])
        for key in [
            "database_write_performed", "real_secret_read_performed",
            "real_log_read_performed", "real_history_table_read_performed",
            "operator_task_created", "real_approval_created",
            "permission_granted_for_real_execution",
            "real_execution_performed",
        ]:
            with self.subTest(check=key):
                self.assertFalse(checks[key])

        audit = pack["audit_preview"]
        self.assertTrue(audit["matrix_id"])
        self.assertFalse(audit["is_real_permission_system"])
        self.assertFalse(audit["database_write_performed"])
        self.assertFalse(audit["secret_read_performed"])
        self.assertFalse(audit["real_log_read_performed"])
        self.assertFalse(audit["real_history_table_read_performed"])
        self.assertFalse(audit["operator_task_created"])
        self.assertFalse(audit["real_approval_created"])
        self.assertFalse(audit["audit_persisted"])

        boundaries = pack["safety_boundaries"]
        for key in [
            "provider_calls_enabled", "llm_api_enabled",
            "video_generation_enabled", "media_upload_enabled",
            "media_download_enabled", "paid_operation_enabled",
            "registry_write_enabled", "rollback_enabled",
            "external_scraping_enabled", "database_persistence_enabled",
            "real_restore_enabled", "real_execution_enabled",
        ]:
            with self.subTest(boundary=key):
                self.assertFalse(boundaries[key])

    def test_workspace_system_integration_health_pack_is_preview_only(self):
        payload = {
            "workspace_id": "workspace-system-integration-health",
            "source": "manual_import",
            "output_language": "en",
            "products": [{
                "platform": "manual",
                "asin": "HEALTH001",
                "title": "Compact Travel Mug",
                "reviews": [{
                    "rating": 2,
                    "title": "Leaks during commute",
                    "text": "Leaks.",
                    "source_section": "manual_review",
                }],
            }],
        }
        response = self.client.post(
            "/api/v1/analyze-review-workspace", json=payload
        )
        self.assertEqual(response.status_code, 200)
        creative_pack = response.json()["creative_decision_pack"]
        for existing_pack in [
            "review_import_pack", "competitor_review_comparison_pack",
            "llm_assist_dry_run_pack",
            "video_provider_orchestration_dry_run_pack",
            "campaign_export_pack", "workspace_session_snapshot_pack",
            "workspace_run_compare_pack", "workspace_action_queue_pack",
            "workspace_action_ticket_pack",
            "workspace_approval_decision_pack",
            "workspace_execution_readiness_pack",
            "workspace_execution_rehearsal_pack",
            "workspace_rehearsal_result_pack",
            "workspace_rehearsal_remediation_pack",
            "workspace_remediation_verification_pack",
            "workspace_retry_rehearsal_plan_pack",
            "workspace_retry_rehearsal_result_pack",
            "workspace_retry_cycle_decision_pack",
            "workspace_cycle_history_timeline_pack",
            "workspace_control_center_pack",
            "workspace_agent_run_ledger_pack",
            "workspace_human_review_queue_pack",
            "workspace_capability_permission_matrix_pack",
            "workspace_system_integration_health_pack",
        ]:
            with self.subTest(existing_pack=existing_pack):
                self.assertIn(existing_pack, creative_pack)

        pack = creative_pack["workspace_system_integration_health_pack"]
        self.assertEqual(
            pack["pack_version"],
            "workspace_system_integration_health_pack_v1",
        )
        summary = pack["integration_health_summary"]
        self.assertTrue(summary["health_id"])
        self.assertIn("integration_health_preview", summary["mode"])
        self.assertIn("readiness_overview", summary["mode"])
        self.assertIn("dry_run_only", summary["mode"])
        self.assertFalse(summary["real_execution_allowed"])

        cards = pack["pack_health_cards"]
        self.assertGreaterEqual(len(cards), 4)
        for card in cards:
            for field in [
                "pack_id", "source_pack", "health_status", "present",
            ]:
                with self.subTest(pack_card=card["pack_id"], field=field):
                    self.assertIn(field, card)
            self.assertIn("ready_for_review", card)
            self.assertIsInstance(card["missing_or_weak_fields"], list)
            self.assertIsInstance(card["upstream_dependencies"], list)
            self.assertIsInstance(card["downstream_consumers"], list)
            self.assertFalse(card["real_execution_allowed"])

        workflow = pack["workflow_chain_health"]
        self.assertTrue(workflow)
        for key in [
            "evidence", "decision", "readiness", "rehearsal",
            "remediation", "retry", "control_center", "permission_matrix",
        ]:
            with self.subTest(chain=key):
                self.assertIn(key, workflow["chain_components"])
        self.assertFalse(workflow["real_execution_allowed"])

        gate = pack["gate_health_overview"]
        self.assertTrue(gate)
        self.assertFalse(gate["is_real_execution_gate"])
        self.assertFalse(gate["launch_lock"]["real_execution_allowed"])
        self.assertFalse(gate["cycle_gate"]["real_execution_allowed"])
        self.assertFalse(gate["policy_gate"]["real_execution_allowed"])
        self.assertFalse(gate["human_review_gate"]["real_execution_allowed"])

        traceability = pack["traceability_health"]
        self.assertTrue(traceability["agent_run_ledger_present"])
        self.assertTrue(traceability["cycle_history_timeline_present"])
        self.assertFalse(traceability["real_log_read_performed"])
        self.assertFalse(traceability["real_history_table_read_performed"])
        self.assertFalse(traceability["real_execution_allowed"])

        operator = pack["operator_readiness_overview"]
        self.assertTrue(operator["human_review_queue_present"])
        self.assertTrue(operator["control_center_present"])
        self.assertFalse(operator["operator_task_created"])
        self.assertFalse(operator["real_execution_allowed"])

        capability_health = pack["capability_lock_health"]
        self.assertEqual(capability_health["capability_count"], 13)
        self.assertTrue(
            capability_health["all_capabilities_disabled_or_preview_only"]
        )
        for capability_id, capability in capability_health["capabilities"].items():
            with self.subTest(capability=capability_id):
                status_text = (
                    capability["current_status"]
                    + " "
                    + capability["permission_level"]
                    + " "
                    + " ".join(capability["allowed_modes"])
                )
                self.assertTrue(
                    any(
                        token in status_text
                        for token in ["disabled", "preview", "dry"]
                    )
                )
                self.assertFalse(capability["real_execution_allowed"])

        risks = pack["integration_risk_register"]
        self.assertIsInstance(risks, list)
        self.assertTrue(risks)
        risk_types = {risk["risk_type"] for risk in risks}
        self.assertTrue(
            risk_types.intersection({
                "blocked", "missing_input", "weak_evidence",
                "locked_capability", "review_required",
            })
        )
        for risk in risks:
            for field in [
                "risk_id", "risk_type", "source_pack", "risk_title",
                "risk_detail", "severity", "blocked_by",
                "recommended_operator_action",
            ]:
                with self.subTest(risk=risk["risk_id"], field=field):
                    self.assertIn(field, risk)
            self.assertFalse(risk["real_execution_allowed"])

        checks = pack["health_quality_checks"]
        for key in [
            "pack_health_cards_present",
            "workflow_chain_health_present",
            "gate_health_overview_present",
            "gate_health_is_not_real_execution_gate",
            "traceability_health_present",
            "traceability_uses_preview_packs_only",
            "operator_readiness_overview_present",
            "capability_lock_health_present",
            "all_capabilities_execution_disabled",
            "integration_risk_register_present_or_empty_state",
            "audit_preview_not_persisted",
        ]:
            with self.subTest(check=key):
                self.assertTrue(checks[key])
        for key in [
            "real_service_health_read_performed",
            "database_write_performed", "real_log_read_performed",
            "real_history_table_read_performed", "operator_task_created",
            "real_approval_created", "real_execution_performed",
        ]:
            with self.subTest(check=key):
                self.assertFalse(checks[key])

        audit = pack["audit_preview"]
        self.assertTrue(audit["health_id"])
        self.assertFalse(audit["is_real_monitoring_system"])
        self.assertFalse(audit["real_service_health_read_performed"])
        self.assertFalse(audit["database_write_performed"])
        self.assertFalse(audit["real_log_read_performed"])
        self.assertFalse(audit["real_history_table_read_performed"])
        self.assertFalse(audit["operator_task_created"])
        self.assertFalse(audit["real_approval_created"])
        self.assertFalse(audit["audit_persisted"])

        boundaries = pack["safety_boundaries"]
        for key in [
            "provider_calls_enabled", "llm_api_enabled",
            "video_generation_enabled", "media_upload_enabled",
            "media_download_enabled", "paid_operation_enabled",
            "registry_write_enabled", "rollback_enabled",
            "external_scraping_enabled", "database_persistence_enabled",
            "real_restore_enabled", "real_execution_enabled",
        ]:
            with self.subTest(boundary=key):
                self.assertFalse(boundaries[key])

    def test_workspace_replay_harness_pack_is_preview_only(self):
        payload = {
            "workspace_id": "workspace-replay-harness",
            "source": "manual_import",
            "output_language": "en",
            "products": [{
                "platform": "manual",
                "asin": "REPLAY001",
                "title": "Compact Travel Mug",
                "reviews": [{
                    "rating": 2,
                    "title": "Leaks during commute",
                    "text": "Leaks.",
                    "source_section": "manual_review",
                }],
            }],
        }
        response = self.client.post(
            "/api/v1/analyze-review-workspace", json=payload
        )
        self.assertEqual(response.status_code, 200)
        creative_pack = response.json()["creative_decision_pack"]
        for existing_pack in [
            "review_import_pack", "competitor_review_comparison_pack",
            "llm_assist_dry_run_pack",
            "video_provider_orchestration_dry_run_pack",
            "campaign_export_pack", "workspace_session_snapshot_pack",
            "workspace_run_compare_pack", "workspace_action_queue_pack",
            "workspace_action_ticket_pack",
            "workspace_approval_decision_pack",
            "workspace_execution_readiness_pack",
            "workspace_execution_rehearsal_pack",
            "workspace_rehearsal_result_pack",
            "workspace_rehearsal_remediation_pack",
            "workspace_remediation_verification_pack",
            "workspace_retry_rehearsal_plan_pack",
            "workspace_retry_rehearsal_result_pack",
            "workspace_retry_cycle_decision_pack",
            "workspace_cycle_history_timeline_pack",
            "workspace_control_center_pack",
            "workspace_agent_run_ledger_pack",
            "workspace_human_review_queue_pack",
            "workspace_capability_permission_matrix_pack",
            "workspace_system_integration_health_pack",
            "workspace_replay_harness_pack",
        ]:
            with self.subTest(existing_pack=existing_pack):
                self.assertIn(existing_pack, creative_pack)

        pack = creative_pack["workspace_replay_harness_pack"]
        self.assertEqual(
            pack["pack_version"],
            "workspace_replay_harness_pack_v1",
        )
        summary = pack["replay_harness_summary"]
        self.assertTrue(summary["harness_id"])
        self.assertIn("replay_harness_preview", summary["mode"])
        self.assertIn("regression_scenario_preview", summary["mode"])
        self.assertIn("dry_run_only", summary["mode"])
        self.assertFalse(summary["real_execution_allowed"])

        scenarios = pack["replay_scenarios"]
        self.assertGreaterEqual(len(scenarios), 2)
        scenario_types = {scenario["scenario_type"] for scenario in scenarios}
        for expected_type in [
            "pack_presence_replay", "decision_trace_replay",
            "safety_boundary_replay", "permission_gate_replay",
            "human_review_queue_replay", "integration_health_replay",
            "export_contract_replay", "i18n_visibility_replay",
        ]:
            with self.subTest(scenario_type=expected_type):
                self.assertIn(expected_type, scenario_types)
        for scenario in scenarios:
            for field in [
                "scenario_id", "scenario_type", "source_pack",
                "expected_status", "input_refs",
                "expected_pack_outputs", "regression_focus",
                "failure_signal",
            ]:
                with self.subTest(
                    scenario=scenario["scenario_id"], field=field
                ):
                    self.assertIn(field, scenario)
            self.assertFalse(scenario["real_execution_allowed"])

        contracts = pack["replay_input_contracts"]
        self.assertTrue(contracts)
        contract_sources = {contract["source_pack"] for contract in contracts}
        for source_pack in [
            "workspace_system_integration_health_pack",
            "workspace_capability_permission_matrix_pack",
            "workspace_human_review_queue_pack",
            "workspace_agent_run_ledger_pack",
            "workspace_control_center_pack",
            "workspace_cycle_history_timeline_pack",
            "workspace_retry_cycle_decision_pack",
            "workspace_execution_readiness_pack",
        ]:
            with self.subTest(contract=source_pack):
                self.assertIn(source_pack, contract_sources)
        for contract in contracts:
            self.assertIsInstance(contract["required_fields"], list)
            self.assertIsInstance(contract["missing_fields"], list)
            self.assertFalse(contract["database_read_required"])
            self.assertFalse(contract["real_history_table_read_required"])
            self.assertFalse(contract["real_log_read_required"])
            self.assertFalse(contract["real_service_health_read_required"])
            self.assertFalse(contract["real_execution_allowed"])

        snapshots = pack["expected_output_snapshots"]
        self.assertTrue(snapshots)
        for snapshot in snapshots:
            self.assertIn("preview", snapshot["snapshot_mode"])
            self.assertFalse(snapshot["file_write_performed"])
            self.assertFalse(snapshot["database_write_performed"])
            self.assertFalse(snapshot["real_execution_allowed"])

        checks = pack["regression_check_matrix"]
        self.assertGreaterEqual(len(checks), 2)
        for check in checks:
            for field in [
                "check_id", "source_pack", "target_pack",
                "expected_condition", "failure_condition",
                "suggested_fix_preview",
            ]:
                with self.subTest(check=check["check_id"], field=field):
                    self.assertIn(field, check)
            self.assertFalse(check["real_execution_allowed"])

        consistency = pack["pack_consistency_checks"]
        self.assertTrue(consistency)
        self.assertIn("source_packs_checked", consistency)
        self.assertFalse(consistency["database_read_performed"])
        self.assertFalse(consistency["real_history_table_read_performed"])
        self.assertFalse(consistency["real_log_read_performed"])
        self.assertFalse(consistency["real_service_health_read_performed"])
        self.assertFalse(consistency["real_execution_performed"])

        diff_plan = pack["replay_diff_plan"]
        self.assertIn("preview", diff_plan["mode"])
        self.assertFalse(diff_plan["diff_job_executed"])
        self.assertFalse(diff_plan["file_write_performed"])
        self.assertFalse(diff_plan["database_write_performed"])
        self.assertFalse(diff_plan["real_execution_allowed"])

        operator_notes = pack["operator_replay_notes"]
        self.assertTrue(operator_notes["review_required"])
        self.assertFalse(operator_notes["operator_task_created"])
        self.assertFalse(operator_notes["real_approval_created"])
        self.assertFalse(operator_notes["real_execution_allowed"])

        quality = pack["replay_quality_checks"]
        for key in [
            "replay_harness_summary_present",
            "replay_scenarios_present",
            "scenario_types_cover_required_set",
            "replay_input_contracts_present",
            "expected_output_snapshots_preview_only",
            "regression_check_matrix_present",
            "regression_checks_preview_only",
            "pack_consistency_checks_present",
            "audit_preview_not_persisted",
            "all_real_capabilities_disabled",
        ]:
            with self.subTest(quality=key):
                self.assertTrue(quality[key])
        for key in [
            "diff_job_executed", "real_replay_runtime_started",
            "monitoring_system_read_performed",
            "permission_system_write_performed",
            "human_approval_system_write_performed",
            "agent_runtime_started", "database_write_performed",
            "real_history_table_read_performed",
            "real_log_read_performed",
            "real_service_health_read_performed",
            "operator_task_created", "real_approval_created",
            "real_execution_performed",
        ]:
            with self.subTest(quality=key):
                self.assertFalse(quality[key])

        audit = pack["audit_preview"]
        self.assertTrue(audit["harness_id"])
        self.assertFalse(audit["is_real_replay_runtime"])
        self.assertFalse(audit["real_replay_runtime_started"])
        self.assertFalse(audit["monitoring_system_read_performed"])
        self.assertFalse(audit["database_write_performed"])
        self.assertFalse(audit["real_log_read_performed"])
        self.assertFalse(audit["real_history_table_read_performed"])
        self.assertFalse(audit["real_service_health_read_performed"])
        self.assertFalse(audit["operator_task_created"])
        self.assertFalse(audit["real_approval_created"])
        self.assertFalse(audit["audit_persisted"])

        boundaries = pack["safety_boundaries"]
        for key in [
            "provider_calls_enabled", "llm_api_enabled",
            "video_generation_enabled", "media_upload_enabled",
            "media_download_enabled", "paid_operation_enabled",
            "registry_write_enabled", "rollback_enabled",
            "external_scraping_enabled", "database_persistence_enabled",
            "real_restore_enabled", "real_execution_enabled",
        ]:
            with self.subTest(boundary=key):
                self.assertFalse(boundaries[key])

    def test_workspace_provider_adapter_contract_pack_is_preview_only(self):
        payload = {
            "workspace_id": "workspace-provider-adapter-contract",
            "source": "manual_import",
            "output_language": "en",
            "products": [{
                "platform": "manual",
                "asin": "PROVIDER001",
                "title": "Compact Travel Mug",
                "reviews": [{
                    "rating": 2,
                    "title": "Leaks during commute",
                    "text": "Leaks.",
                    "source_section": "manual_review",
                }],
            }],
        }
        response = self.client.post(
            "/api/v1/analyze-review-workspace", json=payload
        )
        self.assertEqual(response.status_code, 200)
        creative_pack = response.json()["creative_decision_pack"]
        for existing_pack in [
            "review_import_pack", "competitor_review_comparison_pack",
            "llm_assist_dry_run_pack",
            "video_provider_orchestration_dry_run_pack",
            "campaign_export_pack", "workspace_session_snapshot_pack",
            "workspace_run_compare_pack", "workspace_action_queue_pack",
            "workspace_action_ticket_pack",
            "workspace_approval_decision_pack",
            "workspace_execution_readiness_pack",
            "workspace_execution_rehearsal_pack",
            "workspace_rehearsal_result_pack",
            "workspace_rehearsal_remediation_pack",
            "workspace_remediation_verification_pack",
            "workspace_retry_rehearsal_plan_pack",
            "workspace_retry_rehearsal_result_pack",
            "workspace_retry_cycle_decision_pack",
            "workspace_cycle_history_timeline_pack",
            "workspace_control_center_pack",
            "workspace_agent_run_ledger_pack",
            "workspace_human_review_queue_pack",
            "workspace_capability_permission_matrix_pack",
            "workspace_system_integration_health_pack",
            "workspace_replay_harness_pack",
            "workspace_provider_adapter_contract_pack",
        ]:
            with self.subTest(existing_pack=existing_pack):
                self.assertIn(existing_pack, creative_pack)

        pack = creative_pack["workspace_provider_adapter_contract_pack"]
        self.assertEqual(
            pack["pack_version"],
            "workspace_provider_adapter_contract_pack_v1",
        )
        summary = pack["adapter_contract_summary"]
        self.assertTrue(summary["contract_id"])
        self.assertIn("provider_adapter_contract_preview", summary["mode"])
        self.assertIn("invocation_boundary_preview", summary["mode"])
        self.assertIn("dry_run_only", summary["mode"])
        self.assertFalse(summary["real_invocation_allowed"])
        self.assertFalse(summary["real_execution_allowed"])

        cards = pack["provider_contract_cards"]
        provider_types = {card["provider_type"] for card in cards}
        for provider_type in [
            "llm_text_generation",
            "video_generation_provider",
            "image_generation_provider",
            "media_storage_provider",
            "external_scraping_provider",
            "translation_provider",
            "analytics_or_tracking_provider",
            "database_persistence_provider",
            "approval_or_ticket_provider",
            "rollback_restore_provider",
        ]:
            with self.subTest(provider_type=provider_type):
                self.assertIn(provider_type, provider_types)
        for card in cards:
            for field in [
                "provider_id", "provider_type", "provider_name",
                "source_capability", "current_status", "allowed_modes",
                "disallowed_modes", "required_inputs", "required_outputs",
                "required_approvals",
            ]:
                with self.subTest(provider=card["provider_id"], field=field):
                    self.assertIn(field, card)
            status_text = " ".join([
                card["current_status"],
                " ".join(card["allowed_modes"]),
            ])
            self.assertTrue(
                any(token in status_text for token in [
                    "disabled", "preview", "dry",
                ])
            )
            for mode in [
                "real_invocation", "real_execution", "media_upload",
                "paid_operation", "secret_access",
            ]:
                with self.subTest(
                    provider=card["provider_id"], disallowed=mode
                ):
                    self.assertIn(mode, card["disallowed_modes"])
            self.assertFalse(card["secret_available"])
            self.assertFalse(card["real_invocation_allowed"])

        input_contracts = pack["input_contracts"]
        output_contracts = pack["output_contracts"]
        self.assertTrue(input_contracts)
        self.assertTrue(output_contracts)
        for contract in input_contracts:
            self.assertIn("required_fields", contract)
            self.assertFalse(contract["request_sent"])
            self.assertFalse(contract["file_write_performed"])
            self.assertFalse(contract["database_write_performed"])
            self.assertFalse(contract["secret_read_performed"])
            self.assertFalse(contract["real_execution_allowed"])
        for contract in output_contracts:
            self.assertIn("required_fields", contract)
            self.assertFalse(contract["provider_called"])
            self.assertFalse(contract["file_write_performed"])
            self.assertFalse(contract["database_write_performed"])
            self.assertFalse(contract["real_execution_allowed"])

        rules = pack["invocation_boundary_rules"]
        self.assertGreaterEqual(len(rules), 2)
        for rule in rules:
            for field in [
                "rule_id", "provider_id", "rule_type",
                "blocked_real_behavior", "required_gate",
            ]:
                with self.subTest(rule=rule["rule_id"], field=field):
                    self.assertIn(field, rule)
            self.assertIn("real_invocation", rule["blocked_real_behavior"])
            self.assertFalse(rule["real_execution_allowed"])

        previews = pack["dry_run_invocation_previews"]
        self.assertTrue(previews)
        for preview in previews:
            self.assertIn("mock_invocation_shape", preview)
            self.assertFalse(preview["provider_called"])
            self.assertFalse(preview["real_invocation_allowed"])
            self.assertFalse(
                preview["mock_invocation_shape"]["provider_called"]
            )
            self.assertFalse(
                preview["mock_invocation_shape"]["secret_read"]
            )

        failures = pack["failure_boundary_matrix"]
        self.assertTrue(failures)
        for failure in failures:
            self.assertFalse(failure["real_failure_triggered"])
            self.assertFalse(failure["retry_allowed"])
            self.assertFalse(failure["rollback_allowed"])
            self.assertFalse(failure["real_execution_allowed"])

        requirements = pack["approval_and_secret_requirements"]
        self.assertTrue(requirements["future_approval_required"])
        self.assertTrue(requirements["providers_requiring_secret"])
        self.assertFalse(requirements["secret_read_performed"])
        self.assertFalse(requirements["secret_available"])
        self.assertFalse(requirements["real_approval_created"])
        self.assertFalse(requirements["operator_task_created"])
        self.assertFalse(requirements["real_invocation_allowed"])

        checks = pack["contract_quality_checks"]
        for key in [
            "adapter_contract_summary_present",
            "provider_contract_cards_present",
            "required_provider_types_covered",
            "all_providers_disabled_or_preview_only",
            "input_contracts_present",
            "output_contracts_present",
            "invocation_boundary_rules_present",
            "dry_run_previews_do_not_call_provider",
            "failure_boundaries_do_not_trigger_real_failure",
            "approval_requirements_do_not_create_real_approval",
            "secret_not_read",
            "audit_preview_not_persisted",
        ]:
            with self.subTest(check=key):
                self.assertTrue(checks[key])
        for key in [
            "database_write_performed", "real_log_read_performed",
            "real_history_table_read_performed",
            "real_service_health_read_performed",
            "provider_invocation_performed",
            "real_execution_performed",
        ]:
            with self.subTest(check=key):
                self.assertFalse(checks[key])

        audit = pack["audit_preview"]
        self.assertTrue(audit["contract_id"])
        self.assertFalse(audit["is_real_provider_adapter"])
        self.assertFalse(audit["provider_invocation_performed"])
        self.assertFalse(audit["provider_called"])
        self.assertFalse(audit["llm_called"])
        self.assertFalse(audit["image_generation_performed"])
        self.assertFalse(audit["video_generation_performed"])
        self.assertFalse(audit["media_upload_performed"])
        self.assertFalse(audit["media_download_performed"])
        self.assertFalse(audit["secret_read_performed"])
        self.assertFalse(audit["database_write_performed"])
        self.assertFalse(audit["real_log_read_performed"])
        self.assertFalse(audit["real_history_table_read_performed"])
        self.assertFalse(audit["real_service_health_read_performed"])
        self.assertFalse(audit["operator_task_created"])
        self.assertFalse(audit["real_approval_created"])
        self.assertFalse(audit["audit_persisted"])

        boundaries = pack["safety_boundaries"]
        for key in [
            "provider_calls_enabled", "llm_api_enabled",
            "image_generation_enabled", "video_generation_enabled",
            "media_upload_enabled", "media_download_enabled",
            "paid_operation_enabled", "registry_write_enabled",
            "rollback_enabled", "external_scraping_enabled",
            "database_persistence_enabled", "real_restore_enabled",
            "real_execution_enabled",
        ]:
            with self.subTest(boundary=key):
                self.assertFalse(boundaries[key])

    def test_workspace_provider_contract_test_pack_is_mock_only(self):
        payload = {
            "workspace_id": "workspace-provider-contract-test",
            "source": "manual_import",
            "output_language": "en",
            "products": [{
                "platform": "manual",
                "asin": "PROVIDERTEST001",
                "title": "Compact Travel Mug",
                "reviews": [{
                    "rating": 2,
                    "title": "Leaks during commute",
                    "text": "Leaks during commute and needs a better seal.",
                    "source_section": "manual_review",
                }],
            }],
        }
        response = self.client.post(
            "/api/v1/analyze-review-workspace", json=payload
        )
        self.assertEqual(response.status_code, 200)
        creative_pack = response.json()["creative_decision_pack"]
        for existing_pack in [
            "review_import_pack", "competitor_review_comparison_pack",
            "llm_assist_dry_run_pack",
            "video_provider_orchestration_dry_run_pack",
            "campaign_export_pack", "workspace_session_snapshot_pack",
            "workspace_run_compare_pack", "workspace_action_queue_pack",
            "workspace_action_ticket_pack",
            "workspace_approval_decision_pack",
            "workspace_execution_readiness_pack",
            "workspace_execution_rehearsal_pack",
            "workspace_rehearsal_result_pack",
            "workspace_rehearsal_remediation_pack",
            "workspace_remediation_verification_pack",
            "workspace_retry_rehearsal_plan_pack",
            "workspace_retry_rehearsal_result_pack",
            "workspace_retry_cycle_decision_pack",
            "workspace_cycle_history_timeline_pack",
            "workspace_control_center_pack",
            "workspace_agent_run_ledger_pack",
            "workspace_human_review_queue_pack",
            "workspace_capability_permission_matrix_pack",
            "workspace_system_integration_health_pack",
            "workspace_replay_harness_pack",
            "workspace_provider_adapter_contract_pack",
            "workspace_provider_contract_test_pack",
        ]:
            with self.subTest(existing_pack=existing_pack):
                self.assertIn(existing_pack, creative_pack)

        pack = creative_pack["workspace_provider_contract_test_pack"]
        self.assertEqual(
            pack["pack_version"], "workspace_provider_contract_test_pack_v1"
        )
        summary = pack["contract_test_summary"]
        self.assertTrue(summary["harness_id"])
        self.assertIn("provider_contract_test_preview", summary["mode"])
        self.assertIn("mock_invocation_harness", summary["mode"])
        self.assertIn("dry_run_only", summary["mode"])
        self.assertFalse(summary["real_invocation_allowed"])
        self.assertFalse(summary["real_execution_allowed"])

        required_provider_types = {
            "llm_text_generation",
            "video_generation_provider",
            "image_generation_provider",
            "media_storage_provider",
            "external_scraping_provider",
            "translation_provider",
            "analytics_or_tracking_provider",
            "database_persistence_provider",
            "approval_or_ticket_provider",
            "rollback_restore_provider",
        }
        test_cases = pack["mock_invocation_test_cases"]
        self.assertTrue(test_cases)
        provider_types = {case["provider_type"] for case in test_cases}
        self.assertTrue(required_provider_types <= provider_types)
        for case in test_cases:
            for field in [
                "test_id", "provider_id", "provider_type",
                "source_contract_id", "expected_status",
            ]:
                with self.subTest(case=case["test_id"], field=field):
                    self.assertIn(field, case)
            self.assertTrue(case["mock_input_refs"])
            self.assertTrue(case["expected_mock_outputs"])
            self.assertIn("mock", case["expected_status"])
            self.assertFalse(case["real_invocation_allowed"])
            self.assertFalse(case["real_execution_allowed"])

        input_results = pack["input_validation_results"]
        output_results = pack["output_validation_results"]
        self.assertTrue(input_results)
        self.assertTrue(output_results)
        for result in input_results:
            self.assertIn("required_fields_checked", result)
            self.assertFalse(result["request_sent"])
            self.assertFalse(result["file_read_performed"])
            self.assertFalse(result["file_write_performed"])
            self.assertFalse(result["media_upload_performed"])
            self.assertFalse(result["media_download_performed"])
            self.assertFalse(result["secret_read_performed"])
            self.assertFalse(result["database_write_performed"])
            self.assertFalse(result["real_execution_allowed"])
        for result in output_results:
            self.assertIn("required_fields_checked", result)
            self.assertFalse(result["provider_called"])
            self.assertFalse(result["file_write_performed"])
            self.assertFalse(result["media_generated"])
            self.assertFalse(result["database_write_performed"])
            self.assertFalse(result["real_execution_allowed"])

        boundary_results = pack["boundary_rule_test_results"]
        self.assertGreaterEqual(len(boundary_results), 2)
        for result in boundary_results:
            for field in [
                "rule_id", "provider_id", "test_status",
                "blocked_real_behavior_verified",
            ]:
                with self.subTest(
                    result=result["result_id"], field=field
                ):
                    self.assertIn(field, result)
            self.assertTrue(result["blocked_real_behavior_verified"])
            self.assertFalse(result["real_execution_allowed"])

        failure_previews = pack["failure_simulation_previews"]
        self.assertTrue(failure_previews)
        for preview in failure_previews:
            self.assertFalse(preview["real_failure_triggered"])
            self.assertFalse(preview["provider_called"])
            self.assertFalse(preview["retry_executed"])
            self.assertFalse(preview["rollback_executed"])
            self.assertFalse(preview["real_execution_allowed"])

        matrix = pack["approval_secret_test_matrix"]
        self.assertTrue(matrix["future_approval_required"])
        self.assertTrue(matrix["providers_requiring_secret"])
        self.assertTrue(matrix["secret_requirement_identified"])
        self.assertFalse(matrix["secret_read_performed"])
        self.assertFalse(matrix["secret_available"])
        self.assertFalse(matrix["real_approval_created"])
        self.assertFalse(matrix["operator_task_created"])
        self.assertFalse(matrix["real_invocation_allowed"])
        self.assertFalse(matrix["real_execution_allowed"])

        coverage = pack["provider_test_coverage"]
        self.assertTrue(coverage["all_required_provider_types_covered"])
        self.assertEqual(set(coverage["required_provider_types"]), required_provider_types)
        self.assertEqual(set(coverage["covered_provider_types"]), required_provider_types)
        self.assertFalse(coverage["missing_provider_types"])
        for provider_type in required_provider_types:
            with self.subTest(provider_type=provider_type):
                self.assertTrue(coverage["provider_type_coverage"][provider_type])

        checks = pack["contract_test_quality_checks"]
        for key in [
            "contract_test_summary_present",
            "source_adapter_contract_pack_present",
            "mock_invocation_test_cases_present",
            "input_validation_results_present",
            "output_validation_results_present",
            "boundary_rule_test_results_present",
            "failure_simulation_previews_present",
            "approval_secret_test_matrix_present",
            "provider_test_coverage_present",
            "all_required_provider_types_covered",
            "all_mock_cases_keep_real_invocation_disabled",
            "all_mock_cases_keep_real_execution_disabled",
            "boundary_results_verify_real_behavior_blocked",
            "failure_previews_do_not_trigger_real_failure",
            "secret_not_read",
            "real_approval_not_created",
            "audit_preview_not_persisted",
        ]:
            with self.subTest(check=key):
                self.assertTrue(checks[key])
        for key in [
            "provider_invocation_performed", "real_execution_performed",
            "database_write_performed", "real_log_read_performed",
            "real_history_table_read_performed",
            "real_service_health_read_performed",
        ]:
            with self.subTest(check=key):
                self.assertFalse(checks[key])

        audit = pack["audit_preview"]
        self.assertTrue(audit["harness_id"])
        self.assertFalse(audit["is_real_provider_invocation"])
        self.assertFalse(audit["provider_invocation_performed"])
        self.assertFalse(audit["provider_called"])
        self.assertFalse(audit["llm_called"])
        self.assertFalse(audit["image_generation_performed"])
        self.assertFalse(audit["video_generation_performed"])
        self.assertFalse(audit["media_upload_performed"])
        self.assertFalse(audit["media_download_performed"])
        self.assertFalse(audit["secret_read_performed"])
        self.assertFalse(audit["database_write_performed"])
        self.assertFalse(audit["real_log_read_performed"])
        self.assertFalse(audit["real_history_table_read_performed"])
        self.assertFalse(audit["real_service_health_read_performed"])
        self.assertFalse(audit["operator_task_created"])
        self.assertFalse(audit["real_approval_created"])
        self.assertFalse(audit["real_failure_injection_triggered"])
        self.assertFalse(audit["real_diff_job_executed"])
        self.assertFalse(audit["replay_snapshot_file_written"])
        self.assertFalse(audit["audit_persisted"])

        boundaries = pack["safety_boundaries"]
        for key in [
            "provider_enabled", "llm_enabled", "image_enabled",
            "video_enabled", "media_enabled", "paid_enabled",
            "registry_enabled", "rollback_enabled",
            "external_scraping_enabled", "database_persistence_enabled",
            "real_restore_enabled", "real_execution_enabled",
        ]:
            with self.subTest(boundary=key):
                self.assertFalse(boundaries[key])

    def test_workspace_provider_mock_invocation_result_pack_is_sandbox_preview_only(self):
        payload = {
            "workspace_id": "workspace-provider-mock-result",
            "source": "manual_import",
            "output_language": "en",
            "products": [{
                "platform": "manual",
                "asin": "PROVIDERRESULT001",
                "title": "Compact Travel Mug",
                "reviews": [{
                    "rating": 2,
                    "title": "Leaks during commute",
                    "text": "Leaks during commute and needs a better seal.",
                    "source_section": "manual_review",
                }],
            }],
        }
        response = self.client.post(
            "/api/v1/analyze-review-workspace", json=payload
        )
        self.assertEqual(response.status_code, 200)
        creative_pack = response.json()["creative_decision_pack"]
        for existing_pack in [
            "review_import_pack", "competitor_review_comparison_pack",
            "llm_assist_dry_run_pack",
            "video_provider_orchestration_dry_run_pack",
            "campaign_export_pack", "workspace_session_snapshot_pack",
            "workspace_run_compare_pack", "workspace_action_queue_pack",
            "workspace_action_ticket_pack",
            "workspace_approval_decision_pack",
            "workspace_execution_readiness_pack",
            "workspace_execution_rehearsal_pack",
            "workspace_rehearsal_result_pack",
            "workspace_rehearsal_remediation_pack",
            "workspace_remediation_verification_pack",
            "workspace_retry_rehearsal_plan_pack",
            "workspace_retry_rehearsal_result_pack",
            "workspace_retry_cycle_decision_pack",
            "workspace_cycle_history_timeline_pack",
            "workspace_control_center_pack",
            "workspace_agent_run_ledger_pack",
            "workspace_human_review_queue_pack",
            "workspace_capability_permission_matrix_pack",
            "workspace_system_integration_health_pack",
            "workspace_replay_harness_pack",
            "workspace_provider_adapter_contract_pack",
            "workspace_provider_contract_test_pack",
            "workspace_provider_mock_invocation_result_pack",
        ]:
            with self.subTest(existing_pack=existing_pack):
                self.assertIn(existing_pack, creative_pack)

        pack = creative_pack["workspace_provider_mock_invocation_result_pack"]
        self.assertEqual(
            pack["pack_version"],
            "workspace_provider_mock_invocation_result_pack_v1",
        )
        summary = pack["mock_invocation_result_summary"]
        self.assertTrue(summary["result_id"])
        self.assertIn("mock_invocation_result_preview", summary["mode"])
        self.assertIn("sandbox_run_ledger", summary["mode"])
        self.assertIn("dry_run_only", summary["mode"])
        self.assertFalse(summary["real_invocation_allowed"])
        self.assertFalse(summary["real_execution_allowed"])

        required_provider_types = {
            "llm_text_generation",
            "video_generation_provider",
            "image_generation_provider",
            "media_storage_provider",
            "external_scraping_provider",
            "translation_provider",
            "analytics_or_tracking_provider",
            "database_persistence_provider",
            "approval_or_ticket_provider",
            "rollback_restore_provider",
        }
        ledger = pack["sandbox_run_ledger"]
        self.assertTrue(ledger)
        ledger_types = {item["provider_type"] for item in ledger}
        self.assertTrue(required_provider_types <= ledger_types)
        for run in ledger:
            for field in [
                "run_id", "provider_id", "provider_type", "source_test_id",
                "run_mode", "mock_started_at", "mock_completed_at",
                "mock_status", "boundary_status",
            ]:
                with self.subTest(run=run["run_id"], field=field):
                    self.assertIn(field, run)
            self.assertIn("mock", run["mock_status"])
            self.assertFalse(run["real_invocation_allowed"])
            self.assertFalse(run["real_execution_allowed"])

        cards = pack["mock_run_result_cards"]
        self.assertTrue(cards)
        card_types = {item["provider_type"] for item in cards}
        self.assertTrue(required_provider_types <= card_types)
        for card in cards:
            for field in [
                "result_id", "run_id", "provider_id", "provider_type",
                "source_test_id", "input_contract_status",
                "output_contract_status", "boundary_rule_status",
                "failure_simulation_status", "approval_secret_status",
                "expected_mock_output_summary",
                "blocked_real_behavior_summary",
                "recommended_operator_action",
            ]:
                with self.subTest(card=card["result_id"], field=field):
                    self.assertIn(field, card)
            self.assertIn("blocked", card["blocked_real_behavior_summary"])
            self.assertFalse(card["real_invocation_allowed"])
            self.assertFalse(card["real_execution_allowed"])

        snapshots = pack["mock_input_output_snapshots"]
        self.assertTrue(snapshots)
        for snapshot in snapshots:
            self.assertIn("mock_input_refs", snapshot)
            self.assertIn("expected_mock_outputs", snapshot)
            self.assertFalse(snapshot["file_write_performed"])
            self.assertFalse(snapshot["database_write_performed"])
            self.assertFalse(snapshot["media_upload_performed"])
            self.assertFalse(snapshot["media_download_performed"])
            self.assertFalse(snapshot["real_invocation_allowed"])
            self.assertFalse(snapshot["real_execution_allowed"])

        enforcement = pack["boundary_enforcement_results"]
        self.assertTrue(enforcement)
        for item in enforcement:
            self.assertTrue(item["blocked_real_behavior_verified"])
            self.assertFalse(item["real_invocation_allowed"])
            self.assertFalse(item["real_execution_allowed"])

        failures = pack["mock_failure_observations"]
        self.assertTrue(failures)
        for failure in failures:
            self.assertFalse(failure["real_failure_triggered"])
            self.assertFalse(failure["provider_called"])
            self.assertFalse(failure["retry_executed"])
            self.assertFalse(failure["rollback_executed"])
            self.assertFalse(failure["real_execution_allowed"])

        notes = pack["operator_review_notes"]
        self.assertTrue(notes)
        for note in notes:
            self.assertFalse(note["operator_task_created"])
            self.assertFalse(note["real_approval_created"])
            self.assertFalse(note["real_execution_allowed"])

        checks = pack["sandbox_result_quality_checks"]
        for key in [
            "mock_invocation_result_summary_present",
            "source_provider_contract_test_pack_present",
            "sandbox_run_ledger_present",
            "mock_run_result_cards_present",
            "mock_input_output_snapshots_present",
            "boundary_enforcement_results_present",
            "mock_failure_observations_present",
            "operator_review_notes_present",
            "all_required_provider_types_covered",
            "all_sandbox_runs_keep_real_invocation_disabled",
            "all_sandbox_runs_keep_real_execution_disabled",
            "all_result_cards_keep_real_invocation_disabled",
            "all_result_cards_keep_real_execution_disabled",
            "snapshots_not_written_to_file_or_database",
            "boundary_results_verify_real_behavior_blocked",
            "failure_observations_do_not_trigger_real_failure",
            "operator_notes_do_not_create_tasks",
            "audit_preview_not_persisted",
        ]:
            with self.subTest(check=key):
                self.assertTrue(checks[key])
        for key in [
            "provider_invocation_performed", "real_execution_performed",
            "database_write_performed", "real_log_read_performed",
            "real_history_table_read_performed",
            "real_service_health_read_performed",
        ]:
            with self.subTest(check=key):
                self.assertFalse(checks[key])

        audit = pack["audit_preview"]
        self.assertTrue(audit["result_id"])
        self.assertFalse(audit["is_real_provider_invocation"])
        self.assertFalse(audit["provider_invocation_performed"])
        self.assertFalse(audit["provider_called"])
        self.assertFalse(audit["llm_called"])
        self.assertFalse(audit["image_generation_performed"])
        self.assertFalse(audit["video_generation_performed"])
        self.assertFalse(audit["media_upload_performed"])
        self.assertFalse(audit["media_download_performed"])
        self.assertFalse(audit["secret_read_performed"])
        self.assertFalse(audit["database_write_performed"])
        self.assertFalse(audit["file_write_performed"])
        self.assertFalse(audit["real_log_read_performed"])
        self.assertFalse(audit["real_history_table_read_performed"])
        self.assertFalse(audit["real_service_health_read_performed"])
        self.assertFalse(audit["operator_task_created"])
        self.assertFalse(audit["real_approval_created"])
        self.assertFalse(audit["real_failure_injection_triggered"])
        self.assertFalse(audit["real_diff_job_executed"])
        self.assertFalse(audit["replay_snapshot_file_written"])
        self.assertFalse(audit["audit_persisted"])

        boundaries = pack["safety_boundaries"]
        for key in [
            "provider_enabled", "llm_enabled", "image_enabled",
            "video_enabled", "media_enabled", "paid_enabled",
            "registry_enabled", "rollback_enabled",
            "external_scraping_enabled", "database_persistence_enabled",
            "real_restore_enabled", "real_execution_enabled",
        ]:
            with self.subTest(boundary=key):
                self.assertFalse(boundaries[key])

    def test_workspace_provider_failure_taxonomy_pack_is_recovery_policy_preview_only(self):
        payload = {
            "workspace_id": "workspace-provider-failure-taxonomy",
            "source": "manual_import",
            "output_language": "en",
            "products": [{
                "platform": "manual",
                "asin": "PROVIDERFAILURE001",
                "title": "Compact Travel Mug",
                "reviews": [{
                    "rating": 2,
                    "title": "Leaks during commute",
                    "text": "Leaks during commute and needs a better seal.",
                    "source_section": "manual_review",
                }],
            }],
        }
        response = self.client.post(
            "/api/v1/analyze-review-workspace", json=payload
        )
        self.assertEqual(response.status_code, 200)
        creative_pack = response.json()["creative_decision_pack"]
        for existing_pack in [
            "review_import_pack", "competitor_review_comparison_pack",
            "llm_assist_dry_run_pack",
            "video_provider_orchestration_dry_run_pack",
            "campaign_export_pack", "workspace_session_snapshot_pack",
            "workspace_run_compare_pack", "workspace_action_queue_pack",
            "workspace_action_ticket_pack",
            "workspace_approval_decision_pack",
            "workspace_execution_readiness_pack",
            "workspace_execution_rehearsal_pack",
            "workspace_rehearsal_result_pack",
            "workspace_rehearsal_remediation_pack",
            "workspace_remediation_verification_pack",
            "workspace_retry_rehearsal_plan_pack",
            "workspace_retry_rehearsal_result_pack",
            "workspace_retry_cycle_decision_pack",
            "workspace_cycle_history_timeline_pack",
            "workspace_control_center_pack",
            "workspace_agent_run_ledger_pack",
            "workspace_human_review_queue_pack",
            "workspace_capability_permission_matrix_pack",
            "workspace_system_integration_health_pack",
            "workspace_replay_harness_pack",
            "workspace_provider_adapter_contract_pack",
            "workspace_provider_contract_test_pack",
            "workspace_provider_mock_invocation_result_pack",
            "workspace_provider_failure_taxonomy_pack",
        ]:
            with self.subTest(existing_pack=existing_pack):
                self.assertIn(existing_pack, creative_pack)

        pack = creative_pack["workspace_provider_failure_taxonomy_pack"]
        self.assertEqual(
            pack["pack_version"],
            "workspace_provider_failure_taxonomy_pack_v1",
        )
        summary = pack["failure_taxonomy_summary"]
        self.assertTrue(summary["taxonomy_id"])
        self.assertIn("failure_taxonomy_preview", summary["mode"])
        self.assertIn("recovery_policy_preview", summary["mode"])
        self.assertIn("dry_run_only", summary["mode"])
        self.assertFalse(summary["real_invocation_allowed"])
        self.assertFalse(summary["real_execution_allowed"])

        required_provider_types = {
            "llm_text_generation",
            "video_generation_provider",
            "image_generation_provider",
            "media_storage_provider",
            "external_scraping_provider",
            "translation_provider",
            "analytics_or_tracking_provider",
            "database_persistence_provider",
            "approval_or_ticket_provider",
            "rollback_restore_provider",
        }
        failure_cards = pack["failure_taxonomy_cards"]
        self.assertTrue(failure_cards)
        failure_card_types = {item["provider_type"] for item in failure_cards}
        self.assertTrue(required_provider_types <= failure_card_types)
        for card in failure_cards:
            for field in [
                "failure_type_id", "failure_type", "provider_id",
                "provider_type", "source_run_id", "source_result_id",
                "failure_category", "failure_signal", "severity",
                "detected_from", "blocked_real_behavior_summary",
                "operator_visible_message",
            ]:
                with self.subTest(card=card["failure_type_id"], field=field):
                    self.assertIn(field, card)
            self.assertIn(
                "workspace_provider_mock_invocation_result_pack",
                card["detected_from"],
            )
            self.assertIn(
                card["failure_category"],
                {
                    "input_contract_failure",
                    "output_contract_failure",
                    "boundary_blocked_real_behavior",
                    "secret_missing_or_blocked",
                    "approval_required",
                    "mock_failure_simulation",
                    "quota_or_cost_risk",
                    "media_contract_risk",
                    "external_call_blocked",
                    "rollback_or_restore_blocked",
                    "database_write_blocked",
                },
            )
            self.assertFalse(card["real_invocation_allowed"])
            self.assertFalse(card["real_execution_allowed"])

        policies = pack["recovery_policy_cards"]
        self.assertTrue(policies)
        policy_types = {item["provider_type"] for item in policies}
        self.assertTrue(required_provider_types <= policy_types)
        for policy in policies:
            for field in [
                "policy_id", "failure_type_id", "provider_id",
                "provider_type", "recovery_strategy",
                "allowed_recovery_modes", "disallowed_recovery_modes",
                "requires_human_review", "requires_secret_check",
                "requires_cost_review", "requires_rollback_review",
                "retry_allowed", "recommended_operator_action",
            ]:
                with self.subTest(policy=policy["policy_id"], field=field):
                    self.assertIn(field, policy)
            self.assertIn(
                "real_provider_retry", policy["disallowed_recovery_modes"]
            )
            self.assertIn("real_rollback", policy["disallowed_recovery_modes"])
            self.assertFalse(policy["real_retry_allowed"])
            self.assertFalse(policy["real_rollback_allowed"])
            self.assertFalse(policy["real_execution_allowed"])

        retry_rules = pack["retry_boundary_rules"]
        self.assertTrue(retry_rules)
        for rule in retry_rules:
            self.assertFalse(rule["real_retry_allowed"])
            self.assertFalse(rule["real_execution_allowed"])
            self.assertIn("preview", rule["rule_summary"])

        manual_requirements = pack["manual_intervention_requirements"]
        self.assertTrue(manual_requirements)
        for requirement in manual_requirements:
            self.assertFalse(requirement["operator_task_created"])
            self.assertFalse(requirement["real_approval_created"])
            self.assertFalse(requirement["real_execution_allowed"])

        non_recoverable = pack["non_recoverable_conditions"]
        self.assertTrue(non_recoverable)
        condition_types = {item["condition_type"] for item in non_recoverable}
        self.assertTrue({
            "secret_missing_or_blocked",
            "quota_or_cost_risk",
            "rollback_or_restore_blocked",
            "database_write_blocked",
            "external_call_blocked",
        } <= condition_types)
        for condition in non_recoverable:
            self.assertFalse(condition["real_recovery_allowed"])

        action_map = pack["failure_to_action_map"]
        self.assertTrue(action_map)
        for item in action_map:
            self.assertIn("preview_action", item)
            self.assertFalse(item["real_action_executed"])
            self.assertFalse(item["real_execution_allowed"])

        checks = pack["recovery_quality_checks"]
        for key in [
            "source_mock_invocation_result_pack_present",
            "mock_invocation_result_summary_referenced",
            "sandbox_run_ledger_referenced",
            "mock_run_result_cards_referenced",
            "mock_input_output_snapshots_referenced",
            "boundary_enforcement_results_referenced",
            "mock_failure_observations_referenced",
            "operator_review_notes_referenced",
            "sandbox_result_quality_checks_referenced",
            "all_required_provider_types_covered",
            "all_failure_cards_keep_real_invocation_disabled",
            "all_failure_cards_keep_real_execution_disabled",
            "all_recovery_policies_keep_real_retry_disabled",
            "all_recovery_policies_keep_real_rollback_disabled",
            "all_failure_action_maps_are_preview_only",
            "manual_intervention_does_not_create_tasks",
            "audit_preview_not_persisted",
        ]:
            with self.subTest(check=key):
                self.assertTrue(checks[key])
        for key in [
            "real_retry_executed", "real_rollback_executed",
            "provider_invocation_performed", "real_execution_performed",
            "database_write_performed", "real_log_read_performed",
            "real_history_table_read_performed",
            "real_service_health_read_performed",
        ]:
            with self.subTest(check=key):
                self.assertFalse(checks[key])

        audit = pack["audit_preview"]
        self.assertTrue(audit["taxonomy_id"])
        self.assertFalse(audit["is_real_failure_handling_system"])
        self.assertFalse(audit["provider_invocation_performed"])
        self.assertFalse(audit["provider_called"])
        self.assertFalse(audit["llm_called"])
        self.assertFalse(audit["image_generation_performed"])
        self.assertFalse(audit["video_generation_performed"])
        self.assertFalse(audit["media_upload_performed"])
        self.assertFalse(audit["media_download_performed"])
        self.assertFalse(audit["secret_read_performed"])
        self.assertFalse(audit["database_write_performed"])
        self.assertFalse(audit["real_log_read_performed"])
        self.assertFalse(audit["real_history_table_read_performed"])
        self.assertFalse(audit["real_service_health_read_performed"])
        self.assertFalse(audit["operator_task_created"])
        self.assertFalse(audit["real_approval_created"])
        self.assertFalse(audit["real_failure_injection_triggered"])
        self.assertFalse(audit["real_retry_executed"])
        self.assertFalse(audit["real_rollback_executed"])
        self.assertFalse(audit["real_restore_executed"])
        self.assertFalse(audit["audit_persisted"])

        boundaries = pack["safety_boundaries"]
        for key in [
            "provider_enabled", "llm_enabled", "image_enabled",
            "video_enabled", "media_enabled", "paid_enabled",
            "registry_enabled", "rollback_enabled",
            "external_scraping_enabled", "database_persistence_enabled",
            "real_restore_enabled", "real_execution_enabled",
        ]:
            with self.subTest(boundary=key):
                self.assertFalse(boundaries[key])

    def test_workspace_provider_asset_contract_pack_is_manifest_preview_only(self):
        payload = {
            "workspace_id": "workspace-provider-asset-contract",
            "source": "manual_import",
            "output_language": "en",
            "products": [{
                "platform": "manual",
                "asin": "PROVIDERASSET001",
                "title": "Compact Travel Mug",
                "reviews": [{
                    "rating": 2,
                    "title": "Leaks during commute",
                    "text": "Leaks during commute and needs a better seal.",
                    "source_section": "manual_review",
                }],
            }],
        }
        response = self.client.post(
            "/api/v1/analyze-review-workspace", json=payload
        )
        self.assertEqual(response.status_code, 200)
        creative_pack = response.json()["creative_decision_pack"]
        for existing_pack in [
            "review_import_pack", "competitor_review_comparison_pack",
            "llm_assist_dry_run_pack",
            "video_provider_orchestration_dry_run_pack",
            "campaign_export_pack", "workspace_session_snapshot_pack",
            "workspace_run_compare_pack", "workspace_action_queue_pack",
            "workspace_action_ticket_pack",
            "workspace_approval_decision_pack",
            "workspace_execution_readiness_pack",
            "workspace_execution_rehearsal_pack",
            "workspace_rehearsal_result_pack",
            "workspace_rehearsal_remediation_pack",
            "workspace_remediation_verification_pack",
            "workspace_retry_rehearsal_plan_pack",
            "workspace_retry_rehearsal_result_pack",
            "workspace_retry_cycle_decision_pack",
            "workspace_cycle_history_timeline_pack",
            "workspace_control_center_pack",
            "workspace_agent_run_ledger_pack",
            "workspace_human_review_queue_pack",
            "workspace_capability_permission_matrix_pack",
            "workspace_system_integration_health_pack",
            "workspace_replay_harness_pack",
            "workspace_provider_adapter_contract_pack",
            "workspace_provider_contract_test_pack",
            "workspace_provider_mock_invocation_result_pack",
            "workspace_provider_failure_taxonomy_pack",
            "workspace_provider_asset_contract_pack",
        ]:
            with self.subTest(existing_pack=existing_pack):
                self.assertIn(existing_pack, creative_pack)

        pack = creative_pack["workspace_provider_asset_contract_pack"]
        self.assertEqual(
            pack["pack_version"],
            "workspace_provider_asset_contract_pack_v1",
        )
        summary = pack["asset_contract_summary"]
        self.assertTrue(summary["asset_contract_pack_id"])
        self.assertIn("asset_contract_preview", summary["mode"])
        self.assertIn("media_manifest_preview", summary["mode"])
        self.assertIn("dry_run_only", summary["mode"])
        for source_pack in [
            "workspace_provider_adapter_contract_pack",
            "workspace_provider_contract_test_pack",
            "workspace_provider_mock_invocation_result_pack",
            "workspace_provider_failure_taxonomy_pack",
            "workspace_capability_permission_matrix_pack",
        ]:
            with self.subTest(source_pack=source_pack):
                self.assertIn(source_pack, summary["source_packs"])
        self.assertFalse(summary["media_upload_allowed"])
        self.assertFalse(summary["media_download_allowed"])
        self.assertFalse(summary["real_generation_allowed"])
        self.assertFalse(summary["real_invocation_allowed"])
        self.assertFalse(summary["real_execution_allowed"])

        required_provider_types = {
            "llm_text_generation",
            "video_generation_provider",
            "image_generation_provider",
            "media_storage_provider",
            "external_scraping_provider",
            "translation_provider",
            "analytics_or_tracking_provider",
            "database_persistence_provider",
            "approval_or_ticket_provider",
            "rollback_restore_provider",
        }
        cards = pack["provider_asset_contract_cards"]
        self.assertTrue(cards)
        self.assertTrue(required_provider_types <= {
            card["provider_type"] for card in cards
        })
        for card in cards:
            for field in [
                "asset_contract_id", "provider_id", "provider_type",
                "source_capability", "asset_role",
                "required_input_assets", "expected_output_assets",
                "allowed_asset_modes", "disallowed_asset_modes",
                "risk_note",
            ]:
                with self.subTest(card=card["asset_contract_id"], field=field):
                    self.assertIn(field, card)
            self.assertFalse(card["media_upload_allowed"])
            self.assertFalse(card["media_download_allowed"])
            self.assertFalse(card["real_generation_allowed"])
            self.assertFalse(card["real_invocation_allowed"])
            self.assertFalse(card["real_execution_allowed"])

        manifests = pack["media_manifest_cards"]
        self.assertTrue(manifests)
        self.assertGreaterEqual(len({item["provider_id"] for item in manifests}), 3)
        self.assertTrue(required_provider_types <= {
            item["provider_type"] for item in manifests
        })
        for manifest in manifests:
            for field in [
                "manifest_id", "provider_id", "provider_type",
                "asset_type", "asset_purpose", "source_pack",
                "mock_asset_ref", "storage_mode", "transfer_mode",
                "validation_status", "blocked_real_behavior_summary",
            ]:
                with self.subTest(
                    manifest=manifest["manifest_id"], field=field
                ):
                    self.assertIn(field, manifest)
            self.assertFalse(manifest["real_media_operation_allowed"])
            self.assertFalse(manifest["real_execution_allowed"])

        input_requirements = pack["input_asset_requirements"]
        self.assertTrue(input_requirements)
        for requirement in input_requirements:
            self.assertFalse(requirement["file_read_performed"])
            self.assertFalse(requirement["media_upload_performed"])
            self.assertFalse(requirement["secret_read_performed"])
            self.assertFalse(requirement["real_execution_allowed"])

        output_requirements = pack["output_asset_requirements"]
        self.assertTrue(output_requirements)
        for requirement in output_requirements:
            self.assertFalse(requirement["file_write_performed"])
            self.assertFalse(requirement["media_download_performed"])
            self.assertFalse(requirement["media_generated"])
            self.assertFalse(requirement["database_write_performed"])
            self.assertFalse(requirement["real_execution_allowed"])

        rules = pack["asset_validation_rules"]
        self.assertTrue(rules)
        for rule in rules:
            self.assertIn("required_fields", rule)
            self.assertIn("blocked_validation_behaviors", rule)
            self.assertFalse(rule["real_media_validation_performed"])
            self.assertFalse(rule["real_execution_allowed"])

        storage_boundaries = pack["storage_transfer_boundaries"]
        self.assertTrue(storage_boundaries)
        for boundary in storage_boundaries:
            self.assertIn("no upload", boundary["storage_boundary"])
            self.assertIn("no download", boundary["storage_boundary"])
            self.assertIn("no storage write", boundary["storage_boundary"])
            self.assertFalse(boundary["media_upload_allowed"])
            self.assertFalse(boundary["media_download_allowed"])
            self.assertFalse(boundary["storage_write_allowed"])
            self.assertFalse(boundary["external_service_call_allowed"])
            self.assertFalse(boundary["database_write_allowed"])
            self.assertFalse(boundary["real_execution_allowed"])

        policy_map = pack["asset_failure_policy_map"]
        self.assertTrue(policy_map)
        for item in policy_map:
            self.assertEqual(
                item["source_pack"],
                "workspace_provider_failure_taxonomy_pack",
            )
            self.assertFalse(item["real_retry_allowed"])
            self.assertFalse(item["real_rollback_allowed"])
            self.assertFalse(item["real_restore_allowed"])
            self.assertFalse(item["real_execution_allowed"])

        checks = pack["asset_quality_checks"]
        for key in [
            "asset_contract_summary_present",
            "source_adapter_contract_pack_present",
            "source_contract_test_pack_present",
            "source_mock_invocation_result_pack_present",
            "source_failure_taxonomy_pack_present",
            "source_permission_matrix_pack_present",
            "provider_asset_contract_cards_present",
            "media_manifest_cards_present",
            "all_required_provider_types_covered",
            "all_contract_cards_block_media_upload",
            "all_contract_cards_block_media_download",
            "all_contract_cards_block_real_generation",
            "all_contract_cards_block_real_invocation",
            "all_contract_cards_block_real_execution",
            "manifests_block_real_media_operations",
            "input_requirements_do_not_read_files",
            "output_requirements_do_not_write_files",
            "storage_boundaries_block_transfer_and_storage",
            "failure_policy_map_does_not_retry_or_rollback",
            "audit_preview_not_persisted",
        ]:
            with self.subTest(check=key):
                self.assertTrue(checks[key])
        for key in [
            "real_media_operation_performed",
            "provider_invocation_performed",
            "real_execution_performed",
            "database_write_performed",
        ]:
            with self.subTest(check=key):
                self.assertFalse(checks[key])

        audit = pack["audit_preview"]
        self.assertTrue(audit["asset_contract_pack_id"])
        self.assertFalse(audit["is_real_media_pipeline"])
        self.assertFalse(audit["provider_invocation_performed"])
        self.assertFalse(audit["provider_called"])
        self.assertFalse(audit["llm_called"])
        self.assertFalse(audit["image_generation_performed"])
        self.assertFalse(audit["video_generation_performed"])
        self.assertFalse(audit["media_upload_performed"])
        self.assertFalse(audit["media_download_performed"])
        self.assertFalse(audit["file_read_performed"])
        self.assertFalse(audit["file_write_performed"])
        self.assertFalse(audit["storage_write_performed"])
        self.assertFalse(audit["secret_read_performed"])
        self.assertFalse(audit["database_write_performed"])
        self.assertFalse(audit["real_retry_executed"])
        self.assertFalse(audit["real_rollback_executed"])
        self.assertFalse(audit["real_restore_executed"])
        self.assertFalse(audit["audit_persisted"])

        boundaries = pack["safety_boundaries"]
        for key in [
            "provider_enabled", "llm_enabled", "image_enabled",
            "video_enabled", "media_enabled", "paid_enabled",
            "registry_enabled", "rollback_enabled",
            "external_scraping_enabled", "database_persistence_enabled",
            "real_restore_enabled", "real_execution_enabled",
        ]:
            with self.subTest(boundary=key):
                self.assertFalse(boundaries[key])

    def test_workspace_provider_cost_quota_risk_guard_pack_is_preview_only(self):
        payload = {
            "workspace_id": "workspace-provider-cost-quota-risk-guard",
            "source": "manual_import",
            "output_language": "en",
            "products": [{
                "platform": "manual",
                "asin": "PROVIDERCOST001",
                "title": "Compact Travel Mug",
                "reviews": [{
                    "rating": 2,
                    "title": "Leaks during commute",
                    "text": "Leaks during commute and needs a better seal.",
                    "source_section": "manual_review",
                }],
            }],
        }
        response = self.client.post(
            "/api/v1/analyze-review-workspace", json=payload
        )
        self.assertEqual(response.status_code, 200)
        creative_pack = response.json()["creative_decision_pack"]
        for existing_pack in [
            "review_import_pack", "competitor_review_comparison_pack",
            "llm_assist_dry_run_pack",
            "video_provider_orchestration_dry_run_pack",
            "campaign_export_pack", "workspace_session_snapshot_pack",
            "workspace_run_compare_pack", "workspace_action_queue_pack",
            "workspace_action_ticket_pack",
            "workspace_approval_decision_pack",
            "workspace_execution_readiness_pack",
            "workspace_execution_rehearsal_pack",
            "workspace_rehearsal_result_pack",
            "workspace_rehearsal_remediation_pack",
            "workspace_remediation_verification_pack",
            "workspace_retry_rehearsal_plan_pack",
            "workspace_retry_rehearsal_result_pack",
            "workspace_retry_cycle_decision_pack",
            "workspace_cycle_history_timeline_pack",
            "workspace_control_center_pack",
            "workspace_agent_run_ledger_pack",
            "workspace_human_review_queue_pack",
            "workspace_capability_permission_matrix_pack",
            "workspace_system_integration_health_pack",
            "workspace_replay_harness_pack",
            "workspace_provider_adapter_contract_pack",
            "workspace_provider_contract_test_pack",
            "workspace_provider_mock_invocation_result_pack",
            "workspace_provider_failure_taxonomy_pack",
            "workspace_provider_asset_contract_pack",
            "workspace_provider_cost_quota_risk_guard_pack",
        ]:
            with self.subTest(existing_pack=existing_pack):
                self.assertIn(existing_pack, creative_pack)

        pack = creative_pack["workspace_provider_cost_quota_risk_guard_pack"]
        self.assertEqual(
            pack["pack_version"],
            "workspace_provider_cost_quota_risk_guard_pack_v1",
        )
        required_provider_types = {
            "llm_text_generation",
            "video_generation_provider",
            "image_generation_provider",
            "media_storage_provider",
            "external_scraping_provider",
            "translation_provider",
            "analytics_or_tracking_provider",
            "database_persistence_provider",
            "approval_or_ticket_provider",
            "rollback_restore_provider",
        }

        summary = pack["cost_quota_risk_summary"]
        self.assertTrue(summary["guard_id"])
        self.assertIn("cost_quota_risk_preview", summary["mode"])
        self.assertIn("quota_guard_preview", summary["mode"])
        self.assertIn("dry_run_only", summary["mode"])
        for source_pack in [
            "workspace_provider_asset_contract_pack",
            "workspace_provider_failure_taxonomy_pack",
            "workspace_provider_mock_invocation_result_pack",
            "workspace_provider_adapter_contract_pack",
            "workspace_capability_permission_matrix_pack",
            "workspace_system_integration_health_pack",
        ]:
            with self.subTest(source_pack=source_pack):
                self.assertIn(source_pack, summary["source_packs"])
        self.assertFalse(summary["paid_operation_allowed"])
        self.assertFalse(summary["real_quota_check_allowed"])
        self.assertFalse(summary["real_invocation_allowed"])
        self.assertFalse(summary["real_execution_allowed"])

        cost_cards = pack["provider_cost_risk_cards"]
        self.assertTrue(cost_cards)
        self.assertTrue(required_provider_types <= {
            card["provider_type"] for card in cost_cards
        })
        for card in cost_cards:
            for field in [
                "cost_risk_id", "provider_id", "provider_type",
                "source_capability", "estimated_cost_level",
                "quota_risk_level", "paid_operation_required",
                "paid_operation_allowed", "quota_check_mode",
                "usage_tracking_mode", "cost_review_required",
                "approval_required", "blocked_by",
                "recommended_operator_action", "real_invocation_allowed",
                "real_execution_allowed", "risk_note",
            ]:
                with self.subTest(card=card["cost_risk_id"], field=field):
                    self.assertIn(field, card)
            self.assertIn("preview", card["estimated_cost_level"])
            self.assertIn("preview", card["quota_risk_level"])
            self.assertIn("no_real_quota_read", card["quota_check_mode"])
            self.assertIn("no_usage_api", card["usage_tracking_mode"])
            self.assertFalse(card["paid_operation_allowed"])
            self.assertFalse(card["real_invocation_allowed"])
            self.assertFalse(card["real_execution_allowed"])

        quota_cards = pack["quota_guard_cards"]
        self.assertTrue(quota_cards)
        self.assertTrue(required_provider_types <= {
            card["provider_type"] for card in quota_cards
        })
        for card in quota_cards:
            for field in [
                "quota_guard_id", "provider_id", "provider_type",
                "guard_type", "guard_status", "allowed_preview_usage",
                "blocked_real_usage", "quota_source", "quota_available",
                "quota_enforcement_mode", "requires_human_review",
                "real_quota_check_allowed", "real_execution_allowed",
                "risk_note",
            ]:
                with self.subTest(card=card["quota_guard_id"], field=field):
                    self.assertIn(field, card)
            self.assertIn("blocked", card["guard_status"])
            self.assertIn("real_provider_usage_api", card["blocked_real_usage"])
            self.assertIn("real_quota_read", card["blocked_real_usage"])
            self.assertFalse(card["real_quota_check_allowed"])
            self.assertFalse(card["real_execution_allowed"])

        budget_cards = pack["budget_policy_cards"]
        self.assertTrue(budget_cards)
        for card in budget_cards:
            self.assertIn("future_budget_policy_preview_only", card["policy_mode"])
            self.assertFalse(card["paid_operation_allowed"])
            self.assertFalse(card["paid_operation_executed"])
            self.assertFalse(card["budget_enforcement_performed"])
            self.assertFalse(card["real_execution_allowed"])

        usage_boundaries = pack["usage_limit_boundaries"]
        self.assertTrue(usage_boundaries)
        for boundary in usage_boundaries:
            self.assertIn("no_real_usage_api", boundary["boundary_mode"])
            self.assertIn("no_usage_log", boundary["boundary_mode"])
            self.assertFalse(boundary["usage_api_called"])
            self.assertFalse(boundary["usage_log_written"])
            self.assertFalse(boundary["billing_read_performed"])
            self.assertFalse(boundary["quota_read_performed"])
            self.assertFalse(boundary["provider_invocation_performed"])
            self.assertFalse(boundary["real_execution_allowed"])

        blockers = pack["paid_operation_blockers"]
        self.assertTrue(blockers)
        for blocker in blockers:
            self.assertEqual(blocker["blocker_type"], "paid_operation_blocked")
            self.assertIn("blocked", blocker["blocker_status"])
            self.assertFalse(blocker["paid_operation_allowed"])
            self.assertFalse(blocker["paid_operation_executed"])
            self.assertFalse(blocker["real_execution_allowed"])

        policy_map = pack["cost_failure_policy_map"]
        self.assertTrue(policy_map)
        for item in policy_map:
            self.assertEqual(
                item["source_pack"],
                "workspace_provider_failure_taxonomy_pack",
            )
            self.assertFalse(item["real_retry_allowed"])
            self.assertFalse(item["real_rollback_allowed"])
            self.assertFalse(item["real_restore_allowed"])
            self.assertFalse(item["real_execution_allowed"])

        approval_requirements = pack["approval_cost_review_requirements"]
        self.assertTrue(approval_requirements)
        for requirement in approval_requirements:
            self.assertTrue(requirement["requires_human_cost_review"])
            self.assertTrue(requirement["requires_quota_review"])
            self.assertFalse(requirement["real_approval_created"])
            self.assertFalse(requirement["operator_task_created"])
            self.assertFalse(requirement["paid_operation_allowed"])
            self.assertFalse(requirement["real_execution_allowed"])

        matrix = pack["risk_score_matrix"]
        self.assertTrue(matrix["matrix_id"])
        self.assertIn("deterministic_preview_score", matrix["mode"])
        self.assertTrue(matrix["entries"])
        self.assertTrue(required_provider_types <= {
            item["provider_type"] for item in matrix["entries"]
        })
        self.assertFalse(matrix["real_billing_read_performed"])
        self.assertFalse(matrix["real_quota_read_performed"])
        self.assertFalse(matrix["real_service_data_read"])
        self.assertFalse(matrix["real_execution_allowed"])

        checks = pack["cost_guard_quality_checks"]
        for key in [
            "source_asset_contract_pack_present",
            "source_failure_taxonomy_pack_present",
            "source_mock_invocation_result_pack_present",
            "source_adapter_contract_pack_present",
            "source_permission_matrix_pack_present",
            "source_system_integration_health_pack_present",
            "all_required_provider_types_covered",
            "provider_cost_risk_cards_present",
            "quota_guard_cards_present",
            "budget_policy_cards_present",
            "usage_limit_boundaries_present",
            "paid_operation_blockers_present",
            "cost_failure_policy_map_present",
            "approval_cost_review_requirements_present",
            "risk_score_matrix_present",
            "all_paid_operations_blocked",
            "all_quota_checks_preview_only",
            "all_real_invocation_disabled",
            "all_real_execution_disabled",
            "usage_boundaries_do_not_call_usage_api",
            "usage_boundaries_do_not_write_usage_log",
            "cost_failure_policy_does_not_retry_or_rollback",
            "approval_review_does_not_create_real_approval",
            "risk_score_matrix_is_preview_only",
            "audit_preview_not_persisted",
        ]:
            with self.subTest(check=key):
                self.assertTrue(checks[key])
        for key in [
            "real_billing_read_performed", "real_quota_read_performed",
            "paid_operation_executed", "provider_invocation_performed",
            "database_write_performed", "real_execution_performed",
        ]:
            with self.subTest(check=key):
                self.assertFalse(checks[key])

        audit = pack["audit_preview"]
        self.assertTrue(audit["guard_id"])
        self.assertFalse(audit["is_real_billing_system"])
        self.assertFalse(audit["is_real_quota_system"])
        self.assertFalse(audit["provider_invocation_performed"])
        self.assertFalse(audit["provider_called"])
        self.assertFalse(audit["llm_called"])
        self.assertFalse(audit["image_generation_performed"])
        self.assertFalse(audit["video_generation_performed"])
        self.assertFalse(audit["media_upload_performed"])
        self.assertFalse(audit["media_download_performed"])
        self.assertFalse(audit["secret_read_performed"])
        self.assertFalse(audit["real_billing_read_performed"])
        self.assertFalse(audit["real_quota_read_performed"])
        self.assertFalse(audit["real_usage_api_called"])
        self.assertFalse(audit["usage_log_written"])
        self.assertFalse(audit["paid_operation_executed"])
        self.assertFalse(audit["database_write_performed"])
        self.assertFalse(audit["real_log_read_performed"])
        self.assertFalse(audit["real_history_table_read_performed"])
        self.assertFalse(audit["real_service_health_read_performed"])
        self.assertFalse(audit["operator_task_created"])
        self.assertFalse(audit["real_approval_created"])
        self.assertFalse(audit["real_retry_executed"])
        self.assertFalse(audit["real_rollback_executed"])
        self.assertFalse(audit["real_restore_executed"])
        self.assertFalse(audit["registry_write_performed"])
        self.assertFalse(audit["external_scraping_performed"])
        self.assertFalse(audit["audit_persisted"])

        boundaries = pack["safety_boundaries"]
        for key in [
            "provider_enabled", "llm_enabled", "image_enabled",
            "video_enabled", "media_enabled", "paid_enabled",
            "registry_enabled", "rollback_enabled",
            "external_scraping_enabled", "database_persistence_enabled",
            "real_restore_enabled", "real_execution_enabled",
        ]:
            with self.subTest(boundary=key):
                self.assertFalse(boundaries[key])


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
