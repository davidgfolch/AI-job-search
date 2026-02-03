@echo off
setlocal EnableDelayedExpansion
set VIRTUAL_ENV=

rem ──────────────────────  Parse command‑line  ─────────────────────
set coverage=0
set idx=0
set "target="

set "app_args="

for %%i in (%*) do (
    set /a idx+=1
    echo Arguments !idx!: %%i
    if "%%i"=="--coverage" (
        set coverage=1
        echo Coverage enabled
    ) else if exist "%%i" (
        set "target=%%i"
    ) else (
        set "app_args=!app_args! %%i"
    )
)

rem ──────────────────────  Execute tests  ─────────────────────
if defined target (
    if /i "!target!"=="apps\e2e" goto :run_e2e_specific
    if /i "!target!"=="apps/e2e" goto :run_e2e_specific
    call :run_test "%CD%\!target!"
) else (
    rem Execute commonlib tests first
    if exist "apps\commonlib" (
        call :run_test "%CD%\apps\commonlib"
    )

    rem Execute other apps tests
    set "tests_failed=0"
    for /d %%a in (apps\*) do (
        if /i not "%%~nxa"=="commonlib" if /i not "%%~nxa"=="e2e" (
            call :run_test "%%~fa"
            if !errorlevel! neq 0 set tests_failed=1
        )
    )
    
    if !tests_failed!==0 (
        echo.
        echo --------------------------------------------------------
        echo Unit tests passed. Running E2E tests...
        echo --------------------------------------------------------
        if exist "apps\backend\uv.lock" (
            uv run --project apps/backend python scripts/run_e2e_tests.py
        ) else (
            python scripts/run_e2e_tests.py
        )
        if !errorlevel! neq 0 set tests_failed=1
    ) else (
        echo.
        echo Skipping E2E tests because unit tests failed.
    )

    if !tests_failed! neq 0 exit /b 1
)

endlocal
exit /b


:run_e2e_specific
echo.
echo --------------------------------------------------------
echo Running E2E tests for apps/e2e...
echo --------------------------------------------------------
if exist "apps\backend\uv.lock" (
    uv run --project apps/backend python scripts/run_e2e_tests.py !app_args!
) else (
    python scripts/run_e2e_tests.py !app_args!
)
if !errorlevel! neq 0 exit /b 1
exit /b

:run_test
set "target_dir=%~1"
echo.
echo Testing %~nx1...
pushd "!target_dir!"
if exist "package.json" (
    if !coverage!==0 (
        call npx vitest run
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
