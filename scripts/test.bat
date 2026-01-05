@echo off
setlocal EnableDelayedExpansion
set VIRTUAL_ENV=

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
rem ──────────────────────  Execute tests  ─────────────────────
if exist "apps\commonlib" (
    call :run_test "%CD%\apps\commonlib"
)

for /d %%a in (apps\*) do (
    if /i not "%%~nxa"=="commonlib" (
        call :run_test "%%~fa"
    )
)

endlocal
exit /b

:run_test
set "target_dir=%~1"
echo.
echo Testing %~nx1...
pushd "!target_dir!"
if exist "package.json" (
    if !coverage!==0 (
        call npm test -- run
    ) else (
        call npm test -- run --coverage
        call npx coverage-badges
    )
) else if exist "pyproject.toml" (
    if exist "uv.lock" (
        @REM set "UV_PROJECT_ENVIRONMENT=custom-venv"
        if !coverage!==0 (
            uv run -m pytest
        ) else (
            uv run -m coverage run -m pytest
            uv run -m coverage report -m
            uv run -m coverage xml
            uv run python -m coverage_badge -o coverage.svg -f
        )
    ) else (
        if !coverage!==0 (
            poetry run pytest
        ) else (
            poetry run coverage run -m pytest
            poetry run coverage report -m
            poetry run coverage xml
            poetry run coverage-badge -o coverage.svg -f
        )
    )
) else (
    echo No known project type found in %~nx1
)
popd
exit /b

endlocal
