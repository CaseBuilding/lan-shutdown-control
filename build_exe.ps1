param(
    [switch]$InstallBuildDeps
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ToolsDir = Join-Path $ProjectRoot "build_tools"

function Ensure-BuildDeps {
    if (Test-Path (Join-Path $ToolsDir "PyInstaller")) {
        return
    }

    Write-Host "Installing build dependencies into $ToolsDir ..."
    python -m pip install --target $ToolsDir pyinstaller
}

if ($InstallBuildDeps) {
    Ensure-BuildDeps
}

if (-not (Test-Path (Join-Path $ToolsDir "PyInstaller"))) {
    Write-Host "Local build_tools copy not found. Will try the current Python environment first."
}

$env:PYTHONPATH = "$ProjectRoot"

try {
    python -m PyInstaller --clean --noconfirm "$ProjectRoot\LanShutdownControl.spec"
}
catch {
    if (-not (Test-Path (Join-Path $ToolsDir "PyInstaller"))) {
        throw
    }

    $env:PYTHONPATH = "$ToolsDir;$ProjectRoot"

    @"
import sys
sys.path.insert(0, r"$ToolsDir")
sys.path.insert(0, r"$ProjectRoot")
from PyInstaller.__main__ import run
run([
    "--clean",
    "--noconfirm",
    r"$ProjectRoot\LanShutdownControl.spec",
])
"@ | python -
}

Write-Host ""
Write-Host "Build completed."
Write-Host "Output folder: $ProjectRoot\dist\LanShutdownControl"
