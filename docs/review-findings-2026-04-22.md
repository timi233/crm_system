# CRM Review Findings

Date: 2026-04-22

## Scope

本次 review 重点覆盖以下高风险链路：

- 认证与能力透出
- 统一策略层与实际后端授权
- 渠道跟进 / 业务跟进拆分
- 渠道业绩、渠道培训相关权限
- 仪表盘与跟进数据汇总

说明：

- 本次不是逐行审完全部改动文件。
- 本文仅记录当前已确认的高优先级问题，便于后续按项修复。

## Findings

### 1. 业务仪表盘仍混入渠道跟进

文件：

- `backend/app/routers/dashboard.py:144-149`
- `backend/app/routers/dashboard.py:271-307`
- `backend/app/routers/dashboard.py:329-358`
- `frontend/src/pages/MyDashboard.tsx:341`
- `frontend/src/pages/MyDashboard.tsx:374`

问题：

- 仪表盘中的“待跟进 / 今日待办 / 最近跟进记录”仍然直接查询全部 `FollowUp`。
- 查询没有过滤 `follow_up_type == "business"`，因此渠道跟进会继续混入业务视图。
- 渠道跟进通常没有 `lead_id / opportunity_id / project_id`，后端会生成空的 `entity_type=""` 和 `entity_id=0`。
- 前端仍把这些入口统一跳到 `/business-follow-ups` 或业务实体详情，存在数据口径错误和无效跳转风险。

影响：

- “业务跟进 / 渠道跟进”概念拆分在仪表盘层面没有真正落地。
- 用户看到的数据仍是混合口径，容易误判工作量和待办。

建议：

- 仪表盘业务口径统一只统计 `follow_up_type == "business"`。
- 如果后续需要单独展示渠道跟进，新增独立指标，不要复用业务卡片。

优先级：P0

### 2. 跟进记录带无效 channel_id 时缺少 404 校验

文件：

- `backend/app/routers/follow_up.py:249-255`
- `backend/app/routers/follow_up.py:448-453`

问题：

- `POST /follow-ups/` 和 `PUT /follow-ups/{id}` 在带 `channel_id` 时，只在查到渠道对象后才做权限校验。
- 如果渠道不存在，当前逻辑不会返回 404，而是继续执行后续创建/更新流程。
- 最终会表现为数据库完整性错误或 500，而不是明确的“渠道不存在”。

影响：

- 前端提交错误数据时，用户拿到的是非预期 500。
- 这类错误会干扰权限、表单、接口问题的排查。

建议：

- 与 lead / opportunity / project 的处理保持一致。
- 查询 `channel_id` 后，如不存在，立即返回 `HTTP 404: Channel not found`。

优先级：P0

### 3. capabilities 返回值与真实策略层授权不一致

文件：

- `backend/app/routers/auth.py:159-168`
- `backend/app/core/policy/resources/execution_plan.py:165-184`
- `backend/app/core/policy/resources/unified_target.py:125-132`

问题：

- `/auth/me/capabilities` 当前把所有 `sales` 都标记为：
  - `channel_performance:manage = true`
  - `channel_training:manage = true`
- 但真实后端授权要求销售对目标渠道拥有 `write` 级分配权限，才能创建培训计划或渠道业绩目标。

影响：

- 前端会为所有销售展示“可管理”入口和操作按钮。
- 用户点击后会被后端 403 拒绝，形成“按钮能点但提交失败”的体验。

建议：

- 能力透出不要只按角色粗判。
- 应与策略层保持同口径，至少区分：
  - 全局管理能力
  - 需依赖渠道分配关系的对象级写权限
- 如果暂时无法精确计算对象级 capability，应把页面能力定义成“可进入页面”而不是“可直接管理全部渠道”。

优先级：P1

### 4. `_can_create_resource()` 吞掉了所有异常

文件：

- `backend/app/routers/auth.py:100-108`

问题：

- `_can_create_resource()` 中使用了裸 `except Exception: return False`。
- 这会把权限拒绝、数据库错误、代码 bug、策略层异常全部吞掉，最后统一伪装成“无创建权限”。

影响：

- 一旦策略层或能力接口本身有 bug，排查会非常困难。
- 前端看到的 capabilities 可能是错误的，但后端日志和接口表面上看不出根因。

建议：

- 仅捕获预期的授权异常。
- 对非授权异常保留日志并继续抛出，避免把真实错误静默降级成权限问题。

优先级：P1

## Suggested Fix Order

建议修复顺序：

1. 修复仪表盘对 `follow_up_type` 的过滤，确保业务跟进与渠道跟进彻底分流。
2. 修复 `follow_up` 的 `channel_id` 不存在时返回 404。
3. 对齐 `/auth/me/capabilities` 与统一策略层的真实授权口径。
4. 收紧 `_can_create_resource()` 的异常捕获范围，避免吞错。

## Status

- 已记录 review 结果
- 已有部分问题修复，需继续复查

## Recheck Update

Date: 2026-04-22

### 已确认修复

#### A. 业务仪表盘已开始按业务跟进口径过滤

文件：

- `backend/app/routers/dashboard.py`

现状：

- `summary` 中的跟进统计已增加 `FollowUp.follow_up_type == "business"` 过滤。
- 说明“渠道跟进混入业务仪表盘”的主方向已被处理。

说明：

- 该项不是完全无风险，因为后续又引入了新的 `todos` 逻辑错误，见下文。

#### B. `follow_up` 在无效 `channel_id` 时已返回 404

文件：

- `backend/app/routers/follow_up.py`

现状：

- `POST /follow-ups/` 和 `PUT /follow-ups/{id}` 在带 `channel_id` 时，已在渠道不存在时明确返回：
  - `404 Channel not found`

结论：

- 该项已按预期修复。

#### C. `_can_create_resource()` 不再吞掉全部异常

文件：

- `backend/app/routers/auth.py`

现状：

- 现在仅对 `HTTPException(403)` 返回 `False`
- 其他异常会记录日志并继续抛出

结论：

- 该项已按预期修复。

### 新发现问题

#### D. `/dashboard/todos` 引入了新的运行时错误

文件：

- `backend/app/routers/dashboard.py:291-299`

问题：

- `get_dashboard_todos()` 中查询语句直接使用了 `.limit(limit)`。
- 但该函数没有定义 `limit` 参数，也没有局部变量 `limit`。
- 请求命中该接口时会触发 `NameError`，最终表现为 500。

影响：

- 首页“今日待办”接口会直接失败。
- 会导致登录后首页部分区域无法正常加载。

建议：

- 删除这处未定义的 `limit` 使用，或为 handler 显式补充 `limit` 参数。
- 保持与 `recent-followups` 的参数设计一致。

优先级：P0

#### E. capabilities 与真实策略层授权仍未对齐

文件：

- `backend/app/routers/auth.py:205-210`
- `backend/app/core/policy/resources/execution_plan.py:165-184`
- `backend/app/core/policy/resources/unified_target.py:125-133`
- `frontend/src/pages/ChannelPerformancePage.tsx`
- `frontend/src/pages/ChannelTrainingPage.tsx`

问题：

- 当前 `/auth/me/capabilities` 将：
  - `channel_performance:manage`
  - `channel_training:manage`
 统一收紧为仅 `admin/business = true`
- 但后端真实策略层仍允许：
  - 具备目标渠道 `write` 分配权限的 `sales`
 进行渠道培训计划创建与渠道业绩目标创建。

影响：

- 权限失配依然存在，只是方向变了：
  - 之前是“前端放开，后端 403”
  - 现在变成“后端允许，但前端没有入口”
- 销售即使具备实际渠道写权限，也可能在前端看不到管理按钮。

建议：

- capability 设计要与策略层同口径。
- 如果无法精确返回“所有可管理渠道集合”，至少不要把页面级管理能力简单降成纯角色判断。
- 可以考虑：
  - 页面允许进入
  - 具体渠道级操作再由接口校验
  - 或单独提供“当前用户可管理渠道列表”接口

优先级：P1

## Current Status Summary

当前状态可分为三类：

1. 已修复

- 无效 `channel_id` 返回 404
- `_can_create_resource()` 不再吞全部异常

2. 部分修复但仍有回归

- 仪表盘已开始按业务跟进过滤，但 `/dashboard/todos` 新增了未定义变量 `limit` 的问题

3. 仍未闭环

- `channel_performance:manage` / `channel_training:manage` 的 capability 与真实策略层授权不一致

## Recheck Update 2

Date: 2026-04-22

### 已确认继续修复

#### F. `/dashboard/todos` 的未定义 `limit` 问题已修复

文件：

- `backend/app/routers/dashboard.py`

现状：

- `get_dashboard_todos()` 中已移除对未定义变量 `limit` 的直接依赖。
- 当前查询逻辑不再因为 `NameError` 导致接口直接 500。

结论：

- 该项已修复。

### 仍未闭环

#### G. 渠道管理 capability 被直接写死为 `False`

文件：

- `backend/app/routers/auth.py:203-204`
- `backend/app/core/policy/resources/execution_plan.py`
- `backend/app/core/policy/resources/unified_target.py`
- `frontend/src/pages/ChannelPerformancePage.tsx`
- `frontend/src/pages/ChannelTrainingPage.tsx`

问题：

- `/auth/me/capabilities` 当前直接返回：
  - `channel_performance:manage = False`
  - `channel_training:manage = False`
- 但后端策略层仍然允许：
  - 对目标渠道具备 `write` 分配权限的 `sales`
 进行渠道培训计划创建与渠道业绩目标创建。
- 前端页面又直接依赖这两个 capability 控制管理入口。

影响：

- 具备实际渠道写权限的销售用户，前端仍然看不到渠道业绩和渠道培训的管理入口。
- 当前状态不是“近似不准”，而是前端把这类管理能力整体锁死。

结论：

- 该问题仍未修复。
- 当前实现属于“后端允许、前端不可达”的权限失配。

建议方案：

方案 A：页面级能力与对象级写权限解耦

- 增加页面进入能力，例如：
  - `channel_performance:manage_page`
  - `channel_training:manage_page`
- 允许 `sales` 进入页面
- 实际保存/删除等动作继续由后端策略层按渠道写权限校验

方案 B：能力接口直接返回“可管理渠道列表”

- 前端按渠道粒度展示可操作按钮
- 精度最高，但改动更大

建议优先采用方案 A，先快速收口。

优先级：P1

## Latest Status Summary

最新状态：

1. 已修复

- 无效 `channel_id` 返回 404
- `_can_create_resource()` 不再吞全部异常
- `/dashboard/todos` 的未定义 `limit` 问题

2. 已部分修复

- 仪表盘业务跟进已按 `follow_up_type == "business"` 分流

3. 仍未闭环

- `channel_performance:manage` / `channel_training:manage` 仍与真实策略层授权不一致
