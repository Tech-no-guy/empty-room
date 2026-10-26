# ==============================================================================
# Empty Room — Smart Screen Lock PowerShell Installer (iex compatible)
# Usage:
#   irm https://raw.githubusercontent.com/Tech-no-guy/empty-room/main/install.ps1 | iex
# or locally:
#   iex (Get-Content ./install.ps1 -Raw)
# ==============================================================================

$ErrorActionPreference = 'Stop'

Write-Host ""
Write-Host "  =======================================================" -ForegroundColor Cyan
Write-Host "     EMPTY ROOM - SMART SCREEN LOCK" -ForegroundColor Cyan
Write-Host "     Automated Installer" -ForegroundColor Cyan
Write-Host "  =======================================================" -ForegroundColor Cyan
Write-Host ""

$InstallDir = Join-Path $HOME ".empty-room"
$AppDir     = Join-Path $InstallDir "app"
$VenvDir    = Join-Path $InstallDir "venv"
$BinDir     = Join-Path $InstallDir "bin"

# 1. Check Python 3
Write-Host "[1/5] Checking for Python 3..." -ForegroundColor Yellow
$PythonCmd = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $ver = & $cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        if ($ver -and [float]$ver -ge 3.8) {
            $PythonCmd = $cmd
            Write-Host "      Found Python $ver ($cmd)" -ForegroundColor Green
            break
        }
    } catch {}
}

if (-not $PythonCmd) {
    Write-Host "[ERROR] Python 3.8 or newer was not detected on your system PATH." -ForegroundColor Red
    Write-Host "Please download and install Python from https://www.python.org/downloads/ (ensure 'Add python.exe to PATH' is checked)." -ForegroundColor Red
    return
}

# 2. Prepare Directories
Write-Host "[2/5] Initializing installation directories in $InstallDir..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $InstallDir, $BinDir | Out-Null

# If running from a git clone/source repository
$CurrentScriptDir = $PSScriptRoot
if (-not $CurrentScriptDir -and $MyInvocation.MyCommand.Path) {
    $CurrentScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}

if ($CurrentScriptDir -and (Test-Path (Join-Path $CurrentScriptDir "core"))) {
    Write-Host "      Detected local source directory. Linking application files..." -ForegroundColor Gray
    Copy-Item -Recurse -Force -Path (Join-Path $CurrentScriptDir "*") -Destination $AppDir
} else {
    Write-Host "      Downloading latest release from GitHub..." -ForegroundColor Gray
    $ZipUrl = "https://github.com/Tech-no-guy/empty-room/archive/refs/heads/main.zip"
    $ZipPath = Join-Path $InstallDir "repo.zip"
    Invoke-WebRequest -Uri $ZipUrl -OutFile $ZipPath
    Expand-Archive -Path $ZipPath -DestinationPath $InstallDir -Force
    Remove-Item -Force $ZipPath
    $Extracted = Join-Path $InstallDir "empty-room-main"
    if (Test-Path $Extracted) {
        if (Test-Path $AppDir) { Remove-Item -Recurse -Force $AppDir }
        Move-Item -Path $Extracted -Destination $AppDir
    }
}

# 3. Setup Virtual Environment
Write-Host "[3/5] Setting up isolated Python environment..." -ForegroundColor Yellow
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    & $PythonCmd -m venv $VenvDir
}

$PipCmd = Join-Path $VenvDir "Scripts\pip.exe"
Write-Host "      Installing required computer-vision dependencies..." -ForegroundColor Gray
& $PipCmd install --quiet --upgrade pip
$ReqPath = Join-Path $AppDir "requirements.txt"
if (Test-Path $ReqPath) {
    & $PipCmd install --quiet -r $ReqPath
} else {
    & $PipCmd install --quiet opencv-contrib-python numpy Flask
}

# 4. Generate Global Command Shims
Write-Host "[4/5] Creating global CLI shims..." -ForegroundColor Yellow

$CmdShimPath = Join-Path $BinDir "empty-room.cmd"
$Ps1ShimPath = Join-Path $BinDir "empty-room.ps1"

$CmdShimContent = @"
@echo off
set "PYTHONPATH=$AppDir;%PYTHONPATH%"
"$VenvPython" -m core.cli %*
"@

$Ps1ShimContent = @"
`$env:PYTHONPATH = "$AppDir;" + `$env:PYTHONPATH
& "$VenvPython" -m core.cli `$args
"@

[System.IO.File]::WriteAllText($CmdShimPath, $CmdShimContent)
[System.IO.File]::WriteAllText($Ps1ShimPath, $Ps1ShimContent)

# 5. Add to User PATH if not present
Write-Host "[5/5] Configuring environment PATH..." -ForegroundColor Yellow
$UserPath = [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::User)
if ($UserPath -notlike "*$BinDir*") {
    $NewUserPath = "$BinDir;$UserPath"
    [Environment]::SetEnvironmentVariable("Path", $NewUserPath, [EnvironmentVariableTarget]::User)
    Write-Host "      Added $BinDir to User PATH." -ForegroundColor Green
}
# Update current session path
if ($env:Path -notlike "*$BinDir*") {
    $env:Path = "$BinDir;$env:Path"
}

Write-Host ""
Write-Host "  =======================================================" -ForegroundColor Green
Write-Host "     INSTALLATION COMPLETE!" -ForegroundColor Green
Write-Host "  =======================================================" -ForegroundColor Green
Write-Host ""
Write-Host "You can now run Empty Room from any terminal:" -ForegroundColor Cyan
Write-Host "  empty-room run            - Run presence detection mode" -ForegroundColor White
Write-Host "  empty-room configure run  - Launch web dashboard to enroll face & adjust settings" -ForegroundColor White
Write-Host "  empty-room shadow on      - Run detached background daemon (survives terminal close)" -ForegroundColor White
Write-Host "  empty-room shadow off     - Stop background shadow daemon" -ForegroundColor White
Write-Host "  empty-room stop           - Stop all active instances" -ForegroundColor White
Write-Host "  empty-room help           - View full command reference" -ForegroundColor White
Write-Host ""
