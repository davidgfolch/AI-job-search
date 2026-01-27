@echo off
setlocal EnableDelayedExpansion

if not "%~1"=="" (
    set "BACKUP_FILE=%~1"
    goto :DoRestore
)

:SelectFile
set "DIR=%~dp0"
set "DIR=%DIR:~0,-1%"

set "BACKUP_DIR=%DIR%\backups"

echo No backup file specified.
echo Available backups in %BACKUP_DIR%:
echo.

set count=0
for %%f in ("%BACKUP_DIR%\*.sql") do (
    set /a count+=1
    set "file[!count!]=%%f"
    echo [!count!] %%~nxf
)

if %count% EQU 0 (
    echo No .sql backup files found in "%BACKUP_DIR%".
    exit /b 1
)

echo.
set /p choice="Select a number to restore: "

if "%choice%"=="" goto :SelectFile
if %choice% LSS 1 goto :SelectFile
if %choice% GTR %count% goto :SelectFile

set "BACKUP_FILE=!file[%choice%]!"

:DoRestore
if not exist "%BACKUP_FILE%" (
    echo Error: File "%BACKUP_FILE%" not found.
    exit /b 1
)

echo Restoring database 'jobs' from %BACKUP_FILE%...

type "%BACKUP_FILE%" | docker exec -i -e MYSQL_PWD=rootPass ai-job-search-mysql ^
    /usr/bin/mysql -u root jobs

if %ERRORLEVEL% EQU 0 (
    echo Restore completed successfully.
) else (
    echo Restore failed.
    exit /b 1
)

endlocal
