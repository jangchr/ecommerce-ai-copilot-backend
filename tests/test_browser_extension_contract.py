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




    def test_manifest_allows_amazon_jp_pages(self):
        manifest = json.loads((self.root / "manifest.json").read_text(encoding="utf-8"))

        self.assertIn("https://www.amazon.co.jp/*", manifest["host_permissions"])
        self.assertIn("https://*.amazon.co.jp/*", manifest["host_permissions"])

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



    def test_popup_cleans_collected_review_tabs_before_merge(self):
        source = (self.root / "popup.js").read_text(encoding="utf-8")
        content = (self.root / "content.js").read_text(encoding="utf-8")

        for marker in [
            "cleanCollectedProductTitle",
            "cleanCollectedReviewText",
            "normalizeCollectedProductForMerge",
            "Customer reviews",
            "\\u4e70\\u5bb6\\u8bc4\\u8bba",
            "Thank you for your feedback",
            "Sorry, there was an error",
            "One person found this",
        ]:
            self.assertIn(marker, source + content)

    def test_popup_merges_open_tabs_by_product_identity(self):
        source = (self.root / "popup.js").read_text(encoding="utf-8")

        for marker in [
            "productIdentityKey",
            "reviewIdentityKey",
            "mergeReviewLists",
            "mergeProductsByUrlWithStats",
            "merged_visible_review_pages",
            "collectedTabsMerged",
            "duplicateReviews",
            "totalReviews",
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




    def test_popup_supports_background_collector_page_limit_control(self):
        html = (self.root / "popup.html").read_text(encoding="utf-8")
        js = (self.root / "popup.js").read_text(encoding="utf-8")

        for marker in [
            "autoCollectMaxPages",
            "autoCollectMaxPagesLabel",
            "<option value=\"3\">3</option>",
            "<option value=\"5\">5</option>",
            "<option value=\"10\">10</option>",
        ]:
            self.assertIn(marker, html + js)

        for marker in [
            "readAutoCollectMaxPages",
            "const maxPages = readAutoCollectMaxPages()",
            "autoCollectMaxPages: result.autoCollectMaxPages",
            "chrome.storage.local.set({ autoCollectMaxPages: readAutoCollectMaxPages() })",
        ]:
            self.assertIn(marker, js)


    def test_content_script_exposes_amazon_pagination_candidates(self):
        source = (self.root / "content.js").read_text(encoding="utf-8")
        popup = (self.root / "popup.js").read_text(encoding="utf-8")

        for marker in [
            "extractAmazonPaginationCandidates",
            "amazonCurrentReviewAsin",
            "amazonCandidateReviewAsin",
            "isAmazonSafeReviewPaginationCandidate",
            "amazonCandidateNextSignal",
            "amazonCandidateLoadMoreSignal",
            "cm_cr_arp_d_paging_btm",
            "show more reviews",
            "filterByStar",
            "formatType",
            "amazonPaginationNodeText",
            "pagination_candidates",
            "pagination_candidate_count",
            "slice(0, 24)",
            "aria_label",
            "class_name",
            "nextpagetoken",
            "cm_cr_getr",
        ]:
            self.assertIn(marker, source + popup)

    def test_popup_supports_background_review_page_collector(self):
        html = (self.root / "popup.html").read_text(encoding="utf-8")
        js = (self.root / "popup.js").read_text(encoding="utf-8")
        content = (self.root / "content.js").read_text(encoding="utf-8")

        for marker in [
            "autoCollectMoreBtn",
            "autoCollectMoreReviews",
        ]:
            self.assertIn(marker, html + js)

        for marker in [
            "collectCurrentProductMoreReviews",
            "amazonAsinFromProduct",
            "amazonReviewPageUrlFor",
            "isAmazonReviewPageUrl",
            "amazonReviewCollectorStartUrl",
            "collector_pages",
            "visitedCollectorUrls",
            "sameCollectorUrl",
            "chooseNextCollectorUrl",
            "shouldClickAmazonLoadMore",
            "clickAmazonReviewLoadMoreInTab",
            "load_more_click",
            "skipNavigationSignal",
            "#skippedLink",
            "nav-assist-skip-to-main-content",
            "labelLoadMoreSignal",
            "skipNavigationOnce",
            "dom_click",
            "isAmazonLoadMoreCollectorUrl",
            "load_more_terminal",
            "selected_next_url",
            "selected_next_source",
            "ignored_next_review_page_url",
            "repeatedCollectorUrl",
            "seenReviewPageSignatures",
            "reviewPageSignatureFromProduct",
            "repeatedReviewPageContent",
            "repeated_page_content",
            "nextSequentialAmazonReviewUrl",
            "amazonReviewPageNumberFromUrl",
            "fallback_next_url",
            "page_number",
            "backgroundCollectorDone",
            "chrome.tabs.create",
            "chrome.tabs.update",
            "chrome.tabs.remove",
            "bind(\"autoCollectMoreBtn\", collectCurrentProductMoreReviews)",
        ]:
            self.assertIn(marker, js)

        for marker in [
            "extractAmazonNextReviewPageUrl",
            "next_review_page_url",
            "pageNumber",
            "li.a-last",
        ]:
            self.assertIn(marker, content)

    def test_popup_surfaces_sample_expansion_guidance(self):
        html = (self.root / "popup.html").read_text(encoding="utf-8")
        js = (self.root / "popup.js").read_text(encoding="utf-8")

        for marker in [
            "sampleGuidanceCard",
            "sampleGuidanceList",
            "sampleGuidanceIntro",
            "sampleGuidanceStrength",
            "sampleGuidanceCta",
            "sampleGuidanceCopyBtn",
            "openLowStarReviewTabBtn",
            "openVerifiedReviewTabBtn",
            "openVariantReviewTabsBtn",
            "copyTargetedReviewLinksBtn",
        ]:
            self.assertIn(marker, html)

        for marker in [
            "SAMPLE_GUIDANCE_REVIEW_THRESHOLD",
            "sampleGuidancePlan",
            "totalSavedReviewCount",
            "renderSampleGuidance",
            "sampleGuidanceStrengthVeryLow",
            "sampleGuidanceStrengthLow",
            "sampleGuidanceStrengthMedium",
            "renderSampleGuidance(products)",
            "sampleGuidanceTitle",
            "sampleGuidanceLowStar",
            "sampleGuidanceVerifiedPurchase",
            "sampleGuidanceVariants",
            "sampleGuidanceCompetitors",
            "sampleGuidanceLoggedIn",
            "sampleGuidanceCta",
            "copySampleGuidanceSteps",
            "openTargetedReviewTab",
            "copyTargetedReviewLinks",\n            "openVariantReviewTabs",\n            "variantReviewLinksForProduct",\n            "amazonAsinFromUrl",\n            "cleanVariantReviewLabel",\n            "targetedReviewLinkLabel",\n            "targetedVariantReviews",\n            "openedVariantReviewTabs",\n            "noVariantReviewLinks",
            "targetedAmazonReviewLinksForProduct",
            "amazonReviewUrlWithParams",
            "latestSavedAmazonProduct",
            "filterByStar",
            "critical",
            "avp_only_reviews",
            "sortBy",
            "formatType",
            "openedTargetedReviewTab",
            "copiedTargetedReviewLinks",
            "sampleGuidanceStepsTitle",
            "copiedSampleGuidanceSteps",
            "actionInProgress",
            "setButtonBusy",
            "aria-busy",
            "is-busy",
            "restoreHandledByAction",
            "async function copySampleGuidanceSteps",
            "bind(\"sampleGuidanceCopyBtn\", copySampleGuidanceSteps)",
            "Collect open tabs",
        ]:
            self.assertIn(marker, js)

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
            "popupLanguageEnglish",
            "popupLanguageChinese",
            "data-i18n=\"title\"",
            "data-i18n=\"visibleSampleTitle\"",
            "backendUrlLabel",
            "visibleSampleBody",
            "saveCurrentProduct",
        ]:
            self.assertIn(marker, html)

        for marker in [
            "openInWebWorkspace",
            "POPUP_COPY",
            "POPUP_THEME_LABELS",
            "popupThemeLabel",
            "\\u4ef7\\u683c / \\u4ef7\\u503c\\u987e\\u8651",
            "\\u5473\\u9053 / \\u98ce\\u5473\\u987e\\u8651",
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


    def test_content_script_has_amazon_review_fallback_selectors(self):
        source = (self.root / "content.js").read_text(encoding="utf-8")

        for marker in [
            "amazonReviewCandidateNodes",
            "[id^='customer_review-']",
            "#cm-cr-dp-review-list",
            "#reviewsMedley",
            "review-text-content",
            "extractAmazonReviewBody",
            "extractAmazonReviewTitle",
            "extractAmazonHelpfulCount",
        ]:
            self.assertIn(marker, source)


    def test_content_script_filters_amazon_review_quality(self):
        source = (self.root / "content.js").read_text(encoding="utf-8")

        for marker in [
            "cleanAmazonReviewText",
            "isAmazonNoiseReviewText",
            "isAmazonAggregateReviewText",
            "isLikelyTitleOnlyReview",
            "ratingBucketFromText",
            "amazonRatingDistribution",
            "amazonVisibleSampleWarning",
            "source_scope",
            "visible_page_sample",
            "sample_warning",
            "rating_distribution",
            "raw_review_candidate_count",
        ]:
            self.assertIn(marker, source)


    def test_popup_surfaces_visible_sample_warning(self):
        source = (self.root / "popup.js").read_text(encoding="utf-8")

        self.assertIn("Visible Amazon review sample only; not the full review set.", source)


    def test_content_script_filters_low_information_amazon_reviews(self):
        source = (self.root / "content.js").read_text(encoding="utf-8")

        for marker in [
            "isLowInformationAmazonReview",
            "isContainedDuplicateAmazonReview",
            "keptReviews",
            "amazon customer",
            "currentIsWeaker",
            "currentLooksAggregate",
        ]:
            self.assertIn(marker, source)


    def test_popup_explains_visible_sample_boundary(self):
        html = (self.root / "popup.html").read_text(encoding="utf-8")
        css = (self.root / "styles.css").read_text(encoding="utf-8")

        for marker in [
            "visibleSampleNotice",
            "Visible-page sample",
            "does not bypass login",
            "CAPTCHA",
            "creative signals",
            "not full review statistics",
        ]:
            self.assertIn(marker, html)

        for marker in [
            ".notice-card",
            ".notice-title",
        ]:
            self.assertIn(marker, css)

if __name__ == "__main__":
    unittest.main()
