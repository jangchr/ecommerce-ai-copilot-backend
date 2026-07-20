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


class ProjectWorkspaceCapabilityBindingPanelFrontendTests(unittest.TestCase):
    def test_project_workspace_capability_binding_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace capability binding panel bundle",
            "PROJECT_WORKSPACE_CAPABILITY_BINDING_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceCapabilityBindingPanel(",
            "function projectWorkspaceCapabilityBindingCopyText(",
            "async function copyProjectWorkspaceCapabilityBinding(",
            "async function dryRunProjectWorkspaceCapabilityBinding(",
            "/runner/capability-binding/dry-run",
            "latestProjectRunnerAgentCapabilityCatalogPreview",
            "latestProjectRunnerAgentToolBindingMatrixPreview",
            "latestProjectRunnerCapabilityPolicyGatePreview",
            "latestProjectRunnerToolInvocationContractPreview",
            "latestProjectRunnerCapabilityHandoffPlanPreview",
            "latestProjectRunnerCapabilityBindingReceiptPreview",
            "projectWorkspaceCapabilityBindingPanel",
            "projectWorkspaceCapabilityBindingStatus",
            "dryRunProjectWorkspaceCapabilityBindingBtn",
            "copyProjectWorkspaceCapabilityBindingBtn",
            "data-project-capability-binding-panel-marker",
            "data-project-capability-binding-dry-run-action",
            "data-capability-binding-audit-preview",
            "capabilityBindingPanelTitle",
            "capabilityBindingPanelHelper",
            "renderProjectWorkspaceCapabilityBindingPanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_capability_binding_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_capability_binding_panel_marker", script)
        self.assertIn("Project Workspace capability binding panel bundle", script)

    def test_project_workspace_capability_binding_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace capability binding panel bundle", script)
        self.assertIn("project_workspace_capability_binding_panel_marker", script)


class ProjectWorkspaceCapabilityInvocationGatePanelFrontendTests(unittest.TestCase):
    def test_project_workspace_capability_invocation_gate_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace capability invocation gate panel bundle",
            "PROJECT_WORKSPACE_CAPABILITY_INVOCATION_GATE_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceCapabilityInvocationGatePanel(",
            "function projectWorkspaceCapabilityInvocationGateCopyText(",
            "async function copyProjectWorkspaceCapabilityInvocationGate(",
            "async function dryRunProjectWorkspaceCapabilityInvocationGate(",
            "/runner/capability-invocation-gate/dry-run",
            "latestProjectRunnerCapabilityInvocationGatePreview",
            "latestProjectRunnerCapabilityInvocationRequestPreview",
            "latestProjectRunnerCapabilityInvocationDecisionPreview",
            "latestProjectRunnerCapabilityInvocationGateReceiptPreview",
            "projectWorkspaceCapabilityInvocationGatePanel",
            "projectWorkspaceCapabilityInvocationGateStatus",
            "dryRunProjectWorkspaceCapabilityInvocationGateBtn",
            "copyProjectWorkspaceCapabilityInvocationGateBtn",
            "data-project-capability-invocation-gate-panel-marker",
            "data-project-capability-invocation-gate-dry-run-action",
            "data-capability-invocation-gate-audit-preview",
            "capabilityInvocationGatePanelTitle",
            "capabilityInvocationGatePanelHelper",
            "renderProjectWorkspaceCapabilityInvocationGatePanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_capability_invocation_gate_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_capability_invocation_gate_panel_marker", script)
        self.assertIn("Project Workspace capability invocation gate panel bundle", script)

    def test_project_workspace_capability_invocation_gate_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace capability invocation gate panel bundle", script)
        self.assertIn("project_workspace_capability_invocation_gate_panel_marker", script)


class ProjectWorkspaceCapabilityInvocationRehearsalPanelFrontendTests(unittest.TestCase):
    def test_project_workspace_capability_invocation_rehearsal_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace capability invocation rehearsal panel bundle",
            "PROJECT_WORKSPACE_CAPABILITY_INVOCATION_REHEARSAL_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceCapabilityInvocationRehearsalPanel(",
            "function projectWorkspaceCapabilityInvocationRehearsalCopyText(",
            "async function copyProjectWorkspaceCapabilityInvocationRehearsal(",
            "async function dryRunProjectWorkspaceCapabilityInvocationRehearsal(",
            "/runner/capability-invocation-rehearsal/dry-run",
            "latestProjectRunnerCapabilityInvocationRuntimeRehearsalPreview",
            "latestProjectRunnerCapabilityInvocationAttemptLedgerPreview",
            "latestProjectRunnerCapabilityInvocationRehearsalReceiptPreview",
            "projectWorkspaceCapabilityInvocationRehearsalPanel",
            "projectWorkspaceCapabilityInvocationRehearsalStatus",
            "dryRunProjectWorkspaceCapabilityInvocationRehearsalBtn",
            "copyProjectWorkspaceCapabilityInvocationRehearsalBtn",
            "data-project-capability-invocation-rehearsal-panel-marker",
            "data-project-capability-invocation-rehearsal-dry-run-action",
            "data-capability-invocation-rehearsal-audit-preview",
            "capabilityInvocationRehearsalPanelTitle",
            "capabilityInvocationRehearsalPanelHelper",
            "renderProjectWorkspaceCapabilityInvocationRehearsalPanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_capability_invocation_rehearsal_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_capability_invocation_rehearsal_panel_marker", script)
        self.assertIn("Project Workspace capability invocation rehearsal panel bundle", script)

    def test_project_workspace_capability_invocation_rehearsal_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace capability invocation rehearsal panel bundle", script)
        self.assertIn("project_workspace_capability_invocation_rehearsal_panel_marker", script)


class ProjectWorkspaceCapabilityInvocationRunbookPanelFrontendTests(unittest.TestCase):
    def test_project_workspace_capability_invocation_runbook_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace capability invocation runbook panel bundle",
            "PROJECT_WORKSPACE_CAPABILITY_INVOCATION_RUNBOOK_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceCapabilityInvocationRunbookPanel(",
            "function projectWorkspaceCapabilityInvocationRunbookCopyText(",
            "async function copyProjectWorkspaceCapabilityInvocationRunbook(",
            "async function dryRunProjectWorkspaceCapabilityInvocationRunbook(",
            "/runner/capability-invocation-runbook/dry-run",
            "latestProjectRunnerCapabilityInvocationRunbookPreview",
            "latestProjectRunnerCapabilityInvocationOperatorReviewPacketPreview",
            "latestProjectRunnerCapabilityInvocationReleaseGuardPreview",
            "projectWorkspaceCapabilityInvocationRunbookPanel",
            "projectWorkspaceCapabilityInvocationRunbookStatus",
            "dryRunProjectWorkspaceCapabilityInvocationRunbookBtn",
            "copyProjectWorkspaceCapabilityInvocationRunbookBtn",
            "data-project-capability-invocation-runbook-panel-marker",
            "data-project-capability-invocation-runbook-dry-run-action",
            "data-capability-invocation-runbook-audit-preview",
            "capabilityInvocationRunbookPanelTitle",
            "capabilityInvocationRunbookPanelHelper",
            "renderProjectWorkspaceCapabilityInvocationRunbookPanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_capability_invocation_runbook_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_capability_invocation_runbook_panel_marker", script)
        self.assertIn("Project Workspace capability invocation runbook panel bundle", script)

    def test_project_workspace_capability_invocation_runbook_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace capability invocation runbook panel bundle", script)
        self.assertIn("project_workspace_capability_invocation_runbook_panel_marker", script)


class ProjectWorkspaceCapabilityInvocationReleasePacketPanelFrontendTests(unittest.TestCase):
    def test_project_workspace_capability_invocation_release_packet_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace capability invocation release packet panel bundle",
            "PROJECT_WORKSPACE_CAPABILITY_INVOCATION_RELEASE_PACKET_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceCapabilityInvocationReleasePacketPanel(",
            "function projectWorkspaceCapabilityInvocationReleasePacketCopyText(",
            "async function copyProjectWorkspaceCapabilityInvocationReleasePacket(",
            "async function dryRunProjectWorkspaceCapabilityInvocationReleasePacket(",
            "/runner/capability-invocation-release-packet/dry-run",
            "latestProjectRunnerCapabilityInvocationReleasePacketPreview",
            "latestProjectRunnerCapabilityInvocationRiskSummaryPreview",
            "latestProjectRunnerCapabilityInvocationSignoffPacketPreview",
            "latestProjectRunnerCapabilityInvocationFinalBlockedReceiptPreview",
            "projectWorkspaceCapabilityInvocationReleasePacketPanel",
            "projectWorkspaceCapabilityInvocationReleasePacketStatus",
            "dryRunProjectWorkspaceCapabilityInvocationReleasePacketBtn",
            "copyProjectWorkspaceCapabilityInvocationReleasePacketBtn",
            "data-project-capability-invocation-release-packet-panel-marker",
            "data-project-capability-invocation-release-packet-dry-run-action",
            "data-capability-invocation-release-packet-audit-preview",
            "capabilityInvocationReleasePacketPanelTitle",
            "capabilityInvocationReleasePacketPanelHelper",
            "renderProjectWorkspaceCapabilityInvocationReleasePacketPanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_capability_invocation_release_packet_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_capability_invocation_release_packet_panel_marker", script)
        self.assertIn("Project Workspace capability invocation release packet panel bundle", script)

    def test_project_workspace_capability_invocation_release_packet_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace capability invocation release packet panel bundle", script)
        self.assertIn("project_workspace_capability_invocation_release_packet_panel_marker", script)


class ProjectWorkspaceRealExecutionModeGatePanelFrontendTests(unittest.TestCase):
    def test_project_workspace_real_execution_mode_gate_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace real execution mode gate panel bundle",
            "PROJECT_WORKSPACE_REAL_EXECUTION_MODE_GATE_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceRealExecutionModeGatePanel(",
            "function projectWorkspaceRealExecutionModeGateCopyText(",
            "async function copyProjectWorkspaceRealExecutionModeGate(",
            "async function dryRunProjectWorkspaceRealExecutionModeGate(",
            "/runner/real-execution-mode-gate/dry-run",
            "latestProjectRunnerRealExecutionModeGatePreview",
            "latestProjectRunnerRealExecutionSwitchPlanPreview",
            "latestProjectRunnerRealExecutionSafetyCasePreview",
            "latestProjectRunnerRealExecutionModeReceiptPreview",
            "projectWorkspaceRealExecutionModeGatePanel",
            "projectWorkspaceRealExecutionModeGateStatus",
            "dryRunProjectWorkspaceRealExecutionModeGateBtn",
            "copyProjectWorkspaceRealExecutionModeGateBtn",
            "data-project-real-execution-mode-gate-panel-marker",
            "data-project-real-execution-mode-gate-dry-run-action",
            "data-real-execution-mode-gate-audit-preview",
            "realExecutionModeGatePanelTitle",
            "realExecutionModeGatePanelHelper",
            "renderProjectWorkspaceRealExecutionModeGatePanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_real_execution_mode_gate_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_real_execution_mode_gate_panel_marker", script)
        self.assertIn("Project Workspace real execution mode gate panel bundle", script)

    def test_project_workspace_real_execution_mode_gate_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace real execution mode gate panel bundle", script)
        self.assertIn("project_workspace_real_execution_mode_gate_panel_marker", script)


class ProjectWorkspaceRealExecutionReadinessSummaryPanelFrontendTests(unittest.TestCase):
    def test_project_workspace_real_execution_readiness_summary_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace real execution readiness summary panel bundle",
            "PROJECT_WORKSPACE_REAL_EXECUTION_READINESS_SUMMARY_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceRealExecutionReadinessSummaryPanel(",
            "function projectWorkspaceRealExecutionReadinessSummaryCopyText(",
            "async function copyProjectWorkspaceRealExecutionReadinessSummary(",
            "async function dryRunProjectWorkspaceRealExecutionReadinessSummary(",
            "/runner/real-execution-readiness-summary/dry-run",
            "latestProjectRunnerRealExecutionReadinessSummaryPreview",
            "latestProjectRunnerRealExecutionOperatorNextActionsPreview",
            "latestProjectRunnerRealExecutionExecutiveBriefPreview",
            "projectWorkspaceRealExecutionReadinessSummaryPanel",
            "projectWorkspaceRealExecutionReadinessSummaryStatus",
            "dryRunProjectWorkspaceRealExecutionReadinessSummaryBtn",
            "copyProjectWorkspaceRealExecutionReadinessSummaryBtn",
            "data-project-real-execution-readiness-summary-panel-marker",
            "data-project-real-execution-readiness-summary-dry-run-action",
            "data-real-execution-readiness-summary-audit-preview",
            "data-real-execution-go-no-go-decision",
            "realExecutionReadinessSummaryPanelTitle",
            "realExecutionReadinessSummaryPanelHelper",
            "renderProjectWorkspaceRealExecutionReadinessSummaryPanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_real_execution_readiness_summary_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_real_execution_readiness_summary_panel_marker", script)
        self.assertIn("Project Workspace real execution readiness summary panel bundle", script)

    def test_project_workspace_real_execution_readiness_summary_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace real execution readiness summary panel bundle", script)
        self.assertIn("project_workspace_real_execution_readiness_summary_panel_marker", script)


class ProjectWorkspaceRealExecutionApprovalRequestPanelFrontendTests(unittest.TestCase):
    def test_project_workspace_real_execution_approval_request_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace real execution approval request panel bundle",
            "PROJECT_WORKSPACE_REAL_EXECUTION_APPROVAL_REQUEST_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceRealExecutionApprovalRequestPanel(",
            "function projectWorkspaceRealExecutionApprovalRequestCopyText(",
            "async function copyProjectWorkspaceRealExecutionApprovalRequest(",
            "async function dryRunProjectWorkspaceRealExecutionApprovalRequest(",
            "/runner/real-execution-approval-request/dry-run",
            "latestProjectRunnerRealExecutionApprovalRequestDraftPreview",
            "latestProjectRunnerRealExecutionApprovalFormSchemaPreview",
            "latestProjectRunnerRealExecutionApprovalReviewQueuePreview",
            "latestProjectRunnerRealExecutionApprovalRequestReceiptPreview",
            "projectWorkspaceRealExecutionApprovalRequestPanel",
            "projectWorkspaceRealExecutionApprovalRequestStatus",
            "dryRunProjectWorkspaceRealExecutionApprovalRequestBtn",
            "copyProjectWorkspaceRealExecutionApprovalRequestBtn",
            "data-project-real-execution-approval-request-panel-marker",
            "data-project-real-execution-approval-request-dry-run-action",
            "data-real-execution-approval-request-audit-preview",
            "realExecutionApprovalRequestPanelTitle",
            "realExecutionApprovalRequestPanelHelper",
            "renderProjectWorkspaceRealExecutionApprovalRequestPanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_real_execution_approval_request_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_real_execution_approval_request_panel_marker", script)
        self.assertIn("Project Workspace real execution approval request panel bundle", script)

    def test_project_workspace_real_execution_approval_request_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace real execution approval request panel bundle", script)
        self.assertIn("project_workspace_real_execution_approval_request_panel_marker", script)


class ProjectWorkspaceRealExecutionApprovalDecisionPanelFrontendTests(unittest.TestCase):
    def test_project_workspace_real_execution_approval_decision_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace real execution approval decision panel bundle",
            "PROJECT_WORKSPACE_REAL_EXECUTION_APPROVAL_DECISION_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceRealExecutionApprovalDecisionPanel(",
            "function projectWorkspaceRealExecutionApprovalDecisionCopyText(",
            "async function copyProjectWorkspaceRealExecutionApprovalDecision(",
            "async function dryRunProjectWorkspaceRealExecutionApprovalDecision(",
            "/runner/real-execution-approval-decision/dry-run",
            "latestProjectRunnerRealExecutionApprovalDecisionPreview",
            "latestProjectRunnerRealExecutionDecisionLedgerPreview",
            "latestProjectRunnerRealExecutionDeniedReceiptPreview",
            "projectWorkspaceRealExecutionApprovalDecisionPanel",
            "projectWorkspaceRealExecutionApprovalDecisionStatus",
            "dryRunProjectWorkspaceRealExecutionApprovalDecisionBtn",
            "copyProjectWorkspaceRealExecutionApprovalDecisionBtn",
            "data-project-real-execution-approval-decision-panel-marker",
            "data-project-real-execution-approval-decision-dry-run-action",
            "data-real-execution-approval-decision-audit-preview",
            "realExecutionApprovalDecisionPanelTitle",
            "realExecutionApprovalDecisionPanelHelper",
            "renderProjectWorkspaceRealExecutionApprovalDecisionPanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_real_execution_approval_decision_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_real_execution_approval_decision_panel_marker", script)
        self.assertIn("Project Workspace real execution approval decision panel bundle", script)

    def test_project_workspace_real_execution_approval_decision_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace real execution approval decision panel bundle", script)
        self.assertIn("project_workspace_real_execution_approval_decision_panel_marker", script)


class ProjectWorkspaceRealExecutionLaunchAuthorizationPanelFrontendTests(unittest.TestCase):
    def test_project_workspace_real_execution_launch_authorization_panel_markers(self):
        html = FRONTEND_PATH.read_text(encoding="utf-8")
        for marker in [
            "Project Workspace real execution launch authorization panel bundle",
            "PROJECT_WORKSPACE_REAL_EXECUTION_LAUNCH_AUTHORIZATION_PANEL_BUNDLE_MARKER",
            "function renderProjectWorkspaceRealExecutionLaunchAuthorizationPanel(",
            "function projectWorkspaceRealExecutionLaunchAuthorizationCopyText(",
            "async function copyProjectWorkspaceRealExecutionLaunchAuthorization(",
            "async function dryRunProjectWorkspaceRealExecutionLaunchAuthorization(",
            "/runner/real-execution-launch-authorization/dry-run",
            "latestProjectRunnerRealExecutionLaunchAuthorizationPreview",
            "latestProjectRunnerRealExecutionLaunchLockPreview",
            "latestProjectRunnerRealExecutionLaunchDenialReceiptPreview",
            "projectWorkspaceRealExecutionLaunchAuthorizationPanel",
            "projectWorkspaceRealExecutionLaunchAuthorizationStatus",
            "dryRunProjectWorkspaceRealExecutionLaunchAuthorizationBtn",
            "copyProjectWorkspaceRealExecutionLaunchAuthorizationBtn",
            "data-project-real-execution-launch-authorization-panel-marker",
            "data-project-real-execution-launch-authorization-dry-run-action",
            "data-real-execution-launch-authorization-audit-preview",
            "realExecutionLaunchAuthorizationPanelTitle",
            "realExecutionLaunchAuthorizationPanelHelper",
            "renderProjectWorkspaceRealExecutionLaunchAuthorizationPanel(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertNotIn("????", html)

    def test_project_workspace_real_execution_launch_authorization_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_real_execution_launch_authorization_panel_marker", script)
        self.assertIn("Project Workspace real execution launch authorization panel bundle", script)

    def test_project_workspace_real_execution_launch_authorization_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace real execution launch authorization panel bundle", script)
        self.assertIn("project_workspace_real_execution_launch_authorization_panel_marker", script)


    def test_project_workspace_real_execution_safety_timeline_bundle_markers(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        self.assertIn("Project Workspace real execution safety timeline bundle", html)
        self.assertIn("PROJECT_WORKSPACE_REAL_EXECUTION_SAFETY_TIMELINE_BUNDLE_MARKER", html)
        self.assertIn("renderProjectWorkspaceRealExecutionSafetyTimelinePanel", html)
        self.assertIn("copyProjectWorkspaceRealExecutionSafetyTimeline", html)

    def test_project_workspace_real_execution_safety_timeline_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_real_execution_safety_timeline_marker", script)
        self.assertIn("Project Workspace real execution safety timeline bundle", script)

    def test_project_workspace_real_execution_safety_timeline_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace real execution safety timeline bundle", script)
        self.assertIn("project_workspace_real_execution_safety_timeline_marker", script)


    def test_project_workspace_export_pack_safety_timeline_bundle_markers(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        self.assertIn("Project Workspace export pack safety timeline bundle", html)
        self.assertIn("PROJECT_WORKSPACE_EXPORT_PACK_SAFETY_TIMELINE_BUNDLE_MARKER", html)
        self.assertIn("projectWorkspaceExportSafetyTimelineSnapshot", html)
        self.assertIn("projectWorkspaceExportSafetyTimelineMarkdown", html)
        self.assertIn("real_execution_safety_timeline", html)
    def test_project_workspace_export_pack_safety_timeline_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_export_pack_safety_timeline_marker", script)
        self.assertIn("Project Workspace export pack safety timeline bundle", script)
    def test_project_workspace_export_pack_safety_timeline_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace export pack safety timeline bundle", script)
        self.assertIn("project_workspace_export_pack_safety_timeline_marker", script)

    def test_project_workspace_runner_event_ledger_summary_bundle_markers(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        self.assertIn("Project Workspace runner event ledger summary bundle", html)
        self.assertIn("PROJECT_WORKSPACE_RUNNER_EVENT_LEDGER_SUMMARY_BUNDLE_MARKER", html)
        self.assertIn("renderProjectWorkspaceRunnerEventLedgerSummaryPanel", html)
        self.assertIn("copyProjectWorkspaceRunnerEventLedgerSummary", html)
        self.assertIn("runner_event_ledger_summary", html)

    def test_project_workspace_runner_event_ledger_summary_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_runner_event_ledger_summary_marker", script)
        self.assertIn("Project Workspace runner event ledger summary bundle", script)

    def test_project_workspace_runner_event_ledger_summary_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace runner event ledger summary bundle", script)
        self.assertIn("project_workspace_runner_event_ledger_summary_marker", script)

    def test_project_workspace_supervisor_event_ledger_decision_bundle_markers(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        self.assertIn("Project Workspace supervisor event ledger decision bundle", html)
        self.assertIn("PROJECT_WORKSPACE_SUPERVISOR_EVENT_LEDGER_DECISION_BUNDLE_MARKER", html)
        self.assertIn("renderProjectWorkspaceSupervisorEventLedgerDecisionPanel", html)
        self.assertIn("copyProjectWorkspaceSupervisorEventLedgerDecision", html)
        self.assertIn("runner_supervisor_event_ledger_decision_summary", html)

    def test_project_workspace_supervisor_event_ledger_decision_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_supervisor_event_ledger_decision_marker", script)
        self.assertIn("Project Workspace supervisor event ledger decision bundle", script)

    def test_project_workspace_supervisor_event_ledger_decision_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace supervisor event ledger decision bundle", script)
        self.assertIn("project_workspace_supervisor_event_ledger_decision_marker", script)

    def test_project_workspace_supervisor_next_step_routing_plan_bundle_markers(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        self.assertIn("Project Workspace supervisor next-step routing plan bundle", html)
        self.assertIn("PROJECT_WORKSPACE_SUPERVISOR_NEXT_STEP_ROUTING_PLAN_BUNDLE_MARKER", html)
        self.assertIn("renderProjectWorkspaceSupervisorNextStepRoutingPlanPanel", html)
        self.assertIn("copyProjectWorkspaceSupervisorNextStepRoutingPlan", html)
        self.assertIn("runner_supervisor_next_step_routing_plan", html)

    def test_project_workspace_supervisor_next_step_routing_plan_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_supervisor_next_step_routing_plan_marker", script)
        self.assertIn("Project Workspace supervisor next-step routing plan bundle", script)

    def test_project_workspace_supervisor_next_step_routing_plan_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace supervisor next-step routing plan bundle", script)
        self.assertIn("project_workspace_supervisor_next_step_routing_plan_marker", script)

    def test_project_workspace_supervisor_next_step_work_order_preview_bundle_markers(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        self.assertIn("Project Workspace supervisor next-step work order preview bundle", html)
        self.assertIn("PROJECT_WORKSPACE_SUPERVISOR_NEXT_STEP_WORK_ORDER_PREVIEW_BUNDLE_MARKER", html)
        self.assertIn("renderProjectWorkspaceSupervisorNextStepWorkOrderPreviewPanel", html)
        self.assertIn("copyProjectWorkspaceSupervisorNextStepWorkOrderPreview", html)
        self.assertIn("runner_supervisor_next_step_work_order_preview", html)

    def test_project_workspace_supervisor_next_step_work_order_preview_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_supervisor_next_step_work_order_preview_marker", script)
        self.assertIn("Project Workspace supervisor next-step work order preview bundle", script)

    def test_project_workspace_supervisor_next_step_work_order_preview_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace supervisor next-step work order preview bundle", script)
        self.assertIn("project_workspace_supervisor_next_step_work_order_preview_marker", script)

    def test_project_workspace_queue_lease_worker_dry_run_chain_bundle_markers(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        self.assertIn("Project Workspace queue lease worker dry-run chain bundle", html)
        self.assertIn("PROJECT_WORKSPACE_QUEUE_LEASE_WORKER_DRY_RUN_CHAIN_BUNDLE_MARKER", html)
        self.assertIn("renderProjectWorkspaceQueueLeaseWorkerDryRunChainPanel", html)
        self.assertIn("copyProjectWorkspaceQueueLeaseWorkerDryRunChain", html)
        self.assertIn("runner_queue_lease_worker_dry_run_chain", html)

    def test_project_workspace_queue_lease_worker_dry_run_chain_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_queue_lease_worker_dry_run_chain_marker", script)
        self.assertIn("Project Workspace queue lease worker dry-run chain bundle", script)

    def test_project_workspace_queue_lease_worker_dry_run_chain_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace queue lease worker dry-run chain bundle", script)
        self.assertIn("project_workspace_queue_lease_worker_dry_run_chain_marker", script)

    def test_project_workspace_agent_contract_registry_bundle_markers(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        self.assertIn("Project Workspace agent contract registry bundle", html)
        self.assertIn("PROJECT_WORKSPACE_AGENT_CONTRACT_REGISTRY_BUNDLE_MARKER", html)
        self.assertIn("renderProjectWorkspaceAgentContractRegistryPanel", html)
        self.assertIn("copyProjectWorkspaceAgentContractRegistry", html)
        self.assertIn("agent_contract_completeness_report", html)

    def test_project_workspace_agent_contract_registry_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_agent_contract_registry_marker", script)
        self.assertIn("Project Workspace agent contract registry bundle", script)

    def test_project_workspace_agent_contract_registry_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace agent contract registry bundle", script)
        self.assertIn("project_workspace_agent_contract_registry_marker", script)

    def test_project_workspace_source_adapter_contract_bundle_markers(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        self.assertIn("Project Workspace source adapter contract bundle", html)
        self.assertIn("PROJECT_WORKSPACE_SOURCE_ADAPTER_CONTRACT_BUNDLE_MARKER", html)
        self.assertIn("renderProjectWorkspaceSourceAdapterContractPanel", html)
        self.assertIn("copyProjectWorkspaceSourceAdapterContract", html)
        self.assertIn("source_adapter_contract_report", html)

    def test_project_workspace_source_adapter_contract_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_source_adapter_contract_marker", script)
        self.assertIn("Project Workspace source adapter contract bundle", script)

    def test_project_workspace_source_adapter_contract_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace source adapter contract bundle", script)
        self.assertIn("project_workspace_source_adapter_contract_marker", script)

    def test_project_workspace_multi_agent_output_chain_bundle_markers(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        self.assertIn("Project Workspace multi-agent output chain bundle", html)
        self.assertIn("PROJECT_WORKSPACE_MULTI_AGENT_OUTPUT_CHAIN_BUNDLE_MARKER", html)
        self.assertIn("renderProjectWorkspaceMultiAgentOutputChainPanel", html)
        self.assertIn("copyProjectWorkspaceMultiAgentOutputChain", html)
        self.assertIn("multi_agent_output_chain_report", html)

    def test_project_workspace_multi_agent_output_chain_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_multi_agent_output_chain_marker", script)
        self.assertIn("Project Workspace multi-agent output chain bundle", script)

    def test_project_workspace_multi_agent_output_chain_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace multi-agent output chain bundle", script)
        self.assertIn("project_workspace_multi_agent_output_chain_marker", script)

import re as _cg_invalid_unicode_re
from pathlib import Path as _CgInvalidUnicodePath
import unittest as _cg_invalid_unicode_unittest


class FrontendInvalidUnicodeEscapeTests(_cg_invalid_unicode_unittest.TestCase):
    def test_project_workspace_keyframe_video_asset_chain_bundle_markers(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        self.assertIn("Project Workspace keyframe video asset chain bundle", html)
        self.assertIn("PROJECT_WORKSPACE_KEYFRAME_VIDEO_ASSET_CHAIN_BUNDLE_MARKER", html)
        self.assertIn("renderProjectWorkspaceKeyframeVideoAssetChainPanel", html)
        self.assertIn("copyProjectWorkspaceKeyframeVideoAssetChain", html)
        self.assertIn("keyframe_video_asset_chain_report", html)

    def test_project_workspace_keyframe_video_asset_chain_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_keyframe_video_asset_chain_marker", script)
        self.assertIn("Project Workspace keyframe video asset chain bundle", script)

    def test_project_workspace_keyframe_video_asset_chain_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace keyframe video asset chain bundle", script)
        self.assertIn("project_workspace_keyframe_video_asset_chain_marker", script)


    def test_project_workspace_keyframe_prompt_pack_bundle_markers(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        self.assertIn("Project Workspace keyframe prompt pack bundle", html)
        self.assertIn("PROJECT_WORKSPACE_KEYFRAME_PROMPT_PACK_BUNDLE_MARKER", html)
        self.assertIn("renderProjectWorkspaceKeyframePromptPackPanel", html)
        self.assertIn("copyProjectWorkspaceKeyframePromptPack", html)
        self.assertIn("copyProjectWorkspaceKeyframePromptShot", html)
        self.assertIn("copyProjectWorkspaceKeyframeProviderPrompt", html)
        self.assertIn("keyframe_prompt_pack_report", html)
        self.assertIn("projectWorkspaceExportKeyframePromptPackMarkdown", html)
        self.assertIn("projectWorkspaceExportKeyframePromptPackSnapshot", html)

    def test_project_workspace_keyframe_prompt_pack_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_keyframe_prompt_pack_marker", script)
        self.assertIn("Project Workspace keyframe prompt pack bundle", script)

    def test_project_workspace_keyframe_prompt_pack_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace keyframe prompt pack bundle", script)
        self.assertIn("project_workspace_keyframe_prompt_pack_marker", script)


    def test_project_workspace_manual_generation_result_bundle_markers(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        self.assertIn("Project Workspace manual generation result bundle", html)
        self.assertIn("PROJECT_WORKSPACE_MANUAL_GENERATION_RESULT_BUNDLE_MARKER", html)
        self.assertIn("renderProjectWorkspaceManualGenerationResultPanel", html)
        self.assertIn("copyProjectWorkspaceManualGenerationResult", html)
        self.assertIn("manual_generation_result_report", html)
        self.assertIn("projectWorkspaceExportManualGenerationResultMarkdown", html)
        self.assertIn("projectWorkspaceExportManualGenerationResultSnapshot", html)
        self.assertIn("result_url_fetched", html)
        self.assertIn("product_drift_checklist", html)
        self.assertIn("evidence_consistency_checklist", html)
        self.assertIn("rework_recommendation_rules", html)

    def test_project_workspace_manual_generation_result_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_manual_generation_result_marker", script)
        self.assertIn("Project Workspace manual generation result bundle", script)

    def test_project_workspace_manual_generation_result_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace manual generation result bundle", script)
        self.assertIn("project_workspace_manual_generation_result_marker", script)


    def test_project_workspace_provider_api_readiness_bundle_markers(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        self.assertIn("Project Workspace provider API readiness bundle", html)
        self.assertIn("PROJECT_WORKSPACE_PROVIDER_API_READINESS_BUNDLE_MARKER", html)
        self.assertIn("renderProjectWorkspaceProviderApiReadinessPanel", html)
        self.assertIn("copyProjectWorkspaceProviderApiReadiness", html)
        self.assertIn("provider_api_readiness_report", html)
        self.assertIn("projectWorkspaceExportProviderApiReadinessMarkdown", html)
        self.assertIn("projectWorkspaceExportProviderApiReadinessSnapshot", html)
        self.assertIn("provider_contracts", html)
        self.assertIn("api_key_boundary", html)
        self.assertIn("async_job_schema", html)
        self.assertIn("polling_contract", html)
        self.assertIn("failure_handling_contract", html)
        self.assertIn("provider_secret_read", html)
        self.assertIn("provider_job_submitted", html)

    def test_project_workspace_provider_api_readiness_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_provider_api_readiness_marker", script)
        self.assertIn("Project Workspace provider API readiness bundle", script)

    def test_project_workspace_provider_api_readiness_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace provider API readiness bundle", script)
        self.assertIn("project_workspace_provider_api_readiness_marker", script)


    def test_project_workspace_provider_sandbox_runtime_bundle_markers(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        self.assertIn("Project Workspace provider sandbox runtime bundle", html)
        self.assertIn("PROJECT_WORKSPACE_PROVIDER_SANDBOX_RUNTIME_BUNDLE_MARKER", html)
        self.assertIn("renderProjectWorkspaceProviderSandboxRuntimePanel", html)
        self.assertIn("copyProjectWorkspaceProviderSandboxRuntime", html)
        self.assertIn("provider_sandbox_runtime_report", html)
        self.assertIn("projectWorkspaceExportProviderSandboxRuntimeMarkdown", html)
        self.assertIn("projectWorkspaceExportProviderSandboxRuntimeSnapshot", html)
        self.assertIn("fake_runtime_matrix", html)
        self.assertIn("submit_contract", html)
        self.assertIn("polling_contract", html)
        self.assertIn("normalized_result_contract", html)
        self.assertIn("result_handoff_contract", html)
        self.assertIn("fake_no_network", html)
        self.assertIn("external_api_called", html)
        self.assertIn("real_provider_client_constructed", html)

    def test_project_workspace_provider_sandbox_runtime_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_provider_sandbox_runtime_marker", script)
        self.assertIn("Project Workspace provider sandbox runtime bundle", script)

    def test_project_workspace_provider_sandbox_runtime_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace provider sandbox runtime bundle", script)
        self.assertIn("project_workspace_provider_sandbox_runtime_marker", script)


    def test_project_workspace_real_provider_execution_gate_bundle_markers(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        self.assertIn("Project Workspace real provider execution gate bundle", html)
        self.assertIn("PROJECT_WORKSPACE_REAL_PROVIDER_EXECUTION_GATE_BUNDLE_MARKER", html)
        self.assertIn("renderProjectWorkspaceRealProviderExecutionGatePanel", html)
        self.assertIn("copyProjectWorkspaceRealProviderExecutionGate", html)
        self.assertIn("real_provider_execution_gate_report", html)
        self.assertIn("projectWorkspaceExportRealProviderExecutionGateMarkdown", html)
        self.assertIn("projectWorkspaceExportRealProviderExecutionGateSnapshot", html)
        self.assertIn("credential_preflight", html)
        self.assertIn("quota_budget_gate", html)
        self.assertIn("approval_gate", html)
        self.assertIn("invocation_contract", html)
        self.assertIn("dry_run_receipt", html)
        self.assertIn("blocking_failures", html)
        self.assertIn("real_provider_client_constructed", html)
        self.assertIn("external_api_called", html)

    def test_project_workspace_real_provider_execution_gate_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_real_provider_execution_gate_marker", script)
        self.assertIn("Project Workspace real provider execution gate bundle", script)

    def test_project_workspace_real_provider_execution_gate_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace real provider execution gate bundle", script)
        self.assertIn("project_workspace_real_provider_execution_gate_marker", script)


    def test_project_workspace_provider_failure_recovery_bundle_markers(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        self.assertIn("Project Workspace provider failure recovery bundle", html)
        self.assertIn("PROJECT_WORKSPACE_PROVIDER_FAILURE_RECOVERY_BUNDLE_MARKER", html)
        self.assertIn("renderProjectWorkspaceProviderFailureRecoveryPanel", html)
        self.assertIn("copyProjectWorkspaceProviderFailureRecovery", html)
        self.assertIn("provider_failure_recovery_report", html)
        self.assertIn("projectWorkspaceExportProviderFailureRecoveryMarkdown", html)
        self.assertIn("projectWorkspaceExportProviderFailureRecoverySnapshot", html)
        self.assertIn("failure_taxonomy", html)
        self.assertIn("retry_policy", html)
        self.assertIn("fallback_plan", html)
        self.assertIn("circuit_breaker", html)
        self.assertIn("incident_policy", html)
        self.assertIn("alert_policy", html)
        self.assertIn("operator_review_packet", html)
        self.assertIn("rollback_pause_policy", html)
        self.assertIn("dry_run_receipt", html)
        self.assertIn("real_retry_performed", html)
        self.assertIn("block_followup_real_execution", html)
        self.assertIn("external_api_called", html)

    def test_project_workspace_provider_failure_recovery_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_provider_failure_recovery_marker", script)
        self.assertIn("Project Workspace provider failure recovery bundle", script)

    def test_project_workspace_provider_failure_recovery_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace provider failure recovery bundle", script)
        self.assertIn("project_workspace_provider_failure_recovery_marker", script)


    def test_project_workspace_provider_observability_report_bundle_markers(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        self.assertIn("Project Workspace provider observability report bundle", html)
        self.assertIn("PROJECT_WORKSPACE_PROVIDER_OBSERVABILITY_REPORT_BUNDLE_MARKER", html)
        self.assertIn("renderProjectWorkspaceProviderObservabilityReportPanel", html)
        self.assertIn("copyProjectWorkspaceProviderObservabilityReport", html)
        self.assertIn("provider_observability_report", html)
        self.assertIn("projectWorkspaceExportProviderObservabilityReportMarkdown", html)
        self.assertIn("projectWorkspaceExportProviderObservabilityReportSnapshot", html)
        self.assertIn("health_snapshot", html)
        self.assertIn("metric_rollup", html)
        self.assertIn("alert_policy", html)
        self.assertIn("trace_summary", html)
        self.assertIn("operator_control_center", html)
        self.assertIn("dashboard_cards", html)
        self.assertIn("observability_receipt", html)
        self.assertIn("audit_preview_ready", html)
        self.assertIn("real_observability_backend_enabled", html)
        self.assertIn("real_alert_delivery_enabled", html)
        self.assertIn("real_metrics_persisted", html)
        self.assertIn("real_trace_persisted", html)
        self.assertIn("external_api_called", html)

    def test_project_workspace_provider_observability_report_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_provider_observability_report_marker", script)
        self.assertIn("Project Workspace provider observability report bundle", script)

    def test_project_workspace_provider_observability_report_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace provider observability report bundle", script)
        self.assertIn("project_workspace_provider_observability_report_marker", script)


    def test_project_workspace_provider_queue_lease_worker_bundle_markers(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        self.assertIn("Project Workspace provider queue lease worker bundle", html)
        self.assertIn("PROJECT_WORKSPACE_PROVIDER_QUEUE_LEASE_WORKER_BUNDLE_MARKER", html)
        self.assertIn("renderProjectWorkspaceProviderQueueLeaseWorkerPanel", html)
        self.assertIn("copyProjectWorkspaceProviderQueueLeaseWorker", html)
        self.assertIn("provider_queue_lease_worker_report", html)
        self.assertIn("projectWorkspaceExportProviderQueueLeaseWorkerMarkdown", html)
        self.assertIn("projectWorkspaceExportProviderQueueLeaseWorkerSnapshot", html)
        self.assertIn("queue_model", html)
        self.assertIn("idempotency_dedupe_policy", html)
        self.assertIn("claim_policy", html)
        self.assertIn("lease_policy", html)
        self.assertIn("heartbeat_policy", html)
        self.assertIn("stale_lease_recovery", html)
        self.assertIn("worker_invocation_envelope", html)
        self.assertIn("completion_ack", html)
        self.assertIn("audit_receipt", html)
        self.assertIn("queue_insert_allowed", html)
        self.assertIn("lease_acquired", html)
        self.assertIn("worker_started", html)
        self.assertIn("external_api_called", html)

    def test_project_workspace_provider_queue_lease_worker_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_provider_queue_lease_worker_marker", script)
        self.assertIn("Project Workspace provider queue lease worker bundle", script)

    def test_project_workspace_provider_queue_lease_worker_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace provider queue lease worker bundle", script)
        self.assertIn("project_workspace_provider_queue_lease_worker_marker", script)


    def test_project_workspace_provider_worker_checkpoint_resume_bundle_markers(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        self.assertIn("Project Workspace provider worker checkpoint resume bundle", html)
        self.assertIn("PROJECT_WORKSPACE_PROVIDER_WORKER_CHECKPOINT_RESUME_BUNDLE_MARKER", html)
        self.assertIn("renderProjectWorkspaceProviderWorkerCheckpointResumePanel", html)
        self.assertIn("copyProjectWorkspaceProviderWorkerCheckpointResume", html)
        self.assertIn("provider_worker_checkpoint_resume_report", html)
        self.assertIn("projectWorkspaceExportProviderWorkerCheckpointResumeMarkdown", html)
        self.assertIn("projectWorkspaceExportProviderWorkerCheckpointResumeSnapshot", html)
        self.assertIn("checkpoint_policy", html)
        self.assertIn("checkpoint_bundle", html)
        self.assertIn("resume_cursor_policy", html)
        self.assertIn("replay_policy", html)
        self.assertIn("recovery_policy", html)
        self.assertIn("dead_letter_policy", html)
        self.assertIn("idempotency_replay_guard", html)
        self.assertIn("provider_replay_blocked", html)
        self.assertIn("duplicate_resume_blocked", html)
        self.assertIn("duplicate_provider_call_blocked", html)
        self.assertIn("checkpoint_recorded", html)
        self.assertIn("resume_allowed", html)
        self.assertIn("external_api_called", html)

    def test_project_workspace_provider_worker_checkpoint_resume_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_provider_worker_checkpoint_resume_marker", script)
        self.assertIn("Project Workspace provider worker checkpoint resume bundle", script)

    def test_project_workspace_provider_worker_checkpoint_resume_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace provider worker checkpoint resume bundle", script)
        self.assertIn("project_workspace_provider_worker_checkpoint_resume_marker", script)


    def test_project_workspace_provider_worker_finalization_bundle_markers(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        self.assertIn("Project Workspace provider worker finalization bundle", html)
        self.assertIn("PROJECT_WORKSPACE_PROVIDER_WORKER_FINALIZATION_BUNDLE_MARKER", html)
        self.assertIn("renderProjectWorkspaceProviderWorkerFinalizationPanel", html)
        self.assertIn("copyProjectWorkspaceProviderWorkerFinalization", html)
        self.assertIn("provider_worker_finalization_report", html)
        self.assertIn("projectWorkspaceExportProviderWorkerFinalizationMarkdown", html)
        self.assertIn("projectWorkspaceExportProviderWorkerFinalizationSnapshot", html)
        self.assertIn("result_validation_gate", html)
        self.assertIn("artifact_manifest", html)
        self.assertIn("artifact_handoff", html)
        self.assertIn("output_contract_validation", html)
        self.assertIn("downstream_handoff_policy", html)
        self.assertIn("run_finalization_policy", html)
        self.assertIn("finalization_audit_receipt", html)
        self.assertIn("result_validated", html)
        self.assertIn("artifact_handoff_ready", html)
        self.assertIn("workspace_export_ready", html)
        self.assertIn("media_uploaded", html)
        self.assertIn("media_downloaded", html)
        self.assertIn("external_api_called", html)

    def test_project_workspace_provider_worker_finalization_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_provider_worker_finalization_marker", script)
        self.assertIn("Project Workspace provider worker finalization bundle", script)

    def test_project_workspace_provider_worker_finalization_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace provider worker finalization bundle", script)
        self.assertIn("project_workspace_provider_worker_finalization_marker", script)


    def test_project_workspace_provider_artifact_lineage_bundle_markers(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        self.assertIn("Project Workspace provider artifact lineage bundle", html)
        self.assertIn("PROJECT_WORKSPACE_PROVIDER_ARTIFACT_LINEAGE_BUNDLE_MARKER", html)
        self.assertIn("renderProjectWorkspaceProviderArtifactLineagePanel", html)
        self.assertIn("copyProjectWorkspaceProviderArtifactLineage", html)
        self.assertIn("provider_artifact_lineage_report", html)
        self.assertIn("projectWorkspaceExportProviderArtifactLineageMarkdown", html)
        self.assertIn("projectWorkspaceExportProviderArtifactLineageSnapshot", html)
        self.assertIn("source_provenance_chain", html)
        self.assertIn("prompt_generation_lineage", html)
        self.assertIn("worker_lineage", html)
        self.assertIn("artifact_version_policy", html)
        self.assertIn("versioned_audit_snapshot", html)
        self.assertIn("reproducibility_packet", html)
        self.assertIn("tamper_drift_guard", html)
        self.assertIn("lineage_audit_receipt", html)
        self.assertIn("lineage_persisted", html)
        self.assertIn("versioned_snapshot_persisted", html)
        self.assertIn("real_hash_computed", html)
        self.assertIn("artifact_mutation_allowed", html)
        self.assertIn("external_api_called", html)

    def test_project_workspace_provider_artifact_lineage_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_provider_artifact_lineage_marker", script)
        self.assertIn("Project Workspace provider artifact lineage bundle", script)

    def test_project_workspace_provider_artifact_lineage_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace provider artifact lineage bundle", script)
        self.assertIn("project_workspace_provider_artifact_lineage_marker", script)


    def test_project_workspace_provider_artifact_registry_restore_bundle_markers(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        self.assertIn("Project Workspace provider artifact registry restore bundle", html)
        self.assertIn("PROJECT_WORKSPACE_PROVIDER_ARTIFACT_REGISTRY_RESTORE_BUNDLE_MARKER", html)
        self.assertIn("projectWorkspaceProviderArtifactRegistryRestoreReportFromWorkspace", html)
        self.assertIn("renderProjectWorkspaceProviderArtifactRegistryRestorePanel", html)
        self.assertIn("copyProjectWorkspaceProviderArtifactRegistryRestore", html)
        self.assertIn("provider_artifact_registry_restore_report", html)
        self.assertIn("projectWorkspaceExportProviderArtifactRegistryRestoreMarkdown", html)
        self.assertIn("projectWorkspaceExportProviderArtifactRegistryRestoreSnapshot", html)
        self.assertIn("artifact_registry_model", html)
        self.assertIn("versioned_snapshot_catalog", html)
        self.assertIn("snapshot_diff_preview", html)
        self.assertIn("restore_plan", html)
        self.assertIn("rollback_plan", html)
        self.assertIn("retention_policy", html)
        self.assertIn("persist_gate", html)
        self.assertIn("restore_audit_ledger", html)
        self.assertIn("registry_receipt", html)
        self.assertIn("blocking_failures", html)
        self.assertIn("artifact_registry_restore_stage_matrix", html)
        self.assertIn("provider_artifact_lineage_ready", html)
        self.assertIn("operator_review_required", html)
        self.assertIn("registry_persisted", html)
        self.assertIn("snapshot_catalog_persisted", html)
        self.assertIn("restore_applied", html)
        self.assertIn("workspace_restored", html)
        self.assertIn("rollback_applied", html)
        self.assertIn("artifact_deleted", html)
        self.assertIn("registry_write_allowed", html)
        self.assertIn("restore_write_allowed", html)
        self.assertIn("restore_audit_recorded", html)
        self.assertIn("provider_secret_read", html)
        self.assertIn("media_uploaded", html)
        self.assertIn("paid_generation_allowed", html)
        self.assertIn("copyProviderArtifactRegistryRestore", html)
        self.assertIn("providerArtifactRegistryRestoreCopied", html)
        self.assertNotIn("????", html)

    def test_project_workspace_provider_artifact_registry_restore_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_provider_artifact_registry_restore_marker", script)
        self.assertIn("Project Workspace provider artifact registry restore bundle", script)

    def test_project_workspace_provider_artifact_registry_restore_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace provider artifact registry restore bundle", script)
        self.assertIn("project_workspace_provider_artifact_registry_restore_marker", script)


    def test_project_workspace_provider_registry_operation_approval_bundle_markers(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        self.assertIn("Project Workspace provider registry operation approval bundle", html)
        self.assertIn("PROJECT_WORKSPACE_PROVIDER_REGISTRY_OPERATION_APPROVAL_BUNDLE_MARKER", html)
        self.assertIn("latestProjectProviderRegistryOperationApprovalReport", html)
        self.assertIn("projectWorkspaceProviderRegistryOperationApprovalReportFromWorkspace", html)
        self.assertIn("projectWorkspaceProviderRegistryOperationApprovalCopyText", html)
        self.assertIn("copyProjectWorkspaceProviderRegistryOperationApproval", html)
        self.assertIn("renderProjectWorkspaceProviderRegistryOperationApprovalPanel", html)
        self.assertIn("provider_registry_operation_approval_report", html)
        self.assertIn("projectWorkspaceExportProviderRegistryOperationApprovalMarkdown", html)
        self.assertIn("projectWorkspaceExportProviderRegistryOperationApprovalSnapshot", html)
        for field in [
            "operator_approval_request",
            "apply_simulation",
            "persistence_boundary",
            "authorization_preview",
            "destructive_action_guard",
            "registry_write_plan",
            "snapshot_write_plan",
            "restore_write_plan",
            "rollback_write_plan",
            "abort_noop_plan",
            "operation_audit_receipt",
            "blocking_failures",
            "registry_operation_approval_stage_matrix",
            "provider_artifact_registry_restore_ready",
            "operator_review_required",
            "operator_approval_required",
            "approval_check_count",
            "simulation_step_count",
            "persistence_boundary_count",
            "authorization_check_count",
            "destructive_guard_count",
            "write_plan_count",
            "abort_condition_count",
            "audit_receipt_item_count",
            "operator_approval_captured",
            "apply_simulation_recorded",
            "apply_simulation_persisted",
            "persist_allowed",
            "persist_gate_recorded",
            "registry_write_allowed",
            "registry_written",
            "snapshot_write_allowed",
            "snapshot_written",
            "restore_write_allowed",
            "restore_applied",
            "workspace_restored",
            "rollback_write_allowed",
            "rollback_applied",
            "artifact_delete_allowed",
            "artifact_deleted",
            "destructive_action_allowed",
            "project_snapshot_saved",
            "audit_ledger_persisted",
            "operation_audit_recorded",
            "workspace_export_ready",
            "json_export_ready",
            "markdown_export_ready",
            "external_api_call_allowed",
            "external_api_called",
            "provider_secret_read",
            "provider_secret_exported",
            "media_uploaded",
            "media_downloaded",
            "paid_generation_allowed",
            "dry_run",
            "has_provider_registry_operation_approval_report",
        ]:
            self.assertIn(field, html)
        for support_field in [
            "supports_operator_approval_request",
            "supports_apply_simulation",
            "supports_persistence_boundary",
            "supports_authorization_preview",
            "supports_destructive_action_guard",
            "supports_registry_write_plan",
            "supports_snapshot_write_plan",
            "supports_restore_write_plan",
            "supports_rollback_write_plan",
            "supports_abort_noop_plan",
            "supports_operation_audit_receipt",
        ]:
            self.assertIn(support_field, html)
        self.assertIn("copyProviderRegistryOperationApproval", html)
        self.assertIn("providerRegistryOperationApprovalCopied", html)
        self.assertIn("providerRegistryOperationApprovalCopyFailed", html)
        self.assertNotIn("????", html)

    def test_project_workspace_provider_registry_operation_approval_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_provider_registry_operation_approval_marker", script)
        self.assertIn("Project Workspace provider registry operation approval bundle", script)

    def test_project_workspace_provider_registry_operation_approval_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace provider registry operation approval bundle", script)
        self.assertIn("project_workspace_provider_registry_operation_approval_marker", script)

    def test_project_workspace_provider_registry_transaction_rehearsal_bundle_markers(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        self.assertIn("Project Workspace provider registry transaction rehearsal bundle", html)
        self.assertIn("PROJECT_WORKSPACE_PROVIDER_REGISTRY_TRANSACTION_REHEARSAL_BUNDLE_MARKER", html)
        self.assertIn("latestProjectProviderRegistryTransactionRehearsalReport", html)
        self.assertIn("projectWorkspaceProviderRegistryTransactionRehearsalReportFromWorkspace", html)
        self.assertIn("projectWorkspaceProviderRegistryTransactionRehearsalCopyText", html)
        self.assertIn("copyProjectWorkspaceProviderRegistryTransactionRehearsal", html)
        self.assertIn("renderProjectWorkspaceProviderRegistryTransactionRehearsalPanel", html)
        self.assertIn("projectWorkspaceExportProviderRegistryTransactionRehearsalMarkdown", html)
        self.assertIn("projectWorkspaceExportProviderRegistryTransactionRehearsalSnapshot", html)
        self.assertIn("provider_registry_transaction_rehearsal_report", html)
        for field in [
            "transaction_preflight",
            "operation_lock_plan",
            "mutation_ledger_preview",
            "idempotency_guard",
            "commit_packet",
            "rollback_checkpoint",
            "post_apply_verification",
            "release_gate",
            "transaction_audit_receipt",
            "blocking_failures",
            "registry_transaction_rehearsal_stage_matrix",
            "provider_registry_operation_approval_ready",
            "operator_review_required",
            "preflight_check_count",
            "lock_check_count",
            "mutation_entry_count",
            "idempotency_check_count",
            "commit_packet_item_count",
            "rollback_checkpoint_count",
            "verification_check_count",
            "release_gate_check_count",
            "audit_receipt_item_count",
            "transaction_required",
            "transaction_preflight_recorded",
            "operation_lock_required",
            "operation_lock_acquired",
            "mutation_ledger_recorded",
            "mutation_ledger_persisted",
            "idempotency_key_registered",
            "commit_packet_recorded",
            "commit_packet_persisted",
            "commit_allowed",
            "transaction_committed",
            "registry_write_allowed",
            "registry_written",
            "snapshot_write_allowed",
            "snapshot_written",
            "restore_write_allowed",
            "restore_applied",
            "workspace_restored",
            "rollback_write_allowed",
            "rollback_applied",
            "rollback_checkpoint_recorded",
            "rollback_checkpoint_persisted",
            "post_apply_verification_recorded",
            "post_apply_verification_passed",
            "release_gate_open",
            "transaction_audit_recorded",
            "audit_ledger_persisted",
            "project_snapshot_saved",
            "artifact_delete_allowed",
            "artifact_deleted",
            "destructive_action_allowed",
            "operator_approval_captured",
            "external_api_call_allowed",
            "external_api_called",
            "provider_secret_read",
            "provider_secret_exported",
            "media_uploaded",
            "media_downloaded",
            "paid_generation_allowed",
            "dry_run",
            "has_provider_registry_transaction_rehearsal_report",
        ]:
            self.assertIn(field, html)
        for support_field in [
            "supports_transaction_preflight",
            "supports_operation_lock_plan",
            "supports_mutation_ledger_preview",
            "supports_idempotency_guard",
            "supports_commit_packet",
            "supports_rollback_checkpoint",
            "supports_post_apply_verification",
            "supports_release_gate",
            "supports_transaction_audit_receipt",
        ]:
            self.assertIn(support_field, html)
        self.assertIn("copyProviderRegistryTransactionRehearsal", html)
        self.assertIn("providerRegistryTransactionRehearsalCopied", html)
        self.assertIn("providerRegistryTransactionRehearsalCopyFailed", html)
        self.assertNotIn("????", html)

    def test_project_workspace_provider_registry_transaction_rehearsal_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_provider_registry_transaction_rehearsal_marker", script)
        self.assertIn("Project Workspace provider registry transaction rehearsal bundle", script)

    def test_project_workspace_provider_registry_transaction_rehearsal_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace provider registry transaction rehearsal bundle", script)
        self.assertIn("project_workspace_provider_registry_transaction_rehearsal_marker", script)

    def test_project_workspace_provider_transaction_monitor_bundle_markers(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        self.assertIn("Project Workspace provider transaction monitor bundle", html)
        self.assertIn("PROJECT_WORKSPACE_PROVIDER_TRANSACTION_MONITOR_BUNDLE_MARKER", html)
        self.assertIn("latestProjectProviderTransactionMonitorReport", html)
        self.assertIn("projectWorkspaceProviderTransactionMonitorReportFromWorkspace", html)
        self.assertIn("projectWorkspaceProviderTransactionMonitorCopyText", html)
        self.assertIn("copyProjectWorkspaceProviderTransactionMonitor", html)
        self.assertIn("renderProjectWorkspaceProviderTransactionMonitorPanel", html)
        self.assertIn("projectWorkspaceExportProviderTransactionMonitorMarkdown", html)
        self.assertIn("projectWorkspaceExportProviderTransactionMonitorSnapshot", html)
        self.assertIn("provider_transaction_monitor_report", html)
        for field in [
            "monitoring_preflight",
            "transaction_health_monitor",
            "drift_detection_policy",
            "auto_abort_policy",
            "operator_timeline",
            "verification_monitor",
            "incident_escalation_policy",
            "monitoring_audit_receipt",
            "blocking_failures",
            "transaction_monitor_stage_matrix",
            "provider_registry_transaction_rehearsal_ready",
            "operator_review_required",
            "monitor_check_count",
            "health_signal_count",
            "drift_rule_count",
            "auto_abort_rule_count",
            "timeline_event_count",
            "verification_monitor_check_count",
            "incident_escalation_rule_count",
            "audit_receipt_item_count",
            "monitoring_required",
            "monitoring_started",
            "health_monitor_recorded",
            "drift_detection_started",
            "drift_detected",
            "auto_abort_enabled",
            "auto_abort_triggered",
            "transaction_aborted",
            "operator_timeline_recorded",
            "verification_monitor_recorded",
            "verification_passed",
            "incident_escalation_triggered",
            "incident_opened",
            "monitoring_audit_recorded",
            "audit_ledger_persisted",
            "transaction_committed",
            "registry_written",
            "snapshot_written",
            "restore_applied",
            "workspace_restored",
            "rollback_applied",
            "project_snapshot_saved",
            "artifact_deleted",
            "external_api_call_allowed",
            "external_api_called",
            "provider_secret_read",
            "provider_secret_exported",
            "media_uploaded",
            "media_downloaded",
            "paid_generation_allowed",
            "dry_run",
            "has_provider_transaction_monitor_report",
        ]:
            self.assertIn(field, html)
        for support_field in [
            "supports_monitoring_preflight",
            "supports_transaction_health_monitor",
            "supports_drift_detection_policy",
            "supports_auto_abort_policy",
            "supports_operator_timeline",
            "supports_verification_monitor",
            "supports_incident_escalation_policy",
            "supports_monitoring_audit_receipt",
        ]:
            self.assertIn(support_field, html)
        self.assertIn("copyProviderTransactionMonitor", html)
        self.assertIn("providerTransactionMonitorCopied", html)
        self.assertIn("providerTransactionMonitorCopyFailed", html)
        self.assertNotIn("????", html)

    def test_project_workspace_provider_transaction_monitor_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_provider_transaction_monitor_marker", script)
        self.assertIn("Project Workspace provider transaction monitor bundle", script)

    def test_project_workspace_provider_transaction_monitor_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace provider transaction monitor bundle", script)
        self.assertIn("project_workspace_provider_transaction_monitor_marker", script)

    def test_project_workspace_provider_transaction_incident_drill_bundle_markers(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        self.assertIn("Project Workspace provider transaction incident drill bundle", html)
        self.assertIn("PROJECT_WORKSPACE_PROVIDER_TRANSACTION_INCIDENT_DRILL_BUNDLE_MARKER", html)
        self.assertIn("latestProjectProviderTransactionIncidentDrillReport", html)
        self.assertIn("projectWorkspaceProviderTransactionIncidentDrillReportFromWorkspace", html)
        self.assertIn("projectWorkspaceProviderTransactionIncidentDrillCopyText", html)
        self.assertIn("copyProjectWorkspaceProviderTransactionIncidentDrill", html)
        self.assertIn("renderProjectWorkspaceProviderTransactionIncidentDrillPanel", html)
        self.assertIn("projectWorkspaceExportProviderTransactionIncidentDrillMarkdown", html)
        self.assertIn("projectWorkspaceExportProviderTransactionIncidentDrillSnapshot", html)
        self.assertIn("provider_transaction_incident_drill_report", html)
        for field in [
            "incident_drill_preflight",
            "incident_scenario_matrix",
            "recovery_runbook",
            "operator_decision_replay",
            "rollback_restore_drill",
            "evidence_reconciliation",
            "incident_timeline",
            "drill_audit_receipt",
            "blocking_failures",
            "transaction_incident_drill_stage_matrix",
            "provider_transaction_monitor_ready",
            "operator_review_required",
            "drill_check_count",
            "incident_scenario_count",
            "recovery_step_count",
            "operator_decision_count",
            "rollback_restore_step_count",
            "evidence_reconciliation_check_count",
            "incident_timeline_event_count",
            "audit_receipt_item_count",
            "incident_drill_required",
            "incident_drill_started",
            "incident_detected",
            "incident_opened",
            "recovery_runbook_recorded",
            "operator_decision_replayed",
            "operator_decision_persisted",
            "rollback_restore_drill_recorded",
            "rollback_restore_executed",
            "evidence_reconciliation_recorded",
            "incident_timeline_recorded",
            "drill_audit_recorded",
            "audit_ledger_persisted",
            "transaction_aborted",
            "transaction_committed",
            "registry_written",
            "snapshot_written",
            "restore_applied",
            "workspace_restored",
            "rollback_applied",
            "project_snapshot_saved",
            "artifact_deleted",
            "external_api_call_allowed",
            "external_api_called",
            "provider_secret_read",
            "provider_secret_exported",
            "media_uploaded",
            "media_downloaded",
            "paid_generation_allowed",
            "dry_run",
            "has_provider_transaction_incident_drill_report",
        ]:
            self.assertIn(field, html)
        for support_field in [
            "supports_incident_drill_preflight",
            "supports_incident_scenario_matrix",
            "supports_recovery_runbook",
            "supports_operator_decision_replay",
            "supports_rollback_restore_drill",
            "supports_evidence_reconciliation",
            "supports_incident_timeline",
            "supports_drill_audit_receipt",
        ]:
            self.assertIn(support_field, html)
        self.assertIn("copyProviderTransactionIncidentDrill", html)
        self.assertIn("providerTransactionIncidentDrillCopied", html)
        self.assertIn("providerTransactionIncidentDrillCopyFailed", html)
        self.assertNotIn("????", html)

    def test_project_workspace_provider_transaction_incident_drill_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_provider_transaction_incident_drill_marker", script)
        self.assertIn("Project Workspace provider transaction incident drill bundle", script)

    def test_project_workspace_provider_transaction_incident_drill_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace provider transaction incident drill bundle", script)
        self.assertIn("project_workspace_provider_transaction_incident_drill_marker", script)

    def test_project_workspace_provider_execution_readiness_packet_bundle_markers(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        self.assertIn("Project Workspace provider execution readiness packet bundle", html)
        self.assertIn("PROJECT_WORKSPACE_PROVIDER_EXECUTION_READINESS_PACKET_BUNDLE_MARKER", html)
        self.assertIn("latestProjectProviderExecutionReadinessPacketReport", html)
        self.assertIn("projectWorkspaceProviderExecutionReadinessPacketReportFromWorkspace", html)
        self.assertIn("projectWorkspaceProviderExecutionReadinessPacketCopyText", html)
        self.assertIn("copyProjectWorkspaceProviderExecutionReadinessPacket", html)
        self.assertIn("renderProjectWorkspaceProviderExecutionReadinessPacketPanel", html)
        self.assertIn("projectWorkspaceExportProviderExecutionReadinessPacketMarkdown", html)
        self.assertIn("projectWorkspaceExportProviderExecutionReadinessPacketSnapshot", html)
        self.assertIn("provider_execution_readiness_packet_report", html)
        for field in [
            "readiness_packet_summary",
            "system_capability_matrix",
            "execution_boundary_map",
            "operator_runbook",
            "audit_export_index",
            "demo_storyline",
            "final_readiness_gate",
            "readiness_audit_receipt",
            "blocking_failures",
            "execution_readiness_packet_stage_matrix",
            "provider_transaction_incident_drill_ready",
            "operator_review_required",
            "readiness_summary_item_count",
            "capability_count",
            "boundary_count",
            "operator_step_count",
            "audit_export_count",
            "storyline_step_count",
            "final_gate_check_count",
            "audit_receipt_item_count",
            "readiness_packet_required",
            "readiness_packet_recorded",
            "operator_runbook_recorded",
            "demo_executed",
            "final_gate_passed",
            "operator_approval_present",
            "provider_cost_review_complete",
            "provider_secret_policy_approved",
            "registry_write_authorized",
            "rollback_restore_authorized",
            "real_execution_enabled",
            "provider_call_allowed",
            "transaction_started",
            "transaction_aborted",
            "transaction_committed",
            "registry_written",
            "snapshot_written",
            "restore_applied",
            "workspace_restored",
            "rollback_applied",
            "project_snapshot_saved",
            "artifact_deleted",
            "readiness_audit_recorded",
            "audit_ledger_persisted",
            "external_api_call_allowed",
            "external_api_called",
            "provider_secret_read",
            "provider_secret_exported",
            "media_uploaded",
            "media_downloaded",
            "paid_generation_allowed",
            "dry_run",
            "has_provider_execution_readiness_packet_report",
        ]:
            self.assertIn(field, html)
        for support_field in [
            "supports_readiness_packet_summary",
            "supports_system_capability_matrix",
            "supports_execution_boundary_map",
            "supports_operator_runbook",
            "supports_audit_export_index",
            "supports_demo_storyline",
            "supports_final_readiness_gate",
            "supports_readiness_audit_receipt",
        ]:
            self.assertIn(support_field, html)
        self.assertIn("copyProviderExecutionReadinessPacket", html)
        self.assertIn("providerExecutionReadinessPacketCopied", html)
        self.assertIn("providerExecutionReadinessPacketCopyFailed", html)
        self.assertNotIn("????", html)

    def test_project_workspace_provider_execution_readiness_packet_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_provider_execution_readiness_packet_marker", script)
        self.assertIn("Project Workspace provider execution readiness packet bundle", script)

    def test_project_workspace_provider_execution_readiness_packet_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace provider execution readiness packet bundle", script)
        self.assertIn("project_workspace_provider_execution_readiness_packet_marker", script)

    def test_project_workspace_agent_capability_runtime_bundle(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace agent capability runtime bundle",
            "PROJECT_WORKSPACE_AGENT_CAPABILITY_RUNTIME_MARKER",
            "latestProjectAgentCapabilityRuntime",
            "projectWorkspaceAgentCapabilityRuntimeFromWorkspace",
            "projectWorkspaceAgentCapabilityRuntimeCopyText",
            "copyProjectWorkspaceAgentCapabilityRuntime",
            "renderProjectWorkspaceAgentCapabilitySummaryStrip",
            "renderProjectWorkspaceAgentTaskBoardPanel",
            "renderProjectWorkspaceSupervisorNextActionsPanel",
            "projectWorkspaceExportAgentCapabilityRuntimeSnapshot",
            "projectWorkspaceExportAgentCapabilityRuntimeMarkdown",
            "agent_capability_runtime",
            "agent_task_board",
            "supervisor_next_actions",
            "target_panel",
            "copy_or_export_hint",
            "agent_handoff_chain",
            "agent_quality_checks",
            "agent_handoff_ready",
            "projectWorkspaceProviderGovernanceGroup",
            "agentCapabilityRuntimeCopied",
            "agentCapabilityRuntimeCopyFailed",
            "agentCapabilityRuntimeNoData",
        ]:
            self.assertIn(marker, html)
        self.assertIn("Agent Capability Runtime", html)
        self.assertIn("Agent Task Board", html)
        self.assertIn("Supervisor Next Actions", html)
        self.assertIn("Agent Handoff Chain", html)
        self.assertIn("Agent Quality Checks", html)
        self.assertIn("Agent \\u80fd\\u529b\\u8fd0\\u884c\\u65f6", html)
        self.assertIn("Agent \\u4efb\\u52a1\\u677f", html)
        self.assertIn("guidance_only", html)
        self.assertIn("real_execution_enabled: false", html)
        self.assertNotIn("????", html)

    def test_project_workspace_agent_capability_runtime_public_smoke_marker(self):
        script = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("project_workspace_agent_capability_runtime_marker", script)
        self.assertIn("Project Workspace agent capability runtime bundle", script)

    def test_project_workspace_agent_capability_runtime_quality_guard_marker(self):
        script = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        self.assertIn("Project Workspace agent capability runtime bundle", script)
        self.assertIn("project_workspace_agent_capability_runtime_marker", script)


    def test_static_index_has_no_invalid_js_unicode_escape_sequences(self):
        html = _CgInvalidUnicodePath("static/index.html").read_text(encoding="utf-8")
        matches = list(_cg_invalid_unicode_re.finditer(r"\\u(?![0-9a-fA-F]{4})", html))
        self.assertEqual(matches, [])


class ProjectWorkspaceCreativeDecisionPackFrontendTests(unittest.TestCase):
    def test_creative_decision_pack_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace creative decision pack bundle",
            "PROJECT_WORKSPACE_CREATIVE_DECISION_PACK_MARKER",
            "latestProjectCreativeDecisionPack",
            "projectWorkspaceCreativeDecisionPackFromWorkspace",
            "projectWorkspaceCreativeDecisionPackCopyText",
            "copyProjectWorkspaceCreativeDecisionPack",
            "copyProjectWorkspaceTopAngleScript",
            "copyProjectWorkspaceVideoPromptPack",
            "renderProjectWorkspaceCreativeDecisionSummaryStrip",
            "renderProjectWorkspaceCreativeDecisionRecommendationPanel",
            "renderProjectWorkspaceTopAdAnglesPanel",
            "renderProjectWorkspaceCreativeEvidenceQualityPanel",
            "renderProjectWorkspaceCreativeNextActionsPanel",
            "renderProjectWorkspaceVideoPromptPackPanel",
            "renderProjectWorkspaceCreativeQualityChecksPanel",
            "copyProjectWorkspaceRecommendedTikTokScript",
            "projectWorkspaceExportCreativeDecisionPackSnapshot",
            "projectWorkspaceExportCreativeDecisionPackMarkdown",
            "projectWorkspaceCreativeDecisionExportText",
            "copyProjectWorkspaceCreativeDecisionExport",
            "renderProjectWorkspaceCreativeExportPanel",
            "creative_decision_pack: projectWorkspaceExportCreativeDecisionPackSnapshot(workspace)",
            "creative_decision_pack: latestProjectCreativeDecisionPack",
            "Creative Decision Pack",
            "Top 3 Ad Angles",
            "Evidence Brief",
            "Video Prompt Pack",
            "Creative Quality Checks",
            "Recommended Creative Angle",
            "Evidence Quality Summary",
            "Creative Next Actions",
            "TikTok Script",
            "Creative Decision Export",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)

    def test_creative_decision_pack_copy_feedback_and_bilingual_copy_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for key in [
            "creativeDecisionCopyEvidence",
            "creativeDecisionCopyAngle",
            "creativeDecisionCopyVideoPrompt",
            "creativeDecisionEvidenceCopied",
            "creativeDecisionAngleCopied",
            "creativeDecisionVideoCopied",
            "creativeDecisionCopyFailed",
            "creativeDecisionCopyNoData",
            "creativeDecisionReadOnlyNote",
            "creativeDecisionWeakEvidence",
            "creativeDecisionRecommended",
            "creativeDecisionCopyRecommendedScript",
            "creativeDecisionEvidenceQualitySummary",
            "creativeDecisionNextActionsTitle",
            "creativeDecisionEvidenceScore",
            "creativeDecisionEvidenceCoverage",
            "creativeDecisionEvidenceGaps",
            "creativeDecisionClaimSafetyLevel",
            "creativeDecisionWhyRecommended",
            "creativeDecisionEvidenceRisk",
            "creativeDecisionShotPrompt",
            "creativeDecisionShotEvidence",
            "creativeDecisionPromptSafetyBoundary",
            "creativeDecisionExportTitle",
            "creativeDecisionExportMarkdown",
            "creativeDecisionExportJson",
            "creativeDecisionExportMarkdownContents",
            "creativeDecisionExportJsonContents",
            "creativeDecisionExportSafetyNote",
            "creativeDecisionExportMarkdownCopied",
            "creativeDecisionExportJsonCopied",
            "creativeDecisionExportFailed",
            "creativeDecisionExportNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        self.assertIn("\\u521b\\u610f\\u51b3\\u7b56\\u5305", html)
        self.assertIn("\\u8bc1\\u636e\\u7b80\\u62a5", html)
        self.assertNotIn("????", html)

    def test_creative_decision_pack_quality_guard_and_public_smoke_markers(self):
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for script in [guard, smoke]:
            self.assertIn("Project Workspace creative decision pack bundle", script)
            self.assertIn("project_workspace_creative_decision_pack_marker", script)
            self.assertIn("Project Workspace creative decision usability bundle", script)
            self.assertIn("project_workspace_creative_decision_usability_marker", script)
            self.assertIn("Project Workspace creative decision quality polish bundle", script)
            self.assertIn("project_workspace_creative_decision_quality_polish_marker", script)

    def test_creative_decision_pack_consumes_ranking_quality_and_next_actions(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for field in [
            "recommended_angle_id",
            "recommended_angle_title",
            "decision_reason",
            "angle_ranking_summary",
            "weak_evidence_count",
            "missing_quote_count",
            "ready_to_copy_script_count",
            "duplicate_angle_count",
            "creative_next_actions",
            "angle_rank",
            "is_recommended",
            "recommendation_reason",
            "evidence_strength_score",
            "evidence_coverage",
            "evidence_gaps",
            "angle_cluster",
            "duplicate_angle_note",
            "tiktok_script",
            "copy_readiness",
            "claim_safety_level",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, html)
        for export_heading in [
            "creativeDecisionRecommendedAngleTitle",
            "creativeDecisionEvidenceQualitySummary",
            "creativeDecisionNextActionsTitle",
            "creativeDecisionTikTokScript",
        ]:
            self.assertIn(export_heading, html)
        self.assertIn("creative_decision_pack: projectWorkspaceExportCreativeDecisionPackSnapshot(workspace)", html)

    def test_creative_decision_quality_polish_groups_recommendation_script_and_video_safety(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        recommendation_start = html.index("function renderProjectWorkspaceCreativeDecisionRecommendationPanel")
        recommendation_end = html.index("function renderProjectWorkspaceTopAdAnglesPanel", recommendation_start)
        recommendation = html[recommendation_start:recommendation_end]
        for marker in [
            "creativeDecisionWhyRecommended",
            "creativeDecisionEvidenceScore",
            "creativeDecisionClaimSafetyLevel",
            "creativeDecisionCopyReadiness",
            "creativeDecisionEvidenceRisk",
            "creativeDecisionRiskNote",
            "PROJECT_WORKSPACE_CREATIVE_DECISION_QUALITY_POLISH_MARKER",
        ]:
            self.assertIn(marker, recommendation)

        copy_start = html.index("function projectWorkspaceCreativeDecisionPackCopyText")
        copy_end = html.index("async function copyProjectWorkspaceCreativeDecisionText", copy_start)
        copy_source = html[copy_start:copy_end]
        self.assertLess(copy_source.index("creativeDecisionHook"), copy_source.index("creativeDecisionCta"))
        self.assertLess(copy_source.index("creativeDecisionCta"), copy_source.index("creativeDecisionProofQuote"))
        self.assertLess(copy_source.index("creativeDecisionProofQuote"), copy_source.index("creativeDecisionRiskNote"))

        markdown_start = html.index("function projectWorkspaceExportCreativeDecisionPackMarkdown")
        markdown_end = html.index("function projectWorkspaceCreativeDecisionPackCopyText", markdown_start)
        markdown_source = html[markdown_start:markdown_end]
        for marker in [
            "creativeDecisionRecommendedAngleTitle",
            "creativeDecisionTikTokScript",
            "creativeDecisionVideoPromptTitle",
            "creativeDecisionRiskNote",
            "creativeDecisionDoNotClaim",
        ]:
            self.assertIn(marker, markdown_source)

        video_start = html.index("function renderProjectWorkspaceVideoPromptPackPanel")
        video_end = html.index("function renderProjectWorkspaceCreativeQualityChecksPanel", video_start)
        video = html[video_start:video_end]
        for marker in [
            "creativeDecisionShotList",
            "creativeDecisionShotEvidence",
            "creativeDecisionPromptSafetyBoundary",
            "creativeDecisionEvidenceLinks",
            "creativeDecisionProductContext",
        ]:
            self.assertIn(marker, video)
        self.assertNotIn("JSON.stringify(video.evidence_links", video)
        self.assertNotIn("????", html)

    def test_real_sample_export_flow_has_status_guidance_and_bilingual_copy(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        self.assertIn("Project Workspace real sample export flow bundle", html)
        self.assertIn("PROJECT_WORKSPACE_REAL_SAMPLE_EXPORT_FLOW_MARKER", html)
        self.assertIn("renderProjectWorkspaceCreativeExportPanel(workspace)", html)
        self.assertIn("copyProjectWorkspaceCreativeDecisionExport('markdown')", html)
        self.assertIn("copyProjectWorkspaceCreativeDecisionExport('json')", html)
        self.assertIn("pack.top_ad_angles?.length ? 'weak_evidence' : 'no_data'", html)
        for key in [
            "creativeCoreFlowHelper",
            "creativeDecisionExportTitle",
            "creativeDecisionExportHelper",
            "creativeDecisionExportMarkdownContents",
            "creativeDecisionExportJsonContents",
            "creativeDecisionExportSafetyNote",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace real sample export flow bundle", script)
            self.assertIn("project_workspace_real_sample_export_flow_marker", script)
        governance_start = html.index("function renderProjectWorkspaceProviderGovernanceGroup")
        governance_end = html.index("function projectWorkspaceExportPackMarkdownText", governance_start)
        governance = html[governance_start:governance_end]
        self.assertIn('<details class="section-block" id="projectWorkspaceProviderGovernanceGroup">', governance)
        self.assertNotIn("<details open", governance)
        self.assertNotIn("????", html)

    def test_creative_variant_workspace_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace creative variant pack bundle",
            "PROJECT_WORKSPACE_CREATIVE_VARIANT_PACK_MARKER",
            "latestProjectCreativeVariantPack",
            "projectWorkspaceCreativeVariantPackFromWorkspace",
            "projectWorkspaceExportCreativeVariantPackSnapshot",
            "projectWorkspaceExportCreativeVariantPackMarkdown",
            "renderProjectWorkspaceCreativeVariantSummaryPanel",
            "renderProjectWorkspaceCreativeVariantsPanel",
            "renderProjectWorkspaceCreativeVariantComparePanel",
            "copyProjectWorkspaceRecommendedVariantScript",
            "copyProjectWorkspaceCreativeVariantScript",
            "copyProjectWorkspaceCreativeVariantVideoPrompt",
            "creative_variant_pack: projectWorkspaceExportCreativeVariantPackSnapshot(workspace)",
            "Creative Variant Pack",
            "Recommended Variant Script",
            "Variant Scripts and Video Prompts",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for runtime_field in [
            "variant.variant_type",
            "variant.target_length_seconds",
            "variant.creative_style",
            "variant.claim_safety_level",
            "variant.copy_readiness",
        ]:
            self.assertIn(runtime_field, html)

    def test_creative_variant_workspace_has_bilingual_copy_guard_and_collapsed_governance(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "creativeVariantSummaryTitle",
            "creativeVariantPanelTitle",
            "creativeVariantCompareTitle",
            "creativeVariantCopyRecommended",
            "creativeVariantCopyScript",
            "creativeVariantCopyVideoPrompt",
            "creativeVariantScriptCopied",
            "creativeVariantVideoPromptCopied",
            "creativeVariantCopyFailed",
            "creativeVariantCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace creative variant pack bundle", script)
            self.assertIn("project_workspace_creative_variant_pack_marker", script)
        markdown_start = html.index("function projectWorkspaceExportCreativeVariantPackMarkdown")
        markdown_end = html.index("async function copyProjectWorkspaceCreativeVariantText", markdown_start)
        markdown = html[markdown_start:markdown_end]
        for marker in [
            "creativeVariantPackTitle",
            "creativeVariantRecommendedVariant",
            "creativeVariantRecommendedScript",
            "creativeVariantScriptsTitle",
            "creativeVariantVideoPrompt",
        ]:
            self.assertIn(marker, markdown)
        governance_start = html.index("function renderProjectWorkspaceProviderGovernanceGroup")
        governance_end = html.index("function projectWorkspaceExportPackMarkdownText", governance_start)
        governance = html[governance_start:governance_end]
        self.assertIn('<details class="section-block" id="projectWorkspaceProviderGovernanceGroup">', governance)
        self.assertNotIn("<details open", governance)
        self.assertNotIn("????", html)

    def test_creative_variant_selection_workspace_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace creative variant selection bundle",
            "PROJECT_WORKSPACE_CREATIVE_VARIANT_SELECTION_MARKER",
            "latestProjectCreativeVariantSelectionPack",
            "projectWorkspaceCreativeVariantSelectionPackFromWorkspace",
            "projectWorkspaceExportCreativeVariantSelectionSnapshot",
            "projectWorkspaceExportCreativeVariantSelectionMarkdown",
            "renderProjectWorkspaceCreativeVariantSelectionSummaryPanel",
            "renderProjectWorkspaceCreativeVariantSelectionCardsPanel",
            "renderProjectWorkspaceCreativeVariantAbTestPlanPanel",
            "copyProjectWorkspaceRecommendedFirstVariant",
            "copyProjectWorkspaceCreativeVariantSelectionCard",
            "copyProjectWorkspaceCreativeVariantAbTestPlan",
            "variant_selection_pack: projectWorkspaceExportCreativeVariantSelectionSnapshot(workspace)",
            "Variant Selection",
            "Recommended First Variant",
            "A/B Test Plan",
            "Safety Notes",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for runtime_field in [
            "card.best_for",
            "card.selection_reason",
            "card.test_hypothesis",
            "card.success_metric",
            "card.recommended_next_action",
            "card.proof_quote",
            "card.risk_note",
            "card.do_not_claim",
            "card.claim_safety_level",
            "card.copy_readiness",
        ]:
            self.assertIn(runtime_field, html)

    def test_creative_variant_selection_workspace_has_bilingual_copy_guard_and_collapsed_governance(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "creativeVariantSelectionTitle",
            "creativeVariantSelectionCardsTitle",
            "creativeVariantSelectionRecommendedFirst",
            "creativeVariantSelectionAbTestPlan",
            "creativeVariantSelectionCopyRecommended",
            "creativeVariantSelectionCopyCard",
            "creativeVariantSelectionCopyAbPlan",
            "creativeVariantSelectionCardCopied",
            "creativeVariantSelectionAbPlanCopied",
            "creativeVariantSelectionCopyFailed",
            "creativeVariantSelectionCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace creative variant selection bundle", script)
            self.assertIn("project_workspace_creative_variant_selection_marker", script)
        markdown_start = html.index(
            "function projectWorkspaceExportCreativeVariantSelectionMarkdown"
        )
        markdown_end = html.index(
            "async function copyProjectWorkspaceCreativeVariantSelectionText",
            markdown_start,
        )
        markdown = html[markdown_start:markdown_end]
        for marker in [
            "creativeVariantSelectionTitle",
            "creativeVariantSelectionRecommendedFirst",
            "creativeVariantSelectionCardsTitle",
            "creativeVariantSelectionAbTestPlan",
            "creativeVariantSelectionSafetyNotes",
        ]:
            self.assertIn(marker, markdown)
        governance_start = html.index("function renderProjectWorkspaceProviderGovernanceGroup")
        governance_end = html.index("function projectWorkspaceExportPackMarkdownText", governance_start)
        governance = html[governance_start:governance_end]
        self.assertIn('<details class="section-block" id="projectWorkspaceProviderGovernanceGroup">', governance)
        self.assertNotIn("<details open", governance)
        self.assertNotIn("????", html)

    def test_creative_test_feedback_workspace_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace creative test feedback bundle",
            "PROJECT_WORKSPACE_CREATIVE_TEST_FEEDBACK_MARKER",
            "latestProjectCreativeTestFeedbackPack",
            "projectWorkspaceCreativeTestFeedbackPackFromWorkspace",
            "projectWorkspaceExportCreativeTestFeedbackSnapshot",
            "projectWorkspaceExportCreativeTestFeedbackMarkdown",
            "renderProjectWorkspaceCreativeTestFeedbackSummaryPanel",
            "renderProjectWorkspaceCreativeVariantFeedbackCardsPanel",
            "renderProjectWorkspaceCreativeIterationActionsPanel",
            "copyProjectWorkspaceCreativeTestFeedbackSummary",
            "copyProjectWorkspaceCreativeWinnerIterationPlan",
            "copyProjectWorkspaceCreativeVariantFeedbackCard",
            "copyProjectWorkspaceCreativeIterationActions",
            "creative_test_feedback_pack: projectWorkspaceExportCreativeTestFeedbackSnapshot(workspace)",
            "Creative Test Feedback",
            "Recommended Winner",
            "Next Iteration",
            "Iteration Actions",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for runtime_field in [
            "card.performance_tier",
            "card.keep_or_change",
            "card.what_worked",
            "card.what_to_improve",
            "card.next_hook_direction",
            "card.next_scene_direction",
            "card.next_cta_direction",
            "card.risk_note",
            "card.do_not_claim",
            "card.recommended_next_action",
        ]:
            self.assertIn(runtime_field, html)

    def test_creative_test_feedback_workspace_has_bilingual_copy_guard_and_collapsed_governance(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "creativeTestFeedbackTitle",
            "creativeTestFeedbackRecommendedWinner",
            "creativeTestFeedbackNextIteration",
            "creativeTestFeedbackVariantCardsTitle",
            "creativeTestFeedbackIterationActions",
            "creativeTestFeedbackCopySummary",
            "creativeTestFeedbackCopyWinnerPlan",
            "creativeTestFeedbackCopyCard",
            "creativeTestFeedbackCopyActions",
            "creativeTestFeedbackCopied",
            "creativeTestFeedbackCopyFailed",
            "creativeTestFeedbackCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace creative test feedback bundle", script)
            self.assertIn("project_workspace_creative_test_feedback_marker", script)
        markdown_start = html.index(
            "function projectWorkspaceExportCreativeTestFeedbackMarkdown"
        )
        markdown_end = html.index(
            "async function copyProjectWorkspaceCreativeTestFeedbackText",
            markdown_start,
        )
        markdown = html[markdown_start:markdown_end]
        for marker in [
            "creativeTestFeedbackTitle",
            "creativeTestFeedbackRecommendedWinner",
            "creativeTestFeedbackNextIteration",
            "creativeTestFeedbackIterationActions",
            "creativeVariantSelectionSafetyNotes",
        ]:
            self.assertIn(marker, markdown)
        governance_start = html.index("function renderProjectWorkspaceProviderGovernanceGroup")
        governance_end = html.index("function projectWorkspaceExportPackMarkdownText", governance_start)
        governance = html[governance_start:governance_end]
        self.assertIn('<details class="section-block" id="projectWorkspaceProviderGovernanceGroup">', governance)
        self.assertNotIn("<details open", governance)
        self.assertNotIn("????", html)

    def test_creative_iteration_workspace_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace creative iteration bundle",
            "PROJECT_WORKSPACE_CREATIVE_ITERATION_MARKER",
            "latestProjectCreativeIterationPack",
            "projectWorkspaceCreativeIterationPackFromWorkspace",
            "projectWorkspaceExportCreativeIterationSnapshot",
            "projectWorkspaceExportCreativeIterationMarkdown",
            "renderProjectWorkspaceCreativeIterationSummaryPanel",
            "renderProjectWorkspaceCreativeIterationVariantsPanel",
            "renderProjectWorkspaceCreativeOriginalVsRevisedDiffPanel",
            "copyProjectWorkspaceCreativeRecommendedV2Script",
            "copyProjectWorkspaceCreativeV2VideoPrompt",
            "copyProjectWorkspaceCreativeOriginalVsRevisedDiff",
            "copyProjectWorkspaceCreativeIterationSummary",
            "creative_iteration_pack: projectWorkspaceExportCreativeIterationSnapshot(workspace)",
            "Creative Iteration Pack",
            "Recommended V2 Variant",
            "Original vs Revised Diff",
            "V2 Script",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for runtime_field in [
            "variant.revised_hook",
            "variant.revised_scene_1",
            "variant.revised_scene_2",
            "variant.revised_scene_3",
            "variant.revised_cta",
            "variant.revised_proof_quote",
            "variant.revised_risk_note",
            "variant.revised_do_not_claim",
            "variant.what_changed",
            "variant.why_changed",
            "variant.copy_readiness",
            "variant.recommended_next_action",
        ]:
            self.assertIn(runtime_field, html)

    def test_creative_iteration_workspace_has_bilingual_copy_guard_and_collapsed_governance(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "creativeIterationPackTitle",
            "creativeIterationRecommendedV2",
            "creativeIterationVariantsTitle",
            "creativeIterationOriginalVsRevised",
            "creativeIterationV2Script",
            "creativeIterationCopyV2Script",
            "creativeIterationCopyVideoPrompt",
            "creativeIterationCopyDiff",
            "creativeIterationCopySummary",
            "creativeIterationCopied",
            "creativeIterationCopyFailed",
            "creativeIterationCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace creative iteration bundle", script)
            self.assertIn("project_workspace_creative_iteration_marker", script)
        markdown_start = html.index(
            "function projectWorkspaceExportCreativeIterationMarkdown"
        )
        markdown_end = html.index(
            "async function copyProjectWorkspaceCreativeIterationText",
            markdown_start,
        )
        markdown = html[markdown_start:markdown_end]
        for marker in [
            "creativeIterationPackTitle",
            "creativeIterationRecommendedV2",
            "creativeIterationOriginalVsRevised",
            "creativeIterationV2Script",
            "creativeIterationV2VideoPrompt",
            "creativeVariantSelectionSafetyNotes",
        ]:
            self.assertIn(marker, markdown)
        governance_start = html.index("function renderProjectWorkspaceProviderGovernanceGroup")
        governance_end = html.index("function projectWorkspaceExportPackMarkdownText", governance_start)
        governance = html[governance_start:governance_end]
        self.assertIn('<details class="section-block" id="projectWorkspaceProviderGovernanceGroup">', governance)
        self.assertNotIn("<details open", governance)
        self.assertNotIn("????", html)

    def test_creative_version_control_workspace_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace creative version control bundle",
            "PROJECT_WORKSPACE_CREATIVE_VERSION_CONTROL_MARKER",
            "latestProjectCreativeVersionControlPack",
            "projectWorkspaceCreativeVersionControlPackFromWorkspace",
            "projectWorkspaceExportCreativeVersionControlSnapshot",
            "projectWorkspaceExportCreativeVersionControlMarkdown",
            "renderProjectWorkspaceCreativeVersionSummaryPanel",
            "renderProjectWorkspaceCreativeVersionTimelinePanel",
            "renderProjectWorkspaceCreativeVersionComparisonPanel",
            "renderProjectWorkspaceCreativeVersionRiskSummaryPanel",
            "copyProjectWorkspaceRecommendedCreativeVersion",
            "copyProjectWorkspaceCreativeRecommendedVersionScript",
            "copyProjectWorkspaceCreativeVersion",
            "copyProjectWorkspaceCreativeVersionComparison",
            "copyProjectWorkspaceCreativeVersionTimeline",
            "copyProjectWorkspaceCreativeVersionRiskSummary",
            "creative_version_control_pack: projectWorkspaceExportCreativeVersionControlSnapshot(workspace)",
            "Creative Version Control",
            "Version Timeline",
            "V1 vs V2 Comparison",
            "Recommended Next Test Version",
            "Version Risk Summary",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for runtime_field in [
            "pack.version_lineage",
            "pack.version_comparison_cards",
            "pack.recommended_next_test_version_id",
            "version.parent_version_id",
            "version.proof_quote",
            "version.evidence_strength_score",
            "card.what_changed",
            "card.expected_benefit",
            "card.evidence_delta",
            "risk.lowest_risk_version_id",
        ]:
            self.assertIn(runtime_field, html)

    def test_creative_version_control_has_bilingual_copy_guard_and_collapsed_governance(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "creativeVersionControlTitle",
            "creativeVersionTimelineTitle",
            "creativeVersionComparisonTitle",
            "creativeVersionRecommendedNextTitle",
            "creativeVersionRiskSummaryTitle",
            "creativeVersionCopyRecommended",
            "creativeVersionCopyVersion",
            "creativeVersionCopyComparison",
            "creativeVersionCopyTimeline",
            "creativeVersionCopyRisk",
            "creativeVersionCopied",
            "creativeVersionCopyFailed",
            "creativeVersionCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace creative version control bundle", script)
            self.assertIn("project_workspace_creative_version_control_marker", script)
        markdown_start = html.index(
            "function projectWorkspaceExportCreativeVersionControlMarkdown"
        )
        markdown_end = html.index(
            "async function copyProjectWorkspaceCreativeVersionControlText",
            markdown_start,
        )
        markdown = html[markdown_start:markdown_end]
        for marker in [
            "creativeVersionControlTitle",
            "creativeVersionTimelineTitle",
            "creativeVersionComparisonTitle",
            "creativeVersionRecommendedNextTitle",
            "creativeVersionRiskSummaryTitle",
        ]:
            self.assertIn(marker, markdown)
        governance_start = html.index("function renderProjectWorkspaceProviderGovernanceGroup")
        governance_end = html.index("function projectWorkspaceExportPackMarkdownText", governance_start)
        governance = html[governance_start:governance_end]
        self.assertIn('<details class="section-block" id="projectWorkspaceProviderGovernanceGroup">', governance)
        self.assertNotIn("<details open", governance)
        creative_section = html[
            html.index("const PROJECT_WORKSPACE_CREATIVE_DECISION_PACK_MARKER"):
            governance_start
        ]
        self.assertNotIn("fetch(", creative_section)
        self.assertNotIn("????", html)

    def test_creative_asset_pack_workspace_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace creative asset pack bundle",
            "PROJECT_WORKSPACE_CREATIVE_ASSET_PACK_MARKER",
            "latestProjectCreativeAssetPack",
            "projectWorkspaceCreativeAssetPackFromWorkspace",
            "projectWorkspaceExportCreativeAssetPackSnapshot",
            "projectWorkspaceExportCreativeAssetPackMarkdown",
            "renderProjectWorkspaceCreativeAssetPackSummaryPanel",
            "renderProjectWorkspaceCreativeShootingScriptPanel",
            "renderProjectWorkspaceCreativeVideoAssetsPanel",
            "renderProjectWorkspaceCreativeCaptionAssetsPanel",
            "copyProjectWorkspaceCreativeShootingScript",
            "copyProjectWorkspaceCreativeKeyframePrompts",
            "copyProjectWorkspaceCreativeSubtitleLines",
            "copyProjectWorkspaceCreativeCaptionVariants",
            "copyProjectWorkspaceCreativeFullAssetPack",
            "creative_asset_pack: projectWorkspaceExportCreativeAssetPackSnapshot(workspace)",
            "Creative Asset Pack",
            "Shooting Script",
            "Keyframe Prompts",
            "Subtitle Lines",
            "Caption Variants",
            "Thumbnail Prompt",
            "B-roll Notes",
            "Copy Full Asset Pack",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for runtime_field in [
            "pack.asset_pack_summary",
            "pack.asset_packs",
            "pack.recommended_asset_pack_id",
            "asset.shooting_script",
            "asset.keyframe_prompts",
            "asset.subtitle_lines",
            "asset.caption_variants",
            "asset.thumbnail_prompt",
            "asset.b_roll_notes",
            "asset.do_not_claim",
        ]:
            self.assertIn(runtime_field, html)
        version_risk = html.index(
            "${renderProjectWorkspaceCreativeVersionRiskSummaryPanel(workspace)}"
        )
        asset_summary = html.index(
            "${renderProjectWorkspaceCreativeAssetPackSummaryPanel(workspace)}"
        )
        creative_export = html.index(
            "${renderProjectWorkspaceCreativeExportPanel(workspace)}"
        )
        self.assertLess(version_risk, asset_summary)
        self.assertLess(asset_summary, creative_export)

    def test_creative_asset_pack_has_bilingual_copy_guard_and_safe_workspace_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "creativeAssetPackTitle",
            "creativeAssetShootingScriptTitle",
            "creativeAssetKeyframePromptsTitle",
            "creativeAssetSubtitleLinesTitle",
            "creativeAssetCaptionVariantsTitle",
            "creativeAssetThumbnailPrompt",
            "creativeAssetBRollNotes",
            "creativeAssetCopyFullPack",
            "creativeAssetCopied",
            "creativeAssetCopyFailed",
            "creativeAssetCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace creative asset pack bundle", script)
            self.assertIn("project_workspace_creative_asset_pack_marker", script)
        markdown_start = html.index(
            "function projectWorkspaceExportCreativeAssetPackMarkdown"
        )
        markdown_end = html.index(
            "async function copyProjectWorkspaceCreativeAssetText",
            markdown_start,
        )
        markdown = html[markdown_start:markdown_end]
        for key in [
            "creativeAssetPackTitle",
            "creativeAssetShootingScriptTitle",
            "creativeAssetKeyframePromptsTitle",
            "creativeAssetSubtitleLinesTitle",
            "creativeAssetCaptionVariantsTitle",
            "creativeAssetThumbnailPrompt",
            "creativeAssetSafetyNotesTitle",
        ]:
            self.assertIn(key, markdown)
        governance_start = html.index("function renderProjectWorkspaceProviderGovernanceGroup")
        governance_end = html.index("function projectWorkspaceExportPackMarkdownText", governance_start)
        governance = html[governance_start:governance_end]
        self.assertIn('<details class="section-block" id="projectWorkspaceProviderGovernanceGroup">', governance)
        self.assertNotIn("<details open", governance)
        creative_section = html[
            html.index("const PROJECT_WORKSPACE_CREATIVE_DECISION_PACK_MARKER"):
            governance_start
        ]
        self.assertNotIn("fetch(", creative_section)
        self.assertNotIn("????", html)

    def test_multi_platform_asset_pack_workspace_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace multi platform asset pack bundle",
            "PROJECT_WORKSPACE_MULTI_PLATFORM_ASSET_PACK_MARKER",
            "latestProjectMultiPlatformAssetPack",
            "projectWorkspaceMultiPlatformAssetPackFromWorkspace",
            "projectWorkspaceExportMultiPlatformAssetPackSnapshot",
            "projectWorkspaceExportMultiPlatformAssetPackMarkdown",
            "renderProjectWorkspaceMultiPlatformAssetPackSummaryPanel",
            "renderProjectWorkspaceMultiPlatformAssetPackCardsPanel",
            "renderProjectWorkspaceMultiPlatformAssetPackComparePanel",
            "copyProjectWorkspacePlatformAssetPack",
            "copyProjectWorkspaceDurationAssetPack",
            "copyProjectWorkspaceMultiPlatformAssetPack",
            "multi_platform_asset_pack: projectWorkspaceExportMultiPlatformAssetPackSnapshot(workspace)",
            "Multi-Platform Asset Pack",
            "TikTok Pack",
            "Instagram Reels Pack",
            "YouTube Shorts Pack",
            "15s Pack",
            "30s Pack",
            "45s Pack",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for runtime_field in [
            "pack.multi_platform_summary",
            "pack.platform_packs",
            "pack.recommended_platform_pack_id",
            "item.platform",
            "item.duration_seconds",
            "item.opening_hook",
            "item.pacing_strategy",
            "item.claim_safety_level",
            "item.asset_readiness",
            "item.recommended_next_action",
        ]:
            self.assertIn(runtime_field, html)

    def test_multi_platform_asset_pack_has_bilingual_guard_export_and_collapsed_governance(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "multiPlatformAssetPackTitle",
            "multiPlatformCardsTitle",
            "multiPlatformCompareTitle",
            "multiPlatformTikTokPackTitle",
            "multiPlatformReelsPackTitle",
            "multiPlatformShortsPackTitle",
            "multiPlatformCopyTikTok",
            "multiPlatformCopyReels",
            "multiPlatformCopyShorts",
            "multiPlatformCopy15",
            "multiPlatformCopy30",
            "multiPlatformCopy45",
            "multiPlatformCopyFullPack",
            "multiPlatformCopied",
            "multiPlatformCopyFailed",
            "multiPlatformCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace multi platform asset pack bundle", script)
            self.assertIn("project_workspace_multi_platform_asset_pack_marker", script)
        markdown_start = html.index(
            "function projectWorkspaceExportMultiPlatformAssetPackMarkdown"
        )
        markdown_end = html.index(
            "async function copyProjectWorkspaceMultiPlatformAssetPack",
            markdown_start,
        )
        markdown = html[markdown_start:markdown_end]
        for key in [
            "multiPlatformAssetPackTitle",
            "multiPlatformTikTokPackTitle",
            "multiPlatformReelsPackTitle",
            "multiPlatformShortsPackTitle",
            "multiPlatformDuration15",
            "multiPlatformDuration30",
            "multiPlatformDuration45",
            "creativeAssetSafetyNotesTitle",
        ]:
            self.assertIn(key, markdown)
        governance_start = html.index("function renderProjectWorkspaceProviderGovernanceGroup")
        governance_end = html.index("function projectWorkspaceExportPackMarkdownText", governance_start)
        governance = html[governance_start:governance_end]
        self.assertIn('<details class="section-block" id="projectWorkspaceProviderGovernanceGroup">', governance)
        self.assertNotIn("<details open", governance)
        creative_section = html[
            html.index("const PROJECT_WORKSPACE_CREATIVE_DECISION_PACK_MARKER"):
            governance_start
        ]
        self.assertNotIn("fetch(", creative_section)
        self.assertNotIn("????", html)

    def test_asset_quality_gate_workspace_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace asset quality gate bundle",
            "PROJECT_WORKSPACE_ASSET_QUALITY_GATE_MARKER",
            "latestProjectAssetQualityGatePack",
            "projectWorkspaceAssetQualityGatePackFromWorkspace",
            "projectWorkspaceExportAssetQualityGateSnapshot",
            "projectWorkspaceExportAssetQualityGateMarkdown",
            "renderProjectWorkspaceAssetQualitySummaryPanel",
            "renderProjectWorkspaceAssetQualityCardsPanel",
            "renderProjectWorkspaceMissingAssetChecklistPanel",
            "renderProjectWorkspaceAssetQualityFixActionsPanel",
            "copyProjectWorkspaceAssetQualitySummary",
            "copyProjectWorkspaceAssetQualityCard",
            "copyProjectWorkspaceMissingAssetChecklist",
            "copyProjectWorkspaceAssetQualityFixActions",
            "copyProjectWorkspaceFullAssetQualityPack",
            "asset_quality_gate_pack: projectWorkspaceExportAssetQualityGateSnapshot(workspace)",
            "Asset Quality Gate",
            "Quality Scores",
            "Missing Asset Checklist",
            "Recommended Fix Actions",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for runtime_field in [
            "pack.quality_summary",
            "pack.quality_cards",
            "pack.missing_asset_checklist",
            "pack.recommended_fix_actions",
            "card.overall_quality_score",
            "card.completeness_score",
            "card.evidence_coverage_score",
            "card.safety_score",
            "card.delivery_readiness",
            "card.fix_recommendations",
        ]:
            self.assertIn(runtime_field, html)

    def test_asset_quality_gate_has_bilingual_guard_export_and_collapsed_governance(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "assetQualityGateTitle",
            "assetQualityScoresTitle",
            "assetQualityMissingChecklistTitle",
            "assetQualityFixActionsTitle",
            "assetQualityRecommendedPack",
            "assetQualityOverallScore",
            "assetQualityCompletenessScore",
            "assetQualityEvidenceScore",
            "assetQualitySafetyScore",
            "assetQualityCopySummary",
            "assetQualityCopyCard",
            "assetQualityCopyChecklist",
            "assetQualityCopyFixActions",
            "assetQualityCopyFullPack",
            "assetQualityCopied",
            "assetQualityCopyFailed",
            "assetQualityCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace asset quality gate bundle", script)
            self.assertIn("project_workspace_asset_quality_gate_marker", script)
        markdown_start = html.index(
            "function projectWorkspaceExportAssetQualityGateMarkdown"
        )
        markdown_end = html.index(
            "async function copyProjectWorkspaceAssetQualityText",
            markdown_start,
        )
        markdown = html[markdown_start:markdown_end]
        for key in [
            "assetQualityGateTitle",
            "assetQualityScoresTitle",
            "assetQualityMissingChecklistTitle",
            "assetQualityFixActionsTitle",
            "creativeAssetSafetyNotesTitle",
        ]:
            self.assertIn(key, markdown)
        governance_start = html.index("function renderProjectWorkspaceProviderGovernanceGroup")
        governance_end = html.index("function projectWorkspaceExportPackMarkdownText", governance_start)
        governance = html[governance_start:governance_end]
        self.assertIn('<details class="section-block" id="projectWorkspaceProviderGovernanceGroup">', governance)
        self.assertNotIn("<details open", governance)
        creative_section = html[
            html.index("const PROJECT_WORKSPACE_CREATIVE_DECISION_PACK_MARKER"):
            governance_start
        ]
        self.assertNotIn("fetch(", creative_section)
        self.assertNotIn("????", html)

    def test_campaign_export_workspace_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace campaign export pack bundle",
            "PROJECT_WORKSPACE_CAMPAIGN_EXPORT_PACK_MARKER",
            "latestProjectCampaignExportPack",
            "projectWorkspaceCampaignExportPackFromWorkspace",
            "projectWorkspaceExportCampaignPackSnapshot",
            "projectWorkspaceExportCampaignPackMarkdown",
            "renderProjectWorkspaceCampaignExportSummaryPanel",
            "renderProjectWorkspaceCampaignBriefPanel",
            "renderProjectWorkspaceCampaignSectionsPanel",
            "renderProjectWorkspaceCampaignExportManifestPanel",
            "copyProjectWorkspaceCampaignBrief",
            "copyProjectWorkspaceCampaignEvidenceSection",
            "copyProjectWorkspaceCampaignCreativeScriptSection",
            "copyProjectWorkspaceCampaignPlatformAssetsSection",
            "copyProjectWorkspaceCampaignQualityGateSection",
            "copyProjectWorkspaceCampaignTestPlanSection",
            "copyProjectWorkspaceCampaignSafetyNotes",
            "copyProjectWorkspaceFullCampaignExportPack",
            "campaign_export_pack: projectWorkspaceExportCampaignPackSnapshot(workspace)",
            "Campaign Export Pack",
            "Campaign Brief",
            "Campaign Sections",
            "Export Manifest",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for runtime_field in [
            "pack.campaign_summary",
            "pack.campaign_brief",
            "pack.evidence_section",
            "pack.creative_section",
            "pack.platform_assets_section",
            "pack.quality_gate_section",
            "pack.test_plan_section",
            "pack.safety_section",
            "pack.export_manifest",
            "pack.campaign_quality_checks",
            "pack.safety_boundaries",
        ]:
            self.assertIn(runtime_field, html)
        quality_fix = html.index(
            "${renderProjectWorkspaceAssetQualityFixActionsPanel(workspace)}"
        )
        campaign_summary = html.index(
            "${renderProjectWorkspaceCampaignExportSummaryPanel(workspace)}"
        )
        creative_export = html.index(
            "${renderProjectWorkspaceCreativeExportPanel(workspace)}"
        )
        self.assertLess(quality_fix, campaign_summary)
        self.assertLess(campaign_summary, creative_export)

    def test_campaign_export_has_bilingual_guard_markdown_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "campaignExportPackTitle",
            "campaignExportCampaignBriefTitle",
            "campaignExportEvidenceTitle",
            "campaignExportCreativeScriptTitle",
            "campaignExportPlatformAssetsTitle",
            "campaignExportQualityGateTitle",
            "campaignExportAbTestPlanTitle",
            "campaignExportSafetyNotesTitle",
            "campaignExportManifestTitle",
            "campaignExportCopyCampaignBrief",
            "campaignExportCopyEvidence",
            "campaignExportCopyCreativeScript",
            "campaignExportCopyPlatformAssets",
            "campaignExportCopyQualityGate",
            "campaignExportCopyTestPlan",
            "campaignExportCopySafetyNotes",
            "campaignExportCopyFullPack",
            "campaignExportCopied",
            "campaignExportCopyFailed",
            "campaignExportCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace campaign export pack bundle", script)
            self.assertIn("project_workspace_campaign_export_pack_marker", script)
        markdown_start = html.index(
            "function projectWorkspaceExportCampaignPackMarkdown"
        )
        markdown_end = html.index(
            "async function copyProjectWorkspaceCampaignExportText",
            markdown_start,
        )
        markdown = html[markdown_start:markdown_end]
        for key in [
            "campaignExportPackTitle",
            "campaignExportCampaignBriefTitle",
            "campaignExportEvidenceTitle",
            "campaignExportCreativeScriptTitle",
            "campaignExportPlatformAssetsTitle",
            "campaignExportQualityGateTitle",
            "campaignExportAbTestPlanTitle",
            "campaignExportSafetyNotesTitle",
            "campaignExportManifestTitle",
        ]:
            self.assertIn(key, markdown)
        governance_start = html.index("function renderProjectWorkspaceProviderGovernanceGroup")
        governance_end = html.index("function projectWorkspaceExportPackMarkdownText", governance_start)
        governance = html[governance_start:governance_end]
        self.assertIn('<details class="section-block" id="projectWorkspaceProviderGovernanceGroup">', governance)
        self.assertNotIn("<details open", governance)
        creative_section = html[
            html.index("const PROJECT_WORKSPACE_CREATIVE_DECISION_PACK_MARKER"):
            governance_start
        ]
        self.assertNotIn("fetch(", creative_section)
        self.assertIn("feedback persistence remain disabled", html)
        self.assertNotIn("????", html)

    def test_review_import_workspace_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace review import pack bundle",
            "PROJECT_WORKSPACE_REVIEW_IMPORT_PACK_MARKER",
            "latestProjectReviewImportPack",
            "projectWorkspaceReviewImportPackFromWorkspace",
            "projectWorkspaceExportReviewImportPackSnapshot",
            "projectWorkspaceExportReviewImportPackMarkdown",
            "renderProjectWorkspaceReviewImportSummaryPanel",
            "renderProjectWorkspaceNormalizedReviewsPanel",
            "renderProjectWorkspaceReviewImportSourcePanel",
            "renderProjectWorkspaceReviewImportQualityPanel",
            "copyProjectWorkspaceReviewImportSummary",
            "copyProjectWorkspaceNormalizedReviews",
            "copyProjectWorkspaceReviewImportSourceBreakdown",
            "copyProjectWorkspaceReviewImportQualityWarnings",
            "copyProjectWorkspaceFullReviewImportPack",
            "review_import_pack: projectWorkspaceExportReviewImportPackSnapshot(workspace)",
            "Review Import Pack",
            "Import Summary",
            "Normalized Reviews",
            "Source Breakdown / Duplicate Report",
            "Quality Warnings / Import Errors",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for runtime_field in [
            "pack.import_summary",
            "pack.normalized_reviews",
            "pack.source_breakdown",
            "pack.duplicate_report",
            "pack.quality_warnings",
            "pack.import_errors",
            "pack.import_quality_checks",
            "pack.safety_boundaries",
            "summary.raw_import_count",
            "summary.normalized_review_count",
            "summary.duplicate_review_count",
            "summary.usable_review_count",
            "summary.source_type_counts",
            "summary.average_quality_score",
            "summary.import_readiness",
            "summary.recommended_next_action",
            "review.review_id",
            "review.source_type",
            "review.rating",
            "review.review_title",
            "review.review_text",
            "review.normalized_text",
            "review.is_duplicate",
            "review.duplicate_of",
            "review.quality_score",
            "review.quality_tier",
            "review.detected_signals",
        ]:
            self.assertIn(runtime_field, html)
        for source_type in [
            "csv",
            "manual",
            "amazon_visible",
            "competitor",
            "unknown",
        ]:
            self.assertIn(source_type, html)
        supervisor = html.index(
            "${renderProjectWorkspaceSupervisorNextActionsPanel(workspace)}"
        )
        review_summary = html.index(
            "${renderProjectWorkspaceReviewImportSummaryPanel(workspace)}"
        )
        creative_core = html.index(
            "${renderProjectWorkspaceCreativeCoreFlowStrip(workspace)}"
        )
        self.assertLess(supervisor, review_summary)
        self.assertLess(review_summary, creative_core)

    def test_review_import_has_bilingual_guard_markdown_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "reviewImportPackTitle",
            "reviewImportPackHelper",
            "reviewImportSummaryTitle",
            "reviewImportRawCount",
            "reviewImportNormalizedCount",
            "reviewImportDuplicateCount",
            "reviewImportUsableCount",
            "reviewImportSourceTypeCounts",
            "reviewImportAverageQualityScore",
            "reviewImportReadiness",
            "reviewImportRecommendedNextAction",
            "reviewImportNormalizedReviewsTitle",
            "reviewImportSourcePanelTitle",
            "reviewImportQualityPanelTitle",
            "reviewImportDuplicateReportTitle",
            "reviewImportQualityWarnings",
            "reviewImportImportErrors",
            "reviewImportQualityChecks",
            "reviewImportSafetyNotesTitle",
            "reviewImportSafetyNote",
            "reviewImportCopySummary",
            "reviewImportCopyNormalized",
            "reviewImportCopySource",
            "reviewImportCopyQuality",
            "reviewImportCopyFullPack",
            "reviewImportCopied",
            "reviewImportCopyFailed",
            "reviewImportCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace review import pack bundle", script)
            self.assertIn("project_workspace_review_import_pack_marker", script)
        markdown_start = html.index(
            "function projectWorkspaceExportReviewImportPackMarkdown"
        )
        markdown_end = html.index(
            "async function copyProjectWorkspaceReviewImportText",
            markdown_start,
        )
        markdown = html[markdown_start:markdown_end]
        for key in [
            "reviewImportPackTitle",
            "reviewImportSummaryTitle",
            "reviewImportNormalizedReviewsTitle",
            "reviewImportSourcePanelTitle",
            "reviewImportQualityPanelTitle",
            "reviewImportSafetyNotesTitle",
            "reviewImportSafetyNote",
        ]:
            self.assertIn(key, markdown)
        review_import_section = html[
            html.index("const PROJECT_WORKSPACE_REVIEW_IMPORT_PACK_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", review_import_section)
        for disabled_boundary in [
            "provider",
            "LLM",
            "video",
            "media",
            "paid",
            "registry",
            "rollback",
        ]:
            self.assertIn(disabled_boundary, html)
        self.assertIn("empty_review_text", html)
        self.assertIn("missing_rating", html)
        self.assertIn("duplicate_review", html)
        self.assertIn("very_short_review", html)
        self.assertIn("unsupported_source_type", html)
        self.assertIn("weak_review_sample", html)
        self.assertNotIn("????", html)

    def test_competitor_review_comparison_workspace_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace competitor review comparison bundle",
            "PROJECT_WORKSPACE_COMPETITOR_REVIEW_COMPARISON_MARKER",
            "latestProjectCompetitorReviewComparisonPack",
            "projectWorkspaceCompetitorReviewComparisonPackFromWorkspace",
            "projectWorkspaceExportCompetitorReviewComparisonSnapshot",
            "projectWorkspaceExportCompetitorReviewComparisonMarkdown",
            "renderProjectWorkspaceCompetitorComparisonSummaryPanel",
            "renderProjectWorkspaceCompetitorProfilePanel",
            "renderProjectWorkspaceCompetitorGapPanel",
            "renderProjectWorkspaceCompetitorAnglesPanel",
            "copyProjectWorkspaceCompetitorComparisonSummary",
            "copyProjectWorkspaceCompetitorProfile",
            "copyProjectWorkspaceCompetitorGaps",
            "copyProjectWorkspaceCompetitorAngles",
            "copyProjectWorkspaceFullCompetitorComparisonPack",
            "competitor_review_comparison_pack: projectWorkspaceExportCompetitorReviewComparisonSnapshot(workspace)",
            "Competitor Review Comparison",
            "Own vs Competitor Review Profile",
            "Gap Opportunities",
            "Differentiation Angles",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for runtime_field in [
            "pack.comparison_summary",
            "pack.own_review_profile",
            "pack.competitor_review_profile",
            "pack.comparison_cards",
            "pack.gap_opportunity_cards",
            "pack.differentiation_angle_cards",
            "pack.competitor_risk_notes",
            "pack.recommended_competitor_actions",
            "pack.comparison_quality_checks",
            "pack.safety_boundaries",
            "summary.own_review_count",
            "summary.competitor_review_count",
            "summary.comparison_readiness",
            "summary.recommended_next_action",
            "card.gap_title",
            "card.competitor_pain",
            "card.our_possible_angle",
            "card.evidence_quote",
            "card.evidence_strength",
            "card.claim_safety_level",
            "card.risk_note",
            "card.do_not_claim",
            "card.angle_title",
            "card.creative_hook",
            "card.competitor_context",
            "card.our_positioning",
            "card.script_direction",
            "card.video_prompt_direction",
        ]:
            self.assertIn(runtime_field, html)
        review_quality = html.index(
            "${renderProjectWorkspaceReviewImportQualityPanel(workspace)}"
        )
        competitor_summary = html.index(
            "${renderProjectWorkspaceCompetitorComparisonSummaryPanel(workspace)}"
        )
        creative_core = html.index(
            "${renderProjectWorkspaceCreativeCoreFlowStrip(workspace)}"
        )
        self.assertLess(review_quality, competitor_summary)
        self.assertLess(competitor_summary, creative_core)

    def test_competitor_review_comparison_has_bilingual_guard_markdown_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "competitorComparisonPackTitle",
            "competitorComparisonPackHelper",
            "competitorComparisonSummaryTitle",
            "competitorComparisonOwnReviewCount",
            "competitorComparisonCompetitorReviewCount",
            "competitorComparisonReadiness",
            "competitorComparisonTopGap",
            "competitorComparisonTopAngle",
            "competitorComparisonRecommendedNextAction",
            "competitorComparisonProfileTitle",
            "competitorComparisonPainPoints",
            "competitorComparisonObjections",
            "competitorComparisonLikedPoints",
            "competitorComparisonUseCases",
            "competitorComparisonGapTitle",
            "competitorComparisonAnglesTitle",
            "competitorComparisonSafetyNotesTitle",
            "competitorComparisonSafetyNote",
            "competitorComparisonCopySummary",
            "competitorComparisonCopyProfile",
            "competitorComparisonCopyGaps",
            "competitorComparisonCopyAngles",
            "competitorComparisonCopyFullPack",
            "competitorComparisonCopied",
            "competitorComparisonCopyFailed",
            "competitorComparisonCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace competitor review comparison bundle", script)
            self.assertIn("project_workspace_competitor_review_comparison_marker", script)
        markdown_start = html.index(
            "function projectWorkspaceExportCompetitorReviewComparisonMarkdown"
        )
        markdown_end = html.index(
            "async function copyProjectWorkspaceCompetitorComparisonText",
            markdown_start,
        )
        markdown = html[markdown_start:markdown_end]
        for key in [
            "competitorComparisonPackTitle",
            "competitorComparisonProfileTitle",
            "competitorComparisonGapTitle",
            "competitorComparisonAnglesTitle",
            "competitorComparisonSafetyNotesTitle",
            "competitorComparisonSafetyNote",
        ]:
            self.assertIn(key, markdown)
        competitor_section = html[
            html.index("const PROJECT_WORKSPACE_COMPETITOR_REVIEW_COMPARISON_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", competitor_section)
        for disabled_boundary in [
            "Provider",
            "LLM",
            "video",
            "media",
            "paid",
            "registry",
            "rollback",
            "external scraping",
            "database persistence",
        ]:
            self.assertIn(disabled_boundary, html)
        self.assertNotIn("????", html)

    def test_llm_assist_dry_run_workspace_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace LLM assist dry-run bundle",
            "PROJECT_WORKSPACE_LLM_ASSIST_DRY_RUN_MARKER",
            "latestProjectLlmAssistDryRunPack",
            "projectWorkspaceLlmAssistDryRunPackFromWorkspace",
            "projectWorkspaceExportLlmAssistDryRunSnapshot",
            "projectWorkspaceExportLlmAssistDryRunMarkdown",
            "renderProjectWorkspaceLlmDryRunSummaryPanel",
            "renderProjectWorkspaceLlmDryRunPromptPlanPanel",
            "renderProjectWorkspaceLlmDryRunEvidenceClaimsPanel",
            "renderProjectWorkspaceLlmDryRunMockResponsePanel",
            "renderProjectWorkspaceLlmDryRunApprovalSafetyPanel",
            "copyProjectWorkspaceLlmDryRunSummary",
            "copyProjectWorkspaceLlmDryRunPromptPlan",
            "copyProjectWorkspaceLlmDryRunEvidenceBundle",
            "copyProjectWorkspaceLlmDryRunClaimsGuard",
            "copyProjectWorkspaceLlmDryRunMockResponse",
            "copyProjectWorkspaceFullLlmDryRunPack",
            "llm_assist_dry_run_pack: projectWorkspaceExportLlmAssistDryRunSnapshot(workspace)",
            "LLM Assist Dry-Run",
            "Prompt Plan",
            "Evidence Bundle",
            "Allowed Claims",
            "Do Not Claim",
            "Mock LLM Response",
            "Approval Gate",
            "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for runtime_field in [
            "pack.dry_run_summary",
            "pack.prompt_plan",
            "pack.evidence_bundle",
            "pack.allowed_claims",
            "pack.do_not_claim",
            "pack.output_contract",
            "pack.mock_llm_response",
            "pack.risk_checks",
            "pack.approval_gate",
            "pack.safety_boundaries",
            "summary.mode",
            "summary.readiness",
            "summary.real_call_status",
            "summary.recommended_next_action",
            "summary.weak_evidence",
            "summary.missing_quotes",
            "gate.real_llm_call_allowed",
            "gate.approval_required",
            "plan.system_instruction",
            "plan.user_prompt_preview",
            "plan.input_sections",
        ]:
            with self.subTest(runtime_field=runtime_field):
                self.assertIn(runtime_field, html)
        competitor_angles = html.index(
            "${renderProjectWorkspaceCompetitorAnglesPanel(workspace)}"
        )
        dry_run_summary = html.index(
            "${renderProjectWorkspaceLlmDryRunSummaryPanel(workspace)}"
        )
        dry_run_safety = html.index(
            "${renderProjectWorkspaceLlmDryRunApprovalSafetyPanel(workspace)}"
        )
        creative_core = html.index(
            "${renderProjectWorkspaceCreativeCoreFlowStrip(workspace)}"
        )
        self.assertLess(competitor_angles, dry_run_summary)
        self.assertLess(dry_run_summary, dry_run_safety)
        self.assertLess(dry_run_safety, creative_core)

    def test_llm_assist_dry_run_has_bilingual_guard_markdown_and_disabled_boundaries(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "llmDryRunPackTitle",
            "llmDryRunPackHelper",
            "llmDryRunSummaryTitle",
            "llmDryRunMode",
            "llmDryRunReadiness",
            "llmDryRunRealCallStatus",
            "llmDryRunRealCallAllowed",
            "llmDryRunApprovalRequired",
            "llmDryRunRecommendedNextAction",
            "llmDryRunPromptPlanTitle",
            "llmDryRunPromptObjective",
            "llmDryRunPromptPreview",
            "llmDryRunInputEvidenceReferences",
            "llmDryRunOutputRequirements",
            "llmDryRunSafetyInstructions",
            "llmDryRunEvidenceClaimsTitle",
            "llmDryRunEvidenceBundleTitle",
            "llmDryRunAllowedClaimsTitle",
            "llmDryRunDoNotClaimTitle",
            "llmDryRunWeakEvidence",
            "llmDryRunMissingQuotes",
            "llmDryRunMockResponseTitle",
            "llmDryRunPlaceholderWarning",
            "llmDryRunOutputContractTitle",
            "llmDryRunApprovalSafetyTitle",
            "llmDryRunApprovalGateTitle",
            "llmDryRunRiskChecksTitle",
            "llmDryRunSafetyBoundariesTitle",
            "llmDryRunSafetyNote",
            "llmDryRunCopySummary",
            "llmDryRunCopyPromptPlan",
            "llmDryRunCopyEvidenceBundle",
            "llmDryRunCopyClaimsGuard",
            "llmDryRunCopyMockResponse",
            "llmDryRunCopyFullPack",
            "llmDryRunCopied",
            "llmDryRunCopyFailed",
            "llmDryRunCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace LLM assist dry-run bundle", script)
            self.assertIn("project_workspace_llm_assist_dry_run_marker", script)
        markdown_start = html.index(
            "function projectWorkspaceExportLlmAssistDryRunMarkdown"
        )
        markdown_end = html.index(
            "async function copyProjectWorkspaceLlmDryRunText",
            markdown_start,
        )
        markdown = html[markdown_start:markdown_end]
        for key in [
            "llmDryRunPackTitle",
            "llmDryRunPromptPlanTitle",
            "llmDryRunEvidenceBundleTitle",
            "llmDryRunAllowedClaimsTitle",
            "llmDryRunDoNotClaimTitle",
            "llmDryRunMockResponseTitle",
            "llmDryRunApprovalGateTitle",
            "llmDryRunSafetyBoundariesTitle",
            "llmDryRunSafetyNote",
        ]:
            self.assertIn(key, markdown)
        dry_run_section = html[
            html.index("const PROJECT_WORKSPACE_LLM_ASSIST_DRY_RUN_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", dry_run_section)
        self.assertIn("Deterministic placeholder only", html)
        self.assertIn("This is not real LLM output", html)
        for disabled_boundary in [
            "Real LLM",
            "provider",
            "video",
            "media",
            "paid",
            "registry",
            "rollback",
            "external scraping",
            "database persistence",
        ]:
            self.assertIn(disabled_boundary, html)
        self.assertNotIn("????", html)

    def test_video_provider_orchestration_dry_run_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace video provider orchestration dry-run bundle",
            "PROJECT_WORKSPACE_VIDEO_PROVIDER_ORCHESTRATION_DRY_RUN_MARKER",
            "latestProjectVideoProviderOrchestrationDryRunPack",
            "projectWorkspaceVideoProviderOrchestrationDryRunPackFromWorkspace",
            "projectWorkspaceExportVideoProviderOrchestrationDryRunSnapshot",
            "projectWorkspaceExportVideoProviderOrchestrationDryRunMarkdown",
            "renderProjectWorkspaceVideoOrchestrationSummaryPanel",
            "renderProjectWorkspaceVideoJobPlanPanel",
            "renderProjectWorkspaceProviderCapabilityPlanPanel",
            "renderProjectWorkspaceVideoInputAssetsPanel",
            "renderProjectWorkspaceVideoCostMockPanel",
            "renderProjectWorkspaceVideoApprovalSafetyPanel",
            "copyProjectWorkspaceVideoDryRunSummary",
            "copyProjectWorkspaceVideoJobPlan",
            "copyProjectWorkspaceProviderCapabilityPlan",
            "copyProjectWorkspaceVideoInputAssetBundle",
            "copyProjectWorkspaceMockProviderResponse",
            "copyProjectWorkspaceVideoApprovalAbortRollbackPlan",
            "copyProjectWorkspaceFullVideoOrchestrationDryRunPack",
            "video_provider_orchestration_dry_run_pack: projectWorkspaceExportVideoProviderOrchestrationDryRunSnapshot(workspace)",
            "Video Provider Orchestration Dry-Run",
            "Video Job Plan",
            "Provider Capability Plan",
            "Input Asset Bundle",
            "Platform Delivery Specs",
            "Cost Placeholder",
            "Mock Provider Response",
            "Approval Gate",
            "Abort Plan",
            "Rollback Plan",
            "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for runtime_field in [
            "pack.dry_run_summary",
            "pack.video_job_plan",
            "pack.provider_capability_plan",
            "pack.input_asset_bundle",
            "pack.platform_delivery_specs",
            "pack.cost_estimate_placeholder",
            "pack.mock_provider_response",
            "pack.risk_checks",
            "pack.approval_gate",
            "pack.abort_plan",
            "pack.rollback_plan",
            "pack.safety_boundaries",
            "summary.mode",
            "summary.readiness",
            "summary.real_call_status",
            "summary.recommended_next_action",
            "gate.real_video_call_allowed",
            "gate.approval_required",
            "plan.source_campaign_id",
            "plan.source_asset_pack_id",
            "plan.keyframe_prompt",
            "plan.target_platform",
            "plan.target_duration_seconds",
            "plan.target_format",
        ]:
            with self.subTest(runtime_field=runtime_field):
                self.assertIn(runtime_field, html)
        llm_safety = html.index(
            "${renderProjectWorkspaceLlmDryRunApprovalSafetyPanel(workspace)}"
        )
        video_summary = html.index(
            "${renderProjectWorkspaceVideoOrchestrationSummaryPanel(workspace)}"
        )
        video_safety = html.index(
            "${renderProjectWorkspaceVideoApprovalSafetyPanel(workspace)}"
        )
        creative_core = html.index(
            "${renderProjectWorkspaceCreativeCoreFlowStrip(workspace)}"
        )
        self.assertLess(llm_safety, video_summary)
        self.assertLess(video_summary, video_safety)
        self.assertLess(video_safety, creative_core)

    def test_video_orchestration_dry_run_has_bilingual_guard_markdown_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "videoOrchestrationPackTitle",
            "videoOrchestrationPackHelper",
            "videoOrchestrationSummaryTitle",
            "videoOrchestrationMode",
            "videoOrchestrationReadiness",
            "videoOrchestrationRealCallStatus",
            "videoOrchestrationRealVideoAllowed",
            "videoOrchestrationApprovalRequired",
            "videoOrchestrationRecommendedNextAction",
            "videoOrchestrationJobPlanTitle",
            "videoOrchestrationJobObjective",
            "videoOrchestrationCreativeSource",
            "videoOrchestrationAssetSource",
            "videoOrchestrationPromptDirection",
            "videoOrchestrationTargetPlatform",
            "videoOrchestrationTargetDuration",
            "videoOrchestrationOutputFormat",
            "videoOrchestrationProviderPlanTitle",
            "videoOrchestrationCapabilityMatching",
            "videoOrchestrationProviderOptions",
            "videoOrchestrationCapabilityLimitations",
            "videoOrchestrationInputAssetsPanelTitle",
            "videoOrchestrationInputAssetTitle",
            "videoOrchestrationPlatformSpecsTitle",
            "videoOrchestrationCostMockPanelTitle",
            "videoOrchestrationCostPlaceholderTitle",
            "videoOrchestrationCostPlaceholderWarning",
            "videoOrchestrationMockProviderTitle",
            "videoOrchestrationMockProviderWarning",
            "videoOrchestrationApprovalSafetyTitle",
            "videoOrchestrationApprovalGateTitle",
            "videoOrchestrationRiskChecksTitle",
            "videoOrchestrationAbortPlanTitle",
            "videoOrchestrationRollbackPlanTitle",
            "videoOrchestrationSafetyBoundariesTitle",
            "videoOrchestrationSafetyNote",
            "videoOrchestrationCopySummary",
            "videoOrchestrationCopyJobPlan",
            "videoOrchestrationCopyProviderPlan",
            "videoOrchestrationCopyInputAssets",
            "videoOrchestrationCopyMockProvider",
            "videoOrchestrationCopyApprovalPlans",
            "videoOrchestrationCopyFullPack",
            "videoOrchestrationCopied",
            "videoOrchestrationCopyFailed",
            "videoOrchestrationCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn(
                "Project Workspace video provider orchestration dry-run bundle",
                script,
            )
            self.assertIn(
                "project_workspace_video_provider_orchestration_dry_run_marker",
                script,
            )
        markdown_start = html.index(
            "function projectWorkspaceVideoDryRunSummaryText"
        )
        markdown_end = html.index(
            "async function copyProjectWorkspaceVideoOrchestrationText",
            markdown_start,
        )
        markdown = html[markdown_start:markdown_end]
        for key in [
            "videoOrchestrationPackTitle",
            "videoOrchestrationJobPlanTitle",
            "videoOrchestrationProviderPlanTitle",
            "videoOrchestrationInputAssetTitle",
            "videoOrchestrationPlatformSpecsTitle",
            "videoOrchestrationCostPlaceholderTitle",
            "videoOrchestrationMockProviderTitle",
            "videoOrchestrationApprovalGateTitle",
            "videoOrchestrationAbortPlanTitle",
            "videoOrchestrationRollbackPlanTitle",
            "videoOrchestrationSafetyBoundariesTitle",
            "videoOrchestrationSafetyNote",
        ]:
            self.assertIn(key, markdown)
        dry_run_section = html[
            html.index(
                "const PROJECT_WORKSPACE_VIDEO_PROVIDER_ORCHESTRATION_DRY_RUN_MARKER"
            ):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", dry_run_section)
        self.assertIn("Deterministic placeholder only", html)
        self.assertIn("not real provider output", html)
        self.assertIn("not a real quote", html)
        for disabled_boundary in [
            "Real LLM",
            "provider",
            "video",
            "media",
            "paid",
            "registry",
            "rollback",
            "external scraping",
            "database persistence",
        ]:
            self.assertIn(disabled_boundary, html)
        self.assertNotIn("????", html)

    def test_workspace_session_snapshot_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace session snapshot bundle",
            "PROJECT_WORKSPACE_SESSION_SNAPSHOT_MARKER",
            "latestProjectWorkspaceSessionSnapshotPack",
            "projectWorkspaceSessionSnapshotPackFromWorkspace",
            "projectWorkspaceExportSessionSnapshot",
            "projectWorkspaceExportSessionSnapshotMarkdown",
            "renderProjectWorkspaceSessionSummaryPanel",
            "renderProjectWorkspaceSessionInputSourcePanel",
            "renderProjectWorkspaceSessionPackInventoryPanel",
            "renderProjectWorkspaceSessionExportHistoryPanel",
            "renderProjectWorkspaceSessionRestoreSafetyPanel",
            "copyProjectWorkspaceSessionSummary",
            "copyProjectWorkspaceSessionInputSource",
            "copyProjectWorkspaceSessionPackInventory",
            "copyProjectWorkspaceSessionExportManifest",
            "copyProjectWorkspaceSessionHistoryPreview",
            "copyProjectWorkspaceSessionRestorePlan",
            "copyProjectWorkspaceFullSessionSnapshotPack",
            "workspace_session_snapshot_pack: projectWorkspaceExportSessionSnapshot(workspace)",
            "Workspace Session Snapshot",
            "Run Identity",
            "Input Source Summary",
            "Pack Inventory",
            "Export Manifest",
            "History Entry Preview",
            "Restore Plan",
            "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for runtime_field in [
            "pack.session_summary",
            "pack.run_identity",
            "pack.input_source_summary",
            "pack.pack_inventory",
            "pack.export_manifest",
            "pack.restore_plan",
            "pack.history_entry_preview",
            "pack.quality_checks",
            "pack.risk_notes",
            "pack.safety_boundaries",
            "identity.run_id",
            "summary.mode",
            "summary.snapshot_status",
            "summary.recommended_next_action",
            "boundaries.database_persistence_enabled",
            "input.workspace_source",
            "input.raw_review_count",
            "input.unique_review_count",
            "input.duplicate_review_count",
            "input.normalized_review_count",
            "input.source_type_counts",
            "item.pack_name",
            "item.present",
            "item.pack_version",
            "item.snapshot_included",
        ]:
            with self.subTest(runtime_field=runtime_field):
                self.assertIn(runtime_field, html)
        video_safety = html.index(
            "${renderProjectWorkspaceVideoApprovalSafetyPanel(workspace)}"
        )
        session_summary = html.index(
            "${renderProjectWorkspaceSessionSummaryPanel(workspace)}"
        )
        session_safety = html.index(
            "${renderProjectWorkspaceSessionRestoreSafetyPanel(workspace)}"
        )
        creative_core = html.index(
            "${renderProjectWorkspaceCreativeCoreFlowStrip(workspace)}"
        )
        self.assertLess(video_safety, session_summary)
        self.assertLess(session_summary, session_safety)
        self.assertLess(session_safety, creative_core)

    def test_workspace_session_snapshot_has_bilingual_guard_markdown_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "workspaceSessionPackTitle",
            "workspaceSessionPackHelper",
            "workspaceSessionSummaryTitle",
            "workspaceSessionRunId",
            "workspaceSessionMode",
            "workspaceSessionReadiness",
            "workspaceSessionDatabasePersistence",
            "workspaceSessionRecommendedNextAction",
            "workspaceSessionRunIdentityTitle",
            "workspaceSessionInputSourceTitle",
            "workspaceSessionInputSourceType",
            "workspaceSessionRawReviewCount",
            "workspaceSessionUniqueReviewCount",
            "workspaceSessionDuplicateReviewCount",
            "workspaceSessionNormalizedReviewCount",
            "workspaceSessionSourceCounts",
            "workspaceSessionPackInventoryTitle",
            "workspaceSessionPackPresent",
            "workspaceSessionPackVersion",
            "workspaceSessionPackStatus",
            "workspaceSessionSnapshotIncluded",
            "workspaceSessionExportHistoryTitle",
            "workspaceSessionExportManifestTitle",
            "workspaceSessionHistoryPreviewTitle",
            "workspaceSessionExportableWarning",
            "workspaceSessionHistoryPreviewWarning",
            "workspaceSessionRestoreSafetyTitle",
            "workspaceSessionRestorePlanTitle",
            "workspaceSessionQualityChecksTitle",
            "workspaceSessionRiskNotesTitle",
            "workspaceSessionSafetyBoundariesTitle",
            "workspaceSessionRestorePreviewWarning",
            "workspaceSessionSafetyNote",
            "workspaceSessionCopySummary",
            "workspaceSessionCopyInputSource",
            "workspaceSessionCopyPackInventory",
            "workspaceSessionCopyExportManifest",
            "workspaceSessionCopyHistoryPreview",
            "workspaceSessionCopyRestorePlan",
            "workspaceSessionCopyFullPack",
            "workspaceSessionCopied",
            "workspaceSessionCopyFailed",
            "workspaceSessionCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace session snapshot bundle", script)
            self.assertIn("project_workspace_session_snapshot_marker", script)
        markdown_start = html.index(
            "function projectWorkspaceSessionSummaryText"
        )
        markdown_end = html.index(
            "async function copyProjectWorkspaceSessionSnapshotText",
            markdown_start,
        )
        markdown = html[markdown_start:markdown_end]
        for key in [
            "workspaceSessionPackTitle",
            "workspaceSessionRunIdentityTitle",
            "workspaceSessionInputSourceTitle",
            "workspaceSessionPackInventoryTitle",
            "workspaceSessionExportManifestTitle",
            "workspaceSessionHistoryPreviewTitle",
            "workspaceSessionRestorePlanTitle",
            "workspaceSessionSafetyBoundariesTitle",
            "workspaceSessionSafetyNote",
        ]:
            self.assertIn(key, markdown)
        session_section = html[
            html.index("const PROJECT_WORKSPACE_SESSION_SNAPSHOT_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", session_section)
        self.assertIn("Exportable snapshot only", html)
        self.assertIn("not a persisted database record", html)
        self.assertIn("History preview only", html)
        self.assertIn("Restore is preview-only", html)
        for disabled_boundary in [
            "Real LLM",
            "provider",
            "video",
            "media",
            "paid",
            "registry",
            "rollback",
            "external scraping",
            "database persistence",
        ]:
            self.assertIn(disabled_boundary, html)
        self.assertNotIn("????", html)

    def test_workspace_run_snapshot_compare_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace run snapshot compare bundle",
            "PROJECT_WORKSPACE_RUN_SNAPSHOT_COMPARE_MARKER",
            "latestProjectWorkspaceRunComparePack",
            "projectWorkspaceRunComparePackFromWorkspace",
            "projectWorkspaceExportRunCompareSnapshot",
            "projectWorkspaceExportRunCompareMarkdown",
            "renderProjectWorkspaceRunCompareSummaryPanel",
            "renderProjectWorkspaceRunIdentityPanel",
            "renderProjectWorkspaceRunPackReadinessPanel",
            "renderProjectWorkspaceRunDeltaPanel",
            "renderProjectWorkspaceRunFollowUpSafetyPanel",
            "copyProjectWorkspaceRunCompareSummary",
            "copyProjectWorkspaceRunIdentityComparison",
            "copyProjectWorkspaceRunPackInventoryDelta",
            "copyProjectWorkspaceRunReadinessDelta",
            "copyProjectWorkspaceRunRiskExportDelta",
            "copyProjectWorkspaceRunFollowUpActions",
            "copyProjectWorkspaceFullRunComparePack",
            "workspace_run_compare_pack: projectWorkspaceExportRunCompareSnapshot(workspace)",
            "Workspace Run Snapshot Compare",
            "Compare Summary",
            "Current Run Identity",
            "Previous Run Identity",
            "Pack Inventory Delta",
            "Readiness Delta",
            "Risk Delta",
            "Export Delta",
            "Follow-up Actions",
            "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for runtime_field in [
            "pack.compare_summary",
            "pack.current_run_identity",
            "pack.previous_run_identity",
            "pack.input_delta",
            "pack.pack_inventory_delta",
            "pack.readiness_delta",
            "pack.risk_delta",
            "pack.export_delta",
            "pack.recommended_follow_up_actions",
            "pack.compare_quality_checks",
            "pack.safety_boundaries",
            "summary.comparison_mode",
            "summary.current_run_id",
            "summary.previous_run_id",
            "summary.comparison_status",
            "summary.previous_snapshot_available",
            "summary.recommended_next_action",
            "item.pack_name",
            "item.current_present",
            "item.previous_present",
            "item.delta_status",
        ]:
            with self.subTest(runtime_field=runtime_field):
                self.assertIn(runtime_field, html)
        session_safety = html.index(
            "${renderProjectWorkspaceSessionRestoreSafetyPanel(workspace)}"
        )
        compare_summary = html.index(
            "${renderProjectWorkspaceRunCompareSummaryPanel(workspace)}"
        )
        compare_safety = html.index(
            "${renderProjectWorkspaceRunFollowUpSafetyPanel(workspace)}"
        )
        creative_core = html.index(
            "${renderProjectWorkspaceCreativeCoreFlowStrip(workspace)}"
        )
        self.assertLess(session_safety, compare_summary)
        self.assertLess(compare_summary, compare_safety)
        self.assertLess(compare_safety, creative_core)

    def test_workspace_run_compare_has_bilingual_guard_markdown_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "runComparePackTitle",
            "runComparePackHelper",
            "runCompareSummaryTitle",
            "runCompareMode",
            "runCompareCurrentRunId",
            "runComparePreviousRunId",
            "runCompareReadiness",
            "runCompareBaselineStatus",
            "runCompareRecommendedNextAction",
            "runCompareNoPrevious",
            "runCompareIdentityPanelTitle",
            "runCompareCurrentIdentityTitle",
            "runComparePreviousIdentityTitle",
            "runComparePreviousNotProvided",
            "runCompareNoHistoryReadNote",
            "runComparePackReadinessTitle",
            "runComparePackInventoryTitle",
            "runCompareCurrentPresence",
            "runComparePreviousPresence",
            "runCompareDeltaStatus",
            "runCompareReadinessDeltaTitle",
            "runCompareDeltaPanelTitle",
            "runCompareInputDeltaTitle",
            "runCompareRiskDeltaTitle",
            "runCompareExportDeltaTitle",
            "runCompareQualityChecksTitle",
            "runCompareFollowUpSafetyTitle",
            "runCompareFollowUpTitle",
            "runCompareSafetyBoundariesTitle",
            "runCompareSafetyNote",
            "runCompareCopySummary",
            "runCompareCopyIdentity",
            "runCompareCopyInventory",
            "runCompareCopyReadiness",
            "runCompareCopyRiskExport",
            "runCompareCopyFollowUp",
            "runCompareCopyFullPack",
            "runCompareCopied",
            "runCompareCopyFailed",
            "runCompareCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace run snapshot compare bundle", script)
            self.assertIn("project_workspace_run_snapshot_compare_marker", script)
        markdown_start = html.index(
            "function projectWorkspaceRunCompareSummaryText"
        )
        markdown_end = html.index(
            "async function copyProjectWorkspaceRunCompareText",
            markdown_start,
        )
        markdown = html[markdown_start:markdown_end]
        for key in [
            "runComparePackTitle",
            "runCompareSummaryTitle",
            "runCompareCurrentIdentityTitle",
            "runComparePreviousIdentityTitle",
            "runComparePackInventoryTitle",
            "runCompareReadinessDeltaTitle",
            "runCompareRiskDeltaTitle",
            "runCompareExportDeltaTitle",
            "runCompareFollowUpTitle",
            "runCompareSafetyBoundariesTitle",
            "runCompareSafetyNote",
        ]:
            self.assertIn(key, markdown)
        compare_section = html[
            html.index("const PROJECT_WORKSPACE_RUN_SNAPSHOT_COMPARE_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", compare_section)
        self.assertIn("no_previous_snapshot / baseline_only", html)
        self.assertIn("No previous snapshot was provided", html)
        self.assertIn("no real history lookup occurs", html)
        self.assertIn("Comparison preview only", html)
        for disabled_boundary in [
            "Real LLM",
            "provider",
            "video",
            "media",
            "paid",
            "registry",
            "rollback",
            "external scraping",
            "database persistence",
            "real restore",
        ]:
            self.assertIn(disabled_boundary, html)
        self.assertNotIn("????", html)

    def test_workspace_action_queue_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace action queue bundle",
            "PROJECT_WORKSPACE_ACTION_QUEUE_MARKER",
            "latestProjectWorkspaceActionQueuePack",
            "projectWorkspaceActionQueuePackFromWorkspace",
            "projectWorkspaceExportActionQueueSnapshot",
            "projectWorkspaceExportActionQueueMarkdown",
            "renderProjectWorkspaceActionQueueSummaryPanel",
            "renderProjectWorkspaceRecommendedActionsPanel",
            "renderProjectWorkspaceBlockedReadyActionsPanel",
            "renderProjectWorkspaceEvidenceSafetyActionsPanel",
            "renderProjectWorkspaceActionQueueExportSafetyPanel",
            "copyProjectWorkspaceActionQueueSummary",
            "copyProjectWorkspaceRecommendedActions",
            "copyProjectWorkspaceBlockedActions",
            "copyProjectWorkspaceEvidenceGapActions",
            "copyProjectWorkspaceSafetyReviewActions",
            "copyProjectWorkspaceExportFollowUpActions",
            "copyProjectWorkspaceFullActionQueuePack",
            "workspace_action_queue_pack: projectWorkspaceExportActionQueueSnapshot(workspace)",
            "Workspace Action Recommendation Queue",
            "Queue Summary",
            "Recommended Actions",
            "Blocked Actions",
            "Ready Actions",
            "Evidence Gap Actions",
            "Safety Review Actions",
            "Export Follow-up Actions",
            "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for runtime_field in [
            "pack.queue_summary",
            "pack.recommended_actions",
            "pack.blocked_actions",
            "pack.ready_actions",
            "pack.evidence_gap_actions",
            "pack.safety_review_actions",
            "pack.export_follow_up_actions",
            "pack.queue_quality_checks",
            "pack.safety_boundaries",
            "summary.recommended_action_count",
            "summary.ready_action_count",
            "summary.blocked_action_count",
            "summary.evidence_gap_action_count",
            "summary.safety_review_action_count",
            "summary.export_follow_up_action_count",
            "summary.recommended_next_action",
            "summary.real_execution_allowed",
            "action.action_title",
            "action.action_type",
            "action.priority",
            "action.source_pack",
            "action.reason",
            "action.expected_user_value",
            "action.recommended_next_step",
            "action.requires_approval",
            "action.real_execution_allowed",
            "action.blocked_by",
            "action.evidence_reference",
            "action.risk_note",
            "action.do_not_claim",
        ]:
            with self.subTest(runtime_field=runtime_field):
                self.assertIn(runtime_field, html)
        compare_safety = html.index(
            "${renderProjectWorkspaceRunFollowUpSafetyPanel(workspace)}"
        )
        queue_summary = html.index(
            "${renderProjectWorkspaceActionQueueSummaryPanel(workspace)}"
        )
        queue_safety = html.index(
            "${renderProjectWorkspaceActionQueueExportSafetyPanel(workspace)}"
        )
        creative_core = html.index(
            "${renderProjectWorkspaceCreativeCoreFlowStrip(workspace)}"
        )
        self.assertLess(compare_safety, queue_summary)
        self.assertLess(queue_summary, queue_safety)
        self.assertLess(queue_safety, creative_core)

    def test_workspace_action_queue_has_bilingual_guard_markdown_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "actionQueuePackTitle",
            "actionQueuePackHelper",
            "actionQueueSummaryTitle",
            "actionQueueRecommendedCount",
            "actionQueueReadyCount",
            "actionQueueBlockedCount",
            "actionQueueEvidenceGapCount",
            "actionQueueSafetyReviewCount",
            "actionQueueExportFollowUpCount",
            "actionQueueRecommendedNextAction",
            "actionQueueRealExecution",
            "actionQueueRecommendationOnlyNote",
            "actionQueueRecommendedActionsTitle",
            "actionQueueActionType",
            "actionQueuePriority",
            "actionQueueSourcePack",
            "actionQueueReason",
            "actionQueueExpectedValue",
            "actionQueueNextStep",
            "actionQueueRequiresApproval",
            "actionQueueRealExecutionAllowed",
            "actionQueueBlockedReadyTitle",
            "actionQueueBlockedActionsTitle",
            "actionQueueReadyActionsTitle",
            "actionQueueBlockedBy",
            "actionQueueReadyReviewOnlyNote",
            "actionQueueEvidenceSafetyTitle",
            "actionQueueEvidenceGapActionsTitle",
            "actionQueueSafetyReviewActionsTitle",
            "actionQueueEvidenceReference",
            "actionQueueRiskNote",
            "actionQueueDoNotClaim",
            "actionQueueExportSafetyTitle",
            "actionQueueExportFollowUpActionsTitle",
            "actionQueueQualityChecksTitle",
            "actionQueueSafetyBoundariesTitle",
            "actionQueueSafetyNote",
            "actionQueueCopySummary",
            "actionQueueCopyRecommended",
            "actionQueueCopyBlocked",
            "actionQueueCopyEvidenceGap",
            "actionQueueCopySafetyReview",
            "actionQueueCopyExportFollowUp",
            "actionQueueCopyFullPack",
            "actionQueueCopied",
            "actionQueueCopyFailed",
            "actionQueueCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace action queue bundle", script)
            self.assertIn("project_workspace_action_queue_marker", script)
        markdown_start = html.index(
            "function projectWorkspaceActionQueueSummaryText"
        )
        markdown_end = html.index(
            "async function copyProjectWorkspaceActionQueueText",
            markdown_start,
        )
        markdown = html[markdown_start:markdown_end]
        for key in [
            "actionQueuePackTitle",
            "actionQueueSummaryTitle",
            "actionQueueRecommendedActionsTitle",
            "actionQueueBlockedActionsTitle",
            "actionQueueReadyActionsTitle",
            "actionQueueEvidenceGapActionsTitle",
            "actionQueueSafetyReviewActionsTitle",
            "actionQueueExportFollowUpActionsTitle",
            "actionQueueSafetyBoundariesTitle",
            "actionQueueSafetyNote",
        ]:
            self.assertIn(key, markdown)
        queue_section = html[
            html.index("const PROJECT_WORKSPACE_ACTION_QUEUE_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", queue_section)
        self.assertIn("Recommendation queue only", html)
        self.assertIn("ready for user review only", html)
        for disabled_boundary in [
            "Real LLM",
            "provider",
            "video",
            "media",
            "paid",
            "registry",
            "rollback",
            "external scraping",
            "database persistence",
            "real restore",
            "real execution",
        ]:
            self.assertIn(disabled_boundary, html)
        self.assertNotIn("????", html)

    def test_workspace_action_ticket_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace action ticket bundle",
            "PROJECT_WORKSPACE_ACTION_TICKET_MARKER",
            "latestProjectWorkspaceActionTicketPack",
            "projectWorkspaceActionTicketPackFromWorkspace",
            "projectWorkspaceExportActionTicketSnapshot",
            "projectWorkspaceExportActionTicketMarkdown",
            "renderProjectWorkspaceActionTicketSummaryPanel",
            "renderProjectWorkspaceActionTicketsPanel",
            "renderProjectWorkspaceActionTicketApprovalPanel",
            "renderProjectWorkspaceActionTicketValidationPanel",
            "renderProjectWorkspaceActionTicketAuditSafetyPanel",
            "copyProjectWorkspaceActionTicketSummary",
            "copyProjectWorkspaceActionTickets",
            "copyProjectWorkspaceApprovalChecklist",
            "copyProjectWorkspacePreExecutionRequirements",
            "copyProjectWorkspaceActionTicketValidationPlan",
            "copyProjectWorkspaceActionTicketAbortConditions",
            "copyProjectWorkspaceActionTicketAuditPreview",
            "copyProjectWorkspaceFullActionTicketPack",
            "workspace_action_ticket_pack: projectWorkspaceExportActionTicketSnapshot(workspace)",
            "Workspace Action Ticket / Approval Packet",
            "Ticket Summary",
            "Action Tickets",
            "Approval Checklist",
            "Pre-Execution Requirements",
            "Validation Plan",
            "Abort Conditions",
            "Audit Preview",
            "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for runtime_field in [
            "pack.ticket_summary",
            "pack.action_tickets",
            "pack.approval_checklist",
            "pack.pre_execution_requirements",
            "pack.validation_plan",
            "pack.abort_conditions",
            "pack.blocked_ticket_notes",
            "pack.audit_trail_preview",
            "pack.ticket_quality_checks",
            "pack.safety_boundaries",
            "summary.ticket_count",
            "summary.pending_review_ticket_count",
            "summary.blocked_ticket_count",
            "summary.recommended_next_action",
            "summary.real_execution_allowed",
            "ticket.ticket_id",
            "ticket.ticket_title",
            "ticket.ticket_type",
            "ticket.priority",
            "ticket.source_pack",
            "ticket.approval_status",
            "ticket.requires_human_review",
            "ticket.real_execution_allowed",
            "ticket.preconditions",
            "ticket.validation_steps",
            "ticket.abort_conditions",
            "ticket.expected_user_value",
            "ticket.risk_note",
            "ticket.do_not_claim",
            "ticket.audit_note",
        ]:
            with self.subTest(runtime_field=runtime_field):
                self.assertIn(runtime_field, html)
        queue_safety = html.index(
            "${renderProjectWorkspaceActionQueueExportSafetyPanel(workspace)}"
        )
        ticket_summary = html.index(
            "${renderProjectWorkspaceActionTicketSummaryPanel(workspace)}"
        )
        ticket_safety = html.index(
            "${renderProjectWorkspaceActionTicketAuditSafetyPanel(workspace)}"
        )
        creative_core = html.index(
            "${renderProjectWorkspaceCreativeCoreFlowStrip(workspace)}"
        )
        self.assertLess(queue_safety, ticket_summary)
        self.assertLess(ticket_summary, ticket_safety)
        self.assertLess(ticket_safety, creative_core)

    def test_workspace_action_ticket_has_bilingual_guard_markdown_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "actionTicketPackTitle",
            "actionTicketPackHelper",
            "actionTicketSummaryTitle",
            "actionTicketTotalCount",
            "actionTicketPendingCount",
            "actionTicketBlockedCount",
            "actionTicketReviewRequiredCount",
            "actionTicketRecommendedNextAction",
            "actionTicketRealExecution",
            "actionTicketReviewOnlyNote",
            "actionTicketTicketsTitle",
            "actionTicketId",
            "actionTicketType",
            "actionTicketPriority",
            "actionTicketSourcePack",
            "actionTicketApprovalStatus",
            "actionTicketHumanReview",
            "actionTicketRealExecutionAllowed",
            "actionTicketExpectedValue",
            "actionTicketRiskNote",
            "actionTicketDoNotClaim",
            "actionTicketApprovalPanelTitle",
            "actionTicketApprovalChecklistTitle",
            "actionTicketPreExecutionTitle",
            "actionTicketPreconditionsTitle",
            "actionTicketApprovalNotAuthorization",
            "actionTicketValidationAbortTitle",
            "actionTicketValidationPlanTitle",
            "actionTicketAbortConditionsTitle",
            "actionTicketTicketValidationTitle",
            "actionTicketBlockedNotesTitle",
            "actionTicketAuditSafetyTitle",
            "actionTicketAuditPreviewTitle",
            "actionTicketQualityChecksTitle",
            "actionTicketSafetyBoundariesTitle",
            "actionTicketAuditNoWriteNote",
            "actionTicketSafetyNote",
            "actionTicketCopySummary",
            "actionTicketCopyTickets",
            "actionTicketCopyApproval",
            "actionTicketCopyRequirements",
            "actionTicketCopyValidation",
            "actionTicketCopyAbort",
            "actionTicketCopyAudit",
            "actionTicketCopyFullPack",
            "actionTicketCopied",
            "actionTicketCopyFailed",
            "actionTicketCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace action ticket bundle", script)
            self.assertIn("project_workspace_action_ticket_marker", script)
        markdown_start = html.index(
            "function projectWorkspaceActionTicketSummaryText"
        )
        markdown_end = html.index(
            "async function copyProjectWorkspaceActionTicketText",
            markdown_start,
        )
        markdown = html[markdown_start:markdown_end]
        for key in [
            "actionTicketPackTitle",
            "actionTicketSummaryTitle",
            "actionTicketTicketsTitle",
            "actionTicketApprovalChecklistTitle",
            "actionTicketPreExecutionTitle",
            "actionTicketValidationPlanTitle",
            "actionTicketAbortConditionsTitle",
            "actionTicketAuditPreviewTitle",
            "actionTicketSafetyBoundariesTitle",
            "actionTicketSafetyNote",
        ]:
            self.assertIn(key, markdown)
        ticket_section = html[
            html.index("const PROJECT_WORKSPACE_ACTION_TICKET_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", ticket_section)
        self.assertIn("Approval packet review only", html)
        self.assertIn("not authorization for real execution", html)
        self.assertIn("Audit preview only", html)
        for disabled_boundary in [
            "Real LLM",
            "provider",
            "video",
            "media",
            "paid",
            "registry",
            "rollback",
            "external scraping",
            "database persistence",
            "real restore",
            "real execution",
        ]:
            self.assertIn(disabled_boundary, html)
        self.assertNotIn("????", html)

    def test_workspace_approval_decision_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace approval decision bundle",
            "PROJECT_WORKSPACE_APPROVAL_DECISION_MARKER",
            "latestProjectWorkspaceApprovalDecisionPack",
            "projectWorkspaceApprovalDecisionPackFromWorkspace",
            "projectWorkspaceExportApprovalDecisionSnapshot",
            "projectWorkspaceExportApprovalDecisionMarkdown",
            "renderProjectWorkspaceApprovalDecisionSummaryPanel",
            "renderProjectWorkspaceDecisionLedgerPanel",
            "renderProjectWorkspaceDecisionBucketsPanel",
            "renderProjectWorkspaceHumanReviewGatePanel",
            "renderProjectWorkspaceDecisionAuditSafetyPanel",
            "copyProjectWorkspaceApprovalSummary",
            "copyProjectWorkspaceDecisionLedger",
            "copyProjectWorkspacePendingDecisions",
            "copyProjectWorkspaceBlockedDecisions",
            "copyProjectWorkspaceReviewReadyDecisions",
            "copyProjectWorkspaceHumanReviewRequirements",
            "copyProjectWorkspaceGateChecks",
            "copyProjectWorkspaceDecisionAuditPreview",
            "copyProjectWorkspaceFullApprovalDecisionPack",
            "workspace_approval_decision_pack: projectWorkspaceExportApprovalDecisionSnapshot(workspace)",
            "Workspace Approval Decision / Gate Ledger",
            "Approval Summary",
            "Decision Ledger",
            "Pending Decisions",
            "Blocked Decisions",
            "Review Ready Decisions",
            "Human Review Requirements",
            "Gate Checks",
            "Decision Audit Preview",
            "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for runtime_field in [
            "pack.approval_summary",
            "pack.decision_ledger",
            "pack.pending_decisions",
            "pack.blocked_decisions",
            "pack.review_ready_decisions",
            "pack.human_review_requirements",
            "pack.gate_checks",
            "pack.decision_audit_preview",
            "pack.approval_quality_checks",
            "pack.safety_boundaries",
            "summary.decision_count",
            "summary.pending_decision_count",
            "summary.blocked_decision_count",
            "summary.review_ready_decision_count",
            "summary.recommended_next_action",
            "summary.real_execution_allowed",
            "decision.decision_id",
            "decision.source_ticket_id",
            "decision.decision_title",
            "decision.decision_type",
            "decision.priority",
            "decision.source_pack",
            "decision.ticket_approval_status",
            "decision.gate_status",
            "decision.decision_status",
            "decision.human_review_required",
            "decision.real_execution_allowed",
            "decision.blocking_reasons",
            "decision.required_evidence",
            "decision.validation_required",
            "decision.risk_note",
            "decision.do_not_claim",
        ]:
            with self.subTest(runtime_field=runtime_field):
                self.assertIn(runtime_field, html)
        ticket_safety = html.index(
            "${renderProjectWorkspaceActionTicketAuditSafetyPanel(workspace)}"
        )
        approval_summary = html.index(
            "${renderProjectWorkspaceApprovalDecisionSummaryPanel(workspace)}"
        )
        approval_safety = html.index(
            "${renderProjectWorkspaceDecisionAuditSafetyPanel(workspace)}"
        )
        creative_core = html.index(
            "${renderProjectWorkspaceCreativeCoreFlowStrip(workspace)}"
        )
        self.assertLess(ticket_safety, approval_summary)
        self.assertLess(approval_summary, approval_safety)
        self.assertLess(approval_safety, creative_core)

    def test_workspace_approval_decision_has_bilingual_guard_markdown_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "approvalDecisionPackTitle",
            "approvalDecisionPackHelper",
            "approvalDecisionSummaryTitle",
            "approvalDecisionTotalCount",
            "approvalDecisionPendingCount",
            "approvalDecisionBlockedCount",
            "approvalDecisionReviewReadyCount",
            "approvalDecisionRecommendedNextAction",
            "approvalDecisionRealExecution",
            "approvalDecisionPreviewOnlyNote",
            "approvalDecisionLedgerTitle",
            "approvalDecisionId",
            "approvalDecisionSourceTicketId",
            "approvalDecisionType",
            "approvalDecisionPriority",
            "approvalDecisionSourcePack",
            "approvalDecisionTicketStatus",
            "approvalDecisionGateStatus",
            "approvalDecisionDecisionStatus",
            "approvalDecisionHumanReviewRequired",
            "approvalDecisionRealExecutionAllowed",
            "approvalDecisionBucketsTitle",
            "approvalDecisionPendingTitle",
            "approvalDecisionBlockedTitle",
            "approvalDecisionReviewReadyTitle",
            "approvalDecisionBlockingReasons",
            "approvalDecisionRequiredEvidence",
            "approvalDecisionReviewReadyNote",
            "approvalDecisionHumanGateTitle",
            "approvalDecisionHumanReviewTitle",
            "approvalDecisionGateChecksTitle",
            "approvalDecisionValidationRiskTitle",
            "approvalDecisionAuditSafetyTitle",
            "approvalDecisionAuditPreviewTitle",
            "approvalDecisionQualityChecksTitle",
            "approvalDecisionSafetyBoundariesTitle",
            "approvalDecisionAuditNoWriteNote",
            "approvalDecisionSafetyNote",
            "approvalDecisionCopySummary",
            "approvalDecisionCopyLedger",
            "approvalDecisionCopyPending",
            "approvalDecisionCopyBlocked",
            "approvalDecisionCopyReviewReady",
            "approvalDecisionCopyHumanReview",
            "approvalDecisionCopyGateChecks",
            "approvalDecisionCopyAudit",
            "approvalDecisionCopyFullPack",
            "approvalDecisionCopied",
            "approvalDecisionCopyFailed",
            "approvalDecisionCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace approval decision bundle", script)
            self.assertIn("project_workspace_approval_decision_marker", script)
        markdown_start = html.index(
            "function projectWorkspaceApprovalDecisionSummaryText"
        )
        markdown_end = html.index(
            "async function copyProjectWorkspaceApprovalDecisionText",
            markdown_start,
        )
        markdown = html[markdown_start:markdown_end]
        for key in [
            "approvalDecisionPackTitle",
            "approvalDecisionSummaryTitle",
            "approvalDecisionLedgerTitle",
            "approvalDecisionPendingTitle",
            "approvalDecisionBlockedTitle",
            "approvalDecisionReviewReadyTitle",
            "approvalDecisionHumanReviewTitle",
            "approvalDecisionGateChecksTitle",
            "approvalDecisionAuditPreviewTitle",
            "approvalDecisionSafetyBoundariesTitle",
            "approvalDecisionSafetyNote",
        ]:
            self.assertIn(key, markdown)
        approval_section = html[
            html.index("const PROJECT_WORKSPACE_APPROVAL_DECISION_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", approval_section)
        self.assertIn("Approval preview only", html)
        self.assertIn("ready_for_human_review only", html)
        self.assertIn("Audit preview only", html)
        for disabled_boundary in [
            "Real LLM",
            "provider",
            "video",
            "media",
            "paid",
            "registry",
            "rollback",
            "external scraping",
            "database persistence",
            "real restore",
            "real execution",
        ]:
            self.assertIn(disabled_boundary, html)
        self.assertNotIn("????", html)

    def test_workspace_execution_readiness_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace execution readiness bundle",
            "PROJECT_WORKSPACE_EXECUTION_READINESS_MARKER",
            "latestProjectWorkspaceExecutionReadinessPack",
            "projectWorkspaceExecutionReadinessPackFromWorkspace",
            "projectWorkspaceExportExecutionReadinessSnapshot",
            "projectWorkspaceExportExecutionReadinessMarkdown",
            "renderProjectWorkspaceExecutionReadinessSummaryPanel",
            "renderProjectWorkspaceLaunchLockPanel",
            "renderProjectWorkspacePreflightManualReviewPanel",
            "renderProjectWorkspaceBlockedRiskPanel",
            "renderProjectWorkspaceDryRunReadinessSafetyPanel",
            "copyProjectWorkspaceReadinessSummary",
            "copyProjectWorkspaceLaunchLock",
            "copyProjectWorkspacePreflightChecklist",
            "copyProjectWorkspaceManualReviewRequirements",
            "copyProjectWorkspaceBlockedExecutionReasons",
            "copyProjectWorkspaceExecutionRiskRegister",
            "copyProjectWorkspaceDryRunEnforcement",
            "copyProjectWorkspaceFullExecutionReadinessPack",
            "workspace_execution_readiness_pack: projectWorkspaceExportExecutionReadinessSnapshot(workspace)",
            "Workspace Execution Readiness / Launch Lock",
            "Readiness Summary",
            "Launch Lock",
            "Preflight Checklist",
            "Manual Review Requirements",
            "Blocked Execution Reasons",
            "Execution Risk Register",
            "Dry-Run Enforcement",
            "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for runtime_field in [
            "pack.readiness_summary",
            "pack.launch_lock",
            "pack.preflight_checklist",
            "pack.blocked_execution_reasons",
            "pack.manual_review_requirements",
            "pack.dry_run_enforcement",
            "pack.approved_for_review_items",
            "pack.not_approved_items",
            "pack.execution_risk_register",
            "pack.readiness_quality_checks",
            "pack.safety_boundaries",
            "summary.readiness_status",
            "summary.launch_lock_status",
            "summary.blocked_count",
            "summary.review_ready_count",
            "summary.manual_review_required_count",
            "summary.recommended_next_action",
            "summary.real_execution_allowed",
            "lock.lock_id",
            "lock.lock_status",
            "lock.lock_reason",
            "lock.unlock_requirements",
            "lock.dry_run_only",
            "lock.human_approval_required",
            "lock.real_execution_allowed",
        ]:
            with self.subTest(runtime_field=runtime_field):
                self.assertIn(runtime_field, html)
        approval_safety = html.index(
            "${renderProjectWorkspaceDecisionAuditSafetyPanel(workspace)}"
        )
        readiness_summary = html.index(
            "${renderProjectWorkspaceExecutionReadinessSummaryPanel(workspace)}"
        )
        readiness_safety = html.index(
            "${renderProjectWorkspaceDryRunReadinessSafetyPanel(workspace)}"
        )
        creative_core = html.index(
            "${renderProjectWorkspaceCreativeCoreFlowStrip(workspace)}"
        )
        self.assertLess(approval_safety, readiness_summary)
        self.assertLess(readiness_summary, readiness_safety)
        self.assertLess(readiness_safety, creative_core)

    def test_workspace_execution_readiness_has_bilingual_guard_markdown_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "executionReadinessPackTitle",
            "executionReadinessPackHelper",
            "executionReadinessSummaryTitle",
            "executionReadinessStatus",
            "executionReadinessLockStatus",
            "executionReadinessBlockedCount",
            "executionReadinessReviewReadyCount",
            "executionReadinessManualReviewCount",
            "executionReadinessRecommendedNextAction",
            "executionReadinessRealExecution",
            "executionReadinessPreviewNote",
            "executionReadinessLaunchLockTitle",
            "executionReadinessLockId",
            "executionReadinessLockReason",
            "executionReadinessUnlockRequirements",
            "executionReadinessDryRunOnly",
            "executionReadinessHumanApproval",
            "executionReadinessNeverUnlockedNote",
            "executionReadinessPreflightManualTitle",
            "executionReadinessPreflightTitle",
            "executionReadinessManualReviewTitle",
            "executionReadinessApprovedReviewTitle",
            "executionReadinessNotApprovedTitle",
            "executionReadinessReviewOnlyNote",
            "executionReadinessBlockedRiskTitle",
            "executionReadinessBlockedReasonsTitle",
            "executionReadinessRiskRegisterTitle",
            "executionReadinessEvidenceRiskNote",
            "executionReadinessDryQualitySafetyTitle",
            "executionReadinessDryRunTitle",
            "executionReadinessQualityChecksTitle",
            "executionReadinessSafetyBoundariesTitle",
            "executionReadinessNoWriteNote",
            "executionReadinessSafetyNote",
            "executionReadinessCopySummary",
            "executionReadinessCopyLock",
            "executionReadinessCopyPreflight",
            "executionReadinessCopyManualReview",
            "executionReadinessCopyBlocked",
            "executionReadinessCopyRisk",
            "executionReadinessCopyDryRun",
            "executionReadinessCopyFullPack",
            "executionReadinessCopied",
            "executionReadinessCopyFailed",
            "executionReadinessCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace execution readiness bundle", script)
            self.assertIn("project_workspace_execution_readiness_marker", script)
        markdown_start = html.index(
            "function projectWorkspaceExecutionReadinessSummaryText"
        )
        markdown_end = html.index(
            "async function copyProjectWorkspaceExecutionReadinessText",
            markdown_start,
        )
        markdown = html[markdown_start:markdown_end]
        for key in [
            "executionReadinessPackTitle",
            "executionReadinessSummaryTitle",
            "executionReadinessLaunchLockTitle",
            "executionReadinessPreflightTitle",
            "executionReadinessManualReviewTitle",
            "executionReadinessBlockedReasonsTitle",
            "executionReadinessRiskRegisterTitle",
            "executionReadinessDryRunTitle",
            "executionReadinessSafetyBoundariesTitle",
            "executionReadinessSafetyNote",
        ]:
            self.assertIn(key, markdown)
        readiness_section = html[
            html.index("const PROJECT_WORKSPACE_EXECUTION_READINESS_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", readiness_section)
        self.assertIn("unlocked_for_real_execution", html)
        self.assertIn("ready_for_human_review only", html)
        self.assertIn("Launch lock preview only", html)
        for disabled_boundary in [
            "Real LLM",
            "provider",
            "video",
            "media",
            "paid",
            "registry",
            "rollback",
            "external scraping",
            "database persistence",
            "real restore",
            "real execution",
        ]:
            self.assertIn(disabled_boundary, html)
        self.assertNotIn("????", html)

    def test_workspace_execution_rehearsal_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace execution rehearsal bundle",
            "PROJECT_WORKSPACE_EXECUTION_REHEARSAL_MARKER",
            "latestProjectWorkspaceExecutionRehearsalPack",
            "projectWorkspaceExecutionRehearsalPackFromWorkspace",
            "projectWorkspaceExportExecutionRehearsalSnapshot",
            "projectWorkspaceExportExecutionRehearsalMarkdown",
            "renderProjectWorkspaceExecutionRehearsalSummaryPanel",
            "renderProjectWorkspaceExecutionRehearsalRunbookPanel",
            "renderProjectWorkspaceExecutionRehearsalStepsPanel",
            "renderProjectWorkspaceExecutionRehearsalCheckpointTimelinePanel",
            "renderProjectWorkspaceExecutionRehearsalFailurePanel",
            "renderProjectWorkspaceExecutionRehearsalQualitySafetyPanel",
            "copyProjectWorkspaceExecutionRehearsalSummary",
            "copyProjectWorkspaceExecutionRehearsalRunbook",
            "copyProjectWorkspaceExecutionRehearsalSteps",
            "copyProjectWorkspaceExecutionRehearsalCheckpoints",
            "copyProjectWorkspaceExecutionRehearsalTimeline",
            "copyProjectWorkspaceExecutionRehearsalFailureChecks",
            "copyProjectWorkspaceExecutionRehearsalAbortRollback",
            "copyProjectWorkspaceFullExecutionRehearsalPack",
            "workspace_execution_rehearsal_pack: projectWorkspaceExportExecutionRehearsalSnapshot(workspace)",
            "Workspace Execution Rehearsal / Dry-Run Runbook",
            "Execution Rehearsal Summary",
            "Rehearsal Runbook",
            "Step Sequence",
            "Checkpoint Plan",
            "Mock Execution Timeline",
            "Failure Injection Checks",
            "Abort Triggers",
            "Rollback Rehearsal Plan",
            "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for runtime_field in [
            "pack.rehearsal_summary",
            "pack.rehearsal_runbook",
            "pack.step_sequence",
            "pack.checkpoint_plan",
            "pack.mock_execution_timeline",
            "pack.expected_outputs",
            "pack.failure_injection_checks",
            "pack.abort_triggers",
            "pack.rollback_rehearsal_plan",
            "pack.operator_notes",
            "pack.rehearsal_quality_checks",
            "pack.safety_boundaries",
            "summary.mode",
            "summary.rehearsal_status",
            "summary.readiness_status",
            "summary.launch_lock_status",
            "summary.step_count",
            "summary.recommended_next_action",
            "summary.real_execution_allowed",
            "step.step_id",
            "step.step_title",
            "step.step_type",
            "step.source_pack",
            "step.preconditions",
            "step.dry_run_action",
            "step.expected_observation",
            "step.validation_check",
            "step.failure_mode",
            "step.abort_trigger",
            "step.real_execution_allowed",
            "step.risk_note",
        ]:
            with self.subTest(runtime_field=runtime_field):
                self.assertIn(runtime_field, html)
        readiness_safety = html.index(
            "${renderProjectWorkspaceDryRunReadinessSafetyPanel(workspace)}"
        )
        rehearsal_summary = html.index(
            "${renderProjectWorkspaceExecutionRehearsalSummaryPanel(workspace)}"
        )
        rehearsal_safety = html.index(
            "${renderProjectWorkspaceExecutionRehearsalQualitySafetyPanel(workspace)}"
        )
        creative_core = html.index(
            "${renderProjectWorkspaceCreativeCoreFlowStrip(workspace)}"
        )
        self.assertLess(readiness_safety, rehearsal_summary)
        self.assertLess(rehearsal_summary, rehearsal_safety)
        self.assertLess(rehearsal_safety, creative_core)

    def test_workspace_execution_rehearsal_has_bilingual_guard_markdown_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "executionRehearsalPackTitle",
            "executionRehearsalPackHelper",
            "executionRehearsalSummaryTitle",
            "executionRehearsalMode",
            "executionRehearsalReadiness",
            "executionRehearsalLockStatus",
            "executionRehearsalStepCount",
            "executionRehearsalRecommendedNextAction",
            "executionRehearsalRealExecution",
            "executionRehearsalDisabled",
            "executionRehearsalPreviewNote",
            "executionRehearsalRunbookTitle",
            "executionRehearsalRunbookHelper",
            "executionRehearsalOperatorNotesTitle",
            "executionRehearsalExpectedOutputsTitle",
            "executionRehearsalRunbookNote",
            "executionRehearsalStepSequenceTitle",
            "executionRehearsalStepSequenceHelper",
            "executionRehearsalStepId",
            "executionRehearsalSourcePack",
            "executionRehearsalCheckpointTimelineTitle",
            "executionRehearsalCheckpointTimelineHelper",
            "executionRehearsalCheckpointPlanTitle",
            "executionRehearsalMockTimelineTitle",
            "executionRehearsalMockTimelineNote",
            "executionRehearsalFailurePanelTitle",
            "executionRehearsalFailurePanelHelper",
            "executionRehearsalFailureChecksTitle",
            "executionRehearsalAbortTriggersTitle",
            "executionRehearsalRollbackTitle",
            "executionRehearsalRollbackNote",
            "executionRehearsalQualitySafetyTitle",
            "executionRehearsalQualitySafetyHelper",
            "executionRehearsalSafetyBoundariesTitle",
            "executionRehearsalNoWriteNote",
            "executionRehearsalSafetyNote",
            "executionRehearsalNoData",
            "executionRehearsalCopySummary",
            "executionRehearsalCopyRunbook",
            "executionRehearsalCopySteps",
            "executionRehearsalCopyCheckpoints",
            "executionRehearsalCopyTimeline",
            "executionRehearsalCopyFailureChecks",
            "executionRehearsalCopyAbortRollback",
            "executionRehearsalCopyFullPack",
            "executionRehearsalCopied",
            "executionRehearsalCopyFailed",
            "executionRehearsalCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace execution rehearsal bundle", script)
            self.assertIn("project_workspace_execution_rehearsal_marker", script)
        markdown_start = html.index(
            "function projectWorkspaceExecutionRehearsalSummaryText"
        )
        markdown_end = html.index(
            "async function copyProjectWorkspaceExecutionRehearsalText",
            markdown_start,
        )
        markdown = html[markdown_start:markdown_end]
        for key in [
            "executionRehearsalPackTitle",
            "executionRehearsalSummaryTitle",
            "executionRehearsalRunbookTitle",
            "executionRehearsalStepSequenceTitle",
            "executionRehearsalCheckpointPlanTitle",
            "executionRehearsalMockTimelineTitle",
            "executionRehearsalFailureChecksTitle",
            "executionRehearsalAbortTriggersTitle",
            "executionRehearsalRollbackTitle",
            "executionRehearsalSafetyBoundariesTitle",
            "executionRehearsalSafetyNote",
        ]:
            self.assertIn(key, markdown)
        rehearsal_section = html[
            html.index("const PROJECT_WORKSPACE_EXECUTION_REHEARSAL_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", rehearsal_section)
        self.assertIn("deterministic placeholder, not a real execution log", html)
        self.assertIn("never performs real rollback or restore", html)
        self.assertIn("No database write, real failure injection", html)
        for disabled_boundary in [
            "Real LLM",
            "provider",
            "video",
            "media",
            "paid",
            "registry",
            "rollback",
            "external scraping",
            "database persistence",
            "real restore",
            "real execution",
        ]:
            self.assertIn(disabled_boundary, html)
        self.assertNotIn("????", html)

    def test_workspace_rehearsal_remediation_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace rehearsal remediation bundle",
            "PROJECT_WORKSPACE_REHEARSAL_REMEDIATION_MARKER",
            "latestProjectWorkspaceRehearsalRemediationPack",
            "projectWorkspaceRehearsalRemediationPackFromWorkspace",
            "projectWorkspaceExportRehearsalRemediationSnapshot",
            "projectWorkspaceExportRehearsalRemediationMarkdown",
            "renderProjectWorkspaceRehearsalRemediationSummaryPanel",
            "renderProjectWorkspaceRehearsalRemediationActionsPanel",
            "renderProjectWorkspaceRehearsalRetryPlanPanel",
            "renderProjectWorkspaceRehearsalResolutionPanel",
            "renderProjectWorkspaceRehearsalRemediationAuditSafetyPanel",
            "copyProjectWorkspaceRehearsalRemediationSummary",
            "copyProjectWorkspaceRehearsalRemediationActions",
            "copyProjectWorkspaceRehearsalRetryPlan",
            "copyProjectWorkspaceEvidenceGapFixes",
            "copyProjectWorkspaceRemediationOperatorFollowUp",
            "copyProjectWorkspaceBlockedResolutionPlan",
            "copyProjectWorkspaceRemediationAuditPreview",
            "copyProjectWorkspaceFullRehearsalRemediationPack",
            "workspace_rehearsal_remediation_pack: projectWorkspaceExportRehearsalRemediationSnapshot(workspace)",
            "Workspace Rehearsal Remediation / Retry Plan",
            "Remediation Summary",
            "Remediation Action Items",
            "Retry Plan",
            "Evidence Gap Fixes",
            "Operator Follow-up Plan",
            "Blocked Item Resolution Plan",
            "Next Rehearsal Plan",
            "Audit Preview",
            "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for field in [
            "pack.remediation_summary",
            "pack.remediation_action_items",
            "pack.retry_plan",
            "pack.evidence_gap_fixes",
            "pack.operator_follow_up_plan",
            "pack.blocked_item_resolution_plan",
            "pack.next_rehearsal_plan",
            "pack.remediation_priority_rationale",
            "pack.remediation_quality_checks",
            "pack.audit_preview",
            "pack.safety_boundaries",
            "summary.mode",
            "summary.action_count",
            "summary.recommended_next_action",
            "summary.real_execution_allowed",
            "action.action_id",
            "action.source_step_id",
            "action.issue_type",
            "action.remediation_title",
            "action.remediation_detail",
            "action.required_input",
            "action.owner",
            "action.priority",
            "action.validation_before_retry",
            "action.retry_eligible",
            "action.real_execution_allowed",
            "action.risk_note",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, html)
        result_audit = html.index(
            "${renderProjectWorkspaceRehearsalAuditSafetyPanel(workspace)}"
        )
        remediation_summary = html.index(
            "${renderProjectWorkspaceRehearsalRemediationSummaryPanel(workspace)}"
        )
        remediation_audit = html.index(
            "${renderProjectWorkspaceRehearsalRemediationAuditSafetyPanel(workspace)}"
        )
        creative_core = html.index(
            "${renderProjectWorkspaceCreativeCoreFlowStrip(workspace)}"
        )
        self.assertLess(result_audit, remediation_summary)
        self.assertLess(remediation_summary, remediation_audit)
        self.assertLess(remediation_audit, creative_core)

    def test_workspace_rehearsal_remediation_has_bilingual_guard_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "rehearsalRemediationPackTitle",
            "rehearsalRemediationSummaryTitle",
            "rehearsalRemediationActionItemsTitle",
            "rehearsalRemediationRetryPlanTitle",
            "rehearsalRemediationEvidenceFixesTitle",
            "rehearsalRemediationOperatorFollowUpTitle",
            "rehearsalRemediationBlockedResolutionTitle",
            "rehearsalRemediationNextPlanTitle",
            "rehearsalRemediationAuditPreviewTitle",
            "rehearsalRemediationSafetyBoundariesTitle",
            "rehearsalRemediationCopySummary",
            "rehearsalRemediationCopyActions",
            "rehearsalRemediationCopyRetry",
            "rehearsalRemediationCopyEvidence",
            "rehearsalRemediationCopyOperator",
            "rehearsalRemediationCopyBlocked",
            "rehearsalRemediationCopyAudit",
            "rehearsalRemediationCopyFullPack",
            "rehearsalRemediationCopied",
            "rehearsalRemediationCopyFailed",
            "rehearsalRemediationCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace rehearsal remediation bundle", script)
            self.assertIn("project_workspace_rehearsal_remediation_marker", script)
        markdown = html[
            html.index("function projectWorkspaceRehearsalRemediationSummaryText"):
            html.index("async function copyProjectWorkspaceRehearsalRemediationText")
        ]
        for key in [
            "rehearsalRemediationPackTitle",
            "rehearsalRemediationSummaryTitle",
            "rehearsalRemediationActionItemsTitle",
            "rehearsalRemediationRetryPlanTitle",
            "rehearsalRemediationEvidenceFixesTitle",
            "rehearsalRemediationOperatorFollowUpTitle",
            "rehearsalRemediationBlockedResolutionTitle",
            "rehearsalRemediationNextPlanTitle",
            "rehearsalRemediationAuditPreviewTitle",
            "rehearsalRemediationSafetyBoundariesTitle",
        ]:
            self.assertIn(key, markdown)
        section = html[
            html.index("const PROJECT_WORKSPACE_REHEARSAL_REMEDIATION_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", section)
        self.assertIn("Only a dry-run rehearsal retry is allowed", html)
        self.assertIn("No real ticket or external data collection occurs", html)
        for boundary in [
            "Real LLM", "provider", "video", "media", "paid",
            "registry", "rollback", "external scraping",
            "database persistence", "real restore", "real execution",
        ]:
            self.assertIn(boundary, html)
        self.assertNotIn("????", html)

    def test_workspace_remediation_verification_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace remediation verification bundle",
            "PROJECT_WORKSPACE_REMEDIATION_VERIFICATION_MARKER",
            "latestProjectWorkspaceRemediationVerificationPack",
            "projectWorkspaceRemediationVerificationPackFromWorkspace",
            "projectWorkspaceExportRemediationVerificationSnapshot",
            "projectWorkspaceExportRemediationVerificationMarkdown",
            "renderProjectWorkspaceRemediationVerificationSummaryPanel",
            "renderProjectWorkspaceActionVerificationCardsPanel",
            "renderProjectWorkspaceRetryReadinessGatePanel",
            "renderProjectWorkspaceVerificationInputsPanel",
            "renderProjectWorkspaceVerificationSignoffSafetyPanel",
            "copyProjectWorkspaceRemediationVerificationSummary",
            "copyProjectWorkspaceActionVerificationCards",
            "copyProjectWorkspaceRetryReadinessGate",
            "copyProjectWorkspaceVerificationBlockers",
            "copyProjectWorkspaceRequiredInputsChecklist",
            "copyProjectWorkspaceEvidenceReadinessReview",
            "copyProjectWorkspaceOperatorSignoffPreview",
            "copyProjectWorkspaceFullRemediationVerificationPack",
            "workspace_remediation_verification_pack: projectWorkspaceExportRemediationVerificationSnapshot(workspace)",
            "Workspace Remediation Verification / Retry Readiness",
            "Verification Summary", "Action Verification Cards",
            "Retry Readiness Gate", "Remaining Blockers",
            "Required Inputs Checklist", "Evidence Readiness Review",
            "Operator Signoff Preview", "Next Retry Scope",
            "Audit Preview", "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for field in [
            "pack.verification_summary", "pack.action_verification_cards",
            "pack.retry_readiness_gate", "pack.remaining_blockers",
            "pack.required_inputs_checklist", "pack.evidence_readiness_review",
            "pack.operator_signoff_preview", "pack.next_retry_scope",
            "pack.verification_quality_checks", "pack.audit_preview",
            "pack.safety_boundaries", "summary.mode",
            "summary.verification_status", "summary.action_verification_count",
            "summary.remaining_blocker_count", "summary.recommended_next_action",
            "summary.real_execution_allowed", "card.verification_id",
            "card.source_action_id", "card.source_step_id", "card.issue_type",
            "card.verification_status", "card.required_input",
            "card.input_available", "card.validation_before_retry",
            "card.retry_eligible", "card.remaining_gap",
            "card.operator_review_required", "card.real_execution_allowed",
            "card.risk_note",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, html)
        prior = html.index("${renderProjectWorkspaceRehearsalRemediationAuditSafetyPanel(workspace)}")
        summary = html.index("${renderProjectWorkspaceRemediationVerificationSummaryPanel(workspace)}")
        safety = html.index("${renderProjectWorkspaceVerificationSignoffSafetyPanel(workspace)}")
        core = html.index("${renderProjectWorkspaceCreativeCoreFlowStrip(workspace)}")
        self.assertLess(prior, summary)
        self.assertLess(summary, safety)
        self.assertLess(safety, core)

    def test_workspace_remediation_verification_has_bilingual_guard_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "remediationVerificationPackTitle", "remediationVerificationSummaryTitle",
            "remediationVerificationCardsTitle", "remediationVerificationRetryGateTitle",
            "remediationVerificationBlockersTitle", "remediationVerificationRequiredInputsTitle",
            "remediationVerificationEvidenceReviewTitle", "remediationVerificationSignoffTitle",
            "remediationVerificationNextScopeTitle", "remediationVerificationAuditTitle",
            "remediationVerificationSafetyTitle", "remediationVerificationCopySummary",
            "remediationVerificationCopyCards", "remediationVerificationCopyGate",
            "remediationVerificationCopyBlockers", "remediationVerificationCopyInputs",
            "remediationVerificationCopyEvidence", "remediationVerificationCopySignoff",
            "remediationVerificationCopyFull", "remediationVerificationCopied",
            "remediationVerificationCopyFailed", "remediationVerificationCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace remediation verification bundle", script)
            self.assertIn("project_workspace_remediation_verification_marker", script)
        markdown = html[
            html.index("function projectWorkspaceRemediationVerificationSummaryText"):
            html.index("async function copyProjectWorkspaceRemediationVerificationText")
        ]
        for key in [
            "remediationVerificationPackTitle", "remediationVerificationSummaryTitle",
            "remediationVerificationCardsTitle", "remediationVerificationRetryGateTitle",
            "remediationVerificationBlockersTitle", "remediationVerificationRequiredInputsTitle",
            "remediationVerificationEvidenceReviewTitle", "remediationVerificationSignoffTitle",
            "remediationVerificationNextScopeTitle", "remediationVerificationAuditTitle",
            "remediationVerificationSafetyTitle",
        ]:
            self.assertIn(key, markdown)
        section = html[
            html.index("const PROJECT_WORKSPACE_REMEDIATION_VERIFICATION_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", section)
        self.assertIn("ready_for_next_dry_run only", html)
        self.assertIn("never returns ready_for_real_execution", html)
        self.assertIn("No real external data is collected", html)
        for boundary in [
            "Real LLM", "provider", "video", "media", "paid", "registry",
            "rollback", "external scraping", "database persistence",
            "real restore", "real execution",
        ]:
            self.assertIn(boundary, html)
        self.assertNotIn("????", html)

    def test_workspace_retry_rehearsal_plan_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace retry rehearsal plan bundle",
            "PROJECT_WORKSPACE_RETRY_REHEARSAL_PLAN_MARKER",
            "latestProjectWorkspaceRetryRehearsalPlanPack",
            "projectWorkspaceRetryRehearsalPlanPackFromWorkspace",
            "projectWorkspaceExportRetryRehearsalPlanSnapshot",
            "projectWorkspaceExportRetryRehearsalPlanMarkdown",
            "renderProjectWorkspaceRetryRehearsalSummaryPanel",
            "renderProjectWorkspaceSecondPassStepSequencePanel",
            "renderProjectWorkspaceRetryBlockersOperatorPanel",
            "renderProjectWorkspaceRetryCheckpointMatrixPanel",
            "renderProjectWorkspaceRetryTimelineAbortSafetyPanel",
            "copyProjectWorkspaceRetryRehearsalSummary",
            "copyProjectWorkspaceRetryScope",
            "copyProjectWorkspaceSecondPassStepSequence",
            "copyProjectWorkspaceCarryForwardBlockers",
            "copyProjectWorkspaceTightenedCheckpointPlan",
            "copyProjectWorkspaceRetryValidationMatrix",
            "copyProjectWorkspaceMockRetryTimeline",
            "copyProjectWorkspaceRetryAbortPlan",
            "copyProjectWorkspaceFullRetryRehearsalPlanPack",
            "workspace_retry_rehearsal_plan_pack: projectWorkspaceExportRetryRehearsalPlanSnapshot(workspace)",
            "Workspace Retry Rehearsal Plan / Second-Pass Runbook",
            "Retry Rehearsal Summary", "Retry Scope",
            "Second-Pass Step Sequence", "Carry-Forward Blockers",
            "Tightened Checkpoint Plan", "Retry Validation Matrix",
            "Operator Review Before Retry", "Mock Retry Timeline",
            "Retry Abort Plan", "Audit Preview", "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for field in [
            "pack.retry_rehearsal_summary", "pack.retry_scope",
            "pack.second_pass_step_sequence", "pack.carry_forward_blockers",
            "pack.tightened_checkpoint_plan", "pack.retry_validation_matrix",
            "pack.operator_review_before_retry", "pack.mock_retry_timeline",
            "pack.retry_abort_plan", "pack.retry_quality_checks",
            "pack.audit_preview", "pack.safety_boundaries",
            "summary.mode", "summary.plan_status",
            "summary.second_pass_step_count", "summary.carry_forward_blocker_count",
            "summary.operator_review_required", "summary.recommended_next_action",
            "summary.real_execution_allowed", "step.retry_step_id",
            "step.source_verification_id", "step.source_action_id",
            "step.step_title", "step.step_type", "step.retry_reason",
            "step.preconditions", "step.dry_run_retry_action",
            "step.tightened_validation_check", "step.expected_observation",
            "step.remaining_gap", "step.abort_trigger",
            "step.retry_eligible", "step.real_execution_allowed",
            "step.risk_note",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, html)
        previous = html.index("${renderProjectWorkspaceVerificationSignoffSafetyPanel(workspace)}")
        summary = html.index("${renderProjectWorkspaceRetryRehearsalSummaryPanel(workspace)}")
        safety = html.index("${renderProjectWorkspaceRetryTimelineAbortSafetyPanel(workspace)}")
        core = html.index("${renderProjectWorkspaceCreativeCoreFlowStrip(workspace)}")
        self.assertLess(previous, summary)
        self.assertLess(summary, safety)
        self.assertLess(safety, core)

    def test_workspace_retry_rehearsal_plan_has_bilingual_guard_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "retryPlanPackTitle", "retryPlanSummaryTitle",
            "retryPlanScopeTitle", "retryPlanStepsTitle",
            "retryPlanBlockersTitle", "retryPlanCheckpointTitle",
            "retryPlanValidationMatrixTitle", "retryPlanOperatorReviewTitle",
            "retryPlanMockTimelineTitle", "retryPlanAbortTitle",
            "retryPlanAuditTitle", "retryPlanSafetyTitle",
            "retryPlanCopySummary", "retryPlanCopyScope",
            "retryPlanCopySteps", "retryPlanCopyBlockers",
            "retryPlanCopyCheckpoints", "retryPlanCopyMatrix",
            "retryPlanCopyTimeline", "retryPlanCopyAbort",
            "retryPlanCopyFull", "retryPlanCopied",
            "retryPlanCopyFailed", "retryPlanCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace retry rehearsal plan bundle", script)
            self.assertIn("project_workspace_retry_rehearsal_plan_marker", script)
        markdown = html[
            html.index("function projectWorkspaceRetryRehearsalPlanSummaryText"):
            html.index("async function copyProjectWorkspaceRetryRehearsalPlanText")
        ]
        for key in [
            "retryPlanPackTitle", "retryPlanSummaryTitle",
            "retryPlanScopeTitle", "retryPlanStepsTitle",
            "retryPlanBlockersTitle", "retryPlanCheckpointTitle",
            "retryPlanValidationMatrixTitle", "retryPlanOperatorReviewTitle",
            "retryPlanMockTimelineTitle", "retryPlanAbortTitle",
            "retryPlanAuditTitle", "retryPlanSafetyTitle",
        ]:
            self.assertIn(key, markdown)
        section = html[
            html.index("const PROJECT_WORKSPACE_RETRY_REHEARSAL_PLAN_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", section)
        self.assertIn("Second-pass dry-run preview only", html)
        self.assertIn("This is not a real retry", html)
        self.assertIn("No real approval, operator log, or ticket system record is created.", html)
        self.assertIn("dry-run validation matrix only", html)
        self.assertIn("not a real execution log", html)
        for boundary in [
            "Real LLM", "provider", "video", "media", "paid", "registry",
            "rollback", "external scraping", "database persistence",
            "real restore", "real execution",
        ]:
            self.assertIn(boundary, html)
        self.assertNotIn("????", html)

    def test_workspace_retry_rehearsal_result_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace retry rehearsal result bundle",
            "PROJECT_WORKSPACE_RETRY_REHEARSAL_RESULT_MARKER",
            "latestProjectWorkspaceRetryRehearsalResultPack",
            "projectWorkspaceRetryRehearsalResultPackFromWorkspace",
            "projectWorkspaceExportRetryRehearsalResultSnapshot",
            "projectWorkspaceExportRetryRehearsalResultMarkdown",
            "renderProjectWorkspaceRetryResultSummaryPanel",
            "renderProjectWorkspaceSecondPassStepResultsPanel",
            "renderProjectWorkspaceRetryCheckpointFailurePanel",
            "renderProjectWorkspaceRetryOperatorGapsPanel",
            "renderProjectWorkspaceRetryResultAuditSafetyPanel",
            "copyProjectWorkspaceRetryResultSummary",
            "copyProjectWorkspaceSecondPassStepResults",
            "copyProjectWorkspaceRetryCheckpointResults",
            "copyProjectWorkspaceRetryFailureFindings",
            "copyProjectWorkspaceCarryForwardBlockerResults",
            "copyProjectWorkspaceRemainingRetryGaps",
            "copyProjectWorkspaceNextCycleRecommendations",
            "copyProjectWorkspaceRetryResultAuditPreview",
            "copyProjectWorkspaceFullRetryRehearsalResultPack",
            "workspace_retry_rehearsal_result_pack: projectWorkspaceExportRetryRehearsalResultSnapshot(workspace)",
            "Workspace Retry Rehearsal Result / Second-Pass Operator Review",
            "Retry Result Summary", "Second-Pass Step Results",
            "Retry Checkpoint Results", "Retry Failure Findings",
            "Carry-Forward Blocker Results", "Operator Review After Retry",
            "Remaining Retry Gaps", "Next Cycle Recommendations",
            "Audit Preview", "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for field in [
            "pack.retry_result_summary", "pack.second_pass_step_results",
            "pack.retry_checkpoint_results", "pack.carry_forward_blocker_results",
            "pack.retry_failure_findings", "pack.operator_review_after_retry",
            "pack.remaining_retry_gaps", "pack.next_cycle_recommendations",
            "pack.retry_result_quality_checks", "pack.audit_preview",
            "pack.safety_boundaries", "summary.mode",
            "summary.result_status", "summary.second_pass_result_count",
            "summary.remaining_retry_gap_count", "summary.operator_review_required",
            "summary.recommended_next_action", "summary.real_execution_allowed",
            "result.result_id", "result.source_retry_step_id",
            "result.source_verification_id", "result.source_action_id",
            "result.step_title", "result.step_type",
            "result.simulated_retry_status", "result.expected_observation",
            "result.observed_placeholder", "result.tightened_validation_result",
            "result.remaining_gap", "result.operator_review_required",
            "result.follow_up_action", "result.real_execution_allowed",
            "result.risk_note",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, html)
        previous = html.index("${renderProjectWorkspaceRetryTimelineAbortSafetyPanel(workspace)}")
        summary = html.index("${renderProjectWorkspaceRetryResultSummaryPanel(workspace)}")
        safety = html.index("${renderProjectWorkspaceRetryResultAuditSafetyPanel(workspace)}")
        core = html.index("${renderProjectWorkspaceCreativeCoreFlowStrip(workspace)}")
        self.assertLess(previous, summary)
        self.assertLess(summary, safety)
        self.assertLess(safety, core)

    def test_workspace_retry_rehearsal_result_has_bilingual_guard_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "retryResultPackTitle", "retryResultSummaryTitle",
            "retryResultStepsTitle", "retryResultCheckpointTitle",
            "retryResultFailureTitle", "retryResultBlockerTitle",
            "retryResultOperatorReviewTitle", "retryResultRemainingGapsTitle",
            "retryResultNextCycleTitle", "retryResultAuditTitle",
            "retryResultSafetyTitle", "retryResultCopySummary",
            "retryResultCopySteps", "retryResultCopyCheckpoints",
            "retryResultCopyFailures", "retryResultCopyBlockers",
            "retryResultCopyGaps", "retryResultCopyNext",
            "retryResultCopyAudit", "retryResultCopyFull",
            "retryResultCopied", "retryResultCopyFailed",
            "retryResultCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace retry rehearsal result bundle", script)
            self.assertIn("project_workspace_retry_rehearsal_result_marker", script)
        markdown = html[
            html.index("function projectWorkspaceRetryRehearsalResultSummaryText"):
            html.index("async function copyProjectWorkspaceRetryRehearsalResultText")
        ]
        for key in [
            "retryResultPackTitle", "retryResultSummaryTitle",
            "retryResultStepsTitle", "retryResultCheckpointTitle",
            "retryResultFailureTitle", "retryResultBlockerTitle",
            "retryResultOperatorReviewTitle", "retryResultRemainingGapsTitle",
            "retryResultNextCycleTitle", "retryResultAuditTitle",
            "retryResultSafetyTitle",
        ]:
            self.assertIn(key, markdown)
        section = html[
            html.index("const PROJECT_WORKSPACE_RETRY_REHEARSAL_RESULT_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", section)
        self.assertIn("Second-pass dry-run result preview only", html)
        self.assertIn("not a real retry result", html)
        self.assertIn("not real operator logs", html)
        self.assertIn("does not mean real execution completed", html)
        for boundary in [
            "Real LLM", "provider", "video", "media", "paid", "registry",
            "rollback", "external scraping", "database persistence",
            "real restore", "real execution",
        ]:
            self.assertIn(boundary, html)
        self.assertNotIn("????", html)

    def test_workspace_retry_cycle_decision_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace retry cycle decision bundle",
            "PROJECT_WORKSPACE_RETRY_CYCLE_DECISION_MARKER",
            "latestProjectWorkspaceRetryCycleDecisionPack",
            "projectWorkspaceRetryCycleDecisionPackFromWorkspace",
            "projectWorkspaceExportRetryCycleDecisionSnapshot",
            "projectWorkspaceExportRetryCycleDecisionMarkdown",
            "renderProjectWorkspaceRetryCycleSummaryPanel",
            "renderProjectWorkspaceRetryCycleDecisionOptionsPanel",
            "renderProjectWorkspaceRetryCycleGateActionPanel",
            "renderProjectWorkspaceRetryCycleCarryManualPanel",
            "renderProjectWorkspaceRetryCycleScopeAuditSafetyPanel",
            "copyProjectWorkspaceRetryCycleDecisionSummary",
            "copyProjectWorkspaceRetryCycleDecisionOptions",
            "copyProjectWorkspaceRecommendedCycleAction",
            "copyProjectWorkspaceRetryCycleGate",
            "copyProjectWorkspaceRetryCycleCarryForwardItems",
            "copyProjectWorkspaceRetryCycleBlockedReviewItems",
            "copyProjectWorkspaceRetryCycleManualReviewPacket",
            "copyProjectWorkspaceRetryCycleNextScope",
            "copyProjectWorkspaceFullRetryCycleDecisionPack",
            "workspace_retry_cycle_decision_pack: projectWorkspaceExportRetryCycleDecisionSnapshot(workspace)",
            "Workspace Retry Cycle Decision / Next-Cycle Control",
            "Cycle Decision Summary", "Decision Options",
            "Recommended Cycle Action", "Cycle Gate",
            "Carry-Forward Items", "Blocked or Review-Required Items",
            "Manual Review Packet", "Next Cycle Scope",
            "Audit Preview", "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for field in [
            "pack.cycle_decision_summary", "pack.decision_options",
            "pack.recommended_cycle_action", "pack.cycle_gate",
            "pack.carry_forward_items",
            "pack.blocked_or_review_required_items",
            "pack.manual_review_packet", "pack.next_cycle_scope",
            "pack.decision_quality_checks", "pack.audit_preview",
            "pack.safety_boundaries", "summary.mode",
            "summary.decision_status", "summary.recommended_next_state",
            "summary.decision_option_count", "summary.carry_forward_item_count",
            "summary.blocked_or_review_required_count",
            "summary.real_execution_allowed", "option.option_id",
            "option.option_type", "option.option_title", "option.source_pack",
            "option.source_result_ids", "option.rationale",
            "option.required_inputs", "option.blocked_by",
            "option.recommended", "option.allowed_next_state",
            "option.real_execution_allowed", "option.risk_note",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, html)
        previous = html.index("${renderProjectWorkspaceRetryResultAuditSafetyPanel(workspace)}")
        summary = html.index("${renderProjectWorkspaceRetryCycleSummaryPanel(workspace)}")
        safety = html.index("${renderProjectWorkspaceRetryCycleScopeAuditSafetyPanel(workspace)}")
        core = html.index("${renderProjectWorkspaceCreativeCoreFlowStrip(workspace)}")
        self.assertLess(previous, summary)
        self.assertLess(summary, safety)
        self.assertLess(safety, core)

    def test_workspace_retry_cycle_decision_has_bilingual_guard_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "retryCyclePackTitle", "retryCycleSummaryTitle",
            "retryCycleDecisionOptionsTitle",
            "retryCycleRecommendedActionTitle",
            "retryCycleGateTitle", "retryCycleCarryForwardTitle",
            "retryCycleBlockedReviewTitle", "retryCycleManualReviewTitle",
            "retryCycleNextScopeTitle", "retryCycleAuditTitle",
            "retryCycleSafetyTitle", "retryCycleCopySummary",
            "retryCycleCopyOptions", "retryCycleCopyRecommended",
            "retryCycleCopyGate", "retryCycleCopyCarry",
            "retryCycleCopyBlocked", "retryCycleCopyManual",
            "retryCycleCopyScope", "retryCycleCopyFull",
            "retryCycleCopied", "retryCycleCopyFailed",
            "retryCycleCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace retry cycle decision bundle", script)
            self.assertIn("project_workspace_retry_cycle_decision_marker", script)
        markdown = html[
            html.index("function projectWorkspaceRetryCycleDecisionSummaryText"):
            html.index("async function copyProjectWorkspaceRetryCycleDecisionText")
        ]
        for key in [
            "retryCyclePackTitle", "retryCycleSummaryTitle",
            "retryCycleDecisionOptionsTitle",
            "retryCycleRecommendedActionTitle", "retryCycleGateTitle",
            "retryCycleCarryForwardTitle", "retryCycleBlockedReviewTitle",
            "retryCycleManualReviewTitle", "retryCycleNextScopeTitle",
            "retryCycleAuditTitle", "retryCycleSafetyTitle",
        ]:
            self.assertIn(key, markdown)
        section = html[
            html.index("const PROJECT_WORKSPACE_RETRY_CYCLE_DECISION_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", section)
        self.assertIn("Preview decision only", html)
        self.assertIn("not real execution", html)
        self.assertIn("never shows ready_for_real_execution", html)
        self.assertIn("No real approval, ticket, operator log, or database record is created.", html)
        self.assertIn("Next cycle scope does not perform real operations.", html)
        for boundary in [
            "Real LLM", "provider", "video", "media", "paid", "registry",
            "rollback", "external scraping", "database persistence",
            "real restore", "real execution",
        ]:
            self.assertIn(boundary, html)
        self.assertNotIn("????", html)

    def test_workspace_cycle_history_timeline_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace cycle history timeline bundle",
            "PROJECT_WORKSPACE_CYCLE_HISTORY_TIMELINE_MARKER",
            "latestProjectWorkspaceCycleHistoryTimelinePack",
            "projectWorkspaceCycleHistoryTimelinePackFromWorkspace",
            "projectWorkspaceExportCycleHistoryTimelineSnapshot",
            "projectWorkspaceExportCycleHistoryTimelineMarkdown",
            "renderProjectWorkspaceCycleHistorySummaryPanel",
            "renderProjectWorkspaceCycleHistoryEventsPanel",
            "renderProjectWorkspaceCycleHistoryLineageTracePanel",
            "renderProjectWorkspaceCycleHistoryStateTracePanel",
            "renderProjectWorkspaceCycleHistoryAuditSafetyPanel",
            "copyProjectWorkspaceCycleHistorySummary",
            "copyProjectWorkspaceCycleHistoryEvents",
            "copyProjectWorkspaceCycleHistoryLineageMap",
            "copyProjectWorkspaceCycleHistoryDecisionTraceMap",
            "copyProjectWorkspaceCycleHistoryStateTransitions",
            "copyProjectWorkspaceCycleHistoryCarryForwardTrace",
            "copyProjectWorkspaceCycleHistoryOperatorReviewTrace",
            "copyProjectWorkspaceCycleHistoryAuditTimelinePreview",
            "copyProjectWorkspaceFullCycleHistoryTimelinePack",
            "workspace_cycle_history_timeline_pack: projectWorkspaceExportCycleHistoryTimelineSnapshot(workspace)",
            "Workspace Cycle History / Decision Timeline",
            "Cycle History Summary", "Timeline Events",
            "Pack Lineage Map", "Decision Trace Map",
            "Cycle State Transitions", "Carry-Forward Trace",
            "Operator Review Trace", "Audit Timeline Preview",
            "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for field in [
            "pack.timeline_summary", "pack.timeline_events",
            "pack.pack_lineage_map", "pack.decision_trace_map",
            "pack.cycle_state_transitions", "pack.carry_forward_trace",
            "pack.operator_review_trace", "pack.audit_timeline_preview",
            "pack.timeline_quality_checks", "pack.safety_boundaries",
            "summary.mode", "summary.event_count",
            "summary.real_execution_allowed", "event.event_id",
            "event.event_order", "event.event_type", "event.event_title",
            "event.source_pack", "event.source_keys", "event.cycle_phase",
            "event.decision_or_status", "event.summary", "event.input_refs",
            "event.output_refs", "event.real_execution_allowed",
            "event.risk_note",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, html)
        previous = html.index("${renderProjectWorkspaceRetryCycleScopeAuditSafetyPanel(workspace)}")
        summary = html.index("${renderProjectWorkspaceCycleHistorySummaryPanel(workspace)}")
        safety = html.index("${renderProjectWorkspaceCycleHistoryAuditSafetyPanel(workspace)}")
        core = html.index("${renderProjectWorkspaceCreativeCoreFlowStrip(workspace)}")
        self.assertLess(previous, summary)
        self.assertLess(summary, safety)
        self.assertLess(safety, core)

    def test_workspace_cycle_history_timeline_has_bilingual_guard_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "cycleHistoryPackTitle", "cycleHistorySummaryTitle",
            "cycleHistoryEventsTitle", "cycleHistoryLineageTitle",
            "cycleHistoryDecisionTraceTitle", "cycleHistoryTransitionsTitle",
            "cycleHistoryCarryForwardTitle", "cycleHistoryOperatorReviewTitle",
            "cycleHistoryAuditTitle", "cycleHistorySafetyTitle",
            "cycleHistoryCopySummary", "cycleHistoryCopyEvents",
            "cycleHistoryCopyLineage", "cycleHistoryCopyDecisionTrace",
            "cycleHistoryCopyTransitions", "cycleHistoryCopyCarry",
            "cycleHistoryCopyOperator", "cycleHistoryCopyAudit",
            "cycleHistoryCopyFull", "cycleHistoryCopied",
            "cycleHistoryCopyFailed", "cycleHistoryCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace cycle history timeline bundle", script)
            self.assertIn("project_workspace_cycle_history_timeline_marker", script)
        markdown = html[
            html.index("function projectWorkspaceCycleHistoryTimelineSummaryText"):
            html.index("async function copyProjectWorkspaceCycleHistoryTimelineText")
        ]
        for key in [
            "cycleHistoryPackTitle", "cycleHistorySummaryTitle",
            "cycleHistoryEventsTitle", "cycleHistoryLineageTitle",
            "cycleHistoryDecisionTraceTitle", "cycleHistoryTransitionsTitle",
            "cycleHistoryCarryForwardTitle", "cycleHistoryOperatorReviewTitle",
            "cycleHistoryAuditTitle", "cycleHistorySafetyTitle",
        ]:
            self.assertIn(key, markdown)
        section = html[
            html.index("const PROJECT_WORKSPACE_CYCLE_HISTORY_TIMELINE_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", section)
        self.assertIn("Cycle history preview only", html)
        self.assertIn("not a real history database", html)
        self.assertIn("No real history table is read", html)
        self.assertIn("No real approval, ticket, operator log, or database record is created.", html)
        self.assertIn("does not read real history tables", html)
        for boundary in [
            "Real LLM", "provider", "video", "media", "paid", "registry",
            "rollback", "external scraping", "database persistence",
            "real restore", "real execution",
        ]:
            self.assertIn(boundary, html)
        self.assertNotIn("????", html)

    def test_workspace_control_center_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace control center bundle",
            "PROJECT_WORKSPACE_CONTROL_CENTER_MARKER",
            "latestProjectWorkspaceControlCenterPack",
            "projectWorkspaceControlCenterPackFromWorkspace",
            "projectWorkspaceExportControlCenterSnapshot",
            "projectWorkspaceExportControlCenterMarkdown",
            "renderProjectWorkspaceControlCenterSummaryPanel",
            "renderProjectWorkspaceControlCenterStatusCardsPanel",
            "renderProjectWorkspaceControlCenterPriorityQueuePanel",
            "renderProjectWorkspaceControlCenterDecisionRiskInventoryPanel",
            "renderProjectWorkspaceControlCenterLockAuditSafetyPanel",
            "copyProjectWorkspaceControlCenterSummary",
            "copyProjectWorkspaceControlCenterSystemCards",
            "copyProjectWorkspaceControlCenterPriorityQueue",
            "copyProjectWorkspaceControlCenterDecisionSnapshot",
            "copyProjectWorkspaceControlCenterNextBestActions",
            "copyProjectWorkspaceControlCenterRiskOverview",
            "copyProjectWorkspaceControlCenterPackInventory",
            "copyProjectWorkspaceControlCenterCapabilityLock",
            "copyProjectWorkspaceFullControlCenterPack",
            "workspace_control_center_pack: projectWorkspaceExportControlCenterSnapshot(workspace)",
            "Workspace Control Center / Operator Cockpit",
            "Control Center Summary", "System Status Cards",
            "Operator Priority Queue", "Current Decision Snapshot",
            "Next Best Actions", "Risk and Blocker Overview",
            "Pack Readiness Inventory", "Capability Lock Status",
            "Audit Preview", "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for field in [
            "pack.control_center_summary", "pack.system_status_cards",
            "pack.operator_priority_queue",
            "pack.current_decision_snapshot", "pack.next_best_actions",
            "pack.risk_and_blocker_overview",
            "pack.pack_readiness_inventory",
            "pack.capability_lock_status",
            "pack.control_quality_checks", "pack.audit_preview",
            "pack.safety_boundaries", "summary.mode",
            "summary.latest_decision_status", "summary.current_cycle_phase",
            "summary.recommended_next_action",
            "summary.real_execution_allowed", "card.card_id",
            "card.card_type", "card.card_title", "card.source_pack",
            "card.status", "card.summary", "card.priority",
            "card.recommended_operator_action",
            "card.real_execution_allowed", "card.risk_note",
            "item.queue_id", "item.priority", "item.source_pack",
            "item.item_type", "item.why_it_matters",
            "item.required_review", "item.blocked_by",
            "item.next_action_preview", "item.real_execution_allowed",
            "item.risk_note",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, html)
        previous = html.index("${renderProjectWorkspaceCycleHistoryAuditSafetyPanel(workspace)}")
        summary = html.index("${renderProjectWorkspaceControlCenterSummaryPanel(workspace)}")
        safety = html.index("${renderProjectWorkspaceControlCenterLockAuditSafetyPanel(workspace)}")
        core = html.index("${renderProjectWorkspaceCreativeCoreFlowStrip(workspace)}")
        self.assertLess(previous, summary)
        self.assertLess(summary, safety)
        self.assertLess(safety, core)

    def test_workspace_control_center_has_bilingual_guard_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "controlCenterPackTitle", "controlCenterSummaryTitle",
            "controlCenterSystemCardsTitle",
            "controlCenterPriorityQueueTitle",
            "controlCenterDecisionTitle",
            "controlCenterNextBestActionsTitle",
            "controlCenterRiskOverviewTitle",
            "controlCenterPackInventoryTitle",
            "controlCenterCapabilityLockTitle",
            "controlCenterAuditTitle", "controlCenterSafetyTitle",
            "controlCenterCopySummary", "controlCenterCopySystemCards",
            "controlCenterCopyPriorityQueue",
            "controlCenterCopyDecision",
            "controlCenterCopyNextBestActions",
            "controlCenterCopyRisk", "controlCenterCopyInventory",
            "controlCenterCopyCapabilityLock",
            "controlCenterCopyFull", "controlCenterCopied",
            "controlCenterCopyFailed", "controlCenterCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace control center bundle", script)
            self.assertIn("project_workspace_control_center_marker", script)
        markdown = html[
            html.index("function projectWorkspaceControlCenterSummaryText"):
            html.index("async function copyProjectWorkspaceControlCenterText")
        ]
        for key in [
            "controlCenterPackTitle", "controlCenterSummaryTitle",
            "controlCenterSystemCardsTitle",
            "controlCenterPriorityQueueTitle",
            "controlCenterDecisionTitle",
            "controlCenterNextBestActionsTitle",
            "controlCenterRiskOverviewTitle",
            "controlCenterPackInventoryTitle",
            "controlCenterCapabilityLockTitle",
            "controlCenterAuditTitle", "controlCenterSafetyTitle",
        ]:
            self.assertIn(key, markdown)
        section = html[
            html.index("const PROJECT_WORKSPACE_CONTROL_CENTER_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", section)
        self.assertIn("Operator cockpit preview only", html)
        self.assertIn("not real control-center execution", html)
        self.assertIn("No real task, retry, ticket, approval, operator log, or database write is created.", html)
        self.assertIn("no real history table is read", html)
        self.assertIn("no real operator task is created", html)
        for boundary in [
            "Real LLM", "provider", "video", "media", "paid", "registry",
            "rollback", "external scraping", "database persistence",
            "real restore", "real execution",
        ]:
            self.assertIn(boundary, html)
        self.assertNotIn("????", html)

    def test_workspace_agent_run_ledger_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace agent run ledger bundle",
            "PROJECT_WORKSPACE_AGENT_RUN_LEDGER_MARKER",
            "latestProjectWorkspaceAgentRunLedgerPack",
            "projectWorkspaceAgentRunLedgerPackFromWorkspace",
            "projectWorkspaceExportAgentRunLedgerSnapshot",
            "projectWorkspaceExportAgentRunLedgerMarkdown",
            "renderProjectWorkspaceAgentRunLedgerSummaryPanel",
            "renderProjectWorkspaceAgentRunLedgerCardsPanel",
            "renderProjectWorkspaceAgentRunLedgerHandoffPanel",
            "renderProjectWorkspaceAgentRunLedgerTracePanel",
            "renderProjectWorkspaceAgentRunLedgerCapabilityAuditSafetyPanel",
            "copyProjectWorkspaceAgentRunLedgerSummary",
            "copyProjectWorkspaceAgentRunLedgerCards",
            "copyProjectWorkspaceAgentRunLedgerHandoffTrace",
            "copyProjectWorkspaceAgentRunLedgerInputOutputTrace",
            "copyProjectWorkspaceAgentRunLedgerEvidenceTrace",
            "copyProjectWorkspaceAgentRunLedgerDecisionTrace",
            "copyProjectWorkspaceAgentRunLedgerCapabilityUsage",
            "copyProjectWorkspaceAgentRunLedgerAuditPreview",
            "copyProjectWorkspaceFullAgentRunLedgerPack",
            "workspace_agent_run_ledger_pack: projectWorkspaceExportAgentRunLedgerSnapshot(workspace)",
            "Workspace Agent Run Ledger / Traceability",
            "Agent Run Ledger Summary", "Agent Run Cards",
            "Handoff Trace", "Input / Output Trace Map",
            "Evidence Trace", "Decision Trace",
            "Capability Usage Preview", "Audit Preview",
            "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for field in [
            "pack.ledger_summary", "pack.agent_run_cards",
            "pack.handoff_trace", "pack.input_output_trace_map",
            "pack.evidence_trace", "pack.decision_trace",
            "pack.capability_usage_preview", "pack.ledger_quality_checks",
            "pack.audit_preview", "pack.safety_boundaries",
            "summary.mode", "summary.total_run_cards",
            "summary.total_handoffs", "summary.current_workflow_phase",
            "summary.recommended_next_action",
            "summary.real_execution_allowed", "card.run_id",
            "card.agent_role", "card.workflow_phase",
            "card.source_pack", "card.input_refs", "card.output_refs",
            "card.status", "card.summary", "card.handoff_to",
            "card.evidence_refs", "card.decision_refs",
            "card.capability_mode", "card.real_execution_allowed",
            "card.risk_note", "handoff.handoff_id",
            "handoff.from_agent", "handoff.to_agent",
            "handoff.from_pack", "handoff.to_pack",
            "handoff.handoff_reason", "handoff.input_refs",
            "handoff.output_refs", "handoff.blocked_by",
            "handoff.real_execution_allowed", "handoff.risk_note",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, html)
        previous = html.index("${renderProjectWorkspaceControlCenterLockAuditSafetyPanel(workspace)}")
        summary = html.index("${renderProjectWorkspaceAgentRunLedgerSummaryPanel(workspace)}")
        safety = html.index("${renderProjectWorkspaceAgentRunLedgerCapabilityAuditSafetyPanel(workspace)}")
        core = html.index("${renderProjectWorkspaceCreativeCoreFlowStrip(workspace)}")
        self.assertLess(previous, summary)
        self.assertLess(summary, safety)
        self.assertLess(safety, core)

    def test_workspace_agent_run_ledger_has_bilingual_guard_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "agentRunLedgerPackTitle", "agentRunLedgerSummaryTitle",
            "agentRunLedgerCardsTitle", "agentRunLedgerHandoffTitle",
            "agentRunLedgerInputOutputTitle",
            "agentRunLedgerEvidenceTitle", "agentRunLedgerDecisionTitle",
            "agentRunLedgerCapabilityTitle", "agentRunLedgerAuditTitle",
            "agentRunLedgerSafetyTitle", "agentRunLedgerCopySummary",
            "agentRunLedgerCopyCards", "agentRunLedgerCopyHandoff",
            "agentRunLedgerCopyInputOutput", "agentRunLedgerCopyEvidence",
            "agentRunLedgerCopyDecision", "agentRunLedgerCopyCapability",
            "agentRunLedgerCopyAudit", "agentRunLedgerCopyFull",
            "agentRunLedgerCopied", "agentRunLedgerCopyFailed",
            "agentRunLedgerCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace agent run ledger bundle", script)
            self.assertIn("project_workspace_agent_run_ledger_marker", script)
        markdown = html[
            html.index("function projectWorkspaceAgentRunLedgerSummaryText"):
            html.index("async function copyProjectWorkspaceAgentRunLedgerText")
        ]
        for key in [
            "agentRunLedgerPackTitle", "agentRunLedgerSummaryTitle",
            "agentRunLedgerCardsTitle", "agentRunLedgerHandoffTitle",
            "agentRunLedgerInputOutputTitle",
            "agentRunLedgerEvidenceTitle", "agentRunLedgerDecisionTitle",
            "agentRunLedgerCapabilityTitle", "agentRunLedgerAuditTitle",
            "agentRunLedgerSafetyTitle",
        ]:
            self.assertIn(key, markdown)
        section = html[
            html.index("const PROJECT_WORKSPACE_AGENT_RUN_LEDGER_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", section)
        self.assertIn("Traceability preview only", html)
        self.assertIn("not real agent runtime", html)
        self.assertIn("does not read real logs or real history tables", html)
        self.assertIn("No real agent execution, operator task, ticket, approval, operator log, or database write is created.", html)
        self.assertIn("Evidence, quote, and risk flow is derived from workspace packs only.", html)
        self.assertIn("Decision, gate, and recommended action flow is derived from upstream preview packs only.", html)
        self.assertIn("Audit preview is not written to a database, no real logs are read, and no real operator task is created.", html)
        for boundary in [
            "Real LLM", "provider", "video", "media", "paid", "registry",
            "rollback", "external scraping", "database persistence",
            "real restore", "real execution",
        ]:
            self.assertIn(boundary, html)
        self.assertNotIn("????", html)

    def test_workspace_human_review_queue_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace human review queue bundle",
            "PROJECT_WORKSPACE_HUMAN_REVIEW_QUEUE_MARKER",
            "latestProjectWorkspaceHumanReviewQueuePack",
            "projectWorkspaceHumanReviewQueuePackFromWorkspace",
            "projectWorkspaceExportHumanReviewQueueSnapshot",
            "projectWorkspaceExportHumanReviewQueueMarkdown",
            "renderProjectWorkspaceHumanReviewQueueSummaryPanel",
            "renderProjectWorkspaceHumanReviewQueueItemsPanel",
            "renderProjectWorkspaceHumanReviewQueueTaskCardsPanel",
            "renderProjectWorkspaceHumanReviewQueueInputsBlockedDependencyPanel",
            "renderProjectWorkspaceHumanReviewQueueDecisionQualityAuditSafetyPanel",
            "copyProjectWorkspaceHumanReviewQueueSummary",
            "copyProjectWorkspaceHumanReviewQueueItems",
            "copyProjectWorkspaceHumanReviewQueueTaskCards",
            "copyProjectWorkspaceHumanReviewQueueRequiredInputs",
            "copyProjectWorkspaceHumanReviewQueueBlockedItems",
            "copyProjectWorkspaceHumanReviewQueueDependencyMap",
            "copyProjectWorkspaceHumanReviewQueueDecisionOptions",
            "copyProjectWorkspaceHumanReviewQueueAuditPreview",
            "copyProjectWorkspaceFullHumanReviewQueuePack",
            "workspace_human_review_queue_pack: projectWorkspaceExportHumanReviewQueueSnapshot(workspace)",
            "Workspace Human Review Queue / Operator Task Preview",
            "Human Review Queue Summary", "Review Queue Items",
            "Operator Task Cards", "Required Inputs Overview",
            "Blocked Review Items", "Review Dependency Map",
            "Operator Decision Options", "Audit Preview",
            "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for field in [
            "pack.review_queue_summary", "pack.review_queue_items",
            "pack.operator_task_cards", "pack.review_priority_rationale",
            "pack.required_inputs_overview", "pack.blocked_review_items",
            "pack.review_dependency_map", "pack.operator_decision_options",
            "pack.review_quality_checks", "pack.audit_preview",
            "pack.safety_boundaries", "summary.mode",
            "summary.review_item_count", "summary.blocked_review_item_count",
            "summary.recommended_next_action", "summary.real_execution_allowed",
            "item.review_id", "item.priority", "item.review_type",
            "item.source_pack", "item.source_refs", "item.review_title",
            "item.why_review_is_needed", "item.required_inputs",
            "item.blocked_by", "item.operator_decision_needed",
            "item.allowed_decisions", "item.next_action_preview",
            "item.real_execution_allowed", "item.risk_note",
            "task.task_id", "task.task_type", "task.task_title",
            "task.source_review_id", "task.source_pack",
            "task.task_status", "task.assignee_role",
            "task.required_review", "task.completion_criteria",
            "task.blocked_by", "task.real_execution_allowed",
            "task.risk_note",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, html)
        previous = html.index("${renderProjectWorkspaceAgentRunLedgerCapabilityAuditSafetyPanel(workspace)}")
        summary = html.index("${renderProjectWorkspaceHumanReviewQueueSummaryPanel(workspace)}")
        safety = html.index("${renderProjectWorkspaceHumanReviewQueueDecisionQualityAuditSafetyPanel(workspace)}")
        core = html.index("${renderProjectWorkspaceCreativeCoreFlowStrip(workspace)}")
        self.assertLess(previous, summary)
        self.assertLess(summary, safety)
        self.assertLess(safety, core)

    def test_workspace_human_review_queue_has_bilingual_guard_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "humanReviewQueuePackTitle", "humanReviewQueueSummaryTitle",
            "humanReviewQueueItemsTitle", "humanReviewQueueTasksTitle",
            "humanReviewQueueRequiredInputsTitle",
            "humanReviewQueueBlockedItemsTitle",
            "humanReviewQueueDependencyTitle",
            "humanReviewQueueDecisionOptionsTitle",
            "humanReviewQueueAuditTitle", "humanReviewQueueSafetyTitle",
            "humanReviewQueueCopySummary", "humanReviewQueueCopyItems",
            "humanReviewQueueCopyTasks", "humanReviewQueueCopyInputs",
            "humanReviewQueueCopyBlocked", "humanReviewQueueCopyDependency",
            "humanReviewQueueCopyDecisions", "humanReviewQueueCopyAudit",
            "humanReviewQueueCopyFull", "humanReviewQueueCopied",
            "humanReviewQueueCopyFailed", "humanReviewQueueCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace human review queue bundle", script)
            self.assertIn("project_workspace_human_review_queue_marker", script)
        markdown = html[
            html.index("function projectWorkspaceHumanReviewQueueSummaryText"):
            html.index("async function copyProjectWorkspaceHumanReviewQueueText")
        ]
        for key in [
            "humanReviewQueuePackTitle", "humanReviewQueueSummaryTitle",
            "humanReviewQueueItemsTitle", "humanReviewQueueTasksTitle",
            "humanReviewQueueRequiredInputsTitle",
            "humanReviewQueueBlockedItemsTitle",
            "humanReviewQueueDependencyTitle",
            "humanReviewQueueDecisionOptionsTitle",
            "humanReviewQueueAuditTitle", "humanReviewQueueSafetyTitle",
        ]:
            self.assertIn(key, markdown)
        section = html[
            html.index("const PROJECT_WORKSPACE_HUMAN_REVIEW_QUEUE_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", section)
        self.assertIn("Human review queue preview only", html)
        self.assertIn("not a real approval system", html)
        self.assertIn("No real ticket, operator task, approval, or task system write is created.", html)
        self.assertIn("no real external data is collected", html)
        self.assertIn("cannot create real approvals or unlock real execution", html)
        self.assertIn("Audit preview is not written to a database, no real logs or history tables are read, and no operator task is created.", html)
        for boundary in [
            "Real LLM", "provider", "video", "media", "paid", "registry",
            "rollback", "external scraping", "database persistence",
            "real restore", "real execution",
        ]:
            self.assertIn(boundary, html)
        self.assertNotIn("????", html)

    def test_workspace_capability_permission_matrix_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace capability permission matrix bundle",
            "PROJECT_WORKSPACE_CAPABILITY_PERMISSION_MATRIX_MARKER",
            "latestProjectWorkspaceCapabilityPermissionMatrixPack",
            "projectWorkspaceCapabilityPermissionMatrixPackFromWorkspace",
            "projectWorkspaceExportCapabilityPermissionMatrixSnapshot",
            "projectWorkspaceExportCapabilityPermissionMatrixMarkdown",
            "renderProjectWorkspaceCapabilityPermissionMatrixSummaryPanel",
            "renderProjectWorkspaceCapabilityPermissionCardsPanel",
            "renderProjectWorkspaceCapabilityPolicyGateResultsPanel",
            "renderProjectWorkspaceCapabilityUnlockDeniedApprovalPanel",
            "renderProjectWorkspaceCapabilityDependencyQualityAuditSafetyPanel",
            "copyProjectWorkspaceCapabilityPermissionMatrixSummary",
            "copyProjectWorkspaceCapabilityPermissionCards",
            "copyProjectWorkspaceCapabilityPolicyGateResults",
            "copyProjectWorkspaceCapabilityUnlockRequirements",
            "copyProjectWorkspaceDeniedCapabilityReasons",
            "copyProjectWorkspaceCapabilityHumanApprovalRequirements",
            "copyProjectWorkspaceCapabilityDependencyMap",
            "copyProjectWorkspaceCapabilityPermissionAuditPreview",
            "copyProjectWorkspaceFullCapabilityPermissionMatrixPack",
            "workspace_capability_permission_matrix_pack: projectWorkspaceExportCapabilityPermissionMatrixSnapshot(workspace)",
            "Workspace Capability Permission Matrix / Policy Gate",
            "Permission Matrix Summary", "Capability Permission Cards",
            "Policy Gate Results", "Unlock Requirements",
            "Denied Capability Reasons", "Human Approval Requirements",
            "Capability Dependency Map", "Audit Preview",
            "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for capability_id in [
            "llm_generation", "video_provider", "media_upload",
            "media_download", "paid_operation", "provider_registry",
            "rollback_restore", "external_scraping",
            "database_persistence", "real_execution", "human_approval",
            "operator_task_creation", "secret_access",
        ]:
            with self.subTest(capability=capability_id):
                self.assertIn(capability_id, html)
        for field in [
            "pack.permission_matrix_summary",
            "pack.capability_permission_cards",
            "pack.policy_gate_results", "pack.unlock_requirements",
            "pack.denied_capability_reasons",
            "pack.human_approval_requirements",
            "pack.capability_dependency_map",
            "pack.permission_quality_checks", "pack.audit_preview",
            "pack.safety_boundaries", "summary.mode",
            "summary.capability_count", "summary.recommended_next_action",
            "summary.real_execution_allowed", "card.capability_id",
            "card.capability_name", "card.capability_category",
            "card.current_status", "card.permission_level",
            "card.source_pack", "card.required_inputs",
            "card.required_approvals", "card.blocked_by",
            "card.allowed_modes", "card.disallowed_modes",
            "card.real_execution_allowed", "card.risk_note",
            "gate.gate_id", "gate.gate_name", "gate.capability_id",
            "gate.gate_status", "gate.gate_reason",
            "gate.required_evidence", "gate.required_human_review",
            "gate.next_allowed_mode", "gate.real_execution_allowed",
            "gate.risk_note",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, html)
        previous = html.index("${renderProjectWorkspaceHumanReviewQueueDecisionQualityAuditSafetyPanel(workspace)}")
        summary = html.index("${renderProjectWorkspaceCapabilityPermissionMatrixSummaryPanel(workspace)}")
        safety = html.index("${renderProjectWorkspaceCapabilityDependencyQualityAuditSafetyPanel(workspace)}")
        core = html.index("${renderProjectWorkspaceCreativeCoreFlowStrip(workspace)}")
        self.assertLess(previous, summary)
        self.assertLess(summary, safety)
        self.assertLess(safety, core)

    def test_workspace_capability_permission_matrix_has_bilingual_guard_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "capabilityPermissionMatrixPackTitle",
            "capabilityPermissionMatrixSummaryTitle",
            "capabilityPermissionMatrixCardsTitle",
            "capabilityPermissionMatrixPolicyGatesTitle",
            "capabilityPermissionMatrixUnlockTitle",
            "capabilityPermissionMatrixDeniedTitle",
            "capabilityPermissionMatrixHumanApprovalTitle",
            "capabilityPermissionMatrixDependencyTitle",
            "capabilityPermissionMatrixAuditTitle",
            "capabilityPermissionMatrixSafetyTitle",
            "capabilityPermissionMatrixCopySummary",
            "capabilityPermissionMatrixCopyCards",
            "capabilityPermissionMatrixCopyGates",
            "capabilityPermissionMatrixCopyUnlock",
            "capabilityPermissionMatrixCopyDenied",
            "capabilityPermissionMatrixCopyHumanApproval",
            "capabilityPermissionMatrixCopyDependency",
            "capabilityPermissionMatrixCopyAudit",
            "capabilityPermissionMatrixCopyFull",
            "capabilityPermissionMatrixCopied",
            "capabilityPermissionMatrixCopyFailed",
            "capabilityPermissionMatrixCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace capability permission matrix bundle", script)
            self.assertIn("project_workspace_capability_permission_matrix_marker", script)
        markdown = html[
            html.index("function projectWorkspaceCapabilityPermissionMatrixSummaryText"):
            html.index("async function copyProjectWorkspaceCapabilityPermissionMatrixText")
        ]
        for key in [
            "capabilityPermissionMatrixPackTitle",
            "capabilityPermissionMatrixSummaryTitle",
            "capabilityPermissionMatrixCardsTitle",
            "capabilityPermissionMatrixPolicyGatesTitle",
            "capabilityPermissionMatrixUnlockTitle",
            "capabilityPermissionMatrixDeniedTitle",
            "capabilityPermissionMatrixHumanApprovalTitle",
            "capabilityPermissionMatrixDependencyTitle",
            "capabilityPermissionMatrixAuditTitle",
            "capabilityPermissionMatrixSafetyTitle",
        ]:
            self.assertIn(key, markdown)
        section = html[
            html.index("const PROJECT_WORKSPACE_CAPABILITY_PERMISSION_MATRIX_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", section)
        self.assertIn("Permission matrix preview only", html)
        self.assertIn("not a real permission system", html)
        self.assertIn("does not grant or unlock real capabilities", html)
        self.assertIn("Policy gates must not display ready_for_real_execution", html)
        self.assertIn("do not create real approvals", html)
        self.assertIn("Audit preview is not written to a database", html)
        self.assertIn("No secret is read and no real operator task", html)
        self.assertNotIn("ready_for_real_execution</", html)
        for boundary in [
            "Real LLM", "provider", "video", "media", "paid", "registry",
            "rollback", "external scraping", "database persistence",
            "real restore", "real execution",
        ]:
            self.assertIn(boundary, html)
        self.assertNotIn("????", html)

    def test_workspace_system_integration_health_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace system integration health bundle",
            "PROJECT_WORKSPACE_SYSTEM_INTEGRATION_HEALTH_MARKER",
            "latestProjectWorkspaceSystemIntegrationHealthPack",
            "projectWorkspaceSystemIntegrationHealthPackFromWorkspace",
            "projectWorkspaceExportSystemIntegrationHealthSnapshot",
            "projectWorkspaceExportSystemIntegrationHealthMarkdown",
            "renderProjectWorkspaceSystemIntegrationHealthSummaryPanel",
            "renderProjectWorkspacePackHealthCardsPanel",
            "renderProjectWorkspaceWorkflowGateHealthPanel",
            "renderProjectWorkspaceTraceabilityOperatorCapabilityHealthPanel",
            "renderProjectWorkspaceIntegrationRiskQualityAuditSafetyPanel",
            "copyProjectWorkspaceSystemIntegrationHealthSummary",
            "copyProjectWorkspacePackHealthCards",
            "copyProjectWorkspaceWorkflowChainHealth",
            "copyProjectWorkspaceGateHealthOverview",
            "copyProjectWorkspaceTraceabilityHealth",
            "copyProjectWorkspaceOperatorReadinessOverview",
            "copyProjectWorkspaceCapabilityLockHealth",
            "copyProjectWorkspaceIntegrationRiskRegister",
            "copyProjectWorkspaceFullSystemIntegrationHealthPack",
            "workspace_system_integration_health_pack: projectWorkspaceExportSystemIntegrationHealthSnapshot(workspace)",
            "Workspace System Integration Health / Readiness Overview",
            "Integration Health Summary", "Pack Health Cards",
            "Workflow Chain Health", "Gate Health Overview",
            "Traceability Health", "Operator Readiness Overview",
            "Capability Lock Health", "Integration Risk Register",
            "Audit Preview", "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for field in [
            "pack.integration_health_summary",
            "pack.pack_health_cards", "pack.workflow_chain_health",
            "pack.gate_health_overview", "pack.traceability_health",
            "pack.operator_readiness_overview", "pack.capability_lock_health",
            "pack.integration_risk_register", "pack.health_quality_checks",
            "pack.audit_preview", "pack.safety_boundaries",
            "summary.mode", "summary.pack_health_card_count",
            "summary.integration_risk_count", "summary.recommended_next_action",
            "summary.real_execution_allowed", "card.pack_id",
            "card.pack_name", "card.source_pack", "card.health_status",
            "card.present", "card.ready_for_review",
            "card.missing_or_weak_fields", "card.upstream_dependencies",
            "card.downstream_consumers", "card.recommended_fix_preview",
            "card.real_execution_allowed", "card.risk_note",
            "launch_lock", "cycle_gate", "policy_gate", "human_review_gate",
            "agent_run_ledger_present", "cycle_history_timeline_present",
            "human_review_queue_present", "control_center_present",
            "capabilities", "real_service_health_read_performed",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, html)
        previous = html.index("${renderProjectWorkspaceCapabilityDependencyQualityAuditSafetyPanel(workspace)}")
        summary = html.index("${renderProjectWorkspaceSystemIntegrationHealthSummaryPanel(workspace)}")
        safety = html.index("${renderProjectWorkspaceIntegrationRiskQualityAuditSafetyPanel(workspace)}")
        core = html.index("${renderProjectWorkspaceCreativeCoreFlowStrip(workspace)}")
        self.assertLess(previous, summary)
        self.assertLess(summary, safety)
        self.assertLess(safety, core)

    def test_workspace_system_integration_health_has_bilingual_guard_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "systemIntegrationHealthPackTitle",
            "systemIntegrationHealthSummaryTitle",
            "systemIntegrationHealthPackCardsTitle",
            "systemIntegrationHealthWorkflowTitle",
            "systemIntegrationHealthGateTitle",
            "systemIntegrationHealthTraceabilityTitle",
            "systemIntegrationHealthOperatorTitle",
            "systemIntegrationHealthCapabilityTitle",
            "systemIntegrationHealthRiskTitle",
            "systemIntegrationHealthAuditTitle",
            "systemIntegrationHealthSafetyTitle",
            "systemIntegrationHealthCopySummary",
            "systemIntegrationHealthCopyPackCards",
            "systemIntegrationHealthCopyWorkflow",
            "systemIntegrationHealthCopyGate",
            "systemIntegrationHealthCopyTraceability",
            "systemIntegrationHealthCopyOperator",
            "systemIntegrationHealthCopyCapability",
            "systemIntegrationHealthCopyRisk",
            "systemIntegrationHealthCopyFull",
            "systemIntegrationHealthCopied",
            "systemIntegrationHealthCopyFailed",
            "systemIntegrationHealthCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace system integration health bundle", script)
            self.assertIn("project_workspace_system_integration_health_marker", script)
        markdown = html[
            html.index("function projectWorkspaceSystemIntegrationHealthSummaryText"):
            html.index("async function copyProjectWorkspaceSystemIntegrationHealthText")
        ]
        for key in [
            "systemIntegrationHealthPackTitle",
            "systemIntegrationHealthSummaryTitle",
            "systemIntegrationHealthPackCardsTitle",
            "systemIntegrationHealthWorkflowTitle",
            "systemIntegrationHealthGateTitle",
            "systemIntegrationHealthTraceabilityTitle",
            "systemIntegrationHealthOperatorTitle",
            "systemIntegrationHealthCapabilityTitle",
            "systemIntegrationHealthRiskTitle",
            "systemIntegrationHealthAuditTitle",
            "systemIntegrationHealthSafetyTitle",
        ]:
            self.assertIn(key, markdown)
        section = html[
            html.index("const PROJECT_WORKSPACE_SYSTEM_INTEGRATION_HEALTH_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", section)
        self.assertIn("Integration health preview only", html)
        self.assertIn("not a real monitoring system", html)
        self.assertIn("does not read real service health", html)
        self.assertIn("These are preview gates, not real execution gates", html)
        self.assertIn("All 13 capabilities remain disabled", html)
        self.assertIn("Audit preview is not written to a database", html)
        self.assertIn("real service health", html)
        for boundary in [
            "Real LLM", "provider", "video", "media", "paid", "registry",
            "rollback", "external scraping", "database persistence",
            "real restore", "real execution",
        ]:
            self.assertIn(boundary, html)
        self.assertNotIn("????", html)

    def test_workspace_replay_harness_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace replay harness bundle",
            "PROJECT_WORKSPACE_REPLAY_HARNESS_MARKER",
            "latestProjectWorkspaceReplayHarnessPack",
            "projectWorkspaceReplayHarnessPackFromWorkspace",
            "projectWorkspaceExportReplayHarnessSnapshot",
            "projectWorkspaceExportReplayHarnessMarkdown",
            "renderProjectWorkspaceReplayHarnessSummaryPanel",
            "renderProjectWorkspaceReplayScenariosPanel",
            "renderProjectWorkspaceReplayInputExpectedPanel",
            "renderProjectWorkspaceRegressionMatrixConsistencyPanel",
            "renderProjectWorkspaceReplayDiffQualityAuditSafetyPanel",
            "copyProjectWorkspaceReplayHarnessSummary",
            "copyProjectWorkspaceReplayScenarios",
            "copyProjectWorkspaceReplayInputContracts",
            "copyProjectWorkspaceExpectedOutputSnapshots",
            "copyProjectWorkspaceRegressionCheckMatrix",
            "copyProjectWorkspacePackConsistencyChecks",
            "copyProjectWorkspaceReplayDiffPlan",
            "copyProjectWorkspaceOperatorReplayNotes",
            "copyProjectWorkspaceFullReplayHarnessPack",
            "workspace_replay_harness_pack: projectWorkspaceExportReplayHarnessSnapshot(workspace)",
            "Workspace Replay Harness / Regression Scenario",
            "Replay Harness Summary", "Replay Scenarios",
            "Replay Input Contracts", "Expected Output Snapshots",
            "Regression Check Matrix", "Pack Consistency Checks",
            "Replay Diff Plan", "Operator Replay Notes",
            "Audit Preview", "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for field in [
            "pack.replay_harness_summary", "pack.replay_scenarios",
            "pack.replay_input_contracts",
            "pack.expected_output_snapshots",
            "pack.regression_check_matrix",
            "pack.pack_consistency_checks", "pack.replay_diff_plan",
            "pack.operator_replay_notes", "pack.replay_quality_checks",
            "pack.audit_preview", "pack.safety_boundaries",
            "summary.mode", "summary.scenario_count",
            "summary.regression_check_count",
            "summary.recommended_next_action",
            "summary.real_execution_allowed", "scenario.scenario_id",
            "scenario.scenario_name", "scenario.scenario_type",
            "scenario.source_pack", "scenario.input_refs",
            "scenario.expected_pack_outputs", "scenario.expected_status",
            "scenario.regression_focus", "scenario.failure_signal",
            "scenario.operator_review_required",
            "scenario.real_execution_allowed", "scenario.risk_note",
            "check.check_id", "check.source_pack", "check.target_pack",
            "check.expected_condition", "check.failure_condition",
            "check.severity", "check.suggested_fix_preview",
            "check.real_execution_allowed",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, html)
        previous = html.index("${renderProjectWorkspaceIntegrationRiskQualityAuditSafetyPanel(workspace)}")
        summary = html.index("${renderProjectWorkspaceReplayHarnessSummaryPanel(workspace)}")
        safety = html.index("${renderProjectWorkspaceReplayDiffQualityAuditSafetyPanel(workspace)}")
        core = html.index("${renderProjectWorkspaceCreativeCoreFlowStrip(workspace)}")
        self.assertLess(previous, summary)
        self.assertLess(summary, safety)
        self.assertLess(safety, core)

    def test_workspace_replay_harness_has_bilingual_guard_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "replayHarnessPackTitle", "replayHarnessSummaryTitle",
            "replayHarnessScenariosTitle",
            "replayHarnessInputContractsTitle",
            "replayHarnessExpectedSnapshotsTitle",
            "replayHarnessRegressionMatrixTitle",
            "replayHarnessPackConsistencyTitle",
            "replayHarnessDiffPlanTitle",
            "replayHarnessOperatorNotesTitle",
            "replayHarnessAuditTitle", "replayHarnessSafetyTitle",
            "replayHarnessCopySummary", "replayHarnessCopyScenarios",
            "replayHarnessCopyContracts", "replayHarnessCopySnapshots",
            "replayHarnessCopyMatrix", "replayHarnessCopyConsistency",
            "replayHarnessCopyDiff", "replayHarnessCopyOperator",
            "replayHarnessCopyFull", "replayHarnessCopied",
            "replayHarnessCopyFailed", "replayHarnessCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace replay harness bundle", script)
            self.assertIn("project_workspace_replay_harness_marker", script)
        markdown = html[
            html.index("function projectWorkspaceReplayHarnessSummaryText"):
            html.index("async function copyProjectWorkspaceReplayHarnessText")
        ]
        for key in [
            "replayHarnessPackTitle",
            "replayHarnessSummaryTitle",
            "replayHarnessScenariosTitle",
            "replayHarnessInputContractsTitle",
            "replayHarnessExpectedSnapshotsTitle",
            "replayHarnessRegressionMatrixTitle",
            "replayHarnessPackConsistencyTitle",
            "replayHarnessDiffPlanTitle",
            "replayHarnessOperatorNotesTitle",
            "replayHarnessAuditTitle",
            "replayHarnessSafetyTitle",
        ]:
            self.assertIn(key, markdown)
        section = html[
            html.index("const PROJECT_WORKSPACE_REPLAY_HARNESS_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", section)
        self.assertIn("Replay harness preview only", html)
        self.assertIn("not a real replay runtime", html)
        self.assertIn("does not run real replay jobs", html)
        self.assertIn("do not write files", html)
        self.assertIn("do not write databases", html)
        self.assertIn("do not read real history tables", html)
        self.assertIn("does not execute a real diff job", html)
        self.assertIn("Audit preview is not written to a database", html)
        for boundary in [
            "Real LLM", "provider", "video", "media", "paid", "registry",
            "rollback", "external scraping", "database persistence",
            "real restore", "real execution",
        ]:
            self.assertIn(boundary, html)
        self.assertNotIn("????", html)

    def test_workspace_provider_adapter_contract_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace provider adapter contract bundle",
            "PROJECT_WORKSPACE_PROVIDER_ADAPTER_CONTRACT_MARKER",
            "latestProjectWorkspaceProviderAdapterContractPack",
            "projectWorkspaceProviderAdapterContractPackFromWorkspace",
            "projectWorkspaceExportProviderAdapterContractSnapshot",
            "projectWorkspaceExportProviderAdapterContractMarkdown",
            "renderProjectWorkspaceProviderAdapterContractSummaryPanel",
            "renderProjectWorkspaceProviderContractCardsPanel",
            "renderProjectWorkspaceProviderInputOutputContractsPanel",
            "renderProjectWorkspaceProviderInvocationBoundaryPanel",
            "renderProjectWorkspaceProviderApprovalQualityAuditSafetyPanel",
            "copyProjectWorkspaceProviderAdapterContractSummary",
            "copyProjectWorkspaceProviderContractCards",
            "copyProjectWorkspaceProviderInputContracts",
            "copyProjectWorkspaceProviderOutputContracts",
            "copyProjectWorkspaceProviderInvocationBoundaryRules",
            "copyProjectWorkspaceProviderDryRunInvocationPreviews",
            "copyProjectWorkspaceProviderFailureBoundaryMatrix",
            "copyProjectWorkspaceProviderApprovalSecretRequirements",
            "copyProjectWorkspaceFullProviderAdapterContractPack",
            "workspace_provider_adapter_contract_pack: projectWorkspaceExportProviderAdapterContractSnapshot(workspace)",
            "Workspace Provider Adapter Contract / Invocation Boundary",
            "Adapter Contract Summary", "Provider Contract Cards",
            "Input Contracts", "Output Contracts",
            "Invocation Boundary Rules", "Dry-Run Invocation Previews",
            "Failure Boundary Matrix", "Approval and Secret Requirements",
            "Audit Preview", "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for provider_type in [
            "llm_text_generation", "video_generation_provider",
            "image_generation_provider", "media_storage_provider",
            "external_scraping_provider", "translation_provider",
            "analytics_or_tracking_provider", "database_persistence_provider",
            "approval_or_ticket_provider", "rollback_restore_provider",
        ]:
            with self.subTest(provider_type=provider_type):
                self.assertIn(provider_type, html)
        for field in [
            "pack.adapter_contract_summary", "pack.provider_contract_cards",
            "pack.input_contracts", "pack.output_contracts",
            "pack.invocation_boundary_rules",
            "pack.dry_run_invocation_previews",
            "pack.failure_boundary_matrix",
            "pack.approval_and_secret_requirements",
            "pack.contract_quality_checks", "pack.audit_preview",
            "pack.safety_boundaries", "summary.mode",
            "summary.provider_contract_count", "summary.boundary_rule_count",
            "summary.recommended_next_action",
            "summary.real_invocation_allowed",
            "summary.real_execution_allowed", "card.provider_id",
            "card.provider_type", "card.provider_name",
            "card.source_capability", "card.current_status",
            "card.allowed_modes", "card.disallowed_modes",
            "card.required_inputs", "card.required_outputs",
            "card.required_approvals", "card.secret_required",
            "card.secret_available", "card.real_invocation_allowed",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, html)
        previous = html.index("${renderProjectWorkspaceReplayDiffQualityAuditSafetyPanel(workspace)}")
        summary = html.index("${renderProjectWorkspaceProviderAdapterContractSummaryPanel(workspace)}")
        safety = html.index("${renderProjectWorkspaceProviderApprovalQualityAuditSafetyPanel(workspace)}")
        core = html.index("${renderProjectWorkspaceCreativeCoreFlowStrip(workspace)}")
        self.assertLess(previous, summary)
        self.assertLess(summary, safety)
        self.assertLess(safety, core)

    def test_workspace_provider_adapter_contract_has_bilingual_guard_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "providerAdapterContractPackTitle",
            "providerAdapterContractSummaryTitle",
            "providerAdapterContractCardsTitle",
            "providerAdapterContractInputTitle",
            "providerAdapterContractOutputTitle",
            "providerAdapterContractBoundaryRulesTitle",
            "providerAdapterContractDryRunTitle",
            "providerAdapterContractFailureTitle",
            "providerAdapterContractApprovalSecretTitle",
            "providerAdapterContractAuditTitle",
            "providerAdapterContractSafetyTitle",
            "providerAdapterContractCopySummary",
            "providerAdapterContractCopyCards",
            "providerAdapterContractCopyInput",
            "providerAdapterContractCopyOutput",
            "providerAdapterContractCopyRules",
            "providerAdapterContractCopyDryRun",
            "providerAdapterContractCopyFailure",
            "providerAdapterContractCopyApproval",
            "providerAdapterContractCopyFull",
            "providerAdapterContractCopied",
            "providerAdapterContractCopyFailed",
            "providerAdapterContractCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace provider adapter contract bundle", script)
            self.assertIn("project_workspace_provider_adapter_contract_marker", script)
        markdown = html[
            html.index("function projectWorkspaceProviderAdapterContractSummaryText"):
            html.index("async function copyProjectWorkspaceProviderAdapterContractText")
        ]
        for key in [
            "providerAdapterContractPackTitle",
            "providerAdapterContractSummaryTitle",
            "providerAdapterContractCardsTitle",
            "providerAdapterContractInputTitle",
            "providerAdapterContractOutputTitle",
            "providerAdapterContractBoundaryRulesTitle",
            "providerAdapterContractDryRunTitle",
            "providerAdapterContractFailureTitle",
            "providerAdapterContractApprovalSecretTitle",
            "providerAdapterContractAuditTitle",
            "providerAdapterContractSafetyTitle",
        ]:
            self.assertIn(key, markdown)
        section = html[
            html.index("const PROJECT_WORKSPACE_PROVIDER_ADAPTER_CONTRACT_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", section)
        for safety_text in [
            "Provider adapter contract preview only",
            "not a real provider adapter",
            "does not invoke real providers",
            "do not send requests",
            "write files, read secrets, upload media, or download media",
            "do not call providers",
            "mock shapes only",
            "No secret is read",
            "no real approval is created",
            "audit preview is not written to a database",
        ]:
            with self.subTest(safety_text=safety_text):
                self.assertIn(safety_text, html)
        for boundary in [
            "Real LLM", "provider", "image", "video", "media", "paid",
            "registry", "rollback", "external scraping",
            "database persistence", "real restore", "real execution",
        ]:
            self.assertIn(boundary, html)
        self.assertNotIn("????", html)

    def test_workspace_provider_contract_test_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace provider contract test bundle",
            "PROJECT_WORKSPACE_PROVIDER_CONTRACT_TEST_MARKER",
            "latestProjectWorkspaceProviderContractTestPack",
            "projectWorkspaceProviderContractTestPackFromWorkspace",
            "projectWorkspaceExportProviderContractTestSnapshot",
            "projectWorkspaceExportProviderContractTestMarkdown",
            "renderProjectWorkspaceProviderContractTestSummaryPanel",
            "renderProjectWorkspaceMockInvocationTestCasesPanel",
            "renderProjectWorkspaceProviderValidationResultsPanel",
            "renderProjectWorkspaceProviderBoundaryFailurePanel",
            "renderProjectWorkspaceProviderApprovalCoverageQualitySafetyPanel",
            "copyProjectWorkspaceProviderContractTestSummary",
            "copyProjectWorkspaceMockInvocationTestCases",
            "copyProjectWorkspaceInputValidationResults",
            "copyProjectWorkspaceOutputValidationResults",
            "copyProjectWorkspaceBoundaryRuleTestResults",
            "copyProjectWorkspaceFailureSimulationPreviews",
            "copyProjectWorkspaceApprovalSecretTestMatrix",
            "copyProjectWorkspaceProviderTestCoverage",
            "copyProjectWorkspaceFullProviderContractTestPack",
            "workspace_provider_contract_test_pack: projectWorkspaceExportProviderContractTestSnapshot(workspace)",
            "Workspace Provider Contract Test / Mock Invocation Harness",
            "Contract Test Summary", "Mock Invocation Test Cases",
            "Input Validation Results", "Output Validation Results",
            "Boundary Rule Test Results", "Failure Simulation Previews",
            "Approval Secret Test Matrix", "Provider Test Coverage",
            "Audit Preview", "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for provider_type in [
            "llm_text_generation", "video_generation_provider",
            "image_generation_provider", "media_storage_provider",
            "external_scraping_provider", "translation_provider",
            "analytics_or_tracking_provider", "database_persistence_provider",
            "approval_or_ticket_provider", "rollback_restore_provider",
        ]:
            with self.subTest(provider_type=provider_type):
                self.assertIn(provider_type, html)
        for field in [
            "pack.contract_test_summary",
            "pack.mock_invocation_test_cases",
            "pack.input_validation_results",
            "pack.output_validation_results",
            "pack.boundary_rule_test_results",
            "pack.failure_simulation_previews",
            "pack.approval_secret_test_matrix",
            "pack.provider_test_coverage",
            "pack.contract_test_quality_checks",
            "pack.audit_preview", "pack.safety_boundaries",
            "summary.mode", "summary.covered_provider_type_count",
            "summary.provider_test_case_count",
            "summary.boundary_rule_test_count",
            "summary.recommended_next_action",
            "summary.real_invocation_allowed",
            "summary.real_execution_allowed", "testCase.test_id",
            "testCase.provider_id", "testCase.provider_type",
            "testCase.source_contract_id", "testCase.test_name",
            "testCase.mock_input_refs", "testCase.expected_mock_outputs",
            "testCase.boundary_rules_checked", "testCase.expected_status",
            "testCase.failure_signal", "testCase.real_invocation_allowed",
            "testCase.real_execution_allowed", "testCase.risk_note",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, html)
        previous = html.index("${renderProjectWorkspaceProviderApprovalQualityAuditSafetyPanel(workspace)}")
        summary = html.index("${renderProjectWorkspaceProviderContractTestSummaryPanel(workspace)}")
        safety = html.index("${renderProjectWorkspaceProviderApprovalCoverageQualitySafetyPanel(workspace)}")
        core = html.index("${renderProjectWorkspaceCreativeCoreFlowStrip(workspace)}")
        self.assertLess(previous, summary)
        self.assertLess(summary, safety)
        self.assertLess(safety, core)

    def test_workspace_provider_contract_test_has_bilingual_guard_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "providerContractTestPackTitle",
            "providerContractTestSummaryTitle",
            "providerContractTestCasesTitle",
            "providerContractTestInputTitle",
            "providerContractTestOutputTitle",
            "providerContractTestBoundaryTitle",
            "providerContractTestFailureTitle",
            "providerContractTestApprovalSecretTitle",
            "providerContractTestCoverageTitle",
            "providerContractTestAuditTitle",
            "providerContractTestSafetyTitle",
            "providerContractTestCopySummary",
            "providerContractTestCopyCases",
            "providerContractTestCopyInput",
            "providerContractTestCopyOutput",
            "providerContractTestCopyBoundary",
            "providerContractTestCopyFailure",
            "providerContractTestCopyApproval",
            "providerContractTestCopyCoverage",
            "providerContractTestCopyFull",
            "providerContractTestCopied",
            "providerContractTestCopyFailed",
            "providerContractTestCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace provider contract test bundle", script)
            self.assertIn("project_workspace_provider_contract_test_marker", script)
        markdown = html[
            html.index("function projectWorkspaceProviderContractTestSummaryText"):
            html.index("async function copyProjectWorkspaceProviderContractTestText")
        ]
        for key in [
            "providerContractTestPackTitle",
            "providerContractTestSummaryTitle",
            "providerContractTestCasesTitle",
            "providerContractTestInputTitle",
            "providerContractTestOutputTitle",
            "providerContractTestBoundaryTitle",
            "providerContractTestFailureTitle",
            "providerContractTestApprovalSecretTitle",
            "providerContractTestCoverageTitle",
            "providerContractTestAuditTitle",
            "providerContractTestSafetyTitle",
        ]:
            self.assertIn(key, markdown)
        section = html[
            html.index("const PROJECT_WORKSPACE_PROVIDER_CONTRACT_TEST_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", section)
        for safety_text in [
            "Mock invocation harness preview only",
            "not a real provider test",
            "does not invoke real providers",
            "without reading files, writing files, uploading media, or calling providers",
            "do not read files, write files, upload media, download media, or invoke providers",
            "Failure simulation is preview only",
            "does not trigger real failure injection",
            "No secret is read",
            "no real approval is created",
            "audit preview is not written to a database",
        ]:
            with self.subTest(safety_text=safety_text):
                self.assertIn(safety_text, html)
        for boundary in [
            "Real LLM", "provider", "image", "video", "media", "paid",
            "registry", "rollback", "external scraping",
            "database persistence", "real restore", "real execution",
        ]:
            self.assertIn(boundary, html)
        self.assertNotIn("????", html)

    def test_workspace_provider_mock_invocation_result_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace provider mock invocation result bundle",
            "PROJECT_WORKSPACE_PROVIDER_MOCK_INVOCATION_RESULT_MARKER",
            "latestProjectWorkspaceProviderMockInvocationResultPack",
            "projectWorkspaceProviderMockInvocationResultPackFromWorkspace",
            "projectWorkspaceExportProviderMockInvocationResultSnapshot",
            "projectWorkspaceExportProviderMockInvocationResultMarkdown",
            "renderProjectWorkspaceProviderMockInvocationResultSummaryPanel",
            "renderProjectWorkspaceSandboxRunLedgerPanel",
            "renderProjectWorkspaceMockRunResultCardsPanel",
            "renderProjectWorkspaceMockSnapshotsBoundaryPanel",
            "renderProjectWorkspaceMockFailureOperatorQualitySafetyPanel",
            "copyProjectWorkspaceProviderMockInvocationResultSummary",
            "copyProjectWorkspaceSandboxRunLedger",
            "copyProjectWorkspaceMockRunResultCards",
            "copyProjectWorkspaceMockInputOutputSnapshots",
            "copyProjectWorkspaceBoundaryEnforcementResults",
            "copyProjectWorkspaceMockFailureObservations",
            "copyProjectWorkspaceOperatorReviewNotes",
            "copyProjectWorkspaceProviderMockInvocationAuditPreview",
            "copyProjectWorkspaceFullProviderMockInvocationResultPack",
            "workspace_provider_mock_invocation_result_pack: projectWorkspaceExportProviderMockInvocationResultSnapshot(workspace)",
            "Workspace Provider Mock Invocation Result / Sandbox Run Ledger",
            "Mock Invocation Result Summary", "Sandbox Run Ledger",
            "Mock Run Result Cards", "Mock Input Output Snapshots",
            "Boundary Enforcement Results", "Mock Failure Observations",
            "Operator Review Notes", "Audit Preview", "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for provider_type in [
            "llm_text_generation", "video_generation_provider",
            "image_generation_provider", "media_storage_provider",
            "external_scraping_provider", "translation_provider",
            "analytics_or_tracking_provider", "database_persistence_provider",
            "approval_or_ticket_provider", "rollback_restore_provider",
        ]:
            with self.subTest(provider_type=provider_type):
                self.assertIn(provider_type, html)
        for field in [
            "pack.mock_invocation_result_summary",
            "pack.sandbox_run_ledger", "pack.mock_run_result_cards",
            "pack.mock_input_output_snapshots",
            "pack.boundary_enforcement_results",
            "pack.mock_failure_observations",
            "pack.operator_review_notes",
            "pack.sandbox_result_quality_checks",
            "pack.audit_preview", "pack.safety_boundaries",
            "summary.mode", "summary.sandbox_run_count",
            "summary.mock_result_card_count",
            "summary.recommended_next_action",
            "summary.real_invocation_allowed",
            "summary.real_execution_allowed", "run.run_id",
            "run.provider_id", "run.provider_type",
            "run.source_test_id", "run.run_mode",
            "run.mock_started_at", "run.mock_completed_at",
            "run.mock_status", "run.boundary_status",
            "run.real_invocation_allowed", "run.real_execution_allowed",
            "card.result_id", "card.run_id", "card.provider_id",
            "card.provider_type", "card.source_test_id",
            "card.input_contract_status", "card.output_contract_status",
            "card.boundary_rule_status", "card.failure_simulation_status",
            "card.approval_secret_status",
            "card.expected_mock_output_summary",
            "card.blocked_real_behavior_summary",
            "card.recommended_operator_action",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, html)
        previous = html.index("${renderProjectWorkspaceProviderApprovalCoverageQualitySafetyPanel(workspace)}")
        summary = html.index("${renderProjectWorkspaceProviderMockInvocationResultSummaryPanel(workspace)}")
        safety = html.index("${renderProjectWorkspaceMockFailureOperatorQualitySafetyPanel(workspace)}")
        core = html.index("${renderProjectWorkspaceCreativeCoreFlowStrip(workspace)}")
        self.assertLess(previous, summary)
        self.assertLess(summary, safety)
        self.assertLess(safety, core)

    def test_workspace_provider_mock_invocation_result_has_bilingual_guard_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "providerMockResultPackTitle",
            "providerMockResultSummaryTitle",
            "providerMockResultLedgerTitle",
            "providerMockResultCardsTitle",
            "providerMockResultSnapshotsTitle",
            "providerMockResultBoundaryTitle",
            "providerMockResultFailureTitle",
            "providerMockResultOperatorNotesTitle",
            "providerMockResultAuditTitle",
            "providerMockResultSafetyTitle",
            "providerMockResultCopySummary",
            "providerMockResultCopyLedger",
            "providerMockResultCopyCards",
            "providerMockResultCopySnapshots",
            "providerMockResultCopyBoundary",
            "providerMockResultCopyFailure",
            "providerMockResultCopyOperator",
            "providerMockResultCopyAudit",
            "providerMockResultCopyFull",
            "providerMockResultCopied",
            "providerMockResultCopyFailed",
            "providerMockResultCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace provider mock invocation result bundle", script)
            self.assertIn("project_workspace_provider_mock_invocation_result_marker", script)
        markdown = html[
            html.index("function projectWorkspaceProviderMockInvocationResultSummaryText"):
            html.index("async function copyProjectWorkspaceProviderMockInvocationResultText")
        ]
        for key in [
            "providerMockResultPackTitle",
            "providerMockResultSummaryTitle",
            "providerMockResultLedgerTitle",
            "providerMockResultCardsTitle",
            "providerMockResultSnapshotsTitle",
            "providerMockResultBoundaryTitle",
            "providerMockResultFailureTitle",
            "providerMockResultOperatorNotesTitle",
            "providerMockResultAuditTitle",
            "providerMockResultSafetyTitle",
        ]:
            self.assertIn(key, markdown)
        section = html[
            html.index("const PROJECT_WORKSPACE_PROVIDER_MOCK_INVOCATION_RESULT_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", section)
        for safety_text in [
            "Sandbox result preview only",
            "not a real provider invocation",
            "does not invoke real providers",
            "do not write files or databases",
            "real behavior is blocked",
            "Failure observations are preview only",
            "do not trigger real failures",
            "Operator notes do not create real tasks",
            "Audit preview is not written to a database",
        ]:
            with self.subTest(safety_text=safety_text):
                self.assertIn(safety_text, html)
        for boundary in [
            "Real LLM", "provider", "image", "video", "media", "paid",
            "registry", "rollback", "external scraping",
            "database persistence", "real restore", "real execution",
        ]:
            self.assertIn(boundary, html)
        self.assertNotIn("????", html)

    def test_workspace_provider_failure_taxonomy_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace provider failure taxonomy bundle",
            "PROJECT_WORKSPACE_PROVIDER_FAILURE_TAXONOMY_MARKER",
            "latestProjectWorkspaceProviderFailureTaxonomyPack",
            "projectWorkspaceProviderFailureTaxonomyPackFromWorkspace",
            "projectWorkspaceExportProviderFailureTaxonomySnapshot",
            "projectWorkspaceExportProviderFailureTaxonomyMarkdown",
            "renderProjectWorkspaceProviderFailureTaxonomySummaryPanel",
            "renderProjectWorkspaceFailureTaxonomyCardsPanel",
            "renderProjectWorkspaceRecoveryPolicyCardsPanel",
            "renderProjectWorkspaceRetryManualNonRecoverablePanel",
            "renderProjectWorkspaceFailureActionQualityAuditSafetyPanel",
            "copyProjectWorkspaceProviderFailureTaxonomySummary",
            "copyProjectWorkspaceFailureTaxonomyCards",
            "copyProjectWorkspaceRecoveryPolicyCards",
            "copyProjectWorkspaceRetryBoundaryRules",
            "copyProjectWorkspaceManualInterventionRequirements",
            "copyProjectWorkspaceNonRecoverableConditions",
            "copyProjectWorkspaceFailureToActionMap",
            "copyProjectWorkspaceProviderFailureTaxonomyAuditPreview",
            "copyProjectWorkspaceFullProviderFailureTaxonomyPack",
            "workspace_provider_failure_taxonomy_pack: projectWorkspaceExportProviderFailureTaxonomySnapshot(workspace)",
            "Workspace Provider Failure Taxonomy / Recovery Policy",
            "Failure Taxonomy Summary", "Failure Taxonomy Cards",
            "Recovery Policy Cards", "Retry Boundary Rules",
            "Manual Intervention Requirements", "Non-Recoverable Conditions",
            "Failure to Action Map", "Audit Preview", "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for provider_type in [
            "llm_text_generation", "video_generation_provider",
            "image_generation_provider", "media_storage_provider",
            "external_scraping_provider", "translation_provider",
            "analytics_or_tracking_provider", "database_persistence_provider",
            "approval_or_ticket_provider", "rollback_restore_provider",
        ]:
            with self.subTest(provider_type=provider_type):
                self.assertIn(provider_type, html)
        for field in [
            "pack.failure_taxonomy_summary",
            "pack.failure_taxonomy_cards",
            "pack.recovery_policy_cards",
            "pack.retry_boundary_rules",
            "pack.manual_intervention_requirements",
            "pack.non_recoverable_conditions",
            "pack.failure_to_action_map",
            "pack.recovery_quality_checks",
            "pack.audit_preview",
            "pack.safety_boundaries",
            "summary.mode",
            "summary.failure_taxonomy_card_count",
            "summary.recovery_policy_card_count",
            "summary.recommended_next_action",
            "summary.real_invocation_allowed",
            "summary.real_execution_allowed",
            "card.failure_type_id", "card.failure_type",
            "card.provider_id", "card.provider_type",
            "card.source_run_id", "card.source_result_id",
            "card.failure_category", "card.failure_signal",
            "card.severity", "card.detected_from",
            "card.blocked_real_behavior_summary",
            "card.operator_visible_message",
            "card.real_invocation_allowed",
            "card.real_execution_allowed",
            "card.risk_note",
            "policy.policy_id", "policy.failure_type_id",
            "policy.provider_id", "policy.provider_type",
            "policy.recovery_strategy",
            "policy.allowed_recovery_modes",
            "policy.disallowed_recovery_modes",
            "policy.requires_human_review",
            "policy.requires_secret_check",
            "policy.requires_cost_review",
            "policy.requires_rollback_review",
            "policy.retry_allowed",
            "policy.real_retry_allowed",
            "policy.real_rollback_allowed",
            "policy.recommended_operator_action",
            "policy.real_execution_allowed",
            "policy.risk_note",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, html)
        previous = html.index("${renderProjectWorkspaceMockFailureOperatorQualitySafetyPanel(workspace)}")
        summary = html.index("${renderProjectWorkspaceProviderFailureTaxonomySummaryPanel(workspace)}")
        safety = html.index("${renderProjectWorkspaceFailureActionQualityAuditSafetyPanel(workspace)}")
        core = html.index("${renderProjectWorkspaceCreativeCoreFlowStrip(workspace)}")
        self.assertLess(previous, summary)
        self.assertLess(summary, safety)
        self.assertLess(safety, core)

    def test_workspace_provider_failure_taxonomy_has_bilingual_guard_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "providerFailureTaxonomyPackTitle",
            "providerFailureTaxonomySummaryTitle",
            "providerFailureTaxonomyCardsTitle",
            "providerFailureTaxonomyPoliciesTitle",
            "providerFailureTaxonomyRetryTitle",
            "providerFailureTaxonomyManualTitle",
            "providerFailureTaxonomyNonRecoverableTitle",
            "providerFailureTaxonomyActionMapTitle",
            "providerFailureTaxonomyQualityTitle",
            "providerFailureTaxonomyAuditTitle",
            "providerFailureTaxonomySafetyTitle",
            "providerFailureTaxonomyCopySummary",
            "providerFailureTaxonomyCopyCards",
            "providerFailureTaxonomyCopyPolicies",
            "providerFailureTaxonomyCopyRetry",
            "providerFailureTaxonomyCopyManual",
            "providerFailureTaxonomyCopyNonRecoverable",
            "providerFailureTaxonomyCopyActionMap",
            "providerFailureTaxonomyCopyAudit",
            "providerFailureTaxonomyCopyFull",
            "providerFailureTaxonomyCopied",
            "providerFailureTaxonomyCopyFailed",
            "providerFailureTaxonomyCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace provider failure taxonomy bundle", script)
            self.assertIn("project_workspace_provider_failure_taxonomy_marker", script)
        markdown = html[
            html.index("function projectWorkspaceProviderFailureTaxonomySummaryText"):
            html.index("async function copyProjectWorkspaceProviderFailureTaxonomyText")
        ]
        for key in [
            "providerFailureTaxonomyPackTitle",
            "providerFailureTaxonomySummaryTitle",
            "providerFailureTaxonomyCardsTitle",
            "providerFailureTaxonomyPoliciesTitle",
            "providerFailureTaxonomyRetryTitle",
            "providerFailureTaxonomyManualTitle",
            "providerFailureTaxonomyNonRecoverableTitle",
            "providerFailureTaxonomyActionMapTitle",
            "providerFailureTaxonomyAuditTitle",
            "providerFailureTaxonomySafetyTitle",
        ]:
            self.assertIn(key, markdown)
        section = html[
            html.index("const PROJECT_WORKSPACE_PROVIDER_FAILURE_TAXONOMY_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", section)
        for safety_text in [
            "Failure taxonomy preview only",
            "not a real failure handling system",
            "does not execute real recovery",
            "creates no real task",
            "executes no real retry or rollback",
            "does not execute real actions",
            "write databases",
            "Real LLM",
            "provider",
            "image",
            "video",
            "media",
            "paid",
            "registry",
            "rollback",
            "external scraping",
            "database persistence",
            "real restore",
            "real execution",
        ]:
            with self.subTest(safety_text=safety_text):
                self.assertIn(safety_text, html)
        self.assertNotIn("????", html)

    def test_workspace_provider_cost_quota_risk_guard_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace provider cost quota risk guard bundle",
            "PROJECT_WORKSPACE_PROVIDER_COST_QUOTA_RISK_GUARD_MARKER",
            "latestProjectWorkspaceProviderCostQuotaRiskGuardPack",
            "projectWorkspaceProviderCostQuotaRiskGuardPackFromWorkspace",
            "projectWorkspaceExportProviderCostQuotaRiskGuardSnapshot",
            "projectWorkspaceExportProviderCostQuotaRiskGuardMarkdown",
            "renderProjectWorkspaceProviderCostQuotaRiskSummaryPanel",
            "renderProjectWorkspaceProviderCostRiskCardsPanel",
            "renderProjectWorkspaceQuotaBudgetPolicyPanel",
            "renderProjectWorkspaceUsagePaidFailurePolicyPanel",
            "renderProjectWorkspaceApprovalRiskQualityAuditSafetyPanel",
            "copyProjectWorkspaceProviderCostQuotaRiskSummary",
            "copyProjectWorkspaceProviderCostRiskCards",
            "copyProjectWorkspaceQuotaGuardCards",
            "copyProjectWorkspaceBudgetPolicyCards",
            "copyProjectWorkspaceUsageLimitBoundaries",
            "copyProjectWorkspacePaidOperationBlockers",
            "copyProjectWorkspaceCostFailurePolicyMap",
            "copyProjectWorkspaceApprovalCostReviewRequirements",
            "copyProjectWorkspaceFullProviderCostQuotaRiskGuardPack",
            "workspace_provider_cost_quota_risk_guard_pack: projectWorkspaceExportProviderCostQuotaRiskGuardSnapshot(workspace)",
            "Workspace Provider Cost / Quota / Risk Guard",
            "Cost Quota Risk Summary",
            "Provider Cost Risk Cards",
            "Quota Guard Cards",
            "Budget Policy Cards",
            "Usage Limit Boundaries",
            "Paid Operation Blockers",
            "Cost Failure Policy Map",
            "Approval Cost Review Requirements",
            "Risk Score Matrix",
            "Audit Preview",
            "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for provider_type in [
            "llm_text_generation", "video_generation_provider",
            "image_generation_provider", "media_storage_provider",
            "external_scraping_provider", "translation_provider",
            "analytics_or_tracking_provider", "database_persistence_provider",
            "approval_or_ticket_provider", "rollback_restore_provider",
        ]:
            with self.subTest(provider_type=provider_type):
                self.assertIn(provider_type, html)
        for field in [
            "pack.cost_quota_risk_summary",
            "pack.provider_cost_risk_cards",
            "pack.quota_guard_cards",
            "pack.budget_policy_cards",
            "pack.usage_limit_boundaries",
            "pack.paid_operation_blockers",
            "pack.cost_failure_policy_map",
            "pack.approval_cost_review_requirements",
            "pack.risk_score_matrix",
            "pack.cost_guard_quality_checks",
            "pack.audit_preview",
            "pack.safety_boundaries",
            "summary.mode",
            "summary.provider_cost_risk_card_count",
            "summary.quota_guard_card_count",
            "summary.paid_operation_allowed",
            "summary.real_quota_check_allowed",
            "summary.real_invocation_allowed",
            "summary.real_execution_allowed",
            "card.cost_risk_id",
            "card.provider_id",
            "card.provider_type",
            "card.source_capability",
            "card.estimated_cost_level",
            "card.quota_risk_level",
            "card.paid_operation_required",
            "card.paid_operation_allowed",
            "card.quota_check_mode",
            "card.usage_tracking_mode",
            "card.cost_review_required",
            "card.approval_required",
            "card.blocked_by",
            "card.recommended_operator_action",
            "card.real_invocation_allowed",
            "card.real_execution_allowed",
            "card.risk_note",
            "card.quota_guard_id",
            "card.guard_type",
            "card.guard_status",
            "card.allowed_preview_usage",
            "card.blocked_real_usage",
            "card.quota_source",
            "card.quota_available",
            "card.quota_enforcement_mode",
            "card.requires_human_review",
            "card.real_quota_check_allowed",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, html)
        previous = html.index("${renderProjectWorkspaceAssetFailureQualityAuditSafetyPanel(workspace)}")
        summary = html.index("${renderProjectWorkspaceProviderCostQuotaRiskSummaryPanel(workspace)}")
        safety = html.index("${renderProjectWorkspaceApprovalRiskQualityAuditSafetyPanel(workspace)}")
        core = html.index("${renderProjectWorkspaceCreativeCoreFlowStrip(workspace)}")
        self.assertLess(previous, summary)
        self.assertLess(summary, safety)
        self.assertLess(safety, core)

    def test_workspace_provider_cost_quota_risk_guard_has_bilingual_guard_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "providerCostQuotaRiskPackTitle",
            "providerCostQuotaRiskSummaryTitle",
            "providerCostQuotaRiskCardsTitle",
            "providerCostQuotaRiskQuotaTitle",
            "providerCostQuotaRiskBudgetTitle",
            "providerCostQuotaRiskUsageTitle",
            "providerCostQuotaRiskPaidBlockersTitle",
            "providerCostQuotaRiskFailurePolicyTitle",
            "providerCostQuotaRiskApprovalTitle",
            "providerCostQuotaRiskScoreTitle",
            "providerCostQuotaRiskAuditTitle",
            "providerCostQuotaRiskSafetyTitle",
            "providerCostQuotaRiskCopySummary",
            "providerCostQuotaRiskCopyCards",
            "providerCostQuotaRiskCopyQuota",
            "providerCostQuotaRiskCopyBudget",
            "providerCostQuotaRiskCopyUsage",
            "providerCostQuotaRiskCopyPaidBlockers",
            "providerCostQuotaRiskCopyFailurePolicy",
            "providerCostQuotaRiskCopyApproval",
            "providerCostQuotaRiskCopyFull",
            "providerCostQuotaRiskCopied",
            "providerCostQuotaRiskCopyFailed",
            "providerCostQuotaRiskCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace provider cost quota risk guard bundle", script)
            self.assertIn("project_workspace_provider_cost_quota_risk_guard_marker", script)
        markdown = html[
            html.index("function projectWorkspaceProviderCostQuotaRiskGuardSummaryText"):
            html.index("async function copyProjectWorkspaceProviderCostQuotaRiskGuardText")
        ]
        for key in [
            "providerCostQuotaRiskPackTitle",
            "providerCostQuotaRiskSummaryTitle",
            "providerCostQuotaRiskCardsTitle",
            "providerCostQuotaRiskQuotaTitle",
            "providerCostQuotaRiskBudgetTitle",
            "providerCostQuotaRiskUsageTitle",
            "providerCostQuotaRiskPaidBlockersTitle",
            "providerCostQuotaRiskFailurePolicyTitle",
            "providerCostQuotaRiskApprovalTitle",
            "providerCostQuotaRiskScoreTitle",
            "providerCostQuotaRiskAuditTitle",
            "providerCostQuotaRiskSafetyTitle",
        ]:
            self.assertIn(key, markdown)
        section = html[
            html.index("const PROJECT_WORKSPACE_PROVIDER_COST_QUOTA_RISK_GUARD_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", section)
        for safety_text in [
            "cost / quota / risk preview",
            "not a real billing system",
            "does not read real billing",
            "real quota",
            "provider usage",
            "does not call a real usage API",
            "does not write a usage log",
            "paid operation blocked",
            "failure taxonomy",
            "does not execute real retry or rollback",
            "creates no real approval",
            "deterministic preview",
            "does not read real service data",
            "Audit preview is not written to a database",
            "Real LLM",
            "provider",
            "image",
            "video",
            "media",
            "paid",
            "registry",
            "rollback",
            "external scraping",
            "database persistence",
            "real restore",
            "real execution",
        ]:
            with self.subTest(safety_text=safety_text):
                self.assertIn(safety_text, html)
        self.assertNotIn("????", html)

    def test_workspace_real_provider_readiness_checklist_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace real provider readiness checklist bundle",
            "PROJECT_WORKSPACE_REAL_PROVIDER_READINESS_CHECKLIST_MARKER",
            "latestProjectWorkspaceRealProviderReadinessChecklistPack",
            "projectWorkspaceRealProviderReadinessChecklistPackFromWorkspace",
            "projectWorkspaceExportRealProviderReadinessChecklistSnapshot",
            "projectWorkspaceExportRealProviderReadinessChecklistMarkdown",
            "renderProjectWorkspaceRealProviderReadinessSummaryPanel",
            "renderProjectWorkspaceProviderReadinessCardsPanel",
            "renderProjectWorkspaceReadinessGatePrerequisitePanel",
            "renderProjectWorkspaceMissingApprovalSecretCostMediaPanel",
            "renderProjectWorkspaceReadinessRiskQualityAuditSafetyPanel",
            "copyProjectWorkspaceRealProviderReadinessSummary",
            "copyProjectWorkspaceProviderReadinessCards",
            "copyProjectWorkspaceReadinessGateChecks",
            "copyProjectWorkspacePrerequisiteChecklist",
            "copyProjectWorkspaceMissingReadinessRequirements",
            "copyProjectWorkspaceApprovalReadinessRequirements",
            "copyProjectWorkspaceSecretEnvironmentReadiness",
            "copyProjectWorkspaceReadinessRiskRegister",
            "copyProjectWorkspaceFullRealProviderReadinessChecklistPack",
            "workspace_real_provider_readiness_checklist_pack: projectWorkspaceExportRealProviderReadinessChecklistSnapshot(workspace)",
            "Workspace Real Provider Readiness Checklist",
            "Real Provider Readiness Summary",
            "Provider Readiness Cards",
            "Readiness Gate Checks",
            "Prerequisite Checklist",
            "Missing Readiness Requirements",
            "Approval Readiness Requirements",
            "Secret Environment Readiness",
            "Cost Quota Readiness",
            "Media Asset Readiness",
            "Readiness Risk Register",
            "Audit Preview",
            "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for provider_type in [
            "llm_text_generation", "video_generation_provider",
            "image_generation_provider", "media_storage_provider",
            "external_scraping_provider", "translation_provider",
            "analytics_or_tracking_provider", "database_persistence_provider",
            "approval_or_ticket_provider", "rollback_restore_provider",
        ]:
            with self.subTest(provider_type=provider_type):
                self.assertIn(provider_type, html)
        for field in [
            "pack.real_provider_readiness_summary",
            "pack.provider_readiness_cards",
            "pack.readiness_gate_checks",
            "pack.prerequisite_checklist",
            "pack.missing_readiness_requirements",
            "pack.approval_readiness_requirements",
            "pack.secret_environment_readiness",
            "pack.cost_quota_readiness",
            "pack.media_asset_readiness",
            "pack.readiness_risk_register",
            "pack.readiness_quality_checks",
            "pack.audit_preview",
            "pack.safety_boundaries",
            "summary.mode",
            "summary.provider_readiness_card_count",
            "summary.readiness_gate_check_count",
            "summary.real_invocation_allowed",
            "summary.real_execution_allowed",
            "card.readiness_id",
            "card.provider_id",
            "card.provider_type",
            "card.source_capability",
            "card.current_readiness_status",
            "card.readiness_level",
            "card.contract_ready",
            "card.mock_test_ready",
            "card.failure_policy_ready",
            "card.asset_manifest_ready",
            "card.cost_quota_guard_ready",
            "card.secret_ready",
            "card.approval_ready",
            "card.blocked_by",
            "card.recommended_operator_action",
            "card.real_invocation_allowed",
            "card.real_execution_allowed",
            "card.risk_note",
            "gate.gate_id",
            "gate.gate_name",
            "gate.gate_status",
            "gate.required_evidence",
            "gate.missing_evidence",
            "gate.blocked_reason",
            "gate.next_preview_step",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, html)
        previous = html.index("${renderProjectWorkspaceApprovalRiskQualityAuditSafetyPanel(workspace)}")
        summary = html.index("${renderProjectWorkspaceRealProviderReadinessSummaryPanel(workspace)}")
        safety = html.index("${renderProjectWorkspaceReadinessRiskQualityAuditSafetyPanel(workspace)}")
        core = html.index("${renderProjectWorkspaceCreativeCoreFlowStrip(workspace)}")
        self.assertLess(previous, summary)
        self.assertLess(summary, safety)
        self.assertLess(safety, core)

    def test_workspace_real_provider_readiness_checklist_has_bilingual_guard_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "realProviderReadinessPackTitle",
            "realProviderReadinessSummaryTitle",
            "realProviderReadinessCardsTitle",
            "realProviderReadinessGatesTitle",
            "realProviderReadinessPrerequisiteTitle",
            "realProviderReadinessMissingTitle",
            "realProviderReadinessApprovalTitle",
            "realProviderReadinessSecretTitle",
            "realProviderReadinessCostTitle",
            "realProviderReadinessMediaTitle",
            "realProviderReadinessRiskTitle",
            "realProviderReadinessAuditTitle",
            "realProviderReadinessSafetyTitle",
            "realProviderReadinessCopySummary",
            "realProviderReadinessCopyCards",
            "realProviderReadinessCopyGates",
            "realProviderReadinessCopyPrerequisite",
            "realProviderReadinessCopyMissing",
            "realProviderReadinessCopyApproval",
            "realProviderReadinessCopySecret",
            "realProviderReadinessCopyRisk",
            "realProviderReadinessCopyFull",
            "realProviderReadinessCopied",
            "realProviderReadinessCopyFailed",
            "realProviderReadinessCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn(
                "Project Workspace real provider readiness checklist bundle",
                script,
            )
            self.assertIn(
                "project_workspace_real_provider_readiness_checklist_marker",
                script,
            )
        markdown = html[
            html.index("function projectWorkspaceRealProviderReadinessChecklistSummaryText"):
            html.index("async function copyProjectWorkspaceRealProviderReadinessChecklistText")
        ]
        for key in [
            "realProviderReadinessPackTitle",
            "realProviderReadinessSummaryTitle",
            "realProviderReadinessCardsTitle",
            "realProviderReadinessGatesTitle",
            "realProviderReadinessPrerequisiteTitle",
            "realProviderReadinessMissingTitle",
            "realProviderReadinessApprovalTitle",
            "realProviderReadinessSecretTitle",
            "realProviderReadinessCostTitle",
            "realProviderReadinessMediaTitle",
            "realProviderReadinessRiskTitle",
            "realProviderReadinessAuditTitle",
            "realProviderReadinessSafetyTitle",
        ]:
            self.assertIn(key, markdown)
        section = html[
            html.index("const PROJECT_WORKSPACE_REAL_PROVIDER_READINESS_CHECKLIST_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", section)
        for safety_text in [
            "real provider readiness checklist preview",
            "not real provider enablement",
            "does not unlock real invocation",
            "does not read secrets",
            "does not read real billing or quota",
            "does not upload or download media",
            "creates no real approval",
            "locked, blocked, or review-required",
            "secret missing",
            "paid blocked",
            "quota unknown",
            "media operation blocked",
            "rollback blocked",
            "external call blocked",
            "database persistence blocked",
            "Audit preview is not written to a database",
            "Real LLM",
            "provider",
            "image",
            "video",
            "media",
            "paid",
            "registry",
            "rollback",
            "external scraping",
            "database persistence",
            "real restore",
            "real execution",
        ]:
            with self.subTest(safety_text=safety_text):
                self.assertIn(safety_text, html)
        self.assertNotIn("????", html)

    def test_workspace_network_external_call_block_guard_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace network external call block guard bundle",
            "PROJECT_WORKSPACE_NETWORK_EXTERNAL_CALL_BLOCK_GUARD_MARKER",
            "latestProjectWorkspaceNetworkExternalCallBlockGuardPack",
            "workspace_network_external_call_block_guard_pack",
            "projectWorkspaceNetworkExternalCallBlockGuardPackFromWorkspace",
            "projectWorkspaceExportNetworkExternalCallBlockGuardSnapshot",
            "projectWorkspaceExportNetworkExternalCallBlockGuardMarkdown",
            "renderProjectWorkspaceNetworkBlockGuardSummaryPanel",
            "renderProjectWorkspaceExternalCallBlockCardsPanel",
            "renderProjectWorkspaceNetworkGatePreviewContractsPanel",
            "renderProjectWorkspaceBlockedRealCallEndpointDependencyPanel",
            "renderProjectWorkspaceNetworkFailureRiskQualityAuditSafetyPanel",
            "copyProjectWorkspaceNetworkBlockGuardSummary",
            "copyProjectWorkspaceExternalCallBlockCards",
            "copyProjectWorkspaceNetworkGateChecks",
            "copyProjectWorkspaceAllowedPreviewCallContracts",
            "copyProjectWorkspaceBlockedRealCallOperations",
            "copyProjectWorkspaceProviderEndpointDependencyMap",
            "copyProjectWorkspaceNetworkFailurePolicyMap",
            "copyProjectWorkspaceNetworkRiskRegister",
            "copyProjectWorkspaceFullNetworkExternalCallBlockGuardPack",
            "workspace_network_external_call_block_guard_pack: projectWorkspaceExportNetworkExternalCallBlockGuardSnapshot(workspace)",
            "Workspace Network / External Call Block Guard",
            "Network Block Guard Summary",
            "External Call Block Cards",
            "Network Gate Checks",
            "Allowed Preview Call Contracts",
            "Blocked Real Call Operations",
            "Provider Endpoint Dependency Map",
            "Network Failure Policy Map",
            "Network Risk Register",
            "Audit Preview",
            "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for provider_type in [
            "llm_text_generation", "video_generation_provider",
            "image_generation_provider", "media_storage_provider",
            "external_scraping_provider", "translation_provider",
            "analytics_or_tracking_provider", "database_persistence_provider",
            "approval_or_ticket_provider", "rollback_restore_provider",
        ]:
            with self.subTest(provider_type=provider_type):
                self.assertIn(provider_type, html)
        for field in [
            "pack.network_block_guard_summary",
            "pack.external_call_block_cards",
            "pack.network_gate_checks",
            "pack.allowed_preview_call_contracts",
            "pack.blocked_real_call_operations",
            "pack.provider_endpoint_dependency_map",
            "pack.network_failure_policy_map",
            "pack.network_risk_register",
            "pack.network_guard_quality_checks",
            "pack.audit_preview",
            "pack.safety_boundaries",
            "summary.mode",
            "summary.external_call_block_card_count",
            "summary.network_gate_check_count",
            "summary.external_call_allowed",
            "summary.real_provider_call_allowed",
            "summary.secret_use_allowed",
            "summary.real_invocation_allowed",
            "summary.real_execution_allowed",
            "card.block_card_id",
            "card.provider_id",
            "card.provider_type",
            "card.source_capability",
            "card.external_call_type",
            "card.target_endpoint_preview",
            "card.network_access_status",
            "card.allowed_preview_modes",
            "card.blocked_real_modes",
            "card.external_call_allowed",
            "card.real_provider_call_allowed",
            "card.secret_use_allowed",
            "card.real_invocation_allowed",
            "card.real_execution_allowed",
            "card.blocked_by",
            "card.recommended_operator_action",
            "card.risk_note",
            "gate.gate_id",
            "gate.provider_id",
            "gate.provider_type",
            "gate.gate_name",
            "gate.gate_status",
            "gate.required_evidence",
            "gate.missing_evidence",
            "gate.blocked_reason",
            "gate.next_preview_step",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, html)
        for blocked_operation in [
            "http_request", "provider_api_call", "webhook_call",
            "external_scrape", "media_upload_call", "media_download_call",
            "billing_api_call", "database_network_call", "rollback_call",
        ]:
            with self.subTest(blocked_operation=blocked_operation):
                self.assertIn(blocked_operation, html)
        previous = html.index("${renderProjectWorkspaceEnvironmentRiskQualityAuditSafetyPanel(workspace)}")
        summary = html.index("${renderProjectWorkspaceNetworkBlockGuardSummaryPanel(workspace)}")
        safety = html.index("${renderProjectWorkspaceNetworkFailureRiskQualityAuditSafetyPanel(workspace)}")
        core = html.index("${renderProjectWorkspaceCreativeCoreFlowStrip(workspace)}")
        self.assertLess(previous, summary)
        self.assertLess(summary, safety)
        self.assertLess(safety, core)

    def test_workspace_network_external_call_block_guard_has_bilingual_guard_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "networkExternalCallBlockGuardPackTitle",
            "networkExternalCallBlockGuardSummaryTitle",
            "networkExternalCallBlockGuardCardsTitle",
            "networkExternalCallBlockGuardGateTitle",
            "networkExternalCallBlockGuardPreviewContractsTitle",
            "networkExternalCallBlockGuardBlockedTitle",
            "networkExternalCallBlockGuardDependencyTitle",
            "networkExternalCallBlockGuardFailureTitle",
            "networkExternalCallBlockGuardRiskTitle",
            "networkExternalCallBlockGuardAuditTitle",
            "networkExternalCallBlockGuardSafetyTitle",
            "networkExternalCallBlockGuardCopySummary",
            "networkExternalCallBlockGuardCopyCards",
            "networkExternalCallBlockGuardCopyGateChecks",
            "networkExternalCallBlockGuardCopyPreviewContracts",
            "networkExternalCallBlockGuardCopyBlocked",
            "networkExternalCallBlockGuardCopyDependency",
            "networkExternalCallBlockGuardCopyFailure",
            "networkExternalCallBlockGuardCopyRisk",
            "networkExternalCallBlockGuardCopyFull",
            "networkExternalCallBlockGuardCopied",
            "networkExternalCallBlockGuardCopyFailed",
            "networkExternalCallBlockGuardCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn(
                "Project Workspace network external call block guard bundle",
                script,
            )
            self.assertIn(
                "project_workspace_network_external_call_block_guard_marker",
                script,
            )
        markdown = html[
            html.index("function projectWorkspaceNetworkExternalCallBlockGuardSummaryText"):
            html.index("async function copyProjectWorkspaceNetworkExternalCallBlockGuardText")
        ]
        for key in [
            "networkExternalCallBlockGuardPackTitle",
            "networkExternalCallBlockGuardSummaryTitle",
            "networkExternalCallBlockGuardCardsTitle",
            "networkExternalCallBlockGuardGateTitle",
            "networkExternalCallBlockGuardPreviewContractsTitle",
            "networkExternalCallBlockGuardBlockedTitle",
            "networkExternalCallBlockGuardDependencyTitle",
            "networkExternalCallBlockGuardFailureTitle",
            "networkExternalCallBlockGuardRiskTitle",
            "networkExternalCallBlockGuardAuditTitle",
            "networkExternalCallBlockGuardSafetyTitle",
        ]:
            self.assertIn(key, markdown)
        section = html[
            html.index("const PROJECT_WORKSPACE_NETWORK_EXTERNAL_CALL_BLOCK_GUARD_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", section)
        for safety_text in [
            "Network block guard preview",
            "not a real network firewall",
            "does not send HTTP requests",
            "call provider APIs",
            "invoke webhooks",
            "scrape externally",
            "transfer media",
            "use secrets",
            "validate endpoints",
            "write databases",
            "retry",
            "restore",
            "rollback",
            "External call block cards show endpoint",
            "Allowed preview call contracts describe mock",
            "external call blocked",
            "provider endpoint missing",
            "webhook blocked",
            "media transfer blocked",
            "external scraping blocked",
            "database network blocked",
            "rollback endpoint blocked",
            "billing endpoint blocked",
            "Audit preview is not written to a database",
            "Real LLM",
            "provider",
            "image",
            "video",
            "media",
            "paid",
            "registry",
            "rollback",
            "external scraping",
            "database persistence",
            "real restore",
            "real execution",
            "secret read",
            "external call",
        ]:
            with self.subTest(safety_text=safety_text):
                self.assertIn(safety_text, html)
        self.assertNotIn("????", html)

    def test_workspace_real_execution_approval_token_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace real execution approval token bundle",
            "PROJECT_WORKSPACE_REAL_EXECUTION_APPROVAL_TOKEN_MARKER",
            "latestProjectWorkspaceRealExecutionApprovalTokenPack",
            "workspace_real_execution_approval_token_pack",
            "projectWorkspaceRealExecutionApprovalTokenPackFromWorkspace",
            "projectWorkspaceExportRealExecutionApprovalTokenSnapshot",
            "projectWorkspaceExportRealExecutionApprovalTokenMarkdown",
            "renderProjectWorkspaceApprovalTokenSummaryPanel",
            "renderProjectWorkspaceApprovalTokenPreviewCardsPanel",
            "renderProjectWorkspaceExecutionApprovalGateSignoffPanel",
            "renderProjectWorkspaceTokenBlockerPacketScopePanel",
            "renderProjectWorkspaceApprovalTokenRiskQualityAuditSafetyPanel",
            "copyProjectWorkspaceApprovalTokenSummary",
            "copyProjectWorkspaceApprovalTokenPreviewCards",
            "copyProjectWorkspaceExecutionApprovalGateChecks",
            "copyProjectWorkspaceRequiredSignoffMatrix",
            "copyProjectWorkspaceTokenBlockerCards",
            "copyProjectWorkspaceApprovalPacketRequirements",
            "copyProjectWorkspaceTokenScopeBoundaryRules",
            "copyProjectWorkspaceApprovalTokenRiskRegister",
            "copyProjectWorkspaceFullRealExecutionApprovalTokenPack",
            "workspace_real_execution_approval_token_pack: projectWorkspaceExportRealExecutionApprovalTokenSnapshot(workspace)",
            "Workspace Real Execution Approval Token Preview",
            "Approval Token Summary",
            "Approval Token Preview Cards",
            "Execution Approval Gate Checks",
            "Required Signoff Matrix",
            "Token Blocker Cards",
            "Approval Packet Requirements",
            "Token Scope Boundary Rules",
            "Approval Token Risk Register",
            "Audit Preview",
            "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for provider_type in [
            "llm_text_generation", "video_generation_provider",
            "image_generation_provider", "media_storage_provider",
            "external_scraping_provider", "translation_provider",
            "analytics_or_tracking_provider", "database_persistence_provider",
            "approval_or_ticket_provider", "rollback_restore_provider",
        ]:
            with self.subTest(provider_type=provider_type):
                self.assertIn(provider_type, html)
        for field in [
            "pack.approval_token_summary",
            "pack.approval_token_preview_cards",
            "pack.execution_approval_gate_checks",
            "pack.required_signoff_matrix",
            "pack.token_blocker_cards",
            "pack.approval_packet_requirements",
            "pack.token_scope_boundary_rules",
            "pack.approval_token_risk_register",
            "pack.approval_token_quality_checks",
            "pack.audit_preview",
            "pack.safety_boundaries",
            "summary.mode",
            "summary.token_preview_count",
            "summary.execution_approval_gate_check_count",
            "summary.required_signoff_count",
            "summary.token_blocker_count",
            "summary.token_issue_allowed",
            "summary.token_validation_allowed",
            "summary.real_invocation_allowed",
            "summary.real_execution_allowed",
            "card.token_preview_id",
            "card.provider_id",
            "card.provider_type",
            "card.source_capability",
            "card.token_purpose",
            "card.token_scope_preview",
            "card.required_signoffs",
            "card.required_evidence",
            "card.blocked_by",
            "card.token_issue_allowed",
            "card.token_validation_allowed",
            "card.real_invocation_allowed",
            "card.real_execution_allowed",
            "card.recommended_operator_action",
            "card.risk_note",
            "gate.gate_id",
            "gate.provider_id",
            "gate.provider_type",
            "gate.gate_name",
            "gate.gate_status",
            "gate.required_approval_refs",
            "gate.missing_approval_refs",
            "gate.required_evidence",
            "gate.blocked_reason",
            "gate.next_preview_step",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, html)
        for required_text in [
            "human review",
            "cost review",
            "secret review",
            "network review",
            "media review",
            "rollback review",
            "database review",
            "token issue",
            "token validation",
            "token use for execution",
            "token persistence",
            "token export",
            "real provider call",
            "external call",
            "secret read",
            "paid operation",
            "media transfer",
            "database write",
            "rollback",
            "unauthorized execution",
            "missing signoff",
            "secret gate blocked",
            "network blocked",
            "paid blocked",
            "rollback blocked",
            "database persistence blocked",
        ]:
            with self.subTest(required_text=required_text):
                self.assertIn(required_text, html)
        previous = html.index("${renderProjectWorkspaceNetworkFailureRiskQualityAuditSafetyPanel(workspace)}")
        summary = html.index("${renderProjectWorkspaceApprovalTokenSummaryPanel(workspace)}")
        safety = html.index("${renderProjectWorkspaceApprovalTokenRiskQualityAuditSafetyPanel(workspace)}")
        core = html.index("${renderProjectWorkspaceCreativeCoreFlowStrip(workspace)}")
        self.assertLess(previous, summary)
        self.assertLess(summary, safety)
        self.assertLess(safety, core)

    def test_workspace_real_execution_approval_token_has_bilingual_guard_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "realExecutionApprovalTokenPackTitle",
            "realExecutionApprovalTokenSummaryTitle",
            "realExecutionApprovalTokenCardsTitle",
            "realExecutionApprovalTokenGateTitle",
            "realExecutionApprovalTokenSignoffTitle",
            "realExecutionApprovalTokenBlockerTitle",
            "realExecutionApprovalTokenPacketTitle",
            "realExecutionApprovalTokenScopeTitle",
            "realExecutionApprovalTokenRiskTitle",
            "realExecutionApprovalTokenAuditTitle",
            "realExecutionApprovalTokenSafetyTitle",
            "realExecutionApprovalTokenCopySummary",
            "realExecutionApprovalTokenCopyCards",
            "realExecutionApprovalTokenCopyGateChecks",
            "realExecutionApprovalTokenCopySignoff",
            "realExecutionApprovalTokenCopyBlockers",
            "realExecutionApprovalTokenCopyPacket",
            "realExecutionApprovalTokenCopyScope",
            "realExecutionApprovalTokenCopyRisk",
            "realExecutionApprovalTokenCopyFull",
            "realExecutionApprovalTokenCopied",
            "realExecutionApprovalTokenCopyFailed",
            "realExecutionApprovalTokenCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn(
                "Project Workspace real execution approval token bundle",
                script,
            )
            self.assertIn(
                "project_workspace_real_execution_approval_token_marker",
                script,
            )
        markdown = html[
            html.index("function projectWorkspaceRealExecutionApprovalTokenSummaryText"):
            html.index("async function copyProjectWorkspaceRealExecutionApprovalTokenText")
        ]
        for key in [
            "realExecutionApprovalTokenPackTitle",
            "realExecutionApprovalTokenSummaryTitle",
            "realExecutionApprovalTokenCardsTitle",
            "realExecutionApprovalTokenGateTitle",
            "realExecutionApprovalTokenSignoffTitle",
            "realExecutionApprovalTokenBlockerTitle",
            "realExecutionApprovalTokenPacketTitle",
            "realExecutionApprovalTokenScopeTitle",
            "realExecutionApprovalTokenRiskTitle",
            "realExecutionApprovalTokenAuditTitle",
            "realExecutionApprovalTokenSafetyTitle",
        ]:
            self.assertIn(key, markdown)
        section = html[
            html.index("const PROJECT_WORKSPACE_REAL_EXECUTION_APPROVAL_TOKEN_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", section)
        for safety_text in [
            "approval token preview",
            "not a real token system",
            "does not issue a real token",
            "does not validate a real token",
            "creates no real approval",
            "unlocks no real provider capability",
            "No real token is issued",
            "Audit preview is not written to a database",
            "Real LLM",
            "provider",
            "image",
            "video",
            "media",
            "paid",
            "registry",
            "rollback",
            "external scraping",
            "database persistence",
            "real restore",
            "real execution",
            "secret read",
            "external call",
            "token issue",
        ]:
            with self.subTest(safety_text=safety_text):
                self.assertIn(safety_text, html)
        self.assertNotIn("????", html)

    def test_workspace_provider_invocation_audit_packet_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace provider invocation audit packet bundle",
            "PROJECT_WORKSPACE_PROVIDER_INVOCATION_AUDIT_PACKET_MARKER",
            "latestProjectWorkspaceProviderInvocationAuditPacketPack",
            "workspace_provider_invocation_audit_packet_pack",
            "projectWorkspaceProviderInvocationAuditPacketPackFromWorkspace",
            "projectWorkspaceExportProviderInvocationAuditPacketSnapshot",
            "projectWorkspaceExportProviderInvocationAuditPacketMarkdown",
            "renderProjectWorkspaceInvocationAuditPacketSummaryPanel",
            "renderProjectWorkspaceAuditPacketCardsPanel",
            "renderProjectWorkspacePreInvocationEvidenceGatePanel",
            "renderProjectWorkspaceBlockedOperationSignoffExportPanel",
            "renderProjectWorkspaceAuditTraceRiskQualitySafetyPanel",
            "copyProjectWorkspaceInvocationAuditPacketSummary",
            "copyProjectWorkspaceAuditPacketCards",
            "copyProjectWorkspacePreInvocationEvidenceBundle",
            "copyProjectWorkspaceGateSnapshotCards",
            "copyProjectWorkspaceBlockedOperationSummary",
            "copyProjectWorkspaceOperatorSignoffSnapshot",
            "copyProjectWorkspaceAuditExportManifest",
            "copyProjectWorkspaceAuditTraceabilityMap",
            "copyProjectWorkspaceFullProviderInvocationAuditPacketPack",
            "workspace_provider_invocation_audit_packet_pack: projectWorkspaceExportProviderInvocationAuditPacketSnapshot(workspace)",
            "Workspace Provider Invocation Audit Packet",
            "Invocation Audit Packet Summary",
            "Audit Packet Cards",
            "Pre-Invocation Evidence Bundle",
            "Gate Snapshot Cards",
            "Blocked Operation Summary",
            "Operator Signoff Snapshot",
            "Audit Export Manifest",
            "Audit Traceability Map",
            "Audit Packet Risk Register",
            "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for provider_type in [
            "llm_text_generation", "video_generation_provider",
            "image_generation_provider", "media_storage_provider",
            "external_scraping_provider", "translation_provider",
            "analytics_or_tracking_provider", "database_persistence_provider",
            "approval_or_ticket_provider", "rollback_restore_provider",
        ]:
            with self.subTest(provider_type=provider_type):
                self.assertIn(provider_type, html)
        for field in [
            "pack.invocation_audit_packet_summary",
            "pack.audit_packet_cards",
            "pack.pre_invocation_evidence_bundle",
            "pack.gate_snapshot_cards",
            "pack.blocked_operation_summary",
            "pack.operator_signoff_snapshot",
            "pack.audit_export_manifest",
            "pack.audit_traceability_map",
            "pack.audit_packet_risk_register",
            "pack.audit_packet_quality_checks",
            "pack.safety_boundaries",
            "summary.mode",
            "summary.audit_packet_card_count",
            "summary.pre_invocation_evidence_count",
            "summary.gate_snapshot_card_count",
            "summary.blocked_operation_count",
            "summary.database_write_allowed",
            "summary.real_invocation_allowed",
            "summary.real_execution_allowed",
            "card.audit_packet_id",
            "card.provider_id",
            "card.provider_type",
            "card.source_capability",
            "card.packet_status",
            "card.required_evidence_refs",
            "card.gate_snapshot_refs",
            "card.blocked_operation_refs",
            "card.operator_signoff_refs",
            "card.audit_export_allowed",
            "card.database_write_allowed",
            "card.real_invocation_allowed",
            "card.real_execution_allowed",
            "gate.snapshot_id",
            "gate.provider_id",
            "gate.provider_type",
            "gate.gate_source",
            "gate.gate_status",
            "gate.captured_fields",
            "gate.missing_fields",
            "gate.blocked_reason",
            "gate.real_invocation_allowed",
            "gate.real_execution_allowed",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, html)
        for required_text in [
            "provider call", "external call", "secret read",
            "token issue", "paid operation", "media transfer",
            "database write", "rollback", "token", "secret",
            "network", "cost", "asset", "failure", "readiness",
            "agent ledger", "previous packs", "real logs",
            "missing signoff", "network blocked", "secret blocked",
            "token blocked", "paid blocked", "database write blocked",
            "rollback blocked", "media blocked",
        ]:
            with self.subTest(required_text=required_text):
                self.assertIn(required_text, html)
        previous = html.index("${renderProjectWorkspaceApprovalTokenRiskQualityAuditSafetyPanel(workspace)}")
        summary = html.index("${renderProjectWorkspaceInvocationAuditPacketSummaryPanel(workspace)}")
        safety = html.index("${renderProjectWorkspaceAuditTraceRiskQualitySafetyPanel(workspace)}")
        core = html.index("${renderProjectWorkspaceCreativeCoreFlowStrip(workspace)}")
        self.assertLess(previous, summary)
        self.assertLess(summary, safety)
        self.assertLess(safety, core)

    def test_workspace_provider_invocation_audit_packet_has_bilingual_guard_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "providerInvocationAuditPacketPackTitle",
            "providerInvocationAuditPacketSummaryTitle",
            "providerInvocationAuditPacketCardsTitle",
            "providerInvocationAuditPacketEvidenceTitle",
            "providerInvocationAuditPacketGateTitle",
            "providerInvocationAuditPacketBlockedTitle",
            "providerInvocationAuditPacketSignoffTitle",
            "providerInvocationAuditPacketExportTitle",
            "providerInvocationAuditPacketTraceTitle",
            "providerInvocationAuditPacketRiskTitle",
            "providerInvocationAuditPacketSafetyTitle",
            "providerInvocationAuditPacketCopySummary",
            "providerInvocationAuditPacketCopyCards",
            "providerInvocationAuditPacketCopyEvidence",
            "providerInvocationAuditPacketCopyGate",
            "providerInvocationAuditPacketCopyBlocked",
            "providerInvocationAuditPacketCopySignoff",
            "providerInvocationAuditPacketCopyExport",
            "providerInvocationAuditPacketCopyTrace",
            "providerInvocationAuditPacketCopyFull",
            "providerInvocationAuditPacketCopied",
            "providerInvocationAuditPacketCopyFailed",
            "providerInvocationAuditPacketCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn(
                "Project Workspace provider invocation audit packet bundle",
                script,
            )
            self.assertIn(
                "project_workspace_provider_invocation_audit_packet_marker",
                script,
            )
        markdown = html[
            html.index("function projectWorkspaceProviderInvocationAuditPacketSummaryText"):
            html.index("async function copyProjectWorkspaceProviderInvocationAuditPacketText")
        ]
        for key in [
            "providerInvocationAuditPacketPackTitle",
            "providerInvocationAuditPacketSummaryTitle",
            "providerInvocationAuditPacketCardsTitle",
            "providerInvocationAuditPacketEvidenceTitle",
            "providerInvocationAuditPacketGateTitle",
            "providerInvocationAuditPacketBlockedTitle",
            "providerInvocationAuditPacketSignoffTitle",
            "providerInvocationAuditPacketExportTitle",
            "providerInvocationAuditPacketTraceTitle",
            "providerInvocationAuditPacketRiskTitle",
            "providerInvocationAuditPacketSafetyTitle",
        ]:
            self.assertIn(key, markdown)
        section = html[
            html.index("const PROJECT_WORKSPACE_PROVIDER_INVOCATION_AUDIT_PACKET_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", section)
        for safety_text in [
            "invocation audit packet preview",
            "not a real provider invocation audit system",
            "creates no real audit record",
            "writes no database",
            "uploads no audit packet",
            "issues no token",
            "reads no secret",
            "calls no provider",
            "sends no HTTP request",
            "invokes no webhook",
            "No real logs",
            "Real LLM",
            "provider",
            "image",
            "video",
            "media",
            "paid",
            "registry",
            "rollback",
            "external scraping",
            "database persistence",
            "real restore",
            "real execution",
            "secret read",
            "external call",
            "token issue",
        ]:
            with self.subTest(safety_text=safety_text):
                self.assertIn(safety_text, html)
        self.assertNotIn("????", html)

    def test_workspace_review_evidence_quality_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace review evidence quality bundle",
            "PROJECT_WORKSPACE_REVIEW_EVIDENCE_QUALITY_MARKER",
            "latestProjectWorkspaceReviewEvidenceQualityPack",
            "review_evidence_quality_pack",
            "projectWorkspaceReviewEvidenceQualityPackFromWorkspace",
            "projectWorkspaceExportReviewEvidenceQualitySnapshot",
            "projectWorkspaceExportReviewEvidenceQualityMarkdown",
            "renderProjectWorkspaceReviewEvidenceQualitySummaryPanel",
            "renderProjectWorkspaceReviewSourceQualityCardsPanel",
            "renderProjectWorkspaceQuoteBuyerLanguagePanel",
            "renderProjectWorkspaceClaimSupportEvidenceGapsPanel",
            "renderProjectWorkspaceNoiseDoNotClaimRecommendationSafetyPanel",
            "copyProjectWorkspaceEvidenceQualitySummary",
            "copyProjectWorkspaceReviewSourceQualityCards",
            "copyProjectWorkspaceQuoteQualityCards",
            "copyProjectWorkspaceClaimSupportMatrix",
            "copyProjectWorkspaceEvidenceGapCards",
            "copyProjectWorkspaceBuyerLanguageSignals",
            "copyProjectWorkspaceDoNotClaimReinforcement",
            "copyProjectWorkspaceEvidenceQualityRecommendations",
            "copyProjectWorkspaceFullReviewEvidenceQualityPack",
            "review_evidence_quality_pack: projectWorkspaceExportReviewEvidenceQualitySnapshot(workspace)",
            "Review Evidence Quality Upgrade",
            "Evidence Quality Summary",
            "Review Source Quality Cards",
            "Quote Quality Cards",
            "Buyer Language Signal Cards",
            "Claim Support Matrix",
            "Evidence Gap Cards",
            "Duplicate And Noise Checks",
            "Sample Strength Assessment",
            "Do Not Claim Reinforcement",
            "Evidence Quality Recommendations",
            "Audit Preview",
            "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for field in [
            "pack.evidence_quality_summary",
            "pack.review_source_quality_cards",
            "pack.quote_quality_cards",
            "pack.claim_support_matrix",
            "pack.evidence_gap_cards",
            "pack.duplicate_and_noise_checks",
            "pack.sample_strength_assessment",
            "pack.buyer_language_signal_cards",
            "pack.do_not_claim_reinforcement",
            "pack.evidence_quality_recommendations",
            "pack.evidence_quality_checks",
            "pack.audit_preview",
            "pack.safety_boundaries",
            "summary.mode",
            "summary.source_card_count",
            "summary.quote_card_count",
            "summary.claim_row_count",
            "summary.overall_sample_strength",
            "summary.recommended_operator_action",
            "summary.real_scraping_allowed",
            "summary.real_execution_allowed",
            "card.source_id",
            "card.source_type",
            "card.source_label",
            "card.review_count",
            "card.usable_review_count",
            "card.quote_count",
            "card.quality_status",
            "card.sample_strength",
            "card.coverage_notes",
            "card.detected_noise",
            "quote.quote_id",
            "quote.quote_text",
            "quote.quote_role",
            "quote.supports_claim",
            "quote.claim_ref",
            "quote.specificity_level",
            "quote.buyer_language_signal",
            "quote.quality_status",
            "claim.claim_id",
            "claim.claim_text",
            "claim.support_status",
            "claim.supporting_quote_ids",
            "claim.weakness_reason",
            "claim.allowed_usage",
            "claim.disallowed_usage",
            "claim.recommended_rewrite",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, html)
        previous = html.index("renderProjectWorkspaceAuditTraceRiskQualitySafetyPanel(workspace)")
        summary = html.index("renderProjectWorkspaceReviewEvidenceQualitySummaryPanel(workspace)")
        sources = html.index("renderProjectWorkspaceReviewSourceQualityCardsPanel(workspace)")
        quotes = html.index("renderProjectWorkspaceQuoteBuyerLanguagePanel(workspace)")
        claims = html.index("renderProjectWorkspaceClaimSupportEvidenceGapsPanel(workspace)")
        noise = html.index("renderProjectWorkspaceNoiseDoNotClaimRecommendationSafetyPanel(workspace)")
        core = html.index("renderProjectWorkspaceCreativeCoreFlowStrip(workspace)")
        self.assertLess(previous, summary)
        self.assertLess(summary, sources)
        self.assertLess(sources, quotes)
        self.assertLess(quotes, claims)
        self.assertLess(claims, noise)
        self.assertLess(noise, core)

    def test_workspace_review_evidence_quality_has_bilingual_guard_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "reviewEvidenceQualityPackTitle",
            "reviewEvidenceQualitySummaryTitle",
            "reviewEvidenceQualitySourceCardsTitle",
            "reviewEvidenceQualityQuoteCardsTitle",
            "reviewEvidenceQualityBuyerSignalsTitle",
            "reviewEvidenceQualityClaimMatrixTitle",
            "reviewEvidenceQualityGapCardsTitle",
            "reviewEvidenceQualityNoiseChecksTitle",
            "reviewEvidenceQualitySampleStrengthTitle",
            "reviewEvidenceQualityDoNotClaimTitle",
            "reviewEvidenceQualityRecommendationsTitle",
            "reviewEvidenceQualityAuditPreviewTitle",
            "reviewEvidenceQualitySafetyTitle",
            "reviewEvidenceQualityCopySummary",
            "reviewEvidenceQualityCopySourceCards",
            "reviewEvidenceQualityCopyQuoteCards",
            "reviewEvidenceQualityCopyClaimMatrix",
            "reviewEvidenceQualityCopyGapCards",
            "reviewEvidenceQualityCopyBuyerSignals",
            "reviewEvidenceQualityCopyDoNotClaim",
            "reviewEvidenceQualityCopyRecommendations",
            "reviewEvidenceQualityCopyFull",
            "reviewEvidenceQualityCopied",
            "reviewEvidenceQualityCopyFailed",
            "reviewEvidenceQualityCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace review evidence quality bundle", script)
            self.assertIn("project_workspace_review_evidence_quality_marker", script)
        markdown = html[
            html.index("function projectWorkspaceReviewEvidenceQualitySummaryText"):
            html.index("async function copyProjectWorkspaceReviewEvidenceQualityText")
        ]
        for key in [
            "reviewEvidenceQualityPackTitle",
            "reviewEvidenceQualitySummaryTitle",
            "reviewEvidenceQualitySourceCardsTitle",
            "reviewEvidenceQualityQuoteCardsTitle",
            "reviewEvidenceQualityBuyerSignalsTitle",
            "reviewEvidenceQualityClaimMatrixTitle",
            "reviewEvidenceQualityGapCardsTitle",
            "reviewEvidenceQualityNoiseChecksTitle",
            "reviewEvidenceQualitySampleStrengthTitle",
            "reviewEvidenceQualityDoNotClaimTitle",
            "reviewEvidenceQualityRecommendationsTitle",
            "reviewEvidenceQualityAuditPreviewTitle",
            "reviewEvidenceQualitySafetyTitle",
        ]:
            self.assertIn(key, markdown)
        section = html[
            html.index("const PROJECT_WORKSPACE_REVIEW_EVIDENCE_QUALITY_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", section)
        for safety_text in [
            "deterministic evidence quality preview",
            "not real scraping",
            "LLM evidence generation",
            "does not scrape reviews",
            "call an LLM",
            "create buyer evidence",
            "persist audit records",
            "create approvals",
            "create operator tasks",
            "call providers",
            "paid operation",
            "strong_quote",
            "weak_quote",
            "generic_quote",
            "missing_quote",
            "Unsupported",
            "weakly supported",
            "supported",
            "Duplicate",
            "too_short",
            "generic",
            "empty",
            "vague",
            "Real LLM",
            "provider",
            "external scraping",
            "database persistence",
            "real execution",
        ]:
            with self.subTest(safety_text=safety_text):
                self.assertIn(safety_text, html)
        self.assertNotIn("????", html)

    def test_workspace_claim_risk_guard_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace claim risk guard bundle",
            "project_workspace_claim_risk_guard_marker",
            "PROJECT_WORKSPACE_CLAIM_RISK_GUARD_MARKER",
            "latestProjectWorkspaceClaimRiskGuardPack",
            "claim_risk_guard_pack",
            "projectWorkspaceClaimRiskGuardPackFromWorkspace",
            "projectWorkspaceExportClaimRiskGuardSnapshot",
            "projectWorkspaceExportClaimRiskGuardMarkdown",
            "renderProjectWorkspaceClaimRiskSummaryPanel",
            "renderProjectWorkspaceClaimRiskCardsPanel",
            "renderProjectWorkspaceAllowedRestrictedBlockedClaimCardsPanel",
            "renderProjectWorkspaceClaimRewriteTraceOverclaimPanel",
            "renderProjectWorkspaceClaimPlatformDoNotClaimQualityAuditSafetyPanel",
            "copyProjectWorkspaceClaimRiskSummary",
            "copyProjectWorkspaceClaimRiskCards",
            "copyProjectWorkspaceAllowedClaimCards",
            "copyProjectWorkspaceRestrictedClaimCards",
            "copyProjectWorkspaceBlockedClaimCards",
            "copyProjectWorkspaceClaimRewriteSuggestions",
            "copyProjectWorkspaceEvidenceToClaimTrace",
            "copyProjectWorkspaceOverclaimPatternChecks",
            "copyProjectWorkspaceClaimDoNotClaimEnforcement",
            "copyProjectWorkspaceFullClaimRiskGuardPack",
            "claim_risk_guard_pack: projectWorkspaceExportClaimRiskGuardSnapshot(workspace)",
            "Claim Risk Guard / Evidence Claim Safety",
            "Claim Risk Summary",
            "Claim Risk Cards",
            "Allowed Claim Cards",
            "Restricted Claim Cards",
            "Blocked Claim Cards",
            "Claim Rewrite Suggestions",
            "Evidence To Claim Trace",
            "Overclaim Pattern Checks",
            "Platform Claim Safety Notes",
            "Do Not Claim Enforcement",
            "Audit Preview",
            "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for field in [
            "pack.claim_risk_summary",
            "pack.claim_risk_cards",
            "pack.allowed_claim_cards",
            "pack.restricted_claim_cards",
            "pack.blocked_claim_cards",
            "pack.claim_rewrite_suggestions",
            "pack.evidence_to_claim_trace",
            "pack.overclaim_pattern_checks",
            "pack.platform_claim_safety_notes",
            "pack.do_not_claim_enforcement",
            "pack.claim_risk_quality_checks",
            "pack.audit_preview",
            "pack.safety_boundaries",
            "summary.mode",
            "summary.claim_count",
            "summary.allowed_claim_count",
            "summary.restricted_claim_count",
            "summary.blocked_claim_count",
            "summary.recommended_operator_action",
            "summary.real_policy_check_allowed",
            "summary.real_execution_allowed",
            "card.claim_id",
            "card.claim_text",
            "card.claim_source",
            "card.support_status",
            "card.risk_level",
            "card.risk_category",
            "card.supporting_quote_ids",
            "card.evidence_gap_refs",
            "card.allowed_usage",
            "card.restricted_usage",
            "card.disallowed_usage",
            "card.recommended_rewrite",
            "card.operator_review_required",
            "card.real_policy_check_allowed",
            "card.real_execution_allowed",
            "card.risk_note",
            "card.safe_claim_text",
            "card.evidence_basis",
            "card.allowed_channels",
            "card.usage_note",
            "card.blocked_claim_text",
            "card.blocked_reason",
            "card.missing_evidence_refs",
            "card.do_not_claim_refs",
            "card.recommended_safe_alternative",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, html)
        previous = html.index("renderProjectWorkspaceNoiseDoNotClaimRecommendationSafetyPanel(workspace)")
        summary = html.index("renderProjectWorkspaceClaimRiskSummaryPanel(workspace)")
        cards = html.index("renderProjectWorkspaceClaimRiskCardsPanel(workspace)")
        buckets = html.index("renderProjectWorkspaceAllowedRestrictedBlockedClaimCardsPanel(workspace)")
        rewrite = html.index("renderProjectWorkspaceClaimRewriteTraceOverclaimPanel(workspace)")
        safety = html.index("renderProjectWorkspaceClaimPlatformDoNotClaimQualityAuditSafetyPanel(workspace)")
        core = html.index("renderProjectWorkspaceCreativeCoreFlowStrip(workspace)")
        self.assertLess(previous, summary)
        self.assertLess(summary, cards)
        self.assertLess(cards, buckets)
        self.assertLess(buckets, rewrite)
        self.assertLess(rewrite, safety)
        self.assertLess(safety, core)

    def test_workspace_claim_risk_guard_has_bilingual_guard_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "claimRiskGuardPackTitle",
            "claimRiskGuardSummaryTitle",
            "claimRiskGuardCardsTitle",
            "claimRiskGuardAllowedTitle",
            "claimRiskGuardRestrictedTitle",
            "claimRiskGuardBlockedTitle",
            "claimRiskGuardRewriteTitle",
            "claimRiskGuardTraceTitle",
            "claimRiskGuardOverclaimTitle",
            "claimRiskGuardPlatformNotesTitle",
            "claimRiskGuardDoNotClaimTitle",
            "claimRiskGuardQualityChecksTitle",
            "claimRiskGuardAuditPreviewTitle",
            "claimRiskGuardSafetyTitle",
            "claimRiskGuardCopySummary",
            "claimRiskGuardCopyRiskCards",
            "claimRiskGuardCopyAllowed",
            "claimRiskGuardCopyRestricted",
            "claimRiskGuardCopyBlocked",
            "claimRiskGuardCopyRewrite",
            "claimRiskGuardCopyTrace",
            "claimRiskGuardCopyOverclaim",
            "claimRiskGuardCopyDoNotClaim",
            "claimRiskGuardCopyFull",
            "claimRiskGuardCopied",
            "claimRiskGuardCopyFailed",
            "claimRiskGuardCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace claim risk guard bundle", script)
            self.assertIn("project_workspace_claim_risk_guard_marker", script)
        markdown = html[
            html.index("function projectWorkspaceClaimRiskGuardSummaryText"):
            html.index("async function copyProjectWorkspaceClaimRiskGuardText")
        ]
        for key in [
            "claimRiskGuardPackTitle",
            "claimRiskGuardSummaryTitle",
            "claimRiskGuardCardsTitle",
            "claimRiskGuardAllowedTitle",
            "claimRiskGuardRestrictedTitle",
            "claimRiskGuardBlockedTitle",
            "claimRiskGuardRewriteTitle",
            "claimRiskGuardTraceTitle",
            "claimRiskGuardOverclaimTitle",
            "claimRiskGuardPlatformNotesTitle",
            "claimRiskGuardDoNotClaimTitle",
            "claimRiskGuardAuditPreviewTitle",
            "claimRiskGuardSafetyTitle",
        ]:
            self.assertIn(key, markdown)
        section = html[
            html.index("const PROJECT_WORKSPACE_CLAIM_RISK_GUARD_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", section)
        for safety_text in [
            "deterministic claim risk preview",
            "not legal advice",
            "not a real policy API check",
            "not a compliance conclusion",
            "Supported / weakly supported / unsupported / overclaim / missing evidence / do_not_claim violation",
            "absolute wording",
            "guaranteed outcome",
            "medical-like claim",
            "unsupported comparison",
            "best/first/only",
            "external policy needed",
            "missing quote",
            "does not query real law",
            "real policy APIs",
            "real logs",
            "real history tables",
            "do not call an LLM",
            "Provider, LLM, external scraping, database persistence, real execution, and real policy check remain disabled.",
            "Blocked claims cannot be used directly for generated copy.",
        ]:
            with self.subTest(safety_text=safety_text):
                self.assertIn(safety_text, html)
        self.assertNotIn("????", html)

    def test_workspace_claim_safe_creative_brief_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace claim-safe creative brief bundle",
            "project_workspace_claim_safe_creative_brief_marker",
            "PROJECT_WORKSPACE_CLAIM_SAFE_CREATIVE_BRIEF_MARKER",
            "latestProjectWorkspaceClaimSafeCreativeBriefPack",
            "claim_safe_creative_brief_pack",
            "projectWorkspaceClaimSafeCreativeBriefPackFromWorkspace",
            "projectWorkspaceExportClaimSafeCreativeBriefSnapshot",
            "projectWorkspaceExportClaimSafeCreativeBriefMarkdown",
            "renderProjectWorkspaceClaimSafeCreativeBriefSummaryPanel",
            "renderProjectWorkspaceClaimSafeMessagePillarsPanel",
            "renderProjectWorkspaceCreativeClaimUsageMapPanel",
            "renderProjectWorkspaceClaimSafeSurfaceSafetyCardsPanel",
            "renderProjectWorkspaceClaimSafeRewriteEvidenceQualityAuditSafetyPanel",
            "copyProjectWorkspaceClaimSafeBriefSummary",
            "copyProjectWorkspaceApprovedMessagePillars",
            "copyProjectWorkspaceRestrictedMessagePillars",
            "copyProjectWorkspaceBlockedMessagePillars",
            "copyProjectWorkspaceCreativeClaimUsageMap",
            "copyProjectWorkspaceHookSafetyCards",
            "copyProjectWorkspaceScriptSafetyCards",
            "copyProjectWorkspaceCtaSafetyCards",
            "copyProjectWorkspaceVideoPromptSafetyCards",
            "copyProjectWorkspaceCreativeBriefRewriteGuidance",
            "copyProjectWorkspaceEvidenceBackingMap",
            "copyProjectWorkspaceFullClaimSafeCreativeBriefPack",
            "claim_safe_creative_brief_pack: projectWorkspaceExportClaimSafeCreativeBriefSnapshot(workspace)",
            "Claim-Safe Creative Brief",
            "Claim-Safe Brief Summary",
            "Approved Message Pillars",
            "Restricted Message Pillars",
            "Blocked Message Pillars",
            "Creative Claim Usage Map",
            "Hook Safety Cards",
            "Script Safety Cards",
            "CTA Safety Cards",
            "Video Prompt Safety Cards",
            "Creative Brief Rewrite Guidance",
            "Evidence Backing Map",
            "Audit Preview",
            "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for field in [
            "pack.claim_safe_brief_summary",
            "pack.approved_message_pillars",
            "pack.restricted_message_pillars",
            "pack.blocked_message_pillars",
            "pack.creative_claim_usage_map",
            "pack.hook_safety_cards",
            "pack.script_safety_cards",
            "pack.cta_safety_cards",
            "pack.video_prompt_safety_cards",
            "pack.creative_brief_rewrite_guidance",
            "pack.evidence_backing_map",
            "pack.claim_safe_brief_quality_checks",
            "pack.audit_preview",
            "pack.safety_boundaries",
            "summary.mode",
            "summary.approved_pillar_count",
            "summary.restricted_pillar_count",
            "summary.blocked_pillar_count",
            "summary.recommended_operator_action",
            "summary.real_policy_check_allowed",
            "summary.real_execution_allowed",
            "pillar.pillar_id",
            "pillar.pillar_text",
            "pillar.blocked_text",
            "pillar.source_claim_ids",
            "pillar.support_status",
            "pillar.supporting_quote_ids",
            "pillar.allowed_surfaces",
            "pillar.safe_usage_note",
            "pillar.restriction_reason",
            "pillar.required_qualifiers",
            "pillar.operator_review_required",
            "pillar.allowed_internal_use",
            "pillar.disallowed_public_use",
            "pillar.recommended_safe_rewrite",
            "pillar.blocked_reason",
            "pillar.missing_evidence_refs",
            "pillar.do_not_claim_refs",
            "pillar.recommended_safe_alternative",
            "usage.usage_id",
            "usage.creative_surface",
            "usage.candidate_copy",
            "usage.claim_risk_level",
            "usage.support_status",
            "usage.real_policy_check_allowed",
            "usage.real_execution_allowed",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, html)
        previous = html.index("renderProjectWorkspaceClaimPlatformDoNotClaimQualityAuditSafetyPanel(workspace)")
        summary = html.index("renderProjectWorkspaceClaimSafeCreativeBriefSummaryPanel(workspace)")
        pillars = html.index("renderProjectWorkspaceClaimSafeMessagePillarsPanel(workspace)")
        usage = html.index("renderProjectWorkspaceCreativeClaimUsageMapPanel(workspace)")
        safety_cards = html.index("renderProjectWorkspaceClaimSafeSurfaceSafetyCardsPanel(workspace)")
        audit = html.index("renderProjectWorkspaceClaimSafeRewriteEvidenceQualityAuditSafetyPanel(workspace)")
        core = html.index("renderProjectWorkspaceCreativeCoreFlowStrip(workspace)")
        self.assertLess(previous, summary)
        self.assertLess(summary, pillars)
        self.assertLess(pillars, usage)
        self.assertLess(usage, safety_cards)
        self.assertLess(safety_cards, audit)
        self.assertLess(audit, core)

    def test_workspace_claim_safe_creative_brief_has_bilingual_guard_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "claimSafeCreativeBriefPackTitle",
            "claimSafeCreativeBriefSummaryTitle",
            "claimSafeCreativeBriefApprovedTitle",
            "claimSafeCreativeBriefRestrictedTitle",
            "claimSafeCreativeBriefBlockedTitle",
            "claimSafeCreativeBriefUsageMapTitle",
            "claimSafeCreativeBriefHookSafetyTitle",
            "claimSafeCreativeBriefScriptSafetyTitle",
            "claimSafeCreativeBriefCtaSafetyTitle",
            "claimSafeCreativeBriefVideoPromptSafetyTitle",
            "claimSafeCreativeBriefRewriteTitle",
            "claimSafeCreativeBriefEvidenceTitle",
            "claimSafeCreativeBriefAuditTitle",
            "claimSafeCreativeBriefSafetyTitle",
            "claimSafeCreativeBriefCopySummary",
            "claimSafeCreativeBriefCopyApproved",
            "claimSafeCreativeBriefCopyRestricted",
            "claimSafeCreativeBriefCopyBlocked",
            "claimSafeCreativeBriefCopyUsageMap",
            "claimSafeCreativeBriefCopyHookSafety",
            "claimSafeCreativeBriefCopyScriptSafety",
            "claimSafeCreativeBriefCopyCtaSafety",
            "claimSafeCreativeBriefCopyVideoPromptSafety",
            "claimSafeCreativeBriefCopyRewrite",
            "claimSafeCreativeBriefCopyEvidence",
            "claimSafeCreativeBriefCopyFull",
            "claimSafeCreativeBriefCopied",
            "claimSafeCreativeBriefCopyFailed",
            "claimSafeCreativeBriefCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace claim-safe creative brief bundle", script)
            self.assertIn("project_workspace_claim_safe_creative_brief_marker", script)
        markdown = html[
            html.index("function projectWorkspaceClaimSafeCreativeBriefSummaryText"):
            html.index("async function copyProjectWorkspaceClaimSafeCreativeBriefText")
        ]
        for key in [
            "claimSafeCreativeBriefPackTitle",
            "claimSafeCreativeBriefSummaryTitle",
            "claimSafeCreativeBriefApprovedTitle",
            "claimSafeCreativeBriefRestrictedTitle",
            "claimSafeCreativeBriefBlockedTitle",
            "claimSafeCreativeBriefUsageMapTitle",
            "claimSafeCreativeBriefHookSafetyTitle",
            "claimSafeCreativeBriefScriptSafetyTitle",
            "claimSafeCreativeBriefCtaSafetyTitle",
            "claimSafeCreativeBriefVideoPromptSafetyTitle",
            "claimSafeCreativeBriefRewriteTitle",
            "claimSafeCreativeBriefEvidenceTitle",
            "claimSafeCreativeBriefAuditTitle",
            "claimSafeCreativeBriefSafetyTitle",
        ]:
            self.assertIn(key, markdown)
        section = html[
            html.index("const PROJECT_WORKSPACE_CLAIM_SAFE_CREATIVE_BRIEF_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", section)
        for safety_text in [
            "deterministic creative brief preview",
            "not real ad launch content",
            "not legal advice",
            "not a real policy API check",
            "not a compliance conclusion",
            "Blocked pillars cannot enter public creative copy.",
            "unsupported comparison",
            "absolute claim",
            "missing quote",
            "weak evidence treated as strong evidence",
            "guaranteed result",
            "medical-like / safety / performance overclaim",
            "does not generate real ad launch content",
            "call an LLM",
            "call providers",
            "scrape reviews",
            "read real logs",
            "history tables",
            "write databases",
            "Provider, LLM, external scraping, database persistence, real execution, and real policy check remain disabled.",
        ]:
            with self.subTest(safety_text=safety_text):
                self.assertIn(safety_text, html)
        self.assertNotIn("????", html)

    def test_workspace_claim_safe_creative_output_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace claim-safe creative output bundle",
            "project_workspace_claim_safe_creative_output_marker",
            "PROJECT_WORKSPACE_CLAIM_SAFE_CREATIVE_OUTPUT_MARKER",
            "latestProjectWorkspaceClaimSafeCreativeOutputPack",
            "claim_safe_creative_output_pack",
            "projectWorkspaceClaimSafeCreativeOutputPackFromWorkspace",
            "projectWorkspaceExportClaimSafeCreativeOutputSnapshot",
            "projectWorkspaceExportClaimSafeCreativeOutputMarkdown",
            "renderProjectWorkspaceClaimSafeCreativeOutputSummaryPanel",
            "renderProjectWorkspaceClaimSafeCopyCardsPanel",
            "renderProjectWorkspaceClaimSafeVideoShotPanel",
            "renderProjectWorkspaceClaimSafeBlockedTracePanel",
            "renderProjectWorkspaceClaimSafeRewriteQualityExportAuditSafetyPanel",
            "copyProjectWorkspaceClaimSafeOutputSummary",
            "copyProjectWorkspaceSafeHookCards",
            "copyProjectWorkspaceSafeScriptCards",
            "copyProjectWorkspaceSafeCtaCards",
            "copyProjectWorkspaceSafeCaptionCards",
            "copyProjectWorkspaceSafeVideoPromptCards",
            "copyProjectWorkspaceSafeShotListCards",
            "copyProjectWorkspaceBlockedOutputCards",
            "copyProjectWorkspaceOutputClaimTraceMap",
            "copyProjectWorkspaceOutputRewriteGuidance",
            "copyProjectWorkspaceFullClaimSafeCreativeOutputPack",
            "claim_safe_creative_output_pack: projectWorkspaceExportClaimSafeCreativeOutputSnapshot(workspace)",
            "Claim-Safe Creative Output Pack",
            "Claim-Safe Output Summary",
            "Safe Hook Cards",
            "Safe Script Cards",
            "Safe CTA Cards",
            "Safe Caption Cards",
            "Safe Video Prompt Cards",
            "Safe Shot List Cards",
            "Blocked Output Cards",
            "Output Claim Trace Map",
            "Output Rewrite Guidance",
            "Export Preview Manifest",
            "Audit Preview",
            "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for field in [
            "pack.claim_safe_output_summary",
            "pack.safe_hook_cards",
            "pack.safe_script_cards",
            "pack.safe_cta_cards",
            "pack.safe_caption_cards",
            "pack.safe_video_prompt_cards",
            "pack.safe_shot_list_cards",
            "pack.blocked_output_cards",
            "pack.output_claim_trace_map",
            "pack.output_rewrite_guidance",
            "pack.output_quality_checks",
            "pack.export_preview_manifest",
            "pack.audit_preview",
            "pack.safety_boundaries",
            "summary.mode",
            "summary.safe_hook_count",
            "summary.safe_script_count",
            "summary.safe_cta_count",
            "summary.safe_caption_count",
            "summary.safe_video_prompt_count",
            "summary.safe_shot_list_count",
            "summary.blocked_output_count",
            "summary.recommended_operator_action",
            "summary.real_provider_allowed",
            "summary.real_policy_check_allowed",
            "summary.real_execution_allowed",
            "card.hook_id",
            "card.hook_text",
            "card.script_id",
            "card.script_title",
            "card.script_lines",
            "card.cta_text",
            "card.caption_text",
            "card.video_prompt_id",
            "card.prompt_text",
            "card.visual_direction",
            "card.disallowed_visual_claims",
            "card.shot_id",
            "card.shot_description",
            "card.source_pillar_ids",
            "card.source_claim_ids",
            "card.supporting_quote_ids",
            "card.claim_risk_level",
            "card.support_status",
            "card.allowed_usage",
            "card.restricted_usage",
            "card.disallowed_usage",
            "card.safe_usage_note",
            "card.blocked_terms",
            "card.operator_review_required",
            "card.real_provider_allowed",
            "card.real_policy_check_allowed",
            "card.real_execution_allowed",
            "card.blocked_output_id",
            "card.blocked_surface",
            "card.blocked_text",
            "card.blocked_reason",
            "card.missing_evidence_refs",
            "card.do_not_claim_refs",
            "card.recommended_safe_alternative",
            "trace.output_surface",
            "trace.source_claim_ids",
            "trace.supporting_quote_ids",
            "trace.evidence_quality",
            "trace.claim_risk_level",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, html)
        previous = html.index("renderProjectWorkspaceClaimSafeRewriteEvidenceQualityAuditSafetyPanel(workspace)")
        summary = html.index("renderProjectWorkspaceClaimSafeCreativeOutputSummaryPanel(workspace)")
        copy_cards = html.index("renderProjectWorkspaceClaimSafeCopyCardsPanel(workspace)")
        video_shot = html.index("renderProjectWorkspaceClaimSafeVideoShotPanel(workspace)")
        blocked_trace = html.index("renderProjectWorkspaceClaimSafeBlockedTracePanel(workspace)")
        safety = html.index("renderProjectWorkspaceClaimSafeRewriteQualityExportAuditSafetyPanel(workspace)")
        core = html.index("renderProjectWorkspaceCreativeCoreFlowStrip(workspace)")
        self.assertLess(previous, summary)
        self.assertLess(summary, copy_cards)
        self.assertLess(copy_cards, video_shot)
        self.assertLess(video_shot, blocked_trace)
        self.assertLess(blocked_trace, safety)
        self.assertLess(safety, core)

    def test_workspace_claim_safe_creative_output_has_bilingual_guard_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "claimSafeCreativeOutputPackTitle",
            "claimSafeCreativeOutputSummaryTitle",
            "claimSafeCreativeOutputHookTitle",
            "claimSafeCreativeOutputScriptTitle",
            "claimSafeCreativeOutputCtaTitle",
            "claimSafeCreativeOutputCaptionTitle",
            "claimSafeCreativeOutputVideoPromptTitle",
            "claimSafeCreativeOutputShotListTitle",
            "claimSafeCreativeOutputBlockedTitle",
            "claimSafeCreativeOutputTraceTitle",
            "claimSafeCreativeOutputRewriteTitle",
            "claimSafeCreativeOutputExportTitle",
            "claimSafeCreativeOutputAuditTitle",
            "claimSafeCreativeOutputSafetyTitle",
            "claimSafeCreativeOutputCopySummary",
            "claimSafeCreativeOutputCopyHooks",
            "claimSafeCreativeOutputCopyScripts",
            "claimSafeCreativeOutputCopyCtas",
            "claimSafeCreativeOutputCopyCaptions",
            "claimSafeCreativeOutputCopyVideoPrompts",
            "claimSafeCreativeOutputCopyShotList",
            "claimSafeCreativeOutputCopyBlocked",
            "claimSafeCreativeOutputCopyTrace",
            "claimSafeCreativeOutputCopyRewrite",
            "claimSafeCreativeOutputCopyFull",
            "claimSafeCreativeOutputCopied",
            "claimSafeCreativeOutputCopyFailed",
            "claimSafeCreativeOutputCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace claim-safe creative output bundle", script)
            self.assertIn("project_workspace_claim_safe_creative_output_marker", script)
        markdown = html[
            html.index("function projectWorkspaceClaimSafeCreativeOutputSummaryText"):
            html.index("async function copyProjectWorkspaceClaimSafeCreativeOutputText")
        ]
        for key in [
            "claimSafeCreativeOutputPackTitle",
            "claimSafeCreativeOutputSummaryTitle",
            "claimSafeCreativeOutputHookTitle",
            "claimSafeCreativeOutputScriptTitle",
            "claimSafeCreativeOutputCtaTitle",
            "claimSafeCreativeOutputCaptionTitle",
            "claimSafeCreativeOutputVideoPromptTitle",
            "claimSafeCreativeOutputShotListTitle",
            "claimSafeCreativeOutputBlockedTitle",
            "claimSafeCreativeOutputTraceTitle",
            "claimSafeCreativeOutputRewriteTitle",
            "claimSafeCreativeOutputExportTitle",
            "claimSafeCreativeOutputAuditTitle",
            "claimSafeCreativeOutputSafetyTitle",
        ]:
            self.assertIn(key, markdown)
        section = html[
            html.index("const PROJECT_WORKSPACE_CLAIM_SAFE_CREATIVE_OUTPUT_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", section)
        for safety_text in [
            "deterministic creative output preview",
            "not real ad launch content",
            "does not generate real ad launch content",
            "does not generate a real video",
            "does not upload or download media",
            "does not call an LLM",
            "does not call a real provider",
            "does not call providers",
            "does not scrape reviews",
            "does not read real logs",
            "history tables",
            "does not write databases",
            "not legal advice",
            "not a real policy API check",
            "not a compliance conclusion",
            "claim-safe copy preview cards only",
            "not real launched ads",
            "Blocked outputs cannot enter public creative copy or video prompt.",
            "does not upload files or write databases",
            "Audit preview is display-only and does not write databases.",
            "Provider, LLM, media, external scraping, database persistence, real execution, and real policy check remain disabled.",
        ]:
            with self.subTest(safety_text=safety_text):
                self.assertIn(safety_text, html)
        self.assertNotIn("????", html)

    def test_workspace_claim_safe_platform_delivery_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace claim-safe platform delivery bundle",
            "project_workspace_claim_safe_platform_delivery_marker",
            "PROJECT_WORKSPACE_CLAIM_SAFE_PLATFORM_DELIVERY_MARKER",
            "latestProjectWorkspaceClaimSafePlatformDeliveryPack",
            "claim_safe_platform_delivery_pack",
            "projectWorkspaceClaimSafePlatformDeliveryPackFromWorkspace",
            "projectWorkspaceExportClaimSafePlatformDeliverySnapshot",
            "projectWorkspaceExportClaimSafePlatformDeliveryMarkdown",
            "renderProjectWorkspaceClaimSafePlatformDeliverySummaryPanel",
            "renderProjectWorkspaceClaimSafePlatformDeliveryCardsPanel",
            "renderProjectWorkspaceClaimSafePlatformChannelPanel",
            "renderProjectWorkspaceClaimSafePlatformAssetClaimBlockerPanel",
            "renderProjectWorkspaceClaimSafePlatformReadinessExportAuditSafetyPanel",
            "copyProjectWorkspacePlatformDeliverySummary",
            "copyProjectWorkspacePlatformDeliveryCards",
            "copyProjectWorkspaceChannelCopyCards",
            "copyProjectWorkspaceChannelVideoPromptCards",
            "copyProjectWorkspaceAssetRequirementCards",
            "copyProjectWorkspaceChannelClaimSafetyMap",
            "copyProjectWorkspaceDeliveryBlockerCards",
            "copyProjectWorkspaceDeliveryReadinessChecks",
            "copyProjectWorkspaceOperatorHandoffNotes",
            "copyProjectWorkspaceFullClaimSafePlatformDeliveryPack",
            "claim_safe_platform_delivery_pack: projectWorkspaceExportClaimSafePlatformDeliverySnapshot(workspace)",
            "Claim-Safe Platform Delivery Pack",
            "Platform Delivery Summary",
            "Platform Delivery Cards",
            "Channel Copy Cards",
            "Channel Video Prompt Cards",
            "Channel Asset Requirement Cards",
            "Channel Claim Safety Map",
            "Delivery Blocker Cards",
            "Delivery Readiness Checks",
            "Export Bundle Manifest",
            "Operator Handoff Notes",
            "Audit Preview",
            "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for field in [
            "platform_delivery_summary",
            "platform_delivery_cards",
            "channel_copy_cards",
            "channel_video_prompt_cards",
            "channel_asset_requirement_cards",
            "channel_claim_safety_map",
            "delivery_blocker_cards",
            "delivery_readiness_checks",
            "export_bundle_manifest",
            "operator_handoff_notes",
            "audit_preview",
            "safety_boundaries",
            "card.platform_delivery_id",
            "card.platform_label",
            "card.delivery_surface",
            "card.recommended_output_refs",
            "card.recommended_hook_refs",
            "card.recommended_script_refs",
            "card.recommended_cta_refs",
            "card.recommended_video_prompt_refs",
            "card.format_notes",
            "card.claim_safety_status",
            "card.readiness_status",
            "card.operator_review_required",
            "card.blocked_reason",
            "card.real_platform_upload_allowed",
            "card.real_policy_check_allowed",
            "card.real_execution_allowed",
            "card.copy_card_id",
            "card.copy_type",
            "card.copy_text",
            "card.source_output_refs",
            "card.source_claim_ids",
            "card.supporting_quote_ids",
            "card.claim_risk_level",
            "card.support_status",
            "card.allowed_usage",
            "card.restricted_usage",
            "card.disallowed_usage",
            "card.video_delivery_id",
            "card.prompt_text",
            "card.visual_direction",
            "card.shot_refs",
            "card.disallowed_visual_claims",
            "card.real_provider_allowed",
            "card.real_media_upload_allowed",
            "row.evidence_quality",
            "row.do_not_claim_refs",
            "card.blocker_type",
            "card.blocked_text",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, html)
        for surface in [
            "tiktok_short_video",
            "instagram_reel",
            "youtube_short",
            "amazon_listing_video",
            "product_page_asset",
            "ad_copy_snippet",
        ]:
            with self.subTest(surface=surface):
                self.assertIn(surface, html)
        previous = html.index("renderProjectWorkspaceClaimSafeRewriteQualityExportAuditSafetyPanel(workspace)")
        summary = html.index("renderProjectWorkspaceClaimSafePlatformDeliverySummaryPanel(workspace)")
        cards = html.index("renderProjectWorkspaceClaimSafePlatformDeliveryCardsPanel(workspace)")
        channel = html.index("renderProjectWorkspaceClaimSafePlatformChannelPanel(workspace)")
        blockers = html.index("renderProjectWorkspaceClaimSafePlatformAssetClaimBlockerPanel(workspace)")
        safety = html.index("renderProjectWorkspaceClaimSafePlatformReadinessExportAuditSafetyPanel(workspace)")
        core = html.index("renderProjectWorkspaceCreativeCoreFlowStrip(workspace)")
        self.assertLess(previous, summary)
        self.assertLess(summary, cards)
        self.assertLess(cards, channel)
        self.assertLess(channel, blockers)
        self.assertLess(blockers, safety)
        self.assertLess(safety, core)

    def test_workspace_claim_safe_platform_delivery_has_bilingual_guard_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "claimSafePlatformDeliveryPackTitle",
            "claimSafePlatformDeliverySummaryTitle",
            "claimSafePlatformDeliveryCardsTitle",
            "claimSafePlatformDeliveryChannelTitle",
            "claimSafePlatformDeliveryCopyTitle",
            "claimSafePlatformDeliveryVideoTitle",
            "claimSafePlatformDeliveryAssetTitle",
            "claimSafePlatformDeliveryClaimMapTitle",
            "claimSafePlatformDeliveryBlockerTitle",
            "claimSafePlatformDeliveryReadinessTitle",
            "claimSafePlatformDeliveryExportTitle",
            "claimSafePlatformDeliveryHandoffTitle",
            "claimSafePlatformDeliveryAuditTitle",
            "claimSafePlatformDeliverySafetyTitle",
            "claimSafePlatformDeliveryCopySummary",
            "claimSafePlatformDeliveryCopyCards",
            "claimSafePlatformDeliveryCopyChannelCopy",
            "claimSafePlatformDeliveryCopyVideo",
            "claimSafePlatformDeliveryCopyAssets",
            "claimSafePlatformDeliveryCopyClaimMap",
            "claimSafePlatformDeliveryCopyBlockers",
            "claimSafePlatformDeliveryCopyReadiness",
            "claimSafePlatformDeliveryCopyHandoff",
            "claimSafePlatformDeliveryCopyFull",
            "claimSafePlatformDeliveryCopied",
            "claimSafePlatformDeliveryCopyFailed",
            "claimSafePlatformDeliveryCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace claim-safe platform delivery bundle", script)
            self.assertIn("project_workspace_claim_safe_platform_delivery_marker", script)
        markdown = html[
            html.index("function projectWorkspaceClaimSafePlatformDeliverySummaryText"):
            html.index("async function copyProjectWorkspaceClaimSafePlatformDeliveryText")
        ]
        for key in [
            "claimSafePlatformDeliveryPackTitle",
            "claimSafePlatformDeliverySummaryTitle",
            "claimSafePlatformDeliveryCardsTitle",
            "claimSafePlatformDeliveryCopyTitle",
            "claimSafePlatformDeliveryVideoTitle",
            "claimSafePlatformDeliveryAssetTitle",
            "claimSafePlatformDeliveryClaimMapTitle",
            "claimSafePlatformDeliveryBlockerTitle",
            "claimSafePlatformDeliveryReadinessTitle",
            "claimSafePlatformDeliveryExportTitle",
            "claimSafePlatformDeliveryHandoffTitle",
            "claimSafePlatformDeliveryAuditTitle",
            "claimSafePlatformDeliverySafetyTitle",
        ]:
            self.assertIn(key, markdown)
        section = html[
            html.index("const PROJECT_WORKSPACE_CLAIM_SAFE_PLATFORM_DELIVERY_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", section)
        for safety_text in [
            "deterministic platform delivery preview",
            "not a real publication",
            "not a real platform policy API check",
            "does not upload files",
            "does not call a provider",
            "not legal advice",
            "not a real policy API check",
            "not a real platform compliance conclusion",
            "not a real platform policy judgment",
            "does not upload or download files",
            "does not upload media",
            "does not call providers",
            "does not call an LLM",
            "does not scrape reviews",
            "does not read real logs",
            "history tables",
            "does not write databases",
            "does not create approvals or operator tasks",
            "does not execute paid operations",
            "generic delivery previews only",
            "not real platform policy judgments",
            "do not generate real video",
            "publish to a platform",
            "Delivery blockers cannot be delivered to public channels",
            "does not upload files or write databases",
            "do not create real operator tasks",
            "Audit preview is display-only and does not write databases.",
            "Provider, LLM, media, external scraping, database persistence, real execution, real policy check, and platform upload remain disabled.",
        ]:
            with self.subTest(safety_text=safety_text):
                self.assertIn(safety_text, html)
        self.assertNotIn("????", html)

    def test_workspace_claim_safe_delivery_qa_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace claim-safe delivery QA bundle",
            "project_workspace_claim_safe_delivery_qa_marker",
            "PROJECT_WORKSPACE_CLAIM_SAFE_DELIVERY_QA_MARKER",
            "latestProjectWorkspaceClaimSafeDeliveryQaPack",
            "claim_safe_delivery_qa_pack",
            "projectWorkspaceClaimSafeDeliveryQaPackFromWorkspace",
            "projectWorkspaceExportClaimSafeDeliveryQaSnapshot",
            "projectWorkspaceExportClaimSafeDeliveryQaMarkdown",
            "renderProjectWorkspaceClaimSafeDeliveryQaSummaryPanel",
            "renderProjectWorkspaceClaimSafeDeliveryQaSurfaceCopyPanel",
            "renderProjectWorkspaceClaimSafeDeliveryQaVideoClaimPanel",
            "renderProjectWorkspaceClaimSafeDeliveryQaExportBlockerReviewPanel",
            "renderProjectWorkspaceClaimSafeDeliveryQaScoreQualityAuditSafetyPanel",
            "copyProjectWorkspaceDeliveryQaSummary",
            "copyProjectWorkspaceSurfaceReadinessCards",
            "copyProjectWorkspaceCopyCompletenessCards",
            "copyProjectWorkspaceVideoPromptReadinessCards",
            "copyProjectWorkspaceClaimSafetyVerificationCards",
            "copyProjectWorkspaceExportReadinessCards",
            "copyProjectWorkspaceUnresolvedDeliveryBlockers",
            "copyProjectWorkspaceOperatorReviewRecommendations",
            "copyProjectWorkspaceDeliveryQaScoreBreakdown",
            "copyProjectWorkspaceFullClaimSafeDeliveryQaPack",
            "claim_safe_delivery_qa_pack: projectWorkspaceExportClaimSafeDeliveryQaSnapshot(workspace)",
            "Claim-Safe Delivery QA / Export Readiness",
            "Delivery QA Summary",
            "Surface Readiness Cards",
            "Copy Completeness Cards",
            "Video Prompt Readiness Cards",
            "Claim Safety Verification Cards",
            "Export Readiness Cards",
            "Unresolved Delivery Blocker Cards",
            "Operator Review Recommendations",
            "Delivery QA Score Breakdown",
            "Delivery QA Quality Checks",
            "Audit Preview",
            "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for field in [
            "delivery_qa_summary",
            "surface_readiness_cards",
            "copy_completeness_cards",
            "video_prompt_readiness_cards",
            "claim_safety_verification_cards",
            "export_readiness_cards",
            "unresolved_delivery_blocker_cards",
            "operator_review_recommendations",
            "delivery_qa_score_breakdown",
            "delivery_qa_quality_checks",
            "card.surface_qa_id",
            "card.delivery_surface",
            "card.platform_label",
            "card.source_delivery_refs",
            "card.required_copy_fields",
            "card.present_copy_fields",
            "card.missing_copy_fields",
            "card.required_asset_fields",
            "card.present_asset_fields",
            "card.missing_asset_fields",
            "card.claim_safety_status",
            "card.export_readiness_status",
            "card.copy_qa_id",
            "card.copy_type",
            "card.copy_text",
            "card.completeness_status",
            "card.copy_quality_note",
            "card.operator_review_required",
            "card.blocked_reason",
            "card.real_platform_upload_allowed",
            "card.real_policy_check_allowed",
            "card.real_execution_allowed",
            "card.video_prompt_qa_id",
            "card.prompt_text",
            "card.visual_direction",
            "card.shot_refs",
            "card.source_video_prompt_refs",
            "card.source_claim_ids",
            "card.supporting_quote_ids",
            "card.disallowed_visual_claims",
            "card.media_requirement_status",
            "card.provider_readiness_status",
            "card.real_provider_allowed",
            "card.real_media_upload_allowed",
            "card.verification_id",
            "card.checked_text",
            "card.support_status",
            "card.claim_risk_level",
            "card.do_not_claim_refs",
            "card.evidence_quality_refs",
            "card.verification_status",
            "card.recommended_safe_fix",
            "card.blocker_type",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, html)
        for blocker in [
            "ready_for_preview_export",
            "needs_operator_review",
            "blocked",
            "unsupported claim",
            "blocked output",
            "missing quote",
            "missing required field",
            "provider disabled",
            "media upload disabled",
            "policy check disabled",
            "platform upload disabled",
        ]:
            with self.subTest(blocker=blocker):
                self.assertIn(blocker, html)
        previous = html.index("renderProjectWorkspaceClaimSafePlatformReadinessExportAuditSafetyPanel(workspace)")
        summary = html.index("renderProjectWorkspaceClaimSafeDeliveryQaSummaryPanel(workspace)")
        surface = html.index("renderProjectWorkspaceClaimSafeDeliveryQaSurfaceCopyPanel(workspace)")
        video = html.index("renderProjectWorkspaceClaimSafeDeliveryQaVideoClaimPanel(workspace)")
        export = html.index("renderProjectWorkspaceClaimSafeDeliveryQaExportBlockerReviewPanel(workspace)")
        safety = html.index("renderProjectWorkspaceClaimSafeDeliveryQaScoreQualityAuditSafetyPanel(workspace)")
        core = html.index("renderProjectWorkspaceCreativeCoreFlowStrip(workspace)")
        self.assertLess(previous, summary)
        self.assertLess(summary, surface)
        self.assertLess(surface, video)
        self.assertLess(video, export)
        self.assertLess(export, safety)
        self.assertLess(safety, core)

    def test_workspace_claim_safe_delivery_qa_has_bilingual_guard_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "claimSafeDeliveryQaPackTitle",
            "claimSafeDeliveryQaSummaryTitle",
            "claimSafeDeliveryQaSurfaceTitle",
            "claimSafeDeliveryQaCopyTitle",
            "claimSafeDeliveryQaVideoTitle",
            "claimSafeDeliveryQaVerificationTitle",
            "claimSafeDeliveryQaExportTitle",
            "claimSafeDeliveryQaBlockerTitle",
            "claimSafeDeliveryQaReviewTitle",
            "claimSafeDeliveryQaScoreTitle",
            "claimSafeDeliveryQaQualityTitle",
            "claimSafeDeliveryQaAuditTitle",
            "claimSafeDeliveryQaSafetyTitle",
            "claimSafeDeliveryQaCopySummary",
            "claimSafeDeliveryQaCopySurfaces",
            "claimSafeDeliveryQaCopyCopyCompleteness",
            "claimSafeDeliveryQaCopyVideo",
            "claimSafeDeliveryQaCopyVerification",
            "claimSafeDeliveryQaCopyExport",
            "claimSafeDeliveryQaCopyBlockers",
            "claimSafeDeliveryQaCopyReview",
            "claimSafeDeliveryQaCopyScore",
            "claimSafeDeliveryQaCopyFull",
            "claimSafeDeliveryQaCopied",
            "claimSafeDeliveryQaCopyFailed",
            "claimSafeDeliveryQaCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace claim-safe delivery QA bundle", script)
            self.assertIn("project_workspace_claim_safe_delivery_qa_marker", script)
        markdown = html[
            html.index("function projectWorkspaceClaimSafeDeliveryQaSummaryText"):
            html.index("async function copyProjectWorkspaceClaimSafeDeliveryQaText")
        ]
        for key in [
            "claimSafeDeliveryQaPackTitle",
            "claimSafeDeliveryQaSummaryTitle",
            "claimSafeDeliveryQaSurfaceTitle",
            "claimSafeDeliveryQaCopyTitle",
            "claimSafeDeliveryQaVideoTitle",
            "claimSafeDeliveryQaVerificationTitle",
            "claimSafeDeliveryQaExportTitle",
            "claimSafeDeliveryQaBlockerTitle",
            "claimSafeDeliveryQaReviewTitle",
            "claimSafeDeliveryQaScoreTitle",
            "claimSafeDeliveryQaQualityTitle",
            "claimSafeDeliveryQaAuditTitle",
            "claimSafeDeliveryQaSafetyTitle",
        ]:
            self.assertIn(key, markdown)
        section = html[
            html.index("const PROJECT_WORKSPACE_CLAIM_SAFE_DELIVERY_QA_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", section)
        for safety_text in [
            "deterministic delivery QA preview",
            "not a real platform review",
            "not a real platform audit",
            "not real publishing",
            "not a real policy check",
            "does not call an LLM",
            "does not call providers",
            "does not upload files",
            "does not upload or download media",
            "does not scrape reviews",
            "does not read real logs",
            "history tables",
            "does not write databases",
            "does not create real operator tasks",
            "not legal advice",
            "not a real policy API check",
            "not a real platform compliance conclusion",
            "not a real platform pass rate",
            "preview export",
            "There is no real provider, no media upload or download, and no real policy API.",
            "Operator review recommendations are manual guidance only and do not create real operator tasks.",
            "Audit preview is display-only and does not write databases.",
            "Provider, LLM, media, external scraping, database persistence, real execution, real policy check, and platform upload remain disabled.",
        ]:
            with self.subTest(safety_text=safety_text):
                self.assertIn(safety_text, html)
        self.assertNotIn("????", html)

    def test_workspace_secret_environment_gate_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace secret environment gate bundle",
            "PROJECT_WORKSPACE_SECRET_ENVIRONMENT_GATE_MARKER",
            "latestProjectWorkspaceSecretEnvironmentGatePack",
            "projectWorkspaceSecretEnvironmentGatePackFromWorkspace",
            "projectWorkspaceExportSecretEnvironmentGateSnapshot",
            "projectWorkspaceExportSecretEnvironmentGateMarkdown",
            "renderProjectWorkspaceSecretEnvironmentGateSummaryPanel",
            "renderProjectWorkspaceSecretRequirementCardsPanel",
            "renderProjectWorkspaceEnvironmentGatePolicyPanel",
            "renderProjectWorkspaceMissingEnvironmentBlockedSecretDependencyPanel",
            "renderProjectWorkspaceEnvironmentRiskQualityAuditSafetyPanel",
            "copyProjectWorkspaceSecretEnvironmentGateSummary",
            "copyProjectWorkspaceSecretRequirementCards",
            "copyProjectWorkspaceEnvironmentGateChecks",
            "copyProjectWorkspaceSecretAccessPolicyCards",
            "copyProjectWorkspaceMissingEnvironmentRequirements",
            "copyProjectWorkspaceBlockedSecretOperations",
            "copyProjectWorkspaceProviderSecretDependencyMap",
            "copyProjectWorkspaceEnvironmentRiskRegister",
            "copyProjectWorkspaceFullSecretEnvironmentGatePack",
            "workspace_secret_environment_gate_pack: projectWorkspaceExportSecretEnvironmentGateSnapshot(workspace)",
            "Workspace Secret Requirement / Environment Gate Preview",
            "Secret Environment Gate Summary",
            "Secret Requirement Cards",
            "Environment Gate Checks",
            "Secret Access Policy Cards",
            "Missing Environment Requirements",
            "Blocked Secret Operations",
            "Provider Secret Dependency Map",
            "Environment Risk Register",
            "Audit Preview",
            "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for provider_type in [
            "llm_text_generation", "video_generation_provider",
            "image_generation_provider", "media_storage_provider",
            "external_scraping_provider", "translation_provider",
            "analytics_or_tracking_provider", "database_persistence_provider",
            "approval_or_ticket_provider", "rollback_restore_provider",
        ]:
            with self.subTest(provider_type=provider_type):
                self.assertIn(provider_type, html)
        for field in [
            "pack.secret_environment_gate_summary",
            "pack.secret_requirement_cards",
            "pack.environment_gate_checks",
            "pack.secret_access_policy_cards",
            "pack.missing_environment_requirements",
            "pack.blocked_secret_operations",
            "pack.provider_secret_dependency_map",
            "pack.environment_risk_register",
            "pack.secret_gate_quality_checks",
            "pack.audit_preview",
            "pack.safety_boundaries",
            "summary.mode",
            "summary.secret_requirement_card_count",
            "summary.environment_gate_check_count",
            "summary.secret_value_read_allowed",
            "summary.secret_validation_allowed",
            "summary.real_invocation_allowed",
            "summary.real_execution_allowed",
            "card.secret_requirement_id",
            "card.provider_id",
            "card.provider_type",
            "card.source_capability",
            "card.secret_name_preview",
            "card.secret_purpose",
            "card.required_for_modes",
            "card.current_secret_status",
            "card.secret_value_read_allowed",
            "card.secret_validation_allowed",
            "card.real_invocation_allowed",
            "card.real_execution_allowed",
            "card.blocked_by",
            "card.recommended_operator_action",
            "card.risk_note",
            "gate.gate_id",
            "gate.gate_name",
            "gate.gate_status",
            "gate.required_environment_refs",
            "gate.missing_environment_refs",
            "gate.blocked_reason",
            "gate.next_preview_step",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, html)
        previous = html.index("${renderProjectWorkspaceReadinessRiskQualityAuditSafetyPanel(workspace)}")
        summary = html.index("${renderProjectWorkspaceSecretEnvironmentGateSummaryPanel(workspace)}")
        safety = html.index("${renderProjectWorkspaceEnvironmentRiskQualityAuditSafetyPanel(workspace)}")
        core = html.index("${renderProjectWorkspaceCreativeCoreFlowStrip(workspace)}")
        self.assertLess(previous, summary)
        self.assertLess(summary, safety)
        self.assertLess(safety, core)

    def test_workspace_secret_environment_gate_has_bilingual_guard_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "secretEnvironmentGatePackTitle",
            "secretEnvironmentGateSummaryTitle",
            "secretEnvironmentGateCardsTitle",
            "secretEnvironmentGateChecksTitle",
            "secretEnvironmentGatePolicyTitle",
            "secretEnvironmentGateMissingTitle",
            "secretEnvironmentGateBlockedTitle",
            "secretEnvironmentGateDependencyTitle",
            "secretEnvironmentGateRiskTitle",
            "secretEnvironmentGateAuditTitle",
            "secretEnvironmentGateSafetyTitle",
            "secretEnvironmentGateCopySummary",
            "secretEnvironmentGateCopyCards",
            "secretEnvironmentGateCopyChecks",
            "secretEnvironmentGateCopyPolicy",
            "secretEnvironmentGateCopyMissing",
            "secretEnvironmentGateCopyBlocked",
            "secretEnvironmentGateCopyDependency",
            "secretEnvironmentGateCopyRisk",
            "secretEnvironmentGateCopyFull",
            "secretEnvironmentGateCopied",
            "secretEnvironmentGateCopyFailed",
            "secretEnvironmentGateCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn(
                "Project Workspace secret environment gate bundle",
                script,
            )
            self.assertIn(
                "project_workspace_secret_environment_gate_marker",
                script,
            )
        markdown = html[
            html.index("function projectWorkspaceSecretEnvironmentGateSummaryText"):
            html.index("async function copyProjectWorkspaceSecretEnvironmentGateText")
        ]
        for key in [
            "secretEnvironmentGatePackTitle",
            "secretEnvironmentGateSummaryTitle",
            "secretEnvironmentGateCardsTitle",
            "secretEnvironmentGateChecksTitle",
            "secretEnvironmentGatePolicyTitle",
            "secretEnvironmentGateMissingTitle",
            "secretEnvironmentGateBlockedTitle",
            "secretEnvironmentGateDependencyTitle",
            "secretEnvironmentGateRiskTitle",
            "secretEnvironmentGateAuditTitle",
            "secretEnvironmentGateSafetyTitle",
        ]:
            self.assertIn(key, markdown)
        section = html[
            html.index("const PROJECT_WORKSPACE_SECRET_ENVIRONMENT_GATE_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", section)
        for safety_text in [
            "secret/environment gate preview",
            "not a real secret scanner",
            "does not read",
            "validate",
            "export",
            "persist",
            "secret value",
            "Secret requirement cards show secret name previews",
            "read_secret",
            "validate_secret",
            "use_secret_for_call",
            "persist_secret",
            "export_secret",
            "provider API key",
            "billing/quota env",
            "media storage env",
            "approval token",
            "rollback token",
            "database env",
            "secret missing",
            "secret validation blocked",
            "billing/quota env missing",
            "media storage env missing",
            "rollback token blocked",
            "database env blocked",
            "external provider key missing",
            "Audit preview is not written to a database",
            "Real LLM",
            "provider",
            "image",
            "video",
            "media",
            "paid",
            "registry",
            "rollback",
            "external scraping",
            "database persistence",
            "real restore",
            "real execution",
            "secret read",
        ]:
            with self.subTest(safety_text=safety_text):
                self.assertIn(safety_text, html)
        self.assertNotIn("????", html)

    def test_creative_decision_pack_keeps_real_execution_disabled(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        creative_section = html[
            html.index("const PROJECT_WORKSPACE_CREATIVE_DECISION_PACK_MARKER"):
            html.index("function renderProjectWorkspaceProviderGovernanceGroup")
        ]
        self.assertIn("safety_boundaries: pack.safety_boundaries || {}", creative_section)
        self.assertIn("Real providers, media transfer, registry writes, restore, rollback, and paid actions remain disabled.", html)
        self.assertNotIn("fetch(", creative_section)

    def test_creative_feedback_runtime_core_flow_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace creative feedback runtime bundle",
            "PROJECT_WORKSPACE_CREATIVE_FEEDBACK_RUNTIME_MARKER",
            "renderProjectWorkspaceCreativeCoreFlowStrip",
            "renderProjectWorkspaceCreativeFeedbackRuntimePanel",
            "renderProjectWorkspaceCreativeRecommendedActionPanel",
            "copyProjectWorkspaceCreativeFeedbackSummary",
            "copyProjectWorkspaceCreativeFlowHints",
            "copyProjectWorkspaceConservativeScriptGuidance",
            "creative_feedback_runtime: pack.creative_feedback_runtime || {}",
            "Creative Feedback Runtime",
            "Core Creative Flow",
            "Recommended Next Step",
            "Evidence Gap Actions",
            "Safety Reminders",
            "creative_decision_pack: projectWorkspaceExportCreativeDecisionPackSnapshot(workspace)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)

    def test_creative_feedback_runtime_bilingual_copy_and_guard_markers_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "creativeFeedbackRuntimeTitle",
            "creativeCoreFlowTitle",
            "creativeFeedbackRecommendedActionTitle",
            "creativeFeedbackCopySummary",
            "creativeFeedbackCopyFlow",
            "creativeFeedbackCopyConservative",
            "creativeFeedbackSummaryCopied",
            "creativeFeedbackFlowCopied",
            "creativeFeedbackConservativeCopied",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace creative feedback runtime bundle", script)
            self.assertIn("project_workspace_creative_feedback_runtime_marker", script)
        self.assertNotIn("????", html)

    def test_workspace_provider_asset_contract_panels_copy_and_exports_exist(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        for marker in [
            "Project Workspace provider asset contract bundle",
            "PROJECT_WORKSPACE_PROVIDER_ASSET_CONTRACT_MARKER",
            "latestProjectWorkspaceProviderAssetContractPack",
            "projectWorkspaceProviderAssetContractPackFromWorkspace",
            "projectWorkspaceExportProviderAssetContractSnapshot",
            "projectWorkspaceExportProviderAssetContractMarkdown",
            "renderProjectWorkspaceProviderAssetContractSummaryPanel",
            "renderProjectWorkspaceProviderAssetContractCardsPanel",
            "renderProjectWorkspaceMediaManifestCardsPanel",
            "renderProjectWorkspaceAssetRequirementBoundaryPanel",
            "renderProjectWorkspaceAssetFailureQualityAuditSafetyPanel",
            "copyProjectWorkspaceProviderAssetContractSummary",
            "copyProjectWorkspaceProviderAssetContractCards",
            "copyProjectWorkspaceMediaManifestCards",
            "copyProjectWorkspaceInputAssetRequirements",
            "copyProjectWorkspaceOutputAssetRequirements",
            "copyProjectWorkspaceAssetValidationRules",
            "copyProjectWorkspaceStorageTransferBoundaries",
            "copyProjectWorkspaceAssetFailurePolicyMap",
            "copyProjectWorkspaceFullProviderAssetContractPack",
            "workspace_provider_asset_contract_pack: projectWorkspaceExportProviderAssetContractSnapshot(workspace)",
            "Workspace Provider Asset Contract / Media Manifest",
            "Asset Contract Summary",
            "Provider Asset Contract Cards",
            "Media Manifest Cards",
            "Input Asset Requirements",
            "Output Asset Requirements",
            "Asset Validation Rules",
            "Storage Transfer Boundaries",
            "Asset Failure Policy Map",
            "Audit Preview",
            "Safety Boundaries",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for provider_type in [
            "llm_text_generation", "video_generation_provider",
            "image_generation_provider", "media_storage_provider",
            "external_scraping_provider", "translation_provider",
            "analytics_or_tracking_provider", "database_persistence_provider",
            "approval_or_ticket_provider", "rollback_restore_provider",
        ]:
            with self.subTest(provider_type=provider_type):
                self.assertIn(provider_type, html)
        for field in [
            "pack.asset_contract_summary",
            "pack.provider_asset_contract_cards",
            "pack.media_manifest_cards",
            "pack.input_asset_requirements",
            "pack.output_asset_requirements",
            "pack.asset_validation_rules",
            "pack.storage_transfer_boundaries",
            "pack.asset_failure_policy_map",
            "pack.asset_quality_checks",
            "pack.audit_preview",
            "pack.safety_boundaries",
            "summary.mode",
            "summary.provider_asset_contract_card_count",
            "summary.media_manifest_card_count",
            "summary.media_upload_allowed",
            "summary.media_download_allowed",
            "summary.real_generation_allowed",
            "summary.real_invocation_allowed",
            "summary.real_execution_allowed",
            "card.asset_contract_id",
            "card.provider_id",
            "card.provider_type",
            "card.source_capability",
            "card.asset_role",
            "card.required_input_assets",
            "card.expected_output_assets",
            "card.allowed_asset_modes",
            "card.disallowed_asset_modes",
            "card.media_upload_allowed",
            "card.media_download_allowed",
            "card.real_generation_allowed",
            "card.real_invocation_allowed",
            "card.real_execution_allowed",
            "card.risk_note",
            "card.manifest_id",
            "card.asset_type",
            "card.asset_purpose",
            "card.source_pack",
            "card.mock_asset_ref",
            "card.storage_mode",
            "card.transfer_mode",
            "card.validation_status",
            "card.blocked_real_behavior_summary",
            "card.real_media_operation_allowed",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, html)
        previous = html.index("${renderProjectWorkspaceFailureActionQualityAuditSafetyPanel(workspace)}")
        summary = html.index("${renderProjectWorkspaceProviderAssetContractSummaryPanel(workspace)}")
        safety = html.index("${renderProjectWorkspaceAssetFailureQualityAuditSafetyPanel(workspace)}")
        core = html.index("${renderProjectWorkspaceCreativeCoreFlowStrip(workspace)}")
        self.assertLess(previous, summary)
        self.assertLess(summary, safety)
        self.assertLess(safety, core)

    def test_workspace_provider_asset_contract_has_bilingual_guard_and_safe_boundary(self):
        html = Path("static/index.html").read_text(encoding="utf-8")
        guard = Path("scripts/frontend_quality_guard.py").read_text(encoding="utf-8")
        smoke = Path("scripts/smoke_agent_graph_os_public.ps1").read_text(encoding="utf-8")
        for key in [
            "providerAssetContractPackTitle",
            "providerAssetContractSummaryTitle",
            "providerAssetContractCardsTitle",
            "providerAssetContractManifestTitle",
            "providerAssetContractInputTitle",
            "providerAssetContractOutputTitle",
            "providerAssetContractValidationTitle",
            "providerAssetContractStorageTitle",
            "providerAssetContractFailurePolicyTitle",
            "providerAssetContractQualityTitle",
            "providerAssetContractAuditTitle",
            "providerAssetContractSafetyTitle",
            "providerAssetContractCopySummary",
            "providerAssetContractCopyCards",
            "providerAssetContractCopyManifest",
            "providerAssetContractCopyInput",
            "providerAssetContractCopyOutput",
            "providerAssetContractCopyValidation",
            "providerAssetContractCopyStorage",
            "providerAssetContractCopyFailurePolicy",
            "providerAssetContractCopyFull",
            "providerAssetContractCopied",
            "providerAssetContractCopyFailed",
            "providerAssetContractCopyNoData",
        ]:
            with self.subTest(key=key):
                self.assertGreaterEqual(html.count(key), 3)
        for script in [guard, smoke]:
            self.assertIn("Project Workspace provider asset contract bundle", script)
            self.assertIn("project_workspace_provider_asset_contract_marker", script)
        markdown = html[
            html.index("function projectWorkspaceProviderAssetContractSummaryText"):
            html.index("async function copyProjectWorkspaceProviderAssetContractText")
        ]
        for key in [
            "providerAssetContractPackTitle",
            "providerAssetContractSummaryTitle",
            "providerAssetContractCardsTitle",
            "providerAssetContractManifestTitle",
            "providerAssetContractInputTitle",
            "providerAssetContractOutputTitle",
            "providerAssetContractValidationTitle",
            "providerAssetContractStorageTitle",
            "providerAssetContractFailurePolicyTitle",
            "providerAssetContractAuditTitle",
            "providerAssetContractSafetyTitle",
        ]:
            self.assertIn(key, markdown)
        section = html[
            html.index("const PROJECT_WORKSPACE_PROVIDER_ASSET_CONTRACT_MARKER"):
            html.index("function projectWorkspaceCampaignExportPackFromWorkspace")
        ]
        self.assertNotIn("fetch(", section)
        for safety_text in [
            "asset contract / media manifest preview",
            "not a real media pipeline",
            "does not invoke providers or generate media",
            "No media is uploaded, downloaded, generated, transferred, or stored",
            "does not read files",
            "write files",
            "write storage",
            "call external services",
            "write databases",
            "does not execute real retry, restore, rollback",
            "Real LLM",
            "provider",
            "image",
            "video",
            "media",
            "paid",
            "registry",
            "rollback",
            "external scraping",
            "database persistence",
            "real restore",
            "real execution",
        ]:
            with self.subTest(safety_text=safety_text):
                self.assertIn(safety_text, html)
        self.assertNotIn("????", html)
