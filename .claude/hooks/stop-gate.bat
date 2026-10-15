@echo off
setlocal enabledelayedexpansion
set "ROOT=%~1"
if "%ROOT%"=="" set "ROOT=%CD%"
cd /d "%ROOT%" || exit /b 0
set "MODIFIED=0"
for /f "usebackq delims=" %%F in (`git status --porcelain 2^>nul`) do (
    echo %%F | findstr /r /c:"\.py" >nul && set "MODIFIED=1"
)
if "!MODIFIED!"=="1" (
    echo {"continue":true,"stopReason":"SDLC gate: Python source files were modified. Before finishing, run scripts/test.sh (Unix) or scripts/test.bat (Windows), then scripts/sonar.sh scan (or .bat). Do not push until tests and SonarQube quality gate pass."}
) else (
    echo {"continue":true}
)
exit /b 0
