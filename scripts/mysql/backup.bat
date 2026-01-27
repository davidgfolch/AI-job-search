@echo off
setlocal

:: Get directory of the script
set "DIR=%~dp0"
:: Remove trailing backslash
set "DIR=%DIR:~0,-1%"

set "BACKUP_DIR=%DIR%\backups"
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

:: Generate filename with timestamp YYYYMMDD_HHMMSS using PowerShell
for /f %%a in ('powershell -Command "Get-Date -Format 'yyyyMMdd_HHmm'"') do set TIMESTAMP=%%a
set "BACKUP_FILE=%BACKUP_DIR%\%TIMESTAMP%_backup.sql"

echo Backing up database 'jobs' to %BACKUP_FILE%...

docker exec -i -e MYSQL_PWD=rootPass ai-job-search-mysql ^
    /usr/bin/mysqldump -u root ^
    --single-transaction ^
    --routines --triggers --events ^
    --set-gtid-purged=OFF ^
    jobs > "%BACKUP_FILE%"

if %ERRORLEVEL% EQU 0 (
    echo Backup completed successfully.
) else (
    echo Backup failed.
    exit /b 1
)

endlocal
