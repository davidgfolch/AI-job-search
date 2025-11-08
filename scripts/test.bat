@echo off

rem Test commonlib
echo.
echo Testing commonlib library...
pushd packages\commonlib
poetry run pytest
popd

rem Iterate over app directories in apps\
for /d %%a in (apps\*) do (
    echo.
    echo Testing %%~nxa...
    if "%%~nxa"=="aiEnrich" (
        echo Testing aiEnrich library...
        pushd "%%~fa"
        rem set environment variable for this session and run uv commands if available
        set "UV_PROJECT_ENVIRONMENT=custom-venv"
        if exist "%~dp0" (
            rem prefer calling commands directly; errors will be shown by those tools
        )
        uv run pytest
        uv run coverage run -m pytest
        uv run coverage report -m
        uv run coverage xml
        uv run coverage-badge -o coverage-badge.svg -f        popd
    ) else (
        echo Testing %%~nxa library...
        pushd "%%~fa"
        poetry run pytest
        poetry run coverage run -m pytest
        poetry run coverage report -m
        poetry run coverage xml
        poetry run coverage-badge -o coverage-badge.svg -f
        popd
    )
)
