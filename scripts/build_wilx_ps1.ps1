<#
Build script: create a single-file Windows executable for the whole project (entrypoint `main.py`) using PyInstaller.

Usage (PowerShell):
  # from repo root
  .\scripts\build_wilx_ps1.ps1

What it does:
  - creates a temporary venv in ./.venv-build
  - installs pyinstaller
  - runs pyinstaller --onefile --name wilx main.py
  - places final exe in ./dist/wilx.exe

Notes:
  - This script requires PowerShell (Windows) and internet access to pip-install PyInstaller.
  - Building may take a few minutes.
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

# Run PyInstaller for the full project
pyinstaller --onefile --name wilx main.py

if (Test-Path .\dist\wilx.exe) {
    Write-Host "Built: .\dist\wilx.exe"
} else {
    Write-Host 'Build failed or dist/wilx.exe not found.' -ForegroundColor Red
}
