# 日报/周报与角色化工作台设计

日期：2026-05-13

## 背景

当前系统已有 `/dashboard/summary`、`/dashboard/todos`、`/dashboard/recent-followups`、`/dashboard/notifications`、`/dashboard/team-rank`，前端入口为 `frontend/src/pages/MyDashboard.tsx`。现有工作台主要围绕销售角色展示业绩目标、线索、商机、跟进、预警、销售漏斗和团队排行。

下一阶段需要补齐两个能力：

- 日报/周报管理：沉淀个人周期性工作复盘，并支持管理者查看团队执行情况。
- 角色化工作台：不同角色登录后看到不同首页内容，而不是所有角色共用销售型工作台。

## 设计目标

- 销售、渠道运营、技术员、财务、业务管理者、管理员都能在工作台看到与自己角色相关的待办、指标和风险。
- 新增独立渠道运营角色，建议角色编码为 `channel_ops`。
- 日报以“用户当天在系统内完成的结构化业务操作”为主体，只保留一个备注区用于灵活填写。
- 周报以“本周日报聚合”为主体，再保留一个周总结/备注区用于灵活填写。
- 日报/周报能从系统已有业务动作自动生成草稿，减少重复填报。
- 管理者能按团队、人员、日期查看日报/周报提交情况和内容。
- 工作台、通知、待办、日报/周报形成闭环：待办推动执行，日报/周报复盘执行，工作台展示结果和风险。

## 非目标

本阶段不做完整 OA 审批流，不做复杂组织架构引擎，不做绩效考核打分，不做移动端专用页面。日报/周报只做提交、撤回、查看、评论预留，不做多级审批。日报/周报暂不强制提交，工作台可以提示“未提交”，但第一版不阻断用户继续使用系统。财务角色第一版不纳入日报/周报填报范围。

## 已确认业务口径

- 日报是结构化汇报，不以大段手写为主。
- 日报自动汇总用户当天在系统内做过的业务操作，例如新增客户、创建线索、推进商机、添加跟进、处理工单、维护渠道等。
- 日报提供一个备注字段，用于补充系统无法自动识别的事项。
- 周报由本周日报聚合生成，统计每日动作、重点对象和本周趋势。
- 周报提供一个周备注/周总结字段，用于补充风险、计划和主观复盘。
- 新增独立渠道运营角色 `channel_ops`。
- 新增部门负责人关系，作为日报/周报团队视图和角色化工作台团队范围的第一版组织口径。
- 日报/周报暂不强制提交。
- 财务角色暂不参与日报/周报管理，但仍保留财务角色工作台。

## 角色化工作台

### 角色视图

| 角色 | 工作台核心内容 | 主要入口 |
|------|----------------|----------|
| `admin` | 系统健康、用户、权限、告警、操作日志、数据完整性 | 用户管理、操作日志、告警规则、字典 |
| `business` | 销售目标完成、团队业绩、销售漏斗、重点商机、逾期跟进、日报周报提交率 | 报表、销售目标、商机、日报周报 |
| `sales` | 我的客户、我的线索/商机、我的销售任务、今日待跟进、报价/合同、日报周报 | 客户、线索、商机、销售任务、跟进、日报周报 |
| `finance` | 合同、回款计划、逾期回款、客户财务视图、付款进度报表 | 合同、回款报表、客户财务视图 |
| `technician` | 我的工单、待接单、进行中工单、SLA 风险、装机记录、服务评价 | 工单、装机记录、评价 |
| `channel_ops` | 渠道绩效、渠道跟进、渠道培训、渠道客户关联、渠道计划、日报周报 | 渠道、渠道跟进、渠道绩效、渠道培训、日报周报 |

说明：`channel_ops` 是下一阶段新增角色。实现时需要同步更新用户角色枚举/展示、权限策略、菜单能力和工作台卡片。

### 部门负责人关系

为支持销售、渠道运营、技术等多角色团队视图，下一阶段新增通用部门负责人关系，不继续把团队范围绑定在销售专用字段上。

建议在 `User` 模型新增字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `department_manager_id` | int / FK users.id | 当前用户所属部门负责人 |
| `department` | string | 继续复用现有部门字段 |

关系含义：

- 一个用户最多有一个部门负责人。
- 一个部门负责人可以管理多个成员。
- `admin` 拥有全量团队视图。
- `business` 可查看自己作为 `department_manager_id` 的成员数据。
- `channel_ops` 负责人可查看渠道运营团队成员数据。
- `technician` 负责人可查看技术团队成员工单和日报/周报数据。
- 现有 `sales_leader_id` 可暂时保留兼容历史销售数据，但新功能优先使用 `department_manager_id`。

后续如果引入完整组织架构，可再迁移为 `departments` + `department_members` + `department_managers` 表。

### 推荐接口

保留当前旧接口，新增角色化聚合接口：

```text
GET /dashboard/workbench
```

查询参数：

| 参数 | 类型 | 说明 |
|------|------|------|
| `date` | date | 默认今天，用于今日待办和日报状态 |
| `period` | string | `today` / `week` / `month`，默认 `today` |

响应结构建议：

```json
{
  "role": "sales",
  "display_name": "销售工作台",
  "metrics": [],
  "todos": [],
  "risks": [],
  "quick_actions": [],
  "sections": [],
  "report_status": {
    "daily": "draft",
    "weekly": "not_submitted"
  }
}
```

### 通用卡片模型

为了避免每个角色写一套完全不同的前端结构，后端统一返回可组合卡片：

| 字段 | 说明 |
|------|------|
| `key` | 稳定标识，例如 `my_leads`、`pending_work_orders` |
| `title` | 卡片标题 |
| `value` | 主数值 |
| `unit` | 单位 |
| `trend` | 环比/同比信息，可选 |
| `priority` | `low` / `medium` / `high` |
| `route` | 点击跳转路径 |
| `capability` | 前端显示所需 capability |

### 工作台后端分层

建议新增服务层：

```text
backend/app/services/dashboard_workbench_service.py
```

职责：

- 根据当前用户 role/capability 选择工作台配置。
- 聚合已有业务数据。
- 统一过滤权限范围。
- 生成通用卡片、待办、风险和快捷入口。

Router 只负责认证、参数校验、调用服务、返回 Schema。

### 工作台权限

- `dashboard:read`：读取自己的角色化工作台。
- `dashboard:team`：读取团队聚合卡片，建议 `admin`、`business` 和部门负责人。
- `dashboard:system`：读取系统治理卡片，建议 `admin`。
- `dashboard:finance`：读取财务工作台卡片，建议 `admin`、`business`、`finance`。
- `dashboard:technician`：读取技术员工单卡片，建议 `admin`、`business`、`technician`。

当前 `dashboard:team_rank` 只有 admin，后续业务管理者也需要团队视图时，应拆成 `dashboard:team`，避免把管理者误等同于管理员。

## 日报/周报管理

### 业务流程

```text
生成草稿 -> 补充内容 -> 提交 -> 管理者查看 -> 评论/反馈预留 -> 撤回/重新提交
```

### 报告类型

| 类型 | 周期 | 典型内容 |
|------|------|----------|
| 日报 | 单日 | 当天系统操作结构化汇总 + 备注 |
| 周报 | 自然周 | 本周日报聚合 + 周备注/周总结 |

### 状态

| 状态 | 说明 |
|------|------|
| `draft` | 草稿，可编辑 |
| `submitted` | 已提交，普通用户不可直接改正文 |
| `withdrawn` | 已撤回，可重新编辑 |

后续如接入审批流，可扩展 `reviewed`、`rejected` 等状态。

### 数据模型建议

新增模型：

```text
backend/app/models/work_report.py
```

主表 `work_reports`：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int | 主键 |
| `report_type` | string | `daily` / `weekly` |
| `report_date` | date | 日报日期；周报可取周一 |
| `week_start` | date | 周报开始日期，日报可为空 |
| `week_end` | date | 周报结束日期，日报可为空 |
| `owner_id` | int | 填报人 |
| `owner_role` | string | 提交时角色快照 |
| `status` | string | `draft` / `submitted` / `withdrawn` |
| `structured_snapshot` | JSON | 结构化快照，日报来自当天系统操作，周报来自本周日报聚合 |
| `remark` | text | 灵活备注，日报用于补充当天事项，周报用于周总结/风险/计划 |
| `source_report_ids` | JSON | 周报引用的日报 ID 列表，日报为空 |
| `submitted_at` | datetime | 提交时间 |
| `withdrawn_at` | datetime | 撤回时间 |
| `created_at` | datetime | 创建时间 |
| `updated_at` | datetime | 更新时间 |

唯一约束：

```text
owner_id + report_type + report_date
```

说明：周报 `report_date` 统一存周一日期，避免同一周重复提交。

可选评论表 `work_report_comments`：

| 字段 | 说明 |
|------|------|
| `report_id` | 报告 ID |
| `commenter_id` | 评论人 |
| `content` | 评论内容 |
| `created_at` | 评论时间 |

### 结构化汇总规则

日报草稿自动汇总当天系统操作，形成结构化快照：

- 客户动作：当天新增或维护的客户。
- 渠道动作：当天新增或维护的渠道、渠道联系人、渠道跟进、渠道培训。
- 线索动作：当天新增线索、线索转化。
- 商机动作：当天新增商机、商机阶段变化、预计金额变化。第一版如缺少阶段变更日志，可先统计当天创建和当天跟进的商机。
- 项目/合同动作：当天新增项目、签约合同、合同状态变化。
- 跟进动作：`FollowUp.follow_up_date == report_date` 且 `follower_id == 当前用户`。
- 工单动作：技术员看自己参与的工单处理动作，销售看自己提交或关联销售的工单。
- 销售任务动作：当天录入或更新的实际业绩。

周报草稿从本周日报聚合生成，形成结构化快照：

- 每日提交状态。
- 每日结构化动作数量汇总。
- 本周客户、渠道、线索、商机、项目、合同、跟进、工单、销售任务动作汇总。
- 本周重点对象列表，例如重点商机、重点客户、重点渠道、重点工单。
- 本周未完成待办和风险项。

提交时固化 `structured_snapshot`，避免报告提交后历史内容随业务数据变化。用户只能编辑 `remark`，不直接编辑结构化操作明细；如果自动汇总不准确，用户可以点击“重新生成结构化汇总”。

### API 设计

```text
GET    /work-reports
POST   /work-reports
GET    /work-reports/{id}
PUT    /work-reports/{id}
POST   /work-reports/{id}/submit
POST   /work-reports/{id}/withdraw
POST   /work-reports/generate-draft
GET    /work-reports/team
POST   /work-reports/{id}/comments
GET    /work-reports/{id}/comments
```

列表查询参数：

| 参数 | 说明 |
|------|------|
| `report_type` | `daily` / `weekly` |
| `owner_id` | 管理者筛选成员 |
| `status` | 状态 |
| `date_from` / `date_to` | 时间范围 |
| `skip` / `limit` | 分页，`limit <= 100` |

生成草稿请求：

```json
{
  "report_type": "daily",
  "report_date": "2026-05-13"
}
```

### 权限设计

新增资源：

```text
work_report
```

能力建议：

| capability | 说明 |
|------------|------|
| `work_report:read` | 读取自己报告 |
| `work_report:create` | 创建自己报告 |
| `work_report:update` | 编辑自己草稿或撤回状态报告 |
| `work_report:submit` | 提交自己报告 |
| `work_report:withdraw` | 撤回自己报告 |
| `work_report:team_read` | 查看下属或团队报告 |
| `work_report:comment` | 评论授权范围内报告 |

角色口径：

- `sales`：管理自己的日报/周报。
- `technician`：管理自己的日报/周报，自动汇总工单。
- `business`：管理自己的日报/周报，并可查看团队报告。
- `channel_ops`：管理自己的日报/周报，自动汇总渠道相关动作。
- `finance`：第一版不参与日报/周报，仅保留财务工作台。
- `admin`：全量管理。

团队范围第一版使用 `User.department_manager_id` 判断直属团队。现有 `sales_leader_id` 仅作为历史兼容字段，不作为新日报/周报和角色化工作台的主判断依据。

## 前端设计

### 页面与路由

新增页面：

```text
/work-reports
/work-reports/new
/work-reports/:id
/work-reports/team
```

建议组件：

```text
frontend/src/pages/WorkReportPage.tsx
frontend/src/pages/WorkReportDetailPage.tsx
frontend/src/components/work-reports/WorkReportForm.tsx
frontend/src/components/work-reports/WorkReportSummaryPanel.tsx
frontend/src/hooks/useWorkReports.ts
```

### 工作台改造

当前 `MyDashboard.tsx` 体量较大，建议拆分：

```text
frontend/src/pages/MyDashboard.tsx
frontend/src/components/dashboard/RoleDashboard.tsx
frontend/src/components/dashboard/DashboardMetricGrid.tsx
frontend/src/components/dashboard/DashboardTodoList.tsx
frontend/src/components/dashboard/DashboardRiskList.tsx
frontend/src/components/dashboard/DashboardQuickActions.tsx
frontend/src/hooks/useRoleDashboard.ts
```

迁移策略：

- 第一阶段保留旧 `MyDashboard` 页面壳。
- 新增 `useRoleDashboard()` 调用 `/dashboard/workbench`。
- 根据返回的 `role` 和 `sections` 渲染不同模块。
- 旧的销售统计接口可先作为 sales 工作台的数据来源，逐步迁入服务层。

### 日报/周报表单

表单区域：

- 结构化汇总区：只读，日报展示当天系统操作，周报展示本周日报聚合。
- 备注区：可编辑，用于补充系统外事项、风险、计划或主观说明。
- 附件预留：等附件模块完成后接入。

操作：

- 保存草稿
- 提交
- 撤回
- 重新生成结构化汇总

## 通知与提醒联动

日报/周报可以产生待办和通知，但第一版不强制：

- 当天 17:00 后未提交日报：可生成“日报待提交”提醒。
- 周五或周末前未提交周报：可生成“周报待提交”提醒。
- 管理者工作台显示团队未提交人数。
- 报告被评论时通知填报人。

第一版可以先在接口查询时计算“未提交”状态，不急于引入定时任务；后续再接入调度任务生成持久化通知。

## 实施批次

### P1：日报/周报基础能力

- 新增 `WorkReport` 模型、Schema、Router、Policy。
- 新增 `User.department_manager_id` 部门负责人关系，并在用户管理中支持维护。
- 支持生成草稿、保存、提交、撤回、列表、详情。
- 日报结构化汇总当天系统操作，周报聚合本周日报。
- 支持个人日报/周报页面。
- 补后端权限和流程测试。

### P2：角色化工作台接口

- 新增 `/dashboard/workbench`。
- 新增 dashboard workbench service。
- 支持 sales、business、admin、finance、technician、channel_ops 的基础卡片。
- 前端拆分工作台组件，并接入新接口。

### P3：管理者团队视图

- 新增 `/work-reports/team`。
- 支持按人员、日期、状态查看团队日报/周报。
- 工作台展示团队日报/周报提交率和未提交清单。

### P4：通知与待办联动

- 将日报/周报未提交纳入 `/dashboard/workbench` todos。
- 通知中心展示报告评论、未提交提醒。
- 后续可接入定时任务持久化通知。

## 验收标准

- 销售人员能生成当天日报草稿，自动带出当天系统操作结构化摘要，并可填写备注。
- 周报能从本周日报聚合生成，并可填写周备注/周总结。
- 技术员工作台不再展示销售漏斗为主，而是展示工单、SLA、装机、评价相关内容。
- 财务角色工作台展示合同、回款、逾期等财务相关内容，不展示无关销售快捷创建入口。
- 财务角色第一版不展示日报/周报填报入口。
- 渠道运营角色能看到渠道工作台卡片，并能生成渠道动作相关日报/周报。
- 业务管理者能看到团队目标、团队漏斗、重点风险和日报/周报提交情况。
- 管理员能看到系统治理入口、告警、用户和操作日志摘要。
- 普通用户不能查看他人的日报/周报；管理者只能查看授权团队范围。
- 授权团队范围基于 `department_manager_id` 判断，admin 除外。
- 列表接口分页上限 `limit <= 100`。
- 后端测试、前端类型检查和构建通过。
