@echo off
set "ROOT=%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.10+ not found.
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

cd /d "%ROOT%backend"
pythonw launcher.py
