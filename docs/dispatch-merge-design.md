# 派工系统合并方案：让派工系统成为销管系统的附属系统

## 一、背景与目标

### 1.1 当前架构
```
┌─────────────────┐     ┌─────────────────┐
│    销管系统      │     │    派工系统      │
│   PostgreSQL    │     │     SQLite      │
├─────────────────┤     ├─────────────────┤
│ users (销售人员) │     │ users (技术人员) │ ← 数据分离
│ leads           │     │ work_orders      │
│ opportunities   │     │ evaluations      │
│ projects        │     │ knowledge        │
│ dispatch_records│     │ customer_records │
└─────────────────┘     └─────────────────┘
        ↓                      ↓
   销管前端API             派工前端API
        └───────────相互调用───────────┘
```

**问题：**
- 用户数据分离：销售人员和技术人员在不同数据库
- 客户数据分离：terminal_customers vs customer_records
- 需要跨系统API调用，数据同步复杂
- 渠道管理系统待对接，同样面临数据分离问题

### 1.2 目标架构
```
┌─────────────────────────────────────────────┐
│              PostgreSQL (统一数据库)          │
├─────────────────────────────────────────────┤
│            【共享核心表】                      │
│  users (销售+技术人员统一)                    │
│  terminal_customers (客户主表)               │
│  channels (渠道主表)                          │
├─────────────────────────────────────────────┤
│            【销管专用表】                      │
│  leads, opportunities, projects, contracts   │
│  follow_ups, sales_targets                   │
├─────────────────────────────────────────────┤
│            【派工专用表】                      │
│  work_orders (迁移过来)                       │
│  work_order_technicians                      │
│  evaluations                                  │
│  knowledge                                    │
├─────────────────────────────────────────────┤
│            【渠道系统表】(将来)                │
│  channel_orders, ...                          │
└─────────────────────────────────────────────┘
        ↓                  ↓                  ↓
   销管系统API         派工系统API        渠道系统API
   (连接同一DB)        (连接同一DB)       (连接同一DB)
```

**目标：**
- 所有核心数据存储在销管PostgreSQL
- 派工系统作为附属系统，直接连接销管数据库
- 用户、客户、渠道数据只存一份，天然一致

---

## 二、数据库合并方案

### 2.1 Users表合并

**销管users表当前字段：**
```python
id, email, hashed_password, is_active
role (sales/admin/business/finance)  ← 单一角色
name, feishu_id, phone, avatar
sales_leader_id, sales_region, sales_product_line  ← 销售专用
```

**需要新增的字段：**
```python
functional_role       String    # 功能角色: TECHNICIAN/SALES/null
responsibility_role   String    # 职责角色: SYSTEM_ADMIN/ADMIN/AUDITOR/OTHER/null
department            String    # 部门（从飞书同步）
status                String    # 状态: ACTIVE/DISABLED，默认ACTIVE
feishu_union_id       String    # 飞书union_id
```

**迁移策略：**
```sql
-- 1. 添加新字段
ALTER TABLE users ADD COLUMN functional_role VARCHAR(20) DEFAULT 'SALES';
ALTER TABLE users ADD COLUMN responsibility_role VARCHAR(30);
ALTER TABLE users ADD COLUMN department VARCHAR(100);
ALTER TABLE users ADD COLUMN status VARCHAR(10) DEFAULT 'ACTIVE';
ALTER TABLE users ADD COLUMN feishu_union_id VARCHAR(100);

-- 2. 数据迁移（派工SQLite → 销管PostgreSQL）
-- 将派工系统的技术人员插入销管users表
INSERT INTO users (name, phone, email, functional_role, department, status, feishu_id)
SELECT name, phone, email, functionalRole, department, status, feishuId
FROM dispatch_users WHERE functionalRole = 'TECHNICIAN';

-- 3. 角色兼容映射
UPDATE users SET functional_role = 'SALES' WHERE role = 'sales';
UPDATE users SET functional_role = 'TECHNICIAN' WHERE role = 'technician';
```

### 2.2 工单表迁移

**新建work_orders表（PostgreSQL）：**
```sql
CREATE TABLE work_orders (
    id VARCHAR(50) PRIMARY KEY,           -- cuid格式
    order_no VARCHAR(50) UNIQUE,          -- 工单编号
    order_type VARCHAR(10) DEFAULT 'CF',  -- CF/CO/MF/MO
    
    -- 提交人和关联销售
    submitter_id INTEGER REFERENCES users(id),
    related_sales_id INTEGER REFERENCES users(id),
    
    -- 客户信息
    customer_name VARCHAR(255) NOT NULL,
    customer_contact VARCHAR(100),
    customer_phone VARCHAR(50),
    
    -- 渠道信息
    has_channel BOOLEAN DEFAULT FALSE,
    channel_name VARCHAR(100),
    channel_contact VARCHAR(100),
    channel_phone VARCHAR(50),
    
    -- 厂家对接人
    manufacturer_contact VARCHAR(100),
    
    -- 工单信息
    work_type VARCHAR(50),
    priority VARCHAR(20) DEFAULT 'NORMAL',
    description TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING',
    
    -- 时间信息
    estimated_start_date TIMESTAMP,
    estimated_start_period VARCHAR(10),
    estimated_end_date TIMESTAMP,
    estimated_end_period VARCHAR(10),
    accepted_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- 服务信息
    service_summary TEXT,
    cancel_reason TEXT,
    
    -- 关联CRM实体
    source_type VARCHAR(20),
    lead_id INTEGER REFERENCES leads(id),
    opportunity_id INTEGER REFERENCES opportunities(id),
    project_id INTEGER REFERENCES projects(id),
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**新建work_order_technicians关联表：**
```sql
CREATE TABLE work_order_technicians (
    id SERIAL PRIMARY KEY,
    work_order_id VARCHAR(50) REFERENCES work_orders(id) ON DELETE CASCADE,
    technician_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(work_order_id, technician_id)
);
```

### 2.3 其他表迁移

| 表名 | 迁移方式 | 说明 |
|------|----------|------|
| evaluations | 迁移到PostgreSQL | 服务评价表，关联work_orders |
| knowledge | 迁移到PostgreSQL | 知识库表 |
| customer_records | **废弃** | 使用terminal_customers替代 |
| channel_records | **废弃** | 使用channels替代 |

---

## 三、API改造方案

### 3.1 派工系统需要改造的API

| API | 当前实现 | 改造后实现 |
|-----|----------|------------|
| `GET /users/technicians` | SQLite查询 | PostgreSQL查询销管users表 |
| `GET /workorders/suggest/customers` | SQLite customer_records | PostgreSQL terminal_customers |
| `GET /workorders/suggest/channels` | SQLite channel_records | PostgreSQL channels |
| `POST /auth/feishu/login` | 独立认证 | 调用销管飞书认证API |

### 3.2 销管系统需要新增的API

```python
# 技术员列表（改造现有API）
@app.get("/api/users/technicians")
async def get_technicians():
    return await db.execute(
        select(User).where(User.functional_role == 'TECHNICIAN', User.status == 'ACTIVE')
    )

# 客户联想输入（新增）
@app.get("/api/customers/suggest")
async def suggest_customers(keyword: str):
    return await db.execute(
        select(TerminalCustomer)
        .where(TerminalCustomer.name.ilike(f"%{keyword}%"))
        .limit(10)
    )

# 工单管理（新增）
@app.post("/api/dispatch/work-orders")
async def create_work_order(data: WorkOrderCreate):
    ...

@app.get("/api/dispatch/work-orders/{id}")
async def get_work_order(id: str):
    ...

@app.patch("/api/dispatch/work-orders/{id}/status")
async def update_work_order_status(id: str, status: str):
    ...
```

---

## 四、代码改造清单

### 4.1 销管系统改造

| 文件 | 改造内容 |
|------|----------|
| `backend/app/models/user.py` | 添加functional_role, department等字段 |
| `backend/app/models/work_order.py` | 新建工单模型文件 |
| `backend/app/main.py` | 新增工单相关API端点 |
| `backend/app/services/dispatch_service.py` | 重构，直接操作PostgreSQL |

### 4.2 派工系统改造

| 文件 | 改造内容 |
|------|----------|
| `server/prisma/schema.prisma` | 改用PostgreSQL连接 |
| `server/src/routes/user.ts` | 改为调用销管API或直接连接销管DB |
| `server/src/routes/workOrder.ts` | 改为连接销管PostgreSQL |
| `server/src/routes/auth.ts` | 改为调用销管飞书认证 |
| `server/src/feishu/messageService.ts` | 保留，适配销管JWT |

### 4.3 前端改造

| 文件 | 改造内容 |
|------|----------|
| `frontend/src/components/common/DispatchModal.tsx` | 技术员API路径修改 |
| `frontend/src/services/dispatchService.ts` | API路径统一 |
| 派工前端各页面 | API调用路径修改 |

---

## 五、风险评估

### 5.1 高风险项

| 风险 | 严重度 | 应对方案 |
|------|--------|----------|
| users表字段缺失导致数据丢失 | 高 | 先添加字段，设置默认值，再迁移 |
| 工单编号冲突 | 高 | 迁移前检查去重 |
| 飞书OAuth认证失败 | 高 | 保留派工飞书服务，适配销管JWT |
| 技术员ID映射失败 | 高 | 建立过渡映射表 |

### 5.2 中风险项

| 风险 | 严重度 | 应对方案 |
|------|--------|----------|
| 联想输入性能下降 | 中 | 添加索引优化查询 |
| 前端API不兼容 | 中 | API层添加兼容适配器 |
| 数据类型转换问题 | 中 | 编写转换脚本，逐条验证 |

---

## 六、实施步骤（分阶段）

### 阶段一：基础设施准备（1-2周）

**任务清单：**
1. 销管users表添加新字段
2. 创建work_orders、work_order_technicians、evaluations表
3. 编写数据迁移脚本
4. 统一认证系统测试

### 阶段二：API改造（2-3周）

**任务清单：**
1. 销管系统新增工单管理API
2. 派工系统改造数据库连接
3. 技术员/客户/渠道联想API改造
4. 飞书消息通知适配

### 阶段三：数据迁移（1-2周）

**任务清单：**
1. 迁移派工系统users数据到销管users
2. 迁移work_orders数据
3. 迁移evaluations、knowledge数据
4. 数据验证与一致性检查

### 阶段四：前端适配与测试（1周）

**任务清单：**
1. 前端API调用更新
2. 联调测试
3. 灰度上线
4. 监控与回滚准备

---

## 七、回滚方案

### 7.1 数据库回滚

```sql
-- 备份原始数据
CREATE TABLE users_backup AS SELECT * FROM users;
CREATE TABLE dispatch_records_backup AS SELECT * FROM dispatch_records;

-- 回滚命令
DROP TABLE work_orders;
DROP TABLE work_order_technicians;
DROP TABLE evaluations;
RESTORE TABLE users FROM users_backup;
```

### 7.2 代码回滚

- 所有代码改动使用Git分支管理
- 保留原派工系统代码备份
- 提供一键切换配置脚本

---

## 八、成功标准

1. **数据完整性**：所有工单数据成功迁移，无丢失
2. **功能完整性**：派工流程（创建→接单→服务→评价）全部正常
3. **性能达标**：API响应时间<2s，联想输入<500ms
4. **认证统一**：飞书OAuth登录正常，JWT兼容
5. **前端正常**：所有页面功能无异常
6. **可回滚**：提供完整回滚方案

---

## 附录：当前系统差距总结

### 数据模型差距

| 项目 | 销管系统 | 派工系统 | 差距 |
|------|----------|----------|------|
| users表 | 销售角色 | 双重权限 | 缺5个字段 |
| 工单表 | dispatch_records(简化) | work_orders(完整) | 缺15个字段 |
| 客户联想 | 无 | customer_records | 需改用terminal_customers |

### API差距

- 派工系统4个API依赖SQLite数据源
- 销管系统缺少完整工单管理API
- 认证系统需统一

### 前端差距

- 6个API调用路径需修改
- 技术员下拉框数据源需切换