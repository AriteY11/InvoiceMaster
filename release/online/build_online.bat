@echo off
setlocal
chcp 65001 >nul
set "ROOT=%~dp0..\.."

echo ============================================
echo   InvoiceMaster 在线版一键构建脚本
echo ============================================
echo.

where node >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Node.js 18+，请先安装：https://nodejs.org/
    pause
    exit /b 1
)

set "PYCMD=python"
where python >nul 2>&1
if errorlevel 1 (
    where py >nul 2>&1
    if errorlevel 1 (
        echo [错误] 未找到 Python 3.10+，请先安装
        pause
        exit /b 1
    )
    set "PYCMD=py -3"
)
%PYCMD% --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Python 不可用，请先安装 Python 3.10+
    pause
    exit /b 1
)

echo [1/6] 检查并配置国内依赖镜像（可用则自动使用）...
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\scripts\setup_mirrors.ps1"
if errorlevel 1 echo [提示] 镜像探测失败，将使用已配置的默认源继续

echo [2/6] 读取应用版本号（backend\app\config.py）...
for /f "delims=" %%v in ('%PYCMD% "%ROOT%\scripts\get_version.py"') do set "VERSION=%%v"
if not defined VERSION (
    echo [错误] 读取版本号失败
    pause
    exit /b 1
)
echo   版本号：%VERSION%

echo [3/6] 构建前端（在线版，API 地址运行时配置）...
cd /d "%ROOT%\frontend"
call npm install
if errorlevel 1 (echo [错误] npm install 失败 & pause & exit /b 1)
call npm run build:online
if errorlevel 1 (echo [错误] 前端构建失败 & pause & exit /b 1)

echo [4/6] 安装打包工具（pywebview + pyinstaller）...
%PYCMD% -m pip install pywebview pyinstaller
if errorlevel 1 (echo [错误] 打包工具安装失败 & pause & exit /b 1)

echo [5/6] PyInstaller 打包单 exe（前端壳 + pywebview 运行时一体，--clean 全量重分析）...
cd /d "%ROOT%"
%PYCMD% -m PyInstaller --noconfirm --clean packaging\InvoiceMaster_online.spec
if errorlevel 1 (echo [错误] 打包失败 & pause & exit /b 1)

echo [6/6] 按命名规则复制产物到 release\online\...
for /f "delims=" %%t in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMddHHmmss"') do set "STAMP=%%t"
set "OUTNAME=InvoiceMaster_Online_%VERSION%_%STAMP%.exe"
if not exist "%ROOT%\release\online" mkdir "%ROOT%\release\online"
copy /y "%ROOT%\dist\InvoiceMasterOnline.exe" "%ROOT%\release\online\%OUTNAME%" >nul
if errorlevel 1 (echo [错误] 复制产物失败 & pause & exit /b 1)

echo.
echo 完成！在线版 exe：release\online\%OUTNAME%
echo （单文件，已包含前端页面与 pywebview 桌面壳运行时；后端运行在 Linux 服务器）
pause
