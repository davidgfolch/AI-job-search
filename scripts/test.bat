@echo off
setlocal EnableDelayedExpansion
set VIRTUAL_ENV=

rem ──────────────────────  Parse command‑line  ─────────────────────
set coverage=0
set idx=0
set "target="

for %%i in (%*) do (
    set /a idx+=1
    echo Arguments !idx!: %%i
    if "%%i"=="--coverage" (
        set coverage=1
        echo Coverage enabled
    ) else if exist "%%i" (
        set "target=%%i"
    )
)

rem ──────────────────────  Execute tests  ─────────────────────
rem ──────────────────────  Execute tests  ─────────────────────
if defined target (
     call :run_test "%CD%\!target!"
) else (
    if exist "apps\commonlib" (
        call :run_test "%CD%\apps\commonlib"
    )

    for /d %%a in (apps\*) do (
        if /i not "%%~nxa"=="commonlib" (
            call :run_test "%%~fa"
        )
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
        call npx coverage-badges --label "%~nx1"
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
            uv run genbadge coverage -i coverage.xml -o coverage.svg -n "%~nx1"
        )
    ) else (
        if !coverage!==0 (
            poetry run pytest
        ) else (
            poetry run coverage run -m pytest
            poetry run coverage report -m
            poetry run coverage xml
            poetry run genbadge coverage -i coverage.xml -o coverage.svg -n "%~nx1"
        )
    )
) else (
    echo No known project type found in %~nx1
)
popd
exit /b

endlocal
