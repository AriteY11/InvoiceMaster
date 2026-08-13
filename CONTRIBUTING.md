# 贡献指南

感谢你参与 InvoiceMaster 发票管理系统的开发。本文档定义项目的开发规范，请在提交任何代码前阅读并遵守。

## 版本管理

对项目做任何代码改动时，**必须**同步更新版本号与用户手册：

### 版本号三处同步

版本号定义在三个位置，改动时需全部保持同步：

| 位置 | 说明 |
|------|------|
| `backend/app/config.py` | `Settings` 类中的 `app_version` 字段 |
| `frontend/src/components/Layout.tsx` | 页面头部 `<span>vX.Y.Z</span>` 文本（如 `v1.0.1`） |
| `InvoiceMaster_部署手册与使用说明.docx` | 封面及正文中的版本号 |

### 版本递增规则

| 版本段 | 适用场景 |
|--------|----------|
| **Major（X.0.0）** | 破坏性变更、重大新功能、大规模 UI 重构 |
| **Minor（X.Y.0）** | 新功能、非破坏性增强 |
| **Patch（X.Y.Z）** | Bug 修复、小改进、文档更新 |

### 用户手册再生成

新增功能或重大变更后，需要重新生成根目录的 `InvoiceMaster_部署手册与使用说明.docx`，并确保封面与正文中的版本号与代码一致。

## 提交规范

使用 Conventional Commits 格式：`type(scope): description`

| type | 用途 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 仅文档变更 |
| `refactor` | 既不修复 Bug 也不添加功能的代码改动 |
| `style` | 格式、空白等样式调整 |
| `chore` | 构建流程或辅助工具变更 |

示例：`fix(invoices): 修复导出 Excel 时金额精度丢失`

## 代码风格

- **Python**：遵循 `backend/app/` 中现有代码模式；除非明确要求，不添加注释。
- **TypeScript / React**：遵循 `frontend/src/` 中现有代码模式；使用 `@/lib/utils` 导出的 `cn()` 合并 className。
- **构建验证**：提交前端改动前必须运行 `npm run build` 确认构建通过。

## 本地开发

```bash
# 安装后端依赖
cd backend
pip install --target vendor -r requirements.txt

# 安装并构建前端
cd frontend
npm install
npm run build

# 启动服务（Windows 一键启动，或手动运行）
start_app.bat
# 或
cd backend && python run.py
```

启动后访问 http://127.0.0.1:8000 ，健康检查：`curl http://127.0.0.1:8000/api/health`

## 提交前检查清单

- [ ] 版本号三处同步更新
- [ ] 手册文档版本号一致（如涉及功能变更）
- [ ] 前端改动已通过 `npm run build`
- [ ] Commit 信息符合 Conventional Commits 格式
