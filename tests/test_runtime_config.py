import importlib
import os
import unittest
from unittest.mock import patch

import core.runtime_config as runtime_config


class RuntimeConfigTest(unittest.TestCase):
    def test_default_available_tools_do_not_include_real_apis(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("ALLOW_REAL_SOURCE_ADAPTERS", None)
            config = importlib.reload(runtime_config)

        self.assertFalse(config.ALLOW_REAL_SOURCE_ADAPTERS)
        self.assertEqual(
            config.enabled_source_tools(),
            ["local_review_dataset", "tiktok_trend_mock"],
        )
        self.assertNotIn("amazon_review_api", config.enabled_source_tools())
        self.assertNotIn("tiktok_trend_api", config.enabled_source_tools())
        self.assertNotIn("reddit_review_api", config.enabled_source_tools())

    def test_real_source_permission_exposes_only_explicit_real_tools(self):
        with patch.dict(os.environ, {"ALLOW_REAL_SOURCE_ADAPTERS": "true"}):
            config = importlib.reload(runtime_config)

        self.assertTrue(config.ALLOW_REAL_SOURCE_ADAPTERS)
        self.assertEqual(
            config.enabled_source_tools(),
            [
                "local_review_dataset",
                "tiktok_trend_mock",
                "amazon_review_api",
                "tiktok_trend_api",
                "reddit_review_api",
            ],
        )
        importlib.reload(runtime_config)


if __name__ == "__main__":
    unittest.main()
