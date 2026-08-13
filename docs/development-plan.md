# 发票分析系统实施计划（更新版）

## Summary

基于已有的后端数据模型和前端骨架，完成 PDF 发票解析与 Web 展示系统的剩余开发工作。

- **输入**：用户上传 PDF 电子发票文件（文本型，非扫描件）
- **解析策略**：仅文本提取（pdfplumber），不含 OCR
- **展示要求**：完整信息含行项目明细 + 完整仪表盘（概览卡片 + 趋势图 + 分类统计）
- **交付形态**：Python FastAPI 后端 + React/Vite 前端 + Windows 启动脚本

## Current State

### 已完成项
| 模块 | 文件 | 状态 |
|------|------|------|
| 后端数据模型 | `backend/app/models/invoice.py`, `invoice_item.py`, `base.py` | ✅ |
| 后端 Schemas/DTO | `backend/app/schemas/invoice.py`, `stats.py` | ✅ |
| 后端配置 | `backend/app/config.py` | ✅ |
| 后端数据库 | `backend/app/db.py` | ✅ |
| 后端应用入口 | `backend/app/main.py` (FastAPI + CORS + 静态文件) | ✅ |
| 后端依赖 | `backend/requirements.txt` | ✅ |
| 前端骨架 | `frontend/` (React+Vite+Tailwind+Router+Theme) | ✅ |
| 前端工具 | `cn()`, `useTheme()` | ✅ |
| 模板文件 | `template/` (3 份 PDF 示例) | ✅ |

### 待实现项
| 模块 | 内容 | 优先级 |
|------|------|--------|
| 后端服务层 | pdf_extractor, text_normalizer, invoice_parser, parser_rules, stats_service | 🔴 高 |
| 后端 API 路由 | invoices router, stats router | 🔴 高 |
| 前端 API 层 | client.ts, types/invoice.ts | 🔴 高 |
| 前端页面 | UploadPage, InvoiceListPage, InvoiceDetailPage, StatsPage | 🔴 高 |
| 前端组件 | Layout, FieldCard, ItemsTable | 🔴 高 |
| 启动脚本 | `start_app.bat` | 🟡 中 |

## Proposed Changes（按实现顺序）

---

### 步骤 1：实现后端 PDF 提取与解析服务层

这是系统的核心，负责将 PDF 发票转为结构化数据。

#### 1.1 新建 `backend/app/services/pdf_extractor.py`

**职责**：使用 pdfplumber 提取 PDF 的文本和表格

```python
# 核心功能：
# - 逐页提取文本
# - 提取所有表格（含行列结构）
# - 返回统一中间结构：{pages: [{text, tables}]}
# - 合并原始全文 raw_text
# - 提取 PDF 元信息（页数等）
```

**关键设计决策**：
- 使用 `pdfplumber.open()` 逐页处理
- 每页同时提取 `extract_text()` 和 `extract_tables()`
- 合并所有页文本为 `raw_text`
- 表格保留行列结构供后续解析

#### 1.2 新建 `backend/app/services/text_normalizer.py`

**职责**：清洗和标准化从 PDF 提取的文本

```python
# 核心功能：
# - 全角数字 → 半角数字（１２３→123）
# - 全角字母 → 半角字母（ＡＢＣ→ABC）
# - 中文标点规范化
# - 金额字符串 → Decimal（"¥1,234.56"→Decimal("1234.56")）
# - 税率字符串 → Decimal（"6%"→Decimal("6")）
# - 日期字符串 → date（"2024年01月15日"→date(2024,1,15)）
# - 空白字符清理（\u3000→空格，多余换行合并）
# - 无效字符过滤
```

#### 1.3 新建 `backend/app/services/parser_rules.py`

**职责**：管理字段提取的正则规则和关键词映射

```python
# 核心内容：
# - KEYWORD_MAP：关键词别名字典
#   - "发票名称": ["发票名称", "发票标题", "电子发票"]
#   - "发票代码": ["发票代码", "发票代码："]
#   - "发票号码": ["发票号码", "发票号码：", "No"]
#   - "开票日期": ["开票日期", "开票日期：", "日期"]
#   - "校验码": ["校验码", "校验码："]
#   - "购买方名称": ["购买方名称", "名称", "购方名称"]
#   - "销售方名称": ["销售方名称", "名称", "销方名称"]
#   - "价税合计": ["价税合计", "合计", "小写"]
#   - "不含税金额": ["不含税金额", "金额（不含税）"]
#   - "税额": ["税额", "税额合计"]
#   - 等等...

# - FIELD_PATTERNS：常见正则模式
#   - 发票代码：10-12位数字
#   - 发票号码：8位数字
#   - 日期：YYYY年MM月DD日 / YYYY-MM-DD
#   - 纳税人识别号：18位字母数字
#   - 金额：¥xx,xxx.xx 格式
#   - 大写金额：中文大写数字

# - TABLE_COLUMN_MAP：表格列头到 model 字段的映射
#   - "货物或应税劳务、服务名称" → item_name
#   - "规格型号" → specification
#   - "单位" → unit
#   - "数量" → quantity
#   - "单价" → unit_price
#   - "金额" → amount
#   - "税率" → tax_rate
#   - "税额" → tax_amount
```

#### 1.4 新建 `backend/app/services/invoice_parser.py`

**职责**：将提取的文本和表格映射为标准 Invoice 模型字段

```python
# 核心流程：
# 1. 接收 pdf_extractor 的输出
# 2. 对 raw_text 进行 text_normalizer 清洗
# 3. 使用 parser_rules 中的规则匹配字段：
#    a. 关键词定位 → 按行/按区域提取字段值
#    b. 正则匹配 → 兜底提取（如发票代码、日期等有固定格式的字段）
#    c. 买卖双方信息 → 按"购买方"和"销售方"分段后逐字段提取
#    d. 金额信息 → 提取金额行后分别匹配不含税金额、税额、价税合计
# 4. 从表格数据中提取行项目（明细行）：
#    a. 匹配表格的列头
#    b. 按列映射关系逐行提取
#    c. 对每行的金额/税率/税额做 normalize
# 5. 计算解析置信度（提取到的字段数 / 期望字段总数）
# 6. 记录解析告警（缺失字段、格式异常等）
# 7. 返回 Invoice 数据 dict
```

**解析策略（按优先级）**：
1. **表格优先**：先尝试从 pdfplumber 表格中提取结构化数据（准确度最高）
2. **关键词定位**：对非表格字段，通过关键词在文本中定位
3. **正则兜底**：对固定格式字段（代码、号码、日期），用正则全局搜索
4. **上下文推断**：买卖双方信息通过"购买方"/"销售方"区域分段提取

**针对模板 PDF 的适配**：
- `1.pdf`：标准电子发票格式，表格清晰，字段行规整
- `携程酒店订单电子发票`：携程模板，可能字段排列略有不同，需适配关键词变体

#### 1.5 新建 `backend/app/services/stats_service.py`

**职责**：从数据库查询生成统计数据

```python
# 核心接口：
# - get_overview(db) → {total_invoices, total_amount, total_tax_amount, latest_issue_date}
# - get_trends(db, group_by: "month"|"day") → [{period, invoice_count, total_amount, tax_amount}]
# - get_categories(db, dimension: "invoice_type"|"seller_name"|"item_name") → [{name, count, total_amount}]
```

**实现方式**：使用 SQLAlchemy 聚合查询 + GROUP BY

---

### 步骤 2：实现后端 API 路由

#### 2.1 新建 `backend/app/api/__init__.py`
空文件，标记为 Python 包。

#### 2.2 新建 `backend/app/api/routes/__init__.py`
空文件。

#### 2.3 新建 `backend/app/api/routes/invoices.py`

```python
# POST /api/invoices/upload
# - 接收 multipart/form-data（多个 PDF 文件）
# - 校验：扩展名(.pdf)、大小(≤20MB)
# - 计算文件哈希(SHA256)做重复检测
# - 保存到 upload_dir
# - 调用 pdf_extractor → invoice_parser 解析
# - 写入数据库（Invoice + InvoiceItem）
# - 返回 UploadInvoicesResponse

# GET /api/invoices
# - 查询参数：page, page_size, keyword, date_from, date_to, 
#   amount_min, amount_max, seller_name, invoice_type
# - 分页查询 invoices 表
# - 返回 InvoiceListResponse

# GET /api/invoices/{invoice_id}
# - 查询单张发票 + 关联 items
# - 返回 InvoiceDetailRead

# DELETE /api/invoices/{invoice_id}
# - 软删除或硬删除发票及关联 items
# - 返回 DeleteInvoiceResponse
```

#### 2.4 新建 `backend/app/api/routes/stats.py`

```python
# GET /api/stats/overview
# - 返回 StatsOverviewResponse

# GET /api/stats/trends?group_by=month
# - group_by 可选 "month" | "day"
# - 返回 StatsTrendResponse

# GET /api/stats/categories?dimension=invoice_type
# - dimension 可选 "invoice_type" | "seller_name"
# - 返回 StatsCategoryResponse
```

---

### 步骤 3：修复后端 main.py 导入

当前 `main.py` 已 import 了路由，但路由文件尚不存在。创建路由文件后即可正常启动。无需修改 `main.py` 本身（除非发现路径问题）。

---

### 步骤 4：实现前端 API 层与类型定义

#### 4.1 新建 `frontend/src/types/invoice.ts`

与后端 schemas 完全对应的 TypeScript 类型定义：
- `InvoiceItem`, `InvoiceSummary`, `InvoiceDetail`
- `InvoiceListResponse`, `UploadInvoiceResult`, `UploadInvoicesResponse`
- `StatsOverview`, `TrendPoint`, `StatsTrend`, `CategoryPoint`, `StatsCategory`
- `InvoiceQueryParams`

#### 4.2 新建 `frontend/src/api/client.ts`

Axios/fetch 封装：
- 基准 URL：开发模式代理到 `http://127.0.0.1:8000`
- 统一错误处理
- API 函数：`uploadInvoices()`, `getInvoices()`, `getInvoiceDetail()`, `deleteInvoice()`, `getStatsOverview()`, `getStatsTrends()`, `getStatsCategories()`

#### 4.3 更新 `frontend/vite.config.ts`

添加开发代理配置：
```ts
server: {
  proxy: {
    '/api': 'http://127.0.0.1:8000',
  },
},
```

---

### 步骤 5：实现前端页面与组件

#### 5.1 新建 `frontend/src/components/Layout.tsx`

- 侧边栏/顶部导航：上传发票、发票列表、统计分析 三个入口
- 使用 React Router 的 `<NavLink>`
- 集成暗色模式切换（使用已有 `useTheme()` hook）
- 使用 Tailwind + lucide-react 图标

#### 5.2 新建 `frontend/src/pages/UploadPage.tsx`

- 拖拽上传区域（支持点击选择 + 拖拽）
- 支持多文件上传
- 上传进度提示
- 上传结果展示（成功/失败/重复）
- 上传完成后引导到列表页

#### 5.3 新建 `frontend/src/pages/InvoiceListPage.tsx`

- 表格展示：发票代码、号码、日期、类型、购买方、销售方、金额、状态
- 筛选栏：关键字搜索、日期范围、金额范围、发票类型下拉
- 分页控制器
- 点击行进入详情页
- 删除按钮（含确认弹窗）

#### 5.4 新建 `frontend/src/components/FieldCard.tsx`

- 通用结构化字段卡片组件
- 接收 `{label, value, missing?}` props
- 缺失时显示"未识别"灰色文本

#### 5.5 新建 `frontend/src/components/ItemsTable.tsx`

- 发票行项目明细表格
- 列：序号、商品名称、规格型号、单位、数量、单价、金额、税率、税额
- 合行行显示汇总

#### 5.6 新建 `frontend/src/pages/InvoiceDetailPage.tsx`

- 使用 `useParams()` 获取 invoice_id
- 用 `FieldCard` 展示所有字段分组：
  - 发票基础信息
  - 购买方信息
  - 销售方信息
  - 金额信息
- 用 `ItemsTable` 展示行项目明细
- 原始文本折叠展示区
- 解析告警列表（如有）
- 返回列表按钮

#### 5.7 新建 `frontend/src/pages/StatsPage.tsx`

**完整仪表盘布局**：

1. **概览卡片行**（4 个卡片）：
   - 总发票数
   - 总金额（价税合计）
   - 总税额
   - 最近开票日期

2. **金额趋势图**：
   - 按月/按日切换
   - 柱状图：发票数量 + 金额双轴
   - 使用轻量图表库（如 recharts）

3. **分类统计**：
   - 按发票类型（饼图 + 表格）
   - 按销售方（横向柱状图 Top N + 表格）
   - 维度切换器

4. **数据表格**：
   - 每个图表下方附带数据表格，确保不擅长读图的用户也能获取信息

**图表库选择**：推荐 `recharts`（已在 React 生态中广泛使用，与 Vite 兼容好）

---

### 步骤 6：更新前端 App.tsx 路由

修改 `frontend/src/App.tsx`，使用 `Layout` 组件包裹路由：

```tsx
<Router>
  <Routes>
    <Route element={<Layout />}>
      <Route path="/" element={<UploadPage />} />
      <Route path="/invoices" element={<InvoiceListPage />} />
      <Route path="/invoices/:id" element={<InvoiceDetailPage />} />
      <Route path="/stats" element={<StatsPage />} />
    </Route>
  </Routes>
</Router>
```

---

### 步骤 7：创建 Windows 启动脚本

#### 7.1 新建 `start_app.bat`（项目根目录）

```batch
@echo off
chcp 65001 >nul
title 发票分析系统

echo ================================
echo   发票分析系统 InvoiceMaster
echo ================================
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

:: 安装后端依赖
echo [1/4] 检查后端依赖...
cd /d "%~dp0backend"
python -m pip install -r requirements.txt -q

:: 构建前端
echo [2/4] 构建前端页面...
cd /d "%~dp0frontend"
call npm install --silent
call npm run build

:: 启动后端服务
echo [3/4] 启动服务...
cd /d "%~dp0backend"
start /b python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

:: 等待服务就绪
echo [4/4] 等待服务就绪...
timeout /t 3 /nobreak >nul

:: 打开浏览器
start http://127.0.0.1:8000

echo.
echo 服务已启动！浏览器将自动打开。
echo 按任意键停止服务...
pause >nul

:: 停止服务
taskkill /f /im python.exe >nul 2>&1
```

---

## Data Flow

```
用户上传 PDF 
    → 前端 POST /api/invoices/upload (multipart/form-data)
    → 后端保存文件到 upload_dir
    → pdf_extractor 提取文本+表格
    → text_normalizer 清洗标准化
    → invoice_parser 映射为 Invoice + InvoiceItem
    → 写入 SQLite
    → 返回解析结果给前端
    → 前端跳转到列表页展示
```

## Verification Steps

1. **单文件解析验证**：上传 `template/1.pdf`，检查详情页各字段是否完整准确
2. **多文件解析验证**：上传携程发票 PDF，检查列表页和统计页汇总
3. **字段准确性抽查**：
   - 发票代码/号码是否正确
   - 开票日期格式是否正确
   - 购买方/销售方名称是否完整
   - 金额/税额/价税合计数字是否正确
   - 行项目明细（名称、数量、单价、金额、税率、税额）是否正确
4. **重复上传验证**：上传同一文件两次，检查是否有重复提示
5. **前端页面验证**：
   - 上传页拖拽/点击是否正常
   - 列表页筛选/分页是否正常
   - 详情页字段展示是否完整
   - 统计页图表+表格是否正常渲染
6. **启动脚本验证**：双击 `start_app.bat` 后服务是否正常启动并打开浏览器
