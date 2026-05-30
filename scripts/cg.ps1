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

  if ($exitCode -ne 0) {
    throw "Step failed: $label (exit code $exitCode)"
  }
}

function RequireMessage() {
  if ([string]::IsNullOrWhiteSpace($Message)) {
    throw "Commit message is required. Example: .\scripts\cg.ps1 commit-extension `"My commit message`""
  }
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

  foreach ($bucket in @("extension", "frontend", "backend", "tools")) {
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
    git push -u origin spike/review-collection-p0-recovery
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
    git push -u origin spike/review-collection-p0-recovery
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
    git push -u origin spike/review-collection-p0-recovery
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
    git push -u origin spike/review-collection-p0-recovery
  }

  ShowStatus
}


function CopyFeedbackTail($reason = "completed") {
  if (!(Test-Path $Global:CgLastLog)) {
    return
  }

  $tail = Get-Content $Global:CgLastLog -Tail 180

  try {
    $tail | Set-Clipboard
    Write-Host ""
    if ($reason -eq "failed") {
      Write-Host "Feedback copied to clipboard after failure. Paste it into ChatGPT." -ForegroundColor Yellow
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

  $tail = Get-Content $Global:CgLastLog -Tail 160

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


function PushOnly() {
  Run "Push branch" {
    git push -u origin spike/review-collection-p0-recovery
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
    "commit-backend" { CommitBackend }
    "commit-tools" { CommitTools }
    "push" { PushOnly }
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
      Write-Host "  .\scripts\cg.ps1 commit-backend `"Commit message`""
      Write-Host "  .\scripts\cg.ps1 commit-tools `"Commit message`""
      Write-Host "  .\scripts\cg.ps1 push"
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
