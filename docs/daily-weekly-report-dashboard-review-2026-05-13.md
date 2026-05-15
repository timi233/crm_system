# 日报/周报与角色化工作台阶段 Review 报告

日期：2026-05-13
CCB_REQ_ID: job_efb258ff930f

## 执行摘要

当前 P0-P4 已完成并通过验收（backend 199 passed, frontend build 成功）。整体架构合理，业务闭环基本完整，但存在以下需要收口的风险点和待补强项：

**关键发现：**
- ✅ 组织与角色基础、日报/周报后端、前端页面、工作台后端、工作台前端均已落地
- ⚠️ 团队日报/周报状态计算逻辑简化为 `team_view`，未实现真实团队提交率统计
- ⚠️ 部门负责人团队范围查询未完全验证（policy 有 `can_team_read` 但未在所有场景应用）
- ⚠️ 日报/周报未提交提醒未进入工作台 todos，P5 待办联动缺失
- ⚠️ 前端路由 `/work-reports/new` 和 `/work-reports/team` 在计划中但未实际注册
- ⚠️ 缺少端到端 smoke 测试验证（登录 → 生成草稿 → 提交 → 工作台显示状态）

---

## 一、P0-P4 业务闭环 Review

### 1.1 组织与角色基础（P0）✅

**已完成：**
- `User.department_manager_id` 已添加，支持自关联
- `channel_ops` 角色已注册到 `roles.py` 和前端 `roles.ts`
- `auth.py` 已定义 `work_report:*` 能力，`work_report_roles` 包含 `channel_ops`
- `work_report:team_read` 限定为 `admin` 和 `business`

**风险点：**
- ⚠️ **部门负责人团队范围未完全验证**：`WorkReportPolicy.can_team_read` 支持部门负责人查询成员，但 `/work-reports/team` 接口中 `full_access` 仅判断 `admin/business`，部门负责人走的是 `manager_id` 过滤逻辑，未明确测试覆盖。
- ⚠️ **自关联循环检测缺失**：`user.py` router 禁止用户设置自己为自己的部门负责人，但未检测 A→B→A 循环。

**建议：**
- P5 前补充测试：创建部门负责人 + 成员，验证成员日报/周报在团队视图可见。
- 可选：增加循环检测或文档说明"不支持多级部门负责人链"。

---

### 1.2 日报/周报后端闭环（P1）✅

**已完成：**
- `WorkReport` 模型、schema、router、policy、service 完整
- 唯一约束 `owner_id + report_type + report_date`
- 结构化快照覆盖跟进、线索、商机、项目、合同、工单、渠道
- 提交/撤回状态机正确
- 财务角色禁止创建日报/周报
- 权限策略：本人可读写自己的草稿/撤回报告，admin 全量可读，business 全量可读，部门负责人可读成员报告

**风险点：**
- ⚠️ **结构化快照日期过滤不精确**：`generate_daily_snapshot` 中 `Lead.created_at == report_date` 使用 `==` 比较 `datetime` 和 `date`，可能因时区或时间戳精度导致漏统计。建议改为 `func.date(Lead.created_at) == report_date`。
- ⚠️ **周报快照未实现聚合逻辑**：`generate_weekly_snapshot` 当前仅查询本周日报列表，未真正聚合每日数据（如"本周新增线索总数"）。
- ⚠️ **limit 未全局强制**：`/work-reports/` 和 `/work-reports/team` 接口 `limit` 默认 20，最大 100，但 service 层 `get_team_reports` 未二次校验 limit 上限。

**建议：**
- P5 前修复日期过滤：所有 `created_at == report_date` 改为 `func.date(created_at) == report_date`。
- 周报聚合逻辑可延期到 P5 或 P6，当前"列出本周日报"已满足最小可用。
- Service 层增加 `limit = min(limit, 100)` 防御。

---

### 1.3 日报/周报前端页面（P2）✅

**已完成：**
- `WorkReportPage.tsx` 支持个人/团队 Tab 切换
- 生成日报/周报草稿、查看详情、提交、撤回
- 结构化汇总展示
- 财务角色访问时显示"不支持日报/周报功能"

**风险点：**
- ⚠️ **路由注册不完整**：计划文档提到 `/work-reports/new` 和 `/work-reports/team`，但 `App.tsx` 仅注册了 `/work-reports` 和 `/work-reports/:id`。当前通过 Tab 切换实现团队视图，但 URL 不变，无法直接分享团队视图链接。
- ⚠️ **财务角色前端拦截不彻底**：`WorkReportPage` 中 `canUseWorkReports` 判断 `user?.role !== 'finance'`，但未在路由层拦截，财务用户仍可访问 `/work-reports` 页面（虽然会显示提示）。

**建议：**
- 明确路由策略：如果团队视图通过 Tab 承载，更新计划文档移除 `/work-reports/team` 路由；如果需要独立路由，补充注册。
- 财务角色拦截可保持现状（前端提示 + 后端 403），或在 `ProtectedRoute` 层增加 `user.role !== 'finance'` 判断。

---

### 1.4 角色化工作台后端（P3）✅

**已完成：**
- `GET /dashboard/workbench` 覆盖 6 类角色
- 返回 `role`、`scope`、`metrics`、`todos`、`risks`、`quick_actions`、`report_status`、`generated_at`
- 财务工作台不返回 `report_status`（为 `None`）
- 个人角色（sales/technician/channel_ops）返回个人日报/周报状态
- 团队角色（business）返回 `team_view` 占位

**风险点：**
- ⚠️ **团队日报/周报状态未实现真实统计**：`_get_team_report_status` 硬编码返回 `daily="team_view", weekly="team_view"`，未计算团队成员提交率。业务需求是"团队日报/周报提交率"，当前实现仅为占位符。
- ⚠️ **日报/周报未提交提醒未进入 todos**：个人角色工作台 `report_status` 显示 `not_created`，但未生成"今日日报未提交"待办项。P5 计划中提到"未提交状态进入 todos"，当前缺失。
- ⚠️ **department_manager_id 未传递给 business 工作台**：`get_dashboard_workbench` 查询 `user.department_manager_id` 并传递给 `_build_business_workbench`，但 business 工作台未使用该字段过滤团队范围（当前 business 看全局数据）。

**建议：**
- **P5 必做**：实现 `_get_team_report_status` 真实统计逻辑，查询部门成员今日/本周报告提交情况，返回 `{"daily": "3/5 已提交", "weekly": "2/5 已提交"}` 或类似结构。
- **P5 必做**：个人角色工作台增加日报/周报未提交待办项，优先级"高"，链接到 `/work-reports`。
- 可选：business 工作台指标按 `department_manager_id` 过滤团队范围，或明确文档说明 business 看全局。

---

### 1.5 角色化工作台前端（P4）✅

**已完成：**
- `RoleDashboard.tsx` 渲染工作台，支持 6 类角色
- 日报/周报状态区块显示 `not_created/draft/submitted/withdrawn/team_view`
- 指标卡片、待办、风险、快捷入口按角色差异化
- 财务角色不显示日报/周报状态区块（`report_status` 为 `null`）

**风险点：**
- ⚠️ **team_view 状态展示不友好**：business 工作台显示"今日日报：团队视图"，用户无法直观看到团队提交率。
- ⚠️ **快捷入口能力过滤未完全生效**：`DashboardQuickActions` 按 `capability` 过滤，但后端返回的 `quick_actions` 已包含 `capability` 字段，前端再次过滤可能冗余或不一致。

**建议：**
- P5 实现团队状态统计后，前端调整 `REPORT_STATUS_LABELS` 支持动态文本（如"3/5 已提交"）。
- 明确快捷入口过滤责任：后端返回时已按角色过滤，前端仅做展示；或前端完全负责过滤，后端返回全量。

---

## 二、前后端契约风险 Review

### 2.1 数据口径一致性 ✅

- `report_status.daily/weekly` 枚举值前后端一致：`not_created/draft/submitted/withdrawn/team_view`
- `scope` 枚举值一致：`personal/team/global`
- 日期格式统一：后端返回 ISO 8601，前端 `dayjs` 解析

### 2.2 权限契约 ✅

- 后端 `work_report:team_read` 限定 `admin/business`，前端 `canTeamRead` 判断 `capabilities['work_report:team_read'] || capabilities['dashboard:team']`，逻辑一致。
- 财务角色后端返回 `report_status=None`，前端判断 `reportStatus && ...` 不渲染状态区块，契约正确。

### 2.3 API 响应结构 ✅

- `/dashboard/workbench` 返回结构与 `DashboardWorkbenchResponse` schema 一致
- `/work-reports/` 返回 `list[WorkReportRead]`，前端 `useWorkReports` 类型匹配

---

## 三、P5 通知/待办联动拆分建议

### 3.1 P5 必做任务（高优先级，阻塞业务闭环）

#### P5.1 工作台日报/周报未提交待办

**任务：**
- 修改 `DashboardWorkbenchService._build_sales_workbench`、`_build_technician_workbench`、`_build_channel_ops_workbench`：
  - 查询 `report_status`，如果 `daily == "not_created"`，生成待办项 `DashboardTodoItemNew(key="daily_report_missing", title="今日日报未提交", priority="high", link="/work-reports")`
  - 如果 `weekly == "not_created"` 且今天是周五/周六/周日，生成待办项 `DashboardTodoItemNew(key="weekly_report_missing", title="本周周报未提交", priority="medium", link="/work-reports")`
- 前端 `DashboardTodoList` 已支持渲染 todos，无需修改。

**验收标准：**
- 销售/技术/渠道运营登录工作台，未提交今日日报时，待办列表显示"今日日报未提交"。
- 点击待办项跳转到 `/work-reports`。

**风险：**
- 无

---

#### P5.2 团队日报/周报提交率统计

**任务：**
- 修改 `DashboardWorkbenchService._get_team_report_status`：
  - 查询 `department_manager_id == user_id` 的成员列表（如果 `role == "business"` 则查全部 sales/technician/channel_ops）
  - 统计今日日报：`submitted_count / total_count`
  - 统计本周周报：`submitted_count / total_count`
  - 返回 `DashboardReportStatus(daily=f"{submitted}/{total} 已提交", weekly=f"{submitted}/{total} 已提交")`
- 修改 `DashboardReportStatus` schema：`daily` 和 `weekly` 字段类型改为 `str`（当前已是 `str`，无需改动）
- 前端 `RoleDashboard` 已支持动态文本，无需修改。

**验收标准：**
- business 角色登录工作台，日报/周报状态显示"3/5 已提交"（假设团队 5 人，3 人已提交）。
- 部门负责人登录工作台，显示其直属成员提交率。

**风险：**
- 如果团队成员数量大（>100），查询性能可能下降。建议增加缓存或异步计算。

---

### 3.2 P5 可延期任务（低优先级，不阻塞业务闭环）

#### P5.3 日报/周报评论通知

**任务：**
- 新增 `POST /work-reports/{id}/comments` 接口
- 评论时生成通知记录（复用现有通知表或新增 `work_report_comments` 表）
- 通知中心支持跳转到日报/周报详情

**延期理由：**
- 第一版日报/周报不强制提交，评论功能使用频率低。
- 通知中心当前返回空列表，需先实现通知基础设施。

---

#### P5.4 定时任务：每日未提交提醒

**任务：**
- 新增定时任务（如每日 18:00 执行），查询当天未提交日报的用户，生成通知或发送飞书消息。

**延期理由：**
- 工作台待办已覆盖未提交提醒，定时推送为锦上添花。
- 需要飞书消息推送能力，依赖外部集成。

---

## 四、P5 前收口修复建议（P4.5 阶段）

### 4.1 必做修复（阻塞 P5）

#### 修复 1：日期过滤精度问题

**文件：** `backend/app/services/work_report_service.py`

**问题：**
```python
# 当前代码
Lead.created_at == report_date  # datetime == date 比较不精确
```

**修复：**
```python
func.date(Lead.created_at) == report_date
```

**影响范围：**
- `generate_daily_snapshot` 中所有 `created_at == report_date` 判断
- 涉及 `Lead`、`Opportunity`、`Project`、`Contract`、`WorkOrder`、`Channel`

**验收：**
- 创建今日线索，生成今日日报草稿，结构化快照中 `leads.count > 0`。

---

#### 修复 2：Service 层 limit 防御

**文件：** `backend/app/services/work_report_service.py`

**问题：**
- `get_team_reports` 接受 `limit` 参数，但未校验上限。

**修复：**
```python
async def get_team_reports(self, ..., limit: int = 20):
    limit = min(limit, 100)  # 强制上限
    ...
```

**验收：**
- 调用 `/work-reports/team?limit=999`，返回最多 100 条。

---

### 4.2 可选修复（不阻塞 P5）

#### 修复 3：路由注册与计划文档对齐

**选项 A：** 移除计划文档中 `/work-reports/new` 和 `/work-reports/team` 路由，明确"通过 Tab 切换实现"。

**选项 B：** 补充注册路由：
```tsx
<Route path="/work-reports/new" element={protectedElement(<WorkReportPage />, 'work_report:create')} />
<Route path="/work-reports/team" element={protectedElement(<WorkReportPage />, 'work_report:team_read')} />
```

**建议：** 选项 A，当前 Tab 切换已满足需求，独立路由增加维护成本。

---

#### 修复 4：财务角色路由拦截

**当前：** 财务用户可访问 `/work-reports`，页面显示"不支持日报/周报功能"。

**可选改进：** 在 `ProtectedRoute` 中增加角色判断，财务用户访问时重定向到工作台。

**建议：** 保持现状，前端提示 + 后端 403 已足够。

---

## 五、验收强化建议

### 5.1 端到端 Smoke 测试（P4.5 必做）

**测试场景：**
1. 销售角色登录 → 工作台显示"今日日报：未生成" → 点击"日报/周报"快捷入口 → 生成今日日报草稿 → 编辑备注 → 提交 → 返回工作台 → 状态变为"已提交"
2. 业务经理登录 → 工作台显示"今日日报：团队视图" → 点击"日报/周报"快捷入口 → 切换到"团队报告" Tab → 看到成员日报列表
3. 财务角色登录 → 工作台不显示日报/周报状态 → 访问 `/work-reports` → 显示"不支持日报/周报功能"

**执行方式：**
- 手动测试或使用 Playwright（已有 `webapp-testing` skill）
- 记录截图或视频作为验收证据

---

### 5.2 单元测试补充（可选）

**当前覆盖：**
- `test_work_reports.py`：10+ 测试，覆盖 CRUD、权限、提交/撤回
- `test_dashboard_workbench.py`：10 测试，覆盖 6 类角色工作台

**建议补充：**
- `test_work_report_service.py`：测试 `generate_daily_snapshot` 日期过滤、周报聚合逻辑
- `test_dashboard_workbench_service.py`：测试 `_get_team_report_status` 团队统计逻辑

---

## 六、下一步施工范围建议（交给 opencode）

### 方案 A：P4.5 收口修复（推荐，最小闭环）

**范围：**
1. 修复日期过滤精度问题（`func.date(created_at) == report_date`）
2. 修复 service 层 limit 防御
3. 端到端 smoke 测试（手动执行，记录结果）

**交付物：**
- 修改 `backend/app/services/work_report_service.py`
- 验收报告（smoke 测试截图 + pytest 结果）

**工作量：** 1-2 小时

**风险：** 无

---

### 方案 B：P5.1 + P5.2（推荐，完成业务闭环）

**范围：**
1. P4.5 收口修复（方案 A）
2. P5.1 工作台日报/周报未提交待办
3. P5.2 团队日报/周报提交率统计

**交付物：**
- 修改 `backend/app/services/dashboard_workbench_service.py`
- 修改 `backend/app/schemas/dashboard.py`（如需调整 schema）
- 新增测试 `backend/tests/test_dashboard_workbench_service.py`
- 验收报告

**工作量：** 3-4 小时

**风险：** 团队统计查询性能（可通过限制团队规模或增加索引缓解）

---

### 方案 C：P5 全量（不推荐，范围过大）

**范围：**
- P4.5 + P5.1 + P5.2 + P5.3 + P5.4

**不推荐理由：**
- P5.3 评论通知依赖通知基础设施，当前通知中心返回空列表，需先实现通知表和推送逻辑。
- P5.4 定时任务依赖飞书集成，超出当前阶段范围。

---

## 七、风险总结

| 风险项 | 严重程度 | 阻塞 P5 | 建议处理阶段 |
|--------|----------|---------|--------------|
| 日期过滤精度问题 | 高 | 是 | P4.5 |
| Service 层 limit 防御 | 中 | 否 | P4.5 |
| 团队日报/周报状态未实现 | 高 | 是 | P5.1 |
| 日报/周报未提交待办缺失 | 高 | 是 | P5.1 |
| 部门负责人团队范围未验证 | 中 | 否 | P5 或后续 |
| 周报聚合逻辑未实现 | 低 | 否 | P6 或后续 |
| 路由注册与计划文档不一致 | 低 | 否 | 可选 |
| 财务角色路由拦截不彻底 | 低 | 否 | 可选 |

---

## 八、建议交给 opencode 的施工单

### 施工单 1：P4.5 收口修复（最小闭环）

**目标：** 修复已知缺陷，确保 P0-P4 质量稳定。

**任务清单：**
1. 修改 `backend/app/services/work_report_service.py`：
   - `generate_daily_snapshot` 中所有 `created_at == report_date` 改为 `func.date(created_at) == report_date`
   - `generate_weekly_snapshot` 同理
2. 修改 `backend/app/services/work_report_service.py`：
   - `get_team_reports` 增加 `limit = min(limit, 100)`
3. 执行端到端 smoke 测试：
   - 销售角色：生成日报 → 提交 → 工作台状态更新
   - 业务经理：查看团队日报列表
   - 财务角色：访问 `/work-reports` 显示提示
4. 运行 `pytest -q` 确保无回归

**验收标准：**
- pytest 199 passed
- smoke 测试通过（提供截图或日志）

**预计工作量：** 1-2 小时

---

### 施工单 2：P5.1 工作台未提交待办（业务闭环）

**目标：** 个人角色工作台显示日报/周报未提交待办。

**任务清单：**
1. 修改 `backend/app/services/dashboard_workbench_service.py`：
   - `_build_sales_workbench`、`_build_technician_workbench`、`_build_channel_ops_workbench` 中，查询 `report_status`
   - 如果 `daily == "not_created"`，在 `todos` 中增加 `DashboardTodoItemNew(key="daily_report_missing", title="今日日报未提交", priority="high", link="/work-reports")`
   - 如果 `weekly == "not_created"` 且今天是周五/周六/周日，增加周报待办
2. 新增测试 `backend/tests/test_dashboard_workbench_service.py`：
   - 测试销售角色未提交日报时，工作台 todos 包含"今日日报未提交"
3. 运行 `pytest -q` 确保无回归

**验收标准：**
- 销售角色登录工作台，未提交今日日报时，待办列表显示"今日日报未提交"
- pytest 通过

**预计工作量：** 1-2 小时

---

### 施工单 3：P5.2 团队日报/周报提交率统计（业务闭环）

**目标：** 业务经理和部门负责人工作台显示团队日报/周报提交率。

**任务清单：**
1. 修改 `backend/app/services/dashboard_workbench_service.py`：
   - `_get_team_report_status` 实现真实统计逻辑：
     - 查询 `department_manager_id == user_id` 的成员（如果 `role == "business"` 则查全部 sales/technician/channel_ops）
     - 统计今日日报提交数 / 总人数
     - 统计本周周报提交数 / 总人数
     - 返回 `DashboardReportStatus(daily=f"{submitted}/{total} 已提交", weekly=f"{submitted}/{total} 已提交")`
2. 新增测试 `backend/tests/test_dashboard_workbench_service.py`：
   - 测试 business 角色工作台，团队 5 人 3 人已提交，显示"3/5 已提交"
3. 运行 `pytest -q` 确保无回归

**验收标准：**
- business 角色登录工作台，日报/周报状态显示"3/5 已提交"
- pytest 通过

**预计工作量：** 2 小时

---

## 九、总结

**当前状态：** P0-P4 已完成，整体架构合理，业务闭环基本完整。

**关键缺口：**
1. 日期过滤精度问题（高风险，必修）
2. 团队日报/周报状态未实现（高风险，阻塞业务闭环）
3. 日报/周报未提交待办缺失（高风险，阻塞业务闭环）

**建议下一步：**
- **立即执行：** 施工单 1（P4.5 收口修复）
- **紧接着执行：** 施工单 2 + 施工单 3（P5.1 + P5.2）
- **延期执行：** P5.3 评论通知、P5.4 定时任务（依赖外部能力）

**预计总工作量：** 4-6 小时（P4.5 + P5.1 + P5.2）

**风险可控性：** 高（修改范围小，测试覆盖充分，无破坏性变更）
