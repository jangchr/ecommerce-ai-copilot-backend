from pathlib import Path
import re
import unittest


FRONTEND_PATH = Path(__file__).resolve().parents[1] / "static" / "index.html"


class FrontendProbeBoundaryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = FRONTEND_PATH.read_text(encoding="utf-8")

    def test_product_frontend_does_not_read_embedded_debug_state(self):
        self.assertNotIn("data.debug", self.source)

    def test_public_demo_uses_user_task_flow_shell(self):
        for marker in [
            "pathSelectorPanel",
            "pathAmazonProductCard",
            "pathProductIdeaCard",
            "pathCustomerFeedbackCard",
            "pathSampleProductCard",
            "activeWorkspacePanel",
            "inlineResultPanel",
            "inlineResultEmptyState",
            "inlineResultContent",
            "amazonProductWorkspace",
            "productIdeaWorkspace",
            "customerFeedbackWorkspace",
            "sampleProductWorkspace",
            "I have a product idea",
            "I have customer feedback",
            "Show me a sample",
            "Only the active workspace is shown",
            "After you generate, the Hook, storyboard, and copy actions will appear here in this same workspace.",
            "function setActiveWorkspace(name, options = {})",
            "function mountUserTaskFlow()",
            "function showInlineResultPanel()",
            "showInlineResultPanel();",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.source)

        self.assertIn("amazonProductWorkspace.appendChild(amazonIntakePanel);", self.source)
        self.assertIn("productIdeaWorkspace.appendChild(productDescriptionMode);", self.source)
        self.assertIn("customerFeedbackWorkspace.appendChild(pastedReviewsMode);", self.source)
        self.assertIn("sampleProductWorkspace.appendChild(stableProductWorkspace);", self.source)
        self.assertIn("sampleProductWorkspace.appendChild(exampleGallery);", self.source)
        self.assertIn("inlineResultContent.appendChild(section);", self.source)
        self.assertIn("setActiveWorkspace('amazonProduct');", self.source)

    def test_user_task_flow_shell_does_not_trigger_debug_or_generation(self):
        selector_match = re.search(
            r"<section class=\"path-selector-panel\" id=\"pathSelectorPanel\">(?P<body>.*?)<section class=\"active-workspace-panel\"",
            self.source,
            re.S,
        )
        self.assertIsNotNone(selector_match)
        selector_body = selector_match.group("body")

        inline_match = re.search(
            r"<section class=\"inline-result-panel\" id=\"inlineResultPanel\">(?P<body>.*?)</section>",
            self.source,
            re.S,
        )
        self.assertIsNotNone(inline_match)
        inline_body = inline_match.group("body")

        for body in [selector_body, inline_body]:
            with self.subTest(flow_boundary=body[:40]):
                self.assertNotIn("debug-copilot", body)
                self.assertNotIn("debug-source-probe", body)
                self.assertNotIn("telemetry_summary", body)
                self.assertNotIn("shadow_sources", body)
                self.assertNotIn("memory_observability", body)
                self.assertNotIn("postCopilot(", body)



    def test_extension_workspace_panel_chrome_refreshes_after_payload_language(self):
        for marker in [
            "function refreshExtensionWorkspacePanelChrome(source = extensionWorkspacePageLanguageSource())",
            "function extensionWorkspacePageLanguageSource()",
            "extensionWorkspacePanelEyebrow",
            "extensionWorkspacePanelTitle",
            "extensionWorkspaceBoundaryNote",
            "extensionWorkspaceAnalyze",
            "extensionWorkspaceSendToReviews",
            "extensionWorkspaceBridgeHint",
            "extensionWorkspaceCopy",
            "window.refreshExtensionWorkspacePanelChrome = refreshExtensionWorkspacePanelChrome;",
            "window.refreshExtensionWorkspacePanelChrome();",
            "refreshExtensionWorkspacePanelChrome(payload);",
            "tExtensionWorkspace(\"boundaryNote\")",
            "tExtensionWorkspace(\"waitingPayload\")",
        ]:
            self.assertIn(marker, self.source)

        refresh_start = self.source.find("function refreshExtensionWorkspacePanelChrome")
        refresh_end = self.source.find("function createExtensionWorkspacePanel", refresh_start)
        self.assertNotEqual(refresh_start, -1)
        self.assertNotEqual(refresh_end, -1)
        refresh_body = self.source[refresh_start:refresh_end]
        self.assertIn("extensionWorkspacePageLanguageSource()", refresh_body)
        self.assertIn("Object.assign({}, payload, labelSource)", refresh_body)
        self.assertIn("updateExtensionWorkspaceActionState(payload)", refresh_body)


    def test_extension_workspace_auto_analysis_status_states_are_visible(self):
        self.assertIn("function extensionWorkspaceStatusMessage(kind, source = null)", self.source)
        self.assertIn("function extensionWorkspaceStatusHTML(kind, source = null, detail =", self.source)
        self.assertIn("extensionWorkspaceAutoAnalyzeStatus", self.source)
        self.assertIn("data-extension-auto-analysis-status", self.source)
        self.assertIn("Auto-analyzing workspace...", self.source)
        self.assertIn("Analysis complete", self.source)
        self.assertIn("Analysis failed. Please retry", self.source)
        self.assertIn("\\u6b63\\u5728\\u81ea\\u52a8\\u5206\\u6790\\u5de5\\u4f5c\\u533a...", self.source)
        self.assertIn("\\u5206\\u6790\\u5b8c\\u6210", self.source)
        self.assertIn("\\u5206\\u6790\\u5931\\u8d25\\uff0c\\u8bf7\\u91cd\\u8bd5", self.source)
        self.assertIn('extensionWorkspaceStatusHTML("analyzing", payload)', self.source)
        self.assertIn('extensionWorkspaceStatusHTML("complete", body)', self.source)
        self.assertIn('"failed",\n          payload,', self.source)
        status_start = self.source.find("function extensionWorkspaceStatusHTML")
        status_end = self.source.find("function extensionWorkspaceAutoAnalyzeKey", status_start)
        self.assertNotEqual(status_start, -1)
        self.assertNotEqual(status_end, -1)
        self.assertNotIn("body.creative_angles", self.source[status_start:status_end])


    def test_product_mode_guidance_and_copy_controls_are_present(self):
        self.assertIn(
            "Generate TikTok creative strategy from grounded ecommerce review insights.",
            self.source,
        )
        self.assertIn(
            "This public demo uses 10 stable local grounded product categories. Start with balsamic_vinegar.",
            self.source,
        )
        self.assertIn("Try balsamic_vinegar", self.source)
        self.assertIn("function setDemoSlug(slug)", self.source)
        self.assertIn("Language", self.source)
        self.assertIn("English", self.source)
        self.assertIn("中文", self.source)
        self.assertIn("let outputLanguage = 'en';", self.source)
        self.assertIn("function setLanguageMode(language)", self.source)
        self.assertIn("function currentOutputLanguage()", self.source)
        self.assertIn("output_language", self.source)
        self.assertIn("产品描述模式", self.source)
        self.assertIn("根据产品描述生成", self.source)
        self.assertIn("好的输入应该包含", self.source)
        self.assertIn("加入试用名单", self.source)
        self.assertIn("Example Gallery", self.source)
        self.assertIn("Static examples, no API call", self.source)
        self.assertIn("Try This Product", self.source)
        self.assertIn("function setExampleSlug(slug)", self.source)
        for slug in [
            "balsamic_vinegar",
            "printer",
            "women_bras",
            "girls_overalls",
            "protein_powder",
            "phone_case",
            "desk_lamp",
            "baby_stroller",
            "pet_hair_vacuum",
            "skincare_serum",
        ]:
            self.assertIn(slug, self.source)
        self.assertIn("Amazon.com links are now supported in the Amazon Product Link workflow", self.source)
        self.assertIn("The old sample slug input still expects stable local demo slugs", self.source)
        self.assertIn('id="pathAmazonProductCard"', self.source)
        self.assertIn('id="amazonProductWorkspace"', self.source)
        self.assertIn('id="amazonIntakePanel"', self.source)
        self.assertIn("Amazon links are now supported in the Amazon Product Link workflow", self.source)
        self.assertIn("Product Result", self.source)
        self.assertIn("Copy / Download / Translation Actions", self.source)
        self.assertIn("Feedback", self.source)
        self.assertIn("Product Description Mode", self.source)
        self.assertIn("L17.2-A Chinese landing and onboarding copy polish", self.source)
        self.assertIn("chineseOnboardingPanel", self.source)
        self.assertIn("workflowPathTitle: '选择你的生成方式'", self.source)
        self.assertIn("inlineResultPanelTitle: '你的生成结果'", self.source)
        self.assertIn("inlineResultEmptyState: '点击生成后，Hook、分镜脚本和复制按钮会直接出现在这里，不用滑到页面底部找结果。'", self.source)
        self.assertIn("recentEmptyState: '还没有最近生成记录。'", self.source)
        self.assertIn("/* L18.1-D dedupe bottom feedback/waitlist UI */", self.source)
        self.assertIn(".feedback-panel,", self.source)
        self.assertIn("#waitlistPanel", self.source)
        self.assertIn("recentView: '查看'", self.source)
        self.assertIn("recentCopyMarkdown: '复制 Markdown'", self.source)
        self.assertIn("recentDelete: '删除'", self.source)
        self.assertIn("${escapeHTML(t('recentView'))}", self.source)
        self.assertIn("${escapeHTML(t('recentCopyMarkdown'))}", self.source)
        self.assertIn("${escapeHTML(t('recentDelete'))}", self.source)
        self.assertIn("clearRecentGenerations: '清空最近生成记录'", self.source)
        self.assertIn("feedbackBody: '告诉我们这个创意 brief 是否有用", self.source)
        self.assertIn("waitlistTitle: '加入试用名单'", self.source)
        self.assertIn("waitlistBody: '想把它用在你自己的产品上？", self.source)
        self.assertIn('data-i18n="inlineResultPanelTitle"', self.source)
        self.assertIn('data-i18n="inlineResultEmptyState"', self.source)
        self.assertIn('data-i18n="recentEmptyState"', self.source)
        self.assertIn('data-i18n="clearRecentGenerations"', self.source)
        self.assertIn('data-i18n="waitlistTitle"', self.source)
        self.assertIn('data-i18n="waitlistBody"', self.source)
        self.assertIn("pathProductIdeaTitle: '我有产品想法'", self.source)
        self.assertIn("pathCustomerFeedbackTitle: '我有用户评论/反馈'", self.source)
        self.assertIn("pathSampleProductTitle: '我先看示例'", self.source)
        self.assertIn("userTaskFlowBadge: '用户任务流程'", self.source)
        self.assertIn("data-i18n-placeholder", self.source)
        self.assertIn("descriptionProductDescriptionPlaceholder: '用一句话描述产品。", self.source)
        self.assertIn("descriptionPainPointsPlaceholder: '写用户遇到的问题。", self.source)
        self.assertIn("reviewsPastedReviewsPlaceholder: '- 我讨厌每天早上清洗大搅拌机。", self.source)
        self.assertIn("missingName: '请输入产品名称。'", self.source)
        self.assertIn("inputTooShort: '生成前请补充更多具体信息。'", self.source)
        self.assertIn("L17.3-A Chinese example product library polish", self.source)
        self.assertIn("sampleProductLibraryGuide", self.source)
        self.assertIn("L17.4-A Chinese first-run guide polish", self.source)
        self.assertIn("firstRunGuidePanel", self.source)
        self.assertIn("descriptionFirstRunGuide", self.source)
        self.assertIn("reviewsFirstRunGuide", self.source)
        self.assertIn("第一次来？只做这三步", self.source)
        self.assertIn("先跑一个示例", self.source)
        self.assertIn("产品是什么、谁会想买、它解决什么麻烦", self.source)
        self.assertIn("不知道怎么写也没关系", self.source)
        self.assertIn("如果你还没有真实评论", self.source)
        self.assertIn("示例产品库", self.source)
        self.assertIn("这些只是用来试流程的示例产品", self.source)
        self.assertIn("不需要把它理解成“数据集”", self.source)
        self.assertIn("用示例产品生成", self.source)
        self.assertIn("输入来源：产品描述", self.source)
        self.assertIn("输入来源：粘贴的用户反馈", self.source)
        self.assertIn("Choose a sample product, e.g. desk_lamp", self.source)
        self.assertIn("用 10 分钟，把一个产品想法变成 TikTok 视频脚本", self.source)
        self.assertIn("不需要电商经验", self.source)
        self.assertIn("示例产品库", self.source)
        self.assertIn("不知道从哪里开始", self.source)
        self.assertIn("我有产品想法", self.source)
        self.assertIn("我有用户评论/反馈", self.source)
        self.assertIn("L16.1-A result summary and hook highlight polish", self.source)
        self.assertIn("resultSummaryCard", self.source)
        self.assertIn("L16.3-A evidence source label polish", self.source)
        self.assertIn("evidenceSourceCard", self.source)
        self.assertIn("Evidence Source", self.source)
        self.assertIn("证据来源", self.source)
        self.assertIn("Source type", self.source)
        self.assertIn("来源类型", self.source)
        self.assertIn("function renderEvidenceSourceCard(evidence)", self.source)
        self.assertIn("${renderEvidenceSourceCard(evidence)}", self.source)
        self.assertIn("resultHookHighlightCard", self.source)
        self.assertIn("L16.2-A storyboard scene readability polish", self.source)
        self.assertIn("storyboard-scene-list", self.source)
        self.assertIn("storyboard-scene-card", self.source)
        self.assertIn("storyboard-scene-number", self.source)
        self.assertIn("storyboard-scene-evidence", self.source)
        self.assertIn("Scene goal", self.source)
        self.assertIn("场景目标", self.source)
        self.assertIn("Linked pain point", self.source)
        self.assertIn("关联痛点", self.source)
        self.assertIn("Creative Summary", self.source)
        self.assertIn("Hook highlight", self.source)
        self.assertIn("创意摘要", self.source)
        self.assertIn("Hook 重点", self.source)
        self.assertIn("function renderResultSummaryCard", self.source)
        self.assertIn("function renderHookHighlightCard", self.source)
        self.assertIn("quickStartPanel", self.source)
        self.assertIn("L15.3-A mobile readability polish", self.source)
        self.assertIn("@media (max-width: 720px)", self.source)
        self.assertIn("#quickStartPanel", self.source)
        self.assertIn("#feedbackWaitlistCtaPanel", self.source)
        self.assertIn("#reviewPasteGuide", self.source)
        self.assertIn("scroll-margin-top", self.source)
        self.assertIn("font-size: 16px", self.source)
        self.assertIn("overflow-wrap: anywhere", self.source)
        self.assertIn("feedbackWaitlistCtaPanel", self.source)
        self.assertIn("resultFollowupCtaPanel", self.source)
        self.assertIn("After generating, help shape the next version", self.source)
        self.assertIn("Was the hook useful?", self.source)
        self.assertIn("生成后，帮我们决定下一版怎么改", self.source)
        self.assertIn("Hook 有用吗", self.source)
        self.assertIn("resultFollowupFeedback", self.source)
        self.assertIn("resultFollowupWaitlist", self.source)
        self.assertIn("Join the waitlist", self.source)
        self.assertIn("What should we improve next?", self.source)
        self.assertIn("After you generate a result", self.source)
        self.assertIn("加入试用名单", self.source)
        self.assertIn("下一步应该改进什么", self.source)
        self.assertIn("Try the fastest path", self.source)
        self.assertIn("No login required", self.source)
        self.assertIn("Start with product description", self.source)
        self.assertIn("Start with pasted reviews", self.source)
        self.assertIn("快速试用", self.source)
        self.assertIn("无需登录", self.source)
        self.assertIn("从产品描述开始", self.source)
        self.assertIn("从粘贴评论开始", self.source)
        self.assertIn("Pasted Reviews Mode", self.source)
        self.assertIn("Pasted reviews", self.source)
        self.assertIn("Use sample reviews", self.source)
        self.assertIn("Use pet hair sample", self.source)
        self.assertIn("Use desk lamp sample", self.source)
        self.assertIn("Generate from reviews", self.source)
        self.assertIn("/api/v1/generate-from-reviews", self.source)
        self.assertIn("粘贴评论模式", self.source)
        self.assertIn("根据评论生成", self.source)
        self.assertIn("使用示例评论", self.source)
        self.assertIn("使用宠物毛发示例", self.source)
        self.assertIn("使用台灯示例", self.source)
        self.assertIn("reviewCountPreview", self.source)
        self.assertIn("Review count: 0", self.source)
        self.assertIn("评论条数：0", self.source)
        self.assertIn("function reviewLineCount(value)", self.source)
        self.assertIn("function updateReviewCountPreview()", self.source)
        self.assertIn("reviewPainPointPreview", self.source)
        self.assertIn("Pain point preview", self.source)
        self.assertIn("痛点预览", self.source)
        self.assertIn("function reviewPainPointCandidates(value)", self.source)
        self.assertIn("function updatePainPointPreview()", self.source)
        self.assertIn("function updateReviewInputPreviews()", self.source)
        self.assertIn("What to paste", self.source)
        self.assertIn("Good example", self.source)
        self.assertIn("Weak example", self.source)
        self.assertIn("应该粘贴什么", self.source)
        self.assertIn("好例子", self.source)
        self.assertIn("弱例子", self.source)
        self.assertIn("用户抱怨", self.source)

        zh_reviews_copy_match = re.search(
            r"pastedReviewsMode: '粘贴用户反馈',(?P<body>.*?)exampleGallery: '示例产品库',",
            self.source,
            re.S,
        )
        self.assertIsNotNone(zh_reviews_copy_match)
        zh_reviews_copy_body = zh_reviews_copy_match.group("body")
        self.assertIn("reviewGuideTitle: '应该粘贴什么？'", zh_reviews_copy_body)
        self.assertIn("goodReviewExampleTitle: '好例子'", zh_reviews_copy_body)
        self.assertIn("weakReviewExampleTitle: '弱例子'", zh_reviews_copy_body)
        self.assertNotIn("reviewGuideTitle: 'What to paste'", zh_reviews_copy_body)
        self.assertNotIn("goodReviewExampleTitle: 'Good example'", zh_reviews_copy_body)
        self.assertNotIn("weakReviewExampleTitle: 'Weak example'", zh_reviews_copy_body)
        self.assertIn("电商创意生成助手", self.source)
        self.assertIn("Product name", self.source)
        self.assertIn("Product description", self.source)
        self.assertIn("Customer pain points", self.source)
        self.assertIn("Generate from description", self.source)
        self.assertIn("Use sample product", self.source)
        self.assertIn("Good inputs include", self.source)
        self.assertIn("Describe what the product is, who it is for, and what makes it useful.", self.source)
        self.assertIn("Paste customer complaints, review snippets, objections, or problems your buyers care about.", self.source)
        self.assertIn("便携迷你搅拌机", self.source)
        self.assertIn("Please add more detail before generating.", self.source)
        self.assertIn("function generateFromDescription()", self.source)
        self.assertIn("function fillSampleProductDescription()", self.source)
        self.assertIn("Copy Hook", self.source)
        self.assertIn("Copy Storyboard", self.source)
        self.assertIn("Copy Full Markdown", self.source)
        self.assertIn("Download Markdown", self.source)
        self.assertIn("Download JSON", self.source)
        self.assertIn("Recent Generations", self.source)
        self.assertIn("No recent generations yet.", self.source)
        self.assertIn("View", self.source)
        self.assertIn("Copy Markdown", self.source)
        self.assertIn("Delete", self.source)
        self.assertIn("Clear Recent Generations", self.source)
        self.assertIn("crossgrowth_recent_generations_v1", self.source)
        self.assertIn("Translate to Chinese", self.source)
        self.assertIn("Copy Chinese Translation", self.source)
        self.assertIn("Translate this section", self.source)
        self.assertIn("Copy section translation", self.source)
        self.assertIn("function copyHook()", self.source)
        self.assertIn("function copyStoryboard()", self.source)
        self.assertIn("function copyFullMarkdown()", self.source)
        self.assertIn("function downloadMarkdown()", self.source)
        self.assertIn("function downloadJson()", self.source)
        self.assertIn("function loadRecentGenerations()", self.source)
        self.assertIn("function saveCurrentGenerationToRecent()", self.source)
        self.assertIn("function renderRecentGenerations()", self.source)
        self.assertIn("function viewRecentGeneration(id)", self.source)
        self.assertIn("function copyRecentMarkdown(id)", self.source)
        self.assertIn("function deleteRecentGeneration(id)", self.source)
        self.assertIn("function clearRecentGenerations()", self.source)
        self.assertIn("function translateToChinese()", self.source)
        self.assertIn("function copyChineseTranslation()", self.source)
        self.assertIn("function translateSection(sectionKey)", self.source)
        self.assertIn("function copySectionTranslation(sectionKey)", self.source)


    def test_static_example_gallery_only_sets_product_input(self):
        start = self.source.find("function setDemoSlug(slug)")
        self.assertNotEqual(start, -1)
        body = self.source[start:start + 500]

        self.assertIn("sampleWorkspaceDisplaySlug(slug)", body)
        self.assertNotIn("fetch(", body)
        self.assertNotIn("startSystem()", body)
        self.assertNotIn("generateFromDescription()", body)
        self.assertNotIn("generateFromReviews()", body)

        self.assertIn('data-i18n="exampleSlugBalsamic"', self.source)
        self.assertIn('data-i18n="exampleSlugPetHair"', self.source)
        self.assertIn('data-i18n="exampleSlugDeskLamp"', self.source)
        self.assertIn('data-i18n="samplePainPointsLabel"', self.source)
        self.assertIn('data-i18n="sampleHookLabel"', self.source)
        self.assertIn('data-i18n="sampleStoryboardLabel"', self.source)

        self.assertIn("const SAMPLE_WORKSPACE_COPY", self.source)
        self.assertIn("exampleBalsamicPain", self.source)
        self.assertIn("examplePetHairHook", self.source)
        self.assertIn("exampleDeskLampStoryboard", self.source)
    def test_result_followup_cta_is_static_and_frontend_only(self):
        self.assertIn("resultFollowupCtaPanel", self.source)
        self.assertIn("resultFollowupTitle", self.source)
        self.assertIn("resultFollowupFeedback", self.source)
        self.assertIn("resultFollowupWaitlist", self.source)
        self.assertIn("docs.google.com/forms", self.source)

        match = re.search(
            r'<div id="resultFollowupCtaPanel"(?P<body>.*?)</div>\s*</div>',
            self.source,
            re.S,
        )
        self.assertIsNotNone(match)
        body = match.group("body")

        self.assertIn("Give feedback", body)
        self.assertIn("Join the waitlist", body)

        self.assertNotIn("fetch(", body)
        self.assertNotIn("postPastedReviews", body)
        self.assertNotIn("postProductDescription", body)
        self.assertNotIn("generate-copilot", body)
        self.assertNotIn("debug-copilot", body)
        self.assertNotIn("debug-source-probe", body)
        self.assertNotIn("runSourceProbe", body)
        self.assertNotIn("amazonShadowMode", body)
        self.assertNotIn("saveCurrentGenerationToRecent", body)
        self.assertNotIn("localStorage", body)
        self.assertNotIn("data.debug", body)
        self.assertNotIn("telemetry_summary", body)
        self.assertNotIn("shadow_sources", body)
        self.assertNotIn("memory_observability", body)

    def test_evidence_source_label_is_frontend_only(self):
        self.assertIn("function renderEvidenceSourceCard(evidence)", self.source)
        self.assertIn("function splitEvidenceForDisplay(evidence)", self.source)
        self.assertIn("evidenceSourceCard", self.source)
        self.assertIn("evidenceSourceTitle", self.source)
        self.assertIn("sourceTypeLabel", self.source)
        self.assertIn("sourceConfidenceLabel", self.source)
        self.assertIn("reviewCountLabel", self.source)
        self.assertIn("dataWarningsLabel", self.source)
        self.assertIn("customerReviewSnippets", self.source)
        self.assertIn("productContextBlock", self.source)
        self.assertIn("No customer review snippets returned yet.", self.source)

        start = self.source.find("function renderEvidenceSourceCard(evidence)")
        end = self.source.find("function resultCreativeSummary", start)
        self.assertNotEqual(start, -1)
        self.assertNotEqual(end, -1)

        body = self.source[start:end]

        self.assertIn("source_type", body)
        self.assertIn("data_warnings", body)
        self.assertIn("review_count", body)
        self.assertIn("review_confidence", body)
        split_start = self.source.find("function splitEvidenceForDisplay(evidence)")
        split_end = self.source.find("function renderStoryboardBrief", split_start)
        self.assertNotEqual(split_start, -1)
        self.assertNotEqual(split_end, -1)
        split_body = self.source[split_start:split_end]
        self.assertIn("user_provided_description", split_body)
        self.assertIn("reviewQuotes", split_body)
        self.assertIn("contextLines", split_body)

        self.assertNotIn("fetch(", body)
        self.assertNotIn("postPastedReviews", body)
        self.assertNotIn("postProductDescription", body)
        self.assertNotIn("generate-copilot", body)
        self.assertNotIn("debug-copilot", body)
        self.assertNotIn("debug-source-probe", body)
        self.assertNotIn("runSourceProbe", body)
        self.assertNotIn("amazonShadowMode", body)
        self.assertNotIn("saveCurrentGenerationToRecent", body)
        self.assertNotIn("localStorage", body)
        self.assertNotIn("data.debug", body)
        self.assertNotIn("telemetry_summary", body)
        self.assertNotIn("shadow_sources", body)
        self.assertNotIn("memory_observability", body)

    def test_result_display_uses_clean_hook_cta_and_localized_debug_labels(self):
        self.assertIn("function cleanHookLine(script)", self.source)
        self.assertIn("function cleanCtaLine(script)", self.source)
        self.assertIn("function stripStructuredScriptPrefix(text)", self.source)
        self.assertIn("const cleanHook = cleanHookLine(script);", self.source)
        self.assertIn("const cleanCta = cleanCtaLine(script);", self.source)
        self.assertIn("${block(t('hook'), cleanHook || '')}", self.source)
        self.assertIn("${block(t('cta'), cleanCta || '')}", self.source)
        self.assertIn("${block(t('ctaLogic'), cleanCta || '')}", self.source)
        self.assertIn("requestFailed", self.source)
        self.assertIn("probeStatus", self.source)
        self.assertIn("amazonShadowSummary", self.source)
        self.assertIn("rawDebugState", self.source)
        self.assertIn("主 Hook", self.source)
        self.assertIn("画面：${visual}", self.source)
        self.assertIn("旁白：${narration}", self.source)

    def test_storyboard_scene_readability_is_frontend_only(self):
        self.assertIn("function renderStoryboardBrief(storyboard)", self.source)
        self.assertIn("storyboard-scene-list", self.source)
        self.assertIn("storyboard-scene-card", self.source)
        self.assertIn("storyboard-scene-evidence", self.source)

        start = self.source.find("function renderStoryboardBrief(storyboard)")
        end = self.source.find("let latestDebugCategory", start)
        self.assertNotEqual(start, -1)
        self.assertNotEqual(end, -1)

        body = self.source[start:end]

        self.assertIn("scene_goal", body)
        self.assertIn("visual_description", body)
        self.assertIn("evidence_quote_used", body)
        self.assertIn("linked_painpoint", body)

        self.assertNotIn("fetch(", body)
        self.assertNotIn("postPastedReviews", body)
        self.assertNotIn("postProductDescription", body)
        self.assertNotIn("generate-copilot", body)
        self.assertNotIn("debug-copilot", body)
        self.assertNotIn("debug-source-probe", body)
        self.assertNotIn("runSourceProbe", body)
        self.assertNotIn("amazonShadowMode", body)
        self.assertNotIn("saveCurrentGenerationToRecent", body)
        self.assertNotIn("localStorage", body)
        self.assertNotIn("data.debug", body)
        self.assertNotIn("telemetry_summary", body)
        self.assertNotIn("shadow_sources", body)
        self.assertNotIn("memory_observability", body)

    def test_chinese_recent_actions_and_bottom_ctas_are_deduped(self):
        self.assertIn("/* L18.1-D dedupe bottom feedback/waitlist UI */", self.source)
        self.assertIn(".feedback-panel,", self.source)
        self.assertIn("#waitlistPanel", self.source)

        self.assertIn("recentView: '查看'", self.source)
        self.assertIn("recentCopyMarkdown: '复制 Markdown'", self.source)
        self.assertIn("recentDelete: '删除'", self.source)

        self.assertIn("${escapeHTML(t('recentView'))}", self.source)
        self.assertIn("${escapeHTML(t('recentCopyMarkdown'))}", self.source)
        self.assertIn("${escapeHTML(t('recentDelete'))}", self.source)

        zh_start = self.source.find("'zh-CN': {")
        self.assertNotEqual(zh_start, -1)
        zh_end = self.source.find("\n        };\n\n        function t", zh_start)
        self.assertNotEqual(zh_end, -1)
        zh_copy = self.source[zh_start:zh_end]

        self.assertNotIn("recentView: 'View'", zh_copy)
        self.assertNotIn("recentCopyMarkdown: 'Copy Markdown'", zh_copy)
        self.assertNotIn("recentDelete: 'Delete'", zh_copy)

    def test_chinese_mode_bottom_sections_are_localized(self):
        self.assertIn("inlineResultPanelTitle: '你的生成结果'", self.source)
        self.assertIn("recentEmptyState: '还没有最近生成记录。'", self.source)
        self.assertIn("clearRecentGenerations: '清空最近生成记录'", self.source)
        self.assertIn("waitlistTitle: '加入试用名单'", self.source)
        self.assertIn("waitlistBody: '想把它用在你自己的产品上？", self.source)

        zh_start = self.source.find("'zh-CN': {")
        self.assertNotEqual(zh_start, -1)
        zh_end = self.source.find("\n        };\n\n        function t", zh_start)
        self.assertNotEqual(zh_end, -1)
        zh_copy = self.source[zh_start:zh_end]

        self.assertNotIn("Join the waitlist", zh_copy)
        self.assertNotIn("No recent generations yet.", zh_copy)
        self.assertNotIn("Clear Recent Generations", zh_copy)
        self.assertNotIn("After you generate, the Hook, storyboard, and copy actions will appear here in this same workspace.", zh_copy)

    def test_chinese_mode_microcopy_and_placeholders_are_localized(self):
        self.assertIn("workflowPathTitle: '选择你的生成方式'", self.source)
        self.assertIn("workflowPathSubtitle: '根据你手上已有的素材选择一条路径。", self.source)
        self.assertIn("pathProductIdeaBody: '适合你知道产品是什么", self.source)
        self.assertIn("pathCustomerFeedbackBody: '适合你已经有差评", self.source)
        self.assertIn("pathSampleProductBody: '不用填写内容", self.source)
        self.assertIn("document.querySelectorAll('[data-i18n-placeholder]')", self.source)
        self.assertIn('id="descriptionProductDescription"', self.source)
        self.assertIn('data-i18n-placeholder="descriptionProductDescriptionPlaceholder"', self.source)
        self.assertIn('id="descriptionPainPoints"', self.source)
        self.assertIn('data-i18n-placeholder="descriptionPainPointsPlaceholder"', self.source)
        self.assertIn('id="reviewsPastedReviews"', self.source)
        self.assertIn('data-i18n-placeholder="reviewsPastedReviewsPlaceholder"', self.source)

        zh_start = self.source.find("'zh-CN': {")
        self.assertNotEqual(zh_start, -1)
        zh_end = self.source.find("        };", zh_start)
        self.assertNotEqual(zh_end, -1)
        zh_copy = self.source[zh_start:zh_end]

        self.assertNotIn("missingName: 'Please enter a product name.'", zh_copy)
        self.assertNotIn("missingDescription: 'Please enter a product description.'", zh_copy)
        self.assertNotIn("inputTooShort: 'Please add more detail before generating.'", zh_copy)

    def test_first_run_guide_copy_is_frontend_only(self):
        self.assertIn("firstRunGuidePanel", self.source)
        self.assertIn("firstRunGuideTitle", self.source)
        self.assertIn("firstRunGuideStepOne", self.source)
        self.assertIn("descriptionFirstRunGuide", self.source)
        self.assertIn("reviewsFirstRunGuide", self.source)

        start = self.source.find('id="firstRunGuidePanel"')
        self.assertNotEqual(start, -1)
        end = self.source.find('<div class="demo-warning"', start)
        self.assertNotEqual(end, -1)
        body = self.source[start:end]

        self.assertIn("data-i18n", body)
        self.assertIn("first-run-guide-steps", body)

        self.assertNotIn("fetch(", body)
        self.assertNotIn("postPastedReviews", body)
        self.assertNotIn("postProductDescription", body)
        self.assertNotIn("generate-copilot", body)
        self.assertNotIn("debug-copilot", body)
        self.assertNotIn("debug-source-probe", body)
        self.assertNotIn("runSourceProbe", body)
        self.assertNotIn("amazonShadowMode", body)
        self.assertNotIn("saveCurrentGenerationToRecent", body)
        self.assertNotIn("localStorage", body)
        self.assertNotIn("data.debug", body)
        self.assertNotIn("telemetry_summary", body)
        self.assertNotIn("shadow_sources", body)
        self.assertNotIn("memory_observability", body)

    def test_sample_product_library_copy_is_frontend_only(self):
        self.assertIn("sampleProductLibraryGuide", self.source)
        self.assertIn("sampleProductLibraryTitle", self.source)
        self.assertIn("sampleProductLibraryBody", self.source)
        self.assertIn("sampleProductLibraryTipOne", self.source)
        self.assertIn("sourceBadgeProductDescription", self.source)
        self.assertIn("sourceBadgePastedReviews", self.source)

        start = self.source.find('id="sampleProductLibraryGuide"')
        self.assertNotEqual(start, -1)
        body = self.source[start:start + 1800]

        self.assertIn("data-i18n", body)
        self.assertIn("sample-product-library-grid", body)

        self.assertNotIn("fetch(", body)
        self.assertNotIn("postPastedReviews", body)
        self.assertNotIn("postProductDescription", body)
        self.assertNotIn("generate-copilot", body)
        self.assertNotIn("debug-copilot", body)
        self.assertNotIn("debug-source-probe", body)
        self.assertNotIn("runSourceProbe", body)
        self.assertNotIn("amazonShadowMode", body)
        self.assertNotIn("saveCurrentGenerationToRecent", body)
        self.assertNotIn("localStorage", body)
        self.assertNotIn("data.debug", body)
        self.assertNotIn("telemetry_summary", body)
        self.assertNotIn("shadow_sources", body)
        self.assertNotIn("memory_observability", body)

    def test_chinese_onboarding_copy_is_frontend_only(self):
        self.assertIn("chineseOnboardingPanel", self.source)
        self.assertIn("chineseOnboardingTitle", self.source)
        self.assertIn("chineseOnboardingStepOne", self.source)
        self.assertIn("chineseOnboardingStepTwo", self.source)
        self.assertIn("chineseOnboardingStepThree", self.source)
        self.assertIn("chineseOnboardingNote", self.source)

        start = self.source.find('id="chineseOnboardingPanel"')
        self.assertNotEqual(start, -1)
        body = self.source[start:start + 1800]

        self.assertIn("data-i18n", body)
        self.assertIn("chinese-onboarding-steps", body)

        self.assertNotIn("fetch(", body)
        self.assertNotIn("postPastedReviews", body)
        self.assertNotIn("postProductDescription", body)
        self.assertNotIn("generate-copilot", body)
        self.assertNotIn("debug-copilot", body)
        self.assertNotIn("debug-source-probe", body)
        self.assertNotIn("runSourceProbe", body)
        self.assertNotIn("amazonShadowMode", body)
        self.assertNotIn("saveCurrentGenerationToRecent", body)
        self.assertNotIn("localStorage", body)
        self.assertNotIn("data.debug", body)
        self.assertNotIn("telemetry_summary", body)
        self.assertNotIn("shadow_sources", body)
        self.assertNotIn("memory_observability", body)

    def test_result_summary_and_hook_highlight_are_frontend_only(self):
        self.assertIn("function renderResultSummaryCard", self.source)
        self.assertIn("function renderHookHighlightCard", self.source)
        self.assertIn("resultSummaryCard", self.source)
        self.assertIn("resultHookHighlightCard", self.source)

        for function_name in ["renderResultSummaryCard", "renderHookHighlightCard", "resultCreativeSummary"]:
            with self.subTest(function_name=function_name):
                match = re.search(
                    rf"function {function_name}\([^)]*\) \{{(?P<body>.*?)\n        \}}",
                    self.source,
                    re.S,
                )
                self.assertIsNotNone(match)
                body = match.group("body")

                self.assertNotIn("fetch(", body)
                self.assertNotIn("postPastedReviews", body)
                self.assertNotIn("postProductDescription", body)
                self.assertNotIn("generate-copilot", body)
                self.assertNotIn("debug-copilot", body)
                self.assertNotIn("debug-source-probe", body)
                self.assertNotIn("runSourceProbe", body)
                self.assertNotIn("amazonShadowMode", body)
                self.assertNotIn("saveCurrentGenerationToRecent", body)
                self.assertNotIn("localStorage", body)
                self.assertNotIn("data.debug", body)
                self.assertNotIn("telemetry_summary", body)
                self.assertNotIn("shadow_sources", body)
                self.assertNotIn("memory_observability", body)

    def test_mobile_readability_polish_is_css_only(self):
        self.assertIn("L15.3-A mobile readability polish", self.source)

        css_match = re.search(
            r"/\* L15\.3-A mobile readability polish \*/(?P<body>.*?)</style>",
            self.source,
            re.S,
        )
        self.assertIsNotNone(css_match)
        css_body = css_match.group("body")

        self.assertIn("@media (max-width: 720px)", css_body)
        self.assertIn("#quickStartPanel", css_body)
        self.assertIn("#feedbackWaitlistCtaPanel", css_body)
        self.assertIn("#reviewPasteGuide", css_body)
        self.assertIn("scroll-margin-top", css_body)
        self.assertIn("overflow-wrap: anywhere", css_body)

        self.assertNotIn("fetch(", css_body)
        self.assertNotIn("postPastedReviews", css_body)
        self.assertNotIn("postProductDescription", css_body)
        self.assertNotIn("generate-copilot", css_body)
        self.assertNotIn("debug-copilot", css_body)
        self.assertNotIn("debug-source-probe", css_body)
        self.assertNotIn("runSourceProbe", css_body)
        self.assertNotIn("amazonShadowMode", css_body)
        self.assertNotIn("saveCurrentGenerationToRecent", css_body)
        self.assertNotIn("localStorage", css_body)
        self.assertNotIn("data.debug", css_body)
        self.assertNotIn("telemetry_summary", css_body)
        self.assertNotIn("shadow_sources", css_body)
        self.assertNotIn("memory_observability", css_body)

    def test_feedback_waitlist_cta_is_static_and_frontend_only(self):
        self.assertIn("feedbackWaitlistCtaPanel", self.source)
        self.assertIn("feedbackWaitlistTitle", self.source)
        self.assertIn("feedbackWaitlistJoin", self.source)
        self.assertIn("joinWaitlistQuickStart", self.source)
        self.assertIn("docs.google.com/forms", self.source)

        match = re.search(
            r'<div id="feedbackWaitlistCtaPanel"(?P<body>.*?)</div>\s*</div>',
            self.source,
            re.S,
        )
        self.assertIsNotNone(match)
        body = match.group("body")

        self.assertIn("Give feedback", body)
        self.assertIn("Join the waitlist", body)

        self.assertNotIn("fetch(", body)
        self.assertNotIn("postPastedReviews", body)
        self.assertNotIn("postProductDescription", body)
        self.assertNotIn("generate-copilot", body)
        self.assertNotIn("debug-copilot", body)
        self.assertNotIn("debug-source-probe", body)
        self.assertNotIn("runSourceProbe", body)
        self.assertNotIn("amazonShadowMode", body)
        self.assertNotIn("saveCurrentGenerationToRecent", body)
        self.assertNotIn("localStorage", body)
        self.assertNotIn("data.debug", body)
        self.assertNotIn("telemetry_summary", body)
        self.assertNotIn("shadow_sources", body)
        self.assertNotIn("memory_observability", body)

    def test_public_demo_quick_start_ctas_are_frontend_only(self):
        self.assertIn("function scrollToProductDescriptionMode()", self.source)
        self.assertIn("function scrollToPastedReviewsMode()", self.source)
        self.assertIn("function scrollToFeedbackWaitlist()", self.source)
        self.assertIn("setActiveWorkspace('productIdea', { scroll: true });", self.source)
        self.assertIn("setActiveWorkspace('customerFeedback', { scroll: true });", self.source)

        for function_name in [
            "scrollToSectionById",
            "scrollToProductDescriptionMode",
            "scrollToPastedReviewsMode",
            "scrollToFeedbackWaitlist",
        ]:
            with self.subTest(function_name=function_name):
                match = re.search(
                    rf"function {function_name}\([^)]*\) \{{(?P<body>.*?)\n        \}}",
                    self.source,
                    re.S,
                )
                self.assertIsNotNone(match)
                body = match.group("body")

                self.assertNotIn("fetch(", body)
                self.assertNotIn("postPastedReviews", body)
                self.assertNotIn("postProductDescription", body)
                self.assertNotIn("generate-copilot", body)
                self.assertNotIn("debug-copilot", body)
                self.assertNotIn("debug-source-probe", body)
                self.assertNotIn("runSourceProbe", body)
                self.assertNotIn("amazonShadowMode", body)
                self.assertNotIn("saveCurrentGenerationToRecent", body)
                self.assertNotIn("localStorage", body)
                self.assertNotIn("data.debug", body)
                self.assertNotIn("telemetry_summary", body)
                self.assertNotIn("shadow_sources", body)
                self.assertNotIn("memory_observability", body)

    def test_product_description_mode_calls_only_description_endpoint(self):
        self.assertIn("postProductDescription", self.source)
        self.assertIn("/api/v1/generate-from-description", self.source)
        self.assertIn("Please enter a product name.", self.source)
        self.assertIn("Please enter a product description.", self.source)
        self.assertIn("Please add customer pain points or review snippets.", self.source)
        self.assertIn("Source: user_provided_description", self.source)
        self.assertIn("output_language: currentOutputLanguage()", self.source)

        section_match = re.search(
            r"<section class=\"description-mode\"(?P<body>.*?)<section class=\"example-gallery\"",
            self.source,
            re.S,
        )
        self.assertIsNotNone(section_match)
        section_body = section_match.group("body")

        function_match = re.search(
            r"async function generateFromDescription\(\) \{(?P<body>.*?)\n        function renderProductDashboard",
            self.source,
            re.S,
        )
        self.assertIsNotNone(function_match)
        function_body = function_match.group("body")

        self.assertIn("postProductDescription({", function_body)
        self.assertIn("output_language: currentOutputLanguage()", function_body)
        self.assertIn("renderProductDashboard(response.data", function_body)
        self.assertIn("saveCurrentGenerationToRecent();", function_body)

        for body in [section_body, function_body]:
            with self.subTest(description_boundary=body[:40]):
                self.assertNotIn("generate-copilot", body)
                self.assertNotIn("debug-source-probe", body)
                self.assertNotIn("debug-copilot", body)
                self.assertNotIn("runSourceProbe", body)
                self.assertNotIn("renderDebugPanel", body)
                self.assertNotIn("data.debug", body)
                self.assertNotIn("telemetry_summary", body)
                self.assertNotIn("shadow_sources", body)
                self.assertNotIn("memory_observability", body)




    def test_product_description_sample_only_fills_inputs(self):
        fill_start = self.source.find("function fillSampleProductDescription()")
        self.assertNotEqual(fill_start, -1)
        fill_body = self.source[fill_start:fill_start + 500]

        self.assertIn("applyProductDescriptionSample(sampleInputProfile().productDescription)", fill_body)
        self.assertIn("setDescriptionStatus(t('sampleFilled'))", fill_body)
        self.assertNotIn("generateFromDescription()", fill_body)
        self.assertNotIn("fetch(", fill_body)

        helper_start = self.source.find("function applyProductDescriptionSample(sample)")
        self.assertNotEqual(helper_start, -1)
        helper_body = self.source[helper_start:helper_start + 900]

        self.assertIn("descriptionProductName", helper_body)
        self.assertIn("descriptionProductCategory", helper_body)
        self.assertIn("descriptionProductDescription", helper_body)
        self.assertIn("descriptionPainPoints", helper_body)
        self.assertIn("descriptionTargetPlatform", helper_body)
        self.assertIn("descriptionGoal", helper_body)
        self.assertIn("'TikTok'", helper_body)
        self.assertIn("'tiktok_ctr'", helper_body)

        zh_lamp = "\u67d4\u5149\u684c\u9762\u53f0\u706f"
        zh_pain = "\u7528\u6237\u89c9\u5f97\u666e\u901a\u53f0\u706f\u665a\u4e0a\u592a\u523a\u773c"
        self.assertIn("SoftGlow Desk Lamp", self.source)
        self.assertIn("A compact adjustable desk lamp", self.source)
        self.assertIn("Buyers complain that desk lamps feel too harsh", self.source)
        self.assertIn(zh_lamp, self.source)
        self.assertIn(zh_pain, self.source)
    def test_pasted_reviews_mode_calls_only_reviews_endpoint(self):
        self.assertIn("postPastedReviews", self.source)
        self.assertIn("/api/v1/generate-from-reviews", self.source)
        self.assertIn("function generateFromReviews()", self.source)
        self.assertIn("function fillSamplePastedReviews()", self.source)
        self.assertIn("Source: user_pasted_reviews", self.source)

        section_match = re.search(
            r"<section class=\"description-mode\" id=\"pastedReviewsMode\"(?P<body>.*?)<section class=\"example-gallery\"",
            self.source,
            re.S,
        )
        self.assertIsNotNone(section_match)
        section_body = section_match.group("body")
        self.assertIn("Pasted Reviews Mode", section_body)
        self.assertIn("Pasted reviews", section_body)
        self.assertIn("Use sample reviews", section_body)
        self.assertIn("Use pet hair sample", section_body)
        self.assertIn("Use desk lamp sample", section_body)
        self.assertIn("Generate from reviews", section_body)
        self.assertIn("reviewPasteGuide", section_body)
        self.assertIn("What to paste", section_body)
        self.assertIn("Good example", section_body)
        self.assertIn("Weak example", section_body)
        self.assertIn("reviewCountPreview", section_body)
        self.assertIn("reviewPainPointPreview", section_body)
        self.assertIn("oninput=\"updateReviewInputPreviews()\"", section_body)

        function_match = re.search(
            r"async function generateFromReviews\(\) \{(?P<body>.*?)\n        function renderProductDashboard",
            self.source,
            re.S,
        )
        self.assertIsNotNone(function_match)
        function_body = function_match.group("body")
        self.assertIn("postPastedReviews({", function_body)
        self.assertIn("output_language: currentOutputLanguage()", function_body)
        self.assertIn("renderProductDashboard(response.data", function_body)
        self.assertIn("saveCurrentGenerationToRecent();", function_body)

        for body in [section_body, function_body]:
            with self.subTest(reviews_boundary=body[:40]):
                self.assertNotIn("generate-copilot", body)
                self.assertNotIn("debug-source-probe", body)
                self.assertNotIn("debug-copilot", body)
                self.assertNotIn("runSourceProbe", body)
                self.assertNotIn("renderDebugPanel", body)
                self.assertNotIn("data.debug", body)
                self.assertNotIn("telemetry_summary", body)
                self.assertNotIn("shadow_sources", body)
                self.assertNotIn("memory_observability", body)




    def test_pasted_reviews_sample_only_fills_inputs(self):
        fill_start = self.source.find("function fillSamplePastedReviews()")
        self.assertNotEqual(fill_start, -1)
        fill_body = self.source[fill_start:fill_start + 500]

        self.assertIn("applyReviewSample(sampleInputProfile().miniBlender)", fill_body)
        self.assertIn("setReviewsStatus(t('reviewsSampleFilled'))", fill_body)
        self.assertIn("updateReviewInputPreviews()", fill_body)
        self.assertNotIn("generateFromReviews()", fill_body)
        self.assertNotIn("fetch(", fill_body)

        helper_start = self.source.find("function applyReviewSample(sample)")
        self.assertNotEqual(helper_start, -1)
        helper_body = self.source[helper_start:helper_start + 900]

        self.assertIn("reviewsProductName", helper_body)
        self.assertIn("reviewsProductCategory", helper_body)
        self.assertIn("reviewsProductDescription", helper_body)
        self.assertIn("reviewsPastedReviews", helper_body)
        self.assertIn("reviewsTargetPlatform", helper_body)
        self.assertIn("reviewsGoal", helper_body)
        self.assertIn("sample.reviews", helper_body)
        self.assertIn("reviewsPastedReviews", helper_body)
        self.assertIn("'TikTok'", helper_body)
        self.assertIn("'tiktok_ctr'", helper_body)

        zh_blender = "\u4fbf\u643a\u8ff7\u4f60\u6405\u62cc\u673a"
        zh_kitchen = "\u53a8\u623f\u5c0f\u5bb6\u7535"
        zh_review_1 = "\u6211\u8ba8\u538c\u6bcf\u5929\u65e9\u4e0a\u6e05\u6d17\u5927\u6405\u62cc\u673a\u3002"
        zh_review_2 = "\u6211\u5e0c\u671b\u5728\u529e\u516c\u5ba4\u4e5f\u80fd\u5feb\u901f\u6253\u4e00\u676f\u3002"

        self.assertIn("Portable mini blender", self.source)
        self.assertIn("Kitchen appliance", self.source)
        self.assertIn("A compact rechargeable blender for smoothies", self.source)
        self.assertIn("I hate cleaning my big blender every morning.", self.source)
        self.assertIn("I wish I could blend something quickly at work.", self.source)

        self.assertIn(zh_blender, self.source)
        self.assertIn(zh_kitchen, self.source)
        self.assertIn(zh_review_1, self.source)
        self.assertIn(zh_review_2, self.source)

    def test_pasted_reviews_extra_samples_only_fill_inputs(self):
        samples = {
            "fillSamplePetHairReviews": "petHair",
            "fillSampleDeskLampReviews": "deskLamp",
        }

        for function_name, sample_key in samples.items():
            with self.subTest(sample_function=function_name):
                start = self.source.find(f"function {function_name}()")
                self.assertNotEqual(start, -1)
                body = self.source[start:start + 500]

                self.assertIn(f"applyReviewSample(sampleInputProfile().{sample_key})", body)
                self.assertIn("setReviewsStatus(t(", body)
                self.assertIn("updateReviewInputPreviews()", body)
                self.assertNotIn("generateFromReviews()", body)
                self.assertNotIn("fetch(", body)

        zh_pet_name = "\u5ba0\u7269\u6bdb\u53d1\u6e05\u6d01\u5237"
        zh_pet_category = "\u5ba0\u7269\u6e05\u6d01\u914d\u4ef6"
        zh_pet_review = "\u4e0d\u7ba1\u6211\u600e\u4e48\u5438\uff0c\u6c99\u53d1\u4e0a\u8fd8\u662f\u7c98\u7740\u5ba0\u7269\u6bdb\u3002"
        zh_lamp_name = "\u53ef\u8c03\u8282\u684c\u9762\u53f0\u706f"
        zh_lamp_category = "\u5bb6\u7528\u529e\u516c\u7167\u660e"
        zh_lamp_review = "\u6211\u7684\u4fbf\u5b9c\u53f0\u706f\u665a\u4e0a\u5de5\u4f5c\u65f6\u4f1a\u95ea\u3002"

        self.assertIn("Pet hair vacuum brush", self.source)
        self.assertIn("Pet cleaning accessory", self.source)
        self.assertIn("Pet hair sticks to my couch", self.source)
        self.assertIn(zh_pet_name, self.source)
        self.assertIn(zh_pet_category, self.source)
        self.assertIn(zh_pet_review, self.source)

        self.assertIn("Adjustable desk lamp", self.source)
        self.assertIn("Home office lighting", self.source)
        self.assertIn("My cheap desk lamp flickers", self.source)
        self.assertIn(zh_lamp_name, self.source)
        self.assertIn(zh_lamp_category, self.source)
        self.assertIn(zh_lamp_review, self.source)
    def test_pasted_reviews_review_count_preview_is_frontend_only(self):
        self.assertIn("function reviewLineCount(value)", self.source)
        self.assertIn("function updateReviewCountPreview()", self.source)
        self.assertIn("reviewPainPointPreview", self.source)
        self.assertIn("Pain point preview", self.source)
        self.assertIn("痛点预览", self.source)
        self.assertIn("function reviewPainPointCandidates(value)", self.source)
        self.assertIn("function updatePainPointPreview()", self.source)
        self.assertIn("function updateReviewInputPreviews()", self.source)
        self.assertIn("reviewCountEmpty", self.source)

        match = re.search(
            r"function updateReviewCountPreview\(\) \{(?P<body>.*?)\n        \}",
            self.source,
            re.S,
        )
        self.assertIsNotNone(match)
        body = match.group("body")

        self.assertIn("reviewLineCount", body)
        self.assertIn("reviewCountPreview", body)
        self.assertIn("currentOutputLanguage()", body)

        self.assertNotIn("postPastedReviews", body)
        self.assertNotIn("generate-from-reviews", body)
        self.assertNotIn("generate-copilot", body)
        self.assertNotIn("debug-copilot", body)
        self.assertNotIn("debug-source-probe", body)
        self.assertNotIn("runSourceProbe", body)
        self.assertNotIn("amazonShadowMode", body)
        self.assertNotIn("saveCurrentGenerationToRecent", body)
        self.assertNotIn("localStorage", body)
        self.assertNotIn("data.debug", body)
        self.assertNotIn("telemetry_summary", body)
        self.assertNotIn("shadow_sources", body)
        self.assertNotIn("memory_observability", body)

    def test_pasted_reviews_pain_point_preview_is_frontend_only(self):
        self.assertIn("function reviewPainPointCandidates(value)", self.source)
        self.assertIn("function updatePainPointPreview()", self.source)
        self.assertIn("function updateReviewInputPreviews()", self.source)
        self.assertIn("painPointPreviewEmpty", self.source)
        self.assertIn("painPointPreviewTitle", self.source)

        match = re.search(
            r"function updatePainPointPreview\(\) \{(?P<body>.*?)\n        \}\n\n        function updateReviewInputPreviews",
            self.source,
            re.S,
        )
        self.assertIsNotNone(match)
        body = match.group("body")

        self.assertIn("reviewPainPointPreview", body)
        self.assertIn("reviewPainPointCandidates", body)
        self.assertIn("painPointPreviewEmpty", body)
        self.assertIn("painPointPreviewTitle", body)

        self.assertNotIn("postPastedReviews", body)
        self.assertNotIn("generate-from-reviews", body)
        self.assertNotIn("generate-copilot", body)
        self.assertNotIn("debug-copilot", body)
        self.assertNotIn("debug-source-probe", body)
        self.assertNotIn("runSourceProbe", body)
        self.assertNotIn("amazonShadowMode", body)
        self.assertNotIn("saveCurrentGenerationToRecent", body)
        self.assertNotIn("localStorage", body)
        self.assertNotIn("data.debug", body)
        self.assertNotIn("telemetry_summary", body)
        self.assertNotIn("shadow_sources", body)
        self.assertNotIn("memory_observability", body)

    def test_language_mode_passes_output_language_without_debug_leakage(self):
        self.assertIn("const urlInput = sampleWorkspaceSlugFromValue(document.getElementById('urlInput').value.trim());", self.source)
        self.assertIn("const payload = { url: urlInput, goal: 'tiktok_ctr', output_language: currentOutputLanguage() };", self.source)
        self.assertIn("output_language: currentOutputLanguage()", self.source)

        recent_match = re.search(
            r"function currentRecentRecord\(\) \{(?P<body>.*?)function saveCurrentGenerationToRecent",
            self.source,
            re.S,
        )
        self.assertIsNotNone(recent_match)
        recent_body = recent_match.group("body")
        self.assertIn("output_language: currentOutputLanguage()", recent_body)

        view_match = re.search(
            r"function viewRecentGeneration\(id\) \{(?P<body>.*?)function copyRecentMarkdown",
            self.source,
            re.S,
        )
        self.assertIsNotNone(view_match)
        view_body = view_match.group("body")
        self.assertIn("record.output_language", view_body)
        self.assertIn("applyLanguageCopy();", view_body)

        for body in [recent_body, view_body]:
            with self.subTest(language_boundary=body[:40]):
                self.assertNotIn("data.debug", body)
                self.assertNotIn("shadow_sources", body)
                self.assertNotIn("telemetry_summary", body)
                self.assertNotIn("memory_observability", body)

    def test_product_renderer_does_not_display_observability_fields(self):
        match = re.search(
            r"function renderProductDashboard\(data, options = \{\}\) \{(?P<body>.*?)function renderAmazonShadowSummary",
            self.source,
            re.S,
        )
        self.assertIsNotNone(match)
        body = match.group("body")
        self.assertNotIn("shadow_sources", body)
        self.assertNotIn("telemetry", body)
        self.assertNotIn("telemetry_summary", body)
        self.assertNotIn("memory_observability", body)

    def test_product_mode_result_readability_sections_are_present(self):
        for label in [
            "Evidence Snapshot",
            "Target Audience",
            "Creative Strategy",
            "Hook / Storyboard",
            "Copy / Download / Translation Actions",
            "Evaluation",
            "Core Hook Strategy",
            "Emotional Trigger",
            "CTA Logic",
            "Visual",
            "Narration",
            "Evidence",
            "Approved",
            "Grounded",
            "Risk Level",
            "Grounded CTR",
            "Evidence Alignment",
        ]:
            with self.subTest(label=label):
                self.assertIn(label, self.source)
        self.assertIn("function renderStoryboardBrief(storyboard)", self.source)
        self.assertIn("storyboard-scene-list", self.source)
        self.assertIn("storyboard-scene-card", self.source)
        self.assertIn("storyboard-scene-number", self.source)
        self.assertIn("storyboard-scene-evidence", self.source)
        self.assertIn("Copy Hook", self.source)
        self.assertIn("Copy Storyboard", self.source)
        self.assertIn("Copy Full Markdown", self.source)
        self.assertIn("Download Markdown", self.source)
        self.assertIn("Download JSON", self.source)
        self.assertIn("Translate to Chinese", self.source)
        self.assertIn("Copy Chinese Translation", self.source)
        self.assertIn("Translate this section", self.source)
        self.assertIn("Copy section translation", self.source)

    def test_translation_button_uses_product_markdown_only(self):
        self.assertIn("postCopilot('translate-output'", self.source)
        self.assertIn("const text = productMarkdown(latestProductData);", self.source)
        self.assertIn("Translation unavailable. Original English result is unchanged.", self.source)
        self.assertIn("latestChineseTranslation = '';", self.source)

    def test_download_actions_export_only_product_visible_state(self):
        self.assertIn("function buildDownloadMarkdown(data)", self.source)
        self.assertIn("function exportVisibleProductJson(data)", self.source)
        self.assertIn("function downloadMarkdown()", self.source)
        self.assertIn("function downloadJson()", self.source)
        self.assertIn("function downloadTextFile(filename, content, mimeType)", self.source)
        self.assertIn("creative_brief_${slug}_${exportTimestamp()}.md", self.source)
        self.assertIn("creative_brief_${slug}_${exportTimestamp()}.json", self.source)
        self.assertIn("input_slug: latestInputSlug || ''", self.source)
        self.assertIn("generated_at: latestGeneratedAt || ''", self.source)
        self.assertIn("translations: {", self.source)

        markdown_match = re.search(
            r"function buildDownloadMarkdown\(data\) \{(?P<body>.*?)function exportVisibleProductJson",
            self.source,
            re.S,
        )
        self.assertIsNotNone(markdown_match)
        markdown_body = markdown_match.group("body")

        json_match = re.search(
            r"function exportVisibleProductJson\(data\) \{(?P<body>.*?)function downloadTextFile",
            self.source,
            re.S,
        )
        self.assertIsNotNone(json_match)
        json_body = json_match.group("body")

        for body in [markdown_body, json_body]:
            with self.subTest(export_body=body[:40]):
                self.assertNotIn("data.debug", body)
                self.assertNotIn("shadow_sources", body)
                self.assertNotIn("telemetry_summary", body)
                self.assertNotIn("memory_observability", body)
                self.assertNotIn("api_key", body.lower())

    def test_recent_generations_store_product_visible_state_only(self):
        self.assertIn("const RECENT_GENERATIONS_KEY = 'crossgrowth_recent_generations_v1';", self.source)
        self.assertIn("const MAX_RECENT_GENERATIONS = 10;", self.source)
        self.assertIn("localStorage.getItem(RECENT_GENERATIONS_KEY)", self.source)
        self.assertIn("localStorage.setItem(", self.source)
        self.assertIn(".slice(0, MAX_RECENT_GENERATIONS)", self.source)
        self.assertIn("saveCurrentGenerationToRecent();", self.source)
        self.assertIn("renderRecentGenerations();", self.source)
        self.assertIn("full_chinese_translation: latestChineseTranslation || ''", self.source)
        self.assertIn("section_translations: sectionTranslationPayload()", self.source)

        record_match = re.search(
            r"function currentRecentRecord\(\) \{(?P<body>.*?)function saveCurrentGenerationToRecent",
            self.source,
            re.S,
        )
        self.assertIsNotNone(record_match)
        record_body = record_match.group("body")

        visible_match = re.search(
            r"function visibleProductData\(data\) \{(?P<body>.*?)function cloneVisibleProductData",
            self.source,
            re.S,
        )
        self.assertIsNotNone(visible_match)
        visible_body = visible_match.group("body")

        for body in [record_body, visible_body]:
            with self.subTest(recent_body=body[:40]):
                self.assertNotIn("data.debug", body)
                self.assertNotIn("shadow_sources", body)
                self.assertNotIn("telemetry_summary", body)
                self.assertNotIn("memory_observability", body)
                self.assertNotIn("api_key", body.lower())

    def test_section_translation_uses_product_visible_section_cache(self):
        self.assertIn("let sectionTranslations = {};", self.source)
        self.assertIn("let sectionTextCache = {};", self.source)
        self.assertIn("function resetSectionTranslations()", self.source)
        self.assertIn("resetSectionTranslations();", self.source)
        self.assertIn("function buildSectionText(data)", self.source)
        self.assertIn("sectionTextCache = buildSectionText(data);", self.source)
        self.assertIn("function renderSectionHeader(title, key)", self.source)
        for title, key in [
            ("Evidence Snapshot", "evidence"),
            ("Target Audience & Creative Strategy", "strategy"),
            ("Hook", "hook"),
            ("Storyboard", "storyboard"),
            ("Evaluation", "evaluation"),
        ]:
            with self.subTest(key=key):
                self.assertIn(title, self.source)
        for label_key, section_key in [
            ("evidenceSnapshot", "evidence"),
            ("targetAudienceStrategy", "strategy"),
            ("hook", "hook"),
            ("storyboard", "storyboard"),
            ("evaluation", "evaluation"),
        ]:
            with self.subTest(section_key=section_key):
                self.assertIn(f"renderSectionHeader(t('{label_key}'), '{section_key}')", self.source)
        self.assertIn("const text = (sectionTextCache[sectionKey] || '').trim();", self.source)
        self.assertIn("Translating this section...", self.source)
        self.assertIn("No section text available for translation.", self.source)
        self.assertIn("Translation failed. Please try again.", self.source)
        self.assertIn("Translation returned empty result. Please try again.", self.source)



    def test_l26_amazon_product_path_reuses_description_generation_flow(self):
        self.assertIn('id="pathAmazonProductCard"', self.source)
        self.assertIn('id="amazonProductWorkspace"', self.source)
        self.assertIn("amazonProductWorkspace.appendChild(amazonIntakePanel);", self.source)
        self.assertIn("async function generateFromAmazonIntake()", self.source)
        self.assertIn("amazonIntakeGenerateBtn", self.source)

        match = re.search(
            r"async function generateFromAmazonIntake\(\) \{(?P<body>.*?)\n        \}",
            self.source,
            re.S,
        )
        self.assertIsNotNone(match)
        body = match.group("body")

        self.assertIn("applyAmazonIntakeToDescriptionForm();", body)
        self.assertIn("await generateFromDescription();", body)
        self.assertIn("amazonGenerateMissing", body)
        self.assertIn("amazonGenerated", body)

        self.assertNotIn("/api/v1/amazon-generate", self.source)
        self.assertNotIn("postProductDescription({", body)
        self.assertNotIn("renderProductDashboard(response.data", body)
        self.assertNotIn("saveCurrentGenerationToRecent();", body)
        self.assertNotIn("debug-source-probe", body)
        self.assertNotIn("debug-copilot", body)
        self.assertNotIn("amazonShadowMode", body)


    def test_l26_amazon_intake_homepage_panel_is_primary_but_upgrade_ready(self):
        self.assertIn('id="amazonIntakePanel"', self.source)
        self.assertIn('data-amazon-intake-panel', self.source)
        self.assertIn('data-upgrade-target="amazon-path-card"', self.source)
        self.assertIn('id="amazonIntakeUpgradeAnchor"', self.source)
        self.assertIn("async function postAmazonIntake(payload)", self.source)
        self.assertIn("async function runAmazonIntake()", self.source)
        self.assertIn("function applyAmazonIntakeToDescriptionForm()", self.source)
        self.assertIn("async function generateFromAmazonIntake()", self.source)
        self.assertIn("amazonIntakeGenerateBtn", self.source)
        self.assertIn("pathAmazonProductTitle", self.source)
        self.assertIn("/api/v1/amazon-intake", self.source)
        self.assertIn("latestAmazonIntakeData", self.source)
        self.assertIn("amazonIntakeUpgradeNote", self.source)

        self.assertIn("function mountUserTaskFlow()", self.source)
        self.assertIn("productIdeaWorkspace.appendChild(productDescriptionMode);", self.source)
        self.assertIn("function setActiveWorkspace(name, options = {})", self.source)

        self.assertNotIn("pathAmazonIntakeCard", self.source)

        match = re.search(
            r"async function runAmazonIntake\(\) \{(?P<body>.*?)function applyAmazonIntakeToDescriptionForm",
            self.source,
            re.S,
        )
        self.assertIsNotNone(match)
        body = match.group("body")
        self.assertNotIn("debug-source-probe", body)
        self.assertNotIn("debug-copilot", body)
        self.assertNotIn("amazonShadowMode", body)
        self.assertNotIn("generate-copilot", body)













    def test_l30b_multiline_placeholders_convert_literal_backslash_n(self):
        self.assertIn("function normalizeLocalizedPlaceholderText(value)", self.source)
        self.assertIn("replaceAll('\\\\n', String.fromCharCode(10))", self.source)
        self.assertIn("normalizeLocalizedPlaceholderText(t(key))", self.source)
        self.assertIn("reviewsPastedReviewsPlaceholder", self.source)

    def test_l30_generate_from_amazon_uses_full_review_insight_pack(self):
        self.assertIn("function amazonInsightSectionText(label, items)", self.source)
        self.assertIn("function amazonIntakePainPointsText(data)", self.source)

        match = re.search(
            r"function amazonIntakePainPointsText\(data\) \{(?P<body>.*?)\n        \}\n\n        function renderAmazonIntakeResult",
            self.source,
            re.S,
        )
        self.assertIsNotNone(match)
        body = match.group("body")

        self.assertIn("data.review_insights", body)
        self.assertIn("amazonLocalizedLabel('reviewInsightPack')", body)
        self.assertIn("amazonLocalizedLabel('painPoints')", body)
        self.assertIn("insights.pain_points", body)
        self.assertIn("amazonLocalizedLabel('buyerObjections')", body)
        self.assertIn("insights.buyer_objections", body)
        self.assertIn("amazonLocalizedLabel('useCases')", body)
        self.assertIn("insights.use_cases", body)
        self.assertIn("amazonLocalizedLabel('emotionalTriggers')", body)
        self.assertIn("insights.emotional_triggers", body)
        self.assertIn("amazonLocalizedLabel('evidenceQuotes')", body)
        self.assertIn("insights.evidence_quotes", body)
        self.assertIn("amazonLocalizedLabel('capturedReviewSnippets')", body)
        self.assertIn("data.review_items", body)
        self.assertIn("amazonLocalizedLabel('evidencePreview')", body)
        self.assertIn("data.evidence_preview", body)
        self.assertIn("String.fromCharCode(10)", body)

        apply_match = re.search(
            r"function applyAmazonIntakeToDescriptionForm\(\) \{(?P<body>.*?)\n        \}\n\n        async function generateFromAmazonIntake",
            self.source,
            re.S,
        )
        self.assertIsNotNone(apply_match)
        apply_body = apply_match.group("body")
        self.assertIn("amazonIntakePainPointsText(data)", apply_body)
        self.assertIn("painInput.value = painPoints", apply_body)

        generate_match = re.search(
            r"async function generateFromAmazonIntake\(\) \{(?P<body>.*?)\n        \}\n\n        async function runSourceProbe",
            self.source,
            re.S,
        )
        self.assertIsNotNone(generate_match)
        generate_body = generate_match.group("body")
        self.assertIn("applyAmazonIntakeToDescriptionForm()", generate_body)
        self.assertIn("await generateFromDescription()", generate_body)

    def test_l29b_amazon_review_insight_pack_follows_language_mode(self):
        self.assertIn("function amazonLocalizedLabel(key)", self.source)
        self.assertIn("function amazonLocalizedBoolean(value)", self.source)
        self.assertIn("currentOutputLanguage() === 'zh-CN'", self.source)
        self.assertIn("Amazon \\u4fe1\\u53f7\\u9884\\u89c8", self.source)
        self.assertIn("\\u8bc4\\u8bba\\u6d1e\\u5bdf\\u5305", self.source)
        self.assertIn("\\u5df2\\u6355\\u83b7\\u8bc4\\u8bba\\u7247\\u6bb5", self.source)
        self.assertIn("\\u8d2d\\u4e70\\u987e\\u8651", self.source)
        self.assertIn("\\u4f7f\\u7528\\u573a\\u666f", self.source)
        self.assertIn("\\u60c5\\u7eea\\u89e6\\u53d1\\u70b9", self.source)
        self.assertIn("\\u8bc1\\u636e\\u539f\\u6587", self.source)

        self.assertIn("amazonLocalizedLabel('amazonIntakePreview')", self.source)
        self.assertIn("amazonLocalizedLabel('sourceConfidence')", self.source)
        self.assertIn("amazonLocalizedLabel('capturedReviewSnippets')", self.source)
        self.assertIn("amazonLocalizedLabel('reviewInsightPack')", self.source)
        self.assertIn("amazonLocalizedLabel('painPoints')", self.source)
        self.assertIn("amazonLocalizedLabel('buyerObjections')", self.source)
        self.assertIn("amazonLocalizedLabel('emotionalTriggers')", self.source)

        self.assertNotIn("/api/v1/translate-amazon-intake", self.source)
        self.assertNotIn("/api/v1/amazon-i18n", self.source)
        review_body = re.search(
            r"function amazonReviewInsightsText\(insights\) \{(?P<body>.*?)\n        \}\n\n        function amazonIntakePainPointsText",
            self.source,
            re.S,
        )
        self.assertIsNotNone(review_body)
        self.assertIn("String.fromCharCode(10)", review_body.group("body"))
        self.assertNotIn("`${label}:\\n", review_body.group("body"))

        render_body = re.search(
            r"function renderAmazonIntakeResult\(payload\) \{(?P<body>.*?)\n        \}\n\n        async function runAmazonIntake",
            self.source,
            re.S,
        )
        self.assertIsNotNone(render_body)
        self.assertIn("String.fromCharCode(10)", render_body.group("body"))
        self.assertIn("join(newline)", render_body.group("body"))

        set_language_body = re.search(
            r"function setLanguageMode\(language\) \{(?P<body>.*?)\n        \}\n\n        function resetSectionTranslations",
            self.source,
            re.S,
        )
        self.assertIsNotNone(set_language_body)
        set_language_body_text = set_language_body.group("body")
        self.assertIn("latestAmazonIntakeData", set_language_body_text)
        self.assertIn("renderAmazonIntakeResult({ data: latestAmazonIntakeData })", set_language_body_text)
        self.assertIn("amazonIntakeUnavailable", set_language_body_text)
        self.assertIn("amazonIntakeReady", set_language_body_text)


    def test_l29_amazon_review_insight_pack_is_rendered_and_used_without_new_backend(self):
        self.assertIn("review_insights", self.source)
        self.assertIn("Review Insight Pack", self.source)
        self.assertIn("function amazonReviewInsightsText(insights)", self.source)
        self.assertIn("amazonReviewInsightsText(data.review_insights)", self.source)
        self.assertIn("insights.pain_points", self.source)
        self.assertIn("insights.buyer_objections", self.source)
        self.assertIn("insights.emotional_triggers", self.source)
        self.assertIn("insights.evidence_quotes", self.source)

        match = re.search(
            r"function amazonIntakePainPointsText\(data\) \{(?P<body>.*?)\n        \}",
            self.source,
            re.S,
        )
        self.assertIsNotNone(match)
        body = match.group("body")

        self.assertIn("data.review_insights", body)
        self.assertIn("insights.pain_points", body)
        self.assertIn("insights.buyer_objections", body)
        self.assertIn("insights.emotional_triggers", body)
        self.assertIn("data.review_items", body)

        self.assertNotIn("/api/v1/review-insights", self.source)
        self.assertNotIn("/api/v1/amazon-insights", self.source)

    def test_l28_amazon_review_signal_pack_is_rendered_without_new_backend(self):
        self.assertIn("review_items", self.source)
        self.assertIn("Captured Review Snippets", self.source)
        self.assertIn("(data.review_items || [])", self.source)
        self.assertIn("function amazonIntakePainPointsText(data)", self.source)

        match = re.search(
            r"function amazonIntakePainPointsText\(data\) \{(?P<body>.*?)\n        \}",
            self.source,
            re.S,
        )
        self.assertIsNotNone(match)
        body = match.group("body")

        self.assertIn("reviewItemText", body)
        self.assertIn("data.review_items", body)
        self.assertIn("data.evidence_preview", body)

        self.assertNotIn("/api/v1/amazon-reviews", self.source)
        self.assertNotIn("/api/v1/review-capture", self.source)
        self.assertNotIn("debug-source-probe", body)
        self.assertNotIn("amazonShadowMode", body)

    def test_l27_amazon_fallback_routes_to_customer_feedback_without_new_backend(self):
        self.assertIn('id="amazonIntakeFallbackBtn"', self.source)
        self.assertIn('data-i18n="amazonIntakeFallbackBtn"', self.source)
        self.assertIn("function useAmazonFallbackReviews()", self.source)
        self.assertIn("scrollToPastedReviewsMode();", self.source)
        self.assertIn("setReviewsStatus(t('amazonFallbackReviewsReady'), 'success')", self.source)
        self.assertIn("amazonFallbackOpenedReviews", self.source)
        self.assertIn("reviewsPastedReviews", self.source)
        self.assertIn("fallbackBtn.hidden = canUseAmazonSignals;", self.source)

        match = re.search(
            r"function useAmazonFallbackReviews\(\) \{(?P<body>.*?)\n        \}",
            self.source,
            re.S,
        )
        self.assertIsNotNone(match)
        body = match.group("body")

        self.assertIn("reviewsProductName", body)
        self.assertIn("reviewsProductCategory", body)
        self.assertIn("reviewsProductDescription", body)
        self.assertIn("reviewsPastedReviews", body)
        self.assertIn("updateReviewInputPreviews();", body)
        self.assertIn("scrollToPastedReviewsMode();", body)

        self.assertNotIn("fetch(", body)
        self.assertNotIn("postAmazonIntake", body)
        self.assertNotIn("postPastedReviews", body)
        self.assertNotIn("postProductDescription", body)
        self.assertNotIn("generateFromReviews()", body)
        self.assertNotIn("generateFromDescription()", body)
        self.assertNotIn("debug-source-probe", body)
        self.assertNotIn("debug-copilot", body)
        self.assertNotIn("amazonShadowMode", body)
        self.assertNotIn("saveCurrentGenerationToRecent", body)
    def test_source_probe_is_guarded_by_debug_mode(self):
        self.assertIn("postCopilot('debug-source-probe'", self.source)
        self.assertIn("async function runSourceProbe()", self.source)
        self.assertIn("if (!document.getElementById('debugMode').checked) return;", self.source)
        self.assertIn("document.getElementById('debugTraceSection').hidden = !enabled;", self.source)
        self.assertIn("document.getElementById('sourceProbeTools').hidden = !enabled;", self.source)
        self.assertIn("document.getElementById('amazonShadowOption').hidden = !enabled;", self.source)
        self.assertIn("document.getElementById('amazonShadowMode').checked = false;", self.source)

    def test_debug_trace_is_hidden_when_debug_mode_is_off(self):
        self.assertIn('id="debugTraceSection" hidden', self.source)
        self.assertIn('id="debugMode" onchange="syncDebugMode()"', self.source)
        self.assertIn('class="advanced-debug" id="debugTraceSection" hidden', self.source)
        self.assertIn("Debug Mode Advanced Section", self.source)
        self.assertIn("function clearDebugPanel()", self.source)
        self.assertIn("clearDebugPanel();", self.source)
        self.assertNotIn("renderDebugPanel(response.data.feedback, null, 'Off')", self.source)

    def test_amazon_probe_metadata_fields_are_rendered(self):
        self.assertIn("function renderAmazonProbeMetadata(result)", self.source)
        self.assertIn("amazon_review_api", self.source)
        self.assertIn("Amazon Product Title", self.source)
        self.assertIn("Amazon Rating", self.source)
        self.assertIn("Amazon Review Count", self.source)
        self.assertIn("Amazon Price", self.source)
        self.assertIn("Amazon Category Hint", self.source)
        self.assertIn("Amazon Bullet Points", self.source)
        self.assertIn("Amazon Data Warnings", self.source)
        self.assertIn("Amazon Adapter Error", self.source)

    def test_amazon_shadow_summary_fields_are_rendered(self):
        self.assertIn("function renderAmazonShadowSummary(shadowSources)", self.source)
        self.assertIn("real_source_mode = 'amazon_shadow'", self.source)
        self.assertIn("Shadow Provider Status", self.source)
        self.assertIn("Shadow Source Confidence", self.source)
        self.assertIn("Shadow Product Title", self.source)
        self.assertIn("Shadow Rating", self.source)
        self.assertIn("Shadow Review Count", self.source)
        self.assertIn("Shadow Evidence Preview Count", self.source)
        self.assertIn("Shadow Bullet Points Count", self.source)
        self.assertIn("Shadow Category Hint", self.source)
        self.assertIn("Shadow Latency Ms", self.source)
        self.assertIn("Shadow Error Type", self.source)
        self.assertIn("Shadow Retry Count", self.source)
        self.assertIn("Shadow Memory Write Allowed", self.source)
        self.assertIn("Shadow Used For Generation", self.source)


    def test_l18_simplified_active_workspace_flow_hides_legacy_guides(self):
        self.assertIn("/* L18.2-A simplified active workspace flow */", self.source)
        self.assertIn(".hero > #stableProductWorkspace", self.source)
        self.assertIn("#activeWorkspacePanel #quickStartPanel", self.source)
        self.assertIn("#activeWorkspacePanel #chineseOnboardingPanel", self.source)
        self.assertIn("#activeWorkspacePanel #sampleProductLibraryGuide", self.source)
        self.assertIn("#activeWorkspacePanel #firstRunGuidePanel", self.source)
        self.assertIn("#activeWorkspacePanel .demo-warning", self.source)
        self.assertIn("#activeWorkspacePanel .run-options", self.source)

        self.assertIn('data-i18n="navTagline"', self.source)
        self.assertIn("navTagline: 'Evidence Driven Agent'", self.source)
        self.assertIn("navTagline: '基于证据的创意助手'", self.source)


    def test_l18_inline_result_experience_is_polished(self):
        self.assertIn("/* L18.3-A inline result experience polish */", self.source)
        self.assertIn("#inlineResultContent .result-hook-highlight-card", self.source)
        self.assertIn("#inlineResultContent .copy-toolbar", self.source)
        self.assertIn("inlineResultPanelTitle: '你的生成结果'", self.source)
        self.assertIn("inlineResultEmptyState: '点击生成后，Hook、分镜脚本和复制按钮会直接出现在这里，不用滑到页面底部找结果。'", self.source)
        self.assertIn("inlineResultPanelTitle: 'Your generated brief'", self.source)


    def test_l18_chinese_residual_visible_copy_is_localized(self):
        self.assertIn('data-i18n="debugModeLabel"', self.source)
        self.assertIn('data-i18n="amazonShadowLabel"', self.source)
        self.assertIn('data-i18n="exampleGalleryIntro"', self.source)
        self.assertIn('data-i18n="exampleGallerySourceBadge"', self.source)
        self.assertIn('data-i18n="samplePainPointsLabel"', self.source)
        self.assertIn('data-i18n="sampleHookLabel"', self.source)
        self.assertIn('data-i18n="sampleStoryboardLabel"', self.source)
        self.assertIn('data-i18n="goodReviewInputHesitation"', self.source)

        self.assertIn("debugModeLabel: '调试模式'", self.source)
        self.assertIn("amazonShadowLabel: 'Amazon 影子模式'", self.source)
        self.assertIn("exampleGallerySourceBadge: '静态示例，不调用 API'", self.source)
        self.assertIn("samplePainPointsLabel: '痛点'", self.source)
        self.assertIn("sampleStoryboardLabel: '分镜'", self.source)
        self.assertIn("goodReviewInputHesitation: '用户犹豫购买的原因'", self.source)

        zh_start = self.source.find("'zh-CN': {")
        self.assertNotEqual(zh_start, -1)
        zh_end = self.source.find("\n        };\n\n        function t", zh_start)
        self.assertNotEqual(zh_end, -1)
        zh_copy = self.source[zh_start:zh_end]

        self.assertNotIn("Static examples, no API call", zh_copy)
        self.assertNotIn("reasons people hesitate to buy", zh_copy)
        self.assertNotIn("Debug Mode',", zh_copy)
        self.assertNotIn("Amazon Shadow',", zh_copy)


    def test_l18_workspace_inputs_are_simplified_and_user_question_oriented(self):
        self.assertIn("/* L18.5-A simplify workspace inputs */", self.source)
        self.assertIn("advanced-input-field", self.source)
        self.assertIn("#activeWorkspacePanel .advanced-input-field", self.source)

        self.assertIn("productDescriptionMode: '填写你的产品想法'", self.source)
        self.assertIn("pastedReviewsMode: '粘贴用户反馈'", self.source)
        self.assertIn("productName: '产品是什么？'", self.source)
        self.assertIn("productDescription: '用普通话描述这个产品'", self.source)
        self.assertIn("customerPainPoints: '用户遇到什么问题？'", self.source)
        self.assertIn("pastedReviews: '粘贴用户原话 / 评论'", self.source)
        self.assertIn("generateFromDescription: '生成 TikTok 创意'", self.source)
        self.assertIn("generateFromReviews: '根据用户反馈生成创意'", self.source)

        self.assertIn("productDescriptionMode: 'Describe your product idea'", self.source)
        self.assertIn("pastedReviewsMode: 'Use customer feedback'", self.source)


    def test_recent_empty_state_uses_i18n_runtime_copy(self):
        self.assertIn("recentEmptyState: '还没有最近生成记录。'", self.source)
        self.assertIn("clearRecentGenerations: '清空最近生成记录'", self.source)
        self.assertIn("t('recentEmptyState')", self.source)
        self.assertIn("recent-empty", self.source)

        # English fallback can exist in the English dictionary, but the rendered recent-empty state must not be hard-coded.
        self.assertNotIn('<div class="recent-empty">No recent generations yet.</div>', self.source)


    def test_l18_recent_actions_and_language_label_update_in_chinese_mode(self):
        self.assertIn("/* L18.6-A localized recent actions and language label polish */", self.source)
        self.assertIn('.language-selector [data-i18n="languageLabel"]', self.source)
        self.assertIn("languageLabel: '语言：'", self.source)

        self.assertIn("recentView: '查看'", self.source)
        self.assertIn("recentCopyMarkdown: '复制 Markdown'", self.source)
        self.assertIn("recentDelete: '删除'", self.source)

        self.assertIn('data-i18n="recentView"', self.source)
        self.assertIn('data-i18n="recentCopyMarkdown"', self.source)
        self.assertIn('data-i18n="recentDelete"', self.source)

        set_language_start = self.source.find("function setLanguageMode")
        self.assertNotEqual(set_language_start, -1)
        set_language_block = self.source[set_language_start:set_language_start + 700]
        self.assertIn("renderRecentGenerations();", set_language_block)

        zh_start = self.source.find("'zh-CN': {")
        self.assertNotEqual(zh_start, -1)
        zh_end = self.source.find("\n        };\n\n        function t", zh_start)
        self.assertNotEqual(zh_end, -1)
        zh_copy = self.source[zh_start:zh_end]

        self.assertNotIn("languageLabel: 'Language:'", zh_copy)
        self.assertNotIn("recentView: 'View'", zh_copy)
        self.assertNotIn("recentDelete: 'Delete'", zh_copy)


    def test_l19_publish_ready_result_pack_is_present(self):
        self.assertIn("/* L19-A publish-ready result pack */", self.source)
        self.assertIn("function renderQuickUsePack(script, storyboard, data = null)", self.source)
        self.assertIn("renderQuickUsePack(script, storyboard, data)", self.source)
        self.assertIn('id="quickUsePackCard"', self.source)

        self.assertIn("quickUsePackTitle: '下一步可以直接这样用'", self.source)
        self.assertIn("quickUsePackBody: '先不要继续改页面。", self.source)
        self.assertIn("quickUseStepOne: '复制 Hook，当作视频开头第一句话。'", self.source)
        self.assertIn("quickUseStepTwo: '把分镜当作拍摄清单，一条一条拍。'", self.source)
        self.assertIn("quickUseStepThree: '保留最后的 CTA，只替换成你的产品链接或购买方式。'", self.source)
        self.assertIn("copyReadyScript: '可直接复制的短视频脚本'", self.source)

        self.assertIn("quickUsePackTitle: 'Use this result next'", self.source)
        self.assertIn("copyReadyScript: 'Copy-ready short video script'", self.source)


    def test_l19_copy_ready_script_action_is_present(self):
        self.assertIn("/* L19-B copy-ready script action */", self.source)
        self.assertIn("let latestQuickUseScript = '';", self.source)
        self.assertIn("latestQuickUseScript = copyReady;", self.source)
        self.assertIn("function copyQuickUseScript()", self.source)
        self.assertIn('data-i18n="copyReadyScriptButton"', self.source)
        self.assertIn("copyReadyScriptButton: '复制短视频脚本'", self.source)
        self.assertIn("copyReadyScriptCopied: '短视频脚本已复制。'", self.source)
        self.assertIn("copyReadyScriptButton: 'Copy short video script'", self.source)


    def test_l19_script_pack_includes_shot_list_and_caption(self):
        self.assertIn("/* L19-D script, shot list, and caption pack */", self.source)
        self.assertIn("const shotList = scenes.length ? scenes.join", self.source)
        self.assertIn("const captionDraft = [hook, cta].filter(Boolean).join(' ')", self.source)
        self.assertIn("quick-use-mini-grid", self.source)

        self.assertIn("shotListTitle: '拍摄清单'", self.source)
        self.assertIn("captionTitle: '发布文案草稿'", self.source)
        self.assertIn("captionTemplate: '可以直接当作发布文案", self.source)
        self.assertIn("shotListFallback: '把每个分镜当成一个镜头来拍。'", self.source)

        self.assertIn("shotListTitle: 'Shot list'", self.source)
        self.assertIn("captionTitle: 'Caption draft'", self.source)


    def test_l19_sample_inputs_are_language_scoped(self):
        self.assertIn("// L19-F language-scoped sample input profiles", self.source)
        self.assertIn("function sampleInputProfile()", self.source)
        self.assertIn("function maybeRefreshSampleInputsForLanguage()", self.source)
        self.assertIn("maybeRefreshSampleInputsForLanguage();", self.source)

        self.assertIn("descriptionProductNamePlaceholder: 'SoftGlow Desk Lamp'", self.source)
        self.assertIn("reviewsProductNamePlaceholder: 'Portable mini blender'", self.source)
        self.assertIn("reviewsPastedReviewsPlaceholder: '- I hate cleaning my big blender every morning.", self.source)

        self.assertIn("descriptionProductNamePlaceholder: '柔光桌面台灯'", self.source)
        self.assertIn("reviewsProductNamePlaceholder: '便携迷你搅拌机'", self.source)
        self.assertIn("reviewsPastedReviewsPlaceholder: '- 我讨厌每天早上清洗大搅拌机。", self.source)

        self.assertIn("applyProductDescriptionSample(sampleInputProfile().productDescription)", self.source)
        self.assertIn("applyReviewSample(sampleInputProfile().miniBlender)", self.source)
        self.assertIn("applyReviewSample(sampleInputProfile().petHair)", self.source)
        self.assertIn("applyReviewSample(sampleInputProfile().deskLamp)", self.source)


    def test_l19_english_and_chinese_sample_copy_are_separated(self):
        en_start = self.source.find("en: {")
        self.assertNotEqual(en_start, -1)
        en_end = self.source.find("\n            },\n            'zh-CN': {", en_start)
        self.assertNotEqual(en_end, -1)
        en_copy = self.source[en_start:en_end]

        zh_start = self.source.find("'zh-CN': {")
        self.assertNotEqual(zh_start, -1)
        zh_end = self.source.find("\n        };\n\n        function t", zh_start)
        self.assertNotEqual(zh_end, -1)
        zh_copy = self.source[zh_start:zh_end]

        self.assertIn("descriptionProductNamePlaceholder: 'SoftGlow Desk Lamp'", en_copy)
        self.assertIn("reviewsProductNamePlaceholder: 'Portable mini blender'", en_copy)
        self.assertIn("reviewsPastedReviewsPlaceholder: '- I hate cleaning my big blender every morning.", en_copy)

        self.assertIn("descriptionProductNamePlaceholder: '柔光桌面台灯'", zh_copy)
        self.assertIn("reviewsProductNamePlaceholder: '便携迷你搅拌机'", zh_copy)
        self.assertIn("reviewsPastedReviewsPlaceholder: '- 我讨厌每天早上清洗大搅拌机。", zh_copy)

        self.assertNotIn("柔光桌面台灯", en_copy)
        self.assertNotIn("便携迷你搅拌机", en_copy)
        self.assertNotIn("Portable mini blender", zh_copy)
        self.assertNotIn("I hate cleaning my big blender", zh_copy)


    def test_l19_sample_copy_has_no_garbled_question_marks(self):
        self.assertNotIn("????", self.source)
        self.assertIn("/* L19-G localized sample card labels and garbled sample fix */", self.source)
        self.assertIn('data-i18n="exampleSlugBalsamic"', self.source)
        self.assertIn('data-i18n="exampleSlugPetHair"', self.source)
        self.assertIn('data-i18n="exampleSlugDeskLamp"', self.source)
        self.assertIn("exampleSlugBalsamic: '香醋'", self.source)
        self.assertIn("exampleSlugPetHair: '宠物毛发清理'", self.source)
        self.assertIn("exampleSlugDeskLamp: '台灯'", self.source)


    def test_l19_sample_product_workspace_slug_labels_are_language_scoped(self):
        self.assertIn("/* L19-H localized slug display for sample product workspace */", self.source)
        self.assertIn("const LOCALIZED_DEMO_SLUG_KEYS", self.source)
        self.assertIn("function normalizeDemoSlug(value)", self.source)
        self.assertIn("function displayDemoSlug(slug)", self.source)
        self.assertIn("function refreshDemoSlugDisplayForLanguage()", self.source)
        self.assertIn("refreshDemoSlugDisplayForLanguage();", self.source)

        self.assertIn('data-i18n="stableSlugDeskLamp"', self.source)
        self.assertIn('data-i18n="exampleSlugDeskLamp"', self.source)
        self.assertIn('data-i18n="samplePainPointsLabel"', self.source)
        self.assertIn('data-i18n="sampleHookLabel"', self.source)
        self.assertIn('data-i18n="sampleStoryboardLabel"', self.source)

        self.assertIn("stableSlugDeskLamp: 'desk_lamp'", self.source)
        self.assertIn("stableSlugDeskLamp: '台灯'", self.source)
        self.assertIn("exampleSlugBalsamic: '香醋'", self.source)
        self.assertIn("exampleSlugPetHair: '宠物毛发清理'", self.source)
        self.assertIn("exampleSlugDeskLamp: '台灯'", self.source)

        self.assertNotIn("香醋 / balsamic_vinegar", self.source)
        self.assertNotIn("台灯 / desk_lamp", self.source)


    def test_l19_example_gallery_copy_is_language_scoped(self):
        self.assertIn("/* L19-I language-scoped example gallery copy */", self.source)

        for key in [
            "exampleBalsamicPain",
            "exampleBalsamicHook",
            "exampleBalsamicStoryboard",
            "examplePetHairPain",
            "examplePetHairHook",
            "examplePetHairStoryboard",
            "exampleDeskLampPain",
            "exampleDeskLampHook",
            "exampleDeskLampStoryboard",
        ]:
            self.assertIn(f'data-i18n="{key}"', self.source)

        self.assertIn("exampleBalsamicPain: 'Cracked cap, leaking bottle, thin taste'", self.source)
        self.assertIn("exampleBalsamicPain: '瓶盖破裂、泄漏、口感稀薄'", self.source)
        self.assertIn("examplePetHairPain: 'Pet hair sticks, weak suction, repeated cleanup'", self.source)
        self.assertIn("examplePetHairPain: '宠物毛清不干净、吸力不够、反复清理'", self.source)
        self.assertIn("exampleDeskLampPain: 'Eye strain, desk clutter, late-night work fatigue'", self.source)
        self.assertIn("exampleDeskLampPain: '光线刺眼、桌面杂乱、夜间工作疲劳'", self.source)


    def test_l19_sample_workspace_copy_is_strictly_language_scoped(self):
        self.assertIn("/* L19-J strict sample workspace language scope */", self.source)
        self.assertIn("const SAMPLE_WORKSPACE_COPY", self.source)
        self.assertIn("function sampleWorkspaceSlugFromValue(value)", self.source)
        self.assertIn("function sampleWorkspaceDisplaySlug(slug)", self.source)
        self.assertIn("function refreshSampleWorkspaceCopyForLanguage()", self.source)
        self.assertIn("setTimeout(refreshSampleWorkspaceCopyForLanguage, 0);", self.source)

        self.assertIn("document.getElementById('urlInput').value = sampleWorkspaceDisplaySlug(slug);", self.source)
        self.assertIn("const urlInput = sampleWorkspaceSlugFromValue(document.getElementById('urlInput').value.trim());", self.source)

        self.assertIn('"exampleHookLabel": "Hook"', self.source)
        self.assertIn('"exampleHookLabel": "开头"', self.source)
        self.assertIn('"exampleBalsamicPain": "Cracked cap, leaking bottle, thin taste"', self.source)
        self.assertIn('"exampleBalsamicPain": "瓶盖破裂、泄漏、口感稀薄"', self.source)
        self.assertIn('"balsamic_vinegar": "balsamic_vinegar"', self.source)
        self.assertIn('"balsamic_vinegar": "香醋"', self.source)




    def test_l20_sample_workspace_has_explicit_language_isolation_contract(self):
        self.assertIn("const SAMPLE_WORKSPACE_COPY", self.source)
        self.assertIn("function refreshSampleWorkspaceCopyForLanguage()", self.source)

        en_start = self.source.find('"en": {')
        self.assertNotEqual(en_start, -1)
        zh_start = self.source.find('"zh-CN": {', en_start)
        self.assertNotEqual(zh_start, -1)

        en_copy = self.source[en_start:zh_start]
        zh_end = self.source.find("        };", zh_start)
        self.assertNotEqual(zh_end, -1)
        zh_copy = self.source[zh_start:zh_end]

        zh_balsamic = "\u9999\u918b"
        zh_pet_hair = "\u5ba0\u7269\u6bdb\u53d1\u6e05\u7406"
        zh_desk_lamp = "\u53f0\u706f"
        zh_pain = "\u75db\u70b9"
        zh_hook = "\u5f00\u5934"
        zh_storyboard = "\u5206\u955c"

        self.assertIn('"balsamic_vinegar": "balsamic_vinegar"', en_copy)
        self.assertIn('"pet_hair_vacuum": "pet_hair_vacuum"', en_copy)
        self.assertIn('"desk_lamp": "desk_lamp"', en_copy)
        self.assertIn('"examplePainPointsLabel": "Pain points"', en_copy)
        self.assertIn('"exampleHookLabel": "Hook"', en_copy)
        self.assertIn('"exampleStoryboardLabel": "Storyboard"', en_copy)

        self.assertIn(f'"balsamic_vinegar": "{zh_balsamic}"', zh_copy)
        self.assertIn(f'"pet_hair_vacuum": "{zh_pet_hair}"', zh_copy)
        self.assertIn(f'"desk_lamp": "{zh_desk_lamp}"', zh_copy)
        self.assertIn(f'"examplePainPointsLabel": "{zh_pain}"', zh_copy)
        self.assertIn(f'"exampleHookLabel": "{zh_hook}"', zh_copy)
        self.assertIn(f'"exampleStoryboardLabel": "{zh_storyboard}"', zh_copy)

        self.assertNotIn(f'"balsamic_vinegar": "{zh_balsamic}"', en_copy)
        self.assertNotIn(f'"examplePainPointsLabel": "{zh_pain}"', en_copy)
        self.assertNotIn('"balsamic_vinegar": "balsamic_vinegar"', zh_copy)
        self.assertNotIn('"examplePainPointsLabel": "Pain points"', zh_copy)

        self.assertIn("const urlInput = sampleWorkspaceSlugFromValue(document.getElementById('urlInput').value.trim());", self.source)
        self.assertIn("const payload = { url: urlInput, goal: 'tiktok_ctr', output_language: currentOutputLanguage() };", self.source)


    def test_l20_chinese_entry_copy_avoids_english_slug_jargon(self):
        self.assertIn("/* L20-B localized non-technical Chinese entry copy */", self.source)

        zh_start = self.source.find("'zh-CN': {")
        self.assertNotEqual(zh_start, -1)
        zh_end = self.source.find("\n        };\n\n        function t", zh_start)
        self.assertNotEqual(zh_end, -1)
        zh_copy = self.source[zh_start:zh_end]

        self.assertIn("heroSubtitle: '这个公开 Demo 提供 10 个本地示例产品。建议先试“香醋”或“台灯”。'", zh_copy)
        self.assertIn("urlInputPlaceholder: '选择一个示例产品，例如：台灯'", zh_copy)
        self.assertIn("pathSampleProductBody: '不用填写内容，先用香醋、台灯或宠物毛发清理这类示例产品，看完整生成流程。'", zh_copy)
        self.assertIn("sampleProductLibraryBody: '这些只是用来试流程的示例产品，不需要把它理解成“数据集”。'", zh_copy)

        self.assertNotIn("balsamic_vinegar", zh_copy)
        self.assertNotIn("desk_lamp", zh_copy)
        self.assertNotIn("stable local grounded slug", zh_copy)
        self.assertNotIn("dataset", zh_copy)

        en_start = self.source.find("en: {")
        self.assertNotEqual(en_start, -1)
        en_end = self.source.find("\n            },\n            'zh-CN': {", en_start)
        self.assertNotEqual(en_end, -1)
        en_copy = self.source[en_start:en_end]

        self.assertIn("balsamic_vinegar", en_copy)
        self.assertIn("desk_lamp", en_copy)
        self.assertIn("stable local grounded slug", en_copy)


    def test_l21_primary_workflow_entry_has_clear_visual_hierarchy(self):
        self.assertIn("/* L21-A primary workflow entry hierarchy */", self.source)
        self.assertIn("#pathSelectorPanel .path-selector-shell", self.source)
        self.assertIn("#pathSelectorPanel .path-card-grid", self.source)
        self.assertIn("#pathSelectorPanel .path-card.active", self.source)
        self.assertIn("#pathSelectorPanel .path-card:hover", self.source)
        self.assertIn("#pathSelectorPanel .path-card::before", self.source)
        self.assertIn('#pathAmazonProductCard::before { content: "1"; }', self.source)
        self.assertIn('#pathProductIdeaCard::before { content: "2"; }', self.source)
        self.assertIn('#pathCustomerFeedbackCard::before { content: "3"; }', self.source)
        self.assertIn('#pathSampleProductCard::before { content: "4"; }', self.source)
        self.assertIn("#pathSelectorPanel .path-card-title", self.source)
        self.assertIn("#pathSelectorPanel .path-card-subtitle", self.source)


    def test_l21_result_area_prioritizes_hook_and_copy_ready_script(self):
        self.assertIn("/* L21-B result-first content hierarchy */", self.source)
        self.assertIn("#inlineResultContent .result-hook-highlight-card", self.source)
        self.assertIn("#inlineResultContent .result-hook-highlight-text", self.source)
        self.assertIn("#inlineResultContent .quick-use-pack-card", self.source)
        self.assertIn("#inlineResultContent .quick-use-script", self.source)
        self.assertIn("#inlineResultContent .copy-toolbar", self.source)
        self.assertIn("#inlineResultContent .section-actions", self.source)
        self.assertIn("#inlineResultContent .evidence-source-card", self.source)
        self.assertIn("#inlineResultContent .metric-strip", self.source)
        self.assertIn("#inlineResultContent pre.debug", self.source)
        self.assertIn("opacity: 0.72;", self.source)
        self.assertIn("#inlineResultContent .evidence-source-card:hover", self.source)


    def test_l21_technical_diagnostics_are_secondary_to_user_flow(self):
        self.assertIn("/* L21-C keep technical diagnostics secondary */", self.source)
        self.assertIn(".agent-track", self.source)
        self.assertIn(".agent-track:hover", self.source)
        self.assertIn(".agent-badge", self.source)
        self.assertIn(".advanced-debug", self.source)
        self.assertIn(".advanced-debug:hover", self.source)
        self.assertIn(".probe-tools", self.source)
        self.assertIn(".probe-tools:hover", self.source)
        self.assertIn("pre.debug", self.source)
        self.assertIn(".metric-pill", self.source)
        self.assertIn(".evidence-source-card", self.source)
        self.assertIn(".demo-warning,", self.source)
        self.assertIn(".run-options", self.source)
        self.assertIn("opacity: 0.72;", self.source)
        self.assertIn("max-height: 260px;", self.source)


    def test_l21_copy_actions_are_the_next_obvious_step(self):
        self.assertIn("/* L21-D make copy actions the next obvious step */", self.source)
        self.assertIn("#inlineResultContent .copy-toolbar", self.source)
        self.assertIn("#inlineResultContent .section-actions", self.source)
        self.assertIn("#inlineResultContent .copy-toolbar::before", self.source)
        self.assertIn("#inlineResultContent .section-actions::before", self.source)
        self.assertIn('content: "Next: copy what you need";', self.source)
        self.assertIn("body.zh-mode #inlineResultContent .copy-toolbar::before", self.source)
        self.assertIn('content: "下一步：复制你要用的内容";', self.source)
        self.assertIn("#inlineResultContent .copy-status", self.source)
        self.assertIn("#inlineResultContent .quick-use-copy-status", self.source)
        self.assertIn("border-color: #86efac;", self.source)


    def test_l21_language_mode_body_classes_support_css_copy(self):
        self.assertIn("/* L21-E language mode body class contract */", self.source)
        self.assertIn("// L21-E stable language body classes for CSS-driven copy", self.source)
        self.assertIn("function updateLanguageBodyClass(language)", self.source)
        self.assertIn("document.body.classList.toggle('zh-mode', language === 'zh-CN');", self.source)
        self.assertIn("document.body.classList.toggle('en-mode', language !== 'zh-CN');", self.source)
        self.assertIn("updateLanguageBodyClass(language);", self.source)
        self.assertIn("updateLanguageBodyClass(currentOutputLanguage());", self.source)
        self.assertIn("body.zh-mode #inlineResultContent .copy-toolbar::before", self.source)


    def test_l21_empty_result_state_explains_next_action(self):
        self.assertIn("/* L21-F actionable empty result state */", self.source)
        self.assertIn("#inlineResultEmptyState", self.source)
        self.assertIn("#inlineResultEmptyState::before", self.source)
        self.assertIn("#inlineResultEmptyState::after", self.source)
        self.assertIn('content: "Pick a path above, add a product idea or sample, then generate.";', self.source)
        self.assertIn("body.zh-mode #inlineResultEmptyState::after", self.source)
        self.assertIn('content: "先选择上面的入口，填写产品或选择示例，然后点击生成。";', self.source)
        self.assertIn("border: 1px dashed #93c5fd;", self.source)
        self.assertIn("background: linear-gradient(180deg, #eff6ff 0%, #ffffff 100%);", self.source)


    def test_l22_public_demo_ui_contract_script_exists(self):
        script = Path("scripts/check_public_demo_ui_contract.py").read_text(encoding="utf-8")
        self.assertIn("Public demo UI contract check passed.", script)
        self.assertIn("L21-A workflow entry hierarchy", script)
        self.assertIn("L21-F actionable empty state", script)
        self.assertIn("sample workspace language map", script)
        self.assertIn("garbled question marks", script)
        self.assertIn("mixed balsamic display", script)
        self.assertIn("mixed desk lamp display", script)
        self.assertIn("mixed pet hair display", script)


    def test_l23_public_demo_render_smoke_script_exists(self):
        script = Path("scripts/check_public_demo_render_smoke.py").read_text(encoding="utf-8")
        self.assertIn("Public demo Render smoke check passed.", script)
        self.assertIn("REQUIRED_MARKERS", script)
        self.assertIn("FORBIDDEN_PATTERNS", script)
        self.assertIn("L21-A workflow entry hierarchy", script)
        self.assertIn("sample workspace language map", script)
        self.assertIn("language class helper", script)
        self.assertIn("mixed balsamic display", script)
        self.assertIn("old inline panel fallback", script)
        self.assertIn("render-smoke-", script)


    def test_l23_public_demo_generation_smoke_script_exists(self):
        script = Path("scripts/check_public_demo_generation_smoke.py").read_text(encoding="utf-8")
        self.assertIn("Public demo generation smoke check passed.", script)
        self.assertIn("DEFAULT_ENDPOINT = \"auto\"", script)
        self.assertIn("ENDPOINT_CANDIDATES", script)
        self.assertIn("\"/api/generate-copilot\"", script)
        self.assertIn("\"url\": args.product", script)
        self.assertIn("\"goal\": \"tiktok_ctr\"", script)
        self.assertIn("\"output_language\": args.language", script)
        self.assertIn("failure_type", script)
        self.assertIn("\"hook\"", script)
        self.assertIn("\"storyboard\"", script)
        self.assertIn("--save-json", script)
        self.assertIn("post_json_with_endpoint_discovery", script)


    def test_l23_public_demo_smoke_suite_script_exists(self):
        script = Path("scripts/run_public_demo_smoke_suite.py").read_text(encoding="utf-8")
        self.assertIn("All public demo smoke checks passed.", script)
        self.assertIn("scripts/check_public_demo_ui_contract.py", script)
        self.assertIn("scripts/check_public_demo_render_smoke.py", script)
        self.assertIn("scripts/check_public_demo_generation_smoke.py", script)
        self.assertIn("scripts/check_public_demo_workflow_smoke.py", script)
        self.assertIn("deployed generation smoke EN", script)
        self.assertIn("deployed generation smoke zh-CN", script)
        self.assertIn("deployed workflow smoke EN", script)
        self.assertIn("deployed workflow smoke zh-CN", script)
        self.assertIn("--skip-remote", script)
        self.assertIn("--include-tests", script)
        self.assertIn("--include-workflows", script)
        self.assertIn("--full", script)
        self.assertIn("--save-artifacts", script)

    def test_l23_public_demo_workflow_smoke_script_exists(self):
        script = Path("scripts/check_public_demo_workflow_smoke.py").read_text(encoding="utf-8")
        self.assertIn("All public demo workflow smoke checks passed.", script)
        self.assertIn("\"sample_product\": \"/api/v1/generate-copilot\"", script)
        self.assertIn("\"product_description\": \"/api/v1/generate-from-description\"", script)
        self.assertIn("\"pasted_reviews\": \"/api/v1/generate-from-reviews\"", script)
        self.assertIn("workflow_payloads(language)", script)
        self.assertIn("SoftGlow Desk Lamp", script)
        self.assertIn("Countertop Blender", script)
        self.assertIn("--workflow", script)
        self.assertIn("--save-json", script)


    def test_l24_copy_ready_script_extracts_user_facing_lines(self):
        self.assertIn("// L24-B copy-ready script extraction from structured model output", self.source)
        self.assertIn("function stripStructuredScriptPrefix(text)", self.source)
        self.assertIn("function cleanHookLine(script)", self.source)
        self.assertIn("function cleanCtaLine(script)", self.source)
        self.assertIn("function copyReadyScriptText(data)", self.source)
        self.assertIn("Narration|旁白", self.source)
        self.assertIn("Visual: ${visual}", self.source)
        self.assertIn("画面：${visual}", self.source)
        self.assertIn("Narration: ${narration}", self.source)
        self.assertIn("旁白：${narration}", self.source)
        self.assertIn("const hook = cleanHookLine(script);", self.source)
        self.assertIn("const cta = cleanCtaLine(script);", self.source)
        self.assertIn("const copyReady = copyReadyScriptText(fallbackData);", self.source)
        self.assertIn("latestQuickUseScript = copyReady;", self.source)
        self.assertNotIn("latestQuickUseScript = script.hook", self.source)


    def test_l24_copy_ready_script_contract_script_exists(self):
        script = Path("scripts/check_copy_ready_script_contract.py").read_text(encoding="utf-8")
        self.assertIn("Copy-ready script contract check passed.", script)
        self.assertIn("REQUIRED_MARKERS", script)
        self.assertIn("FORBIDDEN_PATTERNS", script)
        self.assertIn("renderQuickUsePack(script, storyboard, data)", script)
        self.assertIn("${quickUsePackCard}", script)
        self.assertIn("escapeHTML(script.hook || '')", script)
        self.assertIn("latestQuickUseScript = script.hook", script)
        self.assertIn("renderHookHighlightCard should not render raw script.hook", script)



    def test_pasted_review_workspace_analysis_frontend_entry(self):
        for marker in [
            "pastedReviewWorkspaceResult",
            "/api/v1/analyze-pasted-review-workspace",
            "postPastedReviewWorkspaceAnalysis",
            "renderPastedReviewWorkspaceAnalysis",
            "reviewWorkspaceThemeText",
            "pastedReviewWorkspaceTitle",
            "workspaceResponse = await postPastedReviewWorkspaceAnalysis",
        ]:
            self.assertIn(marker, self.source)


    def test_extension_workspace_receiver_overlay_exists(self):
        for marker in [
            "extensionWorkspacePanel",
            "crossgrowth_extension_workspace",
            "extension_workspace=1",
            "crossgrowth-extension-workspace-ready",
            "/api/v1/analyze-review-workspace",
        ]:
            self.assertIn(marker, self.source)

    def test_extension_workspace_can_send_visible_reviews_to_review_workflow(self):
        for marker in [
            "extensionWorkspaceSendToReviews",
            "sendToReviewWorkflow",
            "sendToReviewWorkflowNoReviews",
            "sendToReviewWorkflowWorking",
            "sendToReviewWorkflowReady",
            "sendToReviewWorkflowFailed",
            "function extensionWorkspaceVisibleReviewLines(payload)",
            "function extensionWorkspaceProductDescriptionText(payload)",
            "function fillPastedReviewsFromExtensionWorkspace(payload)",
            "async function sendExtensionWorkspaceToReviewWorkflow()",
            "function setExtensionWorkspaceBridgeStatus(message)",
            "function updateExtensionWorkspaceActionState(payload = readExtensionWorkspacePayload())",
            "document.getElementById(\"reviewsProductName\")",
            "document.getElementById(\"reviewsProductCategory\")",
            "document.getElementById(\"reviewsProductDescription\")",
            "document.getElementById(\"reviewsPastedReviews\")",
            "updateReviewInputPreviews();",
            "scrollToPastedReviewsMode();",
            "const ok = await generateFromReviews();",
        ]:
            self.assertIn(marker, self.source)

        bridge_start = self.source.find("async function sendExtensionWorkspaceToReviewWorkflow()")
        bridge_end = self.source.find("function extensionWorkspaceSampleWarningText", bridge_start)
        self.assertNotEqual(bridge_start, -1)
        self.assertNotEqual(bridge_end, -1)
        bridge_body = self.source[bridge_start:bridge_end]
        self.assertIn("setLanguageMode(language);", bridge_body)
        self.assertIn("setExtensionWorkspaceBridgeStatus(message)", bridge_body)
        self.assertIn("setExtensionWorkspaceBridgeStatus(tExtensionWorkspace(\"sendToReviewWorkflowWorking\", payload))", bridge_body)
        self.assertIn("updateExtensionWorkspaceActionState(null)", bridge_body)
        self.assertIn("updateExtensionWorkspaceActionState(payload)", bridge_body)
        self.assertIn("fillPastedReviewsFromExtensionWorkspace(payload)", bridge_body)
        self.assertIn("generateFromReviews()", bridge_body)
        self.assertNotIn("fetch(", bridge_body)
        self.assertNotIn("/api/v1/generate-from-reviews", bridge_body)
        self.assertNotIn("/api/v1/analyze-review-workspace", bridge_body)
        self.assertNotIn("debug-source-probe", bridge_body)
        self.assertNotIn("amazonShadowMode.checked = true", bridge_body)

    def test_extension_workspace_empty_state_actions_are_clear(self):
        for marker in [
            "No workspace payload found.",
            "analysisComplete",
            "extensionWorkspaceAnalyze",
            "extensionWorkspaceSendToReviews",
            "analyzeButton.disabled = !hasPayload",
            "sendButton.disabled = !hasReviews",
            "amazonButton.disabled = !hasReviews",
            "setExtensionWorkspaceBridgeStatus(message)",
            "output.innerHTML = `<strong>${escapeExtensionHTML(message)}</strong>`;",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.source)

        analyze_start = self.source.find("async function analyzeExtensionWorkspace()")
        analyze_end = self.source.find("function maybeRenderExtensionWorkspace", analyze_start)
        self.assertNotEqual(analyze_start, -1)
        self.assertNotEqual(analyze_end, -1)
        analyze_body = self.source[analyze_start:analyze_end]
        self.assertIn("if (!payload)", analyze_body)
        self.assertIn("setExtensionWorkspaceBridgeStatus(message)", analyze_body)
        self.assertIn("updateExtensionWorkspaceActionState(null)", analyze_body)
        self.assertIn("setExtensionWorkspaceBridgeStatus(tExtensionWorkspace(\"analyzingWorkspace\", payload))", analyze_body)
        self.assertIn("setExtensionWorkspaceBridgeStatus(tExtensionWorkspace(\"analysisComplete\", body))", analyze_body)

    def test_amazon_product_path_guides_extension_visible_review_import(self):
        for marker in [
            "amazonImportPathGuide",
            "amazonImportedWorkspaceStatus",
            "amazonImportedWorkspaceGenerateBtn",
            "amazonImportedWorkspaceStatusText",
            "amazonImportPathTitle",
            "amazonImportPathBody",
            "amazonImportStepOne",
            "amazonImportStepTwo",
            "amazonImportStepThree",
            "amazonImportFallbackNote",
            "amazonImportedWorkspaceReady",
            "Start from a product link or visible page reviews",
            "reviews already visible on the current page",
            "Visible reviews imported by the extension are available. You can generate creative from them.",
            "function hasExtensionWorkspaceVisibleReviews(payload)",
            "function refreshAmazonImportPathStatus()",
            "window.sendExtensionWorkspaceToReviewWorkflow = sendExtensionWorkspaceToReviewWorkflow;",
            "window.refreshAmazonImportPathStatus = refreshAmazonImportPathStatus;",
            "onclick=\"sendExtensionWorkspaceToReviewWorkflow()\"",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.source)

        status_start = self.source.find("function refreshAmazonImportPathStatus()")
        status_end = self.source.find("function summarizeExtensionWorkspace", status_start)
        self.assertNotEqual(status_start, -1)
        self.assertNotEqual(status_end, -1)
        status_body = self.source[status_start:status_end]
        self.assertIn("readExtensionWorkspacePayload()", status_body)
        self.assertIn("hasExtensionWorkspaceVisibleReviews(payload)", status_body)
        self.assertIn("statusPanel.hidden", status_body)
        self.assertNotIn("fetch(", status_body)
        self.assertNotIn("/api/v1/", status_body)

        guide_start = self.source.find('id="amazonImportPathGuide"')
        guide_end = self.source.find('id="amazonImportedWorkspaceStatus"', guide_start)
        self.assertNotEqual(guide_start, -1)
        self.assertNotEqual(guide_end, -1)
        guide_body = self.source[guide_start:guide_end]
        self.assertIn("current page", guide_body)
        self.assertIn("product page or review page", guide_body.lower())
        self.assertNotIn("hidden reviews", guide_body.lower())
        self.assertNotIn("full review", guide_body.lower())


    def test_extension_workspace_displays_sample_metadata(self):
        for marker in [
            "extensionRatingMixText",
            "extensionSourceScopeText",
            "extensionProductSampleMetaHTML",
            "extensionWorkspaceWarningsHTML",
            "${extensionProductSampleMetaHTML(product)}",
            "${extensionWorkspaceWarningsHTML(payload)}",
            "Visible sample only",
            "Rating mix",
            "sample_warning",
            "rating_distribution",
            "source_scope",
        ]:
            self.assertIn(marker, self.source)


    def test_extension_workspace_explains_visible_sample_boundary(self):
        for marker in [
            "extensionWorkspaceBoundaryNote",
            "EXTENSION_WORKSPACE_COPY",
            "workspaceJsonCopied",
            "noPayloadStrong",
            "analyzingWorkspace",
            "signal",
            "tExtensionWorkspace",
            "extensionWorkspaceLanguage",
            "extensionWorkspaceSummaryText",
            "summaryImported",
            "extensionWorkspaceProductMetaText",
            "extensionWorkspaceProductTitle",
            "extensionWorkspaceReviewCount",
            "extensionWorkspaceSampleWarningText",
            "visiblePageSampleSource",
            "copyLabelBrief",
            "copyUnavailable",
            "Product",
            "Source",
            "Reviews used",
            "Sample warning",
            "Visible-page sample only",
            "does not bypass login",
            "CAPTCHA",
            "hidden review pages",
            "creative signals",
            "not full review statistics",
        ]:
            self.assertIn(marker, self.source)


    def test_extension_workspace_renders_evidence_backed_analysis(self):
        for marker in [
            "extensionThemeListHTML",
            "extensionListHTML",
            "evidence_quotes",
            "Buyer objections",
            "Creative angles",
            "extensionThemeListHTML(tExtensionWorkspace(\"topPainPoints\", body), body.common_pain_points, body)",
            "extensionThemeListHTML(tExtensionWorkspace(\"buyerObjectionsSection\", body), body.buyer_objections, body)",
            "extensionListHTML(tExtensionWorkspace(\"creativeAnglesSection\", body), body.creative_angles)",
            "extensionListHTML(tExtensionWorkspace(\"hooksSection\", body), body.hooks)",
        ]:
            self.assertIn(marker, self.source)


    def test_extension_workspace_renders_creative_brief(self):
        for marker in [
            "extensionCreativeBriefHTML",
            "sampleInterpretation",
            "copySampleInterpretation",
            "videoScriptPack",
            "topPainPoints",
            "buyerObjectionsSection",
            "creativeAnglesSection",
            "hooksSection",
            "noSignalsFound",
            "perfect",
            "tExtensionWorkspace(\"topPainPoints\", body)",
            "tExtensionWorkspace(\"buyerObjectionsSection\", body)",
            "tExtensionWorkspace(\"creativeAnglesSection\", body)",
            "tExtensionWorkspace(\"hooksSection\", body)",
            "analysisFailed",
            "unknownError",
            "productsMetric",
            "reviewsMetric",
            "highSignalMetric",
            "tExtensionWorkspace(\"hook\"",
            "copyScriptPack",
            "copyScript15",
            "copyScript30",
            "extensionSampleInterpretationHTML",
            "extensionVideoScriptPackHTML",
            "extensionSampleInterpretationMarkdown",
            "extensionVideoScriptPackMarkdown",
            "extensionWorkspaceCopyPayload",
            "copyLabelSample",
            "copyLabelScriptPack",
            "sample_interpretation",
            "video_script_pack",
            "${extensionSampleInterpretationHTML(body)}",
            "${extensionVideoScriptPackHTML(body)}",
            "Creative brief",
            "Pain -> Evidence -> Copy-ready angle -> TikTok hook",
            "Copy-ready angle",
            "TikTok hook",
            "extensionPositiveProofHTML",
            "extensionCreativeBriefMarkdown",
            "extensionCreativeBriefRowMarkdown",
            "extensionPositiveProofMarkdown",
            "extensionCreativeBriefSignalItems",
            "extensionCreativeBriefSignalLabel",
            "body.buyer_objections",
            "copyExtensionCreativeBrief",
            "extensionCreativeBriefCopyPayload",
            "extensionCreativeBriefCopyStatus",
            "extensionCreativeBriefRowCopyStatus",
            "extensionPositiveProofCopyStatus",
            "data-extension-brief-copy-status",
            "querySelectorAll(\"[data-extension-brief-copy-status]\")",
            "Copy all brief",
            "Copy row",
            "Copy positive proof",
            "Review Workspace Creative Brief",
            "extensionHumanThemeLabel",
            "\\u4ef7\\u683c / \\u4ef7\\u503c\\u987e\\u8651",
            "\\u5473\\u9053 / \\u98ce\\u5473\\u987e\\u8651",
            "\\u89c4\\u683c / \\u6570\\u91cf\\u4e0d\\u4e00\\u81f4",
            "extensionThemeListHTML(tExtensionWorkspace(\"topPainPoints\", body), body.common_pain_points, body)",
            "extensionThemeListHTML(tExtensionWorkspace(\"buyerObjectionsSection\", body), body.buyer_objections, body)",
            "extensionCreativeBriefHook(item, hooks, index, body)",
            "extensionQuoteHasPainSignal",
            "extensionCleanCreativeAngle",
            "Buyers calling it great",
            "Buyers saying they love it",
            "Positive proof",
            "body.liked_points",
            "${extensionCreativeBriefHTML(body)}",
            "body.creative_angles",
            "body.hooks",
            "buyerConcern",
            "\\u8d2d\\u4e70\\u987e\\u8651",
            "positiveSignal",
        ]:
            self.assertIn(marker, self.source)

    def test_extension_creative_brief_falls_back_to_buyer_objections(self):
        for marker in [
            "const briefItems = extensionCreativeBriefSignalItems(body)",
            "const objections = (body.buyer_objections || []).slice(0, 3)",
            "if (objections.length) return objections",
            "briefKind: \"buyer_objection\"",
            "extensionCreativeBriefSignalLabel(item, body)",
            "tExtensionWorkspace(\"buyerConcern\", source)",
            "extensionCreativeBriefRowMarkdown(item, angle, hook, body)",
            "extensionCreativeBriefHook(item, hooks, index, body)",
            "escapeExtensionHTML(quote)",
            "extensionCleanCreativeAngle(angles[index] || angles[0] || \"\")",
            "buyerConcern",
            "\\u8d2d\\u4e70\\u987e\\u8651",
        ]:
            self.assertIn(marker, self.source)


    def test_pasted_review_workspace_source_breakdown_frontend(self):
        for marker in [
            "reviewWorkspaceSourceBreakdownText",
            "reviewWorkspaceAsinContributionText",
            "reviewWorkspaceSourceGroupsText",
            "reviewWorkspaceSourceGuidanceText",
            "analysis.source_breakdown",
            "source_breakdown",
            "raw_review_count",
            "duplicate_review_count",
            "rawReviewCount",
            "duplicateReviewCount",
            "\\u539f\\u59cb\\u53ef\\u89c1\\u8bc4\\u8bba",
            "\\u53bb\\u91cd\\u5206\\u6790\\u8bc4\\u8bba",
            "\\u91cd\\u590d\\u8bc4\\u8bba",
            "main_product_reviews",
            "variant_reviews",
            "low_star_reviews",
            "verified_purchase_reviews",
            "recent_reviews",
            "asin_review_counts",
            "sourceBreakdownTitle",
            "sourceBreakdownGuidance",
        ]:
            self.assertIn(marker, self.source)


    def test_extension_workspace_refreshes_after_injected_payload(self):
        for marker in [
            "crossgrowth-extension-workspace-ready",
            "__crossgrowthExtensionWorkspaceReadyListenerInstalled",
            "renderExtensionWorkspacePayload();",
            "reviewWorkspaceSourceBreakdownText(body.source_breakdown || {}, payload.output_language)",
            "reviewWorkspaceSourceGuidanceText(body.source_breakdown || {})",
            "sourceBreakdownTitle",
            "sourceBreakdownGuidance",
        ]:
            self.assertIn(marker, self.source)


    def test_extension_workspace_source_breakdown_uses_payload_language(self):
        for marker in [
            "reviewWorkspaceSourceLabel(key, language = currentOutputLanguage())",
            "payload.output_language",
            "Unique analyzed reviews",
            "reviewWorkspaceSourceBreakdownText(body.source_breakdown || {}, payload.output_language)",
        ]:
            self.assertIn(marker, self.source)

    def test_extension_workspace_inherits_payload_or_url_language(self):
        for marker in [
            "new URLSearchParams(window.location.search || \"\").get(\"output_language\")",
            "source?.output_language || readExtensionWorkspacePayload()?.output_language || urlLanguage",
            "body.output_language = body.output_language || payload.output_language || extensionWorkspaceLanguage(payload)",
            "reviewWorkspaceSourceBreakdownText(body.source_breakdown || {}, payload.output_language)",
            "tExtensionWorkspace(\"topPainPoints\", body)",
            "tExtensionWorkspace(\"buyerObjectionsSection\", body)",
        ]:
            self.assertIn(marker, self.source)


    def test_review_workspace_localizes_apparel_theme_labels_frontend(self):
        for marker in [
            "reviewWorkspaceLocalizedThemeLabel",
            "summer fabric comfort",
            "sewing / quality control issue",
            "size / fit issue",
            "color expectation mismatch",
            "\\u590f\\u5b63\\u9762\\u6599\\u8212\\u9002\\u5ea6",
            "\\u7f1d\\u5236 / \\u8d28\\u68c0\\u95ee\\u9898",
            "\\u5c3a\\u7801 / \\u7248\\u578b\\u504f\\u5c0f",
            "\\u989c\\u8272 / \\u8272\\u5dee\\u9884\\u671f",
        ]:
            self.assertIn(marker, self.source)


    def test_review_workspace_localized_theme_label_uses_extension_workspace_language(self):
        for marker in [
            "function reviewWorkspaceLocalizedThemeLabel",
            "const language = extensionWorkspaceLanguage(source);",
            "summer fabric comfort",
            "sewing / quality control issue",
            "\\u590f\\u5b63\\u9762\\u6599\\u8212\\u9002\\u5ea6",
            "\\u7f1d\\u5236 / \\u8d28\\u68c0\\u95ee\\u9898",
        ]:
            self.assertIn(marker, self.source)



    def test_review_workspace_source_groups_render_structured_metadata_summary(self):
        for marker in [
            "function reviewWorkspaceMetadataSummaryText(metadata, language = currentOutputLanguage())",
            "function reviewWorkspaceMetadataListText(values)",
            "group.metadata_summary || {}",
            "verified_purchase_count",
            "review_date_count",
            "helpful_vote_review_count",
            "top_colors",
            "top_sizes",
            "top_review_dates",
            "verifiedPurchaseCount",
            "reviewDateCount",
            "helpfulVoteReviewCount",
            "topColors",
            "topSizes",
            "topReviewDates",
            "metadataSummary",
        ]:
            self.assertIn(marker, self.source)


    def test_extension_workspace_auto_analyzes_injected_payload_once(self):
        for marker in [
            "extensionWorkspaceAutoAnalyzeKey",
            "maybeAutoAnalyzeExtensionWorkspace",
            "payload.auto_analyze",
            "crossgrowth_extension_workspace_auto_analyzed",
            "window.sessionStorage.getItem(key)",
            "window.sessionStorage.setItem(key, \"1\")",
            "window.setTimeout(() =>",
            "analyzeExtensionWorkspace();",
            "maybeAutoAnalyzeExtensionWorkspace(readExtensionWorkspacePayload());",
        ]:
            self.assertIn(marker, self.source)


    def test_extension_workspace_auto_analysis_runs_after_payload_render(self):
        for marker in [
            "function renderExtensionWorkspacePayload",
            "maybeAutoAnalyzeExtensionWorkspace(payload);",
            "function maybeAutoAnalyzeExtensionWorkspace",
            "auto_analyze",
        ]:
            self.assertIn(marker, self.source)


    def test_extension_workspace_auto_analysis_shows_status_before_fetch(self):
        self.assertIn('function extensionWorkspaceStatusHTML(kind, source = null, detail = "")', self.source)
        self.assertIn('extensionWorkspaceStatusHTML("analyzing", payload)', self.source)
        self.assertIn('data-extension-auto-analysis-status', self.source)
        self.assertIn('maybeAutoAnalyzeExtensionWorkspace(payload)', self.source)
        self.assertIn('analyzeExtensionWorkspace();', self.source)
        self.assertIn('tExtensionWorkspace("analyzingWorkspace", payload)', self.source)

    def test_extension_workspace_localizes_new_positive_signal_labels(self):
        expected_mappings = {
            "repeat purchase intent": "\\u6301\\u7eed\\u590d\\u8d2d / \\u613f\\u610f\\u7ee7\\u7eed\\u8d2d\\u4e70",
            "best root beer praise": "\\u6700\\u4f73\\u53e3\\u5473\\u8bc4\\u4ef7",
            "root beer flavor comparison": "\\u98ce\\u5473\\u5bf9\\u6bd4 / \\u53e3\\u611f\\u5dee\\u5f02",
            "regional availability context": "\\u5730\\u533a\\u53ef\\u83b7\\u5f97\\u6027 / \\u672c\\u5730\\u4e70\\u4e0d\\u5230",
        }

        for key, escaped_label in expected_mappings.items():
            self.assertIn(f"'{key}': '{escaped_label}',", self.source)
