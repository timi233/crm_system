# 渠道系统集成交接文档

## 1. 文档目的

本文档用于向 `opencode` 交付当前已经收敛的渠道系统集成方案。

目标不是重新讨论方向，而是把以下内容一次性说清楚：

- 当前代码里已经有什么，哪些不要重做
- 前期讨论中哪些判断已经被代码核实或推翻
- 最终认可的目标架构与数据模型
- 后端、前端、权限、迁移、测试的实施边界
- 推荐的开发顺序与切分方式

本文档是渠道集成工作的执行说明书，优先级高于早期的零散讨论记录。

相关参考文档：

- [docs/architecture-design.md](./architecture-design.md)
- [docs/three-system-integration-design.md](./three-system-integration-design.md)
- [docs/dispatch-merge-design.md](./dispatch-merge-design.md)

本文档与上述文档的关系：

- `architecture-design.md` 是系统级说明
- `three-system-integration-design.md` 是较早期的整合设计，包含部分已过时判断
- **本文档是“渠道域如何并入 CRM 并交付实施”的最新定稿**

---

## 2. 项目目标

将渠道系统能力完整并入当前 CRM，使系统最终覆盖三块业务：

- 销售业务
- 渠道管理
- 工程师派工

最终形态不是三个并排系统，而是一个以客户为中心的数据闭环：

```text
TerminalCustomer
  ├─ 销售链路：Lead -> Opportunity -> Project -> Contract
  ├─ 渠道链路：Channel -> Assignment -> Target -> ExecutionPlan
  └─ 服务链路：Dispatch -> WorkOrder -> Evaluation -> Knowledge
```

核心原则：

- CRM 是唯一事实源
- QDmgt 不长期双写，不长期并行
- 客户是中心对象
- 渠道不能再只是客户附属备注，而要成为独立业务域
- 当前能兼容的旧字段继续兼容，但新能力不要建立在旧限制上

---

## 3. 已核实的现状

这一部分非常重要。`opencode` 在实施前必须先接受这些事实，否则容易重复造轮子。

### 3.1 已存在的能力

当前仓库中，以下能力已经存在：

#### 1. `/channels` CRUD 已存在

代码位置：

- [backend/app/routers/channel.py](../backend/app/routers/channel.py)
- [backend/app/main.py](../backend/app/main.py)

已注册路由：

- `GET /channels`
- `POST /channels`
- `GET /channels/{id}`
- `PUT /channels/{id}`
- `DELETE /channels/{id}`

结论：

- **不要新建第二套 `/channels` CRUD**
- 需要做的是收口权限、统一实现、补聚合能力

#### 2. `/channels/{id}/full-view` 已存在

代码位置：

- [backend/app/main.py](../backend/app/main.py)
- [frontend/src/hooks/useChannelFullView.ts](../frontend/src/hooks/useChannelFullView.ts)
- [frontend/src/pages/ChannelFullViewPage.tsx](../frontend/src/pages/ChannelFullViewPage.tsx)

当前后端 full-view 已返回：

- `channel`
- `summary`
- `customers`
- `opportunities`
- `projects`
- `contracts`

当前前端页面已消费该结构。

结论：

- **不要重新设计另一条 full-view 主链路**
- 需要扩展现有接口和前端类型

#### 3. 渠道管理核心模型已存在

代码位置：

- [backend/app/models/channel.py](../backend/app/models/channel.py)
- [backend/app/models/channel_assignment.py](../backend/app/models/channel_assignment.py)
- [backend/app/models/unified_target.py](../backend/app/models/unified_target.py)
- [backend/app/models/execution_plan.py](../backend/app/models/execution_plan.py)

已有模型：

- `Channel`
- `ChannelAssignment`
- `UnifiedTarget`
- `ExecutionPlan`

并且 `Channel` 已带部分 `QDmgt` 兼容字段：

- `uuid_id`
- `business_type`
- `channel_status`
- 审计字段 `created_by / last_modified_by`

#### 4. 前端渠道页已存在

代码位置：

- [frontend/src/components/lists/ChannelList.tsx](../frontend/src/components/lists/ChannelList.tsx)
- [frontend/src/pages/ChannelFullViewPage.tsx](../frontend/src/pages/ChannelFullViewPage.tsx)
- [frontend/src/hooks/useChannels.ts](../frontend/src/hooks/useChannels.ts)
- [frontend/src/hooks/useChannelFullView.ts](../frontend/src/hooks/useChannelFullView.ts)

结论：

- **不要把“前端渠道模块”理解成从零开始**
- 需要做的是把“渠道档案页”升级成“渠道工作台”

#### 5. 派工链路里 `project -> channel` 上下文已修复

代码位置：

- [backend/app/services/local_dispatch_service.py](../backend/app/services/local_dispatch_service.py)

`get_customer_data_from_project()` 当前已经会读取 `project.channel_id` 并回填：

- `has_channel`
- `channel_name`
- `channel_contact`
- `channel_phone`

结论：

- 不要再把“项目派工丢失渠道上下文”作为当前 P0 问题
- 这一项已不再是主阻塞点

#### 6. `Lead.channel_id` 已存在

代码位置：

- [backend/app/models/lead.py](../backend/app/models/lead.py)

结论：

- “给 Lead 加 `channel_id`”不是未来工作，而是已完成状态
- 当前需要解决的是 `channel_id` 的语义升级

### 3.2 当前真实缺口

下面这些才是当前需要实施的真实问题。

#### 1. 渠道接口权限过宽

当前 `/channels` 相关接口基本只依赖 `get_current_user`。

影响：

- 任意登录用户理论上可读全量渠道
- 任意登录用户理论上可创建/修改/删除渠道

这和当前系统权限设计不一致。

#### 2. 渠道 full-view 还是四维聚合，不是渠道工作台

当前缺少：

- `work_orders`
- `assignments`
- `execution_plans`
- `targets`

因此渠道视图仍偏“静态档案”，不是完整业务工作台。

#### 3. 客户与渠道仍是单值关系

当前 `TerminalCustomer` 只有单个 `channel_id`：

- [backend/app/models/customer.py](../backend/app/models/customer.py)

这无法支撑：

- 一个客户多个合作渠道
- 不同角色渠道
- 历史渠道关系
- 未来客户中心化视图

#### 4. `Lead` 的渠道语义还不清晰

当前 `Lead` 只有一个 `channel_id`，但还无法同时表达：

- 来源渠道
- 当前协同渠道

如果不先定语义，后面会产生脏数据。

#### 5. 渠道业绩字段仍是手填

当前 `UnifiedTarget` 有这些字段：

- `achieved_performance`
- `achieved_opportunity`
- `achieved_project_count`

但没有自动汇总逻辑。

#### 6. 存在渠道路由实现分散风险

当前仓库同时存在：

- `backend/app/routers/channel.py`
- `backend/app/main.py` 中的渠道相关接口

这意味着渠道接口实现存在分散或重复维护风险。

结论：

- `opencode` 在实施时应先收敛为单一实现来源
- 不要在已有重复基础上再继续叠加第三套实现

---

## 4. 已达成的一致结论

这部分是本次讨论的最终决策，不再反复摇摆。

### 4.1 结论一：CRM 是唯一事实源

采用单系统并域方案：

- 当前 CRM 做唯一业务主入口
- 渠道能力并入 CRM
- `QDmgt` 作为迁移来源，不作为长期主业务系统

不采用长期双系统同步方案。

原因：

- UUID / int 主键映射会长期制造复杂度
- 权限会分叉
- 同一客户/渠道/工单口径会不一致
- 客户中心化视图会被迫做跨系统聚合

### 4.2 结论二：渠道是独立业务域，不再只是客户附属信息

未来渠道域至少应覆盖：

- 渠道档案
- 渠道分配
- 渠道目标
- 执行计划
- 渠道视角下的客户/商机/项目/合同/工单聚合

### 4.3 结论三：Lead 采用双渠道语义

最终采用双字段方案：

- `source_channel_id`
- `channel_id`

字段语义：

- `source_channel_id`：线索来源渠道，归因用，原则上创建后不改
- `channel_id`：当前协同渠道，可随着业务推进变化

这样既能做归因，也能做当前协同管理。

### 4.4 结论四：客户多渠道关系要引入 link 表

最终方向是新增 `customer_channel_links`，而不是继续扩大 `terminal_customers.channel_id` 的职责。

但实施方式分阶段：

- 先保留 `customer.channel_id` 兼容旧代码
- 再引入 link 表
- 最后逐步把读取逻辑迁到 link 表

### 4.5 结论五：`entity_channel_links` 先设计、后实施

当前不强制马上落表。

策略：

- 服务层先封装统一查询
- 当前内部仍可走 `entity.channel_id`
- 如果未来出现“一个商机/项目/合同/工单多个渠道”的真实需求，再落表

### 4.6 结论六：渠道权限不能直接复用现成通用实体权限器

这是实施中最容易犯错的一点。

当前对象级权限器：

- [backend/app/core/permissions.py](../backend/app/core/permissions.py)

其中 `sales` 的授权判断逻辑主要依赖：

- owner 字段
- `entity.channel_id`

但 `Channel` 实体本身没有 owner 字段，也没有 `channel_id` 字段。

因此：

- **不要把 `Channel` 直接硬塞进现有通用 `EntityPermissionChecker`**
- 应该为渠道做专用授权 helper

推荐新增：

- `apply_channel_scope_filter(query, current_user, db)`
- `assert_can_access_channel(channel_id, action, current_user, db)`

### 4.7 结论七：渠道业绩口径已经选定

最终口径：

- `achieved_performance`
  - 已签约下游合同金额
  - 条件：`contract_direction = 'Downstream' AND contract_status = 'signed'`
- `achieved_opportunity`
  - 进入 `报价投标 / 合同签订 / 已成交` 阶段的商机金额
- `achieved_project_count`
  - 立项项目数

注意：

- 必须按代码里的真实枚举值写查询条件
- `Contract.contract_status` 当前真实值是英文枚举，不是中文“已签约”

---

## 5. 最终目标架构

### 5.1 目标业务链路

```text
TerminalCustomer
  ├─ CustomerChannelLink (主渠道 / 协作渠道 / 历史渠道)
  ├─ Lead
  │    ├─ source_channel_id
  │    └─ channel_id
  ├─ Opportunity
  │    └─ channel_id
  ├─ Project
  │    └─ channel_id
  ├─ Contract
  │    └─ channel_id
  └─ WorkOrder
       └─ channel_id

Channel
  ├─ ChannelAssignment
  ├─ UnifiedTarget
  ├─ ExecutionPlan
  ├─ 聚合客户/商机/项目/合同/工单
  └─ 未来兼容 QDmgt 的 uuid_id
```

### 5.2 设计原则

- 渠道主档唯一
- 客户主档唯一
- 渠道工作台围绕 `Channel`
- 客户 360 围绕 `TerminalCustomer`
- 工单保留渠道上下文
- 旧字段兼容，但新结构用 link 表

---

## 6. 分阶段实施方案

## Phase 1：渠道域收口

### 6.1 目标

把当前“已存在但过宽、过薄”的渠道能力，收口成可控的业务域。

### 6.2 后端改造

#### A. 统一渠道接口实现来源

当前渠道接口存在于：

- `main.py`
- `routers/channel.py`

实施要求：

- 只保留一套实际实现来源
- 推荐收敛到 `router + service` 模式
- `main.py` 中重复的渠道逻辑应逐步移出

#### B. 新增渠道专用权限能力

新增两个能力：

1. `apply_channel_scope_filter(query, current_user, db)`
2. `assert_can_access_channel(channel_id, action, current_user, db)`

其中 `action` 建议枚举：

- `read`
- `write`
- `admin`

#### C. 渠道接口权限矩阵

| 接口 | admin | business | sales | technician |
|------|-------|----------|-------|------------|
| `list_channels` | 全部 | 全部 | 自己 assignment 的渠道 | 自己工单涉及的渠道 |
| `get_channel` | 全部 | 全部 | 需 assignment(read+) | 自己工单涉及的渠道 |
| `get_channel_full_view` | 全部 | 全部 | 需 assignment(read+) | 自己工单涉及的渠道 |
| `create_channel` | 可 | 可 | 不可 | 不可 |
| `update_channel` | 可 | 可 | 需 assignment(write+) | 不可 |
| `delete_channel` | 可 | 不可 | 不可 | 不可 |

权限实现细节：

- `admin`：全量通过
- `business`：按当前系统既有“准管理员”语义处理
- `sales`：依赖 `ChannelAssignment.permission_level`
- `technician`：只允许访问与自己工单相关联的渠道

`ChannelAssignment.permission_level` 建议解释：

- `read`：查看渠道与工作台
- `write`：修改渠道资料
- `admin`：可管理分配、目标、执行计划

#### D. 扩展 `/channels/{id}/full-view`

当前 full-view 只返回四个业务维度。

目标返回结构：

```json
{
  "channel": {},
  "summary": {
    "customers_count": 0,
    "opportunities_count": 0,
    "projects_count": 0,
    "contracts_count": 0,
    "work_orders_count": 0,
    "total_contract_amount": 0,
    "active_plans_count": 0
  },
  "customers": [],
  "opportunities": [],
  "projects": [],
  "contracts": [],
  "work_orders": [],
  "assignments": [],
  "execution_plans": [],
  "targets": []
}
```

新增查询参数：

- `year`
  - 默认当前年
- `quarter`
  - 可选
- `active_only`
  - 默认 `true`

建议：

- full-view 保持汇总能力
- 同时补轻量接口，避免未来 full-view 过重

建议补的轻量接口：

- `GET /channels/{id}/work-orders`
- `GET /channels/{id}/execution-plans`
- `GET /channels/{id}/targets`
- `GET /channels/{id}/assignments`

#### E. 服务层收口

推荐新增或抽出以下服务：

- `channel_scope_service.py`
  - 渠道读写权限判定
- `channel_overview_service.py`
  - 渠道 full-view 聚合
- `channel_performance_service.py`
  - 渠道目标完成情况聚合

不要继续把渠道聚合 SQL 大量堆在 `main.py`。

### 6.3 前端改造

当前 `ChannelFullViewPage` 只有 4 个 Tab。

目标扩展为 8 个：

- 关联客户
- 商机
- 项目
- 合同
- 工单记录
- 执行计划
- 绩效目标
- 渠道分配

展示建议：

- `执行计划` 支持 `year / quarter / active_only`
- `绩效目标` 支持 `year / quarter`
- `渠道分配` 仅 `admin / business` 显示管理入口
- 其余角色无权时只读或隐藏

前端实现建议：

- 按 Tab 懒加载
- 不要首屏一次请求全部子列表
- 先兼容现有 hook，再逐步拆分 hook

### 6.4 Phase 1 验收标准

- 未授权用户不能随意改删渠道
- `sales` 只能看到自己分配的渠道
- `technician` 只能看到与自己工单相关的渠道
- 渠道 full-view 能展示工单、执行计划、目标、分配
- 前端渠道详情页从“档案页”升级成“工作台”

---

## Phase 2：Lead 双渠道语义 + 渠道业绩自动汇总

### 7.1 Lead 双渠道模型

当前：

- `Lead.channel_id` 已存在

目标：

- 新增 `Lead.source_channel_id`
- 保留 `Lead.channel_id`

字段定义：

| 字段 | 语义 | 是否可修改 |
|------|------|------------|
| `source_channel_id` | 来源渠道，归因字段 | 原则上创建后不可改 |
| `channel_id` | 当前协同渠道 | 可改 |

### 7.2 数据库改造

为 `leads` 增加：

- `source_channel_id INTEGER NULL REFERENCES channels(id)`
- 索引 `ix_leads_source_channel_id`

模型、schema、接口都要同步补齐。

### 7.3 存量数据迁移策略

迁移时允许先用现有 `lead.channel_id` 回填 `source_channel_id`。

但要注意：

- 这只是历史默认推断
- 不应在文档或代码里把它宣称为绝对真实来源

如果后续有审计能力或人工校正机制，可逐步修正。

### 7.4 转商机规则

当 `Lead` 转为 `Opportunity`：

- `Opportunity.channel_id` 继承 `Lead.channel_id`
- `Lead.source_channel_id` 不自动覆盖商机的协同渠道

### 7.5 渠道业绩自动汇总

当前 `UnifiedTarget` 中已有字段：

- `achieved_performance`
- `achieved_opportunity`
- `achieved_project_count`

最终口径如下。

#### A. `achieved_performance`

含义：

- 已签约下游合同金额

建议 SQL 口径：

```sql
sum(contract_amount)
where channel_id = :channel_id
  and contract_direction = 'Downstream'
  and contract_status = 'signed'
```

#### B. `achieved_opportunity`

含义：

- 进入较后阶段的商机金额

建议口径：

```sql
sum(expected_contract_amount)
where channel_id = :channel_id
  and opportunity_stage in ('报价投标', '合同签订', '已成交')
```

#### C. `achieved_project_count`

含义：

- 项目数

建议口径：

```sql
count(*)
where channel_id = :channel_id
```

#### D. `work_orders_count`

说明：

- 只放在渠道工作台 `summary`
- **不要**塞进 `UnifiedTarget`

### 7.6 计算方式建议

建议优先顺序：

1. 先实现显式刷新能力
2. 再视性能需要决定是否实时计算或异步定时

推荐方案：

- 增加手动刷新接口
  - `POST /channels/{id}/refresh-performance`
- full-view 可直接读取 `UnifiedTarget`
- 刷新时批量重算渠道相关 achieved 字段

如果后续需要自动化，可再补：

- 商机阶段变更触发
- 项目创建或更新触发
- 合同状态变更触发

### 7.7 Phase 2 验收标准

- `Lead` 能同时表达来源渠道和当前协同渠道
- 线索转商机时协同渠道能正确带入
- 渠道目标 achieved 字段可自动刷新
- 汇总逻辑使用真实枚举值，不使用错误的中文状态值

---

## Phase 3：客户多渠道关系

### 8.1 目标

解决“一客户只能绑一个渠道”的结构限制。

### 8.2 新增表：`customer_channel_links`

推荐结构：

```sql
CREATE TABLE customer_channel_links (
    id BIGSERIAL PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES terminal_customers(id),
    channel_id BIGINT NOT NULL REFERENCES channels(id),
    role VARCHAR(20) NOT NULL,
    discount_rate NUMERIC(5,4),
    start_date DATE,
    end_date DATE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ,
    created_by BIGINT REFERENCES users(id)
);
```

推荐 role 枚举值：

- `主渠道`
- `协作渠道`
- `历史渠道`

### 8.3 唯一约束策略

不要使用：

- `UNIQUE(customer_id, channel_id, role)`

原因：

- 会阻断同一客户-渠道-角色在不同时间段的历史记录

推荐只加部分唯一索引：

```sql
CREATE UNIQUE INDEX uq_customer_active_primary_channel
ON customer_channel_links (customer_id)
WHERE role = '主渠道' AND end_date IS NULL;
```

这表示：

- 一个客户同时只能有一个生效主渠道
- 允许有多个协作渠道
- 允许历史渠道记录存在

其余重叠校验建议在服务层做：

- 同一客户不能有两个同时生效的主渠道
- 同一客户/渠道/角色的有效期不能非法重叠

### 8.4 兼容策略

保留 `terminal_customers.channel_id`：

- 短期作为兼容字段
- 也可作为“当前主渠道快照”

迁移规则：

- 对已有 `customer.channel_id IS NOT NULL` 的记录
- 自动插入一条 `customer_channel_links`
- `role = '主渠道'`
- `end_date = NULL`

### 8.5 读取迁移策略

实施分三步：

1. 先建 link 表并迁移存量
2. 新写入逻辑同时维护 link 表和 `customer.channel_id`
3. 逐步把 full-view 和渠道工作台读取改为 link 表优先

### 8.6 客户视图影响

后续客户详情页应补：

- 合作渠道
- 历史渠道
- 渠道特定折扣或备注

这一步是客户中心化视图的基础。

### 8.7 Phase 3 验收标准

- 一个客户可存在多个渠道关系
- 同时只能有一个生效主渠道
- 老代码仍能通过 `customer.channel_id` 兼容运行
- 新功能优先从 link 表读取

---

## Phase 4：`entity_channel_links` 预留设计

### 9.1 当前决定

当前阶段不强制落地 `entity_channel_links`。

### 9.2 原因

当前业务链路中：

- `Opportunity.channel_id`
- `Project.channel_id`
- `Contract.channel_id`
- `WorkOrder.channel_id`

已经能支撑“一实体一个主渠道”的业务。

如果现在直接为所有交易对象上 link 表，实施成本较高，且未必立即产生业务价值。

### 9.3 预留要求

尽管暂缓落表，但代码实现必须为后续扩展留口子。

建议：

- 商机/项目/合同/工单的渠道查询不要在控制器里直接写死 SQL
- 封装 service 查询函数
- 当前 service 内部可走 `entity.channel_id`
- 以后切换到 `entity_channel_links` 时只改 service 层

### 9.4 适合未来落表的场景

如果出现以下真实业务，就应启动 `entity_channel_links`：

- 一个商机有主渠道和协作渠道
- 一个项目有主实施渠道和辅助渠道
- 一个合同涉及多渠道分润
- 一个工单由不同渠道协同交付

---

## Phase 5：QDmgt 合并

### 10.1 原则

- CRM 作为唯一事实源
- `channels.uuid_id` 作为历史映射锚点
- QDmgt 迁移后只读化，最终下线

### 10.2 迁移对象

主要包括：

- 渠道主档补充字段
- 渠道分配
- 统一目标
- 执行计划

### 10.3 迁移方式

QDmgt 使用 UUID 主键，当前 CRM 主要使用 int 主键。

因此迁移必须做映射翻译：

- `QDmgt channel.uuid -> CRM channels.uuid_id`
- 再通过 `channels.id` 建立内部 int 关联

不能简单做整表复制。

### 10.4 迁移要求

- 迁移脚本幂等
- 迁移前先建立映射表或映射逻辑
- 对找不到目标 channel 的数据做异常记录
- 迁移完成后保留一段只读验证期

### 10.5 不建议的做法

- 不建议长期双写 CRM 与 QDmgt
- 不建议让前端继续跨两个系统取渠道数据
- 不建议让权限模型在两个系统分别演化

---

## 11. 前端信息架构建议

### 11.1 菜单定位

渠道应从“客户附属信息”升级为独立模块，例如：

- 客户管理
- 线索/商机/项目/合同
- 渠道管理
- 工单派工

### 11.2 Channel 工作台结构

建议页面结构：

1. 顶部概览
   - 基本信息
   - 客户数
   - 商机数
   - 项目数
   - 合同数
   - 工单数
   - 当前活跃执行计划数
2. 主体 Tab
   - 关联客户
   - 商机
   - 项目
   - 合同
   - 工单记录
   - 执行计划
   - 绩效目标
   - 渠道分配

### 11.3 客户 360 后续结构

客户详情最终建议包含：

- 基本信息
- 合作渠道
- 线索/商机/项目/合同
- 工单与实施
- 财务摘要
- 历史跟进

---

## 12. 实施注意事项

### 12.1 不要重做的内容

`opencode` 不应再做以下动作：

- 不要新建第二套 `/channels` CRUD
- 不要把“项目派工无渠道上下文”当作当前问题重新修
- 不要把“给 Lead 增加 `channel_id`”当成待开发事项
- 不要继续在 `main.py` 和 router 之外再加第三套渠道接口

### 12.2 不要误用的实现方式

- 不要把 `Channel` 直接接入现有通用 `EntityPermissionChecker`
- 不要对 `customer_channel_links` 使用全局 `UNIQUE(customer_id, channel_id, role)`
- 不要把 `work_orders_count` 写进 `UnifiedTarget`
- 不要把合同状态写成中文“已签约”去匹配数据库

### 12.3 推荐实现风格

- 路由层只做参数校验和权限入口
- 聚合查询收口到 service
- 多阶段迁移要保持兼容字段可用
- Schema 改动与前端类型改动同步进行

---

## 13. 推荐交付切分

为降低风险，推荐按以下批次交付。

### 批次 1：渠道权限与路由收口

- 渠道接口统一到单一实现来源
- `apply_channel_scope_filter`
- `assert_can_access_channel`
- `/channels` 权限收紧

### 批次 2：渠道工作台升级

- full-view 扩展
- 新增轻量列表接口
- 前端 8 Tab

### 批次 3：Lead 双渠道

- migration
- model/schema/router
- 前端表单与详情

### 批次 4：目标自动汇总

- `channel_performance_service`
- 手动刷新接口
- full-view summary/targets 联动

### 批次 5：客户多渠道

- `customer_channel_links`
- 存量迁移
- 客户视图升级

### 批次 6：QDmgt 合并

- UUID 映射
- 数据迁移
- 只读验证

---

## 14. 测试与验收建议

### 14.1 权限测试

至少覆盖以下角色：

- `admin`
- `business`
- `sales`
- `technician`

关键断言：

- `sales` 看不到未分配渠道
- `sales` 无法修改仅 `read` 权限的渠道
- `technician` 只能看到自己工单相关渠道
- `business` 具备准管理员能力
- `delete_channel` 只有 `admin` 可执行

### 14.2 渠道工作台测试

- full-view 返回结构完整
- `year / quarter / active_only` 生效
- summary 数值与列表数量一致
- 合同金额聚合正确
- 工单数聚合正确

### 14.3 Lead 双渠道测试

- 新建线索时可选来源渠道和协同渠道
- 修改线索时只能改协同渠道
- 转商机时协同渠道正确继承
- 历史回填数据不破坏现有展示

### 14.4 多渠道关系测试

- 一个客户可绑定多个协作渠道
- 同时只能有一个生效主渠道
- 历史渠道记录可保留
- `customer.channel_id` 与 link 表主渠道快照一致

### 14.5 迁移测试

- 脚本可重复运行
- 找不到映射对象时有异常日志
- 迁移前后数量对比可核验

---

## 15. 给 `opencode` 的最终执行指令

如果 `opencode` 基于本文档开始实施，应遵守以下原则：

1. 先修正和收口现有渠道域，不要重建渠道域。
2. 渠道权限必须单独建 helper，不要误复用通用实体 mutation checker。
3. full-view 扩展优先，但要避免接口无限变重，必要时拆轻量接口。
4. `Lead` 采用双渠道语义，不再试图用一个字段兼顾来源与协同。
5. 客户多渠道通过 `customer_channel_links` 实现，旧 `customer.channel_id` 只做兼容快照。
6. `entity_channel_links` 当前只做架构预留，不强制立刻落表。
7. `QDmgt` 最终并入 CRM，不做长期双系统同步。

一句话总结：

**这次工作不是“给 CRM 补一个渠道 CRUD 页面”，而是把渠道从附属信息升级为独立业务域，并为客户中心化的销售-渠道-派工一体化打基础。**
