<#
.SYNOPSIS
  One-shot setup for claude-voice on Windows: installs Python, ffmpeg and VoiceStudio if missing,
  then configures Claude Code hooks.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File setup.ps1
  powershell -ExecutionPolicy Bypass -File setup.ps1 -Speed 1.3 -Profile abc12345
  powershell -ExecutionPolicy Bypass -File setup.ps1 -DryRun

.NOTES
  Safe to re-run: every step is skipped if already done.
  Downloads VoiceStudio (about 220 MB) from its official GitHub release and verifies the SHA-256.
  Choosing a speech model and creating/cloning a voice are done in the VoiceStudio app afterwards.
#>
param(
  [switch]$SkipVoiceStudio,   # don't install VoiceStudio (you already have it, or run it elsewhere)
  [switch]$SkipHooks,         # don't touch Claude Code settings
  [switch]$DryRun,            # print what would happen, change nothing
  [string]$Profile,           # default voice profile id
  [string]$Language,          # default language
  [string]$Speed              # default speed multiplier
)
$ErrorActionPreference = 'Stop'
$Repo = Split-Path -Parent $MyInvocation.MyCommand.Path

function Step($m) { Write-Host "`n==> $m" -ForegroundColor Cyan }
function Have($cmd) { [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }
function Refresh-Path {
  $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
}
function Run($desc, [scriptblock]$sb) {
  if ($DryRun) { Write-Host "[dry-run] $desc" -ForegroundColor Yellow } else { & $sb }
}
function Winget-Install($id) {
  if (-not (Have winget)) { throw "winget not found. Install 'App Installer' from the Microsoft Store, or install $id manually, then re-run." }
  winget install --id $id -e --accept-source-agreements --accept-package-agreements
  Refresh-Path
}

# --- Python --------------------------------------------------------------
Step 'Python 3'
$py = if (Have python) { (& python --version 2>&1) } else { $null }
if ($py -match 'Python 3') { Write-Host "found: $py" }
else { Run 'winget install Python.Python.3.12' { Winget-Install 'Python.Python.3.12' } }

# --- ffmpeg (ffplay) -----------------------------------------------------
Step 'ffmpeg / ffplay'
if (Have ffplay) { Write-Host 'found: ffplay' }
else { Run 'winget install Gyan.FFmpeg' { Winget-Install 'Gyan.FFmpeg' } }

# --- VoiceStudio ---------------------------------------------------------
$project = Join-Path $env:APPDATA 'VoiceStudio\runtime\project'
$venvPy = Join-Path $project '.venv\Scripts\python.exe'
Step 'VoiceStudio'
if ($SkipVoiceStudio) { Write-Host 'skipped (-SkipVoiceStudio)' }
elseif (Test-Path $venvPy) { Write-Host "found backend: $project" }
else {
  $arch = if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64') { 'arm64' } else { 'x64' }
  Run "download and install VoiceStudio win-$arch from GitHub releases" {
    $rel = Invoke-RestMethod 'https://api.github.com/repos/debpalash/VoiceStudio/releases/latest' -Headers @{ 'User-Agent' = 'claude-voice-setup' }
    $asset = $rel.assets | Where-Object { $_.name -like "VoiceStudio-*-win-$arch.exe" } | Select-Object -First 1
    if (-not $asset) { throw "No Windows $arch installer in release $($rel.tag_name). Install VoiceStudio manually from https://github.com/debpalash/VoiceStudio/releases/latest and re-run with -SkipVoiceStudio." }
    $dl = Join-Path $env:TEMP $asset.name
    Write-Host "downloading $($asset.name) ($([math]::Round($asset.size/1MB)) MB)..."
    Invoke-WebRequest $asset.browser_download_url -OutFile $dl

    $sums = ($rel.assets | Where-Object { $_.name -eq 'SHA256SUMS.txt' } | Select-Object -First 1)
    if ($sums) {
      $line = (Invoke-RestMethod $sums.browser_download_url -Headers @{ 'User-Agent' = 'claude-voice-setup' }) -split "`n" | Where-Object { $_ -match [regex]::Escape($asset.name) + '\s*$' } | Select-Object -First 1
      if ($line) {
        $want = ($line -split '\s+')[0].ToLower()
        $got = (Get-FileHash $dl -Algorithm SHA256).Hash.ToLower()
        if ($want -ne $got) { Remove-Item $dl; throw "SHA-256 mismatch for $($asset.name). Aborting." }
        Write-Host 'SHA-256 verified.'
      } else { Write-Warning 'No checksum line for this file; continuing unverified.' }
    }

    Write-Host 'running installer (silent)...'
    Start-Process $dl -ArgumentList '/S' -Wait
    $exe = @("$env:LOCALAPPDATA\Programs\VoiceStudio\VoiceStudio.exe", "$env:ProgramFiles\VoiceStudio\VoiceStudio.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $exe) { Write-Warning 'Installed, but could not find VoiceStudio.exe. Launch VoiceStudio once yourself, then re-run this script.'; return }
    Write-Host 'launching VoiceStudio once so it can build its backend (first run can take several minutes)...'
    Start-Process $exe
    $deadline = (Get-Date).AddMinutes(20)
    while (-not (Test-Path $venvPy) -and (Get-Date) -lt $deadline) { Start-Sleep 10 }
    if (-not (Test-Path $venvPy)) { Write-Warning 'Backend not ready yet. Leave VoiceStudio open until it finishes, then re-run this script.' }
  }
}

# --- Claude Code hooks ---------------------------------------------------
Step 'Claude Code hooks'
if ($SkipHooks) { Write-Host 'skipped (-SkipHooks)' }
else {
  $args2 = @('-I', (Join-Path $Repo 'install.py'))
  if ($Profile)  { $args2 += @('--profile', $Profile) }
  if ($Language) { $args2 += @('--language', $Language) }
  if ($Speed)    { $args2 += @('--speed', $Speed) }
  Run "python $($args2 -join ' ')" { & python @args2 }
}

Step 'Done'
Write-Host @"
Remaining manual steps (done in the VoiceStudio app):
  1. Download a speech model (Models page).
  2. Create or clone a voice (only clone voices you have the right to use).
Then:
  python scripts\speak.py --list-voices
  python scripts\speak.py "Hello from Claude"
Start a new Claude Code session and answer yes to "Want voice on this session?".
"@
