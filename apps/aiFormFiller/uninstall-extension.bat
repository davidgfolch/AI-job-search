@echo off
pushd "%~dp0"
set LOG_CONSOLE_MODE=message
uv run python scripts\install_extension.py --uninstall %*
popd
