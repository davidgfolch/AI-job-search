@echo off

for /d %%a in (packages\* apps\*) do (
    echo.
    echo Installing %%~na...
    if exist "%%~fa\package.json" (
        pushd "%%~fa"
        call npm install
        popd
    ) else if "%%~nxa" == "aiEnrich" (
        pushd "%%~fa"
        call uv sync
        call uv tool install --force crewai
        popd
    ) else if "%%~nxa" == "backend" (
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
