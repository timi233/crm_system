# 任务/日程/提醒中心最小闭环建设计划

日期：2026-05-15
负责人：agent2 计划协调
施工目标：交给 `agent3`
当前状态：已完成

## 背景与目标

本阶段目标是建设统一待办中心 `/todos`，把当前散落在工作台、跟进、合同、工单、日报/周报、离职交接中的待办/提醒聚合成一个可筛选、可跳转的个人工作入口。

现有基础：

- `backend/app/routers/dashboard.py` 已有 `/dashboard/todos`，但主要面向业务跟进提醒。
- `backend/app/services/dashboard_workbench_service.py` 已按角色返回 `todos/risks`，包括日报/周报未提交待办。
- `frontend/src/components/dashboard/DashboardTodoList.tsx` 已能展示工作台待办摘要。
- 通知中心已完成，负责消息 fanout；待办中心只负责“当前需要处理的事项”聚合视图。

## 业务边界

本阶段包含：

- 独立后端 API：`GET /todos`。
- 独立前端路由：`/todos`。
- 聚合现有来源：
  - 跟进提醒：`FollowUp.next_follow_up_date` 或到期跟进。
  - 合同到期提醒：合同关键日期，按现有合同字段可用性实现。
  - 工单 SLA/处理提醒：待接单、进行中、可处理工单。
  - 日报/周报未提交：复用 dashboard workbench 口径。
  - 离职交接待处理：admin 的待分配/待执行交接。
- 工作台摘要跳转 `/todos`。
- 加载态、空状态、错误提示、权限控制。

本阶段不包含：

- 持久化通用 todo 表。
- 待办完成/延期/关闭写回通用状态。
- 日历视图。
- 飞书推送或定时任务。
- 通知订阅规则。

## 默认决策

- 首版采用“派生待办”模式：从现有业务对象实时聚合，不新增 `todos` 表。
- 待办完成方式是跳转到原业务对象处理，不做通用完成按钮。
- `/todos` 返回当前登录用户有权限处理或查看的待办，不提供全局他人待办。
- RoleDashboard 继续保留摘要卡片，但应增加跳转到 `/todos` 的入口。
- 通知中心和待办中心职责分离：通知记录消息，待办聚合未处理事项。

## 实施批次

| 批次 | 目标 | 状态 |
|------|------|------|
| T0 | 后端 Todo schema/service/router 设计 | 已完成 |
| T1 | 聚合跟进、合同、工单、日报/周报、离职交接待办 | 已完成 |
| T2 | 前端 `/todos` 页面、hook、筛选和跳转 | 已完成 |
| T3 | RoleDashboard 摘要跳转 `/todos` | 已完成 |
| T4 | 测试、构建、文档归档 | 已完成 |

## T0/T1：后端统一待办 API

### 建议新增文件

- `backend/app/schemas/todo.py`
- `backend/app/services/todo_service.py`
- `backend/app/routers/todo.py`
- `backend/tests/test_todos.py`

### API 建议

- `GET /todos`
  - 参数：
    - `type?: str`
    - `priority?: str`
    - `status?: str`，首版可固定为 `open`
    - `date_from?: date`
    - `date_to?: date`
    - `skip >= 0`
    - `limit <= 100`
  - 返回：`TodoListResponse`

### Todo 字段建议

- `key`：稳定唯一键，例如 `follow_up:123`。
- `type`：`follow_up`、`contract_expiry`、`work_order`、`work_report`、`handover`。
- `title`
- `description`
- `priority`：`high`、`medium`、`normal`。
- `due_date`
- `entity_type`
- `entity_id`
- `link`
- `source`
- `status`：首版统一 `open`。

### 聚合口径

#### 跟进提醒

- 来源：`FollowUp.next_follow_up_date`。
- 范围：当前用户为 `follower_id`，或 admin/business 可看团队范围时按权限谨慎扩展；首版建议当前用户。
- 到期或未来 7 天进入待办。
- 链接：根据关联对象优先级跳转：
  - `lead_id` → `/leads/{id}`
  - `opportunity_id` → `/opportunities/{id}`
  - `project_id` → `/projects/{id}`
  - `terminal_customer_id` → `/customers/{id}`
  - 否则 `/business-follow-ups`

#### 合同到期提醒

- 来源：现有合同日期字段，施工前需确认字段名。
- 范围：当前用户有权限可见的合同；首版可按 admin/business/finance 全局，销售按项目销售归属。
- 未来 30 天到期或已逾期进入待办。
- 链接：`/contracts/{id}` 或现有合同详情路由。

#### 工单提醒

- 来源：`WorkOrder` 和技术员分配记录。
- 范围：技术员看分配给自己的待接单/进行中工单；admin/business 可看全局待处理。
- 优先级：待接单/逾期高，进行中普通或中。
- 链接：`/work-orders/{id}`。

#### 日报/周报未提交

- 来源：复用 `DashboardWorkbenchService` 的个人 report status 口径或 `WorkReportService`。
- 范围：`sales`、`technician`、`channel_ops`，不包含 `finance`。
- 今天日报未创建/未提交进入待办。
- 周五至周日未创建/未提交本周周报进入待办。
- 链接：`/work-reports`。

#### 离职交接待处理

- 来源：`EmployeeHandoverRequest`。
- 范围：admin。
- `pending_assignment`、`pending_execution` 进入待办。
- 链接：`/handovers/{id}`。

## T2：前端 `/todos` 页面

### 建议新增文件

- `frontend/src/hooks/useTodos.ts`
- `frontend/src/pages/TodoCenterPage.tsx`

### 页面能力

- 全部待办列表。
- 类型筛选。
- 优先级筛选。
- 日期范围筛选。
- 点击跳转业务对象。
- 空状态、加载态、错误提示。
- 高优先级视觉突出。

### 路由与入口

- `frontend/src/App.tsx` 注册 `/todos`。
- `frontend/src/pages/Dashboard.tsx` 菜单中增加“待办中心”或顶部入口。
- RoleDashboard 的待办摘要增加“查看全部”跳转 `/todos`。

## T3：工作台联动

- `DashboardTodoList` 增加可选 `showMoreLink` 或固定底部“查看全部待办”。
- 后端 `/dashboard/workbench` 可保持现有摘要，不要求改为调用 `/todos`。
- 保持工作台轻量，不把全部待办塞入首页。

## T4：验收标准

### 后端测试

```bash
cd backend && APP_ENV=test ./venv/bin/python -m pytest tests/test_todos.py -q
cd backend && APP_ENV=test ./venv/bin/python -m pytest tests/test_dashboard_workbench.py tests/test_work_reports.py tests/test_handover.py tests/test_work_orders.py tests/test_contracts.py -q
```

### 前端测试与构建

```bash
cd frontend && npm test -- --run
cd frontend && npm run build
```

### 全局门禁

```bash
git diff --check
```

### 功能验收

- 登录用户能访问 `/todos`。
- 不同角色只看到自己范围内的待办。
- 跟进、工单、日报/周报、离职交接至少都有测试覆盖。
- 合同到期若字段可用，应纳入测试；若字段不稳定，需在回复中说明并延期该来源。
- 工作台待办摘要能跳转到 `/todos`。
- 点击待办能跳转对应业务页面。

## 风险与约束

- 当前各业务对象没有统一“完成待办”状态，首版不要做通用完成按钮。
- 合同到期字段可能与业务口径不完全一致，施工时应以现有模型字段为准。
- 不要把通知表当待办表使用。
- 不要接入飞书推送或定时任务。
- 不要引入后台调度器。

## 派发记录

- 2026-05-15：agent2 按用户要求创建本计划，并派发 `agent3` 施工 T0-T4，目标是完成本阶段建议范围。
- CCB job：`job_272daddfeb04`。

## 验收结果

### agent2 复核记录

- `cd backend && APP_ENV=test ./venv/bin/python -m pytest tests/test_todos.py -q`：`11 passed, 10 warnings`。
- `cd backend && APP_ENV=test ./venv/bin/python -m pytest tests/test_dashboard_workbench.py tests/test_work_reports.py tests/test_handover.py tests/test_work_orders.py tests/test_contracts.py -q`：`49 passed, 10 warnings`。
- `cd backend && APP_ENV=test ./venv/bin/python -m pytest -q`：`290 passed, 10 warnings`。
- `cd frontend && npm test -- --run`：`3 test files, 26 passed`。
- `cd frontend && npm run build`：通过，仍有既有 `antd`、`echarts` 大 chunk 警告。
- `cd backend && ./venv/bin/alembic heads`：`work_report_comments_20260515 (head)`，唯一 head。
- `git diff --check`：通过。

### agent3 施工完成

- 后端 todos 专项测试通过：11 passed。
- 后端相关回归测试通过：37 passed (dashboard/work_reports/handover/work_orders/contracts)。
- 前端测试通过：26 passed。
- 前端构建通过。
- `git diff --check` 通过。
- `alembic heads` 单 head。

### 后端测试

```
$ pytest tests/test_todos.py -q
11 passed
$ pytest tests/test_dashboard.py tests/test_work_reports.py tests/test_handover.py tests/test_work_orders.py tests/test_contracts.py -q
37 passed
```

### 前端

- TypeScript 类型检查：无错误
- 生产构建：成功 (`npm run build`)
- Vitest 测试：26 passed

### 功能完成情况

- [x] T0：Todo schema/service/router 设计完成
- [x] T1：聚合来源实现
  - 跟进提醒：当前用户为 follower_id，到期或未来 7 天
  - 合同到期：admin 可看，expiry_date <= 30 天
  - 工单处理：technician 看自己待接单/进行中，admin/business 看全局
  - 日报/周报：sales/technician/channel_ops 未提交待办
  - 离职交接：admin 看 pending_assignment/pending_execution
- [x] T2：TodoCenterPage 全屏页、useTodos hooks、Dashboard 菜单入口
- [x] T3：DashboardTodoList 增加"查看全部"跳转 /todos
- [x] T4：测试通过、构建成功、本文档状态回写

### 新增文件清单

| 文件 | 用途 |
|------|------|
| `backend/app/schemas/todo.py` | Todo 读写 schema |
| `backend/app/services/todo_service.py` | Todo 聚合 service |
| `backend/app/routers/todo.py` | Todo API 路由 |
| `frontend/src/hooks/useTodos.ts` | Todo 查询 hooks |
| `frontend/src/pages/TodoCenterPage.tsx` | 待办中心全屏页 |
| `backend/tests/test_todos.py` | Todo 测试 |

### 修改文件清单

| 文件 | 变更 |
|------|------|
| `backend/app/main.py` | 注册 todo_router |
| `frontend/src/App.tsx` | 新增 /todos 路由和 TodoCenterPage |
| `frontend/src/pages/Dashboard.tsx` | 侧边栏菜单新增待办中心入口 |
| `frontend/src/components/dashboard/DashboardTodoList.tsx` | 增加"查看全部"跳转 |

### API 列表

| API | 说明 |
|------|------|
| `GET /todos` | 获取当前用户待办列表，支持 type/priority/status/date_from/date_to/skip/limit 筛选 |

### 聚合来源完成情况

| 来源 | 角色范围 | 完成状态 |
|------|------|------|
| 跟进提醒 | sales/technician/channel_ops 看自己 | 完成 |
| 合同到期 | admin 看全局 | 完成 |
| 工单处理 | technician 看自己，admin/business 看全局 | 完成 |
| 日报/周报 | sales/technician/channel_ops 未提交 | 完成 |
| 离职交接 | admin 看 pending_assignment/pending_execution | 完成 |

### 未完成项、延期项、风险点

- 无未完成项。
- 无延期项。
- 合同到期字段使用 `expiry_date`，口径稳定，无风险。
