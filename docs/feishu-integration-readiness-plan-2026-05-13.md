# 飞书集成现状评估与实施计划

日期：2026-05-13

参考来源：

- CRM 当前实现：`backend/app/services/feishu_service.py`、`feishu_ws_service.py`、`feishu_card_service.py`、`feishu_approval_service.py`
- CRM 派工联动：`backend/app/routers/dispatch.py`、`backend/app/routers/work_order.py`、`backend/app/services/work_order_notification_service.py`
- 派工系统参考实现：`new_task_mgt/server/src/feishu/feishuService.ts`、`new_task_mgt/server/src/routes/auth.ts`、`new_task_mgt/server/src/routes/user.ts`
- 设计文档：`docs/feishu-field-work-approval-design.md`

## 当前判断

当前 CRM 代码已经具备飞书集成雏形，但不能视为已经完成真实飞书对接。

证据：

- `backend/.env.example` 中 `FEISHU_APP_ID`、`FEISHU_APP_SECRET` 为空，`FEISHU_WS_ENABLED=false`。
- `backend/app/main.py` 只有在 `FEISHU_WS_ENABLED=true` 时才启动飞书 WebSocket。
- 前端已有飞书登录入口和回调页，后端已有 `/auth/feishu/url`、`/auth/feishu/login`。
- 后端已有 tenant/app token、消息卡片、审批实例、WebSocket 事件处理代码。
- 测试覆盖主要是 payload、事件路由、状态处理，不是使用真实飞书应用的联调。
- 派工系统 `new_task_mgt` 已实现组织同步、用户登录、飞书消息通知等可参考代码，但 CRM 尚未完整吸收组织同步和联调诊断能力。

因此当前状态应定义为：

> 代码能力存在，真实租户配置、权限开通、事件订阅、组织同步和端到端联调未完成。

## 现有 CRM 飞书能力

### 已有

- 飞书 OAuth 登录：
  - 后端：`GET /auth/feishu/url`、`POST /auth/feishu/login`
  - 前端：登录页飞书按钮、`/auth/feishu/callback`
- 飞书 token 获取：
  - tenant_access_token
  - app_access_token
- 派工卡片消息：
  - 给技术员发送交互卡片
  - 卡片按钮包含确认/拒绝
  - `feishu_message_id` 写回 `work_order_technicians`
- 飞书 WebSocket：
  - 监听卡片交互事件
  - 监听审批状态变更事件
- 外勤审批：
  - 技术员确认接单后创建审批实例
  - 审批状态回写工单技术员分配记录和工单状态

### 缺口

- 缺少飞书配置自检接口或命令，无法快速判断 app_id/app_secret/权限/回调配置是否有效。
- 缺少 CRM 侧飞书组织同步能力。
- CRM 飞书登录策略是“预注册用户绑定 open_id”，不会像派工系统那样自动同步组织并创建用户。
- WebSocket 默认关闭，且缺少运行状态健康检查。
- 飞书事件订阅、机器人能力、审批权限、通讯录权限需要在开放平台人工配置，当前项目无自动验证。
- 派工卡片发送失败只记录日志，缺少站内降级通知、重试队列或后台可见失败状态。
- 缺少真实联调 smoke：登录、同步用户、派工发卡片、卡片确认、审批创建、审批状态回写。

## 派工系统可参考点

`new_task_mgt` 中值得借鉴的能力：

- `FeishuService.getDepartments()`：分页获取部门。
- `FeishuService.getDepartmentMembers()`：按部门获取成员。
- `syncFeishuOrganization()`：以 `open_id` 为主、`union_id/phone` 兜底匹配，新增用户默认无权限，管理员后续分配。
- 飞书登录时更新用户基础信息：姓名、手机号、邮箱、头像。
- 消息通知失败不阻断主业务流程。

CRM 应采用更保守策略：

- 新飞书用户同步进 CRM 时默认 `is_active=False` 或无业务角色，避免自动获得 CRM 权限。
- 飞书 OAuth 登录只允许已启用用户登录；未同步或未启用用户返回明确错误。
- 组织同步仅管理员可执行。

## P6：飞书集成建设计划

### P6.0：飞书配置与连通性自检

目标：在没有真实业务操作前，先能判断飞书应用是否配置可用。

后端任务：

- 新增 `backend/app/services/feishu_diagnostics_service.py`
  - 检查 `FEISHU_APP_ID`、`FEISHU_APP_SECRET` 是否配置。
  - 调用 tenant_access_token 接口验证凭证。
  - 调用 app_access_token 接口验证 OAuth 凭证。
  - 返回 token 获取成功/失败、错误码、错误信息。
- 新增管理员接口：
  - `GET /integrations/feishu/status`
  - `POST /integrations/feishu/check`
- 返回结构建议：
  - `configured`
  - `tenant_token_ok`
  - `app_token_ok`
  - `ws_enabled`
  - `redirect_uri`
  - `last_error`
- 测试：
  - 未配置凭证时返回 `configured=false`
  - mock 飞书 token 成功时返回 ok
  - mock 飞书错误码时返回可读错误

验收：

- 管理员可查看飞书配置是否可用。
- 非管理员不可访问。
- 不需要真实飞书凭证也能通过单元测试。

### P6.1：CRM 飞书组织同步

目标：参考派工系统，补齐 CRM 侧组织和用户同步。

后端任务：

- 扩展 `backend/app/services/feishu_service.py`
  - `get_departments(parent_id="0")`
  - `get_department_members(department_id)`
  - `get_user_info(user_id)` 可选
- 新增 `backend/app/services/feishu_org_sync_service.py`
  - 拉取部门和成员。
  - 使用 `open_id` 匹配 `User.feishu_id`。
  - 使用邮箱/手机号做兜底匹配。
  - 已存在用户只补充 `feishu_id`、头像、部门等基础字段，不覆盖业务角色。
  - 新用户默认无权限：建议 `role="sales"` 不可取，应使用 `role="pending"` 或 `is_active=False`。若当前角色枚举不支持 `pending`，先创建为 `is_active=False` 并由管理员启用。
  - 同步结果返回 created/updated/skipped/errors。
- 新增管理员接口：
  - `POST /integrations/feishu/sync-users`
  - `GET /integrations/feishu/sync-preview` 可选
- 前端可后置，先用接口完成。

验收：

- mock 飞书部门/成员后可创建或更新 CRM 用户。
- 新用户不会自动获得有效业务权限。
- 已存在用户不会被覆盖角色。

### P6.2：飞书 OAuth 登录收口

目标：让飞书登录可被真实用户稳定使用。

任务：

- 保持当前“预注册/已同步用户才能登录”的安全策略。
- 登录失败时给出明确原因：
  - 未同步用户
  - 用户未启用
  - 飞书账号与 CRM 用户不匹配
  - OAuth state 过期
- 记录登录审计日志。
- 增加测试覆盖：
  - 已同步启用用户登录成功。
  - 未同步用户 403。
  - 禁用用户 403。
  - 生产环境 state 校验失败 401。

验收：

- `/auth/feishu/url` 生成的 redirect_uri 与飞书后台白名单一致。
- `/auth/feishu/login` 可用 mock 完整走通。

### P6.3：派工飞书消息与审批联调收口

目标：让派工发卡片、卡片确认、审批创建、审批状态回写形成可观测闭环。

后端任务：

- 增加飞书消息发送状态记录：
  - 成功：保存 `feishu_message_id`
  - 失败：记录失败原因到日志或扩展字段
- 增加手动重发接口：
  - `POST /work-orders/{id}/feishu-notifications/retry`
- 增加 WebSocket 状态健康检查：
  - `/integrations/feishu/status` 包含 `ws_running`
- 增加事件处理幂等：
  - 卡片重复点击不重复创建审批。
  - 审批状态重复事件不重复改变状态。
- 增加联调 smoke checklist 文档。

验收：

- 指定有 `feishu_id` 的技术员，派工后能发送飞书卡片。
- 点击确认后创建外勤审批实例。
- 审批通过后 CRM 工单进入可继续流转状态。
- 卡片拒绝后 CRM 记录拒绝状态。

### P6.4：飞书日报/周报提醒

目标：复用 P5 工作台待办，把未提交提醒推送到飞书。

任务：

- 查询 `dashboard_workbench.todos` 或复用同一服务逻辑。
- 每日/每周扫描未提交日报/周报用户。
- 发送飞书消息给用户。
- 失败不阻断业务，记录失败原因。

验收：

- 用户未提交日报时收到飞书提醒。
- 用户无 `feishu_id` 时跳过并记录。

## 开放平台人工配置清单

需要在飞书开放平台完成：

- OAuth 回调地址白名单：
  - development: `http://localhost:3002/auth/feishu/callback`
  - test/prod 使用对应公网前端地址。
- 应用权限：
  - 获取用户基本信息。
  - 获取通讯录部门。
  - 获取部门成员。
  - 发送消息给用户。
  - 创建审批实例。
  - 接收消息卡片交互事件。
  - 接收审批状态变更事件。
- 事件订阅：
  - `im.message.card_action_trigger`
  - `approval.instance.status_changed`
- 应用发布：
  - 确认企业内可用范围包含测试用户、销售、技术员。

## 推荐下一步

建议先交付 P6.0 + P6.1：

- P6.0 能快速判断飞书凭证和基础 API 是否可用。
- P6.1 能把 CRM 用户的 `feishu_id` 数据补齐，这是后续 OAuth、消息、审批的前置条件。

在没有真实飞书凭证和开放平台权限前，不建议直接做 P6.3 真实派工审批联调。
