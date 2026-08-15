# InvoiceMaster 离线版

单 Windows 桌面应用（前后端一体），双击即用，数据存储于本机。

## 产物

- `InvoiceMaster_Offline_<版本号>_<年月日时分秒>.exe` — 单文件桌面应用（由 `build_offline.bat` 产出）

命名规则：`InvoiceMaster_Offline_版本号_时间戳.exe`，版本号自动读取 `backend/app/config.py`，
时间戳为构建时刻（例：`InvoiceMaster_Offline_2.1.1_20260816143025.exe`）。

## 一键构建

在 Windows（需 Node.js 18+ 与 Python 3.10+）双击运行：

```
build_offline.bat
```

脚本自动完成：

1. 探测国内依赖镜像，可用则自动配置 pip/uv/npm 全局镜像（加速依赖下载）
2. 读取当前版本号
3. `npm run build:offline` 构建前端
4. 安装全部后端依赖 + pywebview/pyinstaller
5. PyInstaller 打包单 exe（前端 + 后端 + 全部 Python 依赖一体，`--clean` 全量重分析）
6. 按命名规则复制 exe 到本目录

## 使用

- 双击 exe 启动，应用窗口自动打开
- 数据（SQLite + 上传 PDF）存储于 `%LOCALAPPDATA%/InvoiceMaster/data`
- 无需安装 Python 或任何依赖

## 源码运行（开发者）

```
python backend/desktop/offline_app.py
```

## 版本

- 应用版本与 `backend/app/config.py`、`frontend/src/components/Layout.tsx`、部署手册 docx 三处同步
