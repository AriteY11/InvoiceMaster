# InvoiceMaster 在线版

Windows 桌面壳（前端，只负责展示数据与图片）+ Linux 后端（FastAPI + SQLite）。

## 产物

- `InvoiceMaster_Online_<版本号>_<年月日时分秒>.exe` — Windows 前端壳（由 `build_online.bat` 产出）
- `deploy.sh` — Linux 后端一键部署脚本

命名规则：`InvoiceMaster_Online_版本号_时间戳.exe`，版本号自动读取 `backend/app/config.py`，
时间戳为构建时刻（例：`InvoiceMaster_Online_2.1.1_20260816143025.exe`）。

## 一键构建前端壳（Windows）

在 Windows（需 Node.js 18+ 与 Python 3.10+）双击运行：

```
build_online.bat
```

脚本自动完成：

1. 探测国内依赖镜像，可用则自动配置 pip/uv/npm 全局镜像（加速依赖下载）
2. 读取当前版本号
3. `npm run build:online` 构建前端
4. 安装 pywebview/pyinstaller
5. PyInstaller 打包单 exe（前端页面 + pywebview 运行时一体，`--clean` 全量重分析；后端依赖运行于 Linux 服务器，不打包）
6. 按命名规则复制 exe 到本目录

## 一键部署后端（Linux 服务器）

在已 clone 项目代码的 Linux 服务器项目根目录执行：

```bash
bash release/online/deploy.sh
```

脚本自动完成：复制后端代码 → 创建 venv 安装依赖 → 创建数据目录 → 安装并启动 systemd 服务。详见 `deploy/linux/README.md`。

## 使用

1. 双击 exe 启动前端壳
2. 首次启动填写后端服务器地址（如 `http://192.168.1.100:8000`）与可选 API Token，配置保存于 `%LOCALAPPDATA%/InvoiceMaster/online-config.json`
3. 之后自动连接远程后端，展示发票数据与 PDF 图片

## 版本

- 应用版本与 `backend/app/config.py`、`frontend/src/components/Layout.tsx`、部署手册 docx 三处同步
