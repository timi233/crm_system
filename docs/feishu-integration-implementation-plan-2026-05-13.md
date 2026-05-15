# 飞书集成最终实施计划

日期：2026-05-13

关联文档：

- `docs/feishu-integration-readiness-plan-2026-05-13.md`
- `docs/feishu-field-work-approval-design.md`
- Claude 方案评审：`job_75c551c076e7`

## 目标

把 CRM 当前“已有飞书代码能力，但未完成真实对接”的状态，推进到可诊断、可登录、可同步组织、可观测派工消息与审批闭环的状态。

本计划按批次顺序施工。每一批完成并通过验证后，继续下一批，直到所有代码可交付项完成。真实飞书租户凭证、开放平台权限、回调白名单、事件订阅和应用发布属于外部联调前置条件，代码侧需提供诊断接口、mock 测试和 smoke checklist，不能因缺少真实凭证阻塞可测试代码交付。

## 最终顺序

| 批次 | 阶段 | 内容 | 状态 |
| --- | --- | --- | --- |
| 第一批 | P6.0 | 飞书配置/连通性自检 | 已完成，mock 验证通过 |
| 第一批 | P6.2 | OAuth 登录收口 | 已完成，mock 验证通过 |
| 第一批 | 数据基础 | 增加 `User.feishu_union_id` 和迁移 | 已完成 |
| 第二批 | P6.1 | CRM 飞书组织同步 | 已完成，mock 验证通过 |
| 第三批 | P6.3 | 派工飞书消息与审批联调收口 | 已完成，mock 验证通过 |
| 第四批 | P6.4 | 日报/周报飞书提醒 | 已完成，mock/dry-run 验证通过；真实推送需凭证联调 |

Claude 评审后确认：P6.2 应前置到 P6.1 之前。原因是 OAuth 用户身份匹配和 `union_id` 规则必须先稳定，组织同步才能减少返工。

## 关键设计决策

### 用户身份匹配

必须补充 `User.feishu_union_id`：

- `feishu_id` 保存飞书 `open_id`，用于当前应用内消息、卡片和审批。
- `feishu_union_id` 保存飞书 `union_id`，用于跨应用稳定识别和后续组织同步兜底。
- 字段要求：nullable、unique、index。

匹配优先级：

1. `open_id` -> `User.feishu_id`
2. `union_id` -> `User.feishu_union_id`
3. `email` -> `User.email`
4. `mobile` -> `User.phone`

### 新同步用户默认策略

新同步用户默认：

- `is_active=False`
- `role="sales"`
- `hashed_password=None`

管理员后续手动启用并调整角色。不要新增 `pending` 角色，避免扩大角色、权限、前端展示和策略改造范围。

已存在用户同步时：

- 可更新：`feishu_id`、`feishu_union_id`、姓名、邮箱、手机号、头像、部门。
- 不覆盖：`role`、`is_active`、密码、部门负责人关系。

### 路由组织

保留认证路由：

- `GET /auth/feishu/url`
- `POST /auth/feishu/login`

新增集成路由：

- `backend/app/routers/integrations/__init__.py`
- `backend/app/routers/integrations/feishu.py`

新增接口：

- `GET /integrations/feishu/status`
- `POST /integrations/feishu/check`
- `POST /integrations/feishu/sync-users`
- `GET /integrations/feishu/sync-preview`，可选

`/integrations/feishu/*` 全部限制管理员访问。

## 第一批：P6.0 + P6.2 + union_id

### 目标

先具备飞书配置可诊断能力，并修复 OAuth 登录身份绑定、错误提示和审计逻辑。

### 后端任务

1. 修改 `backend/app/models/user.py`
   - 增加 `feishu_union_id = Column(String, unique=True, index=True, nullable=True)`。

2. 新增 Alembic 迁移
   - 文件放在 `backend/alembic/versions/`。
   - 为 `users.feishu_union_id` 增加列、唯一索引和普通查询索引，按项目既有迁移风格实现。

3. 修改 `backend/app/schemas/user.py`
   - 用户输出、创建或更新 schema 中按需补充 `feishu_union_id`，不要暴露敏感信息。

4. 修改 `backend/app/services/feishu_service.py`
   - `get_user_by_code()` 返回 `union_id`。
   - 增加统一错误类型，例如 `FeishuAPIError`，区分飞书业务错误和网络错误。
   - token、OAuth 用户信息获取失败时返回可读错误，避免吞掉飞书错误码。

5. 新增 `backend/app/services/feishu_diagnostics_service.py`
   - `check_configuration()`：检查 `FEISHU_APP_ID`、`FEISHU_APP_SECRET`、`FEISHU_REDIRECT_URI`。
   - `check_tenant_token()`：验证 tenant access token。
   - `check_app_token()`：验证 app access token。
   - `check_permissions()`：可先 mock/verifiable，实现通讯录权限探测；真实权限不足时返回 readable error。

6. 新增 `backend/app/routers/integrations/feishu.py`
   - `GET /integrations/feishu/status`
   - `POST /integrations/feishu/check`
   - 返回字段建议：
     - `configured`
     - `tenant_token_ok`
     - `app_token_ok`
     - `ws_enabled`
     - `ws_running`
     - `redirect_uri`
     - `last_error`
   - 非管理员返回 403。

7. 修改 `backend/app/main.py`
   - 注册飞书集成 router。

8. 修改 `backend/app/routers/auth.py`
   - OAuth 登录匹配优先级改为 `open_id > union_id > email > phone`。
   - 登录成功时同时更新 `feishu_id` 和 `feishu_union_id`。
   - 未同步用户返回 403，错误信息明确：“用户未同步，请联系管理员”。
   - 禁用用户返回 403，错误信息明确：“用户已禁用，请联系管理员”。
   - state 过期或校验失败返回 401，错误信息明确：“登录链接已过期，请重新登录”。
   - 登录成功和失败尽量记录操作日志；如果现有日志服务不适合公开登录失败，也至少保留结构化日志。

### 测试

新增或更新：

- `backend/tests/test_feishu_diagnostics.py`
- `backend/tests/test_feishu_oauth.py`

覆盖：

- 未配置凭证时 status 返回 `configured=false`。
- mock token 成功时 check 返回 `tenant_token_ok=true`、`app_token_ok=true`。
- mock 飞书错误码时返回可读错误。
- 非管理员访问 `/integrations/feishu/*` 返回 403。
- 已同步启用用户飞书登录成功。
- 通过 `union_id` 匹配现有用户并写回 `feishu_id`。
- 未同步用户登录返回 403。
- 禁用用户登录返回 403。
- state 过期返回 401。

### 验收命令

```bash
cd backend && APP_ENV=test ./venv/bin/python -m pytest tests/test_feishu_diagnostics.py tests/test_feishu_oauth.py -q
cd backend && APP_ENV=test ./venv/bin/python -m pytest -q
```

## 第二批：P6.1 CRM 飞书组织同步

### 目标

参考派工系统实现 CRM 组织用户同步，让 CRM 用户具备飞书身份数据，为登录、消息和审批提供基础。

### 后端任务

1. 扩展 `backend/app/services/feishu_service.py`
   - `get_departments(parent_id="0")`，支持分页。
   - `get_department_members(department_id)`，支持分页。
   - `get_user_info(user_id)`，按需实现。

2. 新增 `backend/app/services/feishu_org_sync_service.py`
   - `sync_users()`：执行同步。
   - `preview_sync_users()`：可选，实现同步预览。
   - 匹配优先级：`open_id > union_id > email > phone`。
   - 已存在用户只更新飞书身份和基础资料，不覆盖角色和启用状态。
   - 新用户按默认策略创建为禁用销售角色。
   - 返回同步结果：
     - `created`
     - `updated`
     - `skipped`
     - `errors`
     - `created_users`
     - `updated_users`
     - `error_details`

3. 扩展 `backend/app/routers/integrations/feishu.py`
   - `POST /integrations/feishu/sync-users`
   - `GET /integrations/feishu/sync-preview`，可选
   - 仅管理员可访问。

4. 审计日志
   - 同步开始、创建用户、更新用户、同步失败应尽量记录到现有 operation log。

### 测试

新增：

- `backend/tests/test_feishu_org_sync.py`

覆盖：

- mock 部门和成员后可创建新用户。
- 新用户 `is_active=False`、`role="sales"`、`hashed_password=None`。
- 已存在用户不覆盖 `role` 和 `is_active`。
- open_id、union_id、email、phone 匹配优先级正确。
- 飞书 API 分页结果能被完整处理。
- 单个成员异常不应中断整批同步，返回 `error_details`。

### 验收命令

```bash
cd backend && APP_ENV=test ./venv/bin/python -m pytest tests/test_feishu_org_sync.py -q
cd backend && APP_ENV=test ./venv/bin/python -m pytest -q
```

## 第三批：P6.3 派工飞书消息与审批联调收口

### 目标

让派工飞书卡片、技术员确认、审批实例创建、审批状态回写形成可观测和可重试闭环。

### 后端任务

1. 修改 `backend/app/models/work_order.py`
   - 在 `WorkOrderTechnician` 增加：
     - `feishu_message_status`：`pending/success/failed`
     - `feishu_message_error`：失败原因
   - 增加对应迁移。

2. 修改 `backend/app/services/feishu_card_service.py`
   - 发送成功后记录 `feishu_message_id` 和 `feishu_message_status="success"`。
   - 发送失败后记录 `feishu_message_status="failed"` 和错误信息。
   - 飞书失败不阻断主业务流程。

3. 修改派工通知服务
   - 保持现有派工业务状态不被飞书失败阻断。
   - 对没有 `feishu_id` 的技术员返回可观测 skipped/failed 状态。

4. 新增手动重发接口
   - 建议放在 `backend/app/routers/work_order.py`：
     - `POST /work-orders/{id}/technicians/{tech_id}/feishu-retry`
   - 仅有派工管理权限的角色可执行。

5. 修改 `backend/app/services/feishu_ws_service.py`
   - 增加 `get_status()`：
     - `running`
     - `last_event_at`
     - `event_count`
     - `error_count`
   - `/integrations/feishu/status` 包含 WebSocket 状态。

6. 事件幂等
   - 卡片重复点击不重复创建审批。
   - 审批状态重复事件不重复改变状态。
   - 对事件 ID 或审批实例状态做可测试防重复处理。

7. 新增 smoke checklist
   - `docs/feishu-dispatch-smoke-checklist.md`
   - 包含真实联调前置条件、测试用户、回调白名单、事件订阅、派工发卡片、卡片确认、审批通过/拒绝、CRM 状态回写。

### 测试

更新：

- `backend/tests/test_feishu_dispatch_integration.py`

覆盖：

- 飞书卡片发送成功记录 success。
- 飞书卡片发送失败记录 failed 和错误原因。
- 手动重发接口可重新发送。
- 无 `feishu_id` 技术员不会导致派工失败。
- 重复卡片点击不重复创建审批。
- 重复审批事件不重复修改状态。
- `/integrations/feishu/status` 返回 `ws_running` 或 `ws_status`。

### 验收命令

```bash
cd backend && APP_ENV=test ./venv/bin/python -m pytest tests/test_feishu_dispatch_integration.py -q
cd backend && APP_ENV=test ./venv/bin/python -m pytest -q
```

## 第四批：P6.4 日报/周报飞书提醒

### 目标

复用 P5 工作台待办逻辑，把未提交日报/周报提醒发送到飞书。

### 后端任务

1. 新增 `backend/app/services/work_report_reminder_service.py`
   - 查询需要提醒的用户。
   - 复用工作台未提交日报/周报判断逻辑，避免两套规则漂移。
   - 对无 `feishu_id` 用户跳过并记录原因。
   - 飞书发送失败不阻断扫描任务。

2. 新增管理员手动触发接口
   - 建议放在 `backend/app/routers/integrations/feishu.py`：
     - `POST /integrations/feishu/work-report-reminders/run`
   - 支持 dry-run。

3. 定时任务
   - 若项目已有调度器，接入定时任务。
   - 若没有调度器，先交付手动触发接口和服务层，定时运行留作部署配置。

4. 消息内容
   - 日报：提醒当天未提交。
   - 周报：周五、周六、周日提醒本周未提交。
   - 消息包含系统入口链接，链接地址来自配置项或前端基础 URL。

### 测试

新增：

- `backend/tests/test_work_report_reminders.py`

覆盖：

- 未提交日报用户进入提醒列表。
- 已提交日报用户不提醒。
- 周五到周日未提交周报用户进入提醒列表。
- finance 角色不参与日报/周报提醒。
- 无 `feishu_id` 用户 skipped。
- dry-run 不调用飞书发送。

### 验收命令

```bash
cd backend && APP_ENV=test ./venv/bin/python -m pytest tests/test_work_report_reminders.py -q
cd backend && APP_ENV=test ./venv/bin/python -m pytest -q
```

## 前端范围

本轮优先完成后端可诊断、可同步、可联调能力。前端如时间允许可增加一个轻量入口：

- 管理员可在系统设置或集成页面查看 `/integrations/feishu/status`。
- 管理员可点击执行 `/integrations/feishu/check` 和 `/sync-users`。

如果项目当前没有集成设置页面，前端可后置，不阻塞后端交付。

无论是否改前端，最终必须运行：

```bash
cd frontend && npm run build
```

## 外部联调前置条件

真实联调需要人工在飞书开放平台配置：

- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`
- `FEISHU_REDIRECT_URI`
- OAuth 回调白名单
- 通讯录读取权限
- 发送消息权限
- 审批实例创建权限
- 卡片交互事件订阅
- 审批状态变更事件订阅
- 应用发布范围包含测试用户、销售、技术员、管理员
- 后端公网 WebSocket/事件通道按飞书要求可访问

如果缺少以上配置，opencode 仍应完成 mock 可验证代码、诊断接口和 smoke 文档，并在最终报告中列出真实联调阻塞项。

## 全量验收

每批完成后执行对应测试。全部代码施工完成后执行：

```bash
cd backend && APP_ENV=test ./venv/bin/python -m pytest tests/test_feishu_diagnostics.py tests/test_feishu_oauth.py tests/test_feishu_org_sync.py tests/test_feishu_dispatch_integration.py tests/test_work_report_reminders.py -q
cd backend && APP_ENV=test ./venv/bin/python -m pytest -q
cd frontend && npm run build
```

最终交付报告必须包含：

- 每批完成状态。
- 修改文件列表。
- 新增/修改接口列表。
- 数据库迁移文件列表。
- 测试命令和结果。
- 真实飞书联调是否完成；如未完成，列出缺少的开放平台配置和凭证。

## 验收记录

验收日期：2026-05-13

代码侧四批施工已落盘并完成本地 mock 验证。真实飞书租户联调尚未执行，原因是当前环境没有真实 `FEISHU_APP_ID`、`FEISHU_APP_SECRET`、开放平台权限、回调白名单、事件订阅和应用发布范围配置。

本次验收结果：

```bash
cd backend && ./venv/bin/alembic heads
# feishu_message_status_20260513 (head)

cd backend && APP_ENV=test ./venv/bin/python -m pytest tests/test_feishu_diagnostics.py tests/test_feishu_oauth.py tests/test_feishu_org_sync.py tests/test_feishu_dispatch_integration.py tests/test_work_report_reminders.py -q
# 56 passed, 10 warnings

cd backend && APP_ENV=test ./venv/bin/python -m pytest -q
# 253 passed, 10 warnings

cd frontend && npm run build
# build successful
```

验收中发现并修复了一个迁移结构问题：`feishu_union_id_20260513` 与 `feishu_message_status_20260513` 原本形成双 head，且前者误包含派工消息字段。现已整理为单线迁移：

1. `work_reports_20260513`
2. `feishu_union_id_20260513`
3. `feishu_message_status_20260513`
