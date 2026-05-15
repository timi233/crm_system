# 日报/周报与角色化工作台开发拆分计划

日期：2026-05-13

关联设计：

- [日报/周报与角色化工作台设计](daily-weekly-report-and-role-dashboard-design-2026-05-13.md)
- [下一阶段业务模块建设计划](next-phase-business-modules-plan-2026-05-12.md)

## 目标范围

本计划覆盖：

- 新增渠道运营角色 `channel_ops`
- 新增部门负责人关系 `department_manager_id`
- 日报/周报管理
- 角色化工作台
- 日报/周报与工作台、待办、通知的基础联动

已确认业务口径：

- 日报是“用户当天系统操作结构化汇总 + 备注”。
- 周报是“本周日报聚合 + 周备注/周总结”。
- 日报/周报第一版不强制提交。
- 财务角色第一版不参与日报/周报，但保留财务工作台。
- 团队范围使用 `department_manager_id`，`sales_leader_id` 仅保留历史兼容。

## 总体实施批次

| 批次 | 目标 | 状态 |
|------|------|------|
| P0 | 组织与角色基础：`channel_ops`、`department_manager_id`、权限能力 | 已完成 |
| P1 | 日报/周报后端闭环：模型、Schema、Router、Policy、结构化快照 | 已完成 |
| P2 | 日报/周报前端页面：列表、详情、草稿、提交、撤回 | 已完成 |
| P3 | 角色化工作台接口：`/dashboard/workbench`、角色卡片、团队口径 | 已完成 |
| P4 | 工作台前端改造：按角色渲染不同模块 | 已完成 |
| P4.5 | 收口修复：日报快照日期过滤、Service 防御、团队视图测试 | 已完成 |
| P5.1 | 工作台未提交待办：个人日报/周报未提交进入 todos | 已完成 |
| P5.2 | 团队提交率统计：团队日报/周报真实提交状态 | 已完成 |
| P5.3 | 日报/周报评论通知 | 延期 |
| P5.4 | 定时提醒/飞书推送 | 延期 |

## P4.5/P5.1/P5.2 验收状态

截至 2026-05-13：

**P4.5 收口修复：**
- 模型字段类型检查确认：`Lead.created_at`、`Opportunity.created_at`、`Contract.created_at` 均为 `Date` 类型，无需使用 `func.date()`。
- `WorkOrder.created_at` 和 `Channel.created_at` 为 `TIMESTAMP` 类型，当前代码已正确使用 `func.date()`。
- Service 层增加 `get_team_reports` 的 limit 防御：`limit = min(max(limit, 1), 100)`。
- 新增测试 `test_daily_snapshot_service_returns_structure` 验证快照结构。

**P5.1 工作台未提交待办：**
- 修改 `dashboard_workbench_service.py`：
  - `_build_sales_workbench`、`_build_technician_workbench`、`_build_channel_ops_workbench` 中增加未提交日报/周报待办逻辑。
  - `daily == "not_created"` 时追加 `daily_report_missing` 待办（priority="high"）。
  - `weekly == "not_created"` 且当天为周五/周六/周日（`weekday >= 4`）时追加 `weekly_report_missing` 待办（priority="medium"）。
  - finance 角色不生成日报/周报待办（后端不返回 report_status）。
- 新增测试：
  - `test_workbench_sales_unsubmitted_daily_report_todo`
  - `test_workbench_channel_ops_unsubmitted_daily_report_todo`
  - `test_workbench_finance_no_report_todos` 增强 todos 验证。

**P5.2 团队提交率统计：**
- 修改 `dashboard_workbench_service.py`：
  - `_get_team_report_status` 实现真实统计逻辑：
    - business 角色统计全量 `sales/technician/channel_ops` 用户。
    - 查询今日日报提交数 (`status="submitted"`) / 成员总数。
    - 查询本周周报提交数 / 成员总数。
    - 返回格式：`"3/5 已提交"` 或 `"0/0 已提交"`。
  - 新增 `_get_department_manager_team_report_status` 用于部门负责人统计直属成员。
- 新增测试：
  - `test_workbench_business_team_report_status_format` 验证 business 团队提交率返回格式。
  - `test_workbench_department_manager_report_status` 验证部门负责人直属成员提交率已接入工作台。

**验收命令结果：**
- `cd backend && APP_ENV=test ./venv/bin/python -m pytest tests/test_work_reports.py -q`：20 passed, 10 warnings
- `cd backend && APP_ENV=test ./venv/bin/python -m pytest tests/test_dashboard_workbench.py -q`：14 passed, 10 warnings
- `cd backend && APP_ENV=test ./venv/bin/python -m pytest -q`：204 passed, 10 warnings
- `cd frontend && npm run build`：成功

## Claude Review 结论

Review 文件：[daily-weekly-report-dashboard-review-2026-05-13.md](daily-weekly-report-dashboard-review-2026-05-13.md)

截至 2026-05-13，P0-P4 架构和实现基本可用，后端 `199 passed`，前端构建成功。进入 P5 前需要先完成三个闭环风险修复：

- 高风险：日报结构化快照中部分 `created_at == report_date` 可能存在 `datetime` 与 `date` 精度不一致，导致当天数据漏统计。
- 高风险：团队日报/周报状态仍是 `_get_team_report_status` 的 `"team_view"` 占位，未展示真实提交率。
- 高风险：个人工作台只有 `report_status.not_created`，但未生成“今日日报未提交”“本周周报未提交”待办。

下一步施工采用方案 B：`P4.5 + P5.1 + P5.2`，先完成业务闭环；`P5.3` 评论通知和 `P5.4` 定时推送延期。

## P4.5：收口修复

### 后端任务

修改建议：

- `backend/app/services/work_report_service.py`
  - 将日报快照中所有以日期统计当天记录的条件统一为稳定日期过滤。
  - 对 `Lead.created_at`、`Opportunity.created_at`、`Contract.created_at`、`Channel.created_at` 等可能为 `DateTime` 的字段使用 `func.date(field) == report_date`。
  - 对已经是 `Date` 的字段保持直接比较，避免破坏现有模型。
  - `get_team_reports` 内增加 service 层防御：`limit = min(max(limit, 1), 100)`。
- `backend/tests/test_work_reports.py`
  - 增加日期过滤回归测试：构造当天带时间的线索/商机等记录，生成日报快照能统计到。
  - 增加团队接口 service 层 limit 防御测试。
  - 增加部门负责人团队视图测试，验证直属成员报告可见，非直属不可见。

### 验收标准

- 当天创建的业务对象不会因为 `datetime` 精度漏出日报快照。
- `get_team_reports(limit=999)` 最多返回 100 条。
- 部门负责人能查看直属成员日报/周报。
- `cd backend && APP_ENV=test ./venv/bin/python -m pytest tests/test_work_reports.py -q` 通过。

## P5.1：工作台未提交待办

### 后端任务

修改建议：

- `backend/app/services/dashboard_workbench_service.py`
  - 为 `sales`、`technician`、`channel_ops` 生成个人工作台时，先取得 `report_status`。
  - 如果今日日报 `daily == "not_created"`，向 `todos` 追加：
    - `key="daily_report_missing"`
    - `title="今日日报未提交"`
    - `description="生成并提交今天的工作报告"`
    - `priority="high"`
    - `link="/work-reports"`
  - 如果本周周报 `weekly == "not_created"` 且当天为周五、周六或周日，向 `todos` 追加：
    - `key="weekly_report_missing"`
    - `title="本周周报未提交"`
    - `description="生成并提交本周工作报告"`
    - `priority="medium"`
    - `link="/work-reports"`
  - 财务角色不得生成日报/周报待办。

### 前端任务

- `frontend/src/components/dashboard/DashboardTodoList.tsx`
  - 当前已能渲染后端 todos，原则上无需新增页面逻辑。
  - 如需优化展示，可对 `daily_report_missing`、`weekly_report_missing` 保持普通待办样式，不做特殊硬编码。

### 验收标准

- 销售/技术/渠道运营未生成今日日报时，`/dashboard/workbench.todos` 包含“今日日报未提交”。
- 周五至周日未生成本周周报时，`todos` 包含“本周周报未提交”。
- 财务角色 `todos` 不包含日报/周报待办。
- 前端工作台能直接展示上述待办，点击跳转 `/work-reports`。

## P5.2：团队提交率统计

### 后端任务

修改建议：

- `backend/app/services/dashboard_workbench_service.py`
  - 修改 `_get_team_report_status`，移除硬编码 `"team_view"`。
  - 团队成员范围：
    - `business`：可按全量填报角色统计，包含 `sales`、`technician`、`channel_ops`；如当前用户也是部门负责人，可优先统计直属成员并在文档说明。
    - 部门负责人：统计 `User.department_manager_id == 当前用户 id` 的直属成员。
  - 统计口径：
    - 今日日报：团队成员中 `report_type="daily"`、`report_date=today`、`status="submitted"` 的人数 / 团队成员总数。
    - 本周周报：团队成员中 `report_type="weekly"`、`report_date=week_start`、`status="submitted"` 的人数 / 团队成员总数。
  - 返回 `DashboardReportStatus(daily="3/5 已提交", weekly="2/5 已提交")`。无成员时返回 `"0/0 已提交"`。
- `backend/tests/test_dashboard_workbench.py`
  - 增加 business 团队提交率测试。
  - 增加部门负责人团队提交率测试。
  - 验证不再返回 `"team_view"`。

### 前端任务

- `frontend/src/components/dashboard/RoleDashboard.tsx`
  - 当前 `REPORT_STATUS_LABELS` 未命中的字符串会原样显示，因此 `"3/5 已提交"` 可直接展示。
  - 如需优化颜色，可对包含“已提交”的动态文本保持蓝色或默认色。

### 验收标准

- business 工作台展示真实团队日报/周报提交率。
- 部门负责人工作台展示直属成员提交率。
- 前端不再显示“团队视图”占位。
- `cd backend && APP_ENV=test ./venv/bin/python -m pytest tests/test_dashboard_workbench.py -q` 通过。

## P5 延期项

### P5.3：日报/周报评论通知

延期原因：评论依赖通知基础设施和评论模型，非当前业务闭环阻塞项。

后续范围：

- 新增工作报告评论模型或复用现有通知表。
- 新增 `POST /work-reports/{id}/comments`。
- 评论后生成通知，通知中心可跳转日报/周报详情。

### P5.4：定时提醒/飞书推送

延期原因：工作台待办已覆盖未提交提醒，定时推送依赖飞书消息或调度基础设施。

后续范围：

- 每日固定时间扫描未提交日报用户。
- 每周固定时间扫描未提交周报用户。
- 生成站内通知或飞书提醒。

## P4 验收状态

截至 2026-05-13 P4 完成：

- 新增 `frontend/src/hooks/useRoleDashboard.ts`：定义 workbench 数据类型、调用 `/dashboard/workbench`。
- 新增 `frontend/src/components/dashboard/RoleDashboard.tsx`：主工作台组件，渲染 role/scope/generated_at、指标卡片、待办、风险、快捷入口、日报/周报状态。
- 新增 `frontend/src/components/dashboard/DashboardMetricGrid.tsx`：指标卡片网格，支持点击跳转。
- 新增 `frontend/src/components/dashboard/DashboardTodoList.tsx`：待办事项列表。
- 新增 `frontend/src/components/dashboard/DashboardRiskList.tsx`：风险提醒列表。
- 新增 `frontend/src/components/dashboard/DashboardQuickActions.tsx`：快捷入口，按 capability 过滤。
- 修改 `frontend/src/pages/MyDashboard.tsx`：渲染 RoleDashboard 替代旧销售工作台。
- 保留 `/dashboard` 入口和 MyDashboard 页面入口，路由不变。
- UI 风格保持 Ant Design + BrandCard + UnifiedStatistic，不做营销页重设计。
- 六类角色适配：
  - `admin`：全局视图，用户/告警/日志/线索/商机指标，用户/日志/预警/字典快捷入口。
  - `business`：团队视图，线索/商机/项目/合同/目标指标，目标/日报/商机/漏斗快捷入口，团队日报/周报状态。
  - `sales`：个人视图，线索/商机/目标/跟进指标，待办来自跟进记录，客户/线索/商机/跟进/日报快捷入口，个人日报/周报状态。
  - `finance`：全局视图，合同/金额指标，合同/回款/业绩快捷入口，无日报/周报状态和入口。
  - `technician`：个人视图，分配/待接单/进行中工单指标，待办来自进行中工单，工单/知识库/日报快捷入口，个人日报/周报状态。
  - `channel_ops`：个人视图，渠道/跟进/计划指标，渠道/跟进/培训/绩效/日报快捷入口，个人日报/周报状态。
- 快捷入口按 capability 过滤：finance 不显示日报/周报入口（后端不返回该快捷入口，前端 report_status 为 null 不渲染状态区块）。
- 验收命令：
  - `cd frontend && npm run build`：成功，无 TypeScript 错误。
  - `cd backend && APP_ENV=test ./venv/bin/python -m pytest tests/test_dashboard_workbench.py -q`：10 passed, 10 warnings。
  - `cd backend && APP_ENV=test ./venv/bin/python -m pytest -q`：199 passed, 10 warnings。

## 当前验收状态

截至 2026-05-13：

- P0、P1、P2 已完成并通过验收。
- P3 已完成后端接口与测试，新增 `/dashboard/workbench`。
- P2 实际落地路由为 `/work-reports`、`/work-reports/:id`；个人与团队视图通过列表页 Tab 承载，暂不单独保留 `/work-reports/new` 和 `/work-reports/team` 页面路由。
- 团队报告已支持类型、状态、日期范围筛选；后端 `/work-reports/team` 已支持 `status` 查询参数。
- 日报/周报结构化汇总已展示跟进、线索、商机、项目、合同、工单、渠道数据。
- 财务角色不显示日报/周报菜单，直接访问页面时也展示“不支持日报/周报功能”。
- `/dashboard/workbench` 已覆盖 `admin`、`business`、`sales`、`finance`、`technician`、`channel_ops` 六类角色，返回 `role`、`scope`、`metrics`、`todos`、`risks`、`quick_actions`、`report_status`、`generated_at`。
- 财务工作台不返回日报/周报待办或快捷入口；销售、技术、渠道运营返回个人日报/周报状态。
- 验收命令：
  - `cd backend && APP_ENV=test ./venv/bin/python -m pytest tests/test_dashboard_workbench.py -q`：`10 passed, 10 warnings`
  - `cd backend && APP_ENV=test ./venv/bin/python -m pytest -q`：`199 passed, 10 warnings`
  - `cd frontend && npm run build`：成功

## P0：组织与角色基础

### 后端任务

修改建议：

- `backend/app/models/user.py`
  - 新增 `department_manager_id = ForeignKey("users.id")`
  - 新增自关联关系 `department_manager`、`department_members`
  - 保留 `sales_leader_id` 不删除
- `backend/app/schemas/user.py`
  - 用户创建、更新、响应结构增加 `department_manager_id`
  - 角色枚举或校验增加 `channel_ops`
- `backend/app/core/roles.py`
  - 角色标准化支持 `channel_ops`
- `backend/app/routers/auth.py`
  - capability 中补充 `channel_ops` 的基础读权限
  - 新增 `work_report:*` 能力占位
  - 新增 `dashboard:team` 能力：`admin`、`business`、部门负责人
- `backend/app/routers/user.py`
  - 用户创建/更新允许维护 `department_manager_id`
  - 禁止用户把自己设为自己的部门负责人

### 前端任务

修改建议：

- `frontend/src/utils/roles.ts`
  - 增加 `channel_ops` 展示名“渠道运营”
- `frontend/src/components/lists/UserList.tsx`
  - 用户表单支持选择角色 `channel_ops`
  - 用户表单支持维护部门负责人

### 测试重点

- 创建/更新用户可设置 `department_manager_id`
- 自己不能成为自己的部门负责人
- `channel_ops` 登录后能获得基础页面能力
- 旧 `sales_leader_id` 不受影响

## P1：日报/周报后端闭环

### 新增文件

- `backend/app/models/work_report.py`
- `backend/app/schemas/work_report.py`
- `backend/app/routers/work_report.py`
- `backend/app/core/policy/resources/work_report.py`
- `backend/app/services/work_report_service.py`
- `backend/tests/test_work_reports.py`

### 模型设计

`work_reports`：

| 字段 | 说明 |
|------|------|
| `id` | 主键 |
| `report_type` | `daily` / `weekly` |
| `report_date` | 日报日期；周报统一用周一 |
| `week_start` / `week_end` | 周报范围 |
| `owner_id` | 填报人 |
| `owner_role` | 角色快照 |
| `status` | `draft` / `submitted` / `withdrawn` |
| `structured_snapshot` | JSON，结构化汇总 |
| `remark` | 备注 |
| `source_report_ids` | JSON，周报引用的日报 ID |
| `submitted_at` / `withdrawn_at` | 状态时间 |
| `created_at` / `updated_at` | 审计时间 |

约束：

- `owner_id + report_type + report_date` 唯一
- `limit <= 100`
- `report_type`、`status` 有后端校验

### API

```text
GET    /work-reports
POST   /work-reports
GET    /work-reports/{id}
PUT    /work-reports/{id}
POST   /work-reports/{id}/submit
POST   /work-reports/{id}/withdraw
POST   /work-reports/generate-draft
GET    /work-reports/team
```

评论接口可留到 P5，不放入 P1。

### 结构化快照

日报快照至少覆盖：

- 当天跟进记录数量和列表摘要
- 当天新增线索数量和列表摘要
- 当天新增商机数量和列表摘要
- 当天新增项目/签约合同摘要，若字段不足可先按已有日期字段统计
- 技术员当天相关工单摘要
- 渠道运营当天渠道/渠道跟进/渠道培训摘要
- 当天实际业绩录入或销售目标动作，若缺少操作日志细粒度，可先统计现有业务表

周报快照：

- 聚合本周日报
- 包含每日提交状态
- 汇总本周各类动作数量
- 汇总重点对象列表

### 权限策略

- 本人可读、创建、编辑自己的草稿/撤回报告
- 本人可提交、撤回自己的报告
- `admin` 全量可读
- `business` 和部门负责人可读 `department_manager_id == 当前用户 id` 的成员报告
- `channel_ops` 仅管理自己的报告；如果其是部门负责人，可查看成员报告
- `finance` 第一版不能创建日报/周报，也不显示填报入口

## P2：日报/周报前端页面

### 新增文件

- `frontend/src/hooks/useWorkReports.ts`
- `frontend/src/pages/WorkReportPage.tsx`
- `frontend/src/pages/WorkReportDetailPage.tsx`
- `frontend/src/components/work-reports/WorkReportForm.tsx`
- `frontend/src/components/work-reports/WorkReportSummaryPanel.tsx`

### 路由

```text
/work-reports
/work-reports/new
/work-reports/:id
/work-reports/team
```

### 页面能力

- 个人日报/周报列表
- 生成日报草稿
- 生成周报草稿
- 查看结构化汇总
- 编辑备注
- 保存草稿
- 提交
- 撤回
- 团队视图按人员、日期、状态筛选

## P3：角色化工作台后端

### 新增/修改

- `backend/app/schemas/dashboard.py`
  - 增加 `DashboardWorkbenchResponse`、卡片、待办、风险、快捷入口 Schema
- `backend/app/services/dashboard_workbench_service.py`
- `backend/app/routers/dashboard.py`
  - 新增 `GET /dashboard/workbench`

### 角色卡片

- `admin`：用户、权限、告警、操作日志、系统数据摘要
- `business`：团队目标、团队漏斗、重点商机、日报/周报提交率
- `sales`：我的客户、线索、商机、销售目标、待跟进、日报/周报状态
- `finance`：合同、回款进度、逾期提醒、客户财务视图，不展示日报/周报入口
- `technician`：我的工单、待接单、进行中、SLA 风险、装机、评价
- `channel_ops`：渠道绩效、渠道跟进、渠道培训、渠道客户关联、日报/周报状态

## P4：角色化工作台前端

### 拆分建议

- `frontend/src/hooks/useRoleDashboard.ts`
- `frontend/src/components/dashboard/RoleDashboard.tsx`
- `frontend/src/components/dashboard/DashboardMetricGrid.tsx`
- `frontend/src/components/dashboard/DashboardTodoList.tsx`
- `frontend/src/components/dashboard/DashboardRiskList.tsx`
- `frontend/src/components/dashboard/DashboardQuickActions.tsx`

迁移策略：

- 保留 `MyDashboard.tsx` 页面入口。
- 逐步用 `/dashboard/workbench` 返回的卡片替代硬编码销售工作台。
- 旧接口保留兼容，避免一次性破坏现有展示。

## P5：通知与待办联动

### 后端

- 日报/周报未提交状态进入 `/dashboard/workbench.todos`
- 报告评论时生成通知
- 第一版不强制定时任务，可在查询时动态计算未提交提醒

### 前端

- 工作台显示“今日日报未提交”“本周周报未提交”
- 通知中心支持跳转到日报/周报详情

## 第一轮交付建议

第一轮施工范围建议为 P0 + P1：

- 完成组织/角色基础
- 完成日报/周报后端闭环
- 暂不做前端大改
- 暂不做角色化工作台前端

这样可以先把数据模型、权限和 API 边界稳定下来，再进入页面施工。

## 第一轮验收命令

后端：

```bash
cd backend
APP_ENV=test pytest -q
```

前端若 P0 涉及用户表单和角色展示：

```bash
cd frontend
npm run build
```

## 第一轮验收标准

- `channel_ops` 可作为合法角色维护。
- 用户可维护 `department_manager_id`，且不能设置自己为自己的部门负责人。
- `work_reports` 支持日报/周报生成草稿、保存、提交、撤回、列表、详情。
- 日报结构化快照来自当天系统业务数据。
- 周报结构化快照来自本周日报聚合。
- 财务角色不能创建日报/周报。
- 普通用户不能查看他人日报/周报。
- 部门负责人能查看直属成员日报/周报。
- `admin` 能查看全部日报/周报。
- 所有新增列表接口限制 `limit <= 100`。
- pytest 全部通过。
