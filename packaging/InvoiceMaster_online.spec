# -*- mode: python ; coding: utf-8 -*-
"""InvoiceMaster 在线版打包 spec（PyInstaller 单 exe，仅前端壳）。

在线版前端壳只负责展示，后端部署在远程 Linux，故不打包 FastAPI/uvicorn/pdfplumber
等后端依赖，仅打包 pywebview 与前端静态资源。

用法（在项目根目录执行，需先 `pip install pywebview pyinstaller` 并
`cd frontend && npm run build:online` 生成 dist-online）：

    pyinstaller packaging/InvoiceMaster_online.spec

产物：dist/InvoiceMasterOnline.exe（单文件，内含 frontend/dist-online）。
首次启动会引导填写后端服务器地址，配置保存于 %LOCALAPPDATA%/InvoiceMaster/online-config.json。
"""

from pathlib import Path

ROOT = Path(SPECPATH).parent

a = Analysis(
    [str(ROOT / 'backend' / 'desktop' / 'online_app.py')],
    pathex=[str(ROOT / 'backend')],
    binaries=[],
    datas=[
        (str(ROOT / 'frontend' / 'dist-online'), 'frontend/dist-online'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'unittest', 'pydoc_data'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='InvoiceMasterOnline',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=None,
)
