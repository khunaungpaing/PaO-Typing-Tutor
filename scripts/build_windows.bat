@echo off
rem ==============================================================================
rem build_windows.bat
rem Launcher wrapper that delegates execution to PowerShell to avoid cmd.exe
rem parenthesis expansion issues.
rem ==============================================================================

setlocal
set "SCRIPT_DIR=%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%build_windows.ps1" %*
set "EXIT_CODE=%ERRORLEVEL%"
exit /b %EXIT_CODE%
