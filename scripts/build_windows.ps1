# ==============================================================================
# build_windows.ps1
# Builds Windows executable and Inno Setup installer for Pa-O Typing Tutor.
# Uses PowerShell to avoid cmd.exe parenthesis expansion issues.
# ==============================================================================

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir
Set-Location $RootDir

Write-Host "==> Extracting application version from core/version.py..." -ForegroundColor Cyan
$Version = python -c "import runpy; print(runpy.run_path('core/version.py')['__version__'])"
$AppName = "Pa-O Typing Tutor"

Write-Host "==> Building $AppName version $Version for Windows..." -ForegroundColor Cyan

Write-Host "==> Ensuring platform icons are generated..." -ForegroundColor Cyan
python make_icons.py

Write-Host "==> Cleaning old build directories..." -ForegroundColor Cyan
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist\$AppName") { Remove-Item -Recurse -Force "dist\$AppName" }

Write-Host "==> Running PyInstaller..." -ForegroundColor Cyan
pyinstaller --clean --noconfirm pao-typing-tutor.spec

$DistExe = "dist\$AppName\$AppName.exe"
if (-not (Test-Path $DistExe)) {
    Write-Error "PyInstaller build failed: $DistExe not found."
}

Write-Host "==> Locating Inno Setup Compiler (ISCC.exe)..." -ForegroundColor Cyan
$IsccCandidates = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles}\Inno Setup 6\ISCC.exe",
    "${env:LOCALAPPDATA}\Programs\Inno Setup 6\ISCC.exe"
)

$Iscc = $null
foreach ($path in $IsccCandidates) {
    if (Test-Path $path) {
        $Iscc = $path
        break
    }
}

if (-not $Iscc) {
    $cmdIscc = Get-Command "ISCC.exe" -ErrorAction SilentlyContinue
    if ($cmdIscc) {
        $Iscc = $cmdIscc.Source
    }
}

if ($Iscc) {
    Write-Host "==> Compiling installer with Inno Setup ($Iscc)..." -ForegroundColor Cyan
    & $Iscc "/DMyAppVersion=$Version" "installer.iss"
    
    $InstallerExe = "dist\Pa-O-Typing-Tutor-v${Version}-windows-setup.exe"
    if (Test-Path $InstallerExe) {
        Write-Host ""
        Write-Host "==============================================================================" -ForegroundColor Green
        Write-Host " Windows Build Succeeded!" -ForegroundColor Green
        Write-Host " Application folder: dist\$AppName" -ForegroundColor Green
        Write-Host " Installer package:  $InstallerExe" -ForegroundColor Green
        Write-Host "==============================================================================" -ForegroundColor Green
    } else {
        Write-Warning "Installer was compiled, but $InstallerExe was not found."
    }
} else {
    Write-Warning "Inno Setup (ISCC.exe) not found. PyInstaller executable was built in dist\$AppName."
    Write-Warning "To build the installer, install Inno Setup 6: https://jrsoftware.org/isdl.php"
}
