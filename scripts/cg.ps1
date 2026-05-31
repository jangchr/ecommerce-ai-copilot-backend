param(
  [Parameter(Position = 0)]
  [string]$Command = "help",

  [Parameter(Position = 1)]
  [string]$Message = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$CgLogDir = Join-Path $RepoRoot ".cg"
$Global:CgLastLog = Join-Path $CgLogDir "last.log"

if (!(Test-Path $CgLogDir)) {
  New-Item -ItemType Directory -Force $CgLogDir | Out-Null
}

if ($Command -ne "feedback") {
  Set-Content -Path $Global:CgLastLog -Encoding UTF8 -Value @(
    "CrossGrowth cg runner",
    "Command: $Command",
    "Started: $(Get-Date -Format o)",
    ""
  )
}

function Run($label, $scriptBlock) {
  Write-Host ""
  Write-Host "==> $label" -ForegroundColor Cyan

  if ($Global:CgLastLog) {
    Add-Content -Path $Global:CgLastLog -Value ""
    Add-Content -Path $Global:CgLastLog -Value "==> $label"
  }

  $startedAt = Get-Date
  $previousErrorActionPreference = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  $global:LASTEXITCODE = 0
  $exitCode = 0

  try {
    & $scriptBlock 2>&1 | ForEach-Object {
      $line = $_.ToString()

      if ($line -eq "System.Management.Automation.RemoteException") {
        return
      }

      Write-Host $line
      if ($Global:CgLastLog) {
        Add-Content -Path $Global:CgLastLog -Value $line
      }
    }

    $exitCode = $global:LASTEXITCODE
  } finally {
    $ErrorActionPreference = $previousErrorActionPreference
  }

  $elapsed = [Math]::Round(((Get-Date) - $startedAt).TotalSeconds, 1)

  if ($exitCode -ne 0) {
    $failedLine = "[FAIL] $label (${elapsed}s, exit code $exitCode)"
    Write-Host $failedLine -ForegroundColor Red
    if ($Global:CgLastLog) {
      Add-Content -Path $Global:CgLastLog -Value $failedLine
    }
    throw "Step failed: $label (exit code $exitCode)"
  }

  $doneLine = "[DONE] $label (${elapsed}s)"
  Write-Host $doneLine -ForegroundColor Green
  if ($Global:CgLastLog) {
    Add-Content -Path $Global:CgLastLog -Value $doneLine
  }
}

function RequireMessage() {
  if ([string]::IsNullOrWhiteSpace($Message)) {
    throw "Commit message is required. Example: .\scripts\cg.ps1 commit-extension `"My commit message`""
  }
}

function GetCurrentBranchName() {
  return (git branch --show-current).Trim()
}

function PushCurrentBranch() {
  $branch = GetCurrentBranchName
  if ([string]::IsNullOrWhiteSpace($branch)) {
    throw "Could not determine current git branch."
  }

  git push -u origin $branch
}


function AddExistingPath($path) {
  if (Test-Path $path) {
    git add $path
  }
}

function CommitStagedChanges() {
  git diff --cached --quiet
  if ($global:LASTEXITCODE -eq 0) {
    Write-Host "No staged changes to commit. Working tree may already be clean."
    $global:LASTEXITCODE = 0
    return
  }

  & git commit -m $Message
}




function WriteCgFeedbackLine($line = "") {
  Write-Host $line
  if ($Global:CgLastLog) {
    Add-Content -Path $Global:CgLastLog -Value $line
  }
}

function GetChangedFiles() {
  $files = @(git status --porcelain | ForEach-Object {
    if ($_.Length -ge 4) {
      $_.Substring(3).Trim()
    }
  } | Where-Object { $_ })

  return $files
}

function TestAllFilesInBucket($files, $bucket) {
  $files = @($files)
  if ($files.Count -eq 0) {
    return $false
  }

  foreach ($file in $files) {
    $match = $false

    if ($bucket -eq "extension") {
      $match = (
        $file -like "browser_extension/*" -or
        $file -eq "tests/test_browser_extension_contract.py"
      )
    } elseif ($bucket -eq "frontend") {
      $match = (
        $file -eq "static/index.html" -or
        $file -eq "tests/test_frontend_probe_boundary.py"
      )
    } elseif ($bucket -eq "ui") {
      $match = (
        $file -like "browser_extension/*" -or
        $file -eq "static/index.html" -or
        $file -eq "tests/test_browser_extension_contract.py" -or
        $file -eq "tests/test_frontend_probe_boundary.py"
      )
    } elseif ($bucket -eq "backend") {
      $match = (
        $file -eq "main.py" -or
        $file -like "schemas/*" -or
        $file -eq "tests/test_review_workspace_endpoint.py"
      )
    } elseif ($bucket -eq "tools") {
      $match = (
        $file -like "scripts/*" -or
        $file -like ".github/workflows/*" -or
        $file -like "recipes/*" -or
        $file -like ".recipes/*" -or
        $file -eq ".gitignore"
      )
    }

    if (!$match) {
      return $false
    }
  }

  return $true
}

function GetChangeBucket($files) {
  $files = @($files)

  if ($files.Count -eq 0) {
    return "clean"
  }

  foreach ($bucket in @("extension", "frontend", "ui", "backend", "tools")) {
    if (TestAllFilesInBucket $files $bucket) {
      return $bucket
    }
  }

  return "mixed"
}

function GetRecommendedCommand($bucket) {
  switch ($bucket) {
    "extension" { return '.\scripts\cg.ps1 commit-extension "Commit message"' }
    "frontend" { return '.\scripts\cg.ps1 commit-frontend "Commit message"' }
    "ui" { return '.\scripts\cg.ps1 commit-ui "Commit message"' }
    "backend" { return '.\scripts\cg.ps1 commit-backend "Commit message"' }
    "tools" { return '.\scripts\cg.ps1 commit-tools "Commit message"' }
    "clean" { return "No commit needed. Working tree clean." }
    default { return "Mixed changes. Ask ChatGPT before committing." }
  }
}

function PrintCgPassSummary() {
  $files = @(GetChangedFiles)
  $bucket = GetChangeBucket $files
  $recommended = GetRecommendedCommand $bucket

  WriteCgFeedbackLine ""
  WriteCgFeedbackLine "CG RESULT: PASS"

  if ($files.Count -eq 0) {
    WriteCgFeedbackLine "Changed files: none"
  } else {
    WriteCgFeedbackLine "Changed files:"
    foreach ($file in $files) {
      WriteCgFeedbackLine "- $file"
    }
  }

  WriteCgFeedbackLine "Change bucket: $bucket"
  WriteCgFeedbackLine "Recommended next command: $recommended"
}

function PrintCgFailSummary($message) {
  WriteCgFeedbackLine ""
  WriteCgFeedbackLine "CG RESULT: FAIL"
  WriteCgFeedbackLine "Failed step: $message"
  WriteCgFeedbackLine "Recommended next command: Do not commit. Paste this feedback to ChatGPT."
}


function Gate() {
  Run "Run focused unit tests" {
    .\l8\Scripts\python.exe -m unittest tests.test_browser_extension_contract tests.test_frontend_probe_boundary tests.test_review_workspace_endpoint
  }

  Run "Check whitespace / diff errors" {
    git diff --check
  }

  Run "Show git status" {
    git status -sb
  }

  PrintCgPassSummary
}

function ShowStatus() {
  Run "Git status" {
    git status -sb
  }

  Run "Diff stat" {
    git diff --stat
  }

  Run "Recent commits" {
    git log -8 --oneline
  }
}

function CommitExtension() {
  RequireMessage
  Gate

  Run "Add extension files" {
    git add browser_extension/popup.html browser_extension/popup.js tests/test_browser_extension_contract.py
  }

  Run "Commit extension changes" {
    CommitStagedChanges
  }

  Run "Push branch" {
    PushCurrentBranch
  }

  ShowStatus
}

function CommitFrontend() {
  RequireMessage
  Gate

  Run "Add frontend files" {
    git add static/index.html tests/test_frontend_probe_boundary.py
  }

  Run "Commit frontend changes" {
    CommitStagedChanges
  }

  Run "Push branch" {
    PushCurrentBranch
  }

  ShowStatus
}


function CommitUi() {
  RequireMessage
  Gate

  Run "Add UI and extension files" {
    AddExistingPath "browser_extension\popup.html"
    AddExistingPath "browser_extension\popup.js"
    AddExistingPath "browser_extension\styles.css"
    AddExistingPath "static\index.html"
    AddExistingPath "tests\test_browser_extension_contract.py"
    AddExistingPath "tests\test_frontend_probe_boundary.py"
  }

  Run "Commit UI changes" {
    CommitStagedChanges
  }

  Run "Push branch" {
    PushCurrentBranch
  }

  ShowStatus
}

function CommitBackend() {
  RequireMessage
  Gate

  Run "Add backend files" {
    git add main.py schemas/review_workspace.py tests/test_review_workspace_endpoint.py
  }

  Run "Commit backend changes" {
    CommitStagedChanges
  }

  Run "Push branch" {
    PushCurrentBranch
  }

  ShowStatus
}

function CommitTools() {
  RequireMessage
  Gate

  Run "Add tool and automation files" {
    AddExistingPath "scripts\\cg.ps1"
    AddExistingPath ".gitignore"
    AddExistingPath "scripts\\*.ps1"
    AddExistingPath ".github\\workflows\\*.yml"
    AddExistingPath ".github\\workflows\\*.yaml"
    AddExistingPath "recipes\\*.ps1"
    AddExistingPath ".recipes\\*.ps1"
  }

  Run "Commit tool changes" {
    CommitStagedChanges
  }

  Run "Push branch" {
    PushCurrentBranch
  }

  ShowStatus
}



function FormatCgFeedbackLine($line) {
  $value = [string]$line
  if ($value.Length -le 360) {
    return $value
  }

  return ($value.Substring(0, 360) + " ... [truncated]")
}

function GetCgFocusedFailureFeedback() {
  if (!(Test-Path $Global:CgLastLog)) {
    return @()
  }

  $lines = @(Get-Content $Global:CgLastLog)
  if ($lines.Count -eq 0) {
    return @()
  }

  $failureIndexes = @()
  for ($i = 0; $i -lt $lines.Count; $i++) {
    $line = [string]$lines[$i]
    if (
      $line -match "^(FAIL|ERROR): " -or
      $line -match "AssertionError|SyntaxError|Traceback \(most recent call last\):|\[FAIL\]"
    ) {
      $failureIndexes += $i
    }
  }

  if ($failureIndexes.Count -eq 0) {
    return @()
  }

  $first = $failureIndexes[0]
  $start = [Math]::Max(0, $first - 8)
  $end = [Math]::Min($lines.Count - 1, $first + 45)

  $focused = @()
  $focused += "CrossGrowth cg runner"
  $focused += "Focused failure summary"
  $focused += ""

  for ($i = $start; $i -le $end; $i++) {
    $focused += (FormatCgFeedbackLine $lines[$i])
  }

  $summary = @(
    $lines |
      Select-Object -Last 80 |
      Where-Object {
        $_ -match "^CG RESULT:" -or
        $_ -match "^Failed step:" -or
        $_ -match "^Recommended next command:" -or
        $_ -match "^cg command failed:"
      }
  )

  if ($summary.Count -gt 0) {
    $focused += ""
    $focused += "Runner summary:"
    foreach ($line in $summary) {
      $focused += (FormatCgFeedbackLine $line)
    }
  }

  return $focused
}



function CopyFeedbackTail($reason = "completed") {
  if (!(Test-Path $Global:CgLastLog)) {
    return
  }

  if ($reason -eq "failed") {
    $tail = @(GetCgFocusedFailureFeedback)
    if ($tail.Count -eq 0) {
      $tail = @(Get-Content $Global:CgLastLog -Tail 180)
    }
  } else {
    $tail = @(Get-Content $Global:CgLastLog -Tail 180)
  }

  try {
    $tail | Set-Clipboard
    Write-Host ""
    if ($reason -eq "failed") {
      Write-Host "Focused failure feedback copied to clipboard. Paste it into ChatGPT." -ForegroundColor Yellow
    } else {
      Write-Host "Feedback copied to clipboard. Paste it into ChatGPT." -ForegroundColor Green
    }
  } catch {
    Write-Host ""
    Write-Host "Could not copy feedback to clipboard. Run .\\scripts\\cg.ps1 feedback or copy .cg/last.log manually." -ForegroundColor Yellow
  }
}


function Feedback() {
  if (!(Test-Path $Global:CgLastLog)) {
    throw "No feedback log found. Run .\scripts\cg.ps1 gate first."
  }

  $all = @(Get-Content $Global:CgLastLog)
  $hasFailure = @($all | Where-Object { $_ -eq "CG RESULT: FAIL" }).Count -gt 0

  if ($hasFailure) {
    $tail = @(GetCgFocusedFailureFeedback)
    if ($tail.Count -eq 0) {
      $tail = @(Get-Content $Global:CgLastLog -Tail 160)
    }
  } else {
    $tail = @(Get-Content $Global:CgLastLog -Tail 160)
  }

  Write-Host ""
  Write-Host "==> Recent cg feedback (.cg/last.log)" -ForegroundColor Cyan
  $tail

  try {
    $tail | Set-Clipboard
    Write-Host ""
    Write-Host "Feedback copied to clipboard. Paste it into ChatGPT." -ForegroundColor Green
  } catch {
    Write-Host ""
    Write-Host "Could not copy feedback to clipboard. Please copy the output above." -ForegroundColor Yellow
  }
}

function MergeMain() {
  $Spike = "spike/review-collection-p0-recovery"
  $Main = "main"

  $dirty = git status --porcelain
  if ($dirty) {
    throw "Working tree is not clean. Run .\\scripts\\cg.ps1 status first."
  }

  Run "Fetch origin" {
    git fetch origin
  }

  Run "Checkout spike branch" {
    git checkout $Spike
  }

  Run "Pull latest spike branch" {
    git pull --ff-only origin $Spike
  }

  Gate

  Run "Checkout main branch" {
    git checkout $Main
  }

  Run "Pull latest main branch" {
    git pull --ff-only origin $Main
  }

  Run "Merge spike into main" {
    git merge --no-ff $Spike -m "Merge review collection recovery spike"
  }

  Gate

  Run "Push merged main" {
    git push origin $Main
  }

  ShowStatus
}


function PushOnly() {
  Run "Push branch" {
    PushCurrentBranch
  }

  ShowStatus
}

$cgCommandFailed = $false

try {
  switch ($Command) {
    "gate" { Gate }
    "status" { ShowStatus }
    "commit-extension" { CommitExtension }
    "commit-frontend" { CommitFrontend }
    "commit-ui" { CommitUi }
    "commit-backend" { CommitBackend }
    "commit-tools" { CommitTools }
    "push" { PushOnly }
  "merge-main" { MergeMain }
    "feedback" { Feedback }
    "help" {
      Write-Host ""
      Write-Host "CrossGrowth local runner"
      Write-Host ""
      Write-Host "Usage:"
      Write-Host "  .\scripts\cg.ps1 gate"
      Write-Host "  .\scripts\cg.ps1 status"
      Write-Host "  .\scripts\cg.ps1 commit-extension `"Commit message`""
      Write-Host "  .\scripts\cg.ps1 commit-frontend `"Commit message`""
      Write-Host "  .\scripts\cg.ps1 commit-ui `"Commit message`""
      Write-Host "  .\scripts\cg.ps1 commit-backend `"Commit message`""
      Write-Host "  .\scripts\cg.ps1 commit-tools `"Commit message`""
      Write-Host "  .\scripts\cg.ps1 push"
    Write-Host "  .\scripts\cg.ps1 merge-main"
      Write-Host "  .\scripts\cg.ps1 feedback"
      Write-Host ""
    }
    default {
      throw "Unknown command: $Command. Run .\scripts\cg.ps1 help"
    }
  }
} catch {
  $cgCommandFailed = $true
  $message = $_.Exception.Message

  Write-Host ""
  Write-Host "cg command failed: $message" -ForegroundColor Red

  if ($Global:CgLastLog) {
    Add-Content -Path $Global:CgLastLog -Value ""
    Add-Content -Path $Global:CgLastLog -Value "cg command failed: $message"
  }

  PrintCgFailSummary $message

  throw
} finally {
  if ($Command -ne "feedback") {
    if ($cgCommandFailed) {
      CopyFeedbackTail "failed"
    } else {
      CopyFeedbackTail "completed"
    }
  }
}
