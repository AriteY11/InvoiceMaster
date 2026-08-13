# AGENTS.md

面向 AI 编码助手的项目规则。完整规范见 [CONTRIBUTING.md](./CONTRIBUTING.md)。

## 版本同步（改代码必做）

版本号定义在三个位置，改动后**必须全部同步**：

1. `backend/app/config.py` — `Settings.app_version`
2. `frontend/src/components/Layout.tsx` — 头部 `<span>vX.Y.Z</span>`
3. `InvoiceMaster_部署手册与使用说明.docx` — 封面及正文

递增规则：Major（破坏性/重大功能）、Minor（新功能/增强）、Patch（修复/小改进/文档）。

## 提交信息

Conventional Commits：`type(scope): description`
`feat` / `fix` / `docs` / `refactor` / `style` / `chore`

## 代码风格

- Python：遵循 `backend/app/` 现有模式，除非明确要求不加注释。
- TypeScript/React：遵循 `frontend/src/` 现有模式，用 `@/lib/utils` 的 `cn()` 合并 className。
- 前端改动后运行 `npm run build` 验证构建。
- 双版本构建：`npm run build:offline`（离线版 → dist）/ `npm run build:online`（在线版 → dist-online）。
- 桌面打包：`pyinstaller packaging/InvoiceMaster_offline.spec` 或 `InvoiceMaster_online.spec`；Linux 部署见 `deploy/linux/README.md`。
