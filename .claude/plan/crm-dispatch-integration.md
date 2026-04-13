# CRM-派工系统集成架构规划

## 项目概述

设计 CRM 系统与 IT 服务派工系统(new_task_mgt)的集成架构，实现从 CRM 发起派工申请的端到端流程。

## 系统现状

### CRM系统
- **后端**: FastAPI + Python, PostgreSQL
- **前端**: React 18 + TypeScript, Redux Toolkit, Ant Design
- **认证**: JWT (HS256, 30min) + 飞书 OAuth
- **核心实体**: Lead → Opportunity → Project → Contract
- **角色**: admin/sales/business/finance

### 派工系统
- **后端**: Express + TypeScript, Prisma ORM, SQLite
- **前端**: Vue 3 + TypeScript, Pinia, Vant 4
- **认证**: JWT (可配置过期) + 飞书 OAuth
- **核心实体**: WorkOrder (CF/CO/MF/MO)
- **权限**: 双重权限模型 (functionalRole + responsibilityRole)

## 技术方案

### 1. 认证架构

```
飞书 OAuth (统一身份源)
        │
        ▼
┌─────────────────┐     ┌─────────────────┐
│   CRM 系统      │     │   派工系统       │
│  JWT (30min)    │     │  JWT (7d)        │
│  feishu_id      │◄───►│  feishuId        │
└─────────────────┘     └─────────────────┘
        │                       │
        │   服务间 API Key      │
        └───────────────────────┘
```

**关键决策**:
- 不共享 JWT，各自维护独立会话
- 用 `feishu_id` 作为跨系统用户关联键
- CRM 后端持有派工系统的 `integration_token`

### 2. 数据流架构

```
CRM Entity (Lead/Opportunity/Project)
        │
        │ 派工申请
        ▼
DispatchRequest (集成映射表)
        │
        │ POST /integration/workorders
        ▼
WorkOrder (派工系统)
        │
        │ 状态回调
        ▼
状态同步到 CRM
```

### 3. 实体-工单类型映射

| CRM 实体 | 可创建工单类型 | 业务场景 |
|---------|--------------|---------|
| Lead | CF, CO | 售前支持、现场勘查 |
| Opportunity | CF, CO, MF, MO | 方案演示、测试、厂商协调 |
| Project | CF, CO | 交付、巡检、故障处理 |

### 4. 字段映射表

| CRM 字段 | 派工工单字段 |
|---------|-------------|
| terminal_customer.customer_name | customerName |
| main_contact | customerContact |
| phone | customerPhone |
| channel.company_name | channelName |
| sales_owner.feishu_id | submitterId |
| dispatch_type | orderType |
| service_type | workType |
| urgency_level | priority |
| service_requirements | description |

## 实施步骤

### 阶段一：基础集成（1-2周）

1. **派工系统：创建集成 API**
   - 文件: `new_task_mgt/server/src/routes/integration.ts`
   - 接口: `POST /api/integration/workorders`
   - 鉴权: `X-Integration-Token`
   - 幂等: `request_id`

2. **CRM：创建集成映射表**
   - 文件: `backend/app/models/dispatch_request.py`
   - 表: `dispatch_requests`
   - 字段: source_entity_type, source_entity_id, dispatch_request_no, work_order_id, sync_status

3. **CRM：后端集成服务**
   - 文件: `backend/app/services/dispatch_integration.py`
   - 方法: `create_work_order_from_entity()`

4. **派工系统：工程师列表 API**
   - 接口: `GET /api/integration/technicians`

### 阶段二：前端集成（1周）

5. **CRM：增强派工申请表单**
   - 文件: `frontend/src/components/modals/DispatchRequestModal.tsx`
   - 功能: 工程师选择器、表单验证

6. **CRM：实体详情页添加入口**
   - 文件: `CustomerFullViewPage.tsx`, `OpportunityFullViewPage.tsx`, `ProjectFullViewPage.tsx`
   - 功能: "派工申请"按钮

7. **CRM：工单状态展示**
   - 文件: `frontend/src/components/dispatch/WorkOrderCard.tsx`
   - 功能: 工单列表、状态标签

### 阶段三：状态回流（1周）

8. **派工系统：状态回调 API**
   - 接口: `POST /api/integration/workorders/:id/status-callback`

9. **CRM：接收状态回调**
   - 接口: `POST /api/dispatch/callback`

10. **端到端测试**

## 关键文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `new_task_mgt/server/src/routes/integration.ts` | 新建 | 集成 API |
| `new_task_mgt/server/src/middlewares/integrationAuth.ts` | 新建 | 服务间鉴权 |
| `backend/app/models/dispatch_request.py` | 新建 | 映射模型 |
| `backend/app/services/dispatch_integration.py` | 新建 | 集成服务 |
| `backend/app/api/dispatch.py` | 新建 | 派工 API |
| `frontend/src/components/modals/DispatchRequestModal.tsx` | 修改 | 表单增强 |
| `frontend/src/hooks/useDispatch.ts` | 新建 | 派工 hooks |
| `frontend/src/components/dispatch/WorkOrderCard.tsx` | 新建 | 工单卡片 |

## 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| 身份映射失败 | 预同步用户或引导首次登录 |
| 派工系统不可用 | 保留记录定时重试 |
| 角色权限不一致 | 角色映射到 functionalRole |
| SQLite 并发瓶颈 | 中期升级 PostgreSQL |

## 技术债

1. 派工系统从 SQLite 迁移到 PostgreSQL
2. 派工系统权限从旧 `role` 迁移到双重权限模型
3. Token 存储从 localStorage 收敛到更安全方案

## SESSION_ID

- CODEX_SESSION: 019d755d-eb8a-7a92-a760-001a995996bb