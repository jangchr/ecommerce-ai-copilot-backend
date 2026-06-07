param(
    [switch]$Fast,
    [switch]$JsonOnly
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$PythonExe = Join-Path $RepoRoot "l8\Scripts\python.exe"
$QualityGuard = Join-Path $RepoRoot "scripts\frontend_quality_guard.py"
$CgScript = Join-Path $RepoRoot "scripts\cg.ps1"
$RunAllTests = Join-Path $RepoRoot "scripts\run_all_tests.py"

function Invoke-Step {
    param(
        [string]$Label,
        [scriptblock]$Command
    )

    Write-Host ""
    Write-Host "==> $Label"
    & $Command
    Write-Host "[DONE] $Label"
}

Push-Location $RepoRoot
try {
    $latestCommit = git log -1 --oneline
    $gitStatus = git status --short
    $isClean = [string]::IsNullOrWhiteSpace($gitStatus)

    $summary = [ordered]@{
        marker = "Pre-render local readiness bundle"
        latest_commit = $latestCommit
        git_clean = $isClean
        fast_requested = [bool]$Fast
        render_deploy_required = $false
        next_recommendation = "Keep batching locally; render later when ready."
    }

    if ($JsonOnly) {
        $summary | ConvertTo-Json -Depth 5
        exit 0
    }

    Write-Host "CrossGrowth pre-render local readiness check"
    Write-Host "Repo: $RepoRoot"
    Write-Host "Latest commit: $latestCommit"
    Write-Host "Git clean: $isClean"

    Invoke-Step "Run frontend quality guard" {
        & $PythonExe $QualityGuard --json
    }

    Invoke-Step "Run cg gate" {
        & $CgScript gate
    }

    if ($Fast) {
        Invoke-Step "Run fast regression suite" {
            & $PythonExe $RunAllTests --fast
        }
    } else {
        Write-Host ""
        Write-Host "Fast suite skipped. Re-run with -Fast before a real Render batch."
    }

    $finalStatus = git status --short
    $finalClean = [string]::IsNullOrWhiteSpace($finalStatus)

    Write-Host ""
    Write-Host "Pre-render local readiness summary"
    Write-Host "latest_commit: $latestCommit"
    Write-Host "git_clean: $finalClean"
    Write-Host "render_deploy_required: false"
    Write-Host "recommendation: Keep batching locally; render later when ready."

    if (-not $finalClean) {
        Write-Host ""
        Write-Host "Changed files:"
        Write-Host $finalStatus
        throw "Working tree is not clean after readiness check."
    }

    Write-Host "Pre-render local readiness PASS."
}
finally {
    Pop-Location
}
