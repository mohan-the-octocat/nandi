@echo off
rem ============================================================================
rem Google Cloud Model Armor Setup Wrapper for Windows Command Prompt
rem Executes setup-model-armor.ps1 with ExecutionPolicy Bypass
rem ============================================================================
setlocal
set "SCRIPT_DIR=%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%setup-model-armor.ps1" %*
exit /b %ERRORLEVEL%
