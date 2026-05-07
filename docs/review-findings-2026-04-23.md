# 前后端 Review Findings - 2026-04-23

## Scope

本次审查覆盖主 CRM 系统：

- 后端：`backend/` FastAPI、认证、配置、数据库、路由挂载。
- 前端：`frontend/` React、路由、API 客户端、关键业务页面。

未深入审查独立目录 `new_task_mgt/`。

## Findings

### High: 客户/项目抽屉保存没有调用后端

- 位置：
  - `frontend/src/pages/CustomerListPage.tsx:58`
  - `frontend/src/pages/ProjectListPage.tsx:57`
  - `frontend/src/hooks/useCustomers.ts:23`
  - `frontend/src/hooks/useProjects.ts:40`
- 现象：`handleSave` 只关闭抽屉、`refetch()`、显示成功提示，没有调用已有的 `useCreateCustomer`、`useUpdateCustomer`、`useCreateProject`、`useUpdateProject`。
- 影响：用户点击“新建/编辑”后界面提示成功，但数据没有保存到后端，刷新后变更丢失。
- 建议：在列表页接入 create/update mutation，按是否有 `editingCustomer` / `editingProject` 调用不同接口；成功后再关闭抽屉并刷新。

### High: 客户/项目列表跳转到不存在的详情路由

- 位置：
  - `frontend/src/pages/CustomerListPage.tsx:76`
  - `frontend/src/pages/CustomerListPage.tsx:111`
  - `frontend/src/pages/ProjectListPage.tsx:75`
  - `frontend/src/pages/ProjectListPage.tsx:117`
  - `frontend/src/App.tsx:113`
  - `frontend/src/App.tsx:124`
- 现象：列表页跳转到 `/customers/:id`、`/projects/:id`，但实际注册的是 `/customers/:id/full`、`/projects/:id/full`。
- 影响：点击客户或项目“查看”会进入未匹配路由，用户无法打开详情页。
- 建议：统一跳转路径为 `/customers/${id}/full`、`/projects/${id}/full`，或补充对应短路径路由重定向。

### High: 合同模块组件存在但没有路由入口

- 位置：
  - `frontend/src/App.tsx:112-143`
  - `frontend/src/components/lists/ContractList.tsx:66`
  - `frontend/src/components/lists/ContractList.tsx:87`
- 现象：`ContractList`、`ContractForm`、`ContractFullViewPage` 已导入，但 `App.tsx` 未注册 `/contracts`、`/contracts/new`、`/contracts/:id/full`。
- 影响：合同管理功能无法通过路由访问；组件内部跳转也会落到不存在页面。
- 建议：在 `App.tsx` 增加合同相关路由，并在侧边栏恢复合同菜单入口。

### Medium: 飞书用户再用邮箱密码登录可能触发 500

- 位置：
  - `backend/app/models/user.py:15`
  - `backend/app/routers/auth.py:254`
  - `backend/app/routers/auth.py:310`
- 现象：`User.hashed_password` 可为空，飞书新用户创建时不设置密码；邮箱密码登录路径直接调用 `verify_password(form_data.password, user.hashed_password)`。
- 影响：同一邮箱的飞书用户尝试密码登录时，可能因 `hashed_password=None` 导致服务端异常，而不是返回 401。
- 建议：登录判断改为 `if not user or not user.hashed_password or not verify_password(...)`，并补充测试覆盖 OAuth-only 用户的密码登录。

### Medium: 数据库配置源不统一且包含硬编码默认凭据

- 位置：
  - `backend/app/database.py:6`
  - `backend/app/core/config.py:18`
  - `backend/alembic.ini:3`
- 现象：应用数据库连接直接从 `os.getenv("DATABASE_URL")` 读取并提供硬编码默认值；`Settings.database_url` 另有一套默认值；Alembic 又使用 `alembic.ini` 中的同步 URL。
- 影响：应用运行、迁移、测试可能连接不同数据库；默认凭据也增加误部署和泄露风险。
- 建议：统一从 `get_settings().database_url` 读取；Alembic `env.py` 从环境变量或 Settings 注入 URL；移除真实样式默认密码，生产环境缺少配置应启动失败。

### Medium: 项目产品选择不会被保存

- 位置：
  - `frontend/src/components/forms/ProjectForm.tsx:24`
  - `frontend/src/components/forms/ProjectForm.tsx:55`
  - `frontend/src/components/forms/ProjectForm.tsx:221`
  - `frontend/src/components/modals/ProjectDrawer.tsx:23`
  - `frontend/src/components/modals/ProjectDrawer.tsx:49`
  - `frontend/src/components/modals/ProjectDrawer.tsx:217`
- 现象：`EntityProductSelect` 通过 `setProductList` 收集选择结果，但提交 payload 没有包含 `productList`。
- 影响：用户选择的产品类型、品牌、型号、数量、单价会被静默丢弃。
- 建议：确认后端项目保存接口期望字段；若已有 `entity-products` 独立接口，应在项目创建成功后用返回的项目 ID 批量保存产品关联。

## Verification

- 前端构建：`cd frontend && npm run build` 通过。
- 构建警告：主 JS gzip 后约 `883.92 kB`，CRA 提示 bundle 过大，建议后续做路由级代码分割。
- 后端测试：未能执行。当前环境缺少 `pytest`，`pytest -q` 和 `python3 -m pytest -q` 均失败，错误为未找到 `pytest` 模块。

## Suggested Fix Order

1. 修复客户/项目保存没有调用后端的问题。
2. 修复客户/项目详情跳转路径和合同路由缺失。
3. 修复飞书 OAuth-only 用户密码登录异常。
4. 统一数据库配置与 Alembic URL。
5. 明确并实现项目产品关联保存流程。
6. 安装后端测试依赖并跑完整测试集。

## Post-Fix Check - 2026-04-23 09:45

检查 commit `7edaad4 fix(crm): 修复 review-findings-2026-04-23 中的所有高优问题` 后，以下问题仍需继续修复。

### High: 项目产品关联保存仍不可用

- 位置：
  - `frontend/src/pages/ProjectListPage.tsx:85`
  - `frontend/src/pages/ProjectListPage.tsx:88`
  - `frontend/src/components/common/EntityProductSelect.tsx:65`
  - `frontend/src/hooks/useEntityProducts.ts:38`
  - `backend/app/models/entity_product.py:6`
- 当前代码问题：
  - `EntityProductSelect` 输出字段为 `product_type_id`、`brand_id`、`model_id`、`quantity`、`unit_price`。
  - `ProjectListPage` 保存时却读取 `product.type_id`、`product.type_name`、`product.brand_name`、`product.model_name`，会导致 `product_type_id` 传 `undefined`。
  - 前端会 POST `/entity-products`，但后端当前只有 `EntityProduct` model，没有注册对应 router/API；`rg "entity-products|EntityProduct|entity_products" backend/app` 没有发现 router。
  - 产品保存失败被内部 `catch` 吞掉，只 `console.warn`，用户仍可能看到项目创建成功。
- 影响：项目可以创建，但产品关联仍无法保存；用户选择的产品数据仍会丢失。
- 修复要求：
  - 先确认是否应实现 `/entity-products` 后端 API。如果采用独立关联表，请新增 router/schema 并在 `app/main.py` 注册。
  - 前端保存字段必须使用 `product_type_id`，不要读取不存在的 `type_id`。
  - 如果需要保存数量、单价，先确认 `entity_products` 表/model 是否包含字段；没有字段时不要静默丢弃，应补迁移或从 UI 移除。
  - 产品关联保存失败不能假装完全成功。至少应提示“项目已保存，但产品关联保存失败”。
  - 覆盖创建项目后保存产品关联的 happy path。

### Medium: Alembic 迁移可能被 asyncpg URL 改坏

- 位置：
  - `backend/alembic/env.py:45`
  - `backend/alembic/env.py:46`
  - `backend/app/core/config.py:18`
- 当前代码问题：
  - `env.py` 从 `get_settings().database_url` 读取 URL。
  - `Settings.database_url` 默认是 `postgresql+asyncpg://...`。
  - `env.py` 的 online migration 使用同步 `sqlalchemy.create_engine(url, ...)`，不应直接使用 asyncpg driver URL。
- 影响：执行 `alembic upgrade head` 时可能因同步 engine 使用 async driver 而失败，或要求不必要的 async driver 依赖。
- 修复要求：
  - 为 Alembic 同步迁移把 `postgresql+asyncpg://` 转换为 `postgresql+psycopg2://` 或 `postgresql://`。
  - 保持 FastAPI 运行时仍使用 asyncpg URL。
  - `alembic.ini` 不应包含真实凭据；可保留 placeholder，但 `env.py` 应优先使用环境/Settings 并做 driver 转换。
  - 增加一个轻量函数测试或至少用脚本验证 URL 转换逻辑。

### Verification After Follow-Up Fix

- 必须运行：`cd frontend && npm run build`。
- 必须尝试：`cd backend && python3 -m pytest -q`；如果缺依赖，明确说明缺少哪些模块。
- 建议尝试：在后端依赖可用时执行 `cd backend && alembic current` 或 `alembic upgrade head --sql` 验证 Alembic URL 逻辑。

## Remaining Issues - 2026-04-23 10:25

当前状态：

- 前端构建通过：`cd frontend && npm run build`。
- 后端测试通过：`cd backend && venv/bin/python -m pytest -q`，结果 `66 passed, 8 warnings`。
- 本轮 `/entity-products/` API、正式迁移、产品关联保存、权限兼容 shim、capabilities 行为和 follow-up 测试夹具已修复。

### Medium: 前端 bundle 偏大

- 现象：生产构建通过，但主 JS gzip 后约 `887.41 kB`，CRA 提示 bundle size significantly larger than recommended。
- 影响：首屏加载性能较差，后续页面越多越明显。
- 建议：
  - 对 `App.tsx` 中的页面组件做路由级 lazy loading/code splitting。
  - 优先拆分报表、渠道全景、客户全景、工单详情等非首屏页面。
  - 保持登录页和主布局可快速加载。
  - 修改后运行 `cd frontend && npm run build`，确认主 chunk 明显下降。

### Low: 后端测试 warnings 需要清理

- 现象：pytest 通过但有 8 个 warnings。
- 主要来源：
  - `app/schemas/finance_view.py` 使用 Pydantic V1 风格 `class Config`，在 Pydantic V2 下弃用。
  - `app/schemas/user.py` 使用 Pydantic V1 风格 `class Config`。
  - `app/services/operation_log_service.py` 使用 `datetime.utcnow()`，Python 3.13 下提示弃用。
- 建议：
  - 将相关 schema 改为 `model_config = ConfigDict(from_attributes=True)`。
  - 将 `datetime.utcnow()` 改为 timezone-aware 的 `datetime.now(datetime.UTC)` 或项目统一的时间工具。
  - 修改后运行 `cd backend && venv/bin/python -m pytest -q`，目标是 `66 passed` 且 warnings 数量下降。

### Medium: Alembic 尚未做真实迁移验证

- 现状：`alembic/env.py` 已做 asyncpg URL 到同步 PostgreSQL URL 的转换，新增了 `entity_products_001` 迁移；但尚未连接真实数据库执行迁移验证。
- 风险：真实环境可能因数据库连接、driver、已有表结构或迁移链路问题失败。
- 建议：
  - 在可用数据库环境中执行 `cd backend && venv/bin/alembic current`。
  - 如可接受，再执行 `cd backend && venv/bin/alembic upgrade head`。
  - 如果本地没有可用数据库，至少执行 `cd backend && venv/bin/alembic upgrade head --sql` 验证 SQL 生成。

### Low: 当前改动尚未提交

- 现象：当前工作树仍有未提交改动和新增文件，包括 `docs/review-findings-2026-04-23.md`。
- 建议：
  - 完成上述剩余修复和验证后，检查 `git status --short`。
  - 若用户确认，整理为一个或多个 commit；不要自动提交，除非用户明确要求。

## Post-Opencode Check - 2026-04-23 10:35

检查 `opencode` 针对 Remaining Issues 的改动后，当前状态如下：

- 前端构建通过：`cd frontend && npm run build`。
- 主 JS gzip 从约 `887.41 kB` 降至 `826.65 kB`，已产生多个 lazy chunks；但 CRA 仍提示主 bundle 偏大。
- 后端测试通过：`cd backend && venv/bin/python -m pytest -q`，结果 `66 passed in 0.24s`。
- 后端 warnings 已清理到当前测试输出中不再出现。
- `opencode` 的 CCB job 被标记为 `incomplete / ccbd_restart_requires_resubmit`，但代码改动已落到工作树。

### Medium: Alembic offline SQL 生成失败

- 命令：`cd backend && venv/bin/alembic upgrade head --sql`
- 结果：失败。
- 失败位置：
  - `backend/alembic/versions/product_installations_001.py:21`
  - `backend/alembic/env.py:54`
- 错误摘要：
  - `sqlalchemy.exc.NoInspectionAvailable: No inspection system is available for object of type <class 'sqlalchemy.engine.mock.MockConnection'>`
- 根因：
  - 既有迁移 `product_installations_001.py` 在 offline SQL 模式中调用 `sa.inspect(bind)`。
  - `alembic upgrade --sql` 使用的是 mock connection，不能做 inspector/introspection。
  - 这不是新增 `entity_products_001` 迁移的直接错误，但导致当前 Alembic offline SQL 验证不可用。
- 修复要求：
  - 修改 `product_installations_001.py`，让迁移在 offline SQL 模式下不调用 `sa.inspect(bind)`。
  - 可选方案：在 offline 模式直接输出幂等 DDL，或封装 helper，在 `context.is_offline_mode()` 时跳过 introspection。
  - 保持 online 模式下的幂等检查能力。
  - 修复后必须重新运行 `cd backend && venv/bin/alembic upgrade head --sql`。

### Low: 前端 bundle 仍偏大

- 当前主 JS gzip：约 `826.65 kB`。
- 已改善：相比 `887.41 kB` 下降约 60 kB。
- 剩余问题：CRA 仍提示 bundle significantly larger than recommended。
- 建议：
  - 继续拆分非首屏重型列表/表单组件，例如合同、工单、知识库、报表相关列表。
  - 避免过度改动布局和路由语义；保持现有路由行为不变。
  - 修复后运行 `cd frontend && npm run build`，记录主 chunk 变化。

### Low: 当前改动仍未提交

- 当前工作树仍有未提交改动和新增文件。
- 本轮仍不要自动 commit，除非用户明确要求。

### Verification Required

- `cd backend && venv/bin/alembic upgrade head --sql`
- `cd backend && venv/bin/python -m pytest -q`
- `cd frontend && npm run build`

## Migration History Risk - 2026-04-23 11:20

检查 `opencode` 针对 Alembic offline SQL 的修复后，虽然验证命令已通过，但它全量重写了多个历史 migration 为 PostgreSQL raw SQL。这个方向存在部署历史风险，需要调整为更保守的方案。

### Medium: 不应大范围重写已存在的历史 migration

- 当前风险文件：
  - `backend/alembic/versions/product_installations_001.py`
  - `backend/alembic/versions/channel_integration_001.py`
  - `backend/alembic/versions/create_customer_channel_links.py`
  - `backend/alembic/versions/add_lead_source_channel.py`
  - `backend/alembic/versions/dispatch_records_001_dispatch_records_table.py`
  - `backend/alembic/versions/channel_followup_leads_001.py`
  - `backend/alembic/versions/follow_up_optimization_001.py`
  - `backend/alembic/versions/execution_plan_category_001.py`
- 问题：
  - 这些 revision 如果已经在某些环境执行过，修改同一个 revision 文件会造成“同 revision id，不同迁移内容”的环境差异。
  - raw SQL 重写可能改变约束名、索引选项、nullable、默认值、外键规则和 downgrade 语义。
  - 大量 PostgreSQL raw SQL 会降低迁移的可维护性；即使项目目标数据库是 PostgreSQL，也应避免不必要地重写历史。
- 推荐修复方向：
  - 不要全量重写历史 migration。
  - 对已经被改写的历史 migration，尽量恢复原有 online 模式逻辑。
  - 仅为 `alembic upgrade head --sql` 增加最小 offline-safe 分支：在 `context.is_offline_mode()` 时避免 `sa.inspect(bind)`，输出对应的 offline-safe DDL。
  - 如果某个 schema 修复不是 offline SQL 兼容问题，而是新功能字段/索引，请使用新的后续 migration，不要塞回旧 revision。
  - 保留本轮新增的 `entity_products_001` migration，因为它是新增功能迁移。
- 验证要求：
- `cd backend && venv/bin/alembic upgrade head --sql`
- `cd backend && venv/bin/python -m pytest -q`
- `cd frontend && npm run build`
- `git diff --check`

## Migration Rework Failed Check - 2026-04-23 11:50

检查 `opencode` 针对 “Migration History Risk” 的返工后，结论：不能接受当前改动。

### High: 返工没有按要求收敛历史 migration 改动

- `opencode` 回复称“只修改 2 个 migration”，但实际工作树仍显示 8 个历史 migration 被改：
  - `backend/alembic/versions/add_lead_source_channel.py`
  - `backend/alembic/versions/channel_followup_leads_001.py`
  - `backend/alembic/versions/channel_integration_001.py`
  - `backend/alembic/versions/create_customer_channel_links.py`
  - `backend/alembic/versions/dispatch_records_001_dispatch_records_table.py`
  - `backend/alembic/versions/execution_plan_category_001.py`
  - `backend/alembic/versions/follow_up_optimization_001.py`
  - `backend/alembic/versions/product_installations_001.py`
- 其中多个文件仍是全量 raw SQL 重写，不符合“恢复 online 原逻辑，仅 offline 最小分支”的要求。
- `git diff --check` 失败，`backend/alembic/versions/channel_integration_001.py` 仍有 trailing whitespace。

### 强约束返工要求

必须严格执行以下约束：

1. **禁止继续大范围重写历史 migration。**
2. 必须恢复以下 6 个历史 migration 到本轮改动前的状态，不允许保留 raw SQL 重写：
   - `backend/alembic/versions/add_lead_source_channel.py`
   - `backend/alembic/versions/channel_followup_leads_001.py`
   - `backend/alembic/versions/create_customer_channel_links.py`
   - `backend/alembic/versions/dispatch_records_001_dispatch_records_table.py`
   - `backend/alembic/versions/execution_plan_category_001.py`
   - `backend/alembic/versions/follow_up_optimization_001.py`
3. 仅允许修改以下迁移文件，且必须采用“online 保留原 introspection 逻辑 + offline 最小 safe DDL 分支”的方式：
   - `backend/alembic/versions/product_installations_001.py`
   - `backend/alembic/versions/channel_integration_001.py`
4. 允许保留新增功能迁移：
   - `backend/alembic/versions/entity_products_001.py`
5. 不允许使用 `git reset --hard`、`git checkout -- .` 等会丢弃无关工作树改动的破坏性命令。
6. 如果要恢复单个文件，只能针对上述明确文件做精确恢复，不能覆盖其他业务修复。
7. 必须清理所有 trailing whitespace，`git diff --check` 必须通过。
8. 不要自动 commit。

### 必须验证

返工完成后必须运行并汇报：

- `git diff --check`
- `cd backend && venv/bin/alembic upgrade head --sql`
- `cd backend && venv/bin/python -m pytest -q`
- `cd frontend && npm run build`

### 当前验证状态，仅供参考

- `cd backend && venv/bin/alembic upgrade head --sql` 当前通过。
- `cd backend && venv/bin/python -m pytest -q` 当前通过，`66 passed`。
- `cd frontend && npm run build` 当前通过，主 JS gzip `788.72 kB`。
- 但由于历史 migration 改动范围不符合要求且 `git diff --check` 失败，当前改动不能接受。

## Migration Rework Second Failed Check - 2026-04-23 13:05

再次检查 `opencode` 针对 “Migration Rework Failed Check - 2026-04-23 11:50” 的返工后，结论：仍不能接受。

### Critical: 6 个要求恢复的历史 migration 仍然存在 diff

`opencode` 回复称已恢复 6 个历史 migration，但实际 `git diff --name-only -- <6 files>` 仍然输出以下文件：

- `backend/alembic/versions/add_lead_source_channel.py`
- `backend/alembic/versions/channel_followup_leads_001.py`
- `backend/alembic/versions/create_customer_channel_links.py`
- `backend/alembic/versions/dispatch_records_001_dispatch_records_table.py`
- `backend/alembic/versions/execution_plan_category_001.py`
- `backend/alembic/versions/follow_up_optimization_001.py`

这说明上一轮“恢复历史 migration”的汇报不准确。即使 Alembic SQL、pytest、frontend build 通过，只要上述 6 个文件仍有 diff，本轮返工就判定失败。

### 强制验收门禁

返工完成后，以下命令必须无输出且退出码为 0：

```bash
git diff --quiet -- \
  backend/alembic/versions/add_lead_source_channel.py \
  backend/alembic/versions/channel_followup_leads_001.py \
  backend/alembic/versions/create_customer_channel_links.py \
  backend/alembic/versions/dispatch_records_001_dispatch_records_table.py \
  backend/alembic/versions/execution_plan_category_001.py \
  backend/alembic/versions/follow_up_optimization_001.py
```

如果该命令失败，禁止回复“已完成”。必须继续修复。

### 强约束返工要求

1. 必须让上述 6 个文件相对当前 `HEAD` 完全无 diff。
2. 禁止继续在上述 6 个文件中保留“去 introspection 化”的改写、格式化改写、revision 链改写、raw SQL 改写或注释翻译。
3. 只允许继续保留/调整以下两个 migration 文件：
   - `backend/alembic/versions/product_installations_001.py`
   - `backend/alembic/versions/channel_integration_001.py`
4. 上述两个允许修改的文件必须遵循：online 模式保留原 introspection 逻辑；offline 模式只增加最小 safe DDL 分支，目的仅是让 `alembic upgrade head --sql` 可生成。
5. 保留新增功能迁移：
   - `backend/alembic/versions/entity_products_001.py`
6. 严禁使用 `git reset --hard`、`git checkout -- .` 等会丢弃无关工作树改动的命令。
7. 如果使用 git 内容恢复，只能精确恢复上述 6 个文件，例如先读取 `git show HEAD:<path>` 再精确写回对应文件；不能覆盖其他业务修复。
8. 不要自动 commit。

### 必须验证并贴出结果

- `git diff --quiet -- <上述 6 个文件>`
- `git diff --check`
- `cd backend && venv/bin/alembic upgrade head --sql`
- `cd backend && venv/bin/python -m pytest -q`
- `cd frontend && npm run build`

最终回复必须包含：

- 6 个历史 migration 的 `git diff --quiet` 验收结果。
- 实际仍有 diff 的 migration 文件列表。
- 四项验证命令结果。
- 若仍不能满足任一门禁，必须明确说“未完成”，不能报告完成。

## Independent Check After Second Rework - 2026-04-23 13:20

本地独立复核 `opencode` 第二次返工后，确认当前状态如下：

### 已通过

- 6 个要求恢复的历史 migration 已相对当前 `HEAD` 无 diff：
  - `backend/alembic/versions/add_lead_source_channel.py`
  - `backend/alembic/versions/channel_followup_leads_001.py`
  - `backend/alembic/versions/create_customer_channel_links.py`
  - `backend/alembic/versions/dispatch_records_001_dispatch_records_table.py`
  - `backend/alembic/versions/execution_plan_category_001.py`
  - `backend/alembic/versions/follow_up_optimization_001.py`
- `git diff --check` 通过。
- `cd backend && venv/bin/python -m pytest -q` 通过，`66 passed`。
- `cd frontend && npm run build` 通过，主 JS gzip `788.72 kB`。

### 仍失败

- `cd backend && venv/bin/alembic upgrade head --sql` 失败。
- 失败点：
  - `backend/alembic/versions/create_customer_channel_links.py:22`
  - `sqlalchemy.exc.NoInspectionAvailable: No inspection system is available for object of type <class 'sqlalchemy.engine.mock.MockConnection'>`
- 根因：
  - 当前要求恢复的 6 个历史 migration 在 `HEAD` 原始内容中本身包含 `sa.inspect(bind)` 或 `inspect(bind)`。
  - Alembic offline SQL 模式使用 mock connection，无法执行 inspector/introspection。

### 结论

当前存在互斥约束：

- 若要求 6 个历史 migration 完全无 diff，则它们会保留原始 introspection，`alembic upgrade head --sql` 必然失败。
- 若要求 `alembic upgrade head --sql` 从空库全量生成成功，则必须修改这些历史 migration，至少增加 offline-safe 分支或改写为 offline-safe DDL。

### 可选决策

1. 接受修改历史 migration：为所有含 introspection 的历史 migration 增加最小 `context.is_offline_mode()` 分支，让 `alembic upgrade head --sql` 可全量生成。
2. 保持历史 migration 完全无 diff：取消“从空库全量 `alembic upgrade head --sql` 必须通过”的门禁，改用 online migration 验证或仅从指定基线 revision 之后生成 SQL。
3. 新建 baseline/squash 方案：保留历史 revision，不再要求旧链路 offline 全量可生成；后续以新的基线 migration 管理部署。

## Final Offline Migration Check - 2026-04-23 16:20

`opencode` 后续任务的 CCB 状态最终为 `failed pane_dead`，但其工作区改动已落地。独立复核后发现并修复了一个遗漏：

- `backend/alembic/versions/create_customer_channel_links.py` 的 offline 分支原先跳过了原有数据回填 INSERT。
- 已补回与 online 分支一致的 `INSERT INTO customer_channel_links ... SELECT ... FROM terminal_customers ...`，避免 offline SQL 与 online migration 语义不一致。

### 当前验证结果

- `git diff --check` 通过。
- `cd backend && venv/bin/alembic upgrade head --sql` 通过，生成 `/tmp/crm_alembic_upgrade_head.sql`，共 `609` 行。
- 生成 SQL 已确认包含 `INSERT INTO customer_channel_links` 回填语句。
- `cd backend && venv/bin/python -m pytest -q` 通过，`66 passed`。
- `cd frontend && npm run build` 通过，主 JS gzip `788.72 kB`，CRA 仍提示 bundle size larger than recommended。

### 当前剩余注意点

- 8 个历史 migration 都已为 offline SQL 增加 `context.is_offline_mode()` 分支；online 分支仍保留 introspection 幂等逻辑。
- 前端主 bundle 仍偏大，但已从最初约 `887.41 kB` 降到 `788.72 kB`。
- 当前工作树仍未提交，包含 backend/frontend 修复、新增 entity product 文件和本文档。

## Feishu Dispatch Implementation Review - 2026-04-24

对 `opencode` 按《飞书外勤审批联动方案设计》落地的代码进行独立复核后，发现以下实现问题需要修复。

### Critical: WebSocket 服务未接入实际处理器，整条确认/回写链路未生效

- `backend/app/services/feishu_ws_service.py`
- 问题：
  - 卡片交互事件和审批状态事件的 dispatcher 注册仍被注释掉。
  - `_on_im_message_card_action` / `_on_approval_status_changed` 只打日志，没有调用实际 handler。
  - `main.py` 已在 startup 启动该服务，但当前启动的是“空接线”版本。
- 修复要求：
  - 必须把卡片交互事件路由到 `process_card_action`。
  - 必须把审批状态事件路由到 `handle_approval_status_changed`。
  - 若 SDK typed dispatcher 接法不稳定，允许改为基于原始事件 payload 的显式解析与分发，但不能继续只打日志。

### High: 卡片按钮 payload 与处理器协议不一致

- `backend/app/services/feishu_card_service.py`
- `backend/app/handlers/card_action_handler.py`
- 问题：
  - 卡片按钮 `value` 目前是 JSON 字符串，字段名为 `action=confirm_receipt`。
  - 处理器要求读取结构化字段 `action_type`，且只识别 `confirm` / `reject`。
  - 卡片里还缺少“拒绝接收”按钮。
- 修复要求：
  - 卡片按钮 payload 必须与处理器协议统一。
  - 至少提供 `confirm` / `reject` 两个动作。
  - 处理器需兼容飞书事件中 `value` 可能为对象或 JSON 字符串的情况。

### High: 审批创建字段映射错误

- `backend/app/handlers/card_action_handler.py`
- `backend/app/services/feishu_approval_service.py`
- 问题：
  - handler 传入审批服务的是顶层 `customer_name`，审批服务却从 `customer.name` 取值，导致客户名称实际会传空。
  - `sales_contact` 被错误地填成当前技术员本人，而不是工单关联销售。
- 修复要求：
  - 审批数据结构必须统一，客户名称不能再丢失。
  - 如工单存在 `related_sales_id`，应按真实销售用户的飞书身份填入审批联系人。
  - 审批创建 payload 需与现有设计文档一致，避免继续使用互不兼容的数据形状。

### High: 请求作用域数据库会话被后台任务复用

- `backend/app/routers/work_order.py`
- 问题：
  - 派工后通过 `asyncio.create_task` 发送卡片，但后台任务继续复用请求内的 `db` session 更新 `feishu_message_id`。
  - 该 session 可能在请求结束后关闭，且不应被多个并发任务共享。
- 修复要求：
  - 后台任务必须使用独立的 `AsyncSession`。
  - 只把必要的标识数据传入后台任务，不要把请求会话或 ORM 对象直接闭包进 task。

### Medium: 缺少新链路回归测试

- `backend/tests/`
- 问题：
  - 当前没有针对卡片 payload、审批字段映射、事件分发、重复状态处理的测试。
- 修复要求：
  - 至少补充：
    - 卡片按钮 payload 协议测试；
    - 审批 widgets/form 映射测试；
    - WebSocket 事件 payload 分发测试；
    - 卡片 handler 对已处理状态/非法操作者的测试。

## Current System Code Review - 2026-04-27

对当前工作树再次复核后，发现以下问题需要继续修复。

### Critical: WebSocket 回调提交了协程，但事件循环并未实际消费

- `backend/app/services/feishu_ws_service.py`
- 问题：
  - 当前通过 `asyncio.run_coroutine_threadsafe(..., self._loop)` 分发卡片点击与审批状态事件。
  - 但 `self._loop` 在后台线程里只被创建和设置，从未显式运行；线程实际阻塞在 `lark_oapi` 自身的 `Client.start()`。
  - 结果是事件到达后协程不会被执行，卡片确认和审批回写仍无法落库。
- 修复要求：
  - 必须让 SDK 使用后台线程内的实际运行事件循环。
  - 必须在回调里把协程调度到当前正在运行的 loop，而不是投递到未运行的 loop。

### High: 卡片主按钮文案与业务动作相反

- `backend/app/services/feishu_card_service.py`
- 问题：
  - 第一颗按钮文案为“查看工单详情”，但点击后实际动作是 `confirm`，会直接确认接单并创建审批。
- 修复要求：
  - 按钮文案与动作必须一致；如果按钮执行确认接单，文案必须明确为确认类动作。
  - 若要保留查看详情能力，应独立提供查看入口，不能与确认动作复用。

### High: WebSocket 服务无法可靠停止，存在重复连接风险

- `backend/app/services/feishu_ws_service.py`
- `backend/app/main.py`
- 问题：
  - `stop()` 目前只改 `_running=False` 并打印日志，没有关闭底层连接，也没有结束后台 loop。
  - 应用 startup 每次都会拉起该服务，在 reload 或重复初始化场景下可能留下悬挂连接。
- 修复要求：
  - `stop()` 至少要触发底层连接断开并结束后台 loop。
  - 对 `lark_oapi` 无显式 `stop()` 的情况，需在本地封装可控的关闭流程。

### Medium: 审批结果回写未真正约束工单流转

- `backend/app/handlers/approval_status_handler.py`
- `backend/app/routers/work_order.py`
- 问题：
  - 当前审批回调只更新 `approval_status` 展示字段，没有约束工单进入 `IN_SERVICE` / `DONE`。
  - 审批被驳回后，前后端仍可继续推进工单状态。
- 修复要求：
  - 至少要在工单继续流转前校验存在已审批通过的技术员分配。
  - 审批结果回写应与工单主状态形成最小一致性约束，避免“审批驳回但继续服务”。

### Medium: 技术员候选人接口仍有页面使用旧逻辑

- `frontend/src/pages/WorkOrderDetailPage.tsx`
- `frontend/src/components/common/DispatchModal.tsx`
- 问题：
  - 新派工弹窗已切到 `/dispatch/technicians`，但工单详情页中的分配弹窗仍请求 `/users/?functional_role=TECHNICIAN`。
  - 两个入口的筛选和权限逻辑已经分叉。
- 修复要求：
  - 技术员候选人查询必须统一到同一后端接口，避免不同页面行为不一致。

## Global System Review - 2026-04-27

汇总本地复核与子 agent 并行审查后，当前系统仍存在以下高优先级问题。

### Critical: JWT 会回退到仓库内置固定密钥

- `backend/app/core/config.py`
- `backend/app/core/security.py`
- `backend/app/core/dependencies.py`
- 问题：
  - `secret_key` 默认值仍为仓库内置常量 `CHANGE_ME_SECRET_KEY`。
  - JWT 签发与验签会在 `JWT_SECRET_KEY` 缺失时回退到该固定值。
  - 任意漏配环境都可被已知固定密钥伪造 token。
- 修复要求：
  - 生产/测试环境必须强制要求显式 JWT 密钥。
  - 禁止回退到仓库内置常量参与签发或验签。

### Critical: 客户渠道关联创建接口存在越权写入

- `backend/app/routers/customer_channel_link.py`
- 问题：
  - 创建客户渠道关联前只校验了客户 `read` 权限。
  - 接口随后会创建 `CustomerChannelLink`，并在主渠道场景下直接改写 `TerminalCustomer.channel_id`。
  - 任何能查看客户的低权限用户，都可能篡改客户主渠道。
- 修复要求：
  - 创建客户渠道关联必须使用明确的写权限校验，而不是 `read`。
  - 改写主渠道应与客户更新权限保持一致。

### High: Feishu OAuth 首次登录会自动创建激活销售账号

- `backend/app/routers/auth.py`
- 问题：
  - 未识别的飞书用户会被自动创建为 `role="sales"` 且 `is_active=True`。
  - 缺少白名单、组织范围或预置账号门槛。
- 修复要求：
  - 首次登录必须受白名单/预注册/组织映射控制。
  - 禁止默认授予销售身份。

### High: `product_installation` 使用分叉鉴权逻辑

- `backend/app/routers/product_installation.py`
- 问题：
  - 独立解 token，只检查用户存在，不检查 `is_active`。
  - 密钥来源与主系统不一致，还带硬编码默认值。
  - 停用账号仍可访问该组接口。
- 修复要求：
  - 统一复用主系统 `get_current_user`。
  - 删除独立 JWT 解码和默认密钥。

### High: 派工历史查询接口绕过 `DispatchRecordPolicy`

- `backend/app/routers/dispatch.py`
- `backend/app/core/policy/resources/dispatch_record.py`
- 问题：
  - `/leads/{id}/dispatch-history`、`/opportunities/{id}/dispatch-history`、`/projects/{id}/dispatch-history` 直接返回记录。
  - 未对源对象做 `read` 权限校验。
  - 任意已登录用户只要知道业务 ID，即可读取他人派工历史。
- 修复要求：
  - 三个接口必须统一走 `DispatchRecordPolicy` 或对源对象做显式授权校验。

### High: `/dispatch/technicians` 绕过用户目录权限策略

- `backend/app/routers/dispatch.py`
- `backend/app/core/policy/resources/user.py`
- 问题：
  - 当前接口只有认证，没有经过用户资源范围控制。
  - 任意登录用户都可直接枚举全部技术员。
- 修复要求：
  - 技术员候选列表必须纳入用户权限策略，至少保持与 `/users?functional_role=TECHNICIAN` 同等约束。

### High: 多技术员审批状态机存在错误顺序依赖

- `backend/app/handlers/approval_status_handler.py`
- 问题：
  - 当前实现会在“先拒绝、尚无已通过分配”时把工单直接置为 `REJECTED`。
  - 后续再收到其他技术员的 `APPROVED` 事件，工单不会被拉回可继续状态。
  - 会形成“存在已批准技术员，但主工单仍是 REJECTED”的死状态。
- 修复要求：
  - 重新定义多技术员审批聚合规则。
  - 工单主状态必须由所有技术员审批结果聚合得出，不能被单个早到事件永久锁死。

### High: `dispatch_webhook` 可绕过审批门禁直接改工单主状态

- `backend/app/routers/dispatch.py`
- `backend/app/routers/work_order.py`
- 问题：
  - 外部 webhook 到达后可直接把工单推进到 `IN_SERVICE` / `DONE`。
  - 不经过工单状态接口中“至少一位审批通过技术员”的约束。
- 修复要求：
  - webhook 更新主状态前也必须复用审批门禁。
  - 禁止存在旁路状态推进逻辑。

### High: 卡片回调缺少并发控制

- `backend/app/handlers/card_action_handler.py`
- 问题：
  - 同一工单分配记录的确认/拒绝处理没有行级锁或版本控制。
  - 外部审批创建先于本地最终落库。
  - 重复点击、回调重试、并发 confirm/reject 时可能出现审批实例和数据库状态互相打架。
- 修复要求：
  - 对分配记录增加并发保护。
  - 外部审批创建与本地状态更新需要可幂等、可重试且保持顺序一致。

### High: 测试体系会掩盖真实回归

- `backend/tests/conftest.py`
- `backend/tests/test_work_orders.py`
- `backend/tests/test_follow_ups.py`
- `backend/tests/test_reports.py`
- 问题：
  - `ASGITransport(..., raise_app_exceptions=False)` 会把应用异常吞成 500。
  - 多个测试直接接受 `500` 为合法结果。
  - `FakeAsyncSession` 不执行真实 SQL/ORM/约束。
- 修复要求：
  - 默认测试应在路由抛异常时直接失败。
  - 不能再把 `500` 当作通过条件。
  - 关键链路需要补真实数据库或更接近真实 ORM 的集成测试。

### High: 仪表盘对工单实体跳转到了不存在的 `/full` 路由

- `frontend/src/pages/MyDashboard.tsx`
- `frontend/src/App.tsx`
- 问题：
  - 仪表盘多个入口统一把实体详情跳到 `/${route}/${id}/full`。
  - `work_order` 实际只注册了 `/work-orders/:id`，没有 `/full` 页面。
  - 点击工单类通知/待办/预警会进错页。
- 修复要求：
  - 工单详情路由映射必须与实际注册路由保持一致，不能套用通用 `/full` 规则。

### High: 任意单接口 `401` 都会把整站打回登录页

- `frontend/src/services/api.ts`
- `frontend/src/pages/CustomerFullViewPage.tsx`
- `frontend/src/hooks/useCustomerChannelLinks.ts`
- 问题：
  - 现在所有非 `skipAuthRedirect` 的 `401` 都会强制跳 `/login`。
  - 页面附属数据请求失败也会导致整页丢失上下文。
- 修复要求：
  - 区分“登录态失效”和“单接口未授权/异常”。
  - 附属查询的 `401` 不能默认直接触发全站登出跳转。

### Medium: 密码登录对 JWT payload 的浏览器端解析不安全

- `frontend/src/services/authService.ts`
- 问题：
  - 直接对 JWT payload 使用 `atob`，未处理 base64url 差异。
  - 合法 token 也可能触发浏览器端解码异常。
- 修复要求：
  - 不要自行用脆弱方式解析 JWT。
  - 若必须解析，需使用兼容 base64url 的安全实现。

### Medium: 密码登录失败没有可见错误反馈

- `frontend/src/pages/auth/Login.tsx`
- `frontend/src/store/slices/authSlice.ts`
- 问题：
  - 登录失败只写入 store，不展示到页面或消息提示。
- 修复要求：
  - 登录失败必须给出明确的可见反馈。

### Medium: 密码登录后当前用户名称会长期显示为伪造值

- `frontend/src/services/authService.ts`
- `frontend/src/components/auth/AuthBootstrap.tsx`
- `frontend/src/pages/Dashboard.tsx`
- `frontend/src/pages/MyDashboard.tsx`
- 问题：
  - 账号密码登录后前端手工拼了 `name: "User"`。
  - 后续 bootstrap 只更新角色，不会回填真实姓名。
- 修复要求：
  - 登录后用户信息必须来自可信后端返回或完整用户信息接口。

### Medium: Feishu WebSocket 生命周期仍不具备可观测性与可靠收口

- `backend/app/main.py`
- `backend/app/services/feishu_ws_service.py`
- 问题：
  - 后台线程启动失败不会阻止服务就绪。
  - `/health` 无法反映飞书链路是否已断。
  - 停止流程也未确认线程完成收口。
- 修复要求：
  - WebSocket 子系统需要明确的 ready/failed 状态暴露。
  - 健康检查和日志需可观测。
  - 关闭流程应确认线程和连接已收口。

### Medium: 前后端 refresh token 契约已经漂移

- `frontend/src/services/authService.ts`
- `backend/app/routers/auth.py`
- 问题：
  - 前端仍保留 `refresh_token` 与 `/auth/refresh` 调用定义。
  - 后端未提供对应接口，登录响应也不返回 refresh token。
- 修复要求：
  - 要么补齐 refresh 流程；
  - 要么删除前端残留契约，避免后续误接入。

### 当前建议修复顺序

1. 先修认证/授权面：
   - 固定 JWT 密钥策略
   - `customer_channel_link`
   - `dispatch-history`
   - `product_installation`
   - Feishu 自动开户
2. 再修飞书审批一致性：
   - 多技术员状态机
   - webhook 旁路
   - 卡片并发
3. 最后收前端：
   - 仪表盘错误路由
   - `401` 全局跳登录
   - 登录页反馈
   - JWT 解析与当前用户信息
