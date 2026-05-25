import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app


class TranslationEndpointTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_translate_output_returns_translated_text_without_debug_fields(self):
        with patch(
            "main.translate_visible_output",
            new=AsyncMock(return_value="# 中文简报\n\n保留 balsamic_vinegar。"),
        ) as translate:
            response = self.client.post(
                "/api/v1/translate-output",
                json={"text": "# Brief\n\nKeep balsamic_vinegar.", "target_language": "zh-CN"},
                headers={"X-Request-ID": "translation-smoke-1"},
            )

        self.assertEqual(response.status_code, 200)
        translate.assert_awaited_once_with("# Brief\n\nKeep balsamic_vinegar.", "zh-CN")
        payload = response.json()
        self.assertEqual(payload["translated_text"], "# 中文简报\n\n保留 balsamic_vinegar。")
        self.assertEqual(payload["target_language"], "zh-CN")
        self.assertEqual(payload["request_id"], "translation-smoke-1")
        self.assertEqual(response.headers["X-Request-ID"], "translation-smoke-1")
        self.assertNotIn("telemetry_summary", payload)
        self.assertNotIn("shadow_sources", payload)
        self.assertNotIn("memory_observability", payload)

    def test_translate_output_does_not_call_workflow_sources_or_memory(self):
        with patch(
            "main.translate_visible_output",
            new=AsyncMock(return_value="中文输出"),
        ), patch("main.copilot_engine.ainvoke", new=AsyncMock()) as workflow, patch(
            "main.source_probe_registry.fetch",
        ) as source_fetch, patch("main.memory_engine.save_memory") as save_memory, patch(
            "main.memory_engine.observability_snapshot"
        ) as memory_snapshot:
            response = self.client.post(
                "/api/v1/translate-output",
                json={"text": "Visible product output only."},
            )

        self.assertEqual(response.status_code, 200)
        workflow.assert_not_awaited()
        source_fetch.assert_not_called()
        save_memory.assert_not_called()
        memory_snapshot.assert_not_called()


if __name__ == "__main__":
    unittest.main()
