@echo off
setlocal EnableDelayedExpansion

rem ──────────────────────  Graphify: per-module knowledge graph pipeline  ────
rem Usage:
rem   scripts\graphify\graphify.bat            Full pipeline
rem   scripts\graphify\graphify.bat --clean    Purge old graph data only
rem   scripts\graphify\graphify.bat --module X Re-extract a single module
rem   scripts\graphify\graphify.bat [graphify CLI args...]  Delegate to graphify CLI

set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%..\.."
rem graphify honors a GRAPHIFY_OUT env var; clear any inherited value so
rem per-module extractions write to apps/<module>/graphify-out, not the root.
set "GRAPHIFY_OUT="
set "GRAPHIFY_OUT_DIR=%ROOT_DIR%\graphify-out"
set "EDGES_FILE=%GRAPHIFY_OUT_DIR%\cross-module-edges.json"

rem ──────────────────────  Parse arguments  ──────────────────────────────────
set "first_arg=%~1"
set "second_arg=%~2"
set "clean=0"
set "single_module="

:parse_args
if "%~1"=="" goto :done_args
if /i "%~1"=="--clean" (
    set "clean=1"
    shift
    goto :parse_args
)
if /i "%~1"=="--module" (
    shift
    set "single_module=%~1"
    shift
    goto :parse_args
)
for /f "tokens=1,2 delims==" %%a in ("%~1") do (
    if /i "%%a"=="--module" set "single_module=%%b"
)
shift
goto :parse_args
:done_args

rem ──────────────────────  CLI passthrough  ──────────────────────────────────
rem Read-only/meta subcommands are delegated verbatim to the graphify CLI.
set "PASSTHROUGH=0"
for %%c in (query path explain) do (
    if /i "%first_arg%"=="%%c" set "PASSTHROUGH=1"
)
if "%first_arg%"=="--help" set "PASSTHROUGH=1"
if "%first_arg%"=="-h" set "PASSTHROUGH=1"
if "%first_arg%"=="--version" set "PASSTHROUGH=1"
if "%PASSTHROUGH%"=="1" goto :delegate_plain
rem `export html` maps to the repo custom generator - the upstream export would
rem overwrite graphify-out/graph.html with the default single-graph visualization.
if /i "%first_arg%"=="export" if /i "%second_arg%"=="html" goto :delegate_html_gen
rem Graph/HTML-mutating subcommands and URLs are delegated, then the wrapper
rem re-runs the custom generator so graph.html stays module-grouped.
set "PASSTHROUGH=0"
for %%c in (update cluster-only add export extract merge-graphs) do (
    if /i "%first_arg%"=="%%c" set "PASSTHROUGH=1"
)
if /i "!first_arg:~0,5!"=="http:" set "PASSTHROUGH=1"
if /i "!first_arg:~0,6!"=="https:" set "PASSTHROUGH=1"
if "%PASSTHROUGH%"=="1" goto :delegate_restore
goto :after_delegation

:delegate_plain
echo Delegating to graphify CLI: graphify %*
graphify %*
exit /b !errorlevel!

:delegate_html_gen
echo Regenerating custom graph.html ^(repo generator^)...
python "%SCRIPT_DIR%graphify-html-grouped.py" --graph "%GRAPHIFY_OUT_DIR%\graph.json" --out "%GRAPHIFY_OUT_DIR%\graph.html"
exit /b !errorlevel!

:delegate_restore
echo Delegating to graphify CLI: graphify %*
graphify %*
set "code=!errorlevel!"
python "%SCRIPT_DIR%graphify-html-grouped.py" --graph "%GRAPHIFY_OUT_DIR%\graph.json" --out "%GRAPHIFY_OUT_DIR%\graph.html" >nul 2>&1
exit /b !code!

:after_delegation

rem ──────────────────────  Clean function  ───────────────────────────────────
if "%clean%"=="1" goto :do_clean

rem ──────────────────────  Single module mode  ──────────────────────────────
if not "%single_module%"=="" (
    echo Re-extracting module: %single_module%
    call :extract_module "%single_module%"
    goto :do_merge
)

rem ──────────────────────  Full pipeline  ────────────────────────────────────
call :do_clean_func

echo.
echo Extracting modules...
rem commonlib first (dependency for all others)
call :extract_module "commonlib"

rem remaining modules
for /d %%a in (%ROOT_DIR%\apps\*) do (
    set "mdir=%%~nxa"
    if /i not "!mdir!"=="commonlib" if /i not "!mdir!"=="e2e" (
        call :extract_module "!mdir!"
    )
)

:do_merge
echo.
echo Collecting module graphs...
set "graph_files="
set "graph_count=0"
for /d %%a in (%ROOT_DIR%\apps\*) do (
    set "mdir=%%~nxa"
    if /i not "!mdir!"=="e2e" (
        if exist "%%~fa\graphify-out\graph.json" (
            set "graph_files=!graph_files! "%%~fa\graphify-out\graph.json""
            set /a graph_count+=1
        )
    )
)

if !graph_count! lss 2 (
    echo ERROR: Need at least 2 module graphs to merge ^(found !graph_count!^)
    exit /b 1
)

echo Merging !graph_count! graphs...
graphify merge-graphs !graph_files! --out "%GRAPHIFY_OUT_DIR%\graph.json"

echo.
echo Preserving raw merged graph...
copy "%GRAPHIFY_OUT_DIR%\graph.json" "%GRAPHIFY_OUT_DIR%\graph.raw.json" >nul

echo.
echo Filtering external dependency nodes...
python "%SCRIPT_DIR%graphify-filter-deps.py"

echo.
echo Injecting cross-module edges...
python "%SCRIPT_DIR%graphify-inject-edges.py"

echo.
echo Step 1 -- Assigning communities...
graphify cluster-only "%ROOT_DIR%" 2>nul

echo.
echo Step 2 -- Labeling communities...
python "%SCRIPT_DIR%graphify-label-communities.py"

echo.
echo Step 3 -- Finalizing report ^(Leiden clustering is non-deterministic, may shift communities^)...
graphify cluster-only "%ROOT_DIR%" 2>nul

echo.
echo Step 4 -- Re-labeling to capture any shifted communities...
python "%SCRIPT_DIR%graphify-label-communities.py" 2>nul

echo.
echo Step 5 -- Generating module-grouped graph.html...
python "%SCRIPT_DIR%graphify-html-grouped.py"

echo.
echo --------------------------------------------------------
echo Graph complete. Outputs in %GRAPHIFY_OUT_DIR%
echo.
echo   graph.html          - interactive graph grouped by module, open in browser
echo   GRAPH_REPORT.md     - architecture audit report
echo   graph.json          - post-processed graph data
echo   graph.raw.json      - raw merged graph ^(before filtering/injection/clustering^)
echo   cross-module-edges.json - edge definitions ^(editable^)
echo --------------------------------------------------------
exit /b

rem ═══════════════════════════════════════════════════════════════════════════
rem  Subroutines
rem ═══════════════════════════════════════════════════════════════════════════

:do_clean
call :do_clean_func
echo.
echo Clean complete.
exit /b

:do_clean_func
echo Cleaning graphify-out/...
if exist "%GRAPHIFY_OUT_DIR%" (
    rem Preserve cross-module-edges.json
    if exist "%EDGES_FILE%" (
        copy "%EDGES_FILE%" "%TEMP%\cross-module-edges-backup.json" >nul
    )
    rmdir /s /q "%GRAPHIFY_OUT_DIR%"
    mkdir "%GRAPHIFY_OUT_DIR%"
    if exist "%TEMP%\cross-module-edges-backup.json" (
        move "%TEMP%\cross-module-edges-backup.json" "%EDGES_FILE%" >nul
    )
    echo   Cleaned. ^(cross-module-edges.json preserved^)
) else (
    mkdir "%GRAPHIFY_OUT_DIR%"
    echo   Created graphify-out/
)
rem Clean per-module extraction outputs
for /d %%a in (%ROOT_DIR%\apps\*) do (
    if exist "%%~fa\graphify-out" (
        rmdir /s /q "%%~fa\graphify-out"
    )
)
echo   Cleaned per-module graphify-out/ directories
exit /b

:extract_module
set "module=%~1"
set "mdir=%ROOT_DIR%\apps\%module%"
if not exist "%mdir%" (
    echo   SKIP: apps\%module% does not exist
    exit /b
)
echo.
echo Extracting %module%...
graphify extract "%mdir%" --no-cluster --code-only
if !errorlevel! neq 0 (
    echo   WARN: %module% extraction failed ^(continuing^)
) else (
    echo   OK: %module%
)
exit /b
