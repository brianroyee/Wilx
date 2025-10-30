<#
Build script: create a single-file Windows executable for `core/kill.py` using PyInstaller.

Usage (PowerShell):
  # from repo root
  .\scripts\build_kill_ps1.ps1

What it does:
  - creates a temporary venv in ./.venv-build
  - installs pyinstaller
  - runs pyinstaller --onefile --name kill core\kill.py
  - places final exe in ./dist/kill.exe

Notes:
  - This script requires PowerShell (Windows) and internet access to pip-install PyInstaller.
  - You can adjust flags (add --noconsole or add icon) as needed.
#>
param(
    [string]$VenvPath = '.venv-build',
    [switch]$Clean
)

if ($Clean) {
    Remove-Item -Recurse -Force $VenvPath -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force .\build, .\dist, .\__pycache__ -ErrorAction SilentlyContinue
    Write-Host 'Cleaned build artifacts.'
    exit 0
}

$here = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $here\..  # repo root

if (-not (Test-Path $VenvPath)) {
    python -m venv $VenvPath
}

. "$VenvPath\Scripts\Activate.ps1"

pip install --upgrade pip
pip install pyinstaller

# Run PyInstaller
pyinstaller --onefile --name kill core\kill.py

if (Test-Path .\dist\kill.exe) {
    Write-Host "Built: .\dist\kill.exe"
} else {
    Write-Host 'Build failed or dist/kill.exe not found.' -ForegroundColor Red
}
