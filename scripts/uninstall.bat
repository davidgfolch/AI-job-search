@echo off
setlocal enabledelayedexpansion

rem Remove the dependencies and generated artifacts installed by install.*.
rem Shows an interactive menu (delegated to PowerShell) and can remove several
rem items at once. No git command is used, and protected paths are never touched.

powershell -NoProfile -File "%~dp0uninstall-menu.ps1"
exit /b