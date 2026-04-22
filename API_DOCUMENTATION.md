# CRM 系统 API 接口文档

## 1. 概述

普悦CRM销管系统提供完整的RESTful API接口，涵盖线索、商机、客户、渠道、项目、合同等核心业务功能。系统采用JWT认证机制，支持细粒度的基于角色的访问控制（RBAC）。

### 1.1 认证方式
- **认证类型**: Bearer Token (JWT)
- **获取Token**: `POST /auth/login`
- **请求头**: `Authorization: Bearer <access_token>`

### 1.2 角色权限
| 角色 | 权限说明 |
|------|----------|
| `admin` | 系统管理员，拥有全量数据读写权限 |
| `business` | 业务管理员（准管理员），拥有全量业务数据读写权限 |
| `sales` | 销售人员，只能访问负责的数据（基于owner/渠道分配） |
| `finance` | 财务人员，具备财务专享视图和财务实体读写权限 |
| `technician` | 技术员，仅能访问被分配的工单场景和关联数据 |

### 1.3 响应格式
所有API响应遵循统一格式：
```json
{
  "success": true,
  "data": {},
  "message": "操作成功"
}
```

错误响应：
```json
{
  "detail": "错误描述"
}
```

## 2. 认证接口 (/auth)

### 2.1 用户登录
**POST /auth/login**

#### 请求参数 (application/json)
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| email | string | 是 | 用户邮箱 |
| password | string | 是 | 用户密码 |

#### 请求示例
```json
{
  "email": "admin@example.com",
  "password": "admin123"
}
```

#### 响应示例
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 2.2 飞书OAuth登录
**POST /auth/feishu/login**

#### 请求参数 (application/json)
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | 飞书授权码 |
| state | string | 是 | 随机状态值 |

#### 响应示例
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "admin@example.com",
    "name": "管理员",
    "role": "admin"
  }
}
```

### 2.3 获取飞书OAuth URL
**GET /auth/feishu/url**

#### 响应示例
```json
{
  "url": "https://open.feishu.cn/open-apis/authen/v1/index?app_id=..."
}
```

### 2.4 获取用户能力
**GET /auth/me/capabilities**

#### 响应示例
```json
{
  "role": "admin",
  "capabilities": {
    "user:create": true,
    "product:create": true,
    "channel:create": true,
    "lead:create": true,
    "customer:create": true,
    "opportunity:create": true,
    "project:create": true,
    "contract:create": true
  }
}
```

## 3. 客户管理接口 (/customers)

### 3.1 获取客户列表
**GET /customers/**

#### 查询参数
| 参数 | 类型 | 说明 |
|------|------|------|
| 无 | - | 根据用户权限返回相应客户列表 |

#### 响应示例
```json
[
  {
    "id": 1,
    "customer_code": "CUS00001",
    "customer_name": "山东科技有限公司",
    "credit_code": "91370105MA3TGY8H2L",
    "customer_industry": "信息技术",
    "customer_region": "山东省",
    "customer_owner_id": 1,
    "customer_owner_name": "张三",
    "channel_id": 1,
    "channel_name": "济南渠道商",
    "main_contact": "李四",
    "phone": "13800138000",
    "customer_status": "活跃",
    "maintenance_expiry": "2026-12-31",
    "notes": "重要客户"
  }
]
```

### 3.2 创建客户
**POST /customers/**

#### 请求参数 (CustomerCreate)
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| customer_name | string | 是 | 客户名称 |
| credit_code | string | 是 | 统一社会信用代码 |
| customer_industry | string | 是 | 所属行业 |
| customer_region | string | 是 | 所在地区 |
| customer_owner_id | integer | 是 | 客户负责人ID |
| channel_id | integer | 否 | 关联渠道ID |
| main_contact | string | 否 | 主要联系人 |
| phone | string | 否 | 联系电话 |
| customer_status | string | 否 | 客户状态（默认：活跃） |
| maintenance_expiry | string | 否 | 维保到期日期 |
| notes | string | 否 | 备注信息 |

#### 请求示例
```json
{
  "customer_name": "山东科技有限公司",
  "credit_code": "91370105MA3TGY8H2L",
  "customer_industry": "信息技术",
  "customer_region": "山东省",
  "customer_owner_id": 1,
  "channel_id": 1,
  "main_contact": "李四",
  "phone": "13800138000",
  "customer_status": "活跃",
  "maintenance_expiry": "2026-12-31",
  "notes": "重要客户"
}
```

#### 响应示例
```json
{
  "id": 1,
  "customer_code": "CUS00001",
  "customer_name": "山东科技有限公司",
  "credit_code": "91370105MA3TGY8H2L",
  "customer_industry": "信息技术",
  "customer_region": "山东省",
  "customer_owner_id": 1,
  "customer_owner_name": "张三",
  "channel_id": 1,
  "channel_name": "济南渠道商",
  "main_contact": "李四",
  "phone": "13800138000",
  "customer_status": "活跃",
  "maintenance_expiry": "2026-12-31",
  "notes": "重要客户"
}
```

### 3.3 获取客户详情
**GET /customers/{customer_id}**

#### 路径参数
| 参数 | 类型 | 说明 |
|------|------|------|
| customer_id | integer | 客户ID |

#### 响应示例
同创建客户的响应格式

### 3.4 更新客户
**PUT /customers/{customer_id}**

#### 路径参数
| 参数 | 类型 | 说明 |
|------|------|------|
| customer_id | integer | 客户ID |

#### 请求参数
同创建客户的请求参数（字段可选）

### 3.5 删除客户
**DELETE /customers/{customer_id}**

#### 路径参数
| 参数 | 类型 | 说明 |
|------|------|------|
| customer_id | integer | 客户ID |

#### 响应示例
```json
{
  "message": "客户删除成功"
}
```

### 3.6 检查统一社会信用代码
**GET /customers/check-credit-code**

#### 查询参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| credit_code | string | 是 | 统一社会信用代码 |
| exclude_id | integer | 否 | 排除的客户ID（用于更新时检查） |

#### 响应示例
```json
{
  "exists": false
}
```

## 4. 线索管理接口 (/leads)

### 4.1 获取线索列表
**GET /leads/**

#### 响应示例
```json
[
  {
    "id": 1,
    "lead_code": "LEAD00001",
    "lead_name": "潜在客户A",
    "contact_name": "王经理",
    "phone": "13900139000",
    "email": "wang@company.com",
    "lead_source": "客户推荐",
    "lead_industry": "制造业",
    "region": "山东省",
    "sales_owner_id": 1,
    "sales_owner_name": "张三",
    "follow_up_status": "待跟进",
    "next_follow_up_date": "2026-04-25",
    "notes": "有强烈购买意向",
    "converted_opportunity_id": null
  }
]
```

### 4.2 创建线索
**POST /leads/**

#### 请求参数 (LeadCreate)
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| lead_name | string | 是 | 线索名称 |
| contact_name | string | 是 | 联系人姓名 |
| phone | string | 是 | 联系电话 |
| email | string | 否 | 联系邮箱 |
| lead_source | string | 是 | 线索来源 |
| lead_industry | string | 是 | 所属行业 |
| region | string | 是 | 所在地区 |
| sales_owner_id | integer | 是 | 负责销售ID |
| next_follow_up_date | string | 否 | 下次跟进日期 |
| notes | string | 否 | 备注信息 |

### 4.3 线索详情、更新、删除
接口格式同客户管理，路径为 `/leads/{lead_id}`

### 4.4 转换线索为商机
**POST /leads/{lead_id}/convert**

#### 路径参数
| 参数 | 类型 | 说明 |
|------|------|------|
| lead_id | integer | 线索ID |

#### 请求参数
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| opportunity_name | string | 是 | 商机名称 |
| expected_amount | number | 是 | 预计金额 |
| close_date | string | 是 | 预计关闭日期 |
| probability | integer | 是 | 成功率（0-100） |

#### 响应示例
```json
{
  "opportunity_id": 1,
  "opportunity_name": "商机A",
  "message": "线索转换成功"
}
```

## 5. 渠道管理接口 (/channels)

### 5.1 获取渠道列表
**GET /channels/**

### 5.2 创建渠道
**POST /channels/**

#### 请求参数 (ChannelCreate)
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| company_name | string | 是 | 公司名称 |
| credit_code | string | 是 | 统一社会信用代码 |
| industry | string | 是 | 所属行业 |
| region | string | 是 | 所在地区 |
| company_address | string | 是 | 公司地址 |
| legal_representative | string | 是 | 法人代表 |
| business_license | string | 是 | 营业执照编号 |
| contract_start_date | string | 是 | 合同开始日期 |
| contract_end_date | string | 是 | 合同结束日期 |
| account_manager_id | integer | 是 | 客户经理ID |
| status | string | 是 | 渠道状态 |
| service_level | string | 是 | 服务等级 |
| payment_terms | string | 是 | 付款条件 |
| pricing_policy | string | 是 | 价格政策 |
| technical_support_level | string | 是 | 技术支持等级 |
| training_entitlement | string | 是 | 培训权益 |
| marketing_support_level | string | 是 | 市场支持等级 |

### 5.3 渠道全景视图
**GET /channels/{channel_id}/full-view**

#### 路径参数
| 参数 | 类型 | 说明 |
|------|------|------|
| channel_id | integer | 渠道ID |

#### 响应示例
```json
{
  "id": 1,
  "company_name": "济南渠道商",
  "basic_info": {
    // 渠道基本信息
  },
  "contacts": [
    // 渠道联系人列表
  ],
  "assignments": [
    // 渠道分配记录
  ],
  "execution_plans": [
    // 执行计划
  ],
  "performance_metrics": {
    // 绩效指标
  },
  "unified_targets": [
    // 统一目标
  ]
}
```

### 5.4 渠道子端点
渠道模块提供丰富的子端点：

- **联系人管理**: `/channels/{channel_id}/contacts`
- **线索管理**: `/channels/{channel_id}/leads`
- **跟进记录**: `/channels/{channel_id}/follow-ups`
- **执行计划**: `/channels/{channel_id}/execution-plans`
- **绩效目标**: `/channels/{channel_id}/unified-targets`

## 6. 数据字典接口 (/dict)

### 6.1 获取字典项列表
**GET /dict/items**

#### 查询参数
| 参数 | 类型 | 说明 |
|------|------|------|
| dict_type | string | 字典类别 |
| parent_id | integer | 父级ID |

#### 响应示例
```json
[
  {
    "id": 1,
    "dict_type": "地区",
    "code": "37",
    "name": "山东省",
    "parent_id": null,
    "sort_order": 1,
    "is_active": true
  },
  {
    "id": 101,
    "dict_type": "地区", 
    "code": "3701",
    "name": "济南市",
    "parent_id": 1,
    "sort_order": 1,
    "is_active": true
  }
]
```

### 6.2 获取字典类别列表
**GET /dict/types**

#### 响应示例
```json
{
  "types": ["地区", "行业", "商机来源", "客户状态", "拜访目的"]
}
```

### 6.3 创建字典项
**POST /dict/items**

#### 请求参数
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| dict_type | string | 是 | 字典类别 |
| code | string | 是 | 业务编码 |
| name | string | 是 | 显示名称 |
| parent_id | integer | 否 | 父级ID |
| sort_order | integer | 否 | 排序权重（默认：0） |
| is_active | boolean | 否 | 是否启用（默认：true） |

### 6.4 产品相关字典
- **品牌列表**: `GET /dict-items/brands`
- **型号列表**: `GET /dict-items/models`
- **产品类型**: `GET /dict-items/product-types`

## 7. 其他核心接口

### 7.1 用户管理 (/users)
- **GET /users/**: 获取用户列表
- **POST /users/**: 创建用户  
- **GET /users/{user_id}**: 获取用户详情
- **PUT /users/{user_id}**: 更新用户
- **DELETE /users/{user_id}**: 删除用户

### 7.2 项目管理 (/projects)
- **GET /projects/**: 获取项目列表
- **POST /projects/**: 创建项目
- **GET /projects/{project_id}**: 获取项目详情
- **PUT /projects/{project_id}**: 更新项目
- **DELETE /projects/{project_id}**: 删除项目

### 7.3 合同管理 (/contracts)
- **GET /contracts/**: 获取合同列表
- **POST /contracts/**: 创建合同
- **GET /contracts/{contract_id}**: 获取合同详情
- **PUT /contracts/{contract_id}**: 更新合同
- **DELETE /contracts/{contract_id}**: 删除合同

### 7.4 工单管理 (/work-orders)
- **GET /work-orders/**: 获取工单列表
- **POST /work-orders/**: 创建工单
- **GET /work-orders/{work_order_id}**: 获取工单详情
- **PUT /work-orders/{work_order_id}**: 更新工单
- **DELETE /work-orders/{work_order_id}**: 删除工单

### 7.5 操作日志 (/operation-logs)
- **GET /operation-logs/**: 获取操作日志列表
- **GET /operation-logs/{log_id}**: 获取日志详情
- **GET /operation-logs/entity/{entity_type}/{entity_id}**: 获取实体操作日志

### 7.6 报表接口 (/reports)
- **GET /reports/sales-funnel**: 销售漏斗报表
- **GET /reports/performance**: 业绩统计报表  
- **GET /reports/repayment-progress**: 回款进度报表
- **GET /reports/channel-performance**: 渠道绩效报表

## 8. 错误处理

### 8.1 常见HTTP状态码
| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未认证或Token过期 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

### 8.2 常见错误信息
- `"该统一社会信用代码已存在"` - 客户/渠道信用代码重复
- `"权限不足，无法访问此资源"` - RBAC权限验证失败
- `"用户未登录或Token已过期"` - 认证失败

## 9. 分页和过滤

### 9.1 列表接口分页
大部分列表接口支持标准分页：
- 默认每页10条记录
- 可通过查询参数调整分页大小

### 9.2 数据过滤
根据用户角色自动过滤数据：
- **sales角色**: 只能看到自己负责的客户/线索/商机
- **technician角色**: 只能看到分配给自己的工单
- **admin/business角色**: 可以看到全部数据

## 10. 安全考虑

### 10.1 认证安全
- JWT Token有效期：30分钟
- 支持Token刷新机制
- 敏感操作需要重新认证

### 10.2 数据安全
- 所有敏感数据传输使用HTTPS
- 密码使用bcrypt加密存储
- 操作日志记录所有关键操作
- 基于角色的细粒度访问控制

### 10.3 API限流
- 防止恶意请求和DDoS攻击
- 关键接口有速率限制

---

*本文档基于CRM系统当前API实现生成，最后更新时间：2026年4月22日*