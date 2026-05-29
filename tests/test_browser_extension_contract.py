import json
import unittest
from pathlib import Path


class BrowserExtensionContractTest(unittest.TestCase):
    def setUp(self):
        self.root = Path("browser_extension")

    def test_extension_files_exist(self):
        for name in ["manifest.json", "popup.html", "popup.js", "content.js", "styles.css"]:
            self.assertTrue((self.root / name).exists(), name)

    def test_manifest_contract(self):
        manifest = json.loads((self.root / "manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["manifest_version"], 3)
        self.assertIn("activeTab", manifest["permissions"])
        self.assertIn("scripting", manifest["permissions"])
        self.assertIn("storage", manifest["permissions"])
        self.assertIn("https://www.amazon.com/*", manifest["host_permissions"])
        self.assertEqual(manifest["action"]["default_popup"], "popup.html")


    def test_manifest_allows_tiktok_pages(self):
        manifest = json.loads((self.root / "manifest.json").read_text(encoding="utf-8"))

        self.assertIn("https://*.tiktok.com/*", manifest["host_permissions"])

    def test_content_script_extracts_product_workspace_shape(self):
        source = (self.root / "content.js").read_text(encoding="utf-8")

        for marker in [
            "extractCurrentPage",
            "platform",
            "url",
            "asin",
            "title",
            "price",
            "rating",
            "review_count",
            "bullet_points",
            "reviews",
            "amazon_visible_review",
        ]:
            self.assertIn(marker, source)


    def test_content_script_has_platform_adapters(self):
        source = (self.root / "content.js").read_text(encoding="utf-8")

        for marker in [
            "detectPlatform",
            "extractAmazonPage",
            "extractTikTokPage",
            "extractGenericPage",
            "platform=tiktok",
            "platform=amazon",
            "tiktok_visible_comment",
            "generic_visible_text",
            "metadata",
            "creator",
            "hashtags",
        ]:
            self.assertIn(marker, source)

    def test_popup_calls_workspace_analysis_endpoint(self):
        source = (self.root / "popup.js").read_text(encoding="utf-8")

        for marker in [
            "/api/v1/analyze-review-workspace",
            "chrome.storage.local",
            "chrome.scripting.executeScript",
            "workspaceProducts",
            "chrome_extension",
            "saveCurrentProduct",
            "analyzeWorkspace",
        ]:
            self.assertIn(marker, source)


if __name__ == "__main__":
    unittest.main()
