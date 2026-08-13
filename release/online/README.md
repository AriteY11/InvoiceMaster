# InvoiceMaster 在线版 v2.0.0

Windows 桌面壳（前端，只负责展示数据与图片）+ Linux 后端（FastAPI + SQLite）。

## 产物

- `InvoiceMasterOnline-v2.0.0.exe` — Windows 前端壳（由 `build_online.bat` 产出）
- `deploy.sh` — Linux 后端一键部署脚本

## 一键构建前端壳（Windows）

在 Windows（需 Node.js 18+ 与 Python 3.10+）双击运行：

```
build_online.bat
```

脚本自动完成：`npm run build:online` → 安装 pywebview/pyinstaller → 打包 → 复制 exe 到本目录。

## 一键部署后端（Linux 服务器）

在已 clone 项目代码的 Linux 服务器项目根目录执行：

```bash
bash release/online/deploy.sh
```

脚本自动完成：复制后端代码 → 创建 venv 安装依赖 → 创建数据目录 → 安装并启动 systemd 服务。详见 `deploy/linux/README.md`。

## 使用

1. 双击 `InvoiceMasterOnline-v2.0.0.exe` 启动前端壳
2. 首次启动填写后端服务器地址（如 `http://192.168.1.100:8000`），配置保存于 `%LOCALAPPDATA%/InvoiceMaster/online-config.json`
3. 之后自动连接远程后端，展示发票数据与 PDF 图片

## 版本

- 应用版本：2.0.0
