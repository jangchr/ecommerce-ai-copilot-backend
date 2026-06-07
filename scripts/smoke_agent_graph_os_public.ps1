param(
    [string]$BaseUrl = "https://ecommerce-ai-copilot-backend.onrender.com"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$base = $BaseUrl.TrimEnd("/")
$checks = [ordered]@{}

function Add-Check {
    param([string]$Name, [bool]$Passed)
    $script:checks[$Name] = $Passed
    $tone = if ($Passed) { "Green" } else { "Red" }
    Write-Host ("{0}: {1}" -f $Name, $(if ($Passed) { "PASS" } else { "FAIL" })) -ForegroundColor $tone
}

function Invoke-CgJson {
    param(
        [string]$Method,
        [string]$Path,
        [hashtable]$Body
    )
    $params = @{
        Uri = "$base$Path"
        Method = $Method
        TimeoutSec = 180
    }
    if ($Body) {
        $params.ContentType = "application/json"
        $params.Body = $Body | ConvertTo-Json -Depth 40
    }
    return Invoke-RestMethod @params
}

Write-Host "CrossGrowth Agent Graph OS public smoke" -ForegroundColor Cyan
Write-Host "Base URL: $base"

$page = Invoke-WebRequest -Uri "$base/" -TimeoutSec 120
Add-Check "page_load" ($page.StatusCode -eq 200)
Add-Check "graph_board_marker" ($page.Content -match "Live Agent Graph Board")
Add-Check "project_workspace_marker" ($page.Content -match "Project Workspace")
Add-Check "project_sources_marker" ($page.Content -match "Project Sources")
Add-Check "source_quality_marker" ($page.Content -match "Source quality gate")
Add-Check "planner_recommendation_marker" ($page.Content -match "Planner Recommendation")
Add-Check "no_garbled_marker" (-not ($page.Content -match "\?\?\?\?"))

$projectCreated = Invoke-CgJson "POST" "/api/v1/projects" @{
    project_name = "Agent Graph OS Public Smoke"
    product_name = "Portable Mini Blender"
    product_category = "kitchen_appliance"
    source_type = "manual"
}
$projectId = [string]$projectCreated.project.project_id
Add-Check "project_created" (-not [string]::IsNullOrWhiteSpace($projectId))
$projectRead = Invoke-CgJson "GET" "/api/v1/projects/$projectId" $null
$projectAssets = Invoke-CgJson "GET" "/api/v1/projects/$projectId/assets" $null
Add-Check "project_readable" ($projectRead.project.project_id -eq $projectId)
Add-Check "project_assets_list" ($null -ne $projectAssets.assets)
Write-Host "Asset upload skipped in public smoke; upload is covered by local multipart tests." -ForegroundColor Yellow

$plannerEmpty = Invoke-CgJson "GET" "/api/v1/projects/$projectId/planner/recommendation" $null
Add-Check "planner_empty_project_needs_source" ($plannerEmpty.planner_recommendation.overall_status -eq "needs_source")

$sourceCreated = Invoke-CgJson "POST" "/api/v1/projects/$projectId/sources" @{
    source_type = "manual"
    product_name = "Portable Mini Blender"
    product_category = "kitchen_appliance"
    product_description = "A compact rechargeable blender for smoothies and travel."
    manual_reviews = "Hard to clean after one smoothie.`nToo loud for early mornings.`nSmall enough for travel but the cup sometimes leaks in my bag."
    source_notes = "Agent Graph OS public source intelligence smoke."
}
$sourceId = [string]$sourceCreated.project_source.source_id
$sourceList = Invoke-CgJson "GET" "/api/v1/projects/$projectId/sources" $null
$sourceEvidence = Invoke-CgJson "GET" "/api/v1/projects/$projectId/sources/$sourceId/evidence" $null
$sourceHistory = Invoke-CgJson "GET" "/api/v1/projects/$projectId/history/sources" $null
$sourceArtifactHistory = Invoke-CgJson "GET" "/api/v1/projects/$projectId/history/source-artifacts" $null
$sourceGateHistory = Invoke-CgJson "GET" "/api/v1/projects/$projectId/history/source-quality-gates" $null
$sourceSnapshotHistory = Invoke-CgJson "GET" "/api/v1/projects/$projectId/history/source-snapshots" $null
Add-Check "project_source_created" (-not [string]::IsNullOrWhiteSpace($sourceId))
Add-Check "source_adapter_result" ($sourceCreated.adapter_result.adapter_version -eq "source_adapter_v1")
Add-Check "source_quality_gate_ready" ($sourceCreated.source_quality_gate.allows_agent_run -eq $true)
Add-Check "source_evidence_artifact" ($sourceCreated.source_evidence_artifact.artifact_version -eq "source_evidence_artifact_v1")
Add-Check "source_snapshot_created" ($sourceCreated.source_snapshot.snapshot_version -eq "source_snapshot_v1")
Add-Check "source_registry_lineage" ($sourceCreated.artifact_registry.lineage_summary.has_source_artifacts -eq $true)
Add-Check "source_list_includes_created" ($sourceList.sources.source_id -contains $sourceId)
Add-Check "source_evidence_readable" ($sourceEvidence.source_evidence_artifact.source_id -eq $sourceId)
Add-Check "source_history_readable" ($sourceHistory.sources.source_id -contains $sourceId)
Add-Check "source_artifact_history_readable" ($sourceArtifactHistory.source_artifacts.source_id -contains $sourceId)
Add-Check "source_gate_history_readable" ($sourceGateHistory.source_quality_gates.source_id -contains $sourceId)
Add-Check "source_snapshot_history_readable" ($sourceSnapshotHistory.source_snapshots.source_id -contains $sourceId)

$plannerSource = Invoke-CgJson "POST" "/api/v1/projects/$projectId/planner/recommendation/refresh" $null
Add-Check "planner_source_ready" ($plannerSource.planner_recommendation.overall_status -in @("asset_recommended", "ready_for_agent_run"))
Add-Check "planner_can_start_agent_run" ($plannerSource.planner_recommendation.can_start_agent_run -eq $true)

$reviewRequest = @{
    project_id = $projectId
    product_name = "Portable Mini Blender"
    product_category = "kitchen_appliance"
    product_description = "A compact rechargeable blender for smoothies and travel."
    pasted_reviews = "Hard to clean after one smoothie.`nToo loud for early mornings.`nSmall enough for travel but the cup sometimes leaks in my bag."
    target_platform = "TikTok"
    goal = "tiktok_ctr"
    output_language = "en"
}

$generated = Invoke-CgJson "POST" "/api/v1/projects/$projectId/sources/$sourceId/generate" @{
    target_platform = "TikTok"
    goal = "tiktok_ctr"
    output_language = "en"
}
Add-Check "generation_success" ($generated.status -eq "success")
Add-Check "generation_project_scope" ($generated.data.project_id -eq $projectId)
Add-Check "source_generation_packet" ($generated.data.llm_evidence_packet.packet_version -eq "source_evidence_v1")
Add-Check "source_generation_lineage" ($generated.data.project_source.source_id -eq $sourceId)

$runCreated = Invoke-CgJson "POST" "/api/v1/agent-runs/from-reviews" $reviewRequest
$runId = [string]$runCreated.run.run_id
Start-Sleep -Seconds 2
$run = Invoke-CgJson "GET" "/api/v1/agent-runs/$runId" $null
$events = Invoke-CgJson "GET" "/api/v1/agent-runs/$runId/events" $null
Add-Check "agent_run_created" (-not [string]::IsNullOrWhiteSpace($runId))
Add-Check "agent_run_has_events" ($events.events.Count -gt 0)
Add-Check "agent_run_project_scope" ($run.run.project_id -eq $projectId)

$jobCreated = Invoke-CgJson "POST" "/api/v1/video-generation/jobs/from-generation" @{
    generation_data = $generated.data
    provider = "runway"
    output_language = "en"
    project_id = $projectId
}
$jobId = [string]$jobCreated.job.job_id
Add-Check "video_job_created" (-not [string]::IsNullOrWhiteSpace($jobId))
Add-Check "video_job_project_scope" ($jobCreated.job.project_id -eq $projectId)

$baseline = Invoke-CgJson "POST" "/api/v1/video-generation/jobs/$jobId/experiments" @{
    tool_name = "manual_test"
    prompt_type = "runway_style_prompt"
    result_url = "https://example.com/agent-graph-os-baseline.mp4"
    product_consistency_score = 1
    storyboard_following_score = 3
    visual_quality_score = 3
    ad_readiness_score = 3
    overall_score = 2
    failure_reason = "Product identity drifted from the reference."
    notes = "Agent Graph OS public smoke baseline."
}
$reworkRunId = [string]$baseline.job.latest_agent_feedback_decision.triggered_rework_run_id
Add-Check "feedback_rework_created" (-not [string]::IsNullOrWhiteSpace($reworkRunId))

$reworkRun = Invoke-CgJson "GET" "/api/v1/agent-runs/$reworkRunId" $null
Add-Check "rework_run_readable" ($reworkRun.run.run_id -eq $reworkRunId)

$second = Invoke-CgJson "POST" "/api/v1/video-generation/jobs/$jobId/experiments" @{
    tool_name = "manual_test"
    prompt_type = "revised_external_video_handoff"
    result_url = "https://example.com/agent-graph-os-second.mp4"
    product_consistency_score = 4
    storyboard_following_score = 4
    visual_quality_score = 4
    ad_readiness_score = 4
    overall_score = 4
    experiment_round = 2
    linked_rework_run_id = $reworkRunId
    prompt_source = "revised_external_video_handoff"
    notes = "Agent Graph OS public smoke improved round."
}
Add-Check "second_experiment_comparison" ($null -ne $second.job.latest_second_experiment_comparison)
Add-Check "artifact_registry_v2_present" ($second.job.latest_artifact_registry.registry_version -eq "artifact_registry_v2")
Add-Check "artifact_registry_project_scope" ($second.job.latest_artifact_registry.project_id -eq $projectId)

if ($second.job.latest_human_approval_gate) {
    $approved = Invoke-CgJson "POST" "/api/v1/video-generation/jobs/$jobId/approval-gate/decision" @{
        decision = "approved"
        reviewer = "public_smoke"
        notes = "Controlled simulated provider smoke only."
        approved_scope = "controlled_provider_or_manual_handoff"
    }
    Add-Check "human_gate_approved" ($approved.approval_gate.status -eq "approved")
}

$submitted = Invoke-CgJson "POST" "/api/v1/video-generation/jobs/$jobId/provider-submit" @{
    notes = "Agent Graph OS simulated provider submit."
}
$processing = Invoke-CgJson "POST" "/api/v1/video-generation/jobs/$jobId/provider-poll" @{
    notes = "Agent Graph OS simulated provider processing."
}
$completed = Invoke-CgJson "POST" "/api/v1/video-generation/jobs/$jobId/provider-poll" @{
    provider_status = "external_result_ready"
    result_url = "https://example.com/agent-graph-os-provider-result.mp4"
    notes = "Agent Graph OS simulated provider completed."
}
Add-Check "provider_submit_safe" ($submitted.job.provider_runtime.external_api_called -eq $false)
Add-Check "provider_processing" ($processing.job.status -eq "processing")
Add-Check "provider_result_ready" ($completed.job.status -eq "external_result_ready")

$history = Invoke-CgJson "GET" "/api/v1/agent-graph/history/summary" $null
$runReport = Invoke-CgJson "GET" "/api/v1/agent-graph/runs/$reworkRunId/report?format=json" $null
$jobReport = Invoke-CgJson "GET" "/api/v1/video-generation/jobs/$jobId/graph-report?format=markdown" $null
Add-Check "history_summary_success" ($history.status -eq "success")
Add-Check "run_report_success" ($runReport.status -eq "success")
Add-Check "job_markdown_report_success" (-not [string]::IsNullOrWhiteSpace($jobReport.markdown_report))
Add-Check "job_report_project_scope" ($jobReport.report.project_id -eq $projectId)
Add-Check "cost_remains_false" ($jobReport.report.safety_boundaries.cost_incurred_by_crossgrowth -eq $false)

$projectSummary = Invoke-CgJson "GET" "/api/v1/projects/$projectId/graph-summary" $null
$projectRunHistory = Invoke-CgJson "GET" "/api/v1/projects/$projectId/history/runs" $null
$projectJobHistory = Invoke-CgJson "GET" "/api/v1/projects/$projectId/history/jobs" $null
$projectArtifactHistory = Invoke-CgJson "GET" "/api/v1/projects/$projectId/history/artifacts" $null
$projectReportHistory = Invoke-CgJson "GET" "/api/v1/projects/$projectId/history/reports" $null
Add-Check "project_graph_summary_success" ($projectSummary.status -eq "success")
Add-Check "project_source_summary_success" ($projectSummary.project.graph_summary.source_count -gt 0)
Add-Check "planner_project_summary_success" ($projectSummary.planner_recommendation.planner_version -eq "supervisor_planner_v2")
Add-Check "planner_safety_boundaries_false" ($projectSummary.planner_recommendation.safety_boundaries.external_api_called -eq $false -and $projectSummary.planner_recommendation.safety_boundaries.cost_incurred_by_crossgrowth -eq $false -and $projectSummary.planner_recommendation.safety_boundaries.llm_autonomous_decision_enabled -eq $false)
Add-Check "project_run_history_success" ($null -ne $projectRunHistory.runs)
Add-Check "project_job_history_success" ($projectJobHistory.jobs.job_id -contains $jobId)
Add-Check "project_artifact_history_success" ($projectArtifactHistory.artifacts.Count -gt 0)
Add-Check "project_report_history_success" ($projectReportHistory.reports.Count -gt 0)

Write-Host ""
$checks | ConvertTo-Json -Depth 5
if ($checks.Values -contains $false) {
    throw "Agent Graph OS public smoke failed."
}
Write-Host "Agent Graph OS public smoke PASS." -ForegroundColor Green
