# CRM销管系统架构与集成设计文档

## 1. 系统架构概述

### 1.1 整体架构
普悦销管系统采用现代化的前后端分离架构，具备高可扩展性和维护性。

```
┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │
│   (React)       │◄──►│   (FastAPI)     │
└─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   PostgreSQL    │
                    │   Database      │
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   Redis         │
                    │   (Optional)    │
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   Feishu OAuth  │
                    │   Integration   │
                    └─────────────────┘
```

### 1.2 技术栈详情

#### 前端技术栈
- **框架**: React 18 + TypeScript
- **UI组件库**: Ant Design v5
- **状态管理**: React Query + Context API  
- **路由**: React Router v6
- **构建工具**: Vite
- **HTTP客户端**: Axios

#### 后端技术栈
- **框架**: FastAPI (Python)
- **ORM**: SQLAlchemy 2.0 (Async)
- **数据库**: PostgreSQL 12+
- **缓存**: Redis (可选)
- **认证**: JWT + OAuth2 (飞书)
- **API文档**: OpenAPI/Swagger

#### 部署架构
- **容器化**: Docker Compose (生产环境)
- **本地开发**: 原生启动 (开发环境)
- **监控**: Prometheus + Grafana (规划中)

## 2. 数据模型设计

### 2.1 核心实体关系图
```
Users ──┬── Leads
        ├── Opportunities  
        ├── Projects
        └── TerminalCustomers ──┬── Leads
                                ├── Opportunities
                                ├── Projects  
                                └── Contracts ── PaymentPlans
                                              └── ContractProducts

SalesTargets ── Users
AlertRules ── System
OperationLogs ── Users
FollowUps ──┬── Leads
           ├── Opportunities  
           └── Projects
```

### 2.2 关键表结构

#### users 表
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR UNIQUE,
    hashed_password VARCHAR,
    is_active BOOLEAN DEFAULT true,
    role VARCHAR NOT NULL,  -- admin/sales/finance/business
    name VARCHAR,
    feishu_id VARCHAR UNIQUE,
    phone VARCHAR,
    avatar TEXT,
    sales_leader_id INTEGER REFERENCES users(id),
    sales_region VARCHAR,
    sales_product_line VARCHAR
);
```

#### leads 表
```sql
CREATE TABLE leads (
    id SERIAL PRIMARY KEY,
    lead_code VARCHAR(25) UNIQUE NOT NULL,
    lead_name VARCHAR(255) NOT NULL,
    terminal_customer_id INTEGER NOT NULL REFERENCES terminal_customers(id),
    lead_stage VARCHAR(30) NOT NULL DEFAULT '初步接触',
    lead_source VARCHAR(50),
    contact_person VARCHAR(100),
    contact_phone VARCHAR(20),
    estimated_budget NUMERIC(15,2),
    has_confirmed_requirement BOOLEAN DEFAULT false,
    has_confirmed_budget BOOLEAN DEFAULT false,
    converted_to_opportunity BOOLEAN DEFAULT false,
    opportunity_id INTEGER REFERENCES opportunities(id),
    sales_owner_id INTEGER NOT NULL REFERENCES users(id),
    notes TEXT,
    created_at DATE,
    updated_at DATE
);
```

#### contracts 表
```sql
CREATE TABLE contracts (
    id SERIAL PRIMARY KEY,
    contract_code VARCHAR(30) UNIQUE NOT NULL,
    contract_name VARCHAR(255) NOT NULL,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    contract_direction VARCHAR(20) NOT NULL DEFAULT 'Downstream', -- Downstream/Upstream
    contract_status VARCHAR(20) NOT NULL DEFAULT 'draft',
    terminal_customer_id INTEGER REFERENCES terminal_customers(id),
    channel_id INTEGER REFERENCES channels(id),
    contract_amount NUMERIC(15,2) NOT NULL DEFAULT 0,
    signing_date DATE,
    effective_date DATE,
    expiry_date DATE,
    contract_file_url TEXT,
    notes TEXT,
    created_at DATE,
    updated_at DATE
);
```

## 3. API接口设计

### 3.1 认证接口
| 端点 | 方法 | 描述 |
|------|------|------|
| `/auth/login` | POST | 邮箱密码登录 |
| `/auth/feishu/callback` | GET | 飞书OAuth回调 |
| `/auth/logout` | POST | 用户登出 |

### 3.2 核心业务接口
| 模块 | 端点 | 方法 | 描述 |
|------|------|------|------|
| **用户管理** | `/users` | GET/POST/PUT/DELETE | 用户CRUD |
| **线索管理** | `/leads` | GET/POST/PUT/DELETE | 线索CRUD |
| **商机管理** | `/opportunities` | GET/POST/PUT/DELETE | 商机CRUD |
| **项目管理** | `/projects` | GET/POST/PUT/DELETE | 项目CRUD |
| **合同管理** | `/contracts` | GET/POST/PUT/DELETE | 合同CRUD |
| **客户管理** | `/terminal-customers` | GET/POST/PUT/DELETE | 客户CRUD |

### 3.3 仪表板接口
| 端点 | 方法 | 描述 |
|------|------|------|
| `/dashboard/summary` | GET | 仪表板摘要统计 |
| `/dashboard/notifications` | GET | 用户通知列表 |
| `/dashboard/team-rank` | GET | 团队业绩排行 |
| `/reports/performance` | GET | 业绩报表统计 |
| `/alerts` | GET | 警报中心 |

## 4. 集成设计：CRM与派工系统

### 4.1 集成需求分析
在CRM系统的以下模块添加"派工申请"入口：
- **线索详情页**: 当线索需要技术支持时
- **商机详情页**: 当商机涉及实施服务时  
- **项目详情页**: 当项目需要现场支持时

### 4.2 集成架构设计

#### 4.2.1 架构模式
采用**编排模式**(Orchestration Pattern)，CRM系统作为主控方发起派工请求。

```
┌─────────────────┐    HTTP API    ┌─────────────────┐
│   CRM System    │───────────────►│   Dispatch      │
│   (Orchestrator)│◄───────────────│   System        │
└─────────────────┘    Webhook     └─────────────────┘
```

#### 4.2.2 数据流设计
1. **用户操作**: 在CRM界面点击"派工申请"
2. **数据收集**: 收集派工所需信息（客户、服务类型、紧急程度等）
3. **API调用**: CRM后端调用派工系统集成API
4. **工单创建**: 派工系统创建工单并返回工单ID
5. **状态同步**: 通过Webhook实现双向状态同步

### 4.3 集成接口规范

#### 4.3.1 CRM → 派工系统 (API调用)
**端点**: `POST /api/integration/workorders`

**请求头**:
```http
Content-Type: application/json
Authorization: Bearer <integration_token>
X-CRM-Source-ID: <crm_entity_id>
```

**请求体**:
```json
{
  "work_type": "CF", // CF/CO/MF/MO
  "customer_info": {
    "name": "客户名称",
    "contact": "联系人",
    "phone": "联系电话",
    "address": "客户地址"
  },
  "service_details": {
    "description": "服务描述",
    "urgency": "NORMAL", // NORMAL/URGENT
    "expected_time": "2026-04-15T10:00:00Z",
    "source_entity": "lead", // lead/opportunity/project
    "source_id": "123"
  },
  "crm_context": {
    "user_feishu_id": "ou_f4f87a1bf0d3f17f3d32b3bf4abdda26",
    "crm_instance": "localhost:3002"
  }
}
```

**响应**:
```json
{
  "workorder_id": "WO-2026-0410-001",
  "status": "created",
  "assignee": null,
  "created_at": "2026-04-10T08:00:00Z"
}
```

#### 4.3.2 派工系统 → CRM (Webhook回调)
**端点**: `POST /webhooks/dispatch/status`

**请求头**:
```http
Content-Type: application/json
X-Signature: <hmac_signature>
```

**请求体**:
```json
{
  "workorder_id": "WO-2026-0410-001",
  "previous_status": "created",
  "current_status": "assigned",
  "assignee": {
    "name": "张三",
    "feishu_id": "ou_f4f87a1bf0d3f17f3d32b3bf4abdda27"
  },
  "updated_at": "2026-04-10T09:00:00Z",
  "crm_context": {
    "source_entity": "lead",
    "source_id": "123"
  }
}
```

### 4.4 身份认证与授权

#### 4.4.1 服务间认证
- **认证方式**: API Key + HMAC签名
- **密钥管理**: 环境变量存储
- **权限控制**: 基于角色的访问控制(RBAC)

#### 4.4.2 用户身份映射
- **身份锚点**: 飞书 `open_id`
- **映射表**: 
  ```sql
  CREATE TABLE user_identity_mapping (
      crm_user_id INTEGER REFERENCES users(id),
      feishu_open_id VARCHAR NOT NULL,
      dispatch_system_id VARCHAR,
      created_at TIMESTAMP DEFAULT NOW(),
      UNIQUE(crm_user_id, feishu_open_id)
  );
  ```

### 4.5 错误处理与重试机制

#### 4.5.1 错误分类
| 错误类型 | 处理策略 |
|----------|----------|
| **网络错误** | 指数退避重试 (最多3次) |
| **认证错误** | 立即失败，记录日志 |
| **业务逻辑错误** | 返回用户友好错误信息 |
| **系统内部错误** | 重试 + 降级处理 |

#### 4.5.2 降级策略
- **派工系统不可用**: 保存派工申请到CRM，定时重试
- **网络分区**: 本地缓存 + 异步同步
- **数据不一致**: 手动审核队列

### 4.6 监控与告警

#### 4.6.1 监控指标
- **API成功率**: >99.9%
- **响应时间**: <2s P95
- **错误率**: <0.1%
- **重试次数**: <5次/小时

#### 4.6.2 告警规则
- **集成失败**: 连续3次失败触发告警
- **延迟过高**: P95 > 5s 触发告警
- **数据不同步**: 差异>10分钟触发告警

## 5. 安全设计

### 5.1 认证安全
- **JWT令牌**: HS256算法，30分钟过期
- **密码存储**: bcrypt哈希，盐值随机
- **OAuth**: PKCE增强安全性

### 5.2 数据安全
- **传输加密**: HTTPS强制启用
- **敏感数据**: 数据库字段加密
- **审计日志**: 所有关键操作记录

### 5.3 接口安全
- **CORS**: 严格限制源站
- **CSRF**: JWT无状态，天然免疫
- **速率限制**: 用户级限流保护

## 6. 性能优化

### 6.1 数据库优化
- **索引策略**: 所有外键和查询字段建立索引
- **查询优化**: N+1问题通过selectinload解决
- **连接池**: 异步连接池配置合理大小

### 6.2 缓存策略
- **Redis缓存**: 高频读取数据缓存
- **CDN加速**: 静态资源CDN分发
- **内存缓存**: 应用层LRU缓存

### 6.3 前端优化
- **代码分割**: 按路由懒加载
- **虚拟滚动**: 长列表性能优化  
- **SWR**: 数据预取和缓存

## 7. 部署与运维

### 7.1 开发环境
- **本地启动**: 原生命令行启动
- **热重载**: 开发模式自动重启
- **调试工具**: React DevTools, SQLAlchemy调试

### 7.2 生产环境
- **容器化**: Docker Compose一键部署
- **负载均衡**: Nginx反向代理
- **健康检查**: 自动重启异常服务

### 7.3 监控告警
- **APM**: 应用性能监控
- **日志**: ELK日志分析
- **告警**: 企业微信/邮件告警

## 8. 扩展性设计

### 8.1 微服务演进
- **当前**: 单体架构
- **中期**: 按业务域拆分微服务
- **长期**: 事件驱动架构(EDA)

### 8.2 插件系统
- **业务插件**: 可插拔业务模块
- **集成插件**: 第三方系统集成
- **报表插件**: 自定义报表引擎

### 8.3 国际化支持
- **多语言**: i18n国际化框架
- **本地化**: 区域特定业务规则
- **时区**: 用户时区自适应

## 9. IT派工系统集成

### 9.1 集成架构

```
┌─────────────────┐         ┌─────────────────┐
│   CRM系统       │         │   派工系统      │
│   (FastAPI)     │◄───────►│   (Express)     │
└─────────────────┘         └─────────────────┘
        │                            │
        │                            │
        ▼                            ▼
┌─────────────────┐         ┌─────────────────┐
│   PostgreSQL    │         │   SQLite        │
│   crm_db        │         │   dispatch.db   │
└─────────────────┘         └─────────────────┘
        │                            │
        └────────────┬───────────────┘
                     ▼
           ┌─────────────────┐
           │   飞书OAuth     │
           │   统一认证      │
           └─────────────────┘
```

### 9.2 集成功能

#### 派工申请入口
CRM系统在线索、商机、项目模块中提供派工申请功能：

1. **线索派工**
   - 位置：线索详情页
   - 触发条件：线索未转化为商机
   - 工单类型：CO（公司内勤）

2. **商机派工**
   - 位置：商机详情页
   - 触发条件：商机未成交/未流失
   - 工单类型：CF（有渠道）或 CO（无渠道）

3. **项目派工**
   - 位置：项目详情页
   - 触发条件：任何项目状态
   - 工单类型：CF（公司外勤）

### 9.3 数据映射规则

#### 线索 → 工单映射
```python
{
    'orderType': 'CO',  # 公司内勤
    'customerName': terminal_customer.customer_name,
    'customerContact': lead.contact_person,
    'customerPhone': lead.contact_phone,
    'description': f"线索跟进 - {lead.lead_name}",
    'priority': 'NORMAL',
    'workType': 'COMMUNICATION'
}
```

#### 商机 → 工单映射
```python
{
    'orderType': 'CF' if has_channel else 'CO',
    'customerName': terminal_customer.customer_name,
    'customerContact': terminal_customer.main_contact,
    'customerPhone': terminal_customer.phone,
    'channelName': channel.company_name,
    'description': f"商机跟进 - {opportunity.opportunity_name}",
    'priority': 'URGENT' if expected_contract_amount > 500000 else 'NORMAL',
    'workType': 'COMMUNICATION'
}
```

#### 项目 → 工单映射
```python
{
    'orderType': 'CF',  # 公司外勤
    'customerName': terminal_customer.customer_name,
    'customerContact': terminal_customer.main_contact,
    'customerPhone': terminal_customer.phone,
    'description': f"项目实施 - {project.project_name}",
    'priority': 'NORMAL',
    'workType': 'DELIVERY'
}
```

### 9.4 API端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/leads/{id}/create-dispatch` | POST | 从线索创建派工 |
| `/opportunities/{id}/create-dispatch` | POST | 从商机创建派工 |
| `/projects/{id}/create-dispatch` | POST | 从项目创建派工 |

#### 请求示例
```json
{
  "dispatch_api_url": "http://localhost:3000",
  "dispatch_token": "jwt_token_from_dispatch_system"
}
```

#### 响应示例
```json
{
  "success": true,
  "message": "Dispatch work order created successfully",
  "work_order_id": "workorder_123",
  "work_order_no": "CF-20260410-001"
}
```

### 9.5 认证流程

```
1. 用户通过飞书OAuth登录CRM系统
2. CRM系统提取用户的飞书ID (feishuId)
3. 使用飞书ID查询派工系统用户表
4. 获取派工系统JWT Token
5. 使用Token调用派工系统API
```

### 9.6 错误处理

#### 错误类型
- **400 Bad Request**: 参数验证失败
- **401 Unauthorized**: Token无效或过期
- **404 Not Found**: CRM记录不存在
- **500 Internal Server Error**: 派工系统内部错误

#### 错误处理策略
1. 自动重试（网络错误、超时）
2. 用户提示（参数错误、权限不足）
3. 日志记录（所有错误详情）
4. 降级处理（派工系统不可用时）

### 9.7 实施状态

✅ **已完成**：
- 后端API集成服务实现
- 前端派工申请UI组件
- 数据映射和转换逻辑
- 错误处理和验证
- 端到端测试验证

🔄 **待实施**：
- 派工状态回调（Webhook）
- 工单状态同步显示
- 批量派工功能
- 派工历史查询

---

**文档版本**: 1.1  
**最后更新**: 2026-04-10  
**架构负责人**: Sisyphus  
**审核状态**: 已验证通过