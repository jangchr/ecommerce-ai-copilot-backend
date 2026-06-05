import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

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
    "target_platform": "TikTok",
    "goal": "tiktok_ctr",
    "output_language": "en",
}


GENERATED_REVIEWS_BRIEF = {
    "target_audience": "Busy smoothie drinkers who want single-serve convenience.",
    "core_hook_strategy": "Open with cleanup frustration and travel convenience.",
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


class VideoAssetLockKeyframeTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def _generate(self):
        with patch(
            "main.generate_pasted_reviews_brief",
            new=AsyncMock(return_value=GENERATED_REVIEWS_BRIEF),
        ):
            response = self.client.post("/api/v1/generate-from-reviews", json=VALID_REVIEWS_REQUEST)

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        return payload["data"]

    def test_external_video_handoff_contains_product_asset_lock_and_keyframe_plan(self):
        data = self._generate()
        handoff = data["external_video_tool_handoff"]

        product_asset_lock = handoff.get("product_asset_lock")
        self.assertIsInstance(product_asset_lock, dict)
        self.assertEqual(product_asset_lock.get("lock_version"), "product_asset_lock_v1")
        self.assertIn("Portable Mini Blender", product_asset_lock.get("product_identity", ""))
        self.assertEqual(product_asset_lock.get("product_category"), "kitchen_appliance")
        self.assertTrue(product_asset_lock.get("must_preserve"))
        self.assertTrue(product_asset_lock.get("must_not_change"))
        self.assertTrue(product_asset_lock.get("image_reference_rules"))
        self.assertTrue(product_asset_lock.get("human_review_required"))

        keyframe_plan = handoff.get("keyframe_plan")
        self.assertIsInstance(keyframe_plan, dict)
        self.assertEqual(keyframe_plan.get("plan_version"), "keyframe_plan_v1")
        self.assertTrue(keyframe_plan.get("review_before_paid_generation"))
        self.assertGreaterEqual(keyframe_plan.get("scene_count", 0), 1)
        first_scene = keyframe_plan["scenes"][0]
        for field in [
            "keyframe_goal",
            "product_position",
            "camera_direction",
            "product_constraints",
            "risk_notes",
        ]:
            with self.subTest(scene_field=field):
                self.assertTrue(first_scene.get(field))

        self.assertIn("product asset lock", handoff["tool_prompts"]["gemini_video_prompt"].lower())
        self.assertIn("keyframe plan", handoff["tool_prompts"]["doubao_video_prompt"].lower())
        self.assertIn("one short clip", handoff["copy_ready_generation_brief"].lower())

    def test_multi_agent_workflow_indexes_asset_lock_and_keyframe_artifacts(self):
        data = self._generate()
        workflow = data["multi_agent_workflow"]
        artifact_index = workflow["artifact_index"]
        self.assertTrue(artifact_index.get("product_asset_lock"))
        self.assertTrue(artifact_index.get("keyframe_plan"))

        agents = {agent["agent_id"]: agent for agent in workflow["agents"]}
        asset_lock_agent = agents["asset_lock_agent"]
        asset_outputs = asset_lock_agent["key_outputs"]
        self.assertEqual(asset_outputs.get("asset_lock_version"), "product_asset_lock_v1")
        self.assertIn("Portable Mini Blender", asset_outputs.get("product_identity", ""))
        self.assertTrue(asset_outputs.get("must_preserve"))
        self.assertTrue(asset_outputs.get("must_not_change"))

        keyframe_agent = agents["keyframe_agent"]
        keyframe_outputs = keyframe_agent["key_outputs"]
        self.assertEqual(keyframe_outputs.get("keyframe_plan_version"), "keyframe_plan_v1")
        self.assertGreaterEqual(keyframe_outputs.get("keyframe_plan_scene_count", 0), 1)
        self.assertIn("one short clip", keyframe_outputs.get("recommended_clip_strategy", "").lower())


if __name__ == "__main__":
    unittest.main()
