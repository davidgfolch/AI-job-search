@echo off
setlocal
:: Dump the local 'jobs' DB and full-restore it onto the other machine.
:: Default (no params) auto-discovers the target MySQL IP on the LAN.
:: Usage:
::   sync.bat                  : auto-discover target
::   sync.bat 192.168.1.50     : explicit target IP
::   sync.bat --dry-run        : show summary, skip restore
set "ROOT=%~dp0..\.."
cd /d "%ROOT%\apps\commonlib"
poetry run python -m commonlib.sync.mysql_sync %*
endlocal