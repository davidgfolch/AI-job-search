@echo off

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
        ) else if "%%~nxa" == "aiEnrich" (
            pushd "%%~fa"
            call uv sync
            call uv tool install --force crewai
            popd
        ) else if "%%~nxa" == "aiEnrichNew" (
            pushd "%%~fa"
            call uv sync
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
)
