@echo off
setlocal enabledelayedexpansion
REM ===== AI Job Search SonarQube Analysis Script (Windows) =====
REM Usage: scripts/sonar.bat <command> [token]

cd /d "%~dp0.."
set "HOST_URL=http://localhost:9000"
set "TOKEN=%~2"

if "%TOKEN%"=="" (
    if exist ".env.secrets" (
        for /f "usebackq tokens=1,* delims==" %%A in (".env.secrets") do (
            if /I "%%A"=="SONAR_TOKEN" set "TOKEN=%%B"
        )
    )
)

set "CMD=%~1"
if "%CMD%"=="" (
    echo Usage: scripts\sonar.bat ^<up^|scan^|up-scan^|down^> [token]
    exit /b 1
)

if /I "%CMD%"=="up" (
    echo Starting SonarQube...
    docker compose -f docker-compose.yml -f docker/docker-compose.sonarqube.yml up -d sonarqube
    echo Waiting for server to be ready...
    :wait_up
    curl -sf %HOST_URL%/api/system/status >nul 2>&1
    if errorlevel 1 (
        timeout /t 5 /nobreak >nul
        goto wait_up
    )
    echo SonarQube is ready.
    call scripts\sonar-pw.bat
    goto done
)

if /I "%CMD%"=="scan" (
    if "%TOKEN%"=="" (
        echo Error: no token. Run scripts\sonar.bat up first.
        exit /b 1
    )
    echo Running tests with coverage...
    call scripts\test.bat --coverage
    if errorlevel 1 exit /b 1
    echo Running SonarQube analysis...
    docker compose -f docker-compose.yml -f docker/docker-compose.sonarqube.yml run --rm sonar-scanner
    if errorlevel 1 exit /b 1
    python scripts\sonar-marker.py
    goto done
)

if /I "%CMD%"=="up-scan" (
    echo Starting SonarQube...
    docker compose -f docker-compose.yml -f docker/docker-compose.sonarqube.yml up -d sonarqube
    :wait_upscan
    curl -sf %HOST_URL%/api/system/status >nul 2>&1
    if errorlevel 1 (
        timeout /t 5 /nobreak >nul
        goto wait_upscan
    )
    echo SonarQube is ready.
    call scripts\sonar-pw.bat
    if "%TOKEN%"=="" (
        for /f "usebackq tokens=1,* delims==" %%A in (".env.secrets") do (
            if /I "%%A"=="SONAR_TOKEN" set "TOKEN=%%B"
        )
    )
    if "%TOKEN%"=="" (
        echo Error: no token.
        exit /b 1
    )
    echo Running tests with coverage...
    call scripts\test.bat --coverage
    if errorlevel 1 exit /b 1
    echo Running SonarQube analysis...
    docker compose -f docker-compose.yml -f docker/docker-compose.sonarqube.yml run --rm sonar-scanner
    if errorlevel 1 exit /b 1
    python scripts\sonar-marker.py
    goto done
)

if /I "%CMD%"=="down" (
    docker compose -f docker-compose.yml -f docker/docker-compose.sonarqube.yml down
    goto done
)

echo Unknown command: %CMD%
exit /b 1

:done
echo.
echo SonarQube operation complete.
