import json
import unittest
from io import StringIO
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from core.logging_utils import emit_event
from main import app


class RequestIdLoggingTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_healthz_generates_request_id_without_running_workflow(self):
        with patch(
            "main.copilot_engine.ainvoke",
            new=AsyncMock(side_effect=AssertionError("Health endpoint must not run workflow.")),
        ) as workflow:
            response = self.client.get("/healthz")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers["X-Request-ID"])
        workflow.assert_not_awaited()

    def test_incoming_request_id_is_returned_unchanged(self):
        response = self.client.get(
            "/healthz",
            headers={"X-Request-ID": "deploy-smoke-123"},
        )

        self.assertEqual(response.headers["X-Request-ID"], "deploy-smoke-123")

    def test_structured_event_only_emits_safe_fields(self):
        output = StringIO()
        with patch("sys.stdout", output):
            emit_event(
                "healthz_request",
                "request-1",
                endpoint="/healthz",
                status="ok",
                latency_ms=1.5,
                evidence_quote="must not appear",
                api_key="must not appear",
                prompt="must not appear",
                raw_state={"secret": "must not appear"},
            )

        payload = json.loads(output.getvalue())
        self.assertEqual(payload["event"], "healthz_request")
        self.assertEqual(payload["request_id"], "request-1")
        self.assertNotIn("evidence_quote", payload)
        self.assertNotIn("api_key", payload)
        self.assertNotIn("prompt", payload)
        self.assertNotIn("raw_state", payload)


if __name__ == "__main__":
    unittest.main()
