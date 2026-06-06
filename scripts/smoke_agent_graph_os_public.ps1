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
Add-Check "no_garbled_marker" (-not ($page.Content -match "\?\?\?\?"))

$reviewRequest = @{
    product_name = "Portable Mini Blender"
    product_category = "kitchen_appliance"
    product_description = "A compact rechargeable blender for smoothies and travel."
    pasted_reviews = "Hard to clean after one smoothie.`nToo loud for early mornings.`nSmall enough for travel but the cup sometimes leaks in my bag."
    target_platform = "TikTok"
    goal = "tiktok_ctr"
    output_language = "en"
}

$generated = Invoke-CgJson "POST" "/api/v1/generate-from-reviews" $reviewRequest
Add-Check "generation_success" ($generated.status -eq "success")

$runCreated = Invoke-CgJson "POST" "/api/v1/agent-runs/from-reviews" $reviewRequest
$runId = [string]$runCreated.run.run_id
Start-Sleep -Seconds 2
$run = Invoke-CgJson "GET" "/api/v1/agent-runs/$runId" $null
$events = Invoke-CgJson "GET" "/api/v1/agent-runs/$runId/events" $null
Add-Check "agent_run_created" (-not [string]::IsNullOrWhiteSpace($runId))
Add-Check "agent_run_has_events" ($events.events.Count -gt 0)

$jobCreated = Invoke-CgJson "POST" "/api/v1/video-generation/jobs/from-generation" @{
    generation_data = $generated.data
    provider = "runway"
    output_language = "en"
}
$jobId = [string]$jobCreated.job.job_id
Add-Check "video_job_created" (-not [string]::IsNullOrWhiteSpace($jobId))

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
Add-Check "artifact_registry_present" ($second.job.latest_artifact_registry.registry_version -eq "artifact_registry_v1")

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
Add-Check "cost_remains_false" ($jobReport.report.safety_boundaries.cost_incurred_by_crossgrowth -eq $false)

Write-Host ""
$checks | ConvertTo-Json -Depth 5
if ($checks.Values -contains $false) {
    throw "Agent Graph OS public smoke failed."
}
Write-Host "Agent Graph OS public smoke PASS." -ForegroundColor Green
