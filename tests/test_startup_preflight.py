import unittest

from scripts.startup_preflight import PROJECT_ROOT, collect_startup_preflight


class StartupPreflightTest(unittest.TestCase):
    def test_current_repository_passes_lightweight_startup_preflight(self):
        result = collect_startup_preflight(
            PROJECT_ROOT,
            environment={
                "ALLOW_REAL_SOURCE_ADAPTERS": "false",
                "MEMORY_MAX_RECORD_COUNT": "500",
            },
        )

        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["required_failures"], [])
        self.assertIn("checks", result)
        self.assertGreaterEqual(result["checks"]["review_datasets"]["count"], 10)
        self.assertTrue(result["checks"]["stable_baseline"]["exists"])
        self.assertFalse(result["checks"]["runtime_config"]["openai_api_key_present"])

    def test_invalid_memory_limit_is_a_required_failure(self):
        result = collect_startup_preflight(
            PROJECT_ROOT,
            environment={
                "ALLOW_REAL_SOURCE_ADAPTERS": "false",
                "MEMORY_MAX_RECORD_COUNT": "invalid",
            },
        )

        self.assertEqual(result["status"], "fail")
        self.assertIn(
            "MEMORY_MAX_RECORD_COUNT must be a positive integer",
            result["required_failures"],
        )


if __name__ == "__main__":
    unittest.main()
