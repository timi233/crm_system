# CRM-派工系统集成规范

## 文档概述

本规范定义了CRM系统与IT服务派工系统之间的API集成方案，包括数据映射、认证机制、错误处理、重试策略和回调机制。

---

## 1. 系统架构概览

### 1.1 CRM系统 (FastAPI + PostgreSQL)
- **位置**: `/backend` 目录
- **数据源**: Leads（线索）、Opportunities（商机）、Projects（项目）、Customers（客户）
- **认证**: JWT + 飞书OAuth
- **API**: RESTful，支持Swagger UI (`/docs`)

### 1.2 派工系统 (Express + SQLite)
- **位置**: `/new_task_mgt` 目录
- **核心**: Work Orders（工单）
- **认证**: JWT + 飞书OAuth
- **API**: RESTful (`/api/workorders`)

---

## 2. API端点清单

### 2.1 派工系统核心API

| 端点 | 方法 | 说明 | 认证 |
|------|------|------|------|
| `/api/workorders` | POST | 创建工单 | JWT必需 |
| `/api/workorders` | GET | 获取工单列表 | JWT必需 |
| `/api/workorders/:id` | GET | 获取工单详情 | JWT必需 |
| `/api/workorders/:id/accept` | POST | 接单 | JWT必需 |
| `/api/workorders/:id/start` | POST | 开始服务 | JWT必需 |
| `/api/workorders/:id/complete` | POST | 完成服务 | JWT必需 |
| `/api/workorders/:id/cancel` | POST | 取消工单 | JWT必需 |
| `/api/workorders/:id/evaluate` | POST | 提交评价 | JWT必需 |
| `/auth/login` | POST | 用户登录 | 无 |
| `/auth/refresh` | POST | 刷新Token | JWT必需 |

### 2.2 CRM系统关键数据源

| 数据源 | 说明 | 关键字段 |
|--------|------|---------|
| Leads | 线索管理 | `customer_name`, `contact_info`, `budget` |
| Opportunities | 商机跟进 | `terminal_customer_id`, `expected_contract_amount`, `sales_owner_id` |
| Projects | 项目管理 | `project_code`, `customer_info`, `status` |
| Customers | 客户档案 | `customer_code`, `customer_name`, `main_contact`, `phone` |

---

## 3. 数据字段映射

### 3.1 CRM Customer → 派工系统 WorkOrder 映射

| CRM字段 (Customer) | 派工字段 (WorkOrder) | 转换规则 |
|--------------------|---------------------|---------|
| `customer_name` | `customerName` | 直接映射（必填） |
| `main_contact` | `customerContact` | 直接映射（可选） |
| `phone` | `customerPhone` | 直接映射（可选） |
| `channel_id` → Channel.name | `channelName` | 通过关联查询Channel表 |
| `channel.contact_person` | `channelContact` | Channel关联字段 |
| `channel.phone` | `channelPhone` | Channel关联字段 |

### 3.2 CRM Opportunity → 派工系统 WorkOrder 映射

| CRM字段 (Opportunity) | 派工字段 (WorkOrder) | 转换规则 |
|----------------------|---------------------|---------|
| `terminal_customer_id` → Customer.customer_name | `customerName` | 关联查询Customer表（必填） |
| `terminal_customer.main_contact` | `customerContact` | Customer关联字段（可选） |
| `terminal_customer.phone` | `customerPhone` | Customer关联字段（可选） |
| `channel_id` → Channel.name | `channelName` | 若存在渠道，设置`hasChannel=true` |
| `sales_owner_id` | `relatedSalesId` | 映射到销售负责人的飞书ID |
| `opportunity_name` | `description` | 商机名称作为工单描述前缀 |
| `expected_contract_amount` | → 优先级判断 | 大额商机（>50万）→ `URGENT` |

### 3.3 CRM Project → 派工系统 WorkOrder 映射

| CRM字段 (Project) | 派工字段 (WorkOrder) | 转换规则 |
|------------------|---------------------|---------|
| `terminal_customer_id` → Customer.customer_name | `customerName` | 关联查询（必填） |
| `project_code` | `description` | 项目编号 + 项目名称作为描述 |
| `winning_date` | `estimatedStartDate` | 预计开始日期 |
| `acceptance_date` | `estimatedEndDate` | 预计结束日期 |

### 3.4 工单类型判断规则

根据CRM数据源自动判断工单类型：

```javascript
// 工单类型映射规则
function determineOrderType(source, channelExists) {
  if (source === 'opportunity') {
    // 商机转化工单
    return channelExists ? 'CF' : 'CO'; // 有渠道→外勤，无渠道→内勤
  } else if (source === 'project') {
    // 项目实施工单
    return 'CF'; // 默认外勤
  } else if (source === 'lead') {
    // 线索跟进工单
    return 'CO'; // 默认内勤
  }
}
```

---

## 4. 认证机制

### 4.1 双系统认证架构

两个系统均使用JWT + 飞书OAuth双重认证：

```
┌─────────────┐           ┌─────────────┐
│ CRM系统     │           │ 派工系统    │
│ (FastAPI)   │           │ (Express)   │
└─────────────┘           └─────────────┘
      │                          │
      │    飞书OAuth统一认证      │
      └──────────────────────────┘
                 │
         ┌───────┴───────┐
         │   飞书平台    │
         │   OAuth2.0    │
         └───────────────┘
```

### 4.2 JWT Token结构

**CRM系统JWT Payload**:
```json
{
  "user_id": 123,
  "role": "sales",
  "feishu_id": "ou_xxxx",
  "exp": 1712345678
}
```

**派工系统JWT Payload**:
```json
{
  "userId": "cuid_xxxx",
  "feishuId": "ou_xxxx",
  "functionalRole": "SALES",
  "responsibilityRole": "ADMIN",
  "exp": 1712345678
}
```

### 4.3 跨系统认证流程

**方案A: 共享飞书OAuth Token**（推荐）

```
步骤1: CRM系统通过飞书OAuth获取用户Token
步骤2: 提取飞书用户ID (feishuId)
步骤3: 查询派工系统用户表，匹配feishuId
步骤4: 获取派工系统JWT Token用于API调用
步骤5: 缓存派工系统Token，设置过期时间同步
```

**方案B: 系统间Token交换**（备选）

```typescript
// CRM系统调用派工系统认证API
const response = await axios.post('派工系统URL/auth/feishu/login', {
  code: feishu_auth_code
});
const dispatchToken = response.data.token;
```

### 4.4 Token刷新机制

- **同步刷新**: CRM系统检测派工系统Token过期，自动刷新
- **自动重试**: API调用收到401响应时，先刷新Token再重试
- **缓存策略**: Redis缓存派工系统Token，key格式: `dispatch_token:{feishuId}`

---

## 5. 错误处理策略

### 5.1 HTTP状态码映射

| HTTP状态码 | 错误类型 | 处理策略 |
|-----------|---------|---------|
| 400 | 参数验证失败 | 记录日志，返回错误详情，不重试 |
| 401 | Token失效/过期 | 自动刷新Token，最多重试1次 |
| 403 | 权限不足 | 记录审计日志，通知管理员 |
| 404 | 工单不存在 | 标记CRM记录状态为"派工失败" |
| 409 | 工单冲突（重复） | 检查是否已创建，更新关联关系 |
| 429 | 请求频率超限 | 等待Rate Limit冷却时间，指数退避重试 |
| 500 | 派工系统内部错误 | 重试3次，失败后记录并通知 |
| 503 | 服务不可用 | 等待5分钟后重试 |
| Network Error | 网络故障 | 重试3次，失败后降级处理 |

### 5.2 错误响应结构

**派工系统错误响应格式**:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "缺少必填字段: technicianIds",
    "details": [
      {
        "field": "technicianIds",
        "reason": "required"
      }
    ]
  }
}
```

**CRM系统错误处理**:
```python
class DispatchAPIError(Exception):
    """派工系统API调用异常"""
    def __init__(self, status_code, error_code, message, retry_after=None):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.retry_after = retry_after  # Rate Limit冷却时间
```

### 5.3 降级处理方案

当派工系统不可用时，CRM系统降级策略：

1. **本地记录**: 创建"待派工"状态记录，存储在CRM数据库
2. **异步队列**: 推送到Redis队列，后台定时重试
3. **人工介入**: 发送飞书通知给管理员，人工处理
4. **批量补偿**: 派工系统恢复后，批量同步待派工记录

---

## 6. Rate Limit与重试机制

### 6.1 Rate Limit限制

**派工系统限制**（建议配置）:
- 创建工单: 10次/分钟/IP
- 查询工单: 30次/分钟/IP
- 其他操作: 20次/分钟/IP

**CRM系统应对策略**:
```python
# 使用Rate Limiter
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=8, period=60)  # 略低于限制，留余量
def create_work_order(data):
    return axios.post(DISPATCH_API + '/api/workorders', data)
```

### 6.2 重试机制

**指数退避重试策略**:
```python
import asyncio
from datetime import datetime

async def retry_with_backoff(func, max_retries=3):
    """指数退避重试"""
    for attempt in range(max_retries):
        try:
            return await func()
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            wait_time = min(2 ** attempt, 60)  # 最大60秒
            await asyncio.sleep(wait_time)
        except NetworkError as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(5)  # 网络5秒后重试
```

### 6.3 幂等性保证

**工单创建幂等性**:
```python
# CRM端生成唯一external_id
external_id = f"CRM-{opportunity_code}-{timestamp}"

# 调用派工API时携带
payload = {
    ...,
    "metadata": {
        "external_id": external_id,
        "source_system": "CRM",
        "source_type": "opportunity",
        "source_id": opportunity_id
    }
}

# 派工系统检查external_id是否已存在
# 若存在，返回409 Conflict + 已有工单ID
# CRM系统更新关联关系，不重复创建
```

---

## 7. Webhook回调机制

### 7.1 当前状况

派工系统**暂无**Webhook回调机制，状态变更通过：
- 飞书消息通知（内部）
- 前端轮询查询（客户端）

### 7.2 Webhook需求分析

**建议实现Webhook的场景**:

| 触发事件 | Webhook内容 | CRM处理 |
|---------|------------|---------|
| 工单完成 | `work_order_id`, `completed_at`, `service_summary` | 更新项目状态，记录服务日志 |
| 工单取消 | `work_order_id`, `cancel_reason` | 标记CRM记录状态 |
| 客户评价 | `work_order_id`, `rating`, `feedback` | 记录客户满意度，用于分析 |
| 技术员接单 | `work_order_id`, `technician_id` | 更新派工负责人信息 |

### 7.3 Webhook设计方案

**派工系统端**:
```typescript
// 新增Webhook配置表
model WebhookSubscription {
  id          String   @id @default(cuid())
  system      String   // CRM, ERP, etc.
  url         String   // Webhook接收URL
  secret      String   // 签名密钥
  events      String[] // 监听事件列表
  active      Boolean  @default(true)
  createdAt   DateTime @default(now())
}

// Webhook发送服务
async function sendWebhook(event: string, data: any) {
  const payload = JSON.stringify({ event, data, timestamp: Date.now() });
  const signature = hmac_sha256(payload, webhook.secret);
  
  await axios.post(webhook.url, payload, {
    headers: {
      'X-Webhook-Signature': signature,
      'X-Webhook-Event': event
    }
  });
}
```

**CRM系统端**:
```python
# Webhook接收端点
@app.post("/webhooks/dispatch")
async def receive_dispatch_webhook(
    event: str,
    data: dict,
    signature: str = Header(alias="X-Webhook-Signature")
):
    # 验证签名
    verify_signature(data, signature)
    
    # 处理事件
    if event == "work_order.completed":
        update_project_status(data['work_order_id'])
        record_service_log(data)
    
    return {"status": "acknowledged"}
```

### 7.4 备选方案：定时轮询

若暂不实现Webhook，可采用定时轮询：

```python
# 每15分钟轮询派工系统，检查工单状态
@app.task(schedule='*/15 * * * *')
async def poll_work_order_status():
    # 查询CRM中所有"已派工"状态的记录
    dispatched = await get_dispatched_records()
    
    for record in dispatched:
        # 调用派工API查询状态
        status = await get_work_order_status(record.dispatch_id)
        
        if status == 'DONE':
            await update_crm_status(record.id, 'service_completed')
```

---

## 8. 实施步骤

### 8.1 Phase 1: 基础集成（1-2周）

1. 实现跨系统认证（飞书OAuth Token共享）
2. 开发CRM → 派工数据转换服务
3. 实现工单创建API调用（含错误处理）
4. 添加Rate Limit和基础重试机制

### 8.2 Phase 2: 稳定性增强（1周）

1. 完善幂等性机制（external_id）
2. 实现降级处理和异步队列
3. 添加详细日志和监控
4. 开发批量同步工具（故障恢复）

### 8.3 Phase 3: 双向同步（2周）

1. 派工系统开发Webhook机制
2. CRM系统实现Webhook接收端点
3. 实现定时轮询作为备选方案
4. 完整测试和性能优化

---

## 9. 测试清单

### 9.1 功能测试

- ✅ 正常场景：创建工单成功
- ✅ 边界场景：缺少可选字段
- ✅ 异常场景：必填字段缺失
- ✅ 认证场景：Token过期刷新
- ✅ 权限场景：无权限用户尝试创建
- ✅ 重复场景：相同数据重复创建（幂等性）
- ✅ 大数据场景：批量创建工单

### 9.2 性能测试

- Rate Limit压力测试
- 并发创建测试（10并发）
- 长时间运行稳定性测试

### 9.3 故障恢复测试

- 派工系统宕机恢复后同步
- 网络中断后自动重试
- Token失效后自动刷新

---

## 10. 监控与日志

### 10.1 关键指标

| 指标 | 说明 | 阈值 |
|------|------|------|
| `dispatch_api_success_rate` | API成功率 | >95% |
| `dispatch_api_latency` | API响应时间 | <500ms |
| `dispatch_token_refresh_count` | Token刷新次数 | <10次/小时 |
| `dispatch_retry_count` | 重试次数 | <50次/小时 |
| `dispatch_queue_length` | 待派工队列长度 | <100 |

### 10.2 日志规范

```json
{
  "timestamp": "2026-04-10T10:30:00Z",
  "level": "INFO",
  "event": "dispatch_work_order_created",
  "crm_record_id": "OPP-20260410-001",
  "dispatch_work_order_id": "CF-20260410-001",
  "latency_ms": 350,
  "user_id": "ou_xxxx",
  "retry_count": 0
}
```

---

## 11. 安全考虑

### 11.1 数据安全

- 传输加密：HTTPS/TLS 1.2+
- Token存储：Redis加密存储
- 日志脱敏：客户联系方式部分隐藏
- 审计日志：记录所有API调用

### 11.2 权限控制

- CRM系统：仅销售角色可创建工单
- 派工系统：验证创建者角色权限
- 双重校验：两边系统均校验权限

---

## 12. 附录

### 12.1 完整API调用示例

```python
import requests
import time

class DispatchIntegration:
    def __init__(self, config):
        self.base_url = config.DISPATCH_API_URL
        self.token_cache = RedisTokenCache(config.REDIS_URL)
    
    async def create_work_order_from_opportunity(self, opportunity: Opportunity):
        """从商机创建派工工单"""
        
        # 1. 获取派工系统Token
        token = await self.get_dispatch_token(opportunity.sales_owner.feishu_id)
        
        # 2. 构造工单数据
        payload = self.transform_opportunity_to_work_order(opportunity)
        
        # 3. 调用API（含重试）
        try:
            response = await self.retry_api_call(
                'POST',
                '/api/workorders',
                payload,
                token
            )
            
            # 4. 记录关联关系
            await self.update_opportunity_dispatch(
                opportunity.id,
                response['id'],
                response['orderNo']
            )
            
            return response
            
        except DispatchAPIError as e:
            # 5. 错误处理
            await self.handle_error(opportunity, e)
            raise
    
    def transform_opportunity_to_work_order(self, opp: Opportunity) -> dict:
        """数据转换"""
        customer = opp.terminal_customer
        channel = opp.channel
        
        return {
            "orderType": self.determine_order_type(opp, channel),
            "customerName": customer.customer_name,
            "customerContact": customer.main_contact,
            "customerPhone": customer.phone,
            "hasChannel": bool(channel),
            "channelName": channel.name if channel else None,
            "channelContact": channel.contact_person if channel else None,
            "channelPhone": channel.phone if channel else None,
            "workType": "COMMUNICATION",  # 商机跟进默认沟通类
            "priority": "URGENT" if opp.expected_contract_amount > 500000 else "NORMAL",
            "description": f"{opp.opportunity_name} - {opp.opportunity_stage}",
            "technicianIds": self.get_available_technicians(),
            "metadata": {
                "external_id": f"CRM-{opp.opportunity_code}-{int(time.time())}",
                "source_system": "CRM",
                "source_type": "opportunity",
                "source_id": opp.id
            }
        }
```

### 12.2 派工系统API完整字段

**POST /api/workorders 必填字段**:
```json
{
  "customerName": "string (必填)",
  "description": "string (必填)",
  "technicianIds": ["string"] (必填，至少1个技术员ID)
}
```

**可选字段**:
```json
{
  "orderType": "CF|CO|MF|MO",
  "customerContact": "string",
  "customerPhone": "string",
  "hasChannel": "boolean",
  "channelName": "string",
  "channelContact": "string",
  "channelPhone": "string",
  "manufacturerContact": "string (厂家工单必填)",
  "workType": "COMMUNICATION|TEST|DELIVERY|ISSUE|INSPECTION|TRAINING|OTHER",
  "priority": "NORMAL|URGENT|VERY_URGENT",
  "estimatedStartDate": "ISO8601 datetime",
  "estimatedStartPeriod": "AM|PM",
  "estimatedEndDate": "ISO8601 datetime",
  "estimatedEndPeriod": "AM|PM"
}
```

### 12.3 CRM数据模型关键字段

**Customer (terminal_customers)**:
- `customer_code`: PYCRM-CUST-YYYYMMDD-SEQ
- `customer_name`: 客户公司名称
- `main_contact`: 联系人
- `phone`: 电话
- `customer_industry`: 行业
- `customer_region`: 地区
- `customer_owner_id`: 销售负责人ID
- `channel_id`: 渠道ID（可选）

**Opportunity (opportunities)**:
- `opportunity_code`: PYCRM-OPP-YYYYMMDD-SEQ
- `opportunity_name`: 商机名称
- `terminal_customer_id`: 终端客户ID
- `opportunity_stage`: 商机阶段
- `expected_contract_amount`: 预计合同金额
- `sales_owner_id`: 销售负责人ID
- `channel_id`: 渠道ID（可选）

**Project (projects)**:
- `project_code`: PYCRM-PRJ-YYYYMMDD-SEQ
- `terminal_customer_id`: 终端客户ID
- `winning_date`: 中标日期
- `acceptance_date`: 验收日期

---

## 13. 变更历史

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| 1.0 | 2026-04-10 | 初版发布，定义基础集成规范 |

---

**文档维护**: 请定期更新本规范，确保与系统实际实现保持同步。