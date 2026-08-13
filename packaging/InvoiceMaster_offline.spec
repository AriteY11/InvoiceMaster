# -*- mode: python ; coding: utf-8 -*-
"""InvoiceMaster 离线版打包 spec（PyInstaller 单 exe）。

用法（在项目根目录执行，需先 `pip install -r backend/requirements.txt` 并
`cd frontend && npm run build:offline` 生成 dist）：

    pyinstaller packaging/InvoiceMaster_offline.spec

产物：dist/InvoiceMaster.exe（单文件，内含 frontend/dist 静态资源与 Python 依赖）。
运行时数据目录为 %LOCALAPPDATA%/InvoiceMaster/data，由后端 ensure_directories() 创建。
"""

from pathlib import Path

ROOT = Path(SPECPATH).parent

a = Analysis(
    [str(ROOT / 'backend' / 'desktop' / 'offline_app.py')],
    pathex=[str(ROOT / 'backend')],
    binaries=[],
    datas=[
        (str(ROOT / 'frontend' / 'dist'), 'frontend/dist'),
    ],
    hiddenimports=[
        # uvicorn 的动态 import
        'uvicorn.logging',
        'uvicorn.loops.auto',
        'uvicorn.loops.asyncio',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.protocols.websockets.websockets_impl',
        'uvicorn.lifespan.on',
        # app 模块（部分为字符串 import，需显式声明）
        'app.main',
        'app.embedded',
        'app.api.routes.invoices',
        'app.api.routes.stats',
        'app.models.invoice',
        'app.models.invoice_item',
        'app.services.pdf_extractor',
        'app.services.invoice_parser',
        'app.services.parser_rules',
        'app.services.text_normalizer',
        'app.services.stats_service',
    ],
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
    name='InvoiceMaster',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 桌面应用不显示控制台；调试时改为 True 查看日志
    icon=None,
)
