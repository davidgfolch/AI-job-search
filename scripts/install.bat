@echo off
setlocal enabledelayedexpansion

echo.
echo Installing commonlib...
pushd apps\commonlib
call poetry lock
call poetry install
popd

echo.
echo Pulling Ollama models...
rem Resolve the Ollama server the same way the AI modules do (configured URL ->
rem host.docker.internal -> localhost -> compose service -> LAN scan) so models
rem land on the host that will serve them, including a server on the LAN.
call :ollama_resolve_url
if defined OLLAMA_HOST echo Ollama server: %OLLAMA_HOST%
call :ollama_pull qwen2.5:3b

echo.
echo Installing CodeGraph (default code intelligence)...
echo   powershell -Command "irm https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.ps1 | iex"
powershell -Command "irm https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.ps1 | iex"
if !ERRORLEVEL! equ 0 (
    echo codegraph installed.
    rem The PowerShell installer updates the user PATH, which this cmd.exe session
    rem already inherited, so call the installed launcher directly.
    set "CODEGRAPH_CMD=%LOCALAPPDATA%\codegraph\current\bin\codegraph.cmd"
    if exist "!CODEGRAPH_CMD!" (
        rem --yes runs non-interactively against the global agent configs and the
        rem auto-detected agents; --init builds this project's .codegraph index.
        echo Wiring codegraph into the detected agents and indexing this project...
        call "!CODEGRAPH_CMD!" install --yes --init
        if !ERRORLEVEL! equ 0 (
            echo codegraph agent setup and project indexing done.
        ) else (
            echo WARNING: codegraph agent setup or indexing failed; run 'codegraph install --yes --init' later.
        )
    ) else (
        echo WARNING: codegraph installed but its launcher was not found at !CODEGRAPH_CMD!. Open a new terminal and run: codegraph install --yes --init
    )
) else (
    echo WARNING: codegraph install failed; continuing without it. Install manually with: powershell -Command "irm https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.ps1 | iex"
)

echo.
echo Installing Crawlee...
uv tool install "crawlee[all]"

for /d %%a in (apps\*) do (
    if /i not "%%~nxa"=="commonlib" (
        echo.
        echo Installing %%~na...
        if exist "%%~fa\package.json" (
            pushd "%%~fa"
            call npm install
            REM The e2e module uses Playwright: install its browser binaries and OS deps.
            if /i "%%~na"=="e2e" (
                call npx playwright install
                call npx playwright install-deps || echo WARNING: 'npx playwright install-deps' failed; run it manually (as admin) for e2e browsers.
            )
            popd
        ) else if "%%~nxa" == "aiFormFiller" (
            pushd "%%~fa"
            call uv sync
            popd
        ) else if "%%~nxa" == "aiEnrich" (
            pushd "%%~fa"
            call uv sync
            popd
        ) else if "%%~nxa" == "aiEnrichNew" (
            pushd "%%~fa"
            call uv sync
            popd
        ) else if "%%~nxa" == "backend" (
            pushd "%%~fa"
            call uv sync
            popd
        ) else if "%%~nxa" == "aiCvMatcher" (
            pushd "%%~fa"
            call uv sync
            popd
        ) else if "%%~nxa" == "aiEnrich3" (
            pushd "%%~fa"
            call uv sync
            popd
        ) else if "%%~nxa" == "aiEnrichSkill" (
            pushd "%%~fa"
            call uv sync
            popd
        ) else if "%%~nxa" == "cron" (
            pushd "%%~fa"
            call uv sync
            popd
        ) else (
            pushd "%%~fa"
            call poetry lock
            call poetry install
            popd
        )
    )
)

exit /b 0

rem Resolve the Ollama server via commonlib discovery (source tree; no install needed).
:ollama_resolve_url
set "RESOLVED_URL="
echo from commonlib.ollama_client import resolve_ollama_url > "%TEMP%\install-ollama-resolve.py"
echo from commonlib.ollama_config import get_configured_ollama_url >> "%TEMP%\install-ollama-resolve.py"
echo import os >> "%TEMP%\install-ollama-resolve.py"
echo print(resolve_ollama_url(os.environ.get('OLLAMA_HOST') or get_configured_ollama_url()) or '') >> "%TEMP%\install-ollama-resolve.py"
pushd apps\commonlib
for /f "delims=" %%i in ('poetry run python "%TEMP%\install-ollama-resolve.py" 2^>nul') do set "RESOLVED_URL=%%i"
popd
if defined RESOLVED_URL set "OLLAMA_HOST=%RESOLVED_URL%"
del "%TEMP%\install-ollama-resolve.py" 2>nul
exit /b 0

:ollama_pull
set "MODEL=%~1"
call :ollama_has_model "!MODEL!"
if !ERRORLEVEL! equ 0 (
    echo !MODEL! already present on the Ollama server; skipping the download.
    exit /b 0
)
set "RUN_CMD=ollama"
set "HF_SPEC="
set "REMOTE_HOST=%OLLAMA_HOST%"
for /f %%i in ('docker ps -q --filter "name=ai-job-search-ollama" 2^>nul') do set "CID=%%i"
if defined CID (
    set "RUN_CMD=docker exec !CID! ollama"
) else (
    where ollama >nul 2>&1
    if not !ERRORLEVEL! equ 0 (
        rem No local CLI and no container: try a remote Ollama host over HTTP.
        if defined REMOTE_HOST (
            echo Pulling !MODEL! via remote Ollama host !REMOTE_HOST!...
            if /i "!MODEL!"=="qwen2.5:3b" set "HF_SPEC=hf.co/Qwen/Qwen2.5-3B-Instruct-GGUF:q4_k_m"
            if defined HF_SPEC (
                echo {"name": "!HF_SPEC!"} > "%TEMP%\install-ollama-pull.json"
                curl.exe -s -m 120 -X POST "!REMOTE_HOST!/api/pull" -H "Content-Type: application/json" -d "@%TEMP%\install-ollama-pull.json" >nul 2>&1
                if !ERRORLEVEL! equ 0 (
                    echo {"source": "!HF_SPEC!", "destination": "!MODEL!"} > "%TEMP%\install-ollama-cp.json"
                    echo {"name": "!HF_SPEC!"} > "%TEMP%\install-ollama-rm.json"
                    curl.exe -s -m 120 -X POST "!REMOTE_HOST!/api/cp" -H "Content-Type: application/json" -d "@%TEMP%\install-ollama-cp.json" >nul 2>&1 || true
                    curl.exe -s -m 120 -X POST "!REMOTE_HOST!/api/delete" -H "Content-Type: application/json" -d "@%TEMP%\install-ollama-rm.json" >nul 2>&1 || true
                )
            ) else (
                echo {"name": "!MODEL!"} > "%TEMP%\install-ollama-pull.json"
                curl.exe -s -m 120 -X POST "!REMOTE_HOST!/api/pull" -H "Content-Type: application/json" -d "@%TEMP%\install-ollama-pull.json" >nul 2>&1
            )
            if !ERRORLEVEL! equ 0 exit /b 0
            echo WARNING: could not pull !MODEL! from remote Ollama host !REMOTE_HOST!; continuing.
        )
        echo WARNING: Ollama not found. Pull !MODEL! manually using host 'ollama pull !MODEL!' or dockerized 'docker exec ai-job-search-ollama ollama pull !MODEL!'.
        exit /b 0
    )
)
if /i "!MODEL!"=="qwen2.5:3b" set "HF_SPEC=hf.co/Qwen/Qwen2.5-3B-Instruct-GGUF:q4_k_m"
set "R2_OK=1"
if /i "!OLLAMA_PULL_SOURCE!"=="hf" set "R2_OK=0"
if /i "!OLLAMA_PULL_SOURCE!"=="ollama" set "R2_OK=1"
if not defined OLLAMA_PULL_SOURCE (
    curl.exe -s -m 5 -o NUL https://r2.cloudflarestorage.com/ >nul 2>&1
    if !ERRORLEVEL! neq 0 set "R2_OK=0"
)
if "!R2_OK!"=="1" (
    echo Pulling !MODEL! via !RUN_CMD!...
    !RUN_CMD! pull "!MODEL!"
) else if defined HF_SPEC (
    echo Ollama registry unreachable [r2.cloudflarestorage.com blocked] - pulling !MODEL! from HF [!HF_SPEC!] via !RUN_CMD!...
    !RUN_CMD! pull "!HF_SPEC!"
    if errorlevel 1 exit /b 0
    !RUN_CMD! cp "!HF_SPEC!" "!MODEL!"
    !RUN_CMD! rm "!HF_SPEC!"
) else (
    echo Pulling !MODEL! via !RUN_CMD!...
    !RUN_CMD! pull "!MODEL!"
)
exit /b 0

rem Check whether a model is already on the server (a remote LAN host included),
rem via 'ollama show' or the host's HTTP API, so a blocked registry does not
rem re-download a model that is already there from HuggingFace.
:ollama_has_model
set "CHECK_MODEL=%~1"
set "CID="
for /f %%i in ('docker ps -q --filter "name=ai-job-search-ollama" 2^>nul') do set "CID=%%i"
if defined CID (
    docker exec !CID! ollama show "!CHECK_MODEL!" >nul 2>&1
    if !ERRORLEVEL! equ 0 exit /b 0
    exit /b 1
)
where ollama >nul 2>&1
if !ERRORLEVEL! equ 0 (
    ollama show "!CHECK_MODEL!" >nul 2>&1
    if !ERRORLEVEL! equ 0 exit /b 0
    exit /b 1
)
if not defined OLLAMA_HOST exit /b 1
echo {"name": "!CHECK_MODEL!"} > "%TEMP%\install-ollama-show.json"
curl.exe -sf -m 10 -o NUL -X POST "!OLLAMA_HOST!/api/show" -H "Content-Type: application/json" -d "@%TEMP%\install-ollama-show.json" >nul 2>&1
set "SHOW_STATUS=!ERRORLEVEL!"
del "%TEMP%\install-ollama-show.json" 2>nul
if !SHOW_STATUS! equ 0 exit /b 0
exit /b 1
