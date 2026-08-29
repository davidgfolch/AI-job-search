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
set "FAILED=0"

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
    echo Cloning live MySQL 'jobs' DB into sandbox mysql...
    call "%BACKUP_SCRIPT%"
    if errorlevel 1 (
        echo MySQL backup failed.
        set "FAILED=1"
        goto :cleanup
    )
    set "BACKUP_FILE="
    for /f "delims=" %%f in ('dir /b /o-d "%CD%\scripts\mysql\backups\*_backup.sql" 2^>nul') do if not defined BACKUP_FILE set "BACKUP_FILE=%%f"
)

if defined BACKUP_FILE (
    echo Waiting for sandbox mysql to accept authenticated connections...
    call :wait_mysql
    if errorlevel 1 (
        echo Sandbox mysql not ready for restore.
        set "FAILED=1"
        goto :cleanup
    )
    echo Restoring MySQL backup into sandbox...
    type "%CD%\scripts\mysql\backups\!BACKUP_FILE!" | docker exec -i -e MYSQL_PWD=rootPass ai-job-search-test-mysql /usr/bin/mysql -u root jobs
    if errorlevel 1 (
        echo MySQL restore failed.
        set "FAILED=1"
        goto :cleanup
    )
) else if "%FAILED%"=="0" (
    if "%DB_CLONE%"=="1" if /i "%TARGET%"=="backend" (
        echo No MySQL backup file found.
        set "FAILED=1"
    )
)

echo Waiting for sandbox services to become ready...
docker compose %FILES% %PROFILE_ARGS% -p %PROJECT% ps

echo --- Logs for %TARGET% (last 100 lines) ---
docker compose %FILES% %PROFILE_ARGS% -p %PROJECT% logs %TARGET% --tail=100

echo Checking sandbox logs for errors...
docker compose %FILES% %PROFILE_ARGS% -p %PROJECT% logs %TARGET% 2>&1 | findstr /i /c:"ERROR" /c:"CRITICAL" /c:"Traceback"
if not errorlevel 1 (
    echo Sandbox log check FAILED: ERROR/CRITICAL/Traceback found in '%TARGET%' logs.
    set "FAILED=1"
)

:cleanup
if "%KEEP%"=="1" (
    echo Keep mode: leaving sandbox running in project '%PROJECT%'.
    exit /b %FAILED%
)
echo Tearing down sandbox project '%PROJECT%'...
docker compose %FILES% %PROFILE_ARGS% -p %PROJECT% rm -sfv
docker volume rm %PROJECT%_mongo_data_sandbox >nul 2>&1
rmdir /s /q "%SANDBOX_DIR%" >nul 2>&1
if "%FAILED%"=="1" (
    echo Sandbox verification FAILED.
    exit /b 1
)
echo Sandbox removed.
exit /b 0

:wait_mysql
set /a MYSQL_TRIES=0
:wait_mysql_loop
docker exec -e MYSQL_PWD=rootPass ai-job-search-test-mysql /usr/bin/mysql -h 127.0.0.1 -u root -e "SELECT 1" >nul 2>&1
if not errorlevel 1 exit /b 0
set /a MYSQL_TRIES+=1
if !MYSQL_TRIES! GEQ 30 (
    echo Sandbox mysql not ready.
    exit /b 1
)
ping -n 3 127.0.0.1 >nul
goto wait_mysql_loop
