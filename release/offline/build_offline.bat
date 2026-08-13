@echo off
setlocal
chcp 65001 >nul
set "ROOT=%~dp0..\.."

echo ============================================
echo   InvoiceMaster 离线版一键构建脚本  v2.0.0
echo ============================================
echo.

where node >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Node.js 18+，请先安装：https://nodejs.org/
    pause
    exit /b 1
)
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python 3.10+，请先安装
    pause
    exit /b 1
)

echo [1/4] 构建前端（离线版，API 走本地内嵌后端）...
cd /d "%ROOT%\frontend"
call npm install
if errorlevel 1 (echo [错误] npm install 失败 & pause & exit /b 1)
call npm run build:offline
if errorlevel 1 (echo [错误] 前端构建失败 & pause & exit /b 1)

echo [2/4] 安装后端依赖与打包工具...
cd /d "%ROOT%\backend"
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pywebview pyinstaller

echo [3/4] 打包单 exe（PyInstaller）...
cd /d "%ROOT%"
pyinstaller --noconfirm packaging\InvoiceMaster_offline.spec
if errorlevel 1 (echo [错误] 打包失败，请根据报错补充 hiddenimports & pause & exit /b 1)

echo [4/4] 复制产物到 release\offline\...
if not exist "%ROOT%\release\offline" mkdir "%ROOT%\release\offline"
copy /y "%ROOT%\dist\InvoiceMaster.exe" "%ROOT%\release\offline\InvoiceMaster-v2.0.0.exe"

echo.
echo 完成！离线版 exe：release\offline\InvoiceMaster-v2.0.0.exe
pause
