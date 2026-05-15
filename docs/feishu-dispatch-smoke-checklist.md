# 飞书派工联调 Smoke Checklist

日期：2026-05-13

## 真实联调前置条件

在执行真实飞书联调前，需要在飞书开放平台完成以下配置：

### 应用凭证

- `FEISHU_APP_ID` - 飞书应用 ID
- `FEISHU_APP_SECRET` - 飞书应用密钥
- `FEISHU_REDIRECT_URI` - OAuth 回调地址（需在飞书开放平台白名单）

### 权限配置

- 通讯录读取权限（`contact:user.base:readonly`）
- 发送消息权限（`im:message:send_as_bot`）
- 审批实例创建权限（`approval:approval:readonly` + `approval:approval:write`）
- 卡片交互事件订阅权限
- 审批状态变更事件订阅权限

### 事件订阅

- 卡片交互事件：`im.message.card_action_trigger`
- 审批状态变更事件：`approval.instance.status_changed`
- 后端公网 WebSocket/事件通道按飞书要求可访问

### 应用发布范围

- 测试用户、销售、技术员、管理员需在应用发布范围内

## Smoke 测试步骤

### 1. 飞书配置诊断

```bash
# 管理员登录后访问诊断接口
curl -X POST http://localhost:8000/integrations/feishu/check \
  -H "Authorization: Bearer <admin_jwt_token>"
```

预期返回：
- `configured: true`
- `tenant_token_ok: true`
- `app_token_ok: true`
- `ws_running: true` (如果启用 WebSocket)

### 2. 组织同步测试

```bash
# 预览同步
curl -X GET http://localhost:8000/integrations/feishu/sync-preview \
  -H "Authorization: Bearer <admin_jwt_token>"

# 执行同步
curl -X POST http://localhost:8000/integrations/feishu/sync-users \
  -H "Authorization: Bearer <admin_jwt_token>"
```

预期返回：
- `created` 和 `updated` 数量合理
- `errors: 0`

### 3. 测试用户飞书登录

- 使用测试用户通过飞书 OAuth 登录
- 验证用户 `feishu_id` 和 `feishu_union_id` 正确写入

### 4. 派工卡片发送测试

1. 创建工单并分配技术员（技术员必须有 `feishu_id`）
2. 技术员飞书收到派工通知卡片
3. 检查 `WorkOrderTechnician.feishu_message_status` 为 `SUCCESS`

### 5. 卡片确认/拒绝测试

- 技术员点击"确认接收"按钮
- 验证审批实例创建成功
- 验证 `WorkOrderTechnician.approval_instance_code` 写入
- 技术员点击"拒绝接收"按钮
- 验证状态更新为 `REJECTED`

### 6. 审批状态回写测试

- 飞书审批通过：CRM 工单状态更新为 `ACCEPTED`
- 飞书审批拒绝：CRM 技术员状态更新为 `REJECTED`

### 7. 消息重发测试

```bash
# 手动重发飞书通知
curl -X POST http://localhost:8000/work-orders/{id}/technicians/{tech_id}/feishu-retry \
  -H "Authorization: Bearer <jwt_token>"
```

预期返回：
- `success: true`
- `message_id` 更新

## 无真实凭证时的 Mock 验证

如果缺少真实飞书凭证，以下测试可通过 Mock 完成：

```bash
cd backend
APP_ENV=test ./venv/bin/python -m pytest tests/test_feishu_diagnostics.py tests/test_feishu_oauth.py tests/test_feishu_org_sync.py tests/test_feishu_dispatch_integration.py -q
```

预期：所有测试通过

## 外部阻塞项

如果真实联调未能完成，记录阻塞项：

- [ ] 飞书应用未创建
- [ ] 应用凭证未配置
- [ ] 通讯录权限未开通
- [ ] 消息发送权限未开通
- [ ] 审批权限未开通
- [ ] 事件订阅未配置
- [ ] 应用未发布到目标用户
- [ ] 后端 WebSocket 通道不可访问

## 验收标准

- Mock 测试全部通过
- 真实联调 smoke checklist 全部完成
- 或已记录外部阻塞项并说明原因