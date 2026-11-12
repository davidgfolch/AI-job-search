@echo off
setlocal EnableDelayedExpansion
rem ===== AI Job Search parallel development workflow (Windows) =====
rem Usage: scripts\dev.bat <command> [args]  - same commands as scripts/dev.sh
rem   new <name>              - clone ..\ai_job_search-<name>, branch feat/<name> from the gate branch, copy env + lockfiles
rem   dep <pr>                - clone ..\ai_job_search-dependabot-<pr> and check out that PR (used by dependabot-agent)
rem   list                    - show sibling clones
rem   checkout <branch>       - switch branch in the current clone
rem   test [modules]          - run scripts\test.bat here (no args = everything)
rem   sandbox <service> [...] - run scripts\test-sandbox.bat here
rem   commit "msg"            - git add -A && git commit
rem   push                    - push the current branch (never staging/master)
rem   pr [title] [--base br]  - open a PR (default base: the staging gate)
rem   merge [-k]              - wait for green checks, squash-merge, delete branch and clone (keep clone with -k)
rem   sync                    - fast-forward staging from master and push it (run before dependabot work)
rem   cleanup <name|path>     - delete a sibling clone by name, prefixed name, or path
rem   status                  - branch, dirty state, ahead/behind vs the gate branch

for %%i in ("%~dp0..") do set "ROOT=%%~fi"
pushd "%ROOT%\.."
set "PARENT=%CD%"
popd
set "PREFIX=ai_job_search-"
if not defined DEV_GATE_BRANCH set "DEV_GATE_BRANCH=staging"
if not defined DEV_MAIN_BRANCH set "DEV_MAIN_BRANCH=master"

set "CMD=%~1"
if "%CMD%"=="" goto usage
if /i "%CMD%"=="new" goto cmd_new
if /i "%CMD%"=="dep" goto cmd_dep
if /i "%CMD%"=="list" goto cmd_list
if /i "%CMD%"=="checkout" goto cmd_checkout
if /i "%CMD%"=="test" goto cmd_test
if /i "%CMD%"=="sandbox" goto cmd_sandbox
if /i "%CMD%"=="commit" goto cmd_commit
if /i "%CMD%"=="push" goto cmd_push
if /i "%CMD%"=="pr" goto cmd_pr
if /i "%CMD%"=="merge" goto cmd_merge
if /i "%CMD%"=="auto-merge" goto cmd_merge
if /i "%CMD%"=="sync" goto cmd_sync
if /i "%CMD%"=="cleanup" goto cmd_cleanup
if /i "%CMD%"=="status" goto cmd_status
goto usage

:curbranch
set "BR="
for /f "delims=" %%i in ('git rev-parse --abbrev-ref HEAD') do set "BR=%%i"
exit /b 0

:create_clone
set "CLONE=%PARENT%\%PREFIX%%~1"
if exist "!CLONE!" (
    echo Reusing clone: !CLONE!
) else (
    for /f "delims=" %%i in ('git remote get-url origin') do set "ORIGIN=%%i"
    echo Cloning !ORIGIN! to !CLONE!...
    git clone "!ORIGIN!" "!CLONE!"
    if errorlevel 1 (echo Error: clone failed. & exit /b 1)
)
if exist "%ROOT%\.env" if not exist "!CLONE!\.env" copy /Y "%ROOT%\.env" "!CLONE!\.env" >nul
if exist "%ROOT%\.env.secrets" if not exist "!CLONE!\.env.secrets" copy /Y "%ROOT%\.env.secrets" "!CLONE!\.env.secrets" >nul
for /d %%m in ("%ROOT%\apps\*") do (
    for %%f in (uv.lock poetry.lock package-lock.json) do (
        if exist "%%~fm\%%f" if not exist "!CLONE!\apps\%%~nxm\%%f" (
            if not exist "!CLONE!\apps\%%~nxm\" mkdir "!CLONE!\apps\%%~nxm\"
            copy /Y "%%~fm\%%f" "!CLONE!\apps\%%~nxm\%%f" >nul
        )
    )
)
exit /b 0

:cmd_new
set "NAME=%~2"
if "%NAME%"=="" goto usage
for %%i in ("%NAME%") do set "NAME=%%~nxi"
if /i "!NAME:~0,14!"=="%PREFIX%" set "NAME=!NAME:%PREFIX%=!"
call :create_clone "!NAME!"
cd /d "!CLONE!" || exit /b 1
git fetch origin >nul 2>&1
set "BRANCH=feat/!NAME!"
git checkout -b "!BRANCH!" "origin/!DEV_GATE_BRANCH!" 2>nul
if errorlevel 1 git checkout -b "!BRANCH!" "origin/!DEV_MAIN_BRANCH!" 2>nul
if errorlevel 1 git checkout "!BRANCH!"
if errorlevel 1 (echo Error: could not set branch !BRANCH!. & exit /b 1)
echo.
echo Clone ready: !CLONE!
echo Branch: !BRANCH!
exit /b 0

:cmd_dep
set "PR=%~2"
if "%PR%"=="" goto usage
set "PR=!PR:#=!"
where gh >nul 2>&1 || (echo Error: 'gh' CLI is required. Install GitHub CLI and authenticate. & exit /b 1)
call :create_clone "dependabot-!PR!"
cd /d "!CLONE!" || exit /b 1
gh pr checkout !PR!
if errorlevel 1 exit /b 1
echo.
echo Clone ready: !CLONE! ^(PR #!PR! checked out^)
exit /b 0

:cmd_list
echo Sibling clones under %PARENT%:
set "FOUND="
for /d %%d in ("%PARENT%\%PREFIX%*") do (
    if /i not "%%~fd"=="%ROOT%" ( echo   %%~nxd & set "FOUND=1" )
)
if not defined FOUND echo   (none)
exit /b 0

:cmd_checkout
if "%~2"=="" goto usage
git checkout %~2
exit /b 0

:cmd_test
shift
if "%~1"=="" (cd /d "%ROOT%" && call scripts\test.bat) else (cd /d "%ROOT%" && call scripts\test.bat %*)
exit /b %errorlevel%

:cmd_sandbox
shift
if "%~1"=="" goto usage
cd /d "%ROOT%" && call scripts\test-sandbox.bat %*
exit /b %errorlevel%

:cmd_commit
if "%~2"=="" (echo Usage: scripts\dev.bat commit "message" & exit /b 1)
git add -A
git commit -m "%~2"
exit /b %errorlevel%

:cmd_push
call :curbranch
if /i "!BR!"=="%DEV_GATE_BRANCH%" (echo Refusing to push !BR! directly. & exit /b 1)
if /i "!BR!"=="%DEV_MAIN_BRANCH%" (echo Refusing to push !BR! directly. & exit /b 1)
git push -u origin "!BR!"
exit /b %errorlevel%

:cmd_pr
set "BASE=%DEV_GATE_BRANCH%"
set "TITLE=%~2"
if /i "%~2"=="--base" (set "BASE=%~3" & set "TITLE=%~4")
where gh >nul 2>&1 || (echo Error: 'gh' CLI is required. & exit /b 1)
call :curbranch
if /i "!BR!"=="%DEV_GATE_BRANCH%" (echo Refusing to open a PR from !BR!. & exit /b 1)
if /i "!BR!"=="%DEV_MAIN_BRANCH%" (echo Refusing to open a PR from !BR!. & exit /b 1)
if not defined TITLE for /f "delims=" %%i in ('git log -1 --pretty^=%%s') do set "TITLE=%%i"
gh pr create --base "!BASE!" --head "!BR!" --title "!TITLE!" --body "Automated PR from the dev workflow for branch !BR! (base !BASE!)."
exit /b %errorlevel%

:cmd_merge
set "KEEP=%~2"
where gh >nul 2>&1 || (echo Error: 'gh' CLI is required. & exit /b 1)
call :curbranch
if /i "!BR!"=="%DEV_GATE_BRANCH%" (echo Cannot merge from !BR!. Run inside a feature/dependabot clone. & exit /b 1)
if /i "!BR!"=="%DEV_MAIN_BRANCH%" (echo Cannot merge from !BR!. & exit /b 1)
set "PRNUM="
for /f "delims=" %%i in ('gh pr list --head "!BR!" --json number --jq ".[0].number"') do set "PRNUM=%%i"
if "!PRNUM!"=="" (echo Error: no open PR found for branch !BR!. & exit /b 1)
echo Waiting for PR #!PRNUM! checks to be green...
gh pr checks !PRNUM! --watch
if errorlevel 1 (echo PR checks did not pass. Clone kept for inspection. & exit /b 1)
set "MERGEABLE="
for /f "delims=" %%i in ('gh pr view !PRNUM! --json mergeable --jq ".mergeable"') do set "MERGEABLE=%%i"
if not "!MERGEABLE!"=="MERGEABLE" (
    echo PR is not mergeable; attempting to auto-resolve conflicts...
    git fetch origin
    git rebase "origin/!DEV_GATE_BRANCH!"
    if errorlevel 1 (git rebase --abort & echo Could not auto-resolve conflicts. Clone kept. & exit /b 1)
    git push --force-with-lease origin "!BR!"
    if errorlevel 1 (echo Push after rebase failed. Clone kept. & exit /b 1)
)
gh pr merge !PRNUM! --squash --delete-branch
if errorlevel 1 (echo PR merge failed. Clone kept for inspection. & exit /b 1)
set "STATE="
for /f "delims=" %%i in ('gh pr view !PRNUM! --json state --jq ".state"') do set "STATE=%%i"
if not "!STATE!"=="MERGED" (echo PR state is !STATE!, expected MERGED. Clone kept. & exit /b 1)
echo PR merged.
if /i "!KEEP!"=="-k" (echo Keeping clone: %CD% & exit /b 0)
pushd "%CD%\.."
call :delete_clone "%CD%"
popd
exit /b 0

:cmd_sync
cd /d "%ROOT%" || exit /b 1
git fetch origin
git checkout %DEV_GATE_BRANCH%
git pull --ff-only origin %DEV_GATE_BRANCH%
for /f "delims=" %%i in ('git rev-parse HEAD') do set "BEFORE=%%i"
git merge --ff-only origin/%DEV_MAIN_BRANCH%
if errorlevel 1 (echo Error: %DEV_GATE_BRANCH% and %DEV_MAIN_BRANCH% diverged. Resolve manually. & exit /b 1)
for /f "delims=" %%i in ('git rev-parse HEAD') do set "AFTER=%%i"
if not "!BEFORE!"=="!AFTER!" (
    git push origin %DEV_GATE_BRANCH%
    echo %DEV_GATE_BRANCH% fast-forwarded to %DEV_MAIN_BRANCH% and pushed.
) else (
    echo %DEV_GATE_BRANCH% already contains %DEV_MAIN_BRANCH%.
)
exit /b 0

:cmd_cleanup
set "NAME=%~2"
if "%NAME%"=="" goto usage
set "TARGET=%PARENT%\%PREFIX%%!NAME!"
if not exist "!TARGET!\" (
    echo Nothing to clean: '!NAME!' does not resolve to an existing clone under %PARENT%.
    goto cmd_list
)
pushd "%TARGET%\.."
call :delete_clone "%CD%"
popd
exit /b %errorlevel%

:delete_clone
rem Guard: sibling dir named ai_job_search-*, never the main workspace, and a git clone.
set "TARGET=%~1"
for %%i in ("%TARGET%") do set "CLONENAME=%%~nxi"
echo !CLONENAME!| findstr /b /c:"%PREFIX%" >nul || (echo Refusing to delete %TARGET% (not an %PREFIX%* sibling clone) & exit /b 1)
pushd "%TARGET%\.."
if /i not "%CD%"=="%PARENT%" (echo Refusing to delete %TARGET% (not a sibling of %PARENT%) & popd & exit /b 1)
popd
git -C "%TARGET%" rev-parse --is-inside-work-tree >nul 2>&1 || (echo Not a git clone: %TARGET% & exit /b 1)
if exist "%TARGET%\.codegraph\daemon.pid" (
    for /f "tokens=2 delims=:," %%p in ('findstr /c:"\"pid\"" "%TARGET%\.codegraph\daemon.pid"') do (
        for /f "tokens=* delims= " %%q in ("%%p") do taskkill /PID %%q /F >nul 2>&1
    )
)
echo Deleting clone %TARGET%...
rmdir /S /Q "%TARGET%"
if exist "%TARGET%\" (echo Error: could not delete %TARGET%. & exit /b 1)
echo Clone deleted.
exit /b 0

:cmd_status
call :curbranch
echo Branch: !BR!
echo.
git status --short
echo.
git rev-list --left-right --count "origin/%DEV_GATE_BRANCH%...HEAD"
exit /b 0

:usage
echo Usage: scripts\dev.bat ^<command^> [args]
echo   new ^<name^>  dep ^<pr^>  list  checkout ^<branch^>  test [modules]  sandbox ^<service^>
echo   commit "msg"  push  pr [title] [--base br]  merge [-k]  sync  cleanup ^<name^>  status
exit /b 1
