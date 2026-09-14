@echo off
setlocal enabledelayedexpansion

echo.
echo Installing graphify...
uv tool install graphifyy
uv tool install "graphifyy[ollama]"
uv tool install "graphifyy[openai]"
uv tool install "graphifyy[sql]"
call :ollama_pull qwen2.5-coder:7b
call :ollama_pull qwen2.5:3b
graphify install --project --platform opencode
graphify . --backend ollama
git add .claude/ .opencode/ AGENTS.md

echo.
echo Installing commonlib...
pushd apps\commonlib
call poetry lock
call poetry install
popd

for /d %%a in (apps\*) do (
    if /i not "%%~nxa"=="commonlib" (
        echo.
        echo Installing %%~na...
        if exist "%%~fa\package.json" (
            pushd "%%~fa"
            call npm install
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
        ) else (
            pushd "%%~fa"
            call poetry lock
            call poetry install
            popd
        )
    )
)

exit /b 0

:ollama_pull
set "MODEL=%~1"
set "RUN_CMD=ollama"
set "HF_SPEC="
for /f %%i in ('docker ps -q --filter "name=ai-job-search-ollama" 2^>nul') do set "CID=%%i"
if defined CID (
    set "RUN_CMD=docker exec !CID! ollama"
) else (
    where ollama >nul 2>&1
    if not !ERRORLEVEL! equ 0 (
        echo WARNING: Ollama not found. Pull !MODEL! manually using host 'ollama pull !MODEL!' or dockerized 'docker exec ai-job-search-ollama ollama pull !MODEL!'.
        exit /b 0
    )
)
if /i "!MODEL!"=="qwen2.5:3b" set "HF_SPEC=hf.co/Qwen/Qwen2.5-3B-Instruct-GGUF:q4_k_m"
if /i "!MODEL!"=="qwen2.5-coder:7b" set "HF_SPEC=hf.co/bartowski/Qwen2.5-Coder-7B-Instruct-GGUF:Q4_K_M"
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
) else (
    echo Pulling !MODEL! via !RUN_CMD!...
    !RUN_CMD! pull "!MODEL!"
)
exit /b 0
