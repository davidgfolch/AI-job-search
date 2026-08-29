@echo off
setlocal EnableDelayedExpansion
rem Sandboxed docker verification for Dependabot upgrades (dependabot-agent).
rem Brings up the affected service(s) in an isolated 'dependabot-test' project so the
rem live ai-job-search-* stack and its data are never touched, then checks logs.
rem Usage: scripts\test-sandbox.bat <service|project> [--profile <name>] [--no-db-clone] [--keep]

set "PROJECT=dependabot-test"
set "FILES=-f docker-compose.yml -f docker-compose.test.override.yml"
set "SANDBOX_DIR=%CD%\.docker-sandbox"
set "BACKUP_SCRIPT=%CD%\scripts\mysql\backup.bat"

set "TARGET="
set "DB_CLONE=1"
set "KEEP=0"
set "PROFILE="
set "PROFILE_ARGS="
set "NEXT_IS_PROFILE=0"

for %%i in (%*) do (
    if "%%i"=="--no-db-clone" ( set DB_CLONE=0
    ) else if "%%i"=="--keep" ( set KEEP=1
    ) else if "%%i"=="--profile" ( set NEXT_IS_PROFILE=1
    ) else if "%%i"=="-p" ( set NEXT_IS_PROFILE=1
    ) else (
        if "!NEXT_IS_PROFILE!"=="1" ( set "PROFILE=%%i" & set "NEXT_IS_PROFILE=0"
        ) else ( set "TARGET=%%i" )
    )
)

if defined PROFILE ( set "PROFILE_ARGS=--profile %PROFILE%" )

if "%TARGET%"=="" (
    echo Usage: %~nx0 ^<service^|project^> [--profile ^<name^>] [--no-db-clone] [--keep]
    exit /b 1
)

rem Modules disabled in .env (all their *_JOB/*_SKILL/*_ENABLED flags false) get a build-only check.
set "CHECK_KEYS="
if "%TARGET%"=="aienrich" set "CHECK_KEYS=AI_ENRICH_JOB AI_ENRICH_SKILL"
if "%TARGET%"=="aienrichnew" set "CHECK_KEYS=AI_ENRICHNEW_JOB AI_ENRICHNEW_SKILL"
if "%TARGET%"=="aienrichskill" set "CHECK_KEYS=AI_ENRICHSKILL_ENABLED"
if "%TARGET%"=="aienrich3" set "CHECK_KEYS=AI_ENRICH3_JOB AI_ENRICH3_SKILL"
if "%TARGET%"=="aicvmatcher" set "CHECK_KEYS=AI_CVMATCHER_ENABLED"
if defined CHECK_KEYS (
    set "MODULE_DISABLED=1"
    for %%k in (%CHECK_KEYS%) do (
        for /f "delims=" %%l in ('findstr /b /c:"%%k=" "%CD%\.env"') do (
            set "VAL=%%l"
            set "VAL=!VAL:*==!"
            set "VAL=!VAL:"=!"
            set "VAL=!VAL:'=!"
            if /i "!VAL!"=="true" set "MODULE_DISABLED=0"
            if /i "!VAL!"=="yes" set "MODULE_DISABLED=0"
            if "!VAL!"=="1" set "MODULE_DISABLED=0"
        )
    )
    if "!MODULE_DISABLED!"=="1" (
        echo Module '%TARGET%' is disabled in .env, performing build-only check...
        docker compose %FILES% %PROFILE_ARGS% -p %PROJECT% build %TARGET%
        exit /b !errorlevel!
    )
)

echo Building and starting '%TARGET%' in isolated project '%PROJECT%'...
docker compose %FILES% %PROFILE_ARGS% -p %PROJECT% up -d --build %TARGET%
if errorlevel 1 (
    echo Sandbox build/up failed.
    exit /b 1
)

if "%DB_CLONE%"=="1" if /i "%TARGET%"=="backend" (
    rem The mysql healthcheck (mysqladmin ping via socket) passes while the entrypoint
    rem temporary init server is up, but that server later restarts to the final server
    rem (port 3306). Restoring before that restart finishes races the down socket.
    rem Wait until the in-container socket accepts queries before restoring.
    call :waitmysql
    if errorlevel 1 (
        echo Sandbox mysql did not become ready for restore.
        goto :cleanup
    )
    echo Cloning live MySQL 'jobs' DB into sandbox mysql...
    call "%BACKUP_SCRIPT%"
    if errorlevel 1 (
        echo MySQL backup failed.
        goto :cleanup
    )
    set "BACKUP_FILE="
    for /f "delims=" %%f in ('dir /b /o-d "%CD%\scripts\mysql\backups\*_backup.sql" 2^>nul') do if not defined BACKUP_FILE set "BACKUP_FILE=%%f"
    if defined BACKUP_FILE (
        type "%CD%\scripts\mysql\backups\!BACKUP_FILE!" | docker exec -i -e MYSQL_PWD=rootPass ai-job-search-test-mysql /usr/bin/mysql -u root jobs
        if errorlevel 1 (
            echo MySQL restore failed.
            goto :cleanup
        )
    ) else (
        echo No MySQL backup file found.
        goto :cleanup
    )
)

echo Waiting for sandbox services to become ready...
docker compose %FILES% %PROFILE_ARGS% -p %PROJECT% ps

echo --- Logs for %TARGET% (last 100 lines) ---
docker compose %FILES% %PROFILE_ARGS% -p %PROJECT% logs %TARGET% --tail=100

goto :cleanup

:waitmysql
rem Poll the in-container mysql socket until the final server accepts queries.
rem Redirection targets /dev/null inside the container so docker exec stays quiet.
docker exec -e MYSQL_PWD=rootPass ai-job-search-test-mysql /bin/sh -c "i=0; until mysqladmin ping -u root >/dev/null 2>&1; do i=$((i+1)); if [ $i -ge 90 ]; then exit 1; fi; sleep 1; done; exit 0"
exit /b %errorlevel%

:cleanup
if "%KEEP%"=="1" (
    echo Keep mode: leaving sandbox running in project '%PROJECT%'.
    exit /b 0
)
echo Tearing down sandbox project '%PROJECT%'...
docker compose %FILES% %PROFILE_ARGS% -p %PROJECT% rm -sfv
docker volume rm %PROJECT%_mongo_data_sandbox >nul 2>&1
rmdir /s /q "%SANDBOX_DIR%" >nul 2>&1
echo Sandbox removed.
exit /b 0
