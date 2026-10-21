@echo off
setlocal EnableDelayedExpansion

rem ──────────────────────  Static analysis entry point  ──────────────────────
rem Usage: scripts\lint.bat [python|web|e2e|all]     (default: all)
rem
rem   python  ruff over apps\ and scripts\ (root ruff.toml)
rem   web     eslint + tsc typecheck over apps\web
rem   e2e     eslint over apps\e2e
rem   all     every check above
rem
rem Ruff is installed once for the whole repo (uv tool install ruff); no app
rem needs it in its own environment. RUFF_BIN overrides the binary used.

set "target=all"
if not "%~1"=="" set "target=%~1"

set "failed=0"
set "ruff_cmd="

call :resolve_ruff

if /i "%target%"=="python" goto :python
if /i "%target%"=="web" goto :web
if /i "%target%"=="e2e" goto :e2e
if /i "%target%"=="all" goto :all
echo Unknown target '%target%'. Expected: python, web, e2e, all
endlocal & exit /b 2

:all
call :python
if !failed! neq 0 goto :finish
call :web
if !failed! neq 0 goto :finish
call :e2e
goto :finish

:python
echo.
echo ────────────────────────────────────────────────────────
echo Static analysis: Python (ruff)
echo ────────────────────────────────────────────────────────
if not defined ruff_cmd (
    echo ruff not found. Install it with: uv tool install ruff
    set "failed=1"
    exit /b 1
)
echo Using: !ruff_cmd!
!ruff_cmd! check apps\ scripts\ --config ruff.toml
if !errorlevel! neq 0 set "failed=1"
exit /b !errorlevel!

:web
echo.
echo ────────────────────────────────────────────────────────
echo Static analysis: apps\web (eslint + typecheck)
echo ────────────────────────────────────────────────────────
pushd "apps\web" || exit /b 1
call npm run lint
if !errorlevel! neq 0 (
    set "failed=1"
    popd
    exit /b 1
)
call npm run typecheck
set "code=!errorlevel!"
popd
if !code! neq 0 set "failed=1"
exit /b !code!

:e2e
echo.
echo ────────────────────────────────────────────────────────
echo Static analysis: apps\e2e (eslint)
echo ────────────────────────────────────────────────────────
pushd "apps\e2e" || exit /b 1
call npm run lint
set "code=!errorlevel!"
popd
if !code! neq 0 set "failed=1"
exit /b !code!

:resolve_ruff
if defined RUFF_BIN (
    set "ruff_cmd=%RUFF_BIN%"
    exit /b 0
)
where ruff >nul 2>&1
if !errorlevel! equ 0 (
    set "ruff_cmd=ruff"
    exit /b 0
)
where uvx >nul 2>&1
if !errorlevel! equ 0 (
    set "ruff_cmd=uvx ruff"
    exit /b 0
)
where uv >nul 2>&1
if !errorlevel! equ 0 (
    set "ruff_cmd=uv tool run ruff"
    exit /b 0
)
exit /b 0

:finish
echo.
if !failed! neq 0 (
    echo Static analysis FAILED.
    endlocal & exit /b 1
)
echo Static analysis passed.
endlocal & exit /b 0
