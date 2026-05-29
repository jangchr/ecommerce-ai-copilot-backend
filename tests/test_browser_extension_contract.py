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



    def test_manifest_allows_tab_collection(self):
        manifest = json.loads((self.root / "manifest.json").read_text(encoding="utf-8"))

        self.assertIn("tabs", manifest["permissions"])

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



    def test_content_script_has_amazon_diagnostics(self):
        source = (self.root / "content.js").read_text(encoding="utf-8")

        for marker in [
            "detectAmazonPageType",
            "amazon_sign_in",
            "sign_in_required",
            "review_visibility_status",
            "no_visible_reviews_on_product_page",
            "no_visible_reviews_on_reviews_page",
            "visible_review_count",
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



    def test_popup_renders_productized_workspace_analysis(self):
        html = (self.root / "popup.html").read_text(encoding="utf-8")
        js = (self.root / "popup.js").read_text(encoding="utf-8")
        css = (self.root / "styles.css").read_text(encoding="utf-8")

        for marker in [
            "analysisSummary",
            "Raw response",
        ]:
            self.assertIn(marker, html)

        for marker in [
            "renderWorkspaceAnalysis",
            "Top pain points",
            "Buyer objections",
            "Creative angles",
            "Hooks",
            "renderWorkspaceAnalysis(body)",
        ]:
            self.assertIn(marker, js)

        for marker in [
            ".metric-grid",
            ".insight-section",
            ".metric-card",
            ".raw-details",
        ]:
            self.assertIn(marker, css)


    def test_popup_supports_collect_open_tabs(self):
        html = (self.root / "popup.html").read_text(encoding="utf-8")
        js = (self.root / "popup.js").read_text(encoding="utf-8")

        for marker in [
            "collectTabsBtn",
            "Collect open tabs",
        ]:
            self.assertIn(marker, html)

        for marker in [
            "collectOpenTabs",
            "chrome.tabs.query",
            "isCollectableTabUrl",
            "extractProductFromTab",
            "mergeProductsByUrl",
            "bind(\"collectTabsBtn\", collectOpenTabs)",
        ]:
            self.assertIn(marker, js)


    def test_popup_renders_collected_product_list(self):
        html = (self.root / "popup.html").read_text(encoding="utf-8")
        js = (self.root / "popup.js").read_text(encoding="utf-8")
        css = (self.root / "styles.css").read_text(encoding="utf-8")

        for marker in [
            "collectedProducts",
            "collected-products",
        ]:
            self.assertIn(marker, html)

        for marker in [
            "renderSavedProducts",
            "shortProductTitle",
            "productSourceLabel",
            "Collected products",
            "renderSavedProducts(products)",
        ]:
            self.assertIn(marker, js)

        for marker in [
            ".collected-products",
            ".collected-header",
            ".collected-title",
            ".collected-meta",
        ]:
            self.assertIn(marker, css)


    def test_popup_supports_copy_actions(self):
        manifest = json.loads((self.root / "manifest.json").read_text(encoding="utf-8"))
        html = (self.root / "popup.html").read_text(encoding="utf-8")
        js = (self.root / "popup.js").read_text(encoding="utf-8")
        css = (self.root / "styles.css").read_text(encoding="utf-8")

        self.assertIn("clipboardWrite", manifest["permissions"])

        for marker in [
            "copyInsightsBtn",
            "copyWorkspaceJsonBtn",
            "Copy insights",
            "Copy workspace JSON",
        ]:
            self.assertIn(marker, html)

        for marker in [
            "lastWorkspaceAnalysis",
            "copyInsights",
            "copyWorkspaceJson",
            "buildWorkspacePayload",
            "navigator.clipboard.writeText",
            "bind(\"copyInsightsBtn\", copyInsights)",
            "bind(\"copyWorkspaceJsonBtn\", copyWorkspaceJson)",
        ]:
            self.assertIn(marker, js)

        for marker in [
            ".analysis-actions",
            "button.compact",
        ]:
            self.assertIn(marker, css)


    def test_popup_supports_open_in_web_workspace(self):
        html = (self.root / "popup.html").read_text(encoding="utf-8")
        js = (self.root / "popup.js").read_text(encoding="utf-8")
        css = (self.root / "styles.css").read_text(encoding="utf-8")

        for marker in [
            "openWorkspaceBtn",
            "Open in Web Workspace",
        ]:
            self.assertIn(marker, html)

        for marker in [
            "openInWebWorkspace",
            "waitForTabLoad",
            "crossgrowth_extension_workspace",
            "chrome.tabs.create",
            "bind(\"openWorkspaceBtn\", openInWebWorkspace)",
        ]:
            self.assertIn(marker, js)

        self.assertIn("button.compact.wide", css)


    def test_popup_surfaces_capture_diagnostics(self):
        source = (self.root / "popup.js").read_text(encoding="utf-8")

        for marker in [
            "captureDiagnosticMessage",
            "Amazon sign-in required",
            "No visible reviews found",
            "capture warning(s)",
        ]:
            self.assertIn(marker, source)

if __name__ == "__main__":
    unittest.main()
