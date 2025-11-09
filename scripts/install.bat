@echo off

for /d %%a in (packages\* apps\*) do (
    echo.
    echo Installing %%~na...
    if "%%a" == "apps\aiEnrich" (
        @REM cd "%%a" && set UV_PROJECT_ENVIRONMENT=custom-venv && uv sync && uv tool install --force crewai && cd ..\..
        cd "%%a" && uv sync && uv tool install --force crewai && cd ..\..
    ) else (
        cd "%%a" && poetry lock && poetry install && cd ..\..
    )
)
