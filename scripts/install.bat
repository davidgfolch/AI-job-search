@echo off

echo.
echo Installing graphify...
uv tool install graphifyy
uv tool install "graphifyy[ollama]"
uv tool install "graphifyy[openai]"
uv tool install "graphifyy[sql]"
ollama pull qwen2.5-coder:7b
graphify install --project --platform opencode
graphify . --backend ollama
git add .opencode/ AGENTS.md

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
