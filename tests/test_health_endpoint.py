import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app


class HealthEndpointTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_healthz_returns_lightweight_service_status_without_runtime_calls(self):
        with patch(
            "main.copilot_engine.ainvoke",
            new=AsyncMock(side_effect=AssertionError("Health endpoint must not run workflow.")),
        ) as workflow, patch(
            "main.source_probe_registry.fetch",
            side_effect=AssertionError("Health endpoint must not call source adapters."),
        ) as source_fetch:
            response = self.client.get("/healthz")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "ok",
                "service": "grounded-ecommerce-creative-agent",
                "stable_baseline": "l9_9_stable",
            },
        )
        workflow.assert_not_awaited()
        source_fetch.assert_not_called()

    def test_root_serves_static_index(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("content-type", ""))
        self.assertIn("Product Mode is stable", response.text)
        self.assertIn("Copy Hook", response.text)

    def test_static_index_path_is_available(self):
        response = self.client.get("/static/index.html")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("content-type", ""))
        self.assertIn("Product Mode is stable", response.text)


if __name__ == "__main__":
    unittest.main()
