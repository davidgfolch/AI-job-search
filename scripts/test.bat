@echo off
setlocal EnableDelayedExpansion
set VIRTUAL_ENV=

rem ──────────────────────  Parse command‑line  ─────────────────────
set coverage=0
set idx=0

set "targets="
set "app_args="

for %%i in (%*) do (
    set /a idx+=1
    echo Arguments !idx!: %%i
    if "%%i"=="--coverage" (
        set coverage=1
        echo Coverage enabled
    ) else (
        if exist "%%i" (
            set "targets=!targets! %%i"
        ) else if exist "apps\%%i" (
            set "targets=!targets! apps\%%i"
        ) else (
            set "app_args=!app_args! %%i"
        )
    )
)

rem Drop the separator space added while accumulating targets, so %~nx1 in :run_test
rem resolves to the plain module name (e.g. "scrapper") and the per-module gates match.
if defined targets set "targets=%targets:~1%"

rem ──────────────────────  Execute tests  ─────────────────────
rem goto-based control flow on purpose: deeply nested if/else + for + call blocks lose
rem statement synchronisation in cmd, which silently skipped the failure check below.
if "%targets%"=="" goto :all_modules

set "tests_failed=0"
for %%t in (!targets!) do (
    if /i "%%~t"=="apps\e2e" goto :run_e2e_specific
    if /i "%%~t"=="apps/e2e" goto :run_e2e_specific
    call :run_test "%%~t"
    if !errorlevel! neq 0 set tests_failed=1
)
if !tests_failed! neq 0 goto :failed
goto :gates

:all_modules
rem Execute commonlib tests first
set "tests_failed=0"
if exist "apps\commonlib" (
    call :run_test "%CD%\apps\commonlib"
    if !errorlevel! neq 0 set tests_failed=1
)

rem Execute other apps tests
for /d %%a in (apps\*) do (
    if /i not "%%~nxa"=="commonlib" if /i not "%%~nxa"=="e2e" call :run_module "%%~fa"
    if !errorlevel! neq 0 set tests_failed=1
)

if !tests_failed! neq 0 goto :skip_e2e
echo.
echo --------------------------------------------------------
echo Unit tests passed. Running E2E tests...
echo --------------------------------------------------------
pushd "apps\e2e"
call npm test
set "e2e_code=!errorlevel!"
popd
if !e2e_code! neq 0 goto :failed
goto :gates

:skip_e2e
echo.
echo Skipping E2E tests because unit tests failed.
goto :failed

:gates
rem ────────────────────  Frontend coverage gate  ────────────────────
rem Gates the union of web unit (vitest) and e2e (monocart) coverage, which is the
rem metric the project enforces. Needs both summaries, so it only runs with --coverage.
call :frontend_gate
if !errorlevel! neq 0 goto :failed

endlocal
exit /b 0

:failed
endlocal
exit /b 1

:frontend_gate
if !coverage!==0 goto :eof
echo.
echo Gating frontend coverage (web unit + e2e union)...
node "%~dp0coverage\frontend-coverage-gate.mjs" --min 90
exit /b %errorlevel%

:run_e2e_specific
echo.
echo --------------------------------------------------------
echo Running E2E tests for apps/e2e...
echo --------------------------------------------------------
pushd "apps\e2e"
call npm test %app_args%
set "e2e_code=!errorlevel!"
popd
if !e2e_code! neq 0 exit /b 1
call :frontend_gate
if !errorlevel! neq 0 exit /b 1
exit /b 0

:run_module
if not exist "%~1\package.json" if not exist "%~1\pyproject.toml" (
    echo Skipping %~nx1 (no package.json or pyproject.toml)
    exit /b 0
)
call :run_test "%~1"
exit /b %errorlevel%

:run_test
rem Flat goto dispatch: the previous nested if/else chain silently skipped the
rem coverage branch under cmd, so --coverage ran plain pytest and no gate ran.
set "target_dir=%~1"
for %%a in ("!target_dir!") do set "target_name=%%~nxa"
set "test_code=0"
echo.
echo Testing !target_name!...
pushd "!target_dir!" || exit /b 1
if exist "package.json" goto :run_js
if not exist "pyproject.toml" goto :run_unknown
if exist "uv.lock" goto :run_uv
if !coverage!==1 goto :run_poetry_coverage
poetry run pytest
set "test_code=!errorlevel!"
goto :run_finish

:run_js
if !coverage!==1 goto :run_js_coverage
call npx vitest run
set "test_code=!errorlevel!"
goto :run_finish

:run_js_coverage
call npm test -- run --coverage
set "test_code=!errorlevel!"
call npx coverage-badges --label "!target_name!" --source coverage/coverage-summary.json
goto :run_finish

:run_uv
if !coverage!==1 goto :run_uv_coverage
uv run -m pytest
set "test_code=!errorlevel!"
goto :run_finish

:run_uv_coverage
uv run -m coverage run -m pytest
set "test_code=!errorlevel!"
uv run -m coverage report -m
uv run -m coverage xml
uv run genbadge coverage -i coverage.xml -o coverage.svg -n "!target_name!"
goto :run_finish

:run_poetry_coverage
poetry run coverage run -m pytest
set "test_code=!errorlevel!"
poetry run coverage report -m
poetry run coverage xml
poetry run genbadge coverage -i coverage.xml -o coverage.svg -n "!target_name!"
if /i not "!target_name!"=="scrapper" goto :run_finish
poetry run python "%~dp0coverage\scrapper_coverage_gate.py" --xml coverage.xml
if !errorlevel! neq 0 set "test_code=1"
goto :run_finish

:run_unknown
echo No known project type found in !target_name!
set "test_code=1"

:run_finish
popd
exit /b !test_code!
