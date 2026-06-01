from pathlib import Path
import unittest

from video_generation import providers
from video_generation.providers import (
    get_video_provider_config,
    normalize_video_provider,
    supported_video_provider_names,
    video_job_export_formats,
    video_provider_catalog,
    video_provider_payload_metadata,
    video_provider_plan,
)


VIDEO_PACKET = {
    "packet_version": "video_generation_v1",
    "video": {
        "recommended_duration_seconds": 20,
        "aspect_ratio": "9:16",
    },
    "scenes": [
        {
            "scene_id": 1,
            "duration_seconds": 5,
            "visual_prompt": "Show the product in use.",
            "narration": "Make the product benefit concrete.",
            "overlay_text": "Quick demo",
            "evidence_quote": "Hard to clean after one smoothie",
        }
    ],
    "full_video_prompt": "Create a 9:16 product video.",
    "evidence_boundary": "Use only supplied evidence.",
    "export_formats": {
        "generic_video_prompt": "Generic prompt",
        "capcut_shot_list": "Scene 1 - 5s",
        "runway_style_prompt": "Runway visual prompt",
        "pika_style_prompt": "Pika motion prompt",
    },
}


class VideoProviderAdapterContractTest(unittest.TestCase):
    def test_catalog_includes_all_supported_providers(self):
        catalog = video_provider_catalog()
        names = {item["provider"] for item in catalog}

        self.assertEqual(
            names,
            {"manual_export", "generic", "capcut", "runway", "pika"},
        )
        for item in catalog:
            with self.subTest(provider=item["provider"]):
                self.assertIn("export_key", item)
                self.assertIn("recommended_use", item)
                self.assertFalse(item["external_api_ready"])

    def test_provider_aliases_normalize_consistently(self):
        self.assertEqual(normalize_video_provider("manual"), "manual_export")
        self.assertEqual(normalize_video_provider("manual_export"), "manual_export")
        self.assertEqual(normalize_video_provider("generic_video_prompt"), "generic")
        self.assertEqual(normalize_video_provider("capcut_shot_list"), "capcut")
        self.assertEqual(normalize_video_provider("runway_style_prompt"), "runway")
        self.assertEqual(normalize_video_provider("pika_style_prompt"), "pika")
        self.assertEqual(normalize_video_provider("unknown_provider"), "")

    def test_unknown_provider_config_is_empty(self):
        self.assertEqual(get_video_provider_config("unknown_provider"), {})
        self.assertEqual(video_provider_plan("unknown_provider"), {})

    def test_manual_export_plan_does_not_require_key(self):
        plan = video_provider_plan("manual_export")

        self.assertEqual(plan["provider"], "manual_export")
        self.assertEqual(plan["selected_export_key"], "generic_video_prompt")
        self.assertFalse(plan["external_api_ready"])
        self.assertFalse(plan["requires_api_key"])
        self.assertFalse(plan["supports_async_polling"])
        self.assertEqual(plan["create_mode"], "manual_export")

    def test_runway_and_pika_are_planned_only_with_env_keys(self):
        expected = {
            "runway": ("RUNWAY_API_KEY", "runway_style_prompt"),
            "pika": ("PIKA_API_KEY", "pika_style_prompt"),
        }
        for provider_name, (env_key, export_key) in expected.items():
            with self.subTest(provider=provider_name):
                plan = video_provider_plan(provider_name)
                self.assertFalse(plan["external_api_ready"])
                self.assertTrue(plan["requires_api_key"])
                self.assertTrue(plan["supports_async_polling"])
                self.assertEqual(plan["env_key_name"], env_key)
                self.assertEqual(plan["selected_export_key"], export_key)
                self.assertIn("queued", plan["supported_statuses"])
                self.assertIn("processing", plan["supported_statuses"])
                self.assertIn("disabled", " ".join(plan["warnings"]).lower())

    def test_all_providers_expose_export_key(self):
        for provider_name in supported_video_provider_names():
            with self.subTest(provider=provider_name):
                plan = video_provider_plan(provider_name)
                self.assertTrue(plan["export_key"])
                self.assertEqual(plan["selected_export_key"], plan["export_key"])

    def test_runway_payload_metadata_preserves_contract_fields(self):
        export_formats = video_job_export_formats(VIDEO_PACKET)
        payload = video_provider_payload_metadata("runway", export_formats, VIDEO_PACKET)

        self.assertEqual(payload["provider"], "runway")
        self.assertEqual(payload["selected_export_key"], "runway_style_prompt")
        self.assertEqual(payload["prompt"], "Runway visual prompt")
        self.assertEqual(payload["prompt_title"], "Runway-style visual prompt")
        self.assertIn("visual video generation", payload["recommended_use"])
        self.assertIn("Runway API integration is planned but disabled", " ".join(payload["provider_limitations"]))
        self.assertEqual(payload["evidence_boundary"], "Use only supplied evidence.")
        self.assertEqual(payload["create_mode"], "planned_external_api")
        self.assertIn("queued", payload["status_lifecycle"])
        self.assertEqual(payload["scene_count"], 1)
        self.assertEqual(payload["recommended_duration_seconds"], 20)
        self.assertEqual(payload["aspect_ratio"], "9:16")

    def test_provider_scaffold_contains_no_real_external_api_calls(self):
        source = Path(providers.__file__).read_text(encoding="utf-8")

        for token in ["requests.", "httpx.", "aiohttp", "urllib.request", "openai", "AsyncOpenAI"]:
            with self.subTest(token=token):
                self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()

