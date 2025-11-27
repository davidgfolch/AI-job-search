@echo off
REM Usage example:
REM ______________________________________________________________________
REM set "colorsScript=%~dp0common\colors.bat"
REM call "%colorsScript%" green "Coverage enabled"

setlocal EnableDelayedExpansion

for /f "delims=" %%A in ('echo prompt $E ^| cmd') do set "ESC=%%A"

set "color=%1"
shift
set "text=%*"

rem Mapear colores dinámicamente
set "code=39"

if /i "!color!"=="green" set code=32
if /i "!color!"=="red" set code=31
if /i "!color!"=="blue" set code=34
if /i "!color!"=="aqua" set code=36
if /i "!color!"=="yellow" set code=33
if /i "!color!"=="purple" set code=35
if /i "!color!"=="white" set code=37
if /i "!color!"=="lightred" set code=91
if /i "!color!"=="lightgreen" set code=92
if /i "!color!"=="lightyellow" set code=93
if /i "!color!"=="lightblue" set code=94
if /i "!color!"=="lightpurple" set code=95
if /i "!color!"=="brightwhite" set code=97

rem Imprimir texto coloreado
echo !ESC![!code!m!text!!ESC![0m

endlocal