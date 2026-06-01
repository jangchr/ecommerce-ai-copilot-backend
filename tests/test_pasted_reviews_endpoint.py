import asyncio
import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

import main
from main import app


VALID_REVIEWS_REQUEST = {
    "product_name": "Portable Mini Blender",
    "product_category": "kitchen_appliance",
    "product_description": "A compact rechargeable blender for smoothies and travel.",
    "pasted_reviews": (
        "Hard to clean after one smoothie.\n"
        "Too loud for early mornings.\n"
        "Small enough for travel but the cup sometimes leaks in my bag."
    ),
}


GENERATED_REVIEWS_BRIEF = {
    "target_audience": "Busy smoothie drinkers who want single-serve convenience.",
    "core_hook_strategy": "Open with the cleanup frustration and contrast it with a quick rinse routine.",
    "emotional_trigger": "Relief from noisy, messy morning prep.",
    "hook": "Your blender should not make one smoothie feel like a full kitchen cleanup.",
    "cta": "Try a compact blender built around quick daily use.",
    "storyboard_scenes": [
        {
            "visual_description": "A sink full of blender parts after one drink.",
            "narration": "One smoothie should not create this much cleanup.",
            "evidence_quote_used": "Hard to clean after one smoothie.",
        },
        {
            "visual_description": "A person hesitates before blending early in the morning.",
            "narration": "The noise makes the routine feel harder.",
            "evidence_quote_used": "Too loud for early mornings.",
        },
        {
            "visual_description": "The compact cup slides into a backpack pocket.",
            "narration": "A smaller setup makes the habit easier to keep.",
            "evidence_quote_used": "Small enough for travel.",
        },
        {
            "visual_description": "The product is rinsed quickly after a shake.",
            "narration": "Make the daily drink feel simple again.",
            "evidence_quote_used": "Hard to clean after one smoothie.",
        },
    ],
    "evaluation_reasoning": "Grounded in pasted customer complaint snippets.",
    "feedback": "Verify pasted reviews before paid use.",
}


ZH_REVIEWS_DATA = {
    "insights": {
        "pain_points": ["\u6e05\u6d17\u9ebb\u70e6", "\u65e9\u4e0a\u592a\u5435"],
        "user_complaint_cluster": ["\u6e05\u6d17\u9ebb\u70e6"],
        "evidence": {
            "source_type": "user_pasted_reviews",
            "source_url": "",
            "confidence": 0.64,
            "review_confidence": 0.64,
            "trend_confidence": 0.0,
            "review_count": 3,
            "evidence_quotes": ["\u4e00\u676f\u679c\u6614\u540e\u5f88\u96be\u6e05\u6d17"],
            "trend_signals": [],
            "data_warnings": [
                "user_pasted_reviews_unverified",
                "user_pasted_reviews_no_external_fetch",
            ],
        },
    },
    "audience": {
        "primary": "\u9700\u8981\u5feb\u901f\u505a\u679c\u6614\u7684\u5fd9\u788c\u7528\u6237",
        "sensitivity": "\u6015\u9ebb\u70e6",
        "trust_barriers": ["\u62c5\u5fc3\u6e05\u6d17"],
    },
    "strategy": {
        "core_hook_strategy": "\u7528\u6e05\u6d17\u75db\u70b9\u505a\u5f00\u573a",
        "emotional_trigger": "\u4ece\u9ebb\u70e6\u5230\u8f7b\u677e",
    },
    "assets": {
        "tiktok_script": {
            "hook": "\u8fd9\u662f\u6765\u81ea\u7c98\u8d34\u8bc4\u8bba\u7684\u4e2d\u6587 Hook",
            "cta": "\u8bd5\u8bd5\u66f4\u8f7b\u677e\u7684\u679c\u6614\u65b9\u5f0f",
        },
        "storyboard": {
            "source": "user_pasted_reviews",
            "scenes": [
                {
                    "scene_id": 1,
                    "visual_description": "\u5c55\u793a\u6e05\u6d17\u9ebb\u70e6",
                    "narration": "\u4e00\u676f\u679c\u6614\u4e0d\u5e94\u8be5\u8fd9\u4e48\u9ebb\u70e6",
                    "evidence_quote_used": "\u4e00\u676f\u679c\u6614\u540e\u5f88\u96be\u6e05\u6d17",
                }
            ],
        },
    },
    "evaluation": {
        "confidence_score": 0.66,
        "risk_level": "medium",
        "reasoning": "\u57fa\u4e8e\u7c98\u8d34\u8bc4\u8bba\u751f\u6210",
        "is_approved": True,
        "is_grounded": True,
        "creative_approved": True,
        "grounded_approved": True,
    },
    "feedback": "\u4f7f\u7528\u524d\u8bf7\u6838\u5b9e\u8bc4\u8bba\u771f\u5b9e\u6027",
}


class PastedReviewsEndpointTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_success_returns_product_like_response_from_pasted_reviews(self):
        with patch(
            "main.generate_pasted_reviews_brief",
            new=AsyncMock(return_value=GENERATED_REVIEWS_BRIEF),
        ) as generate:
            response = self.client.post(
                "/api/v1/generate-from-reviews",
                json=VALID_REVIEWS_REQUEST,
                headers={"X-Request-ID": "reviews-success-1"},
            )

        self.assertEqual(response.status_code, 200)
        generate.assert_awaited_once()
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["output_language"], "en")
        self.assertEqual(payload["request_id"], "reviews-success-1")
        for field in ["insights", "audience", "strategy", "assets", "evaluation", "feedback", "llm_evidence_packet"]:
            with self.subTest(field=field):
                self.assertIn(field, payload["data"])

        packet = payload["data"]["llm_evidence_packet"]
        for section in ["product", "review_stats", "evidence", "generation_constraints"]:
            with self.subTest(packet_section=section):
                self.assertIn(section, packet)
        self.assertEqual(packet["packet_version"], "pasted_reviews_v1")
        self.assertEqual(packet["product"]["title"], "Portable Mini Blender")
        self.assertEqual(packet["product"]["source_type"], "user_pasted_reviews")
        self.assertEqual(packet["review_stats"]["review_count"], 3)
        self.assertIn("user_pasted_reviews_unverified", packet["review_stats"]["warnings"])
        self.assertIn("Use only the supplied review evidence and product fields.", packet["generation_constraints"])
        self.assertIn("Hard to clean after one smoothie", "\n".join(packet["evidence"]["quotes"]))

        evidence = payload["data"]["insights"]["evidence"]
        self.assertEqual(evidence["source_type"], "user_pasted_reviews")
        self.assertEqual(evidence["source_url"], "")
        self.assertEqual(evidence["review_count"], 3)
        self.assertIn("Hard to clean", evidence["evidence_quotes"][0])
        self.assertIn("user_pasted_reviews_unverified", evidence["data_warnings"])
        self.assertIn("user_pasted_reviews_no_external_fetch", evidence["data_warnings"])
        self.assertEqual(payload["data"]["assets"]["storyboard"]["source"], "user_pasted_reviews")
        self.assertNotIn("telemetry_summary", payload)
        self.assertNotIn("shadow_sources", payload)
        self.assertNotIn("memory_observability", payload)

    def test_pasted_reviews_generation_prompt_uses_llm_evidence_packet(self):
        class CapturingLLM:
            def __init__(self):
                self.messages = None

            async def ainvoke(self, messages):
                self.messages = messages
                return SimpleNamespace(
                    content=json.dumps(
                        {
                            "target_audience": "Evidence packet audience",
                            "core_hook_strategy": "Use packet evidence only",
                            "emotional_trigger": "Relief",
                            "hook": "Evidence packet hook",
                            "cta": "Evidence packet CTA",
                            "storyboard_scenes": [
                                {
                                    "visual_description": "Show cleanup frustration.",
                                    "narration": "One smoothie should not make cleanup hard.",
                                    "evidence_quote_used": "Hard to clean after one smoothie",
                                }
                            ],
                            "evaluation_reasoning": "Uses packet evidence.",
                            "feedback": "Packet prompt generated.",
                        }
                    )
                )

        fake_llm = CapturingLLM()
        with patch("main.ChatOpenAI", return_value=fake_llm), patch(
            "main._pasted_reviews_llm_prompt_content",
            wraps=main._pasted_reviews_llm_prompt_content,
        ) as prompt_builder:
            result = asyncio.run(
                main.generate_pasted_reviews_brief(
                    SimpleNamespace(**VALID_REVIEWS_REQUEST),
                    [
                        "Hard to clean after one smoothie",
                        "Too loud for early mornings",
                        "Small enough for travel but the cup sometimes leaks in my bag",
                    ],
                )
            )

        prompt_builder.assert_called_once()
        prompt = fake_llm.messages[1].content
        self.assertIn("llm_evidence_packet JSON", prompt)
        self.assertIn('"packet_version": "pasted_reviews_v1"', prompt)
        self.assertIn('"generation_constraints"', prompt)
        self.assertIn("Do not turn buyer objections into positive claims", prompt)
        self.assertNotIn("Pasted review evidence:", prompt)
        self.assertEqual(result["hook"], "Evidence packet hook")

    def test_pasted_reviews_generation_prompt_accepts_review_workspace_packet(self):
        class CapturingLLM:
            def __init__(self):
                self.messages = None

            async def ainvoke(self, messages):
                self.messages = messages
                return SimpleNamespace(
                    content=json.dumps(
                        {
                            "target_audience": "Workspace packet audience",
                            "core_hook_strategy": "Use workspace packet evidence only",
                            "emotional_trigger": "Confidence",
                            "hook": "Workspace packet hook",
                            "cta": "Workspace packet CTA",
                            "storyboard_scenes": [
                                {
                                    "visual_description": "Show the supplied workspace concern.",
                                    "narration": "Use the workspace packet as evidence.",
                                    "evidence_quote_used": "Hard to clean after one smoothie.",
                                }
                            ],
                            "evaluation_reasoning": "Uses review workspace packet.",
                            "feedback": "Workspace packet prompt generated.",
                        }
                    )
                )

        workspace_packet = {
            "packet_version": "review_workspace_v1",
            "intended_model_use": "creative_brief_generation",
            "product": {
                "title": "Portable Mini Blender",
                "source_type": "review_workspace",
                "product_count": 1,
            },
            "review_stats": {
                "total_reviews": 3,
                "parsed_reviews": 3,
                "warnings": [],
            },
            "evidence": {
                "buyer_objections": [
                    {
                        "label": "cleanup",
                        "evidence_quotes": ["Hard to clean after one smoothie."],
                    }
                ],
                "positive_signals": [
                    {
                        "label": "portable",
                        "evidence_quotes": ["Small enough for travel and easy to carry."],
                    }
                ],
                "quotes": [
                    "Hard to clean after one smoothie.",
                    "Small enough for travel and easy to carry.",
                ],
            },
            "generation_constraints": [
                "Use only supplied review evidence and product fields.",
                "Do not generalize one variant/color/size issue to the whole product unless multiple reviews support it.",
                "Do not turn buyer objections into positive claims unless evidence explicitly resolves the concern.",
            ],
        }
        fake_llm = CapturingLLM()

        with patch("main.ChatOpenAI", return_value=fake_llm):
            result = asyncio.run(
                main.generate_pasted_reviews_brief(
                    SimpleNamespace(**VALID_REVIEWS_REQUEST, llm_evidence_packet=workspace_packet),
                    ["fallback compact review should not be the prompt evidence"],
                )
            )

        prompt = fake_llm.messages[1].content
        self.assertIn("llm_evidence_packet JSON", prompt)
        self.assertIn('"packet_version": "review_workspace_v1"', prompt)
        self.assertIn("Do not generalize one variant/color/size issue", prompt)
        self.assertIn("Do not turn buyer objections into positive claims", prompt)
        self.assertNotIn("Pasted review evidence:", prompt)
        self.assertNotIn("fallback compact review should not be the prompt evidence", prompt)
        self.assertEqual(result["hook"], "Workspace packet hook")

    def test_generate_from_reviews_accepts_review_workspace_packet(self):
        workspace_packet = {
            "packet_version": "review_workspace_v1",
            "intended_model_use": "creative_brief_generation",
            "product": {
                "title": "Portable Mini Blender",
                "source_type": "review_workspace",
                "product_count": 1,
            },
            "review_stats": {
                "total_reviews": 3,
                "parsed_reviews": 3,
                "warnings": [],
            },
            "evidence": {
                "buyer_objections": [
                    {
                        "label": "cleanup",
                        "evidence_quotes": ["Hard to clean after one smoothie."],
                    }
                ],
                "positive_signals": [
                    {
                        "label": "portable",
                        "evidence_quotes": ["Small enough for travel and easy to carry."],
                    }
                ],
                "quotes": [
                    "Hard to clean after one smoothie.",
                    "Small enough for travel and easy to carry.",
                ],
            },
            "generation_constraints": [
                "Use only supplied review evidence and product fields.",
                "Do not generalize one variant/color/size issue to the whole product unless multiple reviews support it.",
            ],
        }

        with patch("main.generate_pasted_reviews_brief", new=AsyncMock(return_value=GENERATED_REVIEWS_BRIEF)) as generate:
            response = self.client.post(
                "/api/v1/generate-from-reviews",
                json={**VALID_REVIEWS_REQUEST, "llm_evidence_packet": workspace_packet},
            )

        self.assertEqual(response.status_code, 200)
        request_arg = generate.await_args.args[0]
        self.assertEqual(request_arg.llm_evidence_packet, workspace_packet)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["data"]["llm_evidence_packet"]["packet_version"], "review_workspace_v1")
        self.assertEqual(payload["data"]["llm_evidence_packet"]["product"]["source_type"], "review_workspace")

    def test_root_beer_amazon_reviews_are_cleaned_and_classified(self):
        root_beer_reviews = (
            "[5 out of 5 stars]\n"
            "Reviewed in the United States on May 12, 2026\n"
            "Verified Purchase\n"
            "This is the best Rootbeer I have ever had and order it frequently.\n"
            "Love it and will continue to purchase.\n"
            "5 out of 5 stars Great flavor Reviewed in the United States on May 13, 2026 Verified Purchase Not as sharp as Barq's, but smoother, greater flavor than A&W.\n"
            "Good root beer, just not worth the high price over something like IBC, which is half the price.\n"
            "Best root beer and unfortunately not available on the West coast.\n"
            "2026年5月12日在美国评论 已验证购买 有史以来最好的根汁汽水"
        )
        generated = {
            **GENERATED_REVIEWS_BRIEF,
            "storyboard_scenes": [
                {
                    "visual_description": "Show a chilled pour.",
                    "narration": "Lead with the review signal.",
                    "evidence_quote_used": "This is the best Rootbeer I have ever had and order it frequently.",
                    "scene_goal": "Show pasted review pain point",
                },
                {
                    "visual_description": "Show a price comparison.",
                    "narration": "Address the buyer concern.",
                    "evidence_quote_used": "Good root beer, just not worth the high price over something like IBC, which is half the price.",
                    "scene_goal": "Show pasted review pain point",
                },
            ],
        }

        with patch("main.generate_pasted_reviews_brief", new=AsyncMock(return_value=generated)):
            response = self.client.post(
                "/api/v1/generate-from-reviews",
                json={
                    **VALID_REVIEWS_REQUEST,
                    "product_name": "1919 Draft Root Beer",
                    "product_category": "root_beer",
                    "pasted_reviews": root_beer_reviews,
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        data = payload["data"]
        evidence = data["insights"]["evidence"]
        evidence_text = "\n".join(evidence["evidence_quotes"])

        self.assertIn("This is the best Rootbeer I have ever had", evidence_text)
        self.assertIn("有史以来最好的根汁汽水", evidence_text)
        for noisy in [
            "5 out of 5 stars",
            "Reviewed in the United States",
            "Verified Purchase",
            "2026年5月12日在美国评论",
            "已验证购买",
        ]:
            self.assertNotIn(noisy, evidence_text)

        pain_text = "\n".join(data["insights"].get("pain_points", []))
        trust_text = "\n".join(data["audience"].get("trust_barriers", []))
        positive_text = "\n".join(data["insights"].get("positive_signals", []))

        self.assertNotIn("Love it and will continue to purchase", pain_text)
        self.assertNotIn("This is the best Rootbeer", pain_text)
        self.assertNotIn("Love it and will continue to purchase", trust_text)
        self.assertNotIn("This is the best Rootbeer", trust_text)
        self.assertIn("Love it and will continue to purchase", positive_text)
        self.assertIn("This is the best Rootbeer", positive_text)
        self.assertIn("high price", trust_text)
        self.assertIn("West coast", trust_text)

        scene_goals = " ".join(
            scene.get("scene_goal", "")
            for scene in data["assets"]["storyboard"]["scenes"]
        )
        self.assertIn("positive review signal", scene_goals)
        self.assertIn("buyer objection", scene_goals)
        self.assertNotIn("review pain point", scene_goals.lower())

    def test_balsamic_value_signals_spout_concern_and_reviewer_names_are_cleaned(self):
        balsamic_reviews = (
            "Amy Worth the price and Cannot beat the price for this quality.\n"
            "retired303 Quality item. Value priced and excellent flavor.\n"
            "analogkid Yes it's pricy but personally I think it's worth it.\n"
            "Amazon Customer However, there is not lid to go over the spout, so air is ever present and oxidation is a concern.\n"
        )
        generated = {
            **GENERATED_REVIEWS_BRIEF,
            "storyboard_scenes": [
                {
                    "visual_description": "Show balsamic being poured cleanly.",
                    "narration": "Lead with the value signal.",
                    "evidence_quote_used": "Worth the price and Cannot beat the price for this quality.",
                },
                {
                    "visual_description": "Show the open spout.",
                    "narration": "Call out the packaging concern.",
                    "evidence_quote_used": "However, there is not lid to go over the spout, so air is ever present and oxidation is a concern.",
                },
            ],
        }

        with patch(
            "main.generate_pasted_reviews_brief",
            new=AsyncMock(return_value=generated),
        ) as generate:
            response = self.client.post(
                "/api/v1/generate-from-reviews",
                json={
                    **VALID_REVIEWS_REQUEST,
                    "product_name": "Balsamic Vinegar",
                    "product_category": "balsamic_vinegar",
                    "pasted_reviews": balsamic_reviews,
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        evidence_quotes = generate.await_args.args[1]
        evidence_text = "\n".join(evidence_quotes)
        data = payload["data"]
        positive_text = "\n".join(data["insights"].get("positive_signals", []))
        trust_text = "\n".join(data["audience"].get("trust_barriers", []))
        pain_text = "\n".join(data["insights"].get("pain_points", []))

        for reviewer_name in ["Amy", "retired303", "analogkid", "Amazon Customer"]:
            self.assertNotIn(reviewer_name, evidence_text)

        self.assertIn("Worth the price", positive_text)
        self.assertIn("Cannot beat the price", positive_text)
        self.assertIn("Value priced", positive_text)
        self.assertIn("pricy", positive_text)

        self.assertNotIn("Cannot beat the price", trust_text)
        self.assertNotIn("Value priced", trust_text)
        self.assertNotIn("Cannot beat the price", pain_text)
        self.assertNotIn("Value priced", pain_text)
        self.assertIn("pricy", trust_text)
        self.assertIn("spout", trust_text)
        self.assertIn("oxidation", trust_text)

    def test_long_repeated_amazon_reviews_compact_before_generation(self):
        dirty_reviews = "\n".join(
            [
                "[5 out of 5 stars]",
                "Reviewed in the United States on May 12, 2026",
                "Verified Purchase",
                "Flavor Name: Traditional Size: 16.9 Fl Oz",
                "This balsamic has a rich flavor and works well on salads.",
                "Good taste, but the cap leaked during shipping.",
                "This balsamic has a rich flavor and works well on salads.",
                "Submit a review",
            ]
            * 90
        )
        self.assertGreater(len(dirty_reviews), 6000)

        with patch(
            "main.generate_pasted_reviews_brief",
            new=AsyncMock(return_value=GENERATED_REVIEWS_BRIEF),
        ) as generate:
            response = self.client.post(
                "/api/v1/generate-from-reviews",
                json={
                    **VALID_REVIEWS_REQUEST,
                    "product_name": "Balsamic Vinegar",
                    "product_category": "balsamic_vinegar",
                    "pasted_reviews": dirty_reviews,
                },
            )

        self.assertEqual(response.status_code, 200)
        generate.assert_awaited_once()
        evidence_quotes = generate.await_args.args[1]
        evidence_text = "\n".join(evidence_quotes)
        self.assertLessEqual(len(evidence_quotes), 12)
        self.assertIn("rich flavor", evidence_text)
        self.assertIn("cap leaked", evidence_text)
        self.assertEqual(sum("This balsamic has a rich flavor" in quote for quote in evidence_quotes), 1)
        for noisy in [
            "5 out of 5 stars",
            "Reviewed in the United States",
            "Verified Purchase",
            "Flavor Name",
            "Size:",
            "Submit a review",
        ]:
            self.assertNotIn(noisy, evidence_text)

    def test_explicit_english_language_succeeds(self):
        with patch(
            "main.generate_pasted_reviews_brief",
            new=AsyncMock(return_value=GENERATED_REVIEWS_BRIEF),
        ):
            response = self.client.post(
                "/api/v1/generate-from-reviews",
                json={**VALID_REVIEWS_REQUEST, "output_language": "en"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["output_language"], "en")

    def test_chinese_language_translates_visible_product_payload(self):
        with patch(
            "main.generate_pasted_reviews_brief",
            new=AsyncMock(return_value=GENERATED_REVIEWS_BRIEF),
        ), patch(
            "main.translate_product_visible_data",
            new=AsyncMock(return_value=ZH_REVIEWS_DATA),
        ) as translate:
            response = self.client.post(
                "/api/v1/generate-from-reviews",
                json={**VALID_REVIEWS_REQUEST, "output_language": "zh-CN"},
            )

        self.assertEqual(response.status_code, 200)
        translate.assert_awaited_once()
        payload = response.json()
        self.assertEqual(payload["output_language"], "zh-CN")
        self.assertIn("\u4e2d\u6587", payload["data"]["assets"]["tiktok_script"]["hook"])
        self.assertEqual(payload["data"]["insights"]["evidence"]["source_type"], "user_pasted_reviews")
        self.assertNotIn("telemetry_summary", payload)
        self.assertNotIn("shadow_sources", payload)
        self.assertNotIn("memory_observability", payload)

    def test_chinese_language_repairs_utf8_mojibake_from_translation_provider(self):
        def mojibake(text):
            return text.encode("utf-8").decode("latin1")

        provider_payload = {
            "insights": {
                "pain_points": [mojibake("用户痛点来自评论")],
                "user_complaint_cluster": [mojibake("评论说清洗很麻烦")],
                "evidence": {
                    "source_type": "user_pasted_reviews",
                    "source_url": "",
                    "confidence": 0.64,
                    "review_confidence": 0.64,
                    "trend_confidence": 0.0,
                    "review_count": 3,
                    "evidence_quotes": [mojibake("用户评论说清洗很麻烦")],
                    "trend_signals": [],
                    "data_warnings": [
                        "user_pasted_reviews_unverified",
                        "user_pasted_reviews_no_external_fetch",
                    ],
                },
            },
            "audience": {
                "primary": mojibake("忙碌用户"),
                "sensitivity": mojibake("怕麻烦"),
                "trust_barriers": [mojibake("担心清洗")],
            },
            "strategy": {
                "core_hook_strategy": mojibake("用评论痛点做开场"),
                "emotional_trigger": mojibake("从麻烦到轻松"),
            },
            "assets": {
                "tiktok_script": {
                    "hook": mojibake("开场直接抓住用户痛点"),
                    "cta": mojibake("试试更轻松的果昔方式"),
                },
                "storyboard": {
                    "source": "user_pasted_reviews",
                    "scenes": [
                        {
                            "scene_id": 1,
                            "visual_description": mojibake("分镜展示清洗麻烦"),
                            "narration": mojibake("用户评论变成开场冲突"),
                            "evidence_quote_used": mojibake("用户评论说清洗很麻烦"),
                        }
                    ],
                },
            },
            "evaluation": {
                "confidence_score": 0.66,
                "risk_level": "medium",
                "reasoning": mojibake("基于粘贴评论生成"),
                "is_approved": True,
                "is_grounded": True,
                "creative_approved": True,
                "grounded_approved": True,
            },
            "feedback": mojibake("请核实评论真实性"),
        }

        with patch(
            "main.generate_pasted_reviews_brief",
            new=AsyncMock(return_value=GENERATED_REVIEWS_BRIEF),
        ), patch(
            "main.translate_visible_output",
            new=AsyncMock(return_value=json.dumps(provider_payload, ensure_ascii=False)),
        ):
            response = self.client.post(
                "/api/v1/generate-from-reviews",
                json={**VALID_REVIEWS_REQUEST, "output_language": "zh-CN"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["output_language"], "zh-CN")
        self.assertEqual(payload["data"]["insights"]["evidence"]["source_type"], "user_pasted_reviews")
        self.assertEqual(payload["data"]["insights"]["evidence"]["source_url"], "")

        response_text = json.dumps(payload, ensure_ascii=False)
        self.assertTrue(any("\u4e00" <= char <= "\u9fff" for char in response_text))
        self.assertTrue(
            any(keyword in response_text for keyword in ["痛点", "评论", "用户", "分镜", "开场"])
        )
        for marker in ["æ", "ä¸", "å®", "ï¼", "ç"]:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, response_text)

        self.assertNotIn("telemetry_summary", payload)
        self.assertNotIn("shadow_sources", payload)
        self.assertNotIn("memory_observability", payload)

    def test_missing_product_name_returns_400(self):
        response = self.client.post(
            "/api/v1/generate-from-reviews",
            json={**VALID_REVIEWS_REQUEST, "product_name": " "},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error_type"], "missing_product_name")

    def test_missing_pasted_reviews_returns_400(self):
        response = self.client.post(
            "/api/v1/generate-from-reviews",
            json={**VALID_REVIEWS_REQUEST, "pasted_reviews": ""},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error_type"], "missing_pasted_reviews")

    def test_short_pasted_reviews_returns_400(self):
        response = self.client.post(
            "/api/v1/generate-from-reviews",
            json={**VALID_REVIEWS_REQUEST, "pasted_reviews": "Too loud."},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error_type"], "pasted_reviews_too_short")

    def test_invalid_output_language_returns_400(self):
        with patch("main.generate_pasted_reviews_brief", new=AsyncMock()) as generate:
            response = self.client.post(
                "/api/v1/generate-from-reviews",
                json={**VALID_REVIEWS_REQUEST, "output_language": "fr"},
                headers={"X-Request-ID": "reviews-invalid-language"},
            )

        self.assertEqual(response.status_code, 400)
        generate.assert_not_awaited()
        payload = response.json()
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error_type"], "unsupported_output_language")
        self.assertEqual(payload["request_id"], "reviews-invalid-language")

    def test_endpoint_does_not_call_workflow_sources_shadow_or_memory(self):
        with patch(
            "main.generate_pasted_reviews_brief",
            new=AsyncMock(return_value=GENERATED_REVIEWS_BRIEF),
        ), patch("main.copilot_engine.ainvoke", new=AsyncMock()) as workflow, patch(
            "main.source_probe_registry.fetch",
        ) as source_fetch, patch("main._amazon_shadow_sources") as shadow, patch(
            "main.memory_engine.save_memory"
        ) as save_memory, patch(
            "main.memory_engine.observability_snapshot"
        ) as memory_snapshot:
            response = self.client.post("/api/v1/generate-from-reviews", json=VALID_REVIEWS_REQUEST)

        self.assertEqual(response.status_code, 200)
        workflow.assert_not_awaited()
        source_fetch.assert_not_called()
        shadow.assert_not_called()
        save_memory.assert_not_called()
        memory_snapshot.assert_not_called()


if __name__ == "__main__":
    unittest.main()
