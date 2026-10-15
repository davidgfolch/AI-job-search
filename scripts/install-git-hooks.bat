@echo off
setlocal
cd /d "%~dp0.."
git config core.hooksPath "%CD%\.githooks"
echo Git hooks enabled: core.hooksPath=%CD%\.githooks
