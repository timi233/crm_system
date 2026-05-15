# 项目建设协调计划

日期：2026-05-15
协调负责人：agent2

## 分工约定

- `agent2`：计划、协调、状态归档；每次更新 plan 必须同步到本地文档。
- `agent1`：咨询、关键问题确认、方案评审。
- `agent3`：施工、代码修改、验证执行。

## 当前状态快照

当前仓库处于大变更收口阶段，不建议直接开启新的大模块开发。

- 工作区存在大量未提交变更：`git status --short | wc -l` 为 `116`。
- 后端全量测试通过：`cd backend && APP_ENV=test ./venv/bin/python -m pytest -q`，结果 `265 passed, 10 warnings`。
- 前端测试通过：`cd frontend && npm test -- --run`，结果 `3 files / 26 tests passed`。
- 前端构建通过：`cd frontend && npm run build` 成功，但仍有 `antd`、`echarts` 大 chunk 警告。
- Alembic 当前单 head：`feishu_handover_fk_20260514 (head)`。
- 当前明确门禁问题：已由 `agent3` 清理，`git diff --check` 通过。

## 已完成主线

- 销售任务管理闭环已完成并验收，参考 `docs/sales-target-management-completion-plan-2026-05-12.md`。
- 日报/周报与角色化工作台已完成至 P5.2，P5.3 评论通知、P5.4 定时提醒/飞书推送延期，参考 `docs/daily-weekly-report-dashboard-implementation-plan-2026-05-13.md`。
- 飞书集成代码侧 mock 验证完成，真实租户联调仍缺外部凭证和开放平台配置，参考 `docs/feishu-integration-implementation-plan-2026-05-13.md`。
- 飞书组织同步与离职交接已有代码和测试，当前需纳入本轮大变更收口验收。

## 当前阻塞项

### S0：可提交状态收口

状态：已完成。

目标：先清理当前工作区，使已有建设成果达到可审查、可提交、可回归状态。

必须处理：

- 修复 `git diff --check` 报出的 trailing whitespace。
- 复跑后端全量测试、前端测试、前端构建。
- 复查 Alembic head 是否仍为单 head。
- 输出本轮变更分组建议，避免 100+ 文件混在一个不可审查提交中。

当前已知空白问题：

- `backend/tests/test_feishu_dispatch_integration.py`
- `frontend/src/components/lists/UserList.tsx`

收口验收结果：

- `git diff --check`：通过。
- `git diff --cached --check`：通过。
- `cd backend && ./venv/bin/alembic heads`：`feishu_handover_fk_20260514 (head)`。
- `cd backend && APP_ENV=test ./venv/bin/python -m pytest -q`：`265 passed, 10 warnings`。
- `cd frontend && npm test -- --run`：`3 test files, 26 passed`。
- `cd frontend && npm run build`：成功，仍存在大 chunk 警告。

本轮格式修复文件：

- `backend/tests/test_feishu_dispatch_integration.py`
- `frontend/src/components/lists/UserList.tsx`
- `frontend/src/pages/Dashboard.tsx`

验收命令：

```bash
git diff --check
cd backend && ./venv/bin/alembic heads
cd backend && APP_ENV=test ./venv/bin/python -m pytest -q
cd frontend && npm test -- --run
cd frontend && npm run build
```

### S1：变更分组与审查

状态：分组核对已完成，待用户确认是否进入下一阶段施工。

目标：把当前大变更拆成可审查单元。

建议分组：

- 组织/角色/权限基础：`channel_ops`、`department_manager_id`、policy deny-by-default、分页上限。
- 日报/周报与角色化工作台：模型、router、service、前端页面、hook、dashboard 组件。
- 飞书诊断/组织同步/离职交接：飞书集成 router、service、migration、CLI、handover。
- 销售任务管理闭环：销售目标规则、前端树组件、相关测试。
- 前端 Vite 迁移与构建基础：`vite.config.ts`、`vitest.config.ts`、`index.html`、Docker/nginx/package 变更。
- 派工/飞书卡片与工单联动：work order、dispatch、feishu card/ws/notification 相关变更。
- 文档与环境模板：README、计划文档、`.env.example`、真实 `.env*` 删除确认。

当前分组原则：

- 优先拆出 S0 门禁修复和文档协调变更，避免混入业务提交。
- 后端 migration、model、router、service、test 应按业务域成组审查，不能只按技术层拆散。
- 前端 Vite 迁移属于基础设施组，应与日报/周报页面功能组区分。
- 删除真实 `.env.production`、`.env.test` 应归入安全/环境模板组，提交说明必须明确“删除真实环境文件，不提交密钥”。

agent3 核对结论：

- 全部 `123` 个变更项已归组。
- 未归组文件：`0`。
- 主要修正：`backend/alembic/versions/work_reports_20260513.py` 应归入 S1-F 日报/周报与角色化工作台，不归入 S1-H 派工/工单/飞书卡片联动。
- 主要修正：`frontend/src/hooks/useRoleDashboard.test.tsx` 应归入 S1-F，不归入 S1-B。
- 跨组共享文件需要在提交说明中明确主归属，避免后续组重复修改同一入口文件。

跨组文件主归属：

- `backend/tests/conftest.py`：主归属 S1-C，S1-H 测试依赖其 fixture。
- `backend/app/main.py`：主归属 S1-C，作为后续 S1-F/S1-G 路由注册的应用入口。
- `frontend/src/App.tsx`：主归属 S1-F，包含日报/周报页面路由。
- `frontend/src/services/api.ts`：主归属 S1-B，包含 Vite API 适配和基础错误处理。
- `backend/app/models/__init__.py`：主归属 S1-C，集中导入后续业务模型。

建议审查顺序：

1. `S1-A 安全与工程基础`：`.gitignore`、`backend/.env.example`、删除 `backend/.env.production`、删除 `backend/.env.test`、README 环境说明。
2. `S1-B Vite/Vitest 迁移`：`frontend/package*.json`、`frontend/index.html`、`frontend/vite.config.ts`、`frontend/vitest.config.ts`、`frontend/src/test/setup.ts`、`frontend/vite-env.d.ts`、删除 CRA 入口和 `setupProxy.js`、Docker/nginx 调整。
3. `S1-C 组织角色与权限基础`：`backend/app/core/roles.py`、`backend/app/models/user.py`、`backend/app/schemas/user.py`、`backend/app/routers/user.py`、`frontend/src/utils/roles.ts`、`frontend/src/components/lists/UserList.tsx`、相关测试。
4. `S1-D 分页与默认拒绝策略`：`backend/app/core/policy/base.py`、分页 router 修复、`backend/tests/test_pagination.py`、`backend/app/routers/alert.py`。
5. `S1-E 销售任务管理闭环`：`backend/app/routers/sales_target.py`、`backend/app/schemas/sales_target.py`、`frontend/src/components/lists/SalesTargetTree.tsx`、`frontend/src/hooks/useSalesTargets.ts`、删除旧 `SalesTargetList.tsx`、销售目标测试。
6. `S1-F 日报/周报与角色化工作台`：`work_report` model/schema/router/service/policy/migration/tests，`dashboard_workbench_service.py`，dashboard schema/router，前端 `components/dashboard`、`components/work-reports`、`useRoleDashboard`、`useWorkReports`、`WorkReportPage`、`WorkReportDetailPage`、`MyDashboard`、`App.tsx` 路由。
7. `S1-G 飞书诊断、组织同步与离职交接`：飞书 migration、`backend/app/cli.py`、`backend/app/routers/integrations/feishu.py`、`feishu_diagnostics_service.py`、`feishu_org_sync_service.py`、handover model/router/service/tests。
8. `S1-H 派工/工单/飞书卡片联动`：`work_order` model/router、`dispatch.py`、`feishu_card_service.py`、`feishu_service.py`、`feishu_ws_service.py`、`work_order_notification_service.py`、相关派工测试。
9. `S1-I 文档与协调记录`：`AGENTS.md`、`.agents/business-domain.md`、`docs/*2026-05-12.md`、`docs/*2026-05-13.md`、`docs/project-coordination-plan-2026-05-15.md`。

组间依赖：

- S1-A 无依赖，应最先审查。
- S1-B 依赖 S1-A，先稳定 `.gitignore` 与环境模板，再审查构建迁移。
- S1-C 依赖 S1-A，用户模型、角色、fixture 是多个业务组的基础。
- S1-D 依赖 S1-C，策略层与角色能力有关。
- S1-E 依赖 S1-C，销售目标测试依赖用户和 fixture。
- S1-F 依赖 S1-C/S1-D，日报/周报依赖用户、角色、policy 基础。
- S1-G 依赖 S1-C，飞书组织同步与交接依赖用户飞书字段和离职状态。
- S1-H 依赖 S1-C，派工测试依赖共享 fixture。
- S1-I 建议最后审查，作为最终文档归档。

推荐提交/审查顺序：`S1-A → S1-B → S1-C → S1-D → S1-E → S1-F → S1-G → S1-H → S1-I`。

分组验证命令：

```bash
# S1-A
git diff --check
test ! -e backend/.env.production
test ! -e backend/.env.test
grep -c 'env.production' .gitignore

# S1-B
cd frontend && npm test -- --run
cd frontend && npm run build

# S1-C
cd backend && APP_ENV=test ./venv/bin/python -m pytest tests/test_auth.py -q

# S1-D
cd backend && APP_ENV=test ./venv/bin/python -m pytest tests/test_pagination.py -q

# S1-E
cd backend && APP_ENV=test ./venv/bin/python -m pytest tests/test_sales_target_rules.py tests/test_sales_target_flow.py -q

# S1-F
cd backend && APP_ENV=test ./venv/bin/python -m pytest tests/test_work_reports.py tests/test_work_report_reminders.py tests/test_dashboard_workbench.py -q
cd frontend && npm test -- --run

# S1-G
cd backend && APP_ENV=test ./venv/bin/python -m pytest tests/test_feishu_diagnostics.py tests/test_feishu_org_sync.py tests/test_feishu_oauth.py tests/test_handover.py -q

# S1-H
cd backend && APP_ENV=test ./venv/bin/python -m pytest tests/test_feishu_dispatch_integration.py tests/test_work_orders.py -q

# S1-I
git diff --cached --stat
```

S1 完成标准：

- 每个分组都有清晰说明、风险点、验证命令。
- 每个分组可独立 `git add -- <paths>`，且不遗漏同一业务域的测试。
- 分组之间存在依赖时必须标注，例如日报/周报依赖组织角色与权限基础。
- 不要求立即提交，但要达到可审查提交边界。

### S2：下一阶段建设入口

状态：离职交接前端入口已完成，通知中心最小闭环已进入施工派发阶段。

下一阶段优先级：

1. 离职交接前端管理入口：补齐当前已存在后端能力的管理页面，作为 S1 收口而非全新模块。
2. 通知中心最小闭环：站内通知模型、列表、已读、业务跳转、安全权限，并合并 P5.3 日报/周报评论通知。
3. 任务/日程/提醒中心最小闭环：统一待办、跟进提醒、合同到期、工单 SLA，承接 RoleDashboard 现有 todos/risks。
4. P5.4 定时提醒/飞书推送：放到通知中心交付之后，与飞书真实租户联调同阶段启动。

通知中心计划文档：

- `docs/notification-center-plan-2026-05-15.md`

通知中心施工拆分：

- N0/N1/N2：后端通知 schema/service/router/tests，dashboard 旧通知接口兼容，统一写入入口。
- N3：前端通知中心 hook、列表页、顶部入口、业务跳转。
- N4：P5.3 日报/周报评论模型、接口、前端评论区、评论通知。
- N5：验收与文档归档。

任务/日程/提醒中心计划文档：

- `docs/todo-reminder-center-plan-2026-05-15.md`

任务/日程/提醒中心施工边界：

- 首版采用派生待办模式，不新增通用 `todos` 表。
- 后端新增 `/todos` 聚合 API。
- 前端新增 `/todos` 页面。
- 聚合跟进、合同、工单、日报/周报、离职交接待办。
- 工作台待办摘要跳转 `/todos`。
- 不做通用完成/延期/关闭，不做日历视图，不接飞书推送。

施工派发策略：

- 按用户要求，本阶段目标是完成通知中心全部 N0-N5。
- 默认交给 `agent3` 做完整施工，`agent2` 负责接收结果、归档状态、必要时再协调复验或补充派工。
- `agent1` 暂不追加咨询，除非施工中出现评论权限、通知泄露或飞书外发边界争议。

agent1 咨询结论：

- 离职交接后端已具备 `list/get/assets-preview/assign/execute/cancel` 能力，但前端无 handover 入口；应优先补齐管理员管理入口，避免后端能力空转。
- 通知中心已有 `Notification` 模型和 dashboard 通知接口雏形，但缺统一读取 API、写入约定和前端入口；应作为下一批基础设施。
- P5.3 日报/周报评论通知建议并入通知中心最小闭环，评论模型独立，通知 fanout 走通知中心。
- 任务/日程/提醒中心应在通知中心之后做，避免提醒 fanout 和待办聚合重复建设。
- P5.4 定时提醒/飞书推送不应夹进通知中心首批，应等调度方案和飞书真实租户联调具备条件后启动。

需要用户拍板的问题：

- 离职交接前端权限边界：仅 `admin` 可见，还是 `admin + 部门负责人 + 当事人` 三方视图。默认建议先做 admin 主入口，当事人侧只读跟进状态。
- 通知中心首批是否接飞书外发。默认建议先纯站内，不引入真实飞书依赖。
- 日报/周报评论模型形态：默认建议独立 `WorkReportComment` 表，不复用 `Notification` 表表达评论实体。
- 任务/日程/提醒中心定位：默认建议独立路由 `/todos`，工作台保留卡片摘要并跳转。

可按默认推进的项：

- 通知中心 P0 范围：复用现有 `Notification` 表，新增 `GET /notifications`、`POST /notifications/mark-read`、`POST /notifications/mark-all-read`，前端右上角通知抽屉、全屏列表页、业务跳转。
- 通知写入约定：现有写入点统一走 `notification_service.create()`，避免散点写库。
- 离职交接前端：管理员侧采用“列表 + 详情 + 分配 + 执行 + 取消”动作，复用现有 Ant Design、BrandCard、UnifiedStatistic 风格。
- P5.3 评论：随通知中心一起落地，评论提交后写一条 `entity_type=work_report` 通知给被评论人和上级。

## 当前派工单

### 给 agent3：离职交接前端管理入口

状态：已完成，agent2 补齐菜单入口。
Job：`job_f1db19f6c865`

目标：

- 补齐现有后端 handover 能力的管理员前端入口。
- 默认只做 `admin` 主入口，不做部门负责人视图、当事人只读视图。

首版功能范围：

- 交接请求列表。
- 交接详情。
- 资产预览。
- 分配接收人。
- 执行交接。
- 取消交接。
- 加载态、空状态、错误提示、权限控制。

验收命令：

```bash
cd frontend && npm test -- --run
cd frontend && npm run build
git diff --check
```

完成结果：

- 新增 `frontend/src/hooks/useHandovers.ts`。
- 新增 `frontend/src/pages/HandoverListPage.tsx`。
- 新增 `frontend/src/pages/HandoverDetailPage.tsx`。
- 修改 `frontend/src/App.tsx`，注册 `/handovers` 与 `/handovers/:id`。
- 修改 `backend/app/routers/auth.py`，为 admin 暴露 `handover:read` capability。
- 修改 `frontend/src/pages/Dashboard.tsx`，在“系统管理”分组按 `handover:read` 显示“离职交接”菜单入口。

已完成能力：

- 交接请求列表，支持状态筛选和离职人员/接收人搜索。
- 交接详情，展示基本信息、资产预览、执行结果。
- 分配接收人、执行交接、取消交接。
- 首版仅面向 `admin`。

延期项：

- 部门负责人视图。
- 当事人只读视图。
- 通知中心集成。

验收结果：

- `cd frontend && npm test -- --run`：`3 test files, 26 passed`。
- `cd frontend && npm run build`：通过，仍有 `antd`、`echarts` 大 chunk 警告。
- `cd backend && APP_ENV=test ./venv/bin/python -m pytest tests/test_handover.py tests/test_auth.py -q`：`12 passed, 10 warnings`。
- `git diff --check`：通过。

### 给 agent3：S1 变更分组核对

状态：已完成。
Job：`job_852bff93c319`

硬约束：

- 只读核对，不修改文件。
- 不要 `git add`。
- 不要 `commit`。
- 不要 `reset/checkout/delete`。

期望输出：

- S1-A 到 S1-I 每组路径清单。
- 未归组文件或重复归组文件。
- 组间提交依赖。
- 每组验证命令。
- 每组精确 `git add -- <paths>` 建议，但不执行。

### 给 agent3：S0 可提交状态收口

状态：已完成。
Job：`job_9811f2209a61`

允许编辑范围：

- 仅修复 `git diff --check` 的 trailing whitespace。
- 如验证发现同类低风险格式门禁问题，可一并修复。
- 不要做业务逻辑扩展，不要重构，不要提交。

期望输出：

- 修改文件列表。
- `git diff --check` 结果。
- 后端全量测试结果。
- 前端测试与构建结果。
- Alembic head 检查结果。
- 如发现阻塞项，列出具体文件和原因。

### 给 agent1：下一阶段优先级咨询

状态：已完成。
Job：`job_f1011b3201e8`

咨询范围：

- 基于当前业务计划和已完成能力，判断下一阶段应优先建设通知中心、任务/日程/提醒中心，还是离职交接前端入口。
- 输出推荐顺序和理由。
- 标注哪些问题需要用户拍板，哪些可以按默认方案推进。

## 下一步施工建议

默认推进路径：

1. 当前大变更继续按 S1 分组作为审查/提交边界保留。
2. 离职交接前端入口已完成，下一步进入通知中心最小闭环。
3. 通知中心第一段建议先施工 N0/N1/N2 后端基础，避免前端先行后接口返工。
4. 默认纯站内通知，不接飞书外发。

通知中心施工前默认边界：

- 复用现有 `Notification` 表。
- 新增独立 `/notifications` API。
- `Notification.is_read/read_at` 作为首版已读状态来源，`UserNotificationRead` 保留兼容。
- 新增独立 `WorkReportComment` 表。
- 通知中心首批不做订阅规则、不做飞书外发、不做定时提醒。

## 决策记录

- 2026-05-15：agent2 判断当前优先级为 S0/S1 收口，原因是工作区变更过大且存在 `git diff --check` 门禁失败；新功能应在可提交状态恢复后再启动。
- 2026-05-15：agent2 已将 S0 收口施工派发给 `agent3`，将下一阶段优先级咨询派发给 `agent1`。按 CCB fire-and-forget 规则，不轮询、不等待。
- 2026-05-15：`agent3` 完成 S0 收口，所有验收命令通过，无阻塞；下一步进入 S1 变更分组与审查。
- 2026-05-15：`agent1` 完成下一阶段优先级咨询。S2 顺序调整为离职交接前端入口、通知中心最小闭环含 P5.3、任务/日程/提醒中心；P5.4 延后到飞书真实租户联调阶段。
- 2026-05-15：agent2 已将 S1 变更分组核对派发给 `agent3`，要求只读核对并输出 `git add -- <paths>` 建议。
- 2026-05-15：`agent3` 完成 S1 变更分组核对，覆盖全部 123 个变更项，提出 work_reports migration 归属修正。
- 2026-05-15：`agent3` 施工离职交接前端管理入口最小闭环，验收通过。新增 `handover:read` 能力至 auth router，创建前端列表页、详情页、hook 层。

## 离职交接前端施工记录

状态：已完成。
Job：`job_f1db19f6c865`

### 实现说明

- **路由**：`/handovers`（列表）、`/handovers/:id`（详情），仅 `admin` 可访问（`handover:read` 能力）。
- **列表页**：展示所有交接请求，支持状态筛选、按离职人员/接收人搜索。
- **详情页**：展示交接基本信息（状态、离职人员、接收人、时间线）、资产预览表、执行结果摘要。
- **操作**：分配接收人（弹窗选择用户 + 资产范围）、执行交接（确认弹窗）、取消交接（可选原因）。
- **状态处理**：加载态（Spin）、空状态（locale emptyText）、错误提示（api interceptor + message）。
- **后端变更**：仅新增 `handover:read` capability 至 `backend/app/routers/auth.py`，不改业务逻辑。

### 修改文件

| 类型 | 路径 |
|---|---|
| 新增 | `frontend/src/hooks/useHandovers.ts` |
| 新增 | `frontend/src/pages/HandoverListPage.tsx` |
| 新增 | `frontend/src/pages/HandoverDetailPage.tsx` |
| 修改 | `frontend/src/App.tsx`（路由注册） |
| 修改 | `backend/app/routers/auth.py`（`handover:read` 能力） |

### 验收结果

- `cd frontend && npm test -- --run`：3 files, 26 tests passed
- `cd frontend && npm run build`：成功，630ms
- `cd backend && APP_ENV=test ./venv/bin/python -m pytest tests/test_handover.py -q`：7 passed
- `cd backend && APP_ENV=test ./venv/bin/python -m pytest tests/test_auth.py -q`：5 passed
- `git diff --check`：通过

### 未完成项

- 部门负责人视图、当事人只读视图（按默认边界延期）
- 通知中心集成（延期到通知中心交付后）
- 菜单侧边栏入口（需确认放置位置后再添加）
- 2026-05-15：`agent3` 完成 S1 分组核对。全部 `123` 个变更项已归组，未归组文件 `0`；已按建议修正 work reports migration 与 RoleDashboard 测试文件归属。
- 2026-05-15：agent2 已按默认推进路径，将“离职交接前端管理入口”施工派发给 `agent3`，首版范围限定为 admin 管理入口。
- 2026-05-15：`agent3` 完成离职交接前端入口施工；agent2 核对发现菜单入口缺失，已按现有结构补到“系统管理”分组。
- 2026-05-15：agent2 完成离职交接前端入口复验，前端测试/构建、handover/auth 后端测试、`git diff --check` 均通过。
- 2026-05-15：agent2 建立下一阶段 `docs/notification-center-plan-2026-05-15.md`，通知中心最小闭环进入计划阶段，默认先施工后端 N0/N1/N2。
- 2026-05-15：用户要求继续并完成本阶段全部任务，agent2 已将通知中心 N0-N5 从计划阶段推进到施工派发阶段。
- 2026-05-15：`agent3` 完成通知中心 N0-N5 功能施工。agent2 复核发现 Alembic 双 head 阻塞项，需先完成迁移链路收口后才能判定本阶段完全完成。
- 2026-05-15：`agent3` 完成 Alembic 收口，`work_report_comments_20260515` 接到 `feishu_handover_fk_20260514` 后；agent2 本地复核 `alembic heads` 唯一 head 为 `work_report_comments_20260515`，`git diff --check` 通过。通知中心阶段完成。
- 2026-05-15：用户要求开始建议目标范围工作。agent2 创建 `docs/todo-reminder-center-plan-2026-05-15.md`，并派发 `agent3` 施工任务/日程/提醒中心最小闭环，CCB job 为 `job_272daddfeb04`。
- 2026-05-15：`agent3` 完成任务/日程/提醒中心 T0-T4。agent2 本地复核 todos 专项、相关回归、后端全量、前端测试/构建、Alembic 单 head、`git diff --check` 均通过。本阶段完成。
- 2026-05-15：用户要求联合审查当前系统代码。agent2 负责后端，agent4 负责前端和原型设计，agent1 负责需求澄清和方案设计。前端构建错误、交接权限、`channel_ops` 能力、团队日报权限、派工分页、待办性能、产品装机策略层等问题已完成整改。
- 2026-05-15：用户拍板离职交接操作允许 `admin` 和部门负责人任意一方执行。后端 `assign/execute/cancel` 已改为 admin 全量、部门负责人仅限 `team_manager_user_id` 等于自己的交接单；前端详情页操作按钮同步按 `admin || team_manager_user_id == currentUser.id` 显示。
- 2026-05-15：用户确认金蝶/财务导出先隐藏。`kingdee_integration:read`、`financial_export:read`、`financial_export:summary` capability 已显式返回 `false`，README、AGENTS、review 文档均标明 router 文件存在但未注册，不能作为线上能力承诺。
- 2026-05-15：用户确认产品装机凭据按字段级加密方案整改。已新增 `PRODUCT_INSTALLATION_CREDENTIAL_KEY`、密文字段迁移、加密工具、存量加密清理脚本和测试；当前 Alembic head 更新为 `product_installation_credential_ciphertext_20260515`。
- 2026-05-15：agent3 完成前端 trailing whitespace 清理，`git diff --check`、前端测试、前端构建均通过。agent2 新增 `docs/project-finalization-report-2026-05-15.md` 记录本轮最终收口、部署注意事项和验证结果。
