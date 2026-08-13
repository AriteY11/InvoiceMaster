#!/usr/bin/env bash
# InvoiceMaster Linux 后端部署脚本（Ubuntu/Debian，需 sudo）
# 在项目根目录运行：bash deploy/linux/deploy.sh
set -euo pipefail

APP_DIR=/opt/invoicemaster
DATA_DIR=/var/lib/invoicemaster/data
SERVICE_USER=invoicemaster

echo "[1/6] 创建应用目录与运行用户"
sudo mkdir -p "$APP_DIR"
sudo useradd --system --no-create-home --shell /usr/sbin/nologin "$SERVICE_USER" || true

echo "[2/6] 复制后端代码"
sudo cp -r backend "$APP_DIR/backend"

echo "[3/6] 创建虚拟环境并安装依赖"
sudo python3 -m venv "$APP_DIR/venv"
sudo "$APP_DIR/venv/bin/pip" install -r backend/requirements.txt

echo "[4/6] 创建数据目录并授权"
sudo mkdir -p "$DATA_DIR/uploads"
sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$APP_DIR" "$DATA_DIR"

echo "[5/6] 安装 systemd 服务"
sudo cp deploy/linux/invoicemaster.service /etc/systemd/system/invoicemaster.service
sudo systemctl daemon-reload
sudo systemctl enable --now invoicemaster

echo "[6/6] 验证"
sleep 2
curl -s http://127.0.0.1:8000/api/health || echo "请检查: systemctl status invoicemaster"
