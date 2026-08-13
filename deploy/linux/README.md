# InvoiceMaster 在线版 Linux 后端部署说明

在线版架构：Windows 桌面壳（pywebview + 本地前端）→ HTTP API → Linux 后端（FastAPI + SQLite）。

## 环境要求

- Linux 服务器（Ubuntu 20.04+/Debian 11+ 均可）
- Python 3.10+
- 磁盘空间：≥ 1 GB（依赖 + 发票 PDF 数据）

## 快速部署

在项目根目录执行：

```bash
bash deploy/linux/deploy.sh
```

脚本会完成：复制后端代码 → 创建 venv 并安装依赖 → 创建数据目录 → 安装并启动 systemd 服务。

## 手动部署

```bash
# 1. 部署代码与依赖
sudo mkdir -p /opt/invoicemaster
sudo cp -r backend /opt/invoicemaster/backend
sudo python3 -m venv /opt/invoicemaster/venv
sudo /opt/invoicemaster/venv/bin/pip install -r backend/requirements.txt

# 2. 数据目录（SQLite 与上传的 PDF）
sudo mkdir -p /var/lib/invoicemaster/data/uploads
sudo useradd --system --no-create-home --shell /usr/sbin/nologin invoicemaster
sudo chown -R invoicemaster:invoicemaster /opt/invoicemaster /var/lib/invoicemaster

# 3. systemd 服务
sudo cp deploy/linux/invoicemaster.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now invoicemaster

# 4. 验证
curl http://127.0.0.1:8000/api/health
# {"status":"ok","service":"InvoiceMaster API"}
```

## 配置（环境变量）

在 `/etc/systemd/system/invoicemaster.service` 的 `[Service]` 段调整：

| 变量 | 默认 | 说明 |
|------|------|------|
| `INVOICEMASTER_DATA_DIR` | `/var/lib/invoicemaster/data` | SQLite 与上传文件目录 |
| `INVOICEMASTER_HOST` | `127.0.0.1` | 监听地址（部署用 `0.0.0.0`） |
| `INVOICEMASTER_PORT` | `8000` | 监听端口 |
| `INVOICEMASTER_CORS_ORIGINS` | `*` | 允许的 Origin 列表（逗号分隔） |

> CORS 说明：在线版桌面壳从 `file://` 加载前端，跨源请求的 Origin 为 `null`。
> 内网部署保持 `*` 即可；如需收紧，必须包含 `null`，例如 `null,https://your.domain`。

## nginx 反向代理（可选）

```bash
sudo cp deploy/linux/nginx.conf /etc/nginx/sites-available/invoicemaster
sudo ln -s /etc/nginx/sites-available/invoicemaster /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

配置完成后，在线版桌面壳填写的服务器地址为 `http://<服务器IP>:8000`（或 nginx 反代后的域名）。

## 多进程部署（可选）

单进程 uvicorn 已满足小团队并发需求；高并发可改用 gunicorn + uvicorn workers：

```bash
/opt/invoicemaster/venv/bin/pip install gunicorn
/opt/invoicemaster/venv/bin/gunicorn app.main:app \
  -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

注意：SQLite 为单文件数据库，多 worker 写入并发有限，小规模场景建议保持单进程。
