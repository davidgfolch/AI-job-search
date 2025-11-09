@echo off
setlocal EnableDelayedExpansion

rem ──────────────────────  Parse command‑line  ─────────────────────
set coverage=0
set idx=0
for %%i in (%*) do (
    set /a idx+=1
    echo Arguments !idx!: %%i
    if "%%i"=="--coverage" (
        set coverage=1
        echo Coverage enabled
    ) 
)

rem ──────────────────────  Execute tests  ─────────────────────
for /d %%a in (packages\* apps\*) do (
    echo.
    echo Testing %%~nxa...
    if "%%~nxa"=="aiEnrich" (
        pushd "%%~fa"
        @REM set "UV_PROJECT_ENVIRONMENT=custom-venv"
        if !coverage!==0 (
            uv run -m pytest
        ) else (
            uv run -m coverage run -m pytest
            uv run -m coverage report -m
            uv run -m coverage xml
            uv run coverage-badge -o coverage-badge.svg -f
        )
        popd
    ) else (
        pushd "%%~fa"
        if !coverage!==0 (
            poetry run pytest
        ) else (
            poetry run coverage run -m pytest
            poetry run coverage report -m
            poetry run coverage xml
            poetry run coverage-badge -o coverage-badge.svg -f
        )
        popd
    )
)

endlocal
