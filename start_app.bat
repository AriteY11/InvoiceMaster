@echo off
set "ROOT=%~dp0"

:: 优先启动打包后的桌面应用（单 exe）
if exist "%ROOT%dist\InvoiceMaster.exe" (
    start "" "%ROOT%dist\InvoiceMaster.exe"
    exit /b 0
)

:: 否则回退为源码运行桌面应用
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.10+ not found.
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

cd /d "%ROOT%backend"
python desktop\offline_app.py
