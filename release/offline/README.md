# InvoiceMaster 离线版 v2.0.0

单 Windows 桌面应用（前后端一体），双击即用，数据存储于本机。

## 产物

- `InvoiceMaster-v2.0.0.exe` — 单文件桌面应用（由 `build_offline.bat` 产出）

## 一键构建

在 Windows（需 Node.js 18+ 与 Python 3.10+）双击运行：

```
build_offline.bat
```

脚本自动完成：`npm run build:offline` → 安装 Python 依赖 → PyInstaller 打包 → 复制 exe 到本目录。

## 使用

- 双击 `InvoiceMaster-v2.0.0.exe` 启动，应用窗口自动打开
- 数据（SQLite + 上传 PDF）存储于 `%LOCALAPPDATA%/InvoiceMaster/data`
- 无需安装 Python 或任何依赖

## 源码运行（开发者）

```
python backend/desktop/offline_app.py
```

## 版本

- 应用版本：2.0.0（与 `backend/app/config.py`、`frontend/src/components/Layout.tsx`、部署手册 docx 同步）
