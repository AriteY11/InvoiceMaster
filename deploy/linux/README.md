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
| `INVOICEMASTER_API_TOKEN` | 未设置 | 设置后启用 Bearer Token 鉴权（`/api/health` 除外） |

> CORS 说明：在线版桌面壳从 `file://` 加载前端，跨源请求的 Origin 为 `null`。
> 内网部署保持 `*` 即可；如需收紧，必须包含 `null`，例如 `null,https://your.domain`。

## 账号管理（推荐）

在线版使用**账号 + 密码**登录（`/api/auth/login` 换取会话 Token，30 天有效）。
首次部署后先用账号管理脚本创建账号：

```bash
sudo -u invoicemaster /opt/invoicemaster/venv/bin/python /opt/invoicemaster/scripts/manage_accounts.py
```

交互式菜单支持：**新增账号 / 修改已有账号密码 / 查看账号列表**。账号保存在服务器 SQLite（`accounts` 表），密码以 scrypt 哈希存储。

- 创建账号后所有 API 自动进入账号鉴权模式（`/api/health`、`/api/auth/login` 除外）
- 未创建任何账号时后端保持免认证（离线版桌面应用即此模式）
- 各账号目前无权限区分，均可查看全部发票；发票记录上传账号（列表可按"上传人"筛选）

### 兼容：静态 API Token

也可用环境变量 `INVOICEMASTER_API_TOKEN` 做静态 Token 鉴权（与账号模式并存，任一生效）：

1. 在 `/etc/systemd/system/invoicemaster.service` 的 `[Service]` 段取消注释并修改：
   ```
   Environment=INVOICEMASTER_API_TOKEN=你的随机Token
   ```
2. `sudo systemctl daemon-reload && sudo systemctl restart invoicemaster`
3. 设置后桌面壳登录页的账号密码登录仍可用（会话 Token 与静态 Token 均被接受）。

未设置该变量且无账号时鉴权完全关闭。
验证：`curl http://<服务器IP>:8000/api/invoices` 应返回 `{"detail":"未登录：请先登录"}`。

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
