from pathlib import Path
import re
import unittest


FRONTEND_PATH = Path(__file__).resolve().parents[1] / "static" / "index.html"


class FrontendProbeBoundaryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = FRONTEND_PATH.read_text(encoding="utf-8")

    def test_video_job_controls_create_job_from_generation_data(self):
        self.assertIn("function renderVideoJobControls(data)", self.source)
        self.assertIn("renderVideoDraftPanel(data.video_generation_packet)", self.source)
        self.assertIn("renderExternalVideoToolHandoffPanel(data.external_video_tool_handoff)", self.source)
        self.assertIn("renderVideoJobControls(data)", self.source)
        self.assertIn("async function createVideoJobFromLatestGeneration()", self.source)
        self.assertIn("async function postVideoJobFromGeneration(payload)", self.source)
        self.assertIn("async function getVideoGenerationJob(jobId)", self.source)
        self.assertIn("async function listVideoGenerationJobs(limit = 10)", self.source)
        self.assertIn("async function postVideoGenerationJobResult(jobId, payload)", self.source)
        self.assertIn("async function postVideoGenerationExperiment(jobId, payload)", self.source)
        self.assertIn("async function postVideoProviderSubmit(jobId, payload)", self.source)
        self.assertIn("async function postVideoProviderPoll(jobId, payload)", self.source)
        self.assertIn("async function getVideoApprovalGate(jobId)", self.source)
        self.assertIn("async function postVideoApprovalDecision(jobId, payload)", self.source)
        self.assertIn("async function videoGenerationJsonResponse(response, fallbackKey)", self.source)
        self.assertIn("/api/v1/video-generation/jobs/from-generation", self.source)
        self.assertIn("/api/v1/video-generation/jobs/${encodeURIComponent(jobId)}", self.source)
        self.assertIn("/api/v1/video-generation/jobs?limit=${encodeURIComponent(limit)}", self.source)
        self.assertIn("/api/v1/video-generation/jobs/${encodeURIComponent(jobId)}/result", self.source)
        self.assertIn("/api/v1/video-generation/jobs/${encodeURIComponent(jobId)}/experiments", self.source)
        self.assertIn("/api/v1/video-generation/jobs/${encodeURIComponent(jobId)}/provider-submit", self.source)
        self.assertIn("/api/v1/video-generation/jobs/${encodeURIComponent(jobId)}/provider-poll", self.source)
        self.assertIn("/api/v1/video-generation/jobs/${encodeURIComponent(jobId)}/approval-gate", self.source)
        self.assertIn(
            "/api/v1/video-generation/jobs/${encodeURIComponent(jobId)}/approval-gate/decision",
            self.source,
        )
        self.assertIn("generation_data: latestProductData", self.source)
        self.assertIn("videoJobProviderSelect", self.source)
        self.assertIn("videoJobCreateBtn", self.source)
        self.assertIn("renderVideoJobResult", self.source)
        self.assertIn("renderVideoJobResultForm", self.source)
        self.assertIn("renderExternalVideoExperimentsPanel", self.source)
        self.assertIn("renderAgentFeedbackDecision", self.source)
        self.assertIn("agentFeedbackIssueLabel", self.source)
        self.assertIn("renderSecondExperimentComparison", self.source)
        self.assertIn("secondExperimentComparisonMessage", self.source)
        self.assertIn("secondExternalExperimentComparisonPanel", self.source)
        self.assertIn("renderExperimentComparisonDecisionGate", self.source)
        self.assertIn("function renderHumanApprovalGate(approvalGate, jobId)", self.source)
        self.assertIn("async function updateHumanApprovalGate(decision)", self.source)
        self.assertIn("experimentDecisionGateMessage", self.source)
        self.assertIn("experimentComparisonDecisionGatePanel", self.source)
        self.assertIn("function renderDemoReadyRunSummary(summary)", self.source)
        self.assertIn("function renderArtifactLineage(lineage)", self.source)
        self.assertIn("function renderControlledProviderHandoffChecklist(checklist)", self.source)
        self.assertIn("demoReadyRunSummaryPanel", self.source)
        self.assertIn("artifactLineageSummaryPanel", self.source)
        self.assertIn("controlledProviderHandoffChecklistPanel", self.source)
        self.assertIn("demoReadyRunSummary", self.source)
        self.assertIn("whyMultiAgentGraph", self.source)
        self.assertIn("controlledProviderHandoffChecklist", self.source)
        self.assertIn("externalApiCallAllowed", self.source)
        self.assertIn("notLinearWorkflow", self.source)
        self.assertIn("Demo-ready run summary", self.source)
        self.assertIn("Why this is a multi-agent graph", self.source)
        self.assertIn("Controlled provider/manual handoff checklist", self.source)
        self.assertIn("This is not a linear workflow", self.source)
        for approval_marker in [
            "Human Approval Gate",
            "Approval status",
            "Approval scope",
            "Blocks provider submit",
            "Blocks external API call",
            "Approval checklist",
            "Approval decision history",
            "Approve controlled test",
            "Request changes",
            "Reject",
            "Cancel approval",
            "Approved controlled provider/manual test",
            "Blocked by human approval",
            "Provider submit is blocked until human approval.",
            "Approval required before provider/manual test.",
            "Approval updated.",
            "Failed to update approval gate.",
            "Changes requested.",
            "Approval rejected.",
            "Approval cancelled.",
            "humanApprovalGatePanel",
            "humanApprovalGateStatus",
            "blocked_by_human_approval",
        ]:
            with self.subTest(approval_marker=approval_marker):
                self.assertIn(approval_marker, self.source)
        self.assertIn("renderVideoProviderProgress", self.source)
        self.assertIn("renderVideoCostEstimate", self.source)
        self.assertIn("providerPayload.cost_estimate", self.source)
        self.assertIn("renderRecentVideoJobsPanel", self.source)
        self.assertIn("renderRecentVideoJobRows", self.source)
        self.assertIn("renderVideoJobControls(data)", self.source)
        self.assertIn("refreshCurrentVideoJobStatus", self.source)
        self.assertIn("copyCurrentVideoJobPrompt", self.source)
        self.assertIn("copyCurrentVideoJobId", self.source)
        self.assertIn("saveCurrentVideoJobResult", self.source)
        self.assertIn("refreshRecentVideoJobs", self.source)
        self.assertIn("loadVideoGenerationJob", self.source)
        self.assertIn("videoJobCreateTitle", self.source)
        self.assertIn("videoJobCreated", self.source)
        self.assertIn("videoJobFailed", self.source)
        for marker in [
            "videoJobCurrentPanel",
            "videoJobExternalResultPanel",
            "externalVideoExperimentsPanel",
            "secondExternalExperimentComparisonPanel",
            "experimentComparisonDecisionGatePanel",
            "videoExperimentSaveBtn",
            "videoExperimentToolName",
            "videoExperimentPromptType",
            "videoExperimentResultUrl",
            "videoExperimentPreviewUrl",
            "videoExperimentActualCostUsd",
            "videoExperimentProductConsistency",
            "videoExperimentStoryboardFollowing",
            "videoExperimentVisualQuality",
            "videoExperimentAdReadiness",
            "videoExperimentOverallScore",
            "videoExperimentNotes",
            "videoExperimentFailureReason",
            "videoProviderProgressPanel",
            "videoProviderRuntimePanel",
            "recentVideoJobsPanel",
            "videoJobRefreshBtn",
            "videoJobCopyPromptBtn",
            "videoJobCopyIdBtn",
            "videoJobSaveResultBtn",
            "videoProviderSubmitBtn",
            "videoProviderPollBtn",
            "videoProviderCompleteBtn",
            "refreshVideoJobsBtn",
            "recentVideoJobsList",
            "provider_payload",
            "provider_runtime",
            "provider_job_id",
            "provider_status",
            "poll_count",
            "external_api_called",
            "submitted_at",
            "last_polled_at",
            "selected_export_key",
            "provider_label",
            "result_url",
            "preview_url",
            "download_url",
            "provider_job_id",
            "warnings",
            "submitCurrentVideoProviderJob",
            "pollCurrentVideoProviderStatus",
            "completeCurrentVideoProviderResult",
            "saveExternalVideoExperiment",
            "external_video_experiments",
            "external_api_called",
            "cost_incurred_by_crossgrowth",
            "agent_feedback_decision",
        ]:
            with self.subTest(video_job_marker=marker):
                self.assertIn(marker, self.source)

        for copy_key in [
            "refreshJobStatus",
            "copySelectedPrompt",
            "copyJobId",
            "recordExternalVideoResult",
            "saveVideoResult",
            "videoResultSaved",
            "videoResultSaveFailed",
            "recentVideoJobs",
            "refreshVideoJobs",
            "noVideoJobsYet",
            "loadJob",
            "resultUrl",
            "previewUrl",
            "downloadUrl",
            "providerJobId",
            "notes",
            "updatedAt",
            "createdAt",
            "warnings",
            "providerProgressTitle",
            "providerProgressNote",
            "providerCostApprovalNote",
            "externalVideoExperimentsTitle",
            "externalVideoExperimentsNote",
            "externalExperimentTrackerNoApi",
            "toolName",
            "promptType",
            "actualCostUsd",
            "productConsistency",
            "storyboardFollowing",
            "visualQuality",
            "adReadiness",
            "overallScore",
            "agentFeedbackDecision",
            "feedbackLoop",
            "sourceAgent",
            "targetAgent",
            "issueType",
            "severity",
            "recommendedAction",
            "experimentAgentRecommendsRework",
            "feedbackTriggeredReworkRun",
            "feedbackTriggeredReworkRunQueued",
            "productConsistencyIssue",
            "storyboardFollowingIssue",
            "visualQualityIssue",
            "adReadinessIssue",
            "costValueIssue",
            "feedbackRecordedNoRework",
            "failureReason",
            "saveExternalExperiment",
            "externalExperimentSaved",
            "videoExperimentSaveFailed",
            "videoCostEstimateTitle",
            "videoEstimatedCostLabel",
            "videoCostLevelLabel",
            "videoCostDurationLabel",
            "videoCostRetryLabel",
            "videoPricingEstimateLabel",
            "videoCostEstimateOnly",
            "videoCostRequiresConfirmation",
            "videoManualNoApiCost",
            "submitProviderJob",
            "providerJobSubmitted",
            "providerJobSubmitFailed",
            "providerJobSubmitting",
            "pollProviderStatus",
            "providerStatusRefreshed",
            "providerStatusRefreshFailed",
            "providerStatusRefreshing",
            "completeSimulatedProviderResult",
            "providerResultCompleted",
            "providerJobIdLabel",
            "providerStatusLabel",
            "pollCountLabel",
            "externalApiCalledLabel",
            "submittedAtLabel",
            "lastPolledAtLabel",
        ]:
            with self.subTest(video_job_copy_key=copy_key):
                self.assertIn(copy_key, self.source)

        self.assertIn("refreshJobStatus: 'Refresh job status'", self.source)
        self.assertIn("refreshJobStatus: '\\u5237\\u65b0\\u4efb\\u52a1\\u72b6\\u6001'", self.source)
        self.assertIn("copySelectedPrompt: 'Copy selected prompt'", self.source)
        self.assertIn("copySelectedPrompt: '\\u590d\\u5236\\u5df2\\u9009\\u63d0\\u793a\\u8bcd'", self.source)
        self.assertIn("recordExternalVideoResult: 'Record external video result'", self.source)
        self.assertIn("recordExternalVideoResult: '\\u8bb0\\u5f55\\u5916\\u90e8\\u89c6\\u9891\\u7ed3\\u679c'", self.source)
        self.assertIn("recentVideoJobs: 'Recent video jobs'", self.source)
        self.assertIn("recentVideoJobs: '\\u6700\\u8fd1\\u89c6\\u9891\\u4efb\\u52a1'", self.source)
        self.assertIn("providerProgressTitle: 'Provider progress'", self.source)
        self.assertIn("providerProgressTitle: '\\u63d0\\u4f9b\\u65b9\\u8fdb\\u5ea6'", self.source)
        self.assertIn("providerCostApprovalNote", self.source)
        self.assertIn("externalVideoExperimentsTitle: 'External Video Experiments'", self.source)
        self.assertIn("Record results from Gemini, Doubao, Runway, Pika, or other external tools.", self.source)
        self.assertIn("CrossGrowth does not call external video APIs in this experiment tracker.", self.source)
        self.assertIn("Save external experiment", self.source)
        self.assertIn("Agent feedback decision", self.source)
        self.assertIn("Feedback loop", self.source)
        self.assertIn("Source Agent", self.source)
        self.assertIn("Target Agent", self.source)
        self.assertIn("Issue type", self.source)
        self.assertIn("Severity", self.source)
        self.assertIn("Recommended action", self.source)
        self.assertIn("Experiment Agent recommends rework", self.source)
        self.assertIn("Feedback-triggered rework run", self.source)
        self.assertIn("Rework run queued for upstream agent review.", self.source)
        self.assertIn("Rework artifact", self.source)
        self.assertIn("Revised keyframe plan", self.source)
        self.assertIn("Revised scene keyframes", self.source)
        self.assertIn("Product consistency constraints", self.source)
        self.assertIn("Human review required", self.source)
        self.assertIn("Revised external video handoff", self.source)
        self.assertIn("Revised Gemini prompt", self.source)
        self.assertIn("Revised Doubao prompt", self.source)
        self.assertIn("Revised image-to-video prompt", self.source)
        self.assertIn("Copy revised handoff package", self.source)
        self.assertIn("Revised prompt handoff", self.source)
        self.assertIn("Experiment feedback created revised video prompts.", self.source)
        self.assertIn("Next external video test", self.source)
        self.assertIn("Product consistency prompt constraints", self.source)
        self.assertIn("Poll rework run", self.source)
        self.assertIn("Experiment feedback created a revised keyframe plan.", self.source)
        self.assertIn("Experiment decision gate", self.source)
        self.assertIn("Recommended route", self.source)
        self.assertIn("Next Agent", self.source)
        self.assertIn("Decision type", self.source)
        self.assertIn("Human approval required", self.source)
        self.assertIn("Proceed to controlled test", self.source)
        self.assertIn("Trigger new rework", self.source)
        self.assertIn("Decision: proceed to controlled provider/manual test.", self.source)
        self.assertIn("Decision: retry rework before scaling.", self.source)
        self.assertIn("Decision: manual review required.", self.source)
        self.assertIn("Decision: stronger reference or keyframe revision required.", self.source)
        self.assertIn("Stronger reference required", self.source)
        self.assertIn("function renderRevisedKeyframePlan(plan)", self.source)
        self.assertIn("function renderRevisedExternalVideoHandoff(handoff)", self.source)
        self.assertIn("function copyRevisedExternalVideoHandoffPackage()", self.source)
        self.assertIn("function pollExperimentReworkRun(runId)", self.source)
        self.assertIn("revised_keyframe_plan", self.source)
        self.assertIn("revised_external_video_handoff", self.source)
        self.assertIn("triggered_rework_run_id", self.source)
        self.assertIn("triggered_rework_result_type", self.source)
        self.assertIn("triggered_rework_next_artifact_type", self.source)
        self.assertIn("triggered_rework_poll_url", self.source)
        self.assertIn("Product consistency issue", self.source)
        self.assertIn("Storyboard following issue", self.source)
        self.assertIn("Visual quality issue", self.source)
        self.assertIn("Ad readiness issue", self.source)
        self.assertIn("Cost/value issue", self.source)
        self.assertIn("Feedback recorded; no rework needed", self.source)
        self.assertIn("Gemini", self.source)
        self.assertIn("Doubao", self.source)
        self.assertIn("videoCostEstimateTitle: 'Estimated API cost'", self.source)
        self.assertIn("videoCostEstimateTitle: '\\u9884\\u4f30 API \\u6210\\u672c'", self.source)
        self.assertIn("videoCostEstimatePanel", self.source)
        self.assertIn("Estimate only. Real provider pricing can change.", self.source)
        self.assertIn("Real video generation requires user confirmation before cost is incurred.", self.source)
        self.assertIn("Manual export has no API cost in this app.", self.source)
        self.assertIn("requires_user_confirmation", self.source)
        self.assertIn("pricing_is_estimate", self.source)
        for marker in [
            "externalVideoToolHandoffTitle",
            "External Video Tool Handoff",
            "renderExternalVideoToolHandoffPanel",
            "external_video_tool_handoff",
            "copyExternalVideoToolPrompt",
            "copyFullExternalVideoHandoffPackage",
            "copyExternalVideoKeyframePrompt",
            "copyGeminiPrompt",
            "copyDoubaoPrompt",
            "copyImageToVideoPrompt",
            "copyFullHandoffPackage",
            "productConsistencyRules",
            "productAssetLock",
            "keyframePlan",
            "mustPreserve",
            "mustNotChange",
            "imageReferenceRules",
            "humanReviewRequired",
            "recommendedClipStrategy",
            "productPosition",
            "cameraDirection",
            "evidenceAnchor",
            "negativePrompt",
            "keyframePrompts",
            "qualityChecklist",
            "No external video API is called by CrossGrowth in this flow.",
            "Review external tool pricing before paid generation.",
        ]:
            with self.subTest(external_handoff_marker=marker):
                self.assertIn(marker, self.source)
        self.assertIn("submitProviderJob: 'Submit provider job'", self.source)
        self.assertIn("pollProviderStatus: 'Poll provider status'", self.source)
        self.assertIn("completeSimulatedProviderResult: 'Complete simulated provider result'", self.source)
        self.assertIn("Simulated provider flow only. No external API is called.", self.source)
        self.assertIn("Use this to test queued, processing, and completed lifecycle states.", self.source)
        self.assertIn("Real Runway/Pika integration requires separate setup, pricing review, API key approval, and user approval later.", self.source)
        self.assertIn("Manual result handoff is still available.", self.source)
        for label in [
            "Product Asset Lock",
            "Keyframe Plan",
            "Must preserve",
            "Must not change",
            "Image reference rules",
            "Human review required",
            "Recommended clip strategy",
            "Product position",
            "Camera direction",
            "Evidence anchor",
        ]:
            with self.subTest(asset_lock_keyframe_label=label):
                self.assertIn(label, self.source)
        for marker in [
            "handoff.product_asset_lock",
            "handoff.keyframe_plan",
            "assetLock.must_preserve",
            "assetLock.must_not_change",
            "assetLock.image_reference_rules",
            "keyframePlan.recommended_clip_strategy",
            "keyframePlan.scenes",
            "scene.product_position",
            "scene.camera_direction",
            "scene.evidence_anchor",
            "scene.risk_notes",
        ]:
            with self.subTest(asset_lock_keyframe_marker=marker):
                self.assertIn(marker, self.source)
        self.assertIn("t('providerCostApprovalNote')", self.source)
        self.assertIn("copyVideoJobText(prompt, 'videoJobPromptCopied')", self.source)
        self.assertIn("copyVideoJobText(jobId, 'videoJobIdCopied')", self.source)
        self.assertIn("status: (resultUrl || previewUrl) ? 'external_result_ready' : 'manual_export_completed'", self.source)
        self.assertIn("await refreshRecentVideoJobs();", self.source)
        self.assertIn("postVideoProviderSubmit(jobId", self.source)
        self.assertIn("postVideoProviderPoll(jobId", self.source)
        self.assertGreaterEqual(self.source.count("await refreshRecentVideoJobs();"), 2)
        self.assertNotIn("????", self.source)

    def test_video_job_controls_render_directly_after_video_draft(self):
        dashboard_start = self.source.find("function renderProductDashboard(data, options = {})")
        self.assertNotEqual(dashboard_start, -1)
        dashboard_end = self.source.find("function renderAmazonShadowSummary", dashboard_start)
        self.assertNotEqual(dashboard_end, -1)
        dashboard_body = self.source[dashboard_start:dashboard_end]

        draft_index = dashboard_body.find("renderVideoDraftPanel(data.video_generation_packet)")
        job_index = dashboard_body.find("renderVideoJobControls(data)", draft_index)
        self.assertNotEqual(draft_index, -1)
        self.assertNotEqual(job_index, -1)
        self.assertGreater(job_index, draft_index)
        self.assertLess(job_index - draft_index, 180)
        self.assertIn("packet.packet_version !== 'video_generation_v1'", self.source)
        self.assertIn("if (!data || !data.video_generation_packet) return ''", self.source)

    def test_agent_trace_panel_is_rendered_from_product_data(self):
        self.assertIn("function renderAgentTracePanel(agentTrace)", self.source)
        self.assertIn("data.agent_trace", self.source)
        self.assertIn("agentTraceTitle", self.source)
        self.assertIn("agentTraceSubtitle", self.source)
        self.assertIn("agentTraceExecutionMode", self.source)
        self.assertIn("agentTraceRealExecution", self.source)
        self.assertIn("agentTraceKeyOutputs", self.source)
        self.assertIn("evidence_agent", self.source)
        self.assertIn("strategy_agent", self.source)
        self.assertIn("storyboard_agent", self.source)
        self.assertIn("video_prompt_agent", self.source)
        self.assertIn("risk_agent", self.source)
        self.assertIn("order.join(\' -> \')", self.source)

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
        self.assertIn("Linked review signal", self.source)
        self.assertIn("关联评论信号", self.source)
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
        self.assertIn("Review signal preview", self.source)
        self.assertIn("评论信号预览", self.source)
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
        self.assertIn("function normalizeStoryboardSceneGoal(goal, storyboard)", self.source)
        self.assertIn("Customer feedback signals", self.source)
        self.assertIn("Positive signals", self.source)
        self.assertIn("Buyer objections", self.source)
        self.assertIn("用户反馈信号", self.source)
        self.assertIn("正向信号", self.source)
        self.assertIn("购买顾虑", self.source)

        start = self.source.find("function renderStoryboardBrief(storyboard)")
        end = self.source.find("let latestDebugCategory", start)
        self.assertNotEqual(start, -1)
        self.assertNotEqual(end, -1)

        body = self.source[start:end]

        self.assertIn("scene_goal", body)
        self.assertIn("normalizeStoryboardSceneGoal", body)
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

    def test_video_draft_frontend_panel_is_present(self):
        self.assertIn("function renderVideoDraftPanel(packet)", self.source)
        self.assertIn("renderVideoDraftPanel(data.video_generation_packet)", self.source)
        self.assertIn("data.video_generation_packet", self.source)
        self.assertIn("video-draft-panel", self.source)
        self.assertIn("video-draft-scenes", self.source)
        self.assertIn("function copyFullVideoPrompt()", self.source)
        self.assertIn("function copyVideoScenePrompt(index)", self.source)
        self.assertIn("function copyVideoExportPrompt(formatKey)", self.source)
        self.assertIn("copyVideoDraftText", self.source)
        self.assertIn("data-video-export-key", self.source)
        self.assertIn("exportFormats[key]", self.source)
        self.assertIn("export_formats?.generic_video_prompt", self.source)
        self.assertIn("generic_video_prompt: t('genericVideoPrompt')", self.source)
        self.assertIn("capcut_shot_list: t('capcutShotList')", self.source)
        self.assertIn("runway_style_prompt: t('runwayStylePrompt')", self.source)
        self.assertIn("pika_style_prompt: t('pikaStylePrompt')", self.source)
        self.assertIn("${escapeHTML(t('copyExportPrompt'))}: ${escapeHTML(exportLabels[key])}", self.source)

        for key in [
            "videoDraftTitle",
            "copyFullVideoPrompt",
            "copyScenePrompt",
            "videoPromptCopied",
            "scenePromptCopied",
            "videoPromptCopyFailed",
            "recommendedDuration",
            "aspectRatio",
            "visualPrompt",
            "narration",
            "overlayText",
            "evidenceQuote",
            "riskNotes",
            "exportPrompts",
            "genericVideoPrompt",
            "capcutShotList",
            "runwayStylePrompt",
            "pikaStylePrompt",
        ]:
            with self.subTest(copy_key=key):
                self.assertIn(key, self.source)

        self.assertIn("videoDraftTitle: 'Video Draft'", self.source)
        self.assertIn("videoDraftTitle: '视频草稿'", self.source)
        self.assertIn("copyFullVideoPrompt: 'Copy full video prompt'", self.source)
        self.assertIn("copyFullVideoPrompt: '复制完整视频提示词'", self.source)
        self.assertIn("copyScenePrompt: 'Copy scene prompt'", self.source)
        self.assertIn("copyScenePrompt: '复制镜头提示词'", self.source)
        self.assertIn("copyExportPrompt: 'Copy export prompt'", self.source)
        self.assertIn("copyExportPrompt: '复制导出提示词'", self.source)
        self.assertIn("videoPromptCopied: 'Video prompt copied.'", self.source)
        self.assertIn("videoPromptCopied: '视频提示词已复制。'", self.source)
        self.assertIn("scenePromptCopied: 'Scene prompt copied.'", self.source)
        self.assertIn("scenePromptCopied: '镜头提示词已复制。'", self.source)
        self.assertNotIn("????", self.source)

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

    def test_multi_agent_demo_sample_and_checklist_exist(self):
        for text in [
            "Use Multi-Agent Demo Sample",
            "Multi-agent demo sample loaded.",
            "Multi-Agent Demo Checklist",
            "Generate from customer feedback.",
            "Open Business-grounded Multi-Agent Workflow.",
            "Review Evidence Agent, Asset Lock Agent, and Keyframe Agent.",
            "Open External Video Tool Handoff.",
            "Review Product Asset Lock and Keyframe Plan.",
            "Create a Video Job.",
            "Submit/poll simulated provider flow.",
            "Optionally record an External Video Experiment.",
            "Confirm no external video API is called.",
            "Portable Mini Blender",
            "kitchen_appliance",
            "A compact rechargeable blender for smoothies, travel, and quick morning drinks.",
            "Blends soft fruit well, but ice takes longer.",
            "Great for office smoothies when it is fully charged.",
        ]:
            with self.subTest(multi_agent_demo_text=text):
                self.assertIn(text, self.source)

        for marker in [
            "multiAgentDemoChecklist",
            "multiAgentDemoSampleBtn",
            "MULTI_AGENT_DEMO_SAMPLE",
            "function fillMultiAgentDemoSample()",
            "setLanguageMode('en')",
            "applyReviewSample(MULTI_AGENT_DEMO_SAMPLE)",
            "setReviewsStatus(t('multiAgentDemoSampleLoaded'))",
            "updateReviewInputPreviews()",
            "Business-grounded Multi-Agent Workflow",
            "Product Asset Lock",
            "Keyframe Plan",
            "External Video Tool Handoff",
            "videoJobCreateTitle",
            "videoCostEstimateTitle",
            "externalVideoExperimentsTitle",
        ]:
            with self.subTest(multi_agent_demo_marker=marker):
                self.assertIn(marker, self.source)

        fill_start = self.source.find("function fillMultiAgentDemoSample()")
        self.assertNotEqual(fill_start, -1)
        fill_body = self.source[fill_start:fill_start + 700]
        self.assertNotIn("generateFromReviews()", fill_body)
        self.assertNotIn("fetch(", fill_body)
        self.assertNotIn("debug-copilot", fill_body)
        self.assertNotIn("debug-source-probe", fill_body)
        self.assertNotIn("data.debug", fill_body)
        self.assertNotIn("????", self.source)

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
        self.assertIn("Review signal preview", self.source)
        self.assertIn("评论信号预览", self.source)
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

    def test_pasted_reviews_generation_uses_compact_clean_reviews(self):
        self.assertIn("function cleanedPastedReviewLines(value", self.source)
        self.assertIn("function compactPastedReviewsForGeneration(workspaceResponse, rawText)", self.source)
        self.assertIn("function compactReviewsFromVisibleLines(lines", self.source)
        self.assertIn("flavor name|size|color|style|pattern name|package quantity", self.source)
        self.assertIn("verified purchase", self.source)
        self.assertIn("reviewed in .*? on", self.source)

        function_match = re.search(
            r"async function generateFromReviews\(\) \{(?P<body>.*?)\n        function renderProductDashboard",
            self.source,
            re.S,
        )
        self.assertIsNotNone(function_match)
        body = function_match.group("body")
        self.assertIn("workspaceResponse = await postPastedReviewWorkspaceAnalysis", body)
        self.assertIn("const enrichedPastedReviews = compactPastedReviewsForGeneration(workspaceResponse, pastedReviews);", body)
        self.assertIn("const workspaceLlmEvidencePacket = workspaceResponse?.llm_evidence_packet || null;", body)
        self.assertIn("pasted_reviews: enrichedPastedReviews", body)
        self.assertIn("llm_evidence_packet: workspaceLlmEvidencePacket || undefined", body)
        self.assertNotIn("const enrichedPastedReviews = pastedReviews;", body)

    def test_pasted_reviews_preview_and_extension_import_clean_deduped_reviews(self):
        count_match = re.search(
            r"function reviewLineCount\(value\) \{(?P<body>.*?)\n        \}",
            self.source,
            re.S,
        )
        self.assertIsNotNone(count_match)
        self.assertIn("previewPastedReviewLines(value).length", count_match.group("body"))
        self.assertIn("function previewPastedReviewLines(value, limit = 80)", self.source)
        self.assertIn("compactReviewsFromVisibleLines([String(value || '')], limit)", self.source)

        preview_match = re.search(
            r"function reviewPainPointCandidates\(value\) \{(?P<body>.*?)\n        \}\n\n",
            self.source,
            re.S,
        )
        self.assertIsNotNone(preview_match)
        preview_body = preview_match.group("body")
        self.assertIn("previewPastedReviewLines(value)", preview_body)
        self.assertIn("positiveValueMarkers", preview_body)
        self.assertIn("explicitConcernMarkers", preview_body)
        self.assertIn("hasPriceTradeoff", preview_body)
        self.assertIn("truncateReviewLine(reviewConcernPreviewSnippet(line), 200)", preview_body)
        self.assertIn("function reviewConcernPreviewSnippet(line)", self.source)
        self.assertIn("cannot beat the price", self.source)
        self.assertIn("value priced", self.source)
        self.assertIn("stripAmazonReviewerPrefix", self.source)
        self.assertIn("Amazon Customer", self.source)

        fill_match = re.search(
            r"function fillPastedReviewsFromExtensionWorkspace\(payload\) \{(?P<body>.*?)\n  async function sendExtensionWorkspaceToReviewWorkflow",
            self.source,
            re.S,
        )
        self.assertIsNotNone(fill_match)
        self.assertIn(
            "compactReviewsFromVisibleLines(extensionWorkspaceVisibleReviewLines(payload), 40)",
            fill_match.group("body"),
        )

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
        self.assertNotIn("setLanguageMode(language);", bridge_body)
        self.assertIn("const labelSource = extensionWorkspacePageLanguageSource();", bridge_body)
        self.assertIn("setExtensionWorkspaceBridgeStatus(message)", bridge_body)
        self.assertIn("setExtensionWorkspaceBridgeStatus(tExtensionWorkspace(\"sendToReviewWorkflowWorking\", labelSource))", bridge_body)
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



class AgentLiveRunFrontendProbeTests(unittest.TestCase):
    def test_agent_live_run_timeline_markers_exist(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")

        for marker in [
            "Agent Live Run Timeline",
            "Start Live Agent Run",
            "Run status",
            "Current agent",
            "Latest events",
            "Polling for agent updates",
            "Agent run completed",
            "Agent run failed",
            "Backend-tracked async run",
            "No external video API is called",
            "Agent Graph Map",
            "Graph execution mode",
            "Autonomy level",
            "Active node",
            "Traversed path",
            "Transition decisions",
            "Validation results",
            "Rework loops",
            "Rework requested",
            "Rework applied",
            "Rework limit",
            "Evidence-safe rework",
            "Branch selected",
            "Waiting for user",
            "Rule-driven autonomous graph",
            "LLM autonomous decision",
            "function startLiveAgentRun()",
            "function renderAgentLiveRunTimeline(run",
            "function renderAgentGraphMap(run)",
            "function pollLiveAgentRun(runId, productName)",
            "function postAgentRunFromReviews(payload)",
            "function getAgentRun(runId)",
            "function getAgentRunEvents(runId)",
            "/api/v1/agent-runs/from-reviews",
            "/api/v1/agent-runs/${encodeURIComponent(runId)}",
            "/api/v1/agent-runs/${encodeURIComponent(runId)}/events",
            "liveAgentRunBtn",
            "agentLiveRunTimeline",
            "startAgentRunPolling",
            "stopAgentRunPolling",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)

        for preserved_marker in [
            "Business-grounded Multi-Agent Workflow",
            "Agent Handoff Map",
            "Agent Action Queue",
            "Product Asset Lock",
            "Keyframe Plan",
            "Video Job",
            "External Video Experiments",
            "Second external experiment comparison",
            "Baseline experiment",
            "Second experiment",
            "Prompt source",
            "Improvement status",
            "Score deltas",
            "Improved dimensions",
            "Regressed dimensions",
            "Second test improved after revised prompt handoff",
            "Second test regressed",
            "Use revised prompt for another short clip",
            "Do not scale this prompt",
            "Experiment decision gate",
            "Recommended route",
            "Next Agent",
            "Decision type",
            "Human approval required",
            "Proceed to controlled test",
            "Trigger new rework",
            "Decision: proceed to controlled provider/manual test",
            "Decision: retry rework before scaling",
            "Decision: manual review required",
            "Stronger reference required",
            "Graph Router Agent",
            "Route decision",
            "Selected next Agent",
            "Secondary next Agent",
            "Route type",
            "Selected edge",
            "Should trigger rework",
            "Should proceed to provider test",
            "Requires human approval",
            "Why this route was selected",
            "Router summary",
            "Centralized route decision",
            "Route selected by Graph Router Agent",
            "Not a linear workflow: route was selected from graph evidence",
            "function renderGraphRouterDecisions(container)",
            "graph_router_decisions",
            "latest_graph_router_decision",
            "graph_router_summary",
            "renderGraphRouterDecisions(run)",
            "renderGraphRouterDecisions(experiment)",
            "Demo-ready run summary",
            "Artifact lineage",
            "External Video Experiments",
        ]:
            with self.subTest(preserved_marker=preserved_marker):
                self.assertIn(preserved_marker, html)

        self.assertNotIn("????", html)


class MultiAgentWorkflowPanelProbeTests(unittest.TestCase):
    def test_multi_agent_workflow_panel_markers_exist(self):
        from pathlib import Path

        html = Path("static/index.html").read_text(encoding="utf-8")

        self.assertIn("function renderMultiAgentWorkflowPanel(workflow)", html)
        self.assertIn("multi_agent_workflow", html)
        self.assertIn("multiAgentWorkflowTitle", html)
        self.assertIn("Business-grounded Multi-Agent Workflow", html)
        self.assertIn("Not a plain automation", html)
        self.assertIn("agentWorkflowDecision", html)
        self.assertIn("agentWorkflowBusinessImpact", html)
        self.assertIn("agentWorkflowInputArtifacts", html)
        self.assertIn("agentWorkflowOutputArtifacts", html)
        self.assertIn("agentWorkflowHandoffTo", html)
        self.assertIn("agentHandoffMap", html)
        self.assertIn("Agent Handoff Map", html)
        self.assertIn("function renderAgentHandoffMap(orderedAgents)", html)
        self.assertIn("agentActionQueue", html)
        self.assertIn("Agent Action Queue", html)
        self.assertIn("function renderAgentActionQueue(orderedAgents)", html)
        self.assertIn("recommendedUserAction", html)
        self.assertIn("Recommended user action", html)
        self.assertIn("debugKeyOutputs", html)
        self.assertIn("Debug key outputs", html)
        self.assertIn("Legacy Debug Trace", html)
        self.assertIn("Debug scaffold for internal trace details", html)
        self.assertIn("reviewEvidenceWarningsAction", html)
        self.assertIn("confirmCreativeAngleAction", html)
        self.assertIn("reviewHookCtaScenesAction", html)
        self.assertIn("confirmProductIdentityAction", html)
        self.assertIn("generateShortClipAction", html)
        self.assertIn("copyGeminiDoubaoAction", html)
        self.assertIn("reviewPricingAction", html)
        self.assertIn("reviewUnsupportedClaimsAction", html)
        self.assertIn("createUpdateVideoJobAction", html)
        self.assertIn("pasteExternalResultAction", html)
        self.assertIn("requires_human_review", html)
        self.assertIn("confidence_score", html)
        self.assertIn("${multiAgentWorkflowPanel}", html)

    def test_multi_agent_workflow_panel_preserves_existing_video_sections(self):
        from pathlib import Path

        html = Path("static/index.html").read_text(encoding="utf-8")

        self.assertIn("renderExternalVideoToolHandoffPanel(data.external_video_tool_handoff)", html)
        self.assertIn("renderVideoDraftPanel(data.video_generation_packet)", html)
        self.assertIn("renderVideoJobControls(data)", html)
        self.assertIn("renderAgentTracePanel(data.agent_trace)", html)
        self.assertIn("function renderAgentTracePanel(agentTrace)", html)
        self.assertIn("External Video Tool Handoff", html)
        self.assertIn("Product Asset Lock", html)
        self.assertIn("Keyframe Plan", html)
        self.assertIn("Use Multi-Agent Demo Sample", html)
        self.assertIn("Video Job", html)
        self.assertIn("Provider progress", html)
        self.assertIn("External Video Experiments", html)
        self.assertIn("Estimated API cost", html)
        self.assertNotIn("????", html)


    def test_agent_status_board_frontend_markers(self):
        source = Path("static/index.html").read_text(encoding="utf-8")
        self.assertIn("function renderAgentStatusBoard(orderedAgents)", source)
        self.assertIn("agentStatusBoard", source)
        self.assertIn("Agent Status Board", source)
        self.assertIn("agentStatusBoardHint", source)
        self.assertIn("Done", source)
        self.assertIn("Active", source)
        self.assertIn("Waiting", source)
        self.assertIn("Blocked", source)
        self.assertIn("Needs review", source)
        self.assertIn("Detailed agent cards", source)
        self.assertIn("agentDetailsCollapsedNote", source)
        self.assertIn("${renderAgentStatusBoard(orderedAgents)}", source)
        self.assertNotIn("????", source)


class ProjectWorkspaceFoundationProbeTests(unittest.TestCase):
    def test_project_workspace_asset_and_registry_v2_markers_exist(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")

        for marker in [
            "Project Workspace",
            "Current project",
            "Project ID",
            "Project name",
            "Project graph summary",
            "Create project",
            "Refresh project summary",
            "Workspace Agent Graph",
            "Project node",
            "Asset node",
            "Run node",
            "Job node",
            "Experiment node",
            "Approval node",
            "Report node",
            "Product assets",
            "Upload product image",
            "Upload reference image",
            "Asset role",
            "Asset notes",
            "Uploaded assets",
            "Primary product asset",
            "Use as product identity reference",
            "Product Asset Lock v2",
            "Asset uploaded",
            "Failed to upload asset",
            "Artifact Registry v2",
            "Project-scoped artifact",
            "Parent artifact",
            "Child artifact",
            "Revision chain",
            "Supersedes",
            "Superseded by",
            "Artifact version",
            "Lineage summary",
            "Uploaded product asset",
            "Creating project...",
            "Project created",
            "Failed to create project",
            "Project summary refreshed",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)

        self.assertIn('id="projectWorkspaceRoot"', html)
        self.assertIn("function renderProjectWorkspacePanel", html)
        self.assertIn("function renderWorkspaceAgentGraph", html)
        self.assertIn("function uploadProjectAssetRequest", html)
        self.assertIn(
            "/api/v1/projects/${encodeURIComponent(projectId || 'demo_project_default')}/assets/upload",
            html,
        )
        self.assertIn("artifact_registry_v2", html)
        self.assertIn("product_asset_lock_v2", html)
        self.assertNotIn("????", html)


class ProjectSourceIntelligenceProbeTests(unittest.TestCase):
    def test_project_source_panel_and_bilingual_copy_markers_exist(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")

        for marker in [
            "Project Sources",
            "Add product source",
            "Amazon product URL",
            "Shopify product URL",
            "Manual product source",
            "Pasted customer feedback source",
            "CSV review batch",
            "Text review batch",
            "Source URL",
            "Source notes",
            "Fetch source",
            "Preview source",
            "Source created",
            "Source fetch limited",
            "Manual fallback required",
            "Source confidence",
            "Source warnings",
            "Source quality gate",
            "Evidence readiness",
            "Source evidence artifact",
            "Generate from source",
            "Recent project sources",
            "Source Evidence Timeline",
            "Quality checked",
            "Evidence Agent ready",
            "No anti-bot bypass",
            "Manual reviews recommended",
            "Source node",
            "Source adapter node",
            "Source quality node",
            "Evidence artifact node",
            "Manual fallback node",
            "ASIN",
            "Shopify handle",
            "Review classification",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)

        for marker in [
            "projectSourcesPanel",
            "projectSourceTypeInput",
            "projectSourceUrlInput",
            "projectSourceReviewsInput",
            "previewProjectSourceBtn",
            "createProjectSourceBtn",
            "projectSourceQualityPanel",
            "projectSourceTimeline",
            "function renderProjectSourcePanel",
            "function renderProjectSourceQuality",
            "function renderSourceEvidenceTimeline",
            "function projectSourcePayloadFromForm",
            "async function previewProjectSourceFromForm",
            "async function createProjectSourceFromForm",
            "async function generateProjectSourceFromWorkspace",
            "function renderArtifactSourceMetadata",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)

        self.assertIn("/sources${suffix}", html)
        self.assertIn("/sources/${encodeURIComponent(sourceId)}/generate", html)
        self.assertIn("renderProjectSourcePanel(workspace)", html)
        self.assertIn("renderProductDashboard(response.data", html)
        self.assertIn("anti-bot", html.lower())
        self.assertIn("sourceTypeAmazon", html)
        self.assertIn("sourceTypeShopify", html)
        self.assertNotIn("????", html)

    def test_project_source_ui_preserves_product_debug_boundary(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        source_panel_start = html.index("function renderProjectSourcePanel")
        source_panel_end = html.index("function renderWorkspaceAgentGraph", source_panel_start)
        source_panel = html[source_panel_start:source_panel_end]

        self.assertNotIn("data.debug", source_panel)
        self.assertNotIn("shadow_sources", source_panel)
        self.assertNotIn("memory_observability", source_panel)
        self.assertNotIn("telemetry_summary", source_panel)
        self.assertIn("currentOutputLanguage()", source_panel)


class LiveAgentGraphBoardProbeTests(unittest.TestCase):
    def test_live_agent_graph_board_frontend_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Live Agent Graph Board",
            "Graph-first view: nodes stay in place",
            "Agent graph board v2",
            "Planning lane",
            "Artifact lane",
            "Decision lane",
            "Human/provider lane",
            "Feedback loop",
            "Human approval gate",
            "Manual/provider branch",
            "Next graph action",
            "Details are collapsed by default",
            "Graph-first UI",
            "function renderLiveAgentGraphBoard(run, events)",
            "function renderLiveGraphNode(run, agentId, currentAgentId)",
            "function renderLiveGraphLane(run, labelKey, agentIds, currentAgentId)",
            "function renderLiveGraphLoopChip(labelKey, detailKey, tone = 'rework')",
            "liveAgentGraphBoard",
            "detailedAgentGraphMap",
            "Detailed Agent Graph Map",
            "riskReworkLoop",
            "Risk rework loop",
            "Planner",
            "Evidence",
            "Strategy",
            "Storyboard",
            "Risk",
            "Asset Lock",
            "Keyframe",
            "Prompt Handoff",
            "Cost",
            "Graph Router",
            "Human Approval",
            "Provider Job",
            "Experiment",
            "Finalizer",
            "${renderLiveAgentGraphBoard(run, events)}",
            "<summary>${escapeHTML(t('showDetailedGraphMap'))}: ${escapeHTML(t('detailedAgentGraphMap'))}</summary>",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_agent_graph_os_state_history_replay_and_export_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        markers = [
            "function buildLiveGraphState(run, events",
            "node_statuses",
            "selected_edges",
            "Routed by Graph Router",
            "Selected route",
            "Selected edge",
            "Primary route",
            "Secondary route",
            "Active loop",
            "Blocked reason",
            "Waiting reason",
            "Approval status",
            "Provider status",
            "Event-derived state",
            "Node state source",
            "provider_submit_blocked_by_human_approval",
            "human_approval_approved",
            "graph_router_route_selected",
            "rework_requested",
            "selected by Graph Router",
            "function renderJobAgentGraphBoard",
            "Job Agent Graph",
            "Generation result",
            "Feedback decision",
            "Rework run",
            "Revised artifacts",
            "Second experiment",
            "Decision gate",
            "Controlled approval",
            "Artifact Registry",
            "Artifact chain",
            "Source Agent",
            "Parent artifacts",
            "Used by next Agent",
            "function renderArtifactRegistry",
            "Graph explanation",
            "Why this is not a workflow",
            "Evidence of graph behavior",
            "Recent Agent Graph Runs",
            "Recent Video Jobs",
            "Recent Artifacts",
            "Recent Agent Messages",
            "Recent Graph Snapshots",
            "Artifact Timeline",
            "Refresh graph history",
            "Persistence mode",
            "Durability note",
            "Graph Replay",
            "Replay step",
            "Previous event",
            "Next event",
            "Graph Health",
            "Graph completeness",
            "Agent Message Protocol",
            "Graph State Snapshot",
            "Export graph JSON",
            "Export graph Markdown",
            "Copy graph report",
        ]
        for marker in markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)

        board_start = html.index("function renderLiveAgentGraphBoard(run, events)")
        board_end = html.index("function renderAgentLiveRunTimeline", board_start)
        board_source = html[board_start:board_end]
        self.assertIn("buildLiveGraphState(run, events", board_source)
        self.assertIn("renderLiveGraphEdge", board_source)
        self.assertIn("renderGraphReplayPanel", board_source)
        self.assertIn("renderGraphExportControls", board_source)
        self.assertIn("renderGraphHealthPanel", board_source)

        self.assertIn('<details class="section-block" id="latestAgentEventsDetails">', html)
        self.assertIn("detailedAgentGraphMap", html)
        self.assertIn("<details", html[html.index("function renderArtifactRegistry"):])
        self.assertIn("${renderJobAgentGraphBoard(job)}", html)
        self.assertNotIn("????", html)

    def test_live_agent_graph_details_are_collapsed_and_ordered(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        timeline_start = html.index("function renderAgentLiveRunTimeline(run")
        timeline_end = html.index("async function pollLiveAgentRun", timeline_start)
        timeline_source = html[timeline_start:timeline_end]

        self.assertIn('<details class="section-block" id="latestAgentEventsDetails">', timeline_source)
        self.assertIn("<summary>${escapeHTML(t('showDetailedEvents'))}", timeline_source)
        self.assertIn("<summary>${escapeHTML(t('showDetailedGraphMap'))}", timeline_source)
        self.assertLess(
            timeline_source.index("${renderLiveAgentGraphBoard(run, events)}"),
            timeline_source.index("${renderAgentGraphMap(run)}"),
        )



class SupervisorPlannerFrontendProbeTests(unittest.TestCase):
    def test_supervisor_planner_frontend_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Planner Recommendation",
            "Current project status",
            "Next best action",
            "Why this action",
            "Missing inputs",
            "Human action required",
            "Can start Agent Run",
            "Can create Video Job",
            "Can record experiment",
            "Can submit provider",
            "Planner details",
            "Source is missing",
            "Reviews are missing",
            "Product image recommended",
            "Ready for Agent Run",
            "Ready for Video Job",
            "Waiting for experiment",
            "Rework recommended",
            "Waiting for approval",
            "Provider simulation ready",
            "Export graph report",
            "Blocked reason",
            "function renderPlannerRecommendationPanel(",
            "function refreshProjectPlannerRecommendation(",
            "plannerRecommendationPanel",
            "refreshPlannerRecommendationBtn",
            "plannerRecommendationStatus",
            "/planner/recommendation/refresh",
            "${renderPlannerRecommendationPanel(planner, summary)}",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_supervisor_planner_action_wiring_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Planner action wiring",
            "Recommended action",
            "Button reason",
            "Button availability",
            "Blocked / waiting",
            "Planner says this action is available now.",
            "Planner does not recommend this action yet.",
            "Provider submit remains blocked until approval",
            "function renderPlannerActionWiringPanel(",
            "function plannerActionAvailabilityRows(",
            "plannerActionWiringPanel",
            "plannerRecommendedActionBanner",
            "plannerButtonReason",
            "plannerButtonAvailabilityList",
            "data-planner-action-row",
            "${renderPlannerActionWiringPanel(planner)}",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_supervisor_planner_public_smoke_markers(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for marker in [
            "planner_recommendation_marker",
            "planner_empty_project_needs_source",
            "planner_source_ready",
            "planner_can_start_agent_run",
            "planner_project_summary_success",
            "planner_safety_boundaries_false",
            "/planner/recommendation",
            "/planner/recommendation/refresh",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, script)



class SupervisorPlannerQuickActionFrontendTests(unittest.TestCase):
    def test_supervisor_planner_quick_action_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Go to recommended action",
            "Scrolls to the recommended area only",
            "It will not submit provider jobs or call external APIs",
            "Planner quick action",
            "function handlePlannerQuickAction()",
            "function plannerQuickActionTargets(",
            "function firstAvailablePlannerTarget(",
            "function focusPlannerQuickActionTarget(",
            "plannerQuickActionPanel",
            "plannerQuickActionBtn",
            "plannerQuickActionStatus",
            "plannerQuickActionTargetMissing",
            "plannerQuickActionMoved",
            "submit_provider_simulation",
            "export_report",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_supervisor_planner_quick_action_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("planner_quick_action_marker", script)
        self.assertIn("Go to recommended action", script)



class GeneratedWorkspaceSyncFrontendTests(unittest.TestCase):
    def test_generated_result_syncs_project_workspace_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "function syncProjectWorkspaceAfterGeneration(",
            "function queueProjectWorkspaceSyncAfterGeneration(",
            "queueProjectWorkspaceSyncAfterGeneration('generation')",
            "await syncProjectWorkspaceAfterGeneration('video_job')",
            "Syncing Project Workspace with the latest generated result",
            "Project Workspace synced with the latest generated result.",
            "Project Workspace synced with the latest Video Job.",
            "Workspace sync after generation",
            "latestProjectWorkspace = await getProjectWorkspaceSummary(latestProjectId)",
            "panel.outerHTML = renderProjectWorkspacePanel(latestProjectWorkspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_generated_workspace_sync_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("workspace_sync_after_generation_marker", script)
        self.assertIn("Workspace sync after generation", script)



class PlannerButtonStateFrontendTests(unittest.TestCase):
    def test_planner_button_state_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Planner button state",
            "Planner recommended and ready",
            "Planner recommended, waiting for prerequisite",
            "Available, but not the next recommended action",
            "Waiting on Planner prerequisite",
            "function updatePlannerButtonStateHints(",
            "function plannerButtonStateDefinitions(",
            "function plannerButtonStateText(",
            "function ensurePlannerButtonHint(",
            "planner-button-state-hint",
            "data-planner-button-state-hint",
            "data-planner-action-state",
            "data-planner-recommended",
            "plannerButtonStateHint_start_agent_run",
            "plannerButtonStateHint_create_video_job",
            "plannerButtonStateHint_record_experiment",
            "plannerButtonStateHint_submit_provider",
            "plannerButtonStateHint_export_report",
            "updatePlannerButtonStateHints(latestProjectWorkspace?.planner_recommendation || {})",
            "window.setTimeout(() => updatePlannerButtonStateHints(planner), 0)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_planner_button_state_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("planner_button_state_marker", script)
        self.assertIn("Planner button state", script)



class DownstreamWorkspaceSyncFrontendTests(unittest.TestCase):
    def test_downstream_actions_sync_project_workspace_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "function syncProjectWorkspaceAfterDownstreamAction(",
            "workspaceSyncedAfterDownstreamAction",
            "Downstream action workspace sync",
            "await syncProjectWorkspaceAfterDownstreamAction('downstream_action')",
            "latestProjectId = latestVideoGenerationJob?.project_id",
            "latestProjectId = response.job?.project_id",
            "Project Workspace synced with the latest downstream action.",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertGreaterEqual(
            html.count("await syncProjectWorkspaceAfterDownstreamAction('downstream_action')"),
            5,
        )
        self.assertNotIn("????", html)

    def test_downstream_workspace_sync_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("downstream_workspace_sync_marker", script)
        self.assertIn("Downstream action workspace sync", script)



class PlannerCleanZhOverrideFrontendTests(unittest.TestCase):
    def test_planner_workspace_clean_zh_override_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Planner clean zh override marker",
            "plannerCleanZhOverrideMarker",
            "plannerRecommendation: '\\u89c4\\u5212 Agent \\u5efa\\u8bae'",
            "plannerButtonState: 'Planner \\u6309\\u94ae\\u72b6\\u6001'",
            "plannerQuickAction: '\\u53bb\\u505a\\u63a8\\u8350\\u52a8\\u4f5c'",
            "workspaceSyncedAfterDownstreamAction: 'Project Workspace \\u5df2\\u540c\\u6b65\\u6700\\u65b0\\u4e0b\\u6e38\\u52a8\\u4f5c\\u3002'",
            "plannerAction_submit_provider_simulation: '\\u63d0\\u4ea4\\u6a21\\u62df Provider Job'",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_planner_clean_zh_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("zh_planner_clean_override_marker", script)
        self.assertIn("Planner clean zh override marker", script)



class CriticalMainZhOverrideFrontendTests(unittest.TestCase):
    def test_critical_main_zh_override_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Critical main zh override marker",
            "criticalMainZhOverrideMarker",
            "productDescriptionMode: '\\u4ea7\\u54c1\\u63cf\\u8ff0\\u6a21\\u5f0f'",
            "pastedReviewsMode: '\\u7c98\\u8d34\\u8bc4\\u8bba\\u6a21\\u5f0f'",
            "generateFromReviews: '\\u6839\\u636e\\u8bc4\\u8bba\\u751f\\u6210'",
            "copyFullMarkdown: '\\u590d\\u5236\\u5b8c\\u6574 Markdown'",
            "evidenceSnapshot: '\\u8bc1\\u636e\\u6458\\u8981'",
            "storyboard: '\\u5206\\u955c\\u811a\\u672c'",
            "evaluation: '\\u8bc4\\u4f30'",
            "sourceQualityGate: '\\u6765\\u6e90\\u8d28\\u91cf\\u95e8'",
            "submitProviderJob: '\\u63d0\\u4ea4 Provider Job'",
            "approveControlledTest: '\\u6279\\u51c6\\u53d7\\u63a7\\u6d4b\\u8bd5'",
            "4. Evaluation / &#35780;&#20272;",
            "&#31561;&#24453;&#35780;&#20272;...",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_critical_main_zh_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("critical_main_zh_override_marker", script)
        self.assertIn("Critical main zh override marker", script)



class HumanApprovalWorkspaceSyncFrontendTests(unittest.TestCase):
    def test_human_approval_syncs_project_workspace_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Human approval workspace sync",
            "workspaceSyncedAfterHumanApproval",
            "Project Workspace synced with the latest human approval decision.",
            "await syncProjectWorkspaceAfterDownstreamAction('human_approval')",
            "reason === 'human_approval'",
            "updateHumanApprovalGate(decision)",
            "humanApprovalWorkspaceSyncMarker",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_human_approval_workspace_sync_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("human_approval_workspace_sync_marker", script)
        self.assertIn("Human approval workspace sync", script)



class AgentGraphZhOverrideFrontendTests(unittest.TestCase):
    def test_agent_graph_zh_override_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Agent graph zh override marker",
            "agentGraphZhOverrideMarker",
            "agentStatusBoard: 'Agent \\u72b6\\u6001\\u770b\\u677f'",
            "agentStatusDone: '\\u5df2\\u5b8c\\u6210'",
            "agentStatusActive: '\\u8fd0\\u884c\\u4e2d'",
            "agentStatusWaiting: '\\u7b49\\u5f85\\u4e2d'",
            "agentStatusBlocked: '\\u5df2\\u963b\\u65ad'",
            "detailedAgentCards: '\\u8be6\\u7ec6 Agent \\u5361\\u7247'",
            "agentDetailsCollapsedNote: '\\u76ee\\u6807",
            "multiAgentWorkflowTitle: '\\u4e1a\\u52a1\\u7ed1\\u5b9a\\u7684\\u591a Agent",
            "agentWorkflowBusinessGoal: '\\u4e1a\\u52a1\\u76ee\\u6807'",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_agent_graph_zh_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("agent_graph_zh_override_marker", script)
        self.assertIn("Agent graph zh override marker", script)



class CopyReadyScriptZhLabelFrontendTests(unittest.TestCase):
    def test_copy_ready_script_zh_labels_are_clean(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        start = html.index("function copyReadyScriptText(data)")
        end = html.index("function renderHookHighlightCard(script)", start)
        segment = html[start:end]

        for marker in [
            "Copy-ready script zh label marker",
            "COPY_READY_SCRIPT_ZH_MARKER",
            "hook: 'Hook\\uff1a'",
            "scene: (index) => `\\u573a\\u666f ${index}\\uff1a`",
            "visual: (value) => `\\u753b\\u9762\\uff1a${value}`",
            "narration: (value) => `\\u65c1\\u767d\\uff1a${value}`",
            "cta: 'CTA\\uff1a'",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, segment)

        for bad_marker in [
            "Hook锛",
            "CTA锛",
            "鍦烘櫙",
            "鐢婚潰",
            "鏃佺櫧",
        ]:
            with self.subTest(bad_marker=bad_marker):
                self.assertNotIn(bad_marker, segment)

    def test_result_summary_zh_copy_is_clean(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        start = html.index("function resultCreativeSummary(data, sourceLabel)")
        end = html.index("function renderResultSummaryCard(data, evidence, evalData, score)", start)
        segment = html[start:end]

        for marker in [
            "\\u8fd9\\u6b21\\u521b\\u610f\\u57fa\\u4e8e ${sourceLabel} \\u751f\\u6210\\u3002",
            "\\u4e3b Hook\\uff1a${hook}",
            "\\u76ee\\u6807\\u53d7\\u4f17\\uff1a${audience}",
            "\\u98ce\\u9669\\u7b49\\u7ea7\\uff1a${riskLevel}",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, segment)

        for bad_marker in [
            "杩欐",
            "涓?Hook",
            "鐩爣",
            "椋庨櫓",
        ]:
            with self.subTest(bad_marker=bad_marker):
                self.assertNotIn(bad_marker, segment)

    def test_copy_ready_script_zh_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("copy_ready_script_zh_marker", script)
        self.assertIn("Copy-ready script zh label marker", script)


class FrontendMojibakeGuardTests(unittest.TestCase):
    def test_static_index_has_no_common_mojibake_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        mojibake_markers = [
            "锛",
            "鍦",
            "鐢",
            "鏃",
            "璇",
            "绮",
            "浜",
            "鎻",
            "鍙",
            "鐩",
            "椋",
            "瑙",
            "鏍",
            "绛",
            "€?",
            "鈥",
            "俙",
            "歖",
        ]

        for marker in mojibake_markers:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, html)

    def test_mojibake_guard_marker_exists(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        self.assertNotIn("????", html)



class WorkspaceRefreshShortcutFrontendTests(unittest.TestCase):
    def test_workspace_refresh_shortcut_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Workspace refresh shortcut",
            "workspaceRefreshShortcutMarker",
            "refreshProjectWorkspaceAndPlannerBtn",
            "refreshProjectWorkspaceAndPlannerShortcut",
            "refreshWorkspaceAndPlanner",
            "workspacePlannerRefreshWorking",
            "workspacePlannerRefreshDone",
            "workspacePlannerRefreshFailed",
            "await refreshProjectWorkspaceSummary();",
            "await refreshProjectPlannerRecommendation();",
            "Refresh Workspace + Planner",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_workspace_refresh_shortcut_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("workspace_refresh_shortcut_marker", script)
        self.assertIn("Workspace refresh shortcut", script)



class WorkspaceLastSyncTimestampFrontendTests(unittest.TestCase):
    def test_workspace_last_sync_timestamp_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Workspace last sync timestamp",
            "workspaceLastSyncTimestampMarker",
            "projectWorkspaceLastSyncStatus",
            "data-workspace-last-sync-marker",
            "data-workspace-last-sync-reason",
            "function workspaceLastSyncTimeLabel(",
            "function updateWorkspaceLastSyncTimestamp(",
            "updateWorkspaceLastSyncTimestamp(reason);",
            "updateWorkspaceLastSyncTimestamp('manual_refresh');",
            "workspaceLastSyncedAt",
            "Last synced:",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_workspace_last_sync_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("workspace_last_sync_timestamp_marker", script)
        self.assertIn("Workspace last sync timestamp", script)


class WorkspaceSyncUxBundleFrontendTests(unittest.TestCase):
    def test_workspace_sync_ux_bundle_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Workspace sync UX bundle",
            "WORKSPACE_SYNC_UX_BUNDLE_MARKER",
            "function workspaceSyncReasonLabel(",
            "function setWorkspaceSyncStatus(",
            "function markPlannerRecommendationStale(",
            "data-workspace-sync-status",
            "data-planner-stale-reason",
            "workspaceSyncReasonLabel",
            "workspaceSyncReasonGeneration",
            "workspaceSyncReasonVideoJob",
            "workspaceSyncReasonHumanApproval",
            "workspaceSyncReasonDownstreamAction",
            "workspaceSyncReasonManualRefresh",
            "workspaceSyncReasonWorkspaceSummary",
            "workspaceSyncReasonPlannerRefresh",
            "workspaceSyncStatusRefreshing",
            "workspaceSyncStatusSynced",
            "workspaceSyncStatusFailed",
            "plannerMayNeedRefresh",
            "setWorkspaceSyncStatus('refreshing', reason);",
            "setWorkspaceSyncStatus('failed', reason);",
            "setWorkspaceSyncStatus('refreshing', 'manual_refresh');",
            "setWorkspaceSyncStatus('failed', 'manual_refresh');",
            "markPlannerRecommendationStale('workspace_summary');",
            "updateWorkspaceLastSyncTimestamp('workspace_summary');",
            "updateWorkspaceLastSyncTimestamp('planner_refresh');",
            "${t('workspaceSyncReasonLabel')} ${reasonLabel}",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_workspace_sync_ux_bundle_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("workspace_sync_ux_bundle_marker", script)
        self.assertIn("Workspace sync UX bundle", script)


class VisibleUiCleanupBundleFrontendTests(unittest.TestCase):
    def test_visible_ui_cleanup_bundle_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Visible UI cleanup bundle",
            "visibleUiCleanupBundleMarker",
            "reasons people hesitate to buy",
            "Static examples, no API call",
            "1. Evidence Snapshot / &#35777;&#25454;&#25688;&#35201;",
            "2. Target Audience & Creative Strategy / &#30446;&#26631;&#21463;&#20247;&#19982;&#21019;&#24847;&#31574;&#30053;",
            "&#31561;&#24453;&#25191;&#34892;...",
            "这次创意基于 ${sourceLabel} 生成。",
            "主 Hook：${hook}",
            "目标受众：${audience}",
            "风险等级：${riskLevel}",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)

    def test_visible_ui_cleanup_removes_known_mojibake(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        bad_markers = [
            "鐢ㄦ埛鐘硅鲍",
            "闈欐€佺ず渚嬶紝",
            "璇佹嵁鎽樿",
            "鐩爣鍙椾紬",
            "绛夊緟鎵ц",
            "杩欐",
            "涓?Hook",
            "鐩爣",
            "椋庨櫓",
        ]
        for marker in bad_markers:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, html)

    def test_visible_ui_cleanup_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("visible_ui_cleanup_bundle_marker", script)
        self.assertIn("Visible UI cleanup bundle", script)


class FrontendCopyGuardHardeningBundleTests(unittest.TestCase):
    def test_frontend_copy_guard_hardening_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Frontend copy guard hardening bundle",
            "frontendCopyGuardHardeningMarker",
            "function normalizeStoryboardSceneGoal(goal, storyboard)",
            ".replace(/\\u8bc4\\u8bba\\u4e2d\\u7684\\u75db\\u70b9/g, '\\u8bc4\\u8bba\\u4e2d\\u7684\\u6838\\u5fc3\\u4fe1\\u53f7')",
            ".replace(/\\u75db\\u70b9/g, '\\u8bc4\\u8bba\\u4fe1\\u53f7')",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)

    def test_static_index_has_no_extended_mojibake_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        bad_markers = [
            "鐢ㄦ埛",
            "鐘硅鲍",
            "璐拱",
            "闈欐",
            "璇佹",
            "鎽樿",
            "鐩爣",
            "鍙椾紬",
            "绛夊緟",
            "鎵ц",
            "杩欐",
            "涓?Hook",
            "椋庨櫓",
            "鐥涚偣",
            "鏍稿績",
            "淇″彿",
        ]
        for marker in bad_markers:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, html)

    def test_frontend_copy_guard_hardening_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("frontend_copy_guard_hardening_marker", script)
        self.assertIn("Frontend copy guard hardening bundle", script)


class ProjectWorkspaceHistoryUxBundleFrontendTests(unittest.TestCase):
    def test_project_workspace_history_ux_bundle_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace history UX bundle",
            "PROJECT_WORKSPACE_HISTORY_UX_BUNDLE_MARKER",
            "function renderProjectWorkspaceHistoryQuickPanel(",
            "function renderProjectWorkspaceHistoryGroup(",
            "function projectWorkspaceHistorySummaryText(",
            "async function copyProjectWorkspaceHistorySummary(",
            "projectWorkspaceHistoryPanel",
            "projectWorkspaceHistoryStatus",
            "copyProjectWorkspaceHistoryBtn",
            "data-project-history-ux-marker",
            "data-project-history-group",
            "data-project-history-kind",
            "recentProjectRunsQuickLink",
            "recentProjectJobsQuickLink",
            "recentProjectArtifactsQuickLink",
            "recentGraphReportsQuickLink",
            "projectHistoryNoRuns",
            "projectHistoryNoJobs",
            "projectHistoryNoArtifacts",
            "projectHistoryNoReports",
            "copyProjectHistorySummary",
            "renderProjectWorkspaceHistoryQuickPanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_history_ux_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_history_ux_bundle_marker", script)
        self.assertIn("Project Workspace history UX bundle", script)

    def test_project_workspace_history_ux_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace history UX bundle", script)
        self.assertIn("project_workspace_history_ux_bundle_marker", script)


class ProjectWorkspaceActionLinksBundleFrontendTests(unittest.TestCase):
    def test_project_workspace_action_links_bundle_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace action links bundle",
            "PROJECT_WORKSPACE_ACTION_LINKS_BUNDLE_MARKER",
            "function projectWorkspaceHistoryKindKey(",
            "function projectWorkspaceHistoryActionLabel(",
            "function projectWorkspaceHistoryActionHint(",
            "function projectWorkspaceHistoryItemDetailText(",
            "async function copyProjectWorkspaceHistoryItemDetail(",
            "data-project-history-action-marker",
            "data-project-history-action-hint",
            "data-project-history-copy-action",
            "copyProjectHistoryItemDetail",
            "projectHistoryItemCopied",
            "projectHistoryJobStatus",
            "projectHistoryApprovalStatus",
            "projectHistoryProviderStatus",
            "projectHistoryJobHasResult",
            "projectHistoryRunHint",
            "projectHistoryArtifactHint",
            "projectHistoryReportHint",
            "items.map((item, index) => renderProjectWorkspaceHistoryItem(item, kind, index)).join('')",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_action_links_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_action_links_bundle_marker", script)
        self.assertIn("Project Workspace action links bundle", script)

    def test_project_workspace_action_links_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace action links bundle", script)
        self.assertIn("project_workspace_action_links_bundle_marker", script)


class ProjectWorkspaceReportReaderBundleFrontendTests(unittest.TestCase):
    def test_project_workspace_report_reader_bundle_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace report reader bundle",
            "PROJECT_WORKSPACE_REPORT_READER_BUNDLE_MARKER",
            "function projectWorkspaceReportPreviewText(",
            "function projectWorkspaceArtifactPreviewText(",
            "function projectWorkspaceJobPreviewText(",
            "function projectWorkspaceRunPreviewText(",
            "function projectWorkspaceHistoryReaderText(",
            "function renderProjectWorkspaceHistoryReaderPreview(",
            "async function copyProjectWorkspaceHistoryReaderPack(",
            "function locateProjectWorkspaceHistoryItem(",
            "data-project-history-reader-marker",
            "data-project-history-reader-kind",
            "data-project-history-reader-preview",
            "data-project-history-report-reader-item",
            "data-project-history-copy-reader-pack",
            "data-project-history-locate-action",
            "copyProjectHistoryReaderPack",
            "locateProjectHistoryItem",
            "projectHistoryReaderCopied",
            "projectHistoryItemLocated",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_report_reader_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_report_reader_bundle_marker", script)
        self.assertIn("Project Workspace report reader bundle", script)

    def test_project_workspace_report_reader_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace report reader bundle", script)
        self.assertIn("project_workspace_report_reader_bundle_marker", script)


class ProjectWorkspaceExportPackBundleFrontendTests(unittest.TestCase):
    def test_project_workspace_export_pack_bundle_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace export pack bundle",
            "PROJECT_WORKSPACE_EXPORT_PACK_BUNDLE_MARKER",
            "function projectWorkspaceExportPackMarkdownText(",
            "function projectWorkspaceExportPackJsonText(",
            "async function copyProjectWorkspaceExportPack(",
            "copyProjectWorkspaceMarkdownPack",
            "copyProjectWorkspaceJsonPack",
            "copyProjectWorkspaceMarkdownPackBtn",
            "copyProjectWorkspaceJsonPackBtn",
            'data-project-workspace-export-pack="markdown"',
            'data-project-workspace-export-pack="json"',
            "projectWorkspaceExportMarkdownCopied",
            "projectWorkspaceExportJsonCopied",
            "projectWorkspaceExportCopyFailed",
            "projectWorkspaceExportGeneratedAt",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_export_pack_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_export_pack_bundle_marker", script)
        self.assertIn("Project Workspace export pack bundle", script)

    def test_project_workspace_export_pack_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace export pack bundle", script)
        self.assertIn("project_workspace_export_pack_bundle_marker", script)


class ProjectWorkspaceRunnerPlanPanelFrontendTests(unittest.TestCase):
    def test_project_workspace_runner_plan_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace runner plan panel bundle",
            "PROJECT_WORKSPACE_RUNNER_PLAN_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceRunnerPlanPanel(",
            "async function refreshProjectWorkspaceRunnerPlan(",
            "async function copyProjectWorkspaceRunnerPlan(",
            "function projectWorkspaceRunnerPlanCopyText(",
            "function projectWorkspaceRunnerPlanStepRows(",
            "function projectWorkspaceRunnerPlanWarnings(",
            "/runner/plan/refresh",
            "projectWorkspaceRunnerPlanPanel",
            "projectWorkspaceRunnerPlanStatus",
            "refreshProjectWorkspaceRunnerPlanBtn",
            "copyProjectWorkspaceRunnerPlanBtn",
            "data-project-runner-plan-panel-marker",
            "data-runner-plan-execution-status",
            "data-runner-plan-next-agent",
            "runnerPlanPanelTitle",
            "runnerPlanDryRunHelper",
            "runnerPlanStatusWaitingForUser",
            "runnerPlanStatusBlocked",
            "renderProjectWorkspaceRunnerPlanPanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_runner_plan_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_runner_plan_panel_marker", script)
        self.assertIn("Project Workspace runner plan panel bundle", script)

    def test_project_workspace_runner_plan_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace runner plan panel bundle", script)
        self.assertIn("project_workspace_runner_plan_panel_marker", script)


class ProjectWorkspaceDispatchTicketPanelFrontendTests(unittest.TestCase):
    def test_project_workspace_dispatch_ticket_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace dispatch ticket panel bundle",
            "PROJECT_WORKSPACE_DISPATCH_TICKET_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceDispatchTicketPanel(",
            "function projectWorkspaceDispatchTicketFromWorkspace(",
            "function projectWorkspaceDispatchStatusLabel(",
            "function projectWorkspaceDispatchPreflightRows(",
            "function projectWorkspaceDispatchTicketCopyText(",
            "async function copyProjectWorkspaceDispatchTicket(",
            "latestProjectRunnerDispatchTicket = payload.runner_dispatch_ticket || {};",
            "runner_dispatch_ticket: latestProjectRunnerDispatchTicket",
            "runner_dispatch_summary: payload.runner_dispatch_summary || {}",
            "projectWorkspaceDispatchTicketPanel",
            "projectWorkspaceDispatchTicketStatus",
            "copyProjectWorkspaceDispatchTicketBtn",
            "data-project-dispatch-ticket-panel-marker",
            "data-dispatch-ticket-status",
            "data-dispatch-ticket-allowed",
            "data-dispatch-preflight-check",
            "dispatchTicketPanelTitle",
            "dispatchDryRunHelper",
            "dispatchStatusReadyToDispatch",
            "renderProjectWorkspaceDispatchTicketPanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_dispatch_ticket_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_dispatch_ticket_panel_marker", script)
        self.assertIn("Project Workspace dispatch ticket panel bundle", script)

    def test_project_workspace_dispatch_ticket_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace dispatch ticket panel bundle", script)
        self.assertIn("project_workspace_dispatch_ticket_panel_marker", script)


class ProjectWorkspaceDispatchEventPanelFrontendTests(unittest.TestCase):
    def test_project_workspace_dispatch_event_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace dispatch event panel bundle",
            "PROJECT_WORKSPACE_DISPATCH_EVENT_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceDispatchEventPanel(",
            "function projectWorkspaceDispatchEventFromWorkspace(",
            "function projectWorkspaceDispatchEventStatusLabel(",
            "function projectWorkspaceDispatchEventCopyText(",
            "async function copyProjectWorkspaceDispatchEvent(",
            "latestProjectRunnerDispatchEvent = payload.runner_dispatch_event || {};",
            "runner_dispatch_event: latestProjectRunnerDispatchEvent",
            "runner_dispatch_event_summary: payload.runner_dispatch_event_summary || {}",
            "projectWorkspaceDispatchEventPanel",
            "projectWorkspaceDispatchEventStatus",
            "copyProjectWorkspaceDispatchEventBtn",
            "data-project-dispatch-event-panel-marker",
            "data-dispatch-event-status",
            "data-dispatch-event-id",
            "data-dispatch-event-target-agent",
            "data-dispatch-event-audit-preview",
            "dispatchEventPanelTitle",
            "dispatchEventDryRunHelper",
            "dispatchEventStatusReady",
            "renderProjectWorkspaceDispatchEventPanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_dispatch_event_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_dispatch_event_panel_marker", script)
        self.assertIn("Project Workspace dispatch event panel bundle", script)

    def test_project_workspace_dispatch_event_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace dispatch event panel bundle", script)
        self.assertIn("project_workspace_dispatch_event_panel_marker", script)


class ProjectWorkspaceDispatchDryRunActionFrontendTests(unittest.TestCase):
    def test_project_workspace_dispatch_dry_run_action_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace dispatch dry-run action bundle",
            "PROJECT_WORKSPACE_DISPATCH_DRY_RUN_ACTION_BUNDLE_MARKER",
            "async function dryRunProjectWorkspaceDispatch(",
            "/runner/dispatch/dry-run",
            "dryRunProjectWorkspaceDispatchBtn",
            "data-project-dispatch-dry-run-action",
            "dryRunDispatch",
            "dispatchDryRunRunning",
            "dispatchDryRunComplete",
            "dispatchDryRunFailed",
            "runner_dispatch_ticket: latestProjectRunnerDispatchTicket",
            "runner_dispatch_event: latestProjectRunnerDispatchEvent",
            "renderProjectWorkspaceDispatchTicketPanel(latestProjectWorkspace)",
            "renderProjectWorkspaceDispatchEventPanel(latestProjectWorkspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_dispatch_dry_run_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_dispatch_dry_run_action_marker", script)
        self.assertIn("Project Workspace dispatch dry-run action bundle", script)

    def test_project_workspace_dispatch_dry_run_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace dispatch dry-run action bundle", script)
        self.assertIn("project_workspace_dispatch_dry_run_action_marker", script)


class ProjectWorkspaceExecutionReceiptPanelFrontendTests(unittest.TestCase):
    def test_project_workspace_execution_receipt_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace execution receipt panel bundle",
            "PROJECT_WORKSPACE_EXECUTION_RECEIPT_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceExecutionReceiptPanel(",
            "function projectWorkspaceExecutionReceiptFromWorkspace(",
            "function projectWorkspaceExecutionReceiptStatusLabel(",
            "function projectWorkspaceExecutionReceiptCopyText(",
            "async function copyProjectWorkspaceExecutionReceipt(",
            "async function dryRunProjectWorkspaceExecution(",
            "/runner/execute/dry-run",
            "latestProjectRunnerExecutionReceipt",
            "runner_execution_receipt: latestProjectRunnerExecutionReceipt",
            "runner_execution_receipt_summary: payload.runner_execution_receipt_summary || {}",
            "projectWorkspaceExecutionReceiptPanel",
            "projectWorkspaceExecutionReceiptStatus",
            "dryRunProjectWorkspaceExecutionBtn",
            "copyProjectWorkspaceExecutionReceiptBtn",
            "data-project-execution-receipt-panel-marker",
            "data-project-execution-dry-run-action",
            "data-execution-receipt-status",
            "data-execution-receipt-target-agent",
            "data-execution-receipt-allowed",
            "data-execution-receipt-audit-preview",
            "executionReceiptPanelTitle",
            "executionReceiptDryRunHelper",
            "renderProjectWorkspaceExecutionReceiptPanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_execution_receipt_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_execution_receipt_panel_marker", script)
        self.assertIn("Project Workspace execution receipt panel bundle", script)

    def test_project_workspace_execution_receipt_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace execution receipt panel bundle", script)
        self.assertIn("project_workspace_execution_receipt_panel_marker", script)


class ProjectWorkspaceWorkOrderPanelFrontendTests(unittest.TestCase):
    def test_project_workspace_work_order_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace work order panel bundle",
            "PROJECT_WORKSPACE_WORK_ORDER_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceWorkOrderPanel(",
            "function projectWorkspaceWorkOrderFromWorkspace(",
            "function projectWorkspaceWorkOrderStatusLabel(",
            "function projectWorkspaceWorkOrderCopyText(",
            "async function copyProjectWorkspaceWorkOrder(",
            "async function dryRunProjectWorkspaceWorkOrder(",
            "/runner/work-order/dry-run",
            "latestProjectRunnerWorkOrder",
            "runner_work_order: latestProjectRunnerWorkOrder",
            "runner_work_order_summary: payload.runner_work_order_summary || {}",
            "projectWorkspaceWorkOrderPanel",
            "projectWorkspaceWorkOrderStatus",
            "dryRunProjectWorkspaceWorkOrderBtn",
            "copyProjectWorkspaceWorkOrderBtn",
            "data-project-work-order-panel-marker",
            "data-project-work-order-dry-run-action",
            "data-work-order-status",
            "data-work-order-target-agent",
            "data-work-order-allowed",
            "data-work-order-audit-preview",
            "workOrderPanelTitle",
            "workOrderDryRunHelper",
            "renderProjectWorkspaceWorkOrderPanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_work_order_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_work_order_panel_marker", script)
        self.assertIn("Project Workspace work order panel bundle", script)

    def test_project_workspace_work_order_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace work order panel bundle", script)
        self.assertIn("project_workspace_work_order_panel_marker", script)


class ProjectWorkspaceQueueItemPanelFrontendTests(unittest.TestCase):
    def test_project_workspace_queue_item_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace queue item panel bundle",
            "PROJECT_WORKSPACE_QUEUE_ITEM_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceQueueItemPanel(",
            "function projectWorkspaceQueueItemFromWorkspace(",
            "function projectWorkspaceQueueItemStatusLabel(",
            "function projectWorkspaceQueueItemCopyText(",
            "async function copyProjectWorkspaceQueueItem(",
            "async function dryRunProjectWorkspaceQueueItem(",
            "/runner/queue/dry-run",
            "latestProjectRunnerQueueItem",
            "runner_queue_item: latestProjectRunnerQueueItem",
            "runner_queue_item_summary: payload.runner_queue_item_summary || {}",
            "projectWorkspaceQueueItemPanel",
            "projectWorkspaceQueueItemStatus",
            "dryRunProjectWorkspaceQueueItemBtn",
            "copyProjectWorkspaceQueueItemBtn",
            "data-project-queue-item-panel-marker",
            "data-project-queue-item-dry-run-action",
            "data-queue-item-status",
            "data-queue-item-id",
            "data-queue-item-enqueue-allowed",
            "data-queue-item-audit-preview",
            "queueItemPanelTitle",
            "queueDryRunHelper",
            "renderProjectWorkspaceQueueItemPanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_queue_item_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_queue_item_panel_marker", script)
        self.assertIn("Project Workspace queue item panel bundle", script)

    def test_project_workspace_queue_item_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace queue item panel bundle", script)
        self.assertIn("project_workspace_queue_item_panel_marker", script)


class ProjectWorkspaceQueueClaimPanelFrontendTests(unittest.TestCase):
    def test_project_workspace_queue_claim_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace queue claim panel bundle",
            "PROJECT_WORKSPACE_QUEUE_CLAIM_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceQueueClaimPanel(",
            "function projectWorkspaceQueueClaimFromWorkspace(",
            "function projectWorkspaceQueueClaimStatusLabel(",
            "function projectWorkspaceQueueClaimCopyText(",
            "async function copyProjectWorkspaceQueueClaim(",
            "async function dryRunProjectWorkspaceQueueClaim(",
            "/runner/claim/dry-run",
            "latestProjectRunnerQueueClaim",
            "runner_queue_claim: latestProjectRunnerQueueClaim",
            "runner_queue_claim_summary: payload.runner_queue_claim_summary || {}",
            "projectWorkspaceQueueClaimPanel",
            "projectWorkspaceQueueClaimStatus",
            "dryRunProjectWorkspaceQueueClaimBtn",
            "copyProjectWorkspaceQueueClaimBtn",
            "data-project-queue-claim-panel-marker",
            "data-project-queue-claim-dry-run-action",
            "data-queue-claim-status",
            "data-queue-claim-id",
            "data-queue-claim-allowed",
            "data-queue-claim-audit-preview",
            "queueClaimPanelTitle",
            "queueClaimDryRunHelper",
            "renderProjectWorkspaceQueueClaimPanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_queue_claim_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_queue_claim_panel_marker", script)
        self.assertIn("Project Workspace queue claim panel bundle", script)

    def test_project_workspace_queue_claim_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace queue claim panel bundle", script)
        self.assertIn("project_workspace_queue_claim_panel_marker", script)


class ProjectWorkspaceWorkerLeasePanelFrontendTests(unittest.TestCase):
    def test_project_workspace_worker_lease_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace worker lease panel bundle",
            "PROJECT_WORKSPACE_WORKER_LEASE_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceWorkerLeasePanel(",
            "function projectWorkspaceWorkerLeaseFromWorkspace(",
            "function projectWorkspaceWorkerLeaseStatusLabel(",
            "function projectWorkspaceWorkerLeaseCopyText(",
            "async function copyProjectWorkspaceWorkerLease(",
            "async function dryRunProjectWorkspaceWorkerLease(",
            "/runner/lease/dry-run",
            "latestProjectRunnerWorkerLease",
            "runner_worker_lease: latestProjectRunnerWorkerLease",
            "runner_worker_lease_summary: payload.runner_worker_lease_summary || {}",
            "projectWorkspaceWorkerLeasePanel",
            "projectWorkspaceWorkerLeaseStatus",
            "dryRunProjectWorkspaceWorkerLeaseBtn",
            "copyProjectWorkspaceWorkerLeaseBtn",
            "data-project-worker-lease-panel-marker",
            "data-project-worker-lease-dry-run-action",
            "data-worker-lease-status",
            "data-worker-lease-id",
            "data-worker-lease-allowed",
            "data-worker-lease-audit-preview",
            "workerLeasePanelTitle",
            "workerLeaseDryRunHelper",
            "renderProjectWorkspaceWorkerLeasePanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_worker_lease_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_worker_lease_panel_marker", script)
        self.assertIn("Project Workspace worker lease panel bundle", script)

    def test_project_workspace_worker_lease_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace worker lease panel bundle", script)
        self.assertIn("project_workspace_worker_lease_panel_marker", script)


class ProjectWorkspaceInvocationPanelFrontendTests(unittest.TestCase):
    def test_project_workspace_invocation_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace invocation panel bundle",
            "PROJECT_WORKSPACE_INVOCATION_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceInvocationPanel(",
            "function projectWorkspaceInvocationEnvelopeFromWorkspace(",
            "function projectWorkspaceInvocationAttemptFromWorkspace(",
            "function projectWorkspaceInvocationStatusLabel(",
            "function projectWorkspaceInvocationCopyText(",
            "async function copyProjectWorkspaceInvocation(",
            "async function dryRunProjectWorkspaceInvocation(",
            "/runner/invoke/dry-run",
            "latestProjectRunnerInvocationEnvelope",
            "latestProjectRunnerInvocationAttempt",
            "runner_invocation_envelope: latestProjectRunnerInvocationEnvelope",
            "runner_invocation_attempt: latestProjectRunnerInvocationAttempt",
            "runner_invocation_attempt_summary: payload.runner_invocation_attempt_summary || {}",
            "projectWorkspaceInvocationPanel",
            "projectWorkspaceInvocationStatus",
            "dryRunProjectWorkspaceInvocationBtn",
            "copyProjectWorkspaceInvocationBtn",
            "data-project-invocation-panel-marker",
            "data-project-invocation-dry-run-action",
            "data-invocation-attempt-status",
            "data-invocation-envelope-id",
            "data-invocation-attempt-allowed",
            "data-invocation-audit-preview",
            "invocationPanelTitle",
            "invocationDryRunHelper",
            "renderProjectWorkspaceInvocationPanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_invocation_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_invocation_panel_marker", script)
        self.assertIn("Project Workspace invocation panel bundle", script)

    def test_project_workspace_invocation_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace invocation panel bundle", script)
        self.assertIn("project_workspace_invocation_panel_marker", script)


class ProjectWorkspaceResultCompletionPanelFrontendTests(unittest.TestCase):
    def test_project_workspace_result_completion_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace result completion panel bundle",
            "PROJECT_WORKSPACE_RESULT_COMPLETION_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceResultCompletionPanel(",
            "function projectWorkspaceInvocationResultFromWorkspace(",
            "function projectWorkspaceCompletionReceiptFromWorkspace(",
            "function projectWorkspaceCompletionStatusLabel(",
            "function projectWorkspaceResultCompletionCopyText(",
            "async function copyProjectWorkspaceResultCompletion(",
            "async function dryRunProjectWorkspaceResultCompletion(",
            "/runner/result/dry-run",
            "latestProjectRunnerInvocationResult",
            "latestProjectRunnerCompletionReceipt",
            "runner_invocation_result: latestProjectRunnerInvocationResult",
            "runner_completion_receipt: latestProjectRunnerCompletionReceipt",
            "runner_completion_receipt_summary: payload.runner_completion_receipt_summary || {}",
            "projectWorkspaceResultCompletionPanel",
            "projectWorkspaceResultCompletionStatus",
            "dryRunProjectWorkspaceResultCompletionBtn",
            "copyProjectWorkspaceResultCompletionBtn",
            "data-project-result-completion-panel-marker",
            "data-project-result-completion-dry-run-action",
            "data-completion-status",
            "data-invocation-result-id",
            "data-completion-handoff-complete",
            "data-result-completion-audit-preview",
            "resultCompletionPanelTitle",
            "resultCompletionDryRunHelper",
            "renderProjectWorkspaceResultCompletionPanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_result_completion_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_result_completion_panel_marker", script)
        self.assertIn("Project Workspace result completion panel bundle", script)

    def test_project_workspace_result_completion_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace result completion panel bundle", script)
        self.assertIn("project_workspace_result_completion_panel_marker", script)


class ProjectWorkspaceHandoffCheckpointPanelFrontendTests(unittest.TestCase):
    def test_project_workspace_handoff_checkpoint_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace handoff checkpoint panel bundle",
            "PROJECT_WORKSPACE_HANDOFF_CHECKPOINT_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceHandoffCheckpointPanel(",
            "function projectWorkspaceHandoffCheckpointFromWorkspace(",
            "function projectWorkspaceNextAgentUnlockFromWorkspace(",
            "function projectWorkspaceUnlockStatusLabel(",
            "function projectWorkspaceHandoffCheckpointCopyText(",
            "async function copyProjectWorkspaceHandoffCheckpoint(",
            "async function dryRunProjectWorkspaceHandoffCheckpoint(",
            "/runner/checkpoint/dry-run",
            "latestProjectRunnerHandoffCheckpoint",
            "latestProjectRunnerNextAgentUnlock",
            "runner_handoff_checkpoint: latestProjectRunnerHandoffCheckpoint",
            "runner_next_agent_unlock: latestProjectRunnerNextAgentUnlock",
            "runner_next_agent_unlock_summary: payload.runner_next_agent_unlock_summary || {}",
            "projectWorkspaceHandoffCheckpointPanel",
            "projectWorkspaceHandoffCheckpointStatus",
            "dryRunProjectWorkspaceHandoffCheckpointBtn",
            "copyProjectWorkspaceHandoffCheckpointBtn",
            "data-project-handoff-checkpoint-panel-marker",
            "data-project-handoff-checkpoint-dry-run-action",
            "data-next-agent-unlock-status",
            "data-handoff-checkpoint-id",
            "data-next-agent-unlocked",
            "data-handoff-checkpoint-audit-preview",
            "handoffCheckpointPanelTitle",
            "handoffCheckpointDryRunHelper",
            "renderProjectWorkspaceHandoffCheckpointPanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_handoff_checkpoint_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_handoff_checkpoint_panel_marker", script)
        self.assertIn("Project Workspace handoff checkpoint panel bundle", script)

    def test_project_workspace_handoff_checkpoint_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace handoff checkpoint panel bundle", script)
        self.assertIn("project_workspace_handoff_checkpoint_panel_marker", script)


class ProjectWorkspaceTransitionProjectionPanelFrontendTests(unittest.TestCase):
    def test_project_workspace_transition_projection_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace transition projection panel bundle",
            "PROJECT_WORKSPACE_TRANSITION_PROJECTION_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceTransitionProjectionPanel(",
            "function projectWorkspaceGraphTransitionFromWorkspace(",
            "function projectWorkspaceStateProjectionFromWorkspace(",
            "function projectWorkspaceTransitionStatusLabel(",
            "function projectWorkspaceTransitionProjectionCopyText(",
            "async function copyProjectWorkspaceTransitionProjection(",
            "async function dryRunProjectWorkspaceTransitionProjection(",
            "/runner/transition/dry-run",
            "latestProjectRunnerGraphTransitionProposal",
            "latestProjectRunnerStateProjection",
            "runner_graph_transition_proposal: latestProjectRunnerGraphTransitionProposal",
            "runner_state_projection: latestProjectRunnerStateProjection",
            "runner_state_projection_summary: payload.runner_state_projection_summary || {}",
            "projectWorkspaceTransitionProjectionPanel",
            "projectWorkspaceTransitionProjectionStatus",
            "dryRunProjectWorkspaceTransitionProjectionBtn",
            "copyProjectWorkspaceTransitionProjectionBtn",
            "data-project-transition-projection-panel-marker",
            "data-project-transition-projection-dry-run-action",
            "data-graph-transition-status",
            "data-state-projection-id",
            "data-state-projection-persisted",
            "data-transition-projection-audit-preview",
            "transitionProjectionPanelTitle",
            "transitionProjectionDryRunHelper",
            "renderProjectWorkspaceTransitionProjectionPanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_transition_projection_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_transition_projection_panel_marker", script)
        self.assertIn("Project Workspace transition projection panel bundle", script)

    def test_project_workspace_transition_projection_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace transition projection panel bundle", script)
        self.assertIn("project_workspace_transition_projection_panel_marker", script)


class ProjectWorkspaceCommitPlanGuardPanelFrontendTests(unittest.TestCase):
    def test_project_workspace_commit_plan_guard_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace commit plan guard panel bundle",
            "PROJECT_WORKSPACE_COMMIT_PLAN_GUARD_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceCommitPlanGuardPanel(",
            "function projectWorkspaceTransitionCommitPlanFromWorkspace(",
            "function projectWorkspaceMutationGuardFromWorkspace(",
            "function projectWorkspaceMutationGuardStatusLabel(",
            "function projectWorkspaceCommitPlanGuardCopyText(",
            "async function copyProjectWorkspaceCommitPlanGuard(",
            "async function dryRunProjectWorkspaceCommitPlanGuard(",
            "/runner/commit-plan/dry-run",
            "latestProjectRunnerTransitionCommitPlan",
            "latestProjectRunnerMutationGuard",
            "runner_transition_commit_plan: latestProjectRunnerTransitionCommitPlan",
            "runner_mutation_guard: latestProjectRunnerMutationGuard",
            "runner_mutation_guard_summary: payload.runner_mutation_guard_summary || {}",
            "projectWorkspaceCommitPlanGuardPanel",
            "projectWorkspaceCommitPlanGuardStatus",
            "dryRunProjectWorkspaceCommitPlanGuardBtn",
            "copyProjectWorkspaceCommitPlanGuardBtn",
            "data-project-commit-plan-guard-panel-marker",
            "data-project-commit-plan-guard-dry-run-action",
            "data-mutation-guard-status",
            "data-transition-commit-plan-id",
            "data-mutation-allowed",
            "data-commit-plan-guard-audit-preview",
            "commitPlanGuardPanelTitle",
            "commitPlanGuardDryRunHelper",
            "renderProjectWorkspaceCommitPlanGuardPanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_commit_plan_guard_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_commit_plan_guard_panel_marker", script)
        self.assertIn("Project Workspace commit plan guard panel bundle", script)

    def test_project_workspace_commit_plan_guard_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace commit plan guard panel bundle", script)
        self.assertIn("project_workspace_commit_plan_guard_panel_marker", script)


class ProjectWorkspacePersistRequestRollbackPanelFrontendTests(unittest.TestCase):
    def test_project_workspace_persist_request_rollback_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace persist request rollback panel bundle",
            "PROJECT_WORKSPACE_PERSIST_REQUEST_ROLLBACK_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspacePersistRequestRollbackPanel(",
            "function projectWorkspaceTransitionPersistRequestFromWorkspace(",
            "function projectWorkspaceRollbackPlanFromWorkspace(",
            "function projectWorkspacePersistRequestStatusLabel(",
            "function projectWorkspacePersistRequestRollbackCopyText(",
            "async function copyProjectWorkspacePersistRequestRollback(",
            "async function dryRunProjectWorkspacePersistRequestRollback(",
            "/runner/persist-request/dry-run",
            "latestProjectRunnerTransitionPersistRequest",
            "latestProjectRunnerRollbackPlan",
            "runner_transition_persist_request: latestProjectRunnerTransitionPersistRequest",
            "runner_rollback_plan: latestProjectRunnerRollbackPlan",
            "runner_rollback_plan_summary: payload.runner_rollback_plan_summary || {}",
            "projectWorkspacePersistRequestRollbackPanel",
            "projectWorkspacePersistRequestRollbackStatus",
            "dryRunProjectWorkspacePersistRequestRollbackBtn",
            "copyProjectWorkspacePersistRequestRollbackBtn",
            "data-project-persist-request-rollback-panel-marker",
            "data-project-persist-request-rollback-dry-run-action",
            "data-persist-request-status",
            "data-transition-persist-request-id",
            "data-rollback-available",
            "data-persist-request-rollback-audit-preview",
            "persistRequestRollbackPanelTitle",
            "persistRequestRollbackDryRunHelper",
            "renderProjectWorkspacePersistRequestRollbackPanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_persist_request_rollback_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_persist_request_rollback_panel_marker", script)
        self.assertIn("Project Workspace persist request rollback panel bundle", script)

    def test_project_workspace_persist_request_rollback_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace persist request rollback panel bundle", script)
        self.assertIn("project_workspace_persist_request_rollback_panel_marker", script)


class ProjectWorkspacePersistGateAuditPanelFrontendTests(unittest.TestCase):
    def test_project_workspace_persist_gate_audit_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace persist gate audit panel bundle",
            "PROJECT_WORKSPACE_PERSIST_GATE_AUDIT_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspacePersistGateAuditPanel(",
            "function projectWorkspacePersistGateFromWorkspace(",
            "function projectWorkspaceAuditLedgerFromWorkspace(",
            "function projectWorkspacePersistGateStatusLabel(",
            "function projectWorkspacePersistGateAuditCopyText(",
            "async function copyProjectWorkspacePersistGateAudit(",
            "async function dryRunProjectWorkspacePersistGateAudit(",
            "/runner/persist-gate/dry-run",
            "latestProjectRunnerPersistGate",
            "latestProjectRunnerAuditLedger",
            "runner_persist_gate: latestProjectRunnerPersistGate",
            "runner_audit_ledger: latestProjectRunnerAuditLedger",
            "runner_audit_ledger_summary: payload.runner_audit_ledger_summary || {}",
            "projectWorkspacePersistGateAuditPanel",
            "projectWorkspacePersistGateAuditStatus",
            "dryRunProjectWorkspacePersistGateAuditBtn",
            "copyProjectWorkspacePersistGateAuditBtn",
            "data-project-persist-gate-audit-panel-marker",
            "data-project-persist-gate-audit-dry-run-action",
            "data-persist-gate-status",
            "data-persist-gate-id",
            "data-audit-entry-count",
            "data-persist-gate-audit-preview",
            "persistGateAuditPanelTitle",
            "persistGateAuditDryRunHelper",
            "renderProjectWorkspacePersistGateAuditPanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_persist_gate_audit_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_persist_gate_audit_panel_marker", script)
        self.assertIn("Project Workspace persist gate audit panel bundle", script)

    def test_project_workspace_persist_gate_audit_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace persist gate audit panel bundle", script)
        self.assertIn("project_workspace_persist_gate_audit_panel_marker", script)


class ProjectWorkspaceApprovalPolicyPanelFrontendTests(unittest.TestCase):
    def test_project_workspace_approval_policy_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace approval policy panel bundle",
            "PROJECT_WORKSPACE_APPROVAL_POLICY_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceApprovalPolicyPanel(",
            "function projectWorkspaceApprovalRequestFromWorkspace(",
            "function projectWorkspacePolicyDecisionFromWorkspace(",
            "function projectWorkspacePolicyDecisionStatusLabel(",
            "function projectWorkspaceApprovalPolicyCopyText(",
            "async function copyProjectWorkspaceApprovalPolicy(",
            "async function dryRunProjectWorkspaceApprovalPolicy(",
            "/runner/approval/dry-run",
            "latestProjectRunnerApprovalRequest",
            "latestProjectRunnerPolicyDecision",
            "runner_approval_request: latestProjectRunnerApprovalRequest",
            "runner_policy_decision: latestProjectRunnerPolicyDecision",
            "runner_policy_decision_summary: payload.runner_policy_decision_summary || {}",
            "projectWorkspaceApprovalPolicyPanel",
            "projectWorkspaceApprovalPolicyStatus",
            "dryRunProjectWorkspaceApprovalPolicyBtn",
            "copyProjectWorkspaceApprovalPolicyBtn",
            "data-project-approval-policy-panel-marker",
            "data-project-approval-policy-dry-run-action",
            "data-policy-decision-status",
            "data-approval-request-id",
            "data-policy-check-count",
            "data-approval-policy-audit-preview",
            "approvalPolicyPanelTitle",
            "approvalPolicyDryRunHelper",
            "renderProjectWorkspaceApprovalPolicyPanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_approval_policy_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_approval_policy_panel_marker", script)
        self.assertIn("Project Workspace approval policy panel bundle", script)

    def test_project_workspace_approval_policy_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace approval policy panel bundle", script)
        self.assertIn("project_workspace_approval_policy_panel_marker", script)


class ProjectWorkspaceAuthorizationManifestPanelFrontendTests(unittest.TestCase):
    def test_project_workspace_authorization_manifest_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace authorization manifest panel bundle",
            "PROJECT_WORKSPACE_AUTHORIZATION_MANIFEST_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceAuthorizationManifestPanel(",
            "function projectWorkspaceAuthorizationPreviewFromWorkspace(",
            "function projectWorkspaceExecutionManifestFromWorkspace(",
            "function projectWorkspaceExecutionManifestStatusLabel(",
            "function projectWorkspaceAuthorizationManifestCopyText(",
            "async function copyProjectWorkspaceAuthorizationManifest(",
            "async function dryRunProjectWorkspaceAuthorizationManifest(",
            "/runner/authorization/dry-run",
            "latestProjectRunnerAuthorizationPreview",
            "latestProjectRunnerExecutionManifest",
            "runner_authorization_preview: latestProjectRunnerAuthorizationPreview",
            "runner_execution_manifest: latestProjectRunnerExecutionManifest",
            "runner_execution_manifest_summary: payload.runner_execution_manifest_summary || {}",
            "projectWorkspaceAuthorizationManifestPanel",
            "projectWorkspaceAuthorizationManifestStatus",
            "dryRunProjectWorkspaceAuthorizationManifestBtn",
            "copyProjectWorkspaceAuthorizationManifestBtn",
            "data-project-authorization-manifest-panel-marker",
            "data-project-authorization-manifest-dry-run-action",
            "data-execution-manifest-status",
            "data-authorization-preview-id",
            "data-manifest-item-count",
            "data-authorization-manifest-audit-preview",
            "authorizationManifestPanelTitle",
            "authorizationManifestDryRunHelper",
            "renderProjectWorkspaceAuthorizationManifestPanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_authorization_manifest_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_authorization_manifest_panel_marker", script)
        self.assertIn("Project Workspace authorization manifest panel bundle", script)

    def test_project_workspace_authorization_manifest_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace authorization manifest panel bundle", script)
        self.assertIn("project_workspace_authorization_manifest_panel_marker", script)


class ProjectWorkspaceRuntimeReadinessPanelFrontendTests(unittest.TestCase):
    def test_project_workspace_runtime_readiness_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace runtime readiness panel bundle",
            "PROJECT_WORKSPACE_RUNTIME_READINESS_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceRuntimeReadinessPanel(",
            "function projectWorkspaceRuntimeReadinessCopyText(",
            "async function copyProjectWorkspaceRuntimeReadiness(",
            "async function dryRunProjectWorkspaceRuntimeReadiness(",
            "/runner/runtime-readiness/dry-run",
            "latestProjectRunnerAuthorizationPreview",
            "latestProjectRunnerExecutionManifest",
            "latestProjectRunnerExecutionSession",
            "latestProjectRunnerPreflightCertificate",
            "latestProjectRunnerRuntimeSandbox",
            "latestProjectRunnerWorkerBootstrapPlan",
            "projectWorkspaceRuntimeReadinessPanel",
            "projectWorkspaceRuntimeReadinessStatus",
            "dryRunProjectWorkspaceRuntimeReadinessBtn",
            "copyProjectWorkspaceRuntimeReadinessBtn",
            "data-project-runtime-readiness-panel-marker",
            "data-project-runtime-readiness-dry-run-action",
            "data-runtime-readiness-audit-preview",
            "runtimeReadinessPanelTitle",
            "runtimeReadinessPanelHelper",
            "renderProjectWorkspaceRuntimeReadinessPanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_runtime_readiness_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_runtime_readiness_panel_marker", script)
        self.assertIn("Project Workspace runtime readiness panel bundle", script)

    def test_project_workspace_runtime_readiness_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace runtime readiness panel bundle", script)
        self.assertIn("project_workspace_runtime_readiness_panel_marker", script)


class ProjectWorkspaceWorkerLoopPanelFrontendTests(unittest.TestCase):
    def test_project_workspace_worker_loop_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace worker loop panel bundle",
            "PROJECT_WORKSPACE_WORKER_LOOP_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceWorkerLoopPanel(",
            "function projectWorkspaceWorkerLoopCopyText(",
            "async function copyProjectWorkspaceWorkerLoop(",
            "async function dryRunProjectWorkspaceWorkerLoop(",
            "/runner/worker-loop/dry-run",
            "latestProjectRunnerWorkerPoll",
            "latestProjectRunnerWorkerHeartbeat",
            "latestProjectRunnerWorkerLoopSimulation",
            "latestProjectRunnerFailureReceipt",
            "latestProjectRunnerRetryPlan",
            "latestProjectRunnerRecoverySummary",
            "projectWorkspaceWorkerLoopPanel",
            "projectWorkspaceWorkerLoopStatus",
            "dryRunProjectWorkspaceWorkerLoopBtn",
            "copyProjectWorkspaceWorkerLoopBtn",
            "data-project-worker-loop-panel-marker",
            "data-project-worker-loop-dry-run-action",
            "data-worker-loop-audit-preview",
            "workerLoopPanelTitle",
            "workerLoopPanelHelper",
            "renderProjectWorkspaceWorkerLoopPanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_worker_loop_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_worker_loop_panel_marker", script)
        self.assertIn("Project Workspace worker loop panel bundle", script)

    def test_project_workspace_worker_loop_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace worker loop panel bundle", script)
        self.assertIn("project_workspace_worker_loop_panel_marker", script)


class ProjectWorkspaceWorkerCheckpointPanelFrontendTests(unittest.TestCase):
    def test_project_workspace_worker_checkpoint_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace worker checkpoint panel bundle",
            "PROJECT_WORKSPACE_WORKER_CHECKPOINT_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceWorkerCheckpointPanel(",
            "function projectWorkspaceWorkerCheckpointCopyText(",
            "async function copyProjectWorkspaceWorkerCheckpoint(",
            "async function dryRunProjectWorkspaceWorkerCheckpoint(",
            "/runner/worker-checkpoint/dry-run",
            "latestProjectRunnerOutputBuffer",
            "latestProjectRunnerArtifactManifest",
            "latestProjectRunnerResultValidationGate",
            "latestProjectRunnerResumeCursor",
            "latestProjectRunnerDeadLetterPolicy",
            "latestProjectRunnerWorkerCheckpointBundle",
            "projectWorkspaceWorkerCheckpointPanel",
            "projectWorkspaceWorkerCheckpointStatus",
            "dryRunProjectWorkspaceWorkerCheckpointBtn",
            "copyProjectWorkspaceWorkerCheckpointBtn",
            "data-project-worker-checkpoint-panel-marker",
            "data-project-worker-checkpoint-dry-run-action",
            "data-worker-checkpoint-audit-preview",
            "workerCheckpointPanelTitle",
            "workerCheckpointPanelHelper",
            "renderProjectWorkspaceWorkerCheckpointPanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_worker_checkpoint_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_worker_checkpoint_panel_marker", script)
        self.assertIn("Project Workspace worker checkpoint panel bundle", script)

    def test_project_workspace_worker_checkpoint_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace worker checkpoint panel bundle", script)
        self.assertIn("project_workspace_worker_checkpoint_panel_marker", script)


class ProjectWorkspaceFinalizationPanelFrontendTests(unittest.TestCase):
    def test_project_workspace_finalization_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace finalization panel bundle",
            "PROJECT_WORKSPACE_FINALIZATION_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceFinalizationPanel(",
            "function projectWorkspaceFinalizationCopyText(",
            "async function copyProjectWorkspaceFinalization(",
            "async function dryRunProjectWorkspaceFinalization(",
            "/runner/finalization/dry-run",
            "latestProjectRunnerResultAcceptance",
            "latestProjectRunnerProjectMergePreview",
            "latestProjectRunnerDownstreamHandoff",
            "latestProjectRunnerHumanReviewPacket",
            "latestProjectRunnerRunFinalization",
            "latestProjectRunnerCompletionLedger",
            "projectWorkspaceFinalizationPanel",
            "projectWorkspaceFinalizationStatus",
            "dryRunProjectWorkspaceFinalizationBtn",
            "copyProjectWorkspaceFinalizationBtn",
            "data-project-finalization-panel-marker",
            "data-project-finalization-dry-run-action",
            "data-finalization-audit-preview",
            "finalizationPanelTitle",
            "finalizationPanelHelper",
            "renderProjectWorkspaceFinalizationPanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_finalization_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_finalization_panel_marker", script)
        self.assertIn("Project Workspace finalization panel bundle", script)

    def test_project_workspace_finalization_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace finalization panel bundle", script)
        self.assertIn("project_workspace_finalization_panel_marker", script)


class ProjectWorkspaceOrchestrationReadinessPanelFrontendTests(unittest.TestCase):
    def test_project_workspace_orchestration_readiness_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace orchestration readiness panel bundle",
            "PROJECT_WORKSPACE_ORCHESTRATION_READINESS_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceOrchestrationReadinessPanel(",
            "function projectWorkspaceOrchestrationReadinessCopyText(",
            "async function copyProjectWorkspaceOrchestrationReadiness(",
            "async function dryRunProjectWorkspaceOrchestrationReadiness(",
            "/runner/orchestration-readiness/dry-run",
            "latestProjectRunnerCapabilityMatrix",
            "latestProjectRunnerBlockerMap",
            "latestProjectRunnerRealExecutionChecklist",
            "latestProjectRunnerSafetyContractSnapshot",
            "latestProjectRunnerMilestoneReport",
            "projectWorkspaceOrchestrationReadinessPanel",
            "projectWorkspaceOrchestrationReadinessStatus",
            "dryRunProjectWorkspaceOrchestrationReadinessBtn",
            "copyProjectWorkspaceOrchestrationReadinessBtn",
            "data-project-orchestration-readiness-panel-marker",
            "data-project-orchestration-readiness-dry-run-action",
            "data-orchestration-readiness-audit-preview",
            "orchestrationReadinessPanelTitle",
            "orchestrationReadinessPanelHelper",
            "renderProjectWorkspaceOrchestrationReadinessPanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_orchestration_readiness_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_orchestration_readiness_panel_marker", script)
        self.assertIn("Project Workspace orchestration readiness panel bundle", script)

    def test_project_workspace_orchestration_readiness_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace orchestration readiness panel bundle", script)
        self.assertIn("project_workspace_orchestration_readiness_panel_marker", script)


class ProjectWorkspaceOperatorControlPanelFrontendTests(unittest.TestCase):
    def test_project_workspace_operator_control_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace operator control panel bundle",
            "PROJECT_WORKSPACE_OPERATOR_CONTROL_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceOperatorControlPanel(",
            "function projectWorkspaceOperatorControlCopyText(",
            "async function copyProjectWorkspaceOperatorControl(",
            "async function dryRunProjectWorkspaceOperatorControl(",
            "/runner/operator-control/dry-run",
            "latestProjectRunnerOperatorControlCenter",
            "latestProjectRunnerHumanApprovalCapturePreview",
            "latestProjectRunnerExecutionModeSwitchPreview",
            "latestProjectRunnerProviderSandboxPreview",
            "latestProjectRunnerQuotaPolicyPreview",
            "latestProjectRunnerReleaseDecisionPacket",
            "projectWorkspaceOperatorControlPanel",
            "projectWorkspaceOperatorControlStatus",
            "dryRunProjectWorkspaceOperatorControlBtn",
            "copyProjectWorkspaceOperatorControlBtn",
            "data-project-operator-control-panel-marker",
            "data-project-operator-control-dry-run-action",
            "data-operator-control-audit-preview",
            "operatorControlPanelTitle",
            "operatorControlPanelHelper",
            "renderProjectWorkspaceOperatorControlPanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_operator_control_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_operator_control_panel_marker", script)
        self.assertIn("Project Workspace operator control panel bundle", script)

    def test_project_workspace_operator_control_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace operator control panel bundle", script)
        self.assertIn("project_workspace_operator_control_panel_marker", script)


class FrontendInteractionRecoveryTests(unittest.TestCase):
    def test_frontend_interaction_recovery_script_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Frontend interaction recovery bundle",
            "frontend-interaction-recovery-script",
            "FRONTEND_INTERACTION_RECOVERY_BUNDLE_MARKER",
            "installFrontendInteractionRecovery",
            "frontendInteractionRecoveryHealth",
            "__crossgrowthFrontendInteractionRecoveryInstalled",
            "fallbackLanguageSwitch",
            "fallbackModuleSwitch",
            "looksLikeLanguageControl",
            "looksLikeModuleControl",
            "data-frontend-interaction-recovery-marker",
            "document.addEventListener('click'",
            "document.addEventListener('change'",
            "setLanguage",
            "switchLanguage",
            "changeLanguage",
            "applyLanguage",
            "data-language",
            "data-lang",
            "data-target",
            "data-tab-target",
            "data-module-target",
            "aria-controls",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_frontend_interaction_recovery_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("frontend_interaction_recovery_marker", script)
        self.assertIn("Frontend interaction recovery bundle", script)

    def test_frontend_interaction_recovery_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Frontend interaction recovery bundle", script)
        self.assertIn("frontend_interaction_recovery_marker", script)


class FrontendInteractionBindingRepairTests(unittest.TestCase):
    def test_no_duplicate_runner_authorization_let_declarations(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        self.assertEqual(html.count("let latestProjectRunnerAuthorizationPreview = {};"), 1)
        self.assertEqual(html.count("let latestProjectRunnerExecutionManifest = {};"), 1)
        self.assertIn("Reuse latestProjectRunnerAuthorizationPreview and latestProjectRunnerExecutionManifest", html)

    def test_frontend_interaction_binding_repair_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Frontend interaction binding repair bundle",
            "frontend-interaction-binding-repair-script",
            "FRONTEND_INTERACTION_BINDING_REPAIR_MARKER",
            "installDirectBindingRepair",
            "frontendInteractionBindingRepairHealth",
            "__crossgrowthFrontendBindingRepairInstalled",
            "__crossgrowthOriginalSetLanguageMode",
            "__crossgrowthOriginalSetActiveWorkspace",
            "repairLanguageSwitch",
            "repairWorkspaceSwitch",
            "setWorkspaceDomState",
            "WORKSPACE_MAP",
            "languageEnglishBtn",
            "languageChineseBtn",
            "pathAmazonProductCard",
            "pathProductIdeaCard",
            "pathCustomerFeedbackCard",
            "pathSampleProductCard",
            "amazonProductWorkspace",
            "productIdeaWorkspace",
            "customerFeedbackWorkspace",
            "sampleProductWorkspace",
            "crossgrowth_active_workspace",
            "data-frontend-interaction-binding-repair-marker",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_frontend_script_blocks_are_syntax_checked_when_node_is_available(self):
        import re
        import shutil
        import subprocess
        import tempfile

        node = shutil.which("node")
        if not node:
            self.skipTest("node is not installed; duplicate declaration guard covers known failure")

        html = FRONTEND_PATH.read_text(encoding="utf-8")
        scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, flags=re.S | re.I)
        self.assertGreaterEqual(len(scripts), 1)

        with tempfile.TemporaryDirectory() as tmpdir:
            for index, script in enumerate(scripts):
                script_path = Path(tmpdir) / f"frontend_script_{index}.js"
                script_path.write_text(script, encoding="utf-8")
                result = subprocess.run(
                    [node, "--check", str(script_path)],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(
                    result.returncode,
                    0,
                    f"script {index} failed node --check\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}",
                )

    def test_frontend_interaction_binding_repair_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("frontend_interaction_binding_repair_marker", script)
        self.assertIn("Frontend interaction binding repair bundle", script)

    def test_frontend_interaction_binding_repair_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Frontend interaction binding repair bundle", script)
        self.assertIn("frontend_interaction_binding_repair_marker", script)


class ProjectWorkspaceOperatorApprovalPanelFrontendTests(unittest.TestCase):
    def test_project_workspace_operator_approval_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace operator approval panel bundle",
            "PROJECT_WORKSPACE_OPERATOR_APPROVAL_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceOperatorApprovalPanel(",
            "function projectWorkspaceOperatorApprovalCopyText(",
            "async function copyProjectWorkspaceOperatorApproval(",
            "async function dryRunProjectWorkspaceOperatorApproval(",
            "/runner/operator-approval/dry-run",
            "latestProjectRunnerApprovalRequestPreview",
            "latestProjectRunnerApprovalAuditTrailPreview",
            "latestProjectRunnerConsentChecklistPreview",
            "latestProjectRunnerRollbackPlaybookPreview",
            "latestProjectRunnerGuardedReleasePreview",
            "projectWorkspaceOperatorApprovalPanel",
            "projectWorkspaceOperatorApprovalStatus",
            "dryRunProjectWorkspaceOperatorApprovalBtn",
            "copyProjectWorkspaceOperatorApprovalBtn",
            "data-project-operator-approval-panel-marker",
            "data-project-operator-approval-dry-run-action",
            "data-operator-approval-audit-preview",
            "operatorApprovalPanelTitle",
            "operatorApprovalPanelHelper",
            "renderProjectWorkspaceOperatorApprovalPanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_operator_approval_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_operator_approval_panel_marker", script)
        self.assertIn("Project Workspace operator approval panel bundle", script)

    def test_project_workspace_operator_approval_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace operator approval panel bundle", script)
        self.assertIn("project_workspace_operator_approval_panel_marker", script)


class ProjectWorkspaceApprovalDecisionPanelFrontendTests(unittest.TestCase):
    def test_project_workspace_approval_decision_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace approval decision panel bundle",
            "PROJECT_WORKSPACE_APPROVAL_DECISION_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceApprovalDecisionPanel(",
            "function projectWorkspaceApprovalDecisionCopyText(",
            "async function copyProjectWorkspaceApprovalDecision(",
            "async function dryRunProjectWorkspaceApprovalDecision(",
            "/runner/approval-decision/dry-run",
            "latestProjectRunnerOperatorDecisionInputPreview",
            "latestProjectRunnerApprovalDecisionSimulator",
            "latestProjectRunnerReleaseGateStatePreview",
            "latestProjectRunnerExecutionUnlockPreview",
            "latestProjectRunnerOperatorDecisionReceiptPreview",
            "projectWorkspaceApprovalDecisionPanel",
            "projectWorkspaceApprovalDecisionStatus",
            "dryRunProjectWorkspaceApprovalDecisionBtn",
            "copyProjectWorkspaceApprovalDecisionBtn",
            "data-project-approval-decision-panel-marker",
            "data-project-approval-decision-dry-run-action",
            "data-approval-decision-audit-preview",
            "approvalDecisionPanelTitle",
            "approvalDecisionPanelHelper",
            "renderProjectWorkspaceApprovalDecisionPanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_approval_decision_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_approval_decision_panel_marker", script)
        self.assertIn("Project Workspace approval decision panel bundle", script)

    def test_project_workspace_approval_decision_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace approval decision panel bundle", script)
        self.assertIn("project_workspace_approval_decision_panel_marker", script)


class ProjectWorkspaceExecutionSandboxPanelFrontendTests(unittest.TestCase):
    def test_project_workspace_execution_sandbox_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace execution sandbox panel bundle",
            "PROJECT_WORKSPACE_EXECUTION_SANDBOX_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceExecutionSandboxPanel(",
            "function projectWorkspaceExecutionSandboxCopyText(",
            "async function copyProjectWorkspaceExecutionSandbox(",
            "async function dryRunProjectWorkspaceExecutionSandbox(",
            "/runner/execution-sandbox/dry-run",
            "latestProjectRunnerExecutionSandboxContract",
            "latestProjectRunnerProviderBoundaryPreview",
            "latestProjectRunnerSecretBoundaryPreview",
            "latestProjectRunnerQuotaLedgerPreview",
            "latestProjectRunnerCostSimulationPreview",
            "latestProjectRunnerSandboxIncidentPlanPreview",
            "latestProjectRunnerExecutionSandboxReceiptPreview",
            "projectWorkspaceExecutionSandboxPanel",
            "projectWorkspaceExecutionSandboxStatus",
            "dryRunProjectWorkspaceExecutionSandboxBtn",
            "copyProjectWorkspaceExecutionSandboxBtn",
            "data-project-execution-sandbox-panel-marker",
            "data-project-execution-sandbox-dry-run-action",
            "data-execution-sandbox-audit-preview",
            "executionSandboxPanelTitle",
            "executionSandboxPanelHelper",
            "renderProjectWorkspaceExecutionSandboxPanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_execution_sandbox_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_execution_sandbox_panel_marker", script)
        self.assertIn("Project Workspace execution sandbox panel bundle", script)

    def test_project_workspace_execution_sandbox_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace execution sandbox panel bundle", script)
        self.assertIn("project_workspace_execution_sandbox_panel_marker", script)


class ProjectWorkspaceProviderAdapterPanelFrontendTests(unittest.TestCase):
    def test_project_workspace_provider_adapter_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace provider adapter panel bundle",
            "PROJECT_WORKSPACE_PROVIDER_ADAPTER_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceProviderAdapterPanel(",
            "function projectWorkspaceProviderAdapterCopyText(",
            "async function copyProjectWorkspaceProviderAdapter(",
            "async function dryRunProjectWorkspaceProviderAdapter(",
            "/runner/provider-adapter/dry-run",
            "latestProjectRunnerProviderAdapterRegistryPreview",
            "latestProjectRunnerProviderAdapterHandshakePreview",
            "latestProjectRunnerInvocationEnvelopePreview",
            "latestProjectRunnerProviderPolicyMatrixPreview",
            "latestProjectRunnerAdapterInvocationReceiptPreview",
            "projectWorkspaceProviderAdapterPanel",
            "projectWorkspaceProviderAdapterStatus",
            "dryRunProjectWorkspaceProviderAdapterBtn",
            "copyProjectWorkspaceProviderAdapterBtn",
            "data-project-provider-adapter-panel-marker",
            "data-project-provider-adapter-dry-run-action",
            "data-provider-adapter-audit-preview",
            "providerAdapterPanelTitle",
            "providerAdapterPanelHelper",
            "renderProjectWorkspaceProviderAdapterPanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_provider_adapter_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_provider_adapter_panel_marker", script)
        self.assertIn("Project Workspace provider adapter panel bundle", script)

    def test_project_workspace_provider_adapter_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace provider adapter panel bundle", script)
        self.assertIn("project_workspace_provider_adapter_panel_marker", script)


class ProjectWorkspaceProviderInvocationPanelFrontendTests(unittest.TestCase):
    def test_project_workspace_provider_invocation_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace provider invocation panel bundle",
            "PROJECT_WORKSPACE_PROVIDER_INVOCATION_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceProviderInvocationPanel(",
            "function projectWorkspaceProviderInvocationCopyText(",
            "async function copyProjectWorkspaceProviderInvocation(",
            "async function dryRunProjectWorkspaceProviderInvocation(",
            "/runner/provider-invocation/dry-run",
            "latestProjectRunnerProviderInvocationRouterPreview",
            "latestProjectRunnerProviderInvocationStubPreview",
            "latestProjectRunnerNormalizedProviderResultPreview",
            "latestProjectRunnerProviderIdempotencyKeyPreview",
            "latestProjectRunnerProviderResultHandoffPreview",
            "latestProjectRunnerProviderInvocationAuditReceiptPreview",
            "projectWorkspaceProviderInvocationPanel",
            "projectWorkspaceProviderInvocationStatus",
            "dryRunProjectWorkspaceProviderInvocationBtn",
            "copyProjectWorkspaceProviderInvocationBtn",
            "data-project-provider-invocation-panel-marker",
            "data-project-provider-invocation-dry-run-action",
            "data-provider-invocation-audit-preview",
            "providerInvocationPanelTitle",
            "providerInvocationPanelHelper",
            "renderProjectWorkspaceProviderInvocationPanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_provider_invocation_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_provider_invocation_panel_marker", script)
        self.assertIn("Project Workspace provider invocation panel bundle", script)

    def test_project_workspace_provider_invocation_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace provider invocation panel bundle", script)
        self.assertIn("project_workspace_provider_invocation_panel_marker", script)


class ProjectWorkspaceProviderFailurePanelFrontendTests(unittest.TestCase):
    def test_project_workspace_provider_failure_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace provider failure panel bundle",
            "PROJECT_WORKSPACE_PROVIDER_FAILURE_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceProviderFailurePanel(",
            "function projectWorkspaceProviderFailureCopyText(",
            "async function copyProjectWorkspaceProviderFailure(",
            "async function dryRunProjectWorkspaceProviderFailure(",
            "/runner/provider-failure/dry-run",
            "latestProjectRunnerProviderFailureTaxonomyPreview",
            "latestProjectRunnerProviderRetryPolicyPreview",
            "latestProjectRunnerProviderFallbackPlanPreview",
            "latestProjectRunnerProviderCircuitBreakerPreview",
            "latestProjectRunnerProviderFailureRecoveryHandoffPreview",
            "latestProjectRunnerProviderFailureReceiptPreview",
            "projectWorkspaceProviderFailurePanel",
            "projectWorkspaceProviderFailureStatus",
            "dryRunProjectWorkspaceProviderFailureBtn",
            "copyProjectWorkspaceProviderFailureBtn",
            "data-project-provider-failure-panel-marker",
            "data-project-provider-failure-dry-run-action",
            "data-provider-failure-audit-preview",
            "providerFailurePanelTitle",
            "providerFailurePanelHelper",
            "renderProjectWorkspaceProviderFailurePanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_provider_failure_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_provider_failure_panel_marker", script)
        self.assertIn("Project Workspace provider failure panel bundle", script)

    def test_project_workspace_provider_failure_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace provider failure panel bundle", script)
        self.assertIn("project_workspace_provider_failure_panel_marker", script)


class ProjectWorkspaceProviderObservabilityPanelFrontendTests(unittest.TestCase):
    def test_project_workspace_provider_observability_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace provider observability panel bundle",
            "PROJECT_WORKSPACE_PROVIDER_OBSERVABILITY_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceProviderObservabilityPanel(",
            "function projectWorkspaceProviderObservabilityCopyText(",
            "async function copyProjectWorkspaceProviderObservability(",
            "async function dryRunProjectWorkspaceProviderObservability(",
            "/runner/provider-observability/dry-run",
            "latestProjectRunnerProviderHealthSnapshotPreview",
            "latestProjectRunnerProviderMetricRollupPreview",
            "latestProjectRunnerProviderAlertPolicyPreview",
            "latestProjectRunnerProviderTraceSummaryPreview",
            "latestProjectRunnerProviderObservabilityDashboardPreview",
            "latestProjectRunnerProviderObservabilityReceiptPreview",
            "projectWorkspaceProviderObservabilityPanel",
            "projectWorkspaceProviderObservabilityStatus",
            "dryRunProjectWorkspaceProviderObservabilityBtn",
            "copyProjectWorkspaceProviderObservabilityBtn",
            "data-project-provider-observability-panel-marker",
            "data-project-provider-observability-dry-run-action",
            "data-provider-observability-audit-preview",
            "providerObservabilityPanelTitle",
            "providerObservabilityPanelHelper",
            "renderProjectWorkspaceProviderObservabilityPanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_provider_observability_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_provider_observability_panel_marker", script)
        self.assertIn("Project Workspace provider observability panel bundle", script)

    def test_project_workspace_provider_observability_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace provider observability panel bundle", script)
        self.assertIn("project_workspace_provider_observability_panel_marker", script)

