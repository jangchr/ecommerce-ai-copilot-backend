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
    git commit -m $Message
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
    git commit -m $Message
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
    git commit -m $Message
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
    git commit -m $Message
  }

  Run "Push branch" {
    git push -u origin spike/review-collection-p0-recovery
  }

  ShowStatus
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
