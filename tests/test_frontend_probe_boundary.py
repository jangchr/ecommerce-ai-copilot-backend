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
            "pathProductIdeaCard",
            "pathCustomerFeedbackCard",
            "pathSampleProductCard",
            "activeWorkspacePanel",
            "inlineResultPanel",
            "inlineResultEmptyState",
            "inlineResultContent",
            "productIdeaWorkspace",
            "customerFeedbackWorkspace",
            "sampleProductWorkspace",
            "I have a product idea",
            "I have customer feedback",
            "Show me a sample",
            "Only the active workspace is shown",
            "Generate from the active workspace",
            "function setActiveWorkspace(name, options = {})",
            "function mountUserTaskFlow()",
            "function showInlineResultPanel()",
            "showInlineResultPanel();",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.source)

        self.assertIn("productIdeaWorkspace.appendChild(productDescriptionMode);", self.source)
        self.assertIn("customerFeedbackWorkspace.appendChild(pastedReviewsMode);", self.source)
        self.assertIn("sampleProductWorkspace.appendChild(stableProductWorkspace);", self.source)
        self.assertIn("sampleProductWorkspace.appendChild(exampleGallery);", self.source)
        self.assertIn("inlineResultContent.appendChild(section);", self.source)
        self.assertIn("setActiveWorkspace('productIdea');", self.source)

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
        self.assertIn("Do not use Amazon URLs in Product Mode yet", self.source)
        self.assertIn("Amazon URLs are available only in Debug Mode / Amazon Shadow", self.source)
        self.assertIn("Product Result", self.source)
        self.assertIn("Copy / Download / Translation Actions", self.source)
        self.assertIn("Feedback", self.source)
        self.assertIn("Product Description Mode", self.source)
        self.assertIn("L17.2-A Chinese landing and onboarding copy polish", self.source)
        self.assertIn("chineseOnboardingPanel", self.source)
        self.assertIn("workflowPathTitle: '选择你的生成方式'", self.source)
        self.assertIn("inlineResultPanelTitle: '生成结果预览'", self.source)
        self.assertIn("inlineResultEmptyState: '点击生成后，Hook、创意摘要和分镜脚本会显示在这里。'", self.source)
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
        self.assertIn("香醋 / balsamic_vinegar", self.source)
        self.assertIn("台灯 / desk_lamp", self.source)
        self.assertIn("宠物毛发清理 / pet_hair_vacuum", self.source)
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
            r"pastedReviewsMode: '粘贴用户反馈模式',(?P<body>.*?)exampleGallery: '示例产品库',",
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
        self.assertIn("Portable mini blender", self.source)
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
        for text in [
            "balsamic_vinegar",
            "pet_hair_vacuum",
            "desk_lamp",
            "瓶盖破裂、泄漏、口感稀薄",
            "宠物毛清不干净、吸力不够、反复清理",
            "光线刺眼、桌面杂乱、夜间工作疲劳",
            "别再让一瓶漏得到处都是的香醋毁掉你的沙拉。",
            "如果你每天都在和沙发上的宠物毛打仗，这个开场能直接抓住目标用户。",
            "你的桌灯是在帮你工作，还是正在让你更累？",
            "展示破损瓶盖、粘腻包装，再切到干净浓稠的替代方案。",
            "展示沙发、地毯和衣服上的宠物毛，再展示清理前后对比。",
            "展示昏暗桌面、眼疲劳，再展示柔和灯光和整洁工作区。",
        ]:
            with self.subTest(text=text):
                self.assertIn(text, self.source)

        gallery_match = re.search(
            r"<section class=\"example-gallery\"(?P<body>.*?)<section class=\"agent-track\"",
            self.source,
            re.S,
        )
        self.assertIsNotNone(gallery_match)
        gallery_body = gallery_match.group("body")
        self.assertIn("setExampleSlug('balsamic_vinegar')", gallery_body)
        self.assertIn("setExampleSlug('pet_hair_vacuum')", gallery_body)
        self.assertIn("setExampleSlug('desk_lamp')", gallery_body)

        function_match = re.search(
            r"function setExampleSlug\(slug\) \{(?P<body>.*?)\n        \}",
            self.source,
            re.S,
        )
        self.assertIsNotNone(function_match)
        function_body = function_match.group("body")
        self.assertIn("setDemoSlug(slug);", function_body)
        for body in [gallery_body, function_body]:
            with self.subTest(gallery_boundary=body[:40]):
                self.assertNotIn("startSystem(", body)
                self.assertNotIn("postCopilot", body)
                self.assertNotIn("generate-copilot", body)
                self.assertNotIn("debug-source-probe", body)
                self.assertNotIn("amazonShadowMode", body)
                self.assertNotIn("localStorage", body)
                self.assertNotIn("data.debug", body)
                self.assertNotIn("shadow_sources", body)
                self.assertNotIn("telemetry_summary", body)
                self.assertNotIn("memory_observability", body)

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
        self.assertIn("evidenceSourceCard", self.source)
        self.assertIn("evidenceSourceTitle", self.source)
        self.assertIn("sourceTypeLabel", self.source)
        self.assertIn("sourceConfidenceLabel", self.source)
        self.assertIn("reviewCountLabel", self.source)
        self.assertIn("dataWarningsLabel", self.source)

        start = self.source.find("function renderEvidenceSourceCard(evidence)")
        end = self.source.find("function resultCreativeSummary", start)
        self.assertNotEqual(start, -1)
        self.assertNotEqual(end, -1)

        body = self.source[start:end]

        self.assertIn("source_type", body)
        self.assertIn("data_warnings", body)
        self.assertIn("review_count", body)
        self.assertIn("review_confidence", body)

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
        self.assertIn("inlineResultPanelTitle: '生成结果预览'", self.source)
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
        self.assertNotIn("Generate from the active workspace", zh_copy)

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
        function_match = re.search(
            r"function fillSampleProductDescription\(\) \{(?P<body>.*?)\n        \}",
            self.source,
            re.S,
        )
        self.assertIsNotNone(function_match)
        body = function_match.group("body")

        for text in [
            "Portable mini blender",
            "Kitchen appliance",
            "A compact rechargeable blender for smoothies, protein shakes, and travel use.",
            "Customers complain that large blenders are hard to clean",
            "TikTok",
            "tiktok_ctr",
        ]:
            with self.subTest(text=text):
                self.assertIn(text, body)

        self.assertIn("descriptionProductName", body)
        self.assertIn("descriptionProductCategory", body)
        self.assertIn("descriptionProductDescription", body)
        self.assertIn("descriptionPainPoints", body)
        self.assertIn("descriptionTargetPlatform", body)
        self.assertIn("descriptionGoal", body)

        self.assertNotIn("postProductDescription", body)
        self.assertNotIn("generate-from-description", body)
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
        function_match = re.search(
            r"function fillSamplePastedReviews\(\) \{(?P<body>.*?)\n        \}",
            self.source,
            re.S,
        )
        self.assertIsNotNone(function_match)
        body = function_match.group("body")

        for text in [
            "Portable mini blender",
            "Kitchen appliance",
            "A compact rechargeable blender for smoothies, protein shakes, and travel use.",
            "I hate cleaning my big blender every morning.",
            "It is too loud for my apartment.",
            "I wish I could blend something quickly at work.",
            "TikTok",
            "tiktok_ctr",
        ]:
            with self.subTest(text=text):
                self.assertIn(text, body)

        self.assertIn("reviewsProductName", body)
        self.assertIn("reviewsProductCategory", body)
        self.assertIn("reviewsProductDescription", body)
        self.assertIn("reviewsPastedReviews", body)
        self.assertIn("reviewsTargetPlatform", body)
        self.assertIn("reviewsGoal", body)

        self.assertIn("function fillSamplePetHairReviews()", self.source)
        self.assertIn("function fillSampleDeskLampReviews()", self.source)
        self.assertIn("Pet hair vacuum brush", self.source)
        self.assertIn("Adjustable desk lamp", self.source)

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

    def test_pasted_reviews_extra_samples_only_fill_inputs(self):
        for function_name in ["fillSamplePetHairReviews", "fillSampleDeskLampReviews"]:
            with self.subTest(sample_function=function_name):
                match = re.search(
                    rf"function {function_name}\(\) \{{(?P<body>.*?)\n        \}}",
                    self.source,
                    re.S,
                )
                self.assertIsNotNone(match)
                body = match.group("body")

                self.assertIn("reviewsProductName", body)
                self.assertIn("reviewsProductCategory", body)
                self.assertIn("reviewsProductDescription", body)
                self.assertIn("reviewsPastedReviews", body)
                self.assertIn("reviewsTargetPlatform", body)
                self.assertIn("reviewsGoal", body)
                self.assertIn("setReviewsStatus", body)

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
        self.assertIn("const payload = { url, goal: 'tiktok_ctr', output_language: currentOutputLanguage() };", self.source)
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


if __name__ == "__main__":
    unittest.main()
