# 三系统整合方案：销管核心 + 派工/渠道附属模块

## 一、背景与目标

### 1.1 用户目标
"我想要把渠道和派工的核心能力抽象出来放到销管系统里作为一个模块进行使用。渠道管理和派工系统与销管系统进行联动，作为销管系统的派生能力。"

### 1.2 当前系统概况

| 系统 | 技术栈 | 数据库 | 用户主键 | 认证方式 | 核心功能 |
|------|--------|--------|----------|----------|----------|
| **销管(CRM)** | Python/FastAPI | PostgreSQL | Integer | JWT+飞书OAuth | 线索/商机/项目/合同/客户管理 |
| **派工系统** | Node/Express/Prisma | SQLite | String(cuid) | 飞书OAuth | 工单/评价/知识库 |
| **渠道管理(QDmgt)** | Python/FastAPI | PostgreSQL | UUID | JWT | 渠道目标/分配/执行计划 |

**关键发现：**
- 派工系统与销管系统技术栈不同（Node vs Python），需重构
- 渠道管理与销管系统技术栈相同，可直接整合
- 三个用户表结构差异大，需要统一设计

---

## 二、整体架构设计

### 2.1 目标架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    PostgreSQL (统一数据库)                       │
├─────────────────────────────────────────────────────────────────┤
│                   【共享核心表】                                   │
│  users (统一用户 - 销售+技术+渠道管理)                            │
│  channels (增强渠道 - 基础+高级功能)                              │
│  terminal_customers (客户主表)                                    │
├─────────────────────────────────────────────────────────────────┤
│                   【销管核心模块】                                 │
│  leads, opportunities, projects, contracts                       │
│  follow_ups, sales_targets                                       │
│  dispatch_records (派工记录追踪)                                  │
├─────────────────────────────────────────────────────────────────┤
│                   【渠道管理模块】(附属)                           │
│  channel_assignments (渠道分配)                                   │
│  unified_targets (统一目标 - 个人/渠道)                           │
│  execution_plans (执行计划)                                       │
├─────────────────────────────────────────────────────────────────┤
│                   【派工集成模块】(附属)                           │
│  work_orders (工单完整生命周期)                                   │
│  work_order_technicians (工单-技术员关联)                        │
│  evaluations (服务评价)                                           │
│  knowledge (知识库)                                               │
│  customer_autocomplete (客户联想输入)                             │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 模块划分原则

**核心能力（保留在销管）：**
- 业务实体管理（客户、商机、项目、合同）
- 用户认证和权限管理
- 基础渠道信息
- 销售目标和业绩分析

**派工附属能力：**
- 工单完整生命周期管理
- 技术人员分配和调度
- 服务评价和反馈
- 知识库沉淀

**渠道附属能力：**
- 渠道高级管理（状态追踪、业务类型）
- 目标规划（季度/月度目标）
- 渠道分配和权限控制
- 执行计划跟踪

---

## 三、数据合并方案

### 3.1 用户表统一（难度：4/5）

**挑战：三个不同的主键策略**
- 销管：Integer主键
- 渠道：UUID主键
- 派工：String(cuid)主键

**解决方案：扩展销管users表，保持兼容性**

```python
class User(Base):
    __tablename__ = "users"
    
    # 保持销管现有结构（Integer主键）
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="sales")  # 扩展角色
    name = Column(String)
    feishu_id = Column(String, unique=True, index=True)
    phone = Column(String)
    avatar = Column(Text)
    
    # 新增字段 - 兼容其他系统
    uuid_id = Column(UUID(as_uuid=True), unique=True, index=True)  # 渠道系统兼容
    cuid_id = Column(String(255), unique=True, index=True)  # 派工系统兼容
    functional_role = Column(String(50))  # TECHNICIAN/SALES（派工）
    responsibility_role = Column(String(50))  # ADMIN/AUDITOR（派工）
    department = Column(String(100))  # 部门
    status = Column(String(10), default='ACTIVE')  # ACTIVE/DISABLED
    
    # 销管原有字段
    sales_leader_id = Column(Integer, ForeignKey("users.id"))
    sales_region = Column(String)
    sales_product_line = Column(String)
```

**迁移策略：**
1. 添加新列（nullable）
2. 渠道用户：创建新记录，映射uuid_id → id
3. 派工用户：创建新记录，映射cuid_id → id
4. 统一认证逻辑
5. 验证后移除旧主键映射

### 3.2 渠道数据整合（难度：3/5）

**现状：**
- 销管channels：基础信息，Integer主键
- 渠道channels：高级功能，UUID主键，状态枚举，业务类型

**方案：增强销管channel模型**

```python
class Channel(Base):
    __tablename__ = "channels"
    
    # 保持销管现有字段
    id = Column(Integer, primary_key=True)
    channel_code = Column(String(30), unique=True)
    company_name = Column(String(255))
    channel_type = Column(String(30))
    status = Column(String(20), default="合作中")
    
    # 新增渠道系统高级字段
    uuid_id = Column(UUID(as_uuid=True), unique=True, index=True)  # 兼容
    business_type = Column(Enum(BusinessType))  # basic/high-value/pending-signup
    channel_status = Column(Enum(ChannelStatus))  # active/inactive/suspended
    contact_person = Column(String(100))
    contact_email = Column(String(255))
    contact_phone = Column(String(50))
    
    # 增强审计字段
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    last_modified_by = Column(Integer, ForeignKey("users.id"))
    
    # 关系
    opportunities = relationship("Opportunity", back_populates="channel")
    projects = relationship("Project", back_populates="channel")
    channel_assignments = relationship("ChannelAssignment", back_populates="channel")
    channel_targets = relationship("ChannelTarget", back_populates="channel")
```

### 3.3 派工数据迁移（难度：4/5）

**SQLite → PostgreSQL 迁移映射：**

| 派工表 | 目标表 | 迁移要点 |
|--------|--------|----------|
| work_orders | work_orders | 字段映射+类型转换 |
| users | users | 用户统一方案 |
| evaluations | evaluations | 保持工单关联 |
| knowledge | knowledge | 内容验证 |
| customer_records | customer_autocomplete | 整合到联想系统 |

**工单表结构：**
```python
class WorkOrder(Base):
    __tablename__ = "work_orders"
    
    id = Column(Integer, primary_key=True)  # 改为Integer
    work_order_no = Column(String(50), unique=True)
    order_type = Column(String(10), default="CF")  # CF/CO/MF/MO
    submitter_id = Column(Integer, ForeignKey("users.id"))
    related_sales_id = Column(Integer, ForeignKey("users.id"))
    customer_name = Column(String(255))
    channel_id = Column(Integer, ForeignKey("channels.id"))
    priority = Column(String(20), default="NORMAL")
    description = Column(Text)
    status = Column(String(50), default="PENDING")
    # 时间字段...
```

---

## 四、API设计规范

### 4.1 核心API（保留）

```
用户管理：
GET  /api/v1/users
POST /api/v1/users
PUT  /api/v1/users/{id}

渠道基础：
GET  /api/v1/channels
POST /api/v1/channels
```

### 4.2 渠道管理API（新增）

```
渠道高级管理：
POST   /api/v1/channels/{id}/assignments      # 分配用户
GET    /api/v1/channels/{id}/targets          # 获取目标
POST   /api/v1/channels/targets               # 创建统一目标
GET    /api/v1/channels/{id}/execution-plans  # 执行计划
POST   /api/v1/channels/{id}/full-view        # 渠道全景
```

### 4.3 派工API（新增）

```
工单管理：
POST   /api/v1/dispatch/work-orders           # 创建工单
GET    /api/v1/dispatch/work-orders           # 工单列表
PUT    /api/v1/dispatch/work-orders/{id}      # 更新状态
POST   /api/v1/dispatch/work-orders/{id}/assign # 分配技术员
POST   /api/v1/dispatch/evaluations           # 提交评价
GET    /api/v1/dispatch/knowledge             # 知识库搜索
```

### 4.4 整合API（增强）

```
跨模块整合：
POST /api/v1/leads/{id}/create-dispatch          # 线索→派工
POST /api/v1/opportunities/{id}/create-dispatch  # 商机→派工
POST /api/v1/projects/{id}/create-dispatch       # 项目→派工
POST /api/v1/webhooks/dispatch                   # 状态回调
```

---

## 五、可行性评估

### 5.1 技术可行性

| 领域 | 可行性 | 说明 |
|------|--------|------|
| 数据库扩展 | ✅ 高 | PostgreSQL支持所有特性 |
| API整合 | ✅ 高 | FastAPI模块化设计友好 |
| 用户认证统一 | ✅ 高 | 标准JWT协议 |
| 主键迁移 | ⚠️ 中 | 需要数据转换 |
| 派工系统重构 | ⚠️ 中 | Node→Python需重写 |

### 5.2 业务可行性

- ✅ 无功能冲突：三个系统互补而非冲突
- ✅ 增强用户体验：单点登录、统一仪表盘
- ✅ 数据一致性：消除数据孤岛
- ✅ 成本效率：减少基础设施和维护成本

---

## 六、实施难度与风险评估

### 6.1 难度评分矩阵

| 整合点 | 难度(1-5) | 主要风险 | 应对方案 |
|--------|-----------|----------|----------|
| 用户表统一 | 4 | 数据丢失、认证失败 | 双写迁移、完整备份、回滚计划 |
| 主键迁移 | 4 | 外键约束冲突 | 扩展-收缩模式、验证后再切换 |
| 派工数据迁移 | 3 | 类型不匹配、关系完整性 | Schema验证脚本、增量迁移 |
| API整合 | 2 | 破坏现有客户端 | 版本化API、兼容层 |
| 性能影响 | 3 | 查询性能下降 | 索引优化、缓存策略 |
| 认证统一 | 3 | Token过期问题 | 刷新机制、会话管理 |

### 6.2 关键风险与应对

**风险1：用户数据丢失**
- 严重度：高
- 应对：迁移前完整备份、双写验证期、迁移后数据校验

**风险2：派工系统重构复杂**
- 严重度：高
- 应对：分阶段重构，先迁移数据，再重写API

**风险3：外键关系破坏**
- 严重度：中
- 应对：扩展-收缩迁移模式，先添加映射字段，验证后再移除

**风险4：认证系统不兼容**
- 严重度：中
- 应对：统一JWT payload格式，保留飞书OAuth流程

---

## 七、实施计划（分阶段）

### 阶段一：基础设施（第1-2周）

**任务：**
1. 设计并实现统一用户表
2. 增强渠道模型
3. 准备数据库迁移脚本
4. 统一认证系统设计

### 阶段二：渠道模块整合（第3-5周）

**任务：**
1. 渠道管理模块实现
2. 目标规划和分配功能
3. 执行计划追踪
4. 渠道分析功能

### 阶段三：派工模块整合（第6-8周）

**任务：**
1. 工单管理系统迁移（SQLite→PostgreSQL）
2. 技术人员分配和调度
3. 知识库整合
4. 服务评价功能

### 阶段四：整合测试（第9-10周）

**任务：**
1. 跨模块API整合
2. 端到端流程测试
3. 性能优化和验证
4. 文档和培训

**总计：10周**

---

## 八、成功标准

| 标准 | 指标 |
|------|------|
| 数据完整性 | 迁移过程零数据丢失 |
| 向后兼容 | 现有CRM客户端继续工作 |
| 性能 | 关键操作响应<200ms |
| 安全 | 所有模块权限检查正确 |
| 测试覆盖 | 90%+，重点整合点 |
| 回滚能力 | 各阶段可独立回滚 |

---

## 九、回滚策略

1. **数据库备份**：每个迁移阶段前完整备份
2. **功能开关**：新功能通过feature flag控制
3. **双写期**：过渡期间保持双写能力
4. **监控告警**：数据不一致实时告警

---

## 十、关键决策点

1. **用户表主键选择**：建议保持Integer（销管兼容），通过映射字段兼容其他系统
2. **派工系统重构**：建议重写为Python（与销管技术栈统一）
3. **渠道系统整合**：建议直接合并（技术栈相同）
4. **认证统一**：建议保留销管JWT+飞书OAuth，扩展payload字段