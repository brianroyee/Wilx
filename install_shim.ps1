<#
install_shim.ps1

Installs the `wilx.bat` shim into a user-local bin directory and
adds that directory to the user's PATH environment variable.

Run this script from PowerShell (unrestricted script policy may be required):
  powershell -ExecutionPolicy Bypass -File .\install_shim.ps1

It will:
- create %USERPROFILE%\bin if needed
- copy wilx.bat into that folder
- add the folder to the user PATH if it is not already present

This does NOT require administrator privileges because it updates the
current user's environment variables.
#>

param()

$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$shimSource = Join-Path $projectRoot 'wilx.bat'
$userBin = Join-Path $env:USERPROFILE 'bin'

if (-not (Test-Path $shimSource)) {
    Write-Error "Cannot find $shimSource. Run this script from the project root where wilx.bat exists."
    exit 1
}

Write-Host "Creating user bin folder: $userBin"
New-Item -ItemType Directory -Path $userBin -Force | Out-Null

$shimDest = Join-Path $userBin 'wilx.bat'
Write-Host "Creating shim at: $shimDest"
# Instead of copying the project-local shim (which expects shell.py next to it),
# create a shim that points to the project's shell.py absolute path. This
# avoids the shim looking for shell.py in %USERPROFILE%\bin.
$shellPath = Join-Path $projectRoot 'shell.py'
if (-not (Test-Path $shellPath)) {
    Write-Error "Cannot find shell.py at expected location: $shellPath"
    exit 1
}

$quotedShell = '"' + $shellPath + '"'
$shimContent = "@echo off`r`nrem Wilx shim - forward to project shell.py`r`npython $quotedShell %*`r`n"
Set-Content -Path $shimDest -Value $shimContent -Encoding Ascii -Force

# Add user bin to PATH if missing
$currentPath = [Environment]::GetEnvironmentVariable('Path', 'User')
if ($currentPath -notlike "*$userBin*") {
    Write-Host "Adding $userBin to user PATH"
    $newPath = $currentPath.TrimEnd(';') + ';' + $userBin
    [Environment]::SetEnvironmentVariable('Path', $newPath, 'User')
    Write-Host "Added. You may need to restart your shell for changes to take effect."
} else {
    Write-Host "$userBin is already on the user PATH"
}

Write-Host "Installation complete. You can now run 'wilx' from a new CMD/PowerShell session."
