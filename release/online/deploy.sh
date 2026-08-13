#!/usr/bin/env bash
# InvoiceMaster 在线版 Linux 后端一键部署脚本 v2.0.0
# 用法：在已 clone 项目代码的 Linux 服务器项目根目录执行
#   bash release/online/deploy.sh
set -euo pipefail

APP_DIR=/opt/invoicemaster
DATA_DIR=/var/lib/invoicemaster/data
SERVICE_USER=invoicemaster
PIP_MIRROR="${PIP_MIRROR:-https://pypi.tuna.tsinghua.edu.cn/simple}"

echo "============================================"
echo "  InvoiceMaster 在线版 Linux 后端部署 v2.0.0"
echo "============================================"

echo "[1/6] 创建应用目录与运行用户"
sudo mkdir -p "$APP_DIR"
sudo useradd --system --no-create-home --shell /usr/sbin/nologin "$SERVICE_USER" || true

echo "[2/6] 复制后端代码"
sudo cp -r backend "$APP_DIR/backend"

echo "[3/6] 创建虚拟环境并安装依赖"
sudo python3 -m venv "$APP_DIR/venv"
sudo "$APP_DIR/venv/bin/pip" install -i "$PIP_MIRROR" -r backend/requirements.txt

echo "[4/6] 创建数据目录并授权"
sudo mkdir -p "$DATA_DIR/uploads"
sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$APP_DIR" "$DATA_DIR"

echo "[5/6] 安装 systemd 服务"
sudo cp deploy/linux/invoicemaster.service /etc/systemd/system/invoicemaster.service
sudo systemctl daemon-reload
sudo systemctl enable --now invoicemaster

echo "[6/6] 验证"
sleep 2
curl -s http://127.0.0.1:8000/api/health && echo "" || echo "请检查: systemctl status invoicemaster"

echo ""
echo "部署完成。在线版桌面壳填写的服务器地址：http://<服务器IP>:8000"
