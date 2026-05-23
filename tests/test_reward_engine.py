import unittest

from core.workflow import RewardEngine


EVIDENCE = {
    "source_type": "local_dataset+mock",
    "confidence": 0.67,
    "review_confidence": 0.75,
    "trend_confidence": 0.35,
    "evidence_quotes": [
        "The cap cracked during shipping and leaked all over the box.",
        "The glaze was too watery and ran off the salad instead of sticking.",
        "It tasted more like sweet syrup than aged balsamic vinegar.",
        "The bottle arrived sticky, and the seal looked like it had already been opened.",
    ],
}


def scene(scene_id, quote, dopamine=False):
    return {
        "scene_id": scene_id,
        "duration_sec": 4,
        "scene_goal": "Show concrete product failure",
        "visual_description": (
            "A close, practical kitchen counter shot shows the bottle, the packaging, the sticky label, "
            "and the exact messy failure in a real household context with no glamour lighting or staged props. "
            "The camera lingers on the practical detail that a buyer would inspect before trusting the product."
        ),
        "narration": (
            "This scene ties the visible product failure directly to the customer quote, making the problem feel "
            "specific, concrete, and impossible to dismiss as generic dissatisfaction."
        ),
        "on_screen_text": "Real customer complaint",
        "camera_motion": "slow_push",
        "camera_speed": 1.0,
        "transition_style": "cut",
        "emotional_intensity": 0.7,
        "audio_emotion": "frustration",
        "dopamine_trigger": dopamine,
        "dopamine_type": "relief" if dopamine else "",
        "retention_reason": "The scene anchors a visible failure to a real customer quote.",
        "linked_painpoint": "Product quality did not match expectations.",
        "evidence_quote_used": quote,
    }


class RewardEngineTest(unittest.TestCase):
    def test_empty_scenes_fail_as_weak_visual(self):
        metrics = RewardEngine.calculate_reward({"scenes": []}, EVIDENCE)
        self.assertFalse(metrics["is_approved"])
        self.assertEqual(metrics["failure_type"], "weak_visual")

    def test_reward_hacking_penalty_when_all_scenes_trigger_dopamine(self):
        scenes = [
            scene(1, EVIDENCE["evidence_quotes"][0], dopamine=True),
            scene(2, EVIDENCE["evidence_quotes"][1], dopamine=True),
            scene(3, EVIDENCE["evidence_quotes"][2], dopamine=True),
        ]
        metrics = RewardEngine.calculate_reward({"scenes": scenes}, EVIDENCE)
        self.assertGreater(metrics["reward_hacking_penalty"], 0)
        self.assertEqual(metrics["failure_type"], "reward_hacking")
        self.assertFalse(metrics["is_approved"])

    def test_mismatched_evidence_quote_fails_alignment(self):
        scenes = [
            scene(1, "This quote does not appear in the evidence.", dopamine=False),
            scene(2, "Another unrelated invented quote.", dopamine=True),
        ]
        metrics = RewardEngine.calculate_reward({"scenes": scenes}, EVIDENCE)
        self.assertLess(metrics["evidence_alignment"], 0.5)
        self.assertEqual(metrics["failure_type"], "no_evidence_alignment")
        self.assertFalse(metrics["is_grounded"])

    def test_local_dataset_matching_quotes_can_be_grounded(self):
        scenes = [
            scene(1, EVIDENCE["evidence_quotes"][0], dopamine=True),
            scene(2, EVIDENCE["evidence_quotes"][1], dopamine=True),
            scene(3, EVIDENCE["evidence_quotes"][2], dopamine=False),
            scene(4, EVIDENCE["evidence_quotes"][3], dopamine=False),
        ]
        metrics = RewardEngine.calculate_reward({"scenes": scenes}, EVIDENCE)
        self.assertGreaterEqual(metrics["evidence_alignment"], 0.5)
        self.assertTrue(metrics["is_grounded"])
        self.assertGreaterEqual(metrics["grounded_ctr"], 0.04)

    def test_mock_source_applies_confidence_penalty(self):
        mock_evidence = {
            **EVIDENCE,
            "source_type": "mock",
            "confidence": 0.45,
            "review_confidence": 0.45,
        }
        scenes = [
            scene(1, EVIDENCE["evidence_quotes"][0], dopamine=True),
            scene(2, EVIDENCE["evidence_quotes"][1], dopamine=False),
            scene(3, EVIDENCE["evidence_quotes"][2], dopamine=False),
        ]
        metrics = RewardEngine.calculate_reward({"scenes": scenes}, mock_evidence)
        self.assertEqual(metrics["confidence_penalty"], 0.15)
        self.assertFalse(metrics["is_grounded"])


if __name__ == "__main__":
    unittest.main()
