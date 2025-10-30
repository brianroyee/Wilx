# Clean build artifacts and virtual environments for Wilx
# Usage: Run from project root in PowerShell: .\scripts\clean_artifacts.ps1

$paths = @("build","dist","venv",".venv-build","__pycache__")
foreach ($p in $paths) {
    if (Test-Path $p) {
        Write-Host "Removing $p..."
        try {
            Remove-Item -Recurse -Force -ErrorAction Stop $p
            Write-Host "Removed $p"
        } catch {
            Write-Warning ('Failed to remove ' + $p + ': ' + $_.Exception.Message)
        }
    } else {
        Write-Host "$p not present, skipping"
    }
}

# Also remove any __pycache__ directories under core and scripts
Get-ChildItem -Path . -Directory -Recurse -Force -ErrorAction SilentlyContinue | Where-Object { $_.Name -eq '__pycache__' } | ForEach-Object {
    try {
        Write-Host "Removing $($_.FullName)"
        Remove-Item -Recurse -Force -ErrorAction Stop $_.FullName
    } catch {
        Write-Warning ('Failed to remove ' + $_.FullName + ': ' + $_.Exception.Message)
    }
}

Write-Host "Clean complete."