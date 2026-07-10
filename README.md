# InvoiceMaster 发票管理系统

基于 FastAPI + React 的电子发票管理工具，支持 PDF 发票的自动解析、存储、查询、统计与导出。适用于个人或小型企业的发票管理需求。

## 功能特性

| 模块 | 功能 |
|------|------|
| **发票上传** | 拖拽上传多个 PDF 电子发票，自动解析提取全部字段信息 |
| **人工录入** | 手动创建发票，支持一次录入多条，字段自由填写 |
| **发票列表** | 多条件搜索筛选，分页浏览，支持 Excel/CSV 导出 |
| **发票详情** | 完整发票信息展示，行项目明细表格，原 PDF 预览 |
| **统计分析** | 金额趋势折线图、分类饼图、卖家排名柱状图、按类型/月份统计 |
| **导出配置** | 自由选择导出列，过滤无关字段 |
| **复制配置** | 自由勾选要复制的字段，一键复制发票信息到剪贴板 |
| **时间配置** | 支持切换时区，上传时间按选定时区显示 |
| **暗色模式** | 亮/暗色主题切换 |
| **中文优化** | Microsoft YaHei / PingFang 字体栈，显示效果统一 |

## 技术栈

### 后端
- **Python 3.10+** / **FastAPI** - Web API 框架
- **SQLAlchemy** - ORM，SQLite 数据库
- **pdfplumber / pypdf** - PDF 文本与表格提取
- **openpyxl** - Excel 导出
- **Pydantic** - 数据校验

### 前端
- **React 18** / **TypeScript** / **Vite 6**
- **Tailwind CSS** - 样式框架，支持暗色模式
- **Zustand** - 状态管理（导出/复制/时区配置持久化）
- **Recharts** - 统计图表
- **React Router** - 前端路由
- **Lucide React** - 图标库

## 项目结构

```
InvoiceMaster/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # API 路由（发票、统计）
│   │   ├── models/              # 数据库模型
│   │   ├── schemas/             # Pydantic 数据模型
│   │   ├── services/            # 业务逻辑（PDF 解析、统计）
│   │   ├── config.py            # 配置
│   │   ├── db.py                # 数据库连接
│   │   └── main.py              # FastAPI 入口
│   ├── data/uploads/            # 上传文件存储
│   ├── run.py                   # 服务器入口
│   ├── launcher.py              # Windows 启动器
│   └── requirements.txt         # Python 依赖
├── frontend/
│   ├── src/
│   │   ├── api/                 # API 调用封装
│   │   ├── components/          # 通用组件（Layout、弹窗）
│   │   ├── pages/               # 页面组件
│   │   ├── store/               # Zustand 状态
│   │   ├── types/               # TypeScript 类型
│   │   └── hooks/               # 自定义 Hooks
│   ├── index.html               # HTML 入口
│   ├── vite.config.ts           # Vite 配置
│   └── package.json             # Node 依赖
├── template/                    # 测试发票 PDF 模板
├── start_app.bat                # Windows 一键启动脚本
├── package.json                 # 根目录构建脚本
└── InvoiceMaster_部署手册与使用说明.docx
```

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- pip

### 1. 安装后端依赖

```bash
cd backend
pip install --target vendor -r requirements.txt
```

### 2. 构建前端

```bash
cd frontend
npm install
npm run build
```

构建产物输出到 `frontend/dist/`，后端会自动托管静态文件。

### 3. 启动服务

**Windows（一键启动）：**

双击 `start_app.bat` 或执行：

```bash
start_app.bat
```

**手动启动：**

```bash
cd backend
python run.py
```

启动后访问 http://127.0.0.1:8000

### 验证安装

```bash
curl http://127.0.0.1:8000/api/health
# {"status":"ok","service":"InvoiceMaster API"}
```

## API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/invoices/upload` | 上传 PDF 发票文件 |
| POST | `/api/invoices/manual` | 手动创建发票 |
| GET | `/api/invoices` | 发票列表（分页+筛选） |
| GET | `/api/invoices/{id}` | 发票详情 |
| GET | `/api/invoices/{id}/file` | 下载原始 PDF |
| DELETE | `/api/invoices/{id}` | 删除发票 |
| GET | `/api/invoices/export` | 导出 Excel/CSV |
| GET | `/api/invoices/filters` | 获取筛选选项 |
| GET | `/api/stats/overview` | 统计概览（总数、总额） |
| GET | `/api/stats/trend` | 金额趋势 |
| GET | `/api/stats/category` | 分类统计 |
| GET | `/api/health` | 健康检查 |

## 解析能力

支持当前主流电子发票格式，可提取的字段包括：

- 基础信息：发票名称、发票代码、发票号码、开票日期、校验码、机器编号、发票类型、币种
- 购买方：名称、纳税人识别号、地址电话、开户行及账号
- 销售方：名称、纳税人识别号、地址电话、开户行及账号
- 金额：不含税金额、税额、价税合计、价税合计（大写）
- 行项目：名称、规格型号、单位、数量、单价、金额、税率、税额
- 其他：备注、页数、解析状态、解析置信度

## 配置说明

| 配置项 | 文件 | 说明 |
|--------|------|------|
| 应用版本 | `backend/app/config.py` | 显示在页面顶部 |
| 允许格式 | `backend/app/config.py` | 默认 .pdf |
| 上传上限 | `backend/app/config.py` | 默认 20MB |
| 数据库 | `backend/data/invoices.db` | SQLite 自动创建 |
| 文件存储 | `backend/data/uploads/` | 上传的 PDF 文件 |

## 许可证

著作人：ForWhat | 联系：1256418086@qq.com
