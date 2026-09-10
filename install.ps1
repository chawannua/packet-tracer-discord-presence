[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Cisco Packet Tracer - Discord Rich Presence Installer" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "[ERROR] Python was not found in PATH." -ForegroundColor Red
    Write-Host "Please install Python 3.9+ from https://www.python.org/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit..."
    exit 1
}

Write-Host "[*] Python detected ($($python.Source)). Setting up virtual environment..." -ForegroundColor Green

$venvPath = Join-Path $PSScriptRoot ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "[*] Creating .venv..." -ForegroundColor Gray
    & python -m venv $venvPath
}

$venvPython = Join-Path $venvPath "Scripts\python.exe"
$venvPip = Join-Path $venvPath "Scripts\pip.exe"

Write-Host "[*] Installing dependencies..." -ForegroundColor Gray
& $venvPython -m pip install --quiet --upgrade pip
& $venvPip install --quiet -r (Join-Path $PSScriptRoot "requirements.txt")

Write-Host "[*] Configuring silent Windows Startup..." -ForegroundColor Gray
& $venvPython (Join-Path $PSScriptRoot "install_autostart.py")

Write-Host "[*] Starting presence service silently..." -ForegroundColor Gray
$vbsPath = Join-Path $PSScriptRoot "start_silently.vbs"
Start-Process "wscript.exe" -ArgumentList "`"$vbsPath`""

Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host "  SUCCESS! Packet Tracer Presence is installed & running!" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
Write-Host "- Automatically turns on whenever you open Cisco Packet Tracer." -ForegroundColor White
Write-Host "- Configured to start silently on Windows boot." -ForegroundColor White
Write-Host ""
