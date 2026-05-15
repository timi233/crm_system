# 通知中心最小闭环建设计划

日期：2026-05-15
负责人：agent2 计划协调
施工目标：交给 `agent3`
当前状态：已完成

## 背景与目标

本阶段目标是建设统一站内通知中心，并合并日报/周报评论通知 P5.3。

当前代码已有基础：

- `backend/app/models/notification.py`：已有 `Notification` 表。
- `backend/app/models/user_notification_read.py`：已有旧式按业务对象记录已读的表。
- `backend/app/routers/dashboard.py`：已有 `/dashboard/notifications` 和 `/dashboard/notifications/mark-read`，但当前列表直接返回空数组。
- `frontend/src/hooks/useDashboard.ts`：已有 dashboard 通知 hook，但没有独立通知中心页面或抽屉。
- `backend/app/services/feishu_org_sync_service.py`：已在离职检测时直接写入 `Notification`。

本阶段不从零设计，应复用现有 `Notification` 表并收敛现有散点写入。

## 业务边界

本阶段包含：

- 站内通知列表。
- 未读/已读状态。
- 单条或批量已读。
- 通知跳转到关联业务对象。
- 统一通知写入 service。
- 日报/周报评论模型和评论通知 P5.3。
- 前端右上角通知入口和通知中心全屏页。

本阶段不包含：

- 飞书外发。
- 定时提醒 P5.4。
- 通知订阅规则。
- 多渠道消息投递。
- 复杂审批流。
- 通用任务/日程中心。

## 默认决策

- 首批只做站内通知，不接飞书外发。
- 通知读取以 `Notification.is_read/read_at` 为准，`UserNotificationRead` 暂保留兼容，不继续扩展。
- 新增独立 `WorkReportComment` 表，不复用 `Notification` 表表达评论实体。
- 通知 API 使用独立前缀 `/notifications`，dashboard 旧接口可复用 service 或保持兼容。
- 前端新增独立路由 `/notifications`，工作台或右上角入口跳转到该路由。

## 实施批次

| 批次 | 目标 | 状态 |
|------|------|------|
| N0 | 现状收敛：Notification schema/service/router 设计，旧 dashboard 通知接口兼容 | 已完成 |
| N1 | 后端通知中心 API：列表、未读数、单条已读、批量已读 | 已完成 |
| N2 | 通知写入统一入口：`notification_service.create()`，迁移现有离职交接写入点 | 已完成 |
| N3 | 前端通知中心：hook、通知列表页、右上角/菜单入口、业务跳转 | 已完成 |
| N4 | P5.3 日报/周报评论：评论模型、接口、前端评论区、评论通知 | 已完成 |
| N5 | 验收与文档：测试、构建、README/计划归档 | 已完成 |

## N0/N1：后端通知中心 API

### 建议新增文件

- `backend/app/schemas/notification.py`
- `backend/app/services/notification_service.py`
- `backend/app/routers/notification.py`
- `backend/tests/test_notifications.py`

### API 建议

- `GET /notifications`
  - 查询当前用户通知。
  - 参数：`is_read?: bool`、`type?: str`、`skip >= 0`、`limit <= 100`。
  - 返回按 `created_at desc` 排序的通知列表。
- `GET /notifications/unread-count`
  - 返回 `{ "count": number }`。
- `POST /notifications/{notification_id}/mark-read`
  - 只能标记自己的通知。
- `POST /notifications/mark-all-read`
  - 标记当前用户通知为已读，可选按类型过滤。

### Schema 建议

通知读模型字段：

- `id`
- `type`
- `title`
- `content`
- `entity_type`
- `entity_id`
- `entity_code`
- `link`
- `is_read`
- `created_at`
- `read_at`

`link` 可后端计算，也可前端根据 `entity_type/entity_id` 计算；首版建议后端返回 `link`，避免多端重复规则。

### 权限规则

- 所有已登录用户可读取自己的通知。
- 用户只能标记自己的通知。
- 管理员也不默认读取他人通知，避免通知内容泄露。
- 创建通知不暴露通用外部 API，业务服务内部调用 `notification_service.create()`。

### 兼容处理

- `/dashboard/notifications` 不应继续返回空数组，应复用 `NotificationService.list_user_notifications(limit=5)`。
- `/dashboard/notifications/mark-read` 可保留兼容，但新前端优先使用 `/notifications/*`。

## N2：统一通知写入入口

### Service 建议

`NotificationService.create()` 参数：

- `user_id`
- `notification_type`
- `title`
- `content`
- `entity_type`
- `entity_id`
- `entity_code`
- `dedupe_key` 或业务层去重参数（首版可选）

### 首批迁移写入点

- `backend/app/services/feishu_org_sync_service.py`
  - 当前直接 `Notification(...)` 写库。
  - 改为 `NotificationService.create()`。
- 后续模块禁止散点直接写 `Notification`，除非测试 fixture。

## N3：前端通知中心

### 建议新增文件

- `frontend/src/hooks/useNotifications.ts`
- `frontend/src/pages/NotificationCenterPage.tsx`
- 可选：`frontend/src/components/notifications/NotificationBell.tsx`

### 页面能力

- 通知列表，支持全部/未读筛选。
- 未读数量展示。
- 单条标记已读。
- 全部标记已读。
- 点击通知跳转关联业务对象。
- 加载态、空状态、错误提示。

### 入口建议

- 顶部 Header 增加通知按钮或 Badge，点击进入 `/notifications`。
- 侧边栏可放在“系统管理”或“业务管理”中；首版建议顶部入口优先，减少菜单膨胀。

### 跳转映射首版

- `entity_type="work_report"` → `/work-reports/{entity_id}`
- `entity_type="handover_request"` → `/handovers/{entity_id}`
- `entity_type="work_order"` → `/work-orders/{entity_id}`
- 未知类型：点击只标记已读，不跳转。

## N4：日报/周报评论通知 P5.3

### 建议新增后端文件

- `backend/app/models/work_report_comment.py`
- `backend/app/schemas/work_report_comment.py`
- 可并入 `backend/app/routers/work_report.py`，新增评论子资源。
- `backend/tests/test_work_report_comments.py`

### API 建议

- `GET /work-reports/{report_id}/comments`
- `POST /work-reports/{report_id}/comments`

### 评论规则

- 能读取报告的人可查看评论。
- 能读取报告的人可发表评论。
- 评论内容必填，长度上限建议 `1..1000`。
- 评论创建后通知报告 owner。
- 如果评论人不是报告 owner，通知报告 owner。
- 如果报告 owner 评论自己的报告，首版不自发通知。
- 可选通知部门负责人；首版建议只通知报告 owner，避免团队范围误发。

### 前端能力

- 在 `WorkReportDetailPage` 增加评论区。
- 评论列表按时间升序或降序展示。
- 提交评论后刷新评论和通知。

## N5：验收标准

### 后端测试

```bash
cd backend && APP_ENV=test ./venv/bin/python -m pytest tests/test_notifications.py tests/test_work_report_comments.py -q
cd backend && APP_ENV=test ./venv/bin/python -m pytest tests/test_dashboard.py tests/test_work_reports.py -q
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

- 当前用户能看到自己的站内通知。
- 未读数准确。
- 单条和全部已读后状态刷新。
- 通知不会泄露给非接收人。
- 离职交接通知能在通知中心展示并跳转到交接详情。
- 工作报告被评论后，报告 owner 收到通知并能跳转到报告详情。
- Dashboard 旧通知接口不再固定返回空数组。

## 风险与约束

- 当前存在 `UserNotificationRead` 旧表，首版不要删除，避免破坏历史部署。
- `Notification.is_read` 是按通知记录自身记录已读状态，因此每个接收人应有独立 notification 行。
- 通知创建失败不应影响主业务事务；第一版可在业务事务内创建，但 service 需要明确异常处理策略。
- 飞书外发与定时提醒依赖真实租户和调度方案，本阶段不纳入。

## 施工派发建议

已按用户要求交给 `agent3` 施工完整阶段：

1. 后端 N0/N1/N2：通知 schema/service/router/tests，并让 dashboard 旧通知接口复用 service。
2. 前端 N3：通知中心页面、顶部入口、业务跳转。
3. 后端/前端 N4：工作报告评论、评论通知。
4. N5：验收与文档状态回写。

每段完成后都必须更新本计划状态和验证记录。

## 派发记录

- 2026-05-15：agent2 按用户要求将 N0-N5 全阶段施工派发给 `agent3`，目标是完成通知中心最小闭环全部任务。

## 验收结果

### agent2 复核记录

- 后端通知/评论专项测试通过。
- 后端 dashboard/work reports 回归测试通过。
- 后端全量测试通过。
- 前端测试和构建通过。
- `git diff --check` 通过。
- 已发现并修复 Alembic 双 head：`work_report_comments_20260515` 已接到 `feishu_handover_fk_20260514` 后。
- 当前 `alembic heads`：`work_report_comments_20260515 (head)`，唯一 head。

### 后端测试

```
$ pytest tests/test_notifications.py tests/test_work_report_comments.py -v
20 passed (14 notifications + 6 work report comments)

$ pytest backend/tests/ -v
279 passed (全量后端测试)
```

### 前端

- TypeScript 类型检查：无错误
- 生产构建：成功 (`npm run build`)

### 全局门禁

```
$ git diff --check
无尾部空白
```

### 功能完成情况

- [x] N0：Notification schema/service/router 设计完成，dashboard 旧接口返回真实数据
- [x] N1：`GET /notifications`、`GET /notifications/unread-count`、`POST /notifications/{id}/mark-read`、`POST /notifications/mark-all-read` 全部可用
- [x] N2：`NotificationService.create()` 统一写入，feishu_org_sync_service 已迁移
- [x] N3：`NotificationCenterPage` 全屏页、`useNotifications` hooks、Dashboard header 铃铛 Badge、侧边栏菜单入口
- [x] N4：`WorkReportComment` 模型、评论 CRUD API、`WorkReportDetailPage` 评论区、评论创建时通知报告 owner
- [x] N5：测试通过、构建成功、本文档状态回写

### 迁移收口

- `backend/alembic/versions/work_report_comments_20260515.py`
  - `down_revision` 从 `work_reports_20260513` 调整为 `feishu_handover_fk_20260514`。
  - 原因：该迁移属于本轮新增未提交文件，直接接到当前主线 head 比新增 merge migration 更小、更清晰。
  - 验证：`cd backend && ./venv/bin/alembic heads` 仅返回 `work_report_comments_20260515 (head)`。

### 新增文件清单

| 文件 | 用途 |
|------|------|
| `backend/app/schemas/notification.py` | 通知读写 schema |
| `backend/app/services/notification_service.py` | 通知统一 service |
| `backend/app/routers/notification.py` | 通知中心 API 路由 |
| `backend/app/models/work_report_comment.py` | 工作报告评论模型 |
| `backend/alembic/versions/work_report_comments_20260515.py` | 评论表迁移 |
| `frontend/src/hooks/useNotifications.ts` | 通知查询 hooks |
| `frontend/src/pages/NotificationCenterPage.tsx` | 通知中心全屏页 |

### 修改文件清单

| 文件 | 变更 |
|------|------|
| `backend/app/main.py` | 注册 notification_router |
| `backend/app/routers/dashboard.py` | dashboard 通知接口复用 NotificationService |
| `backend/app/routers/work_report.py` | 新增评论子资源 API |
| `backend/app/models/__init__.py` | 导入 WorkReportComment |
| `backend/app/schemas/work_report.py` | 新增评论 schema |
| `backend/app/services/feishu_org_sync_service.py` | 迁移到 NotificationService.create() |
| `frontend/src/App.tsx` | 新增 /notifications 路由和 WorkReportDetailPage |
| `frontend/src/pages/Dashboard.tsx` | Header 铃铛 Badge + 侧边栏通知菜单 |
| `frontend/src/pages/WorkReportDetailPage.tsx` | 新增评论区 UI |
