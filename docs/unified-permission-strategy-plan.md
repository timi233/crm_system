# CRM 统一策略层设计方案

## 1. 目标

本方案的目标不是重写整套权限系统，而是在保留现有 API 路径、响应结构、角色定义不变的前提下，把权限判断逐步收敛到一套统一策略层。

统一策略层要解决的核心问题：

- 同一个资源的列表、详情、创建、更新、删除权限分散在多个位置
- 角色判断、数据范围过滤、对象级校验没有统一入口
- `channel` 这类特殊资源单独维护，和通用实体权限形成两套体系
- 前端菜单可见性、按钮可操作性和后端真实权限容易漂移
- 修一个权限 bug 时，常常不知道还要改哪些分支

本方案的最终目标是让 router 不再直接书写大段 `if user_role == ...`，而统一改为调用策略层：

```python
await policy_service.authorize(
    resource="lead",
    action="read",
    principal=current_user,
    db=db,
    obj=lead,
)

query = await policy_service.scope_query(
    resource="lead",
    action="read",
    principal=current_user,
    db=db,
    query=query,
    model=Lead,
)
```

## 2. 当前现状

当前权限实现是混合式的，主要分散在以下几个入口：

- [backend/app/core/dependencies.py](/home/jian/crm-system/backend/app/core/dependencies.py:1)
  - `require_roles(...)`
  - `apply_data_scope_filter(...)`
- [backend/app/core/permissions.py](/home/jian/crm-system/backend/app/core/permissions.py:1)
  - `EntityPermissionChecker`
  - `assert_can_mutate_entity_v2(...)`
- [backend/app/core/channel_permissions.py](/home/jian/crm-system/backend/app/core/channel_permissions.py:1)
  - 渠道专用 scope/filter/check
- 各 router 内部手写分支
  - 例如 [backend/app/routers/lead.py](/home/jian/crm-system/backend/app/routers/lead.py:89)
  - 例如 [backend/app/routers/customer.py](/home/jian/crm-system/backend/app/routers/customer.py:22)
  - 例如 [backend/app/routers/opportunity.py](/home/jian/crm-system/backend/app/routers/opportunity.py:70)
  - 例如 [backend/app/routers/work_order.py](/home/jian/crm-system/backend/app/routers/work_order.py:31)

已经暴露出的典型问题：

- 列表权限和详情权限不一致
- 创建权限和更新权限不一致
- `channel` 相关逻辑和其他实体逻辑无法复用
- 角色变更时，容易遗漏某个 router 分支

## 3. 设计原则

### 3.1 单一入口

后端所有业务权限判断最终只走一个服务入口，不允许继续在 router 中长期保留自定义分支。

### 3.2 分层表达

权限必须拆成两层：

- 能力判断
  - 这个角色能不能对某类资源做某个动作
- 范围判断
  - 即使能做这个动作，能操作哪些记录

### 3.3 列表与详情一致

`scope_query()` 和 `authorize()` 必须来自同一策略定义，避免“能看列表，不能看详情”。

### 3.4 特殊资源不再独立成孤岛

`channel` 可以有特殊规则，但要纳入统一策略注册表，而不是永远挂在独立模块里自成体系。

### 3.5 渐进迁移

不能一次性改完全部 router。需要允许新旧实现短期并存，但新增或改造模块必须优先接入新策略层。

## 4. 统一策略层的目标结构

建议新增目录：

```text
backend/app/core/policy/
  __init__.py
  types.py
  context.py
  service.py
  registry.py
  helpers.py
  resources/
    __init__.py
    lead.py
    customer.py
    opportunity.py
    channel.py
    project.py
    contract.py
    follow_up.py
    work_order.py
    user.py
    product.py
```

各文件职责如下：

- `types.py`
  - 定义 `Action`、`Resource`、`PolicyDecision`
- `context.py`
  - 定义 `PrincipalContext`
- `service.py`
  - 对外提供统一调用入口
- `registry.py`
  - 维护资源到 policy 的注册关系
- `helpers.py`
  - 通用 owner/channel/work-order 关联判定工具
- `resources/*.py`
  - 每类资源一个 policy 文件

## 5. 核心模型

### 5.1 PrincipalContext

统一封装当前登录用户，替代在各处传裸 `dict`：

```python
@dataclass(slots=True)
class PrincipalContext:
    user_id: int
    role: str
    email: str | None = None
    name: str | None = None
```

说明：

- 现阶段保留和当前 `get_current_user()` 返回内容兼容
- 后续如果要加入部门、区域、岗位标签，可继续扩字段

### 5.2 Action

建议统一标准动作集合：

```python
Action = Literal[
    "list",
    "read",
    "create",
    "update",
    "delete",
    "manage",
]
```

说明：

- `list` 和 `read` 必须显式分开
- `manage` 用于渠道分配、预警规则、销售目标分解等管理类动作
- 如有必要可加 `export`、`approve`

### 5.3 Resource

建议显式注册资源名：

```python
Resource = Literal[
    "user",
    "customer",
    "lead",
    "opportunity",
    "project",
    "contract",
    "follow_up",
    "channel",
    "channel_assignment",
    "product",
    "work_order",
    "alert",
    "alert_rule",
    "sales_target",
    "operation_log",
]
```

## 6. 策略层统一接口

### 6.1 authorize

用于详情、更新、删除、管理类动作：

```python
await policy_service.authorize(
    resource="lead",
    action="read",
    principal=principal,
    db=db,
    obj=lead,
)
```

行为要求：

- 允许时返回 `None`
- 拒绝时统一抛 `HTTPException(403, ...)`
- 对象不存在仍由 router 负责抛 `404`

### 6.2 authorize_create

用于创建前校验，因为创建阶段通常还没有实体对象：

```python
await policy_service.authorize_create(
    resource="lead",
    principal=principal,
    db=db,
    payload=lead_create,
)
```

适用场景：

- `sales` 创建客户/线索/商机时，负责人必须是自己
- 创建合同时，需要校验所关联项目/渠道/客户是否可访问
- 创建渠道时，只允许 `admin/business`

### 6.3 scope_query

用于列表查询统一收口：

```python
query = await policy_service.scope_query(
    resource="lead",
    action="list",
    principal=principal,
    db=db,
    query=query,
    model=Lead,
)
```

行为要求：

- 所有列表接口一律先构造基础 query，再交给策略层加过滤条件
- 不能继续在 router 中写一套、策略层再写一套

### 6.4 can

用于非强制场景，例如前端能力透出、后端衍生字段：

```python
allowed = await policy_service.can(
    resource="channel",
    action="manage",
    principal=principal,
    db=db,
    obj=channel,
)
```

## 7. Policy 约定

每个资源 policy 至少实现三个方法：

```python
class LeadPolicy(BasePolicy):
    resource = "lead"

    async def scope_query(self, *, principal, db, query, model, action="list"):
        ...

    async def authorize(self, *, principal, db, action, obj):
        ...

    async def authorize_create(self, *, principal, db, payload):
        ...
```

统一要求：

- `scope_query` 与 `authorize(read)` 必须基于同一套规则来源
- 如果资源存在 owner 语义，应优先复用 helper
- 如果资源存在跨实体访问，应在 policy 内显式声明依赖来源

## 8. 通用 helper 能力

建议在 `helpers.py` 中沉淀以下通用判断，避免每个 policy 重复拼 SQL：

- `is_admin(principal)`
- `is_business(principal)`
- `is_sales(principal)`
- `is_finance(principal)`
- `is_technician(principal)`
- `owner_filter(model, principal.user_id)`
- `matches_owner(obj, principal.user_id)`
- `assigned_channel_ids(db, user_id, min_level=None)`
- `technician_work_order_ids(db, user_id)`
- `technician_related_lead_ids(db, user_id)`
- `technician_related_opportunity_ids(db, user_id)`
- `technician_related_project_ids(db, user_id)`
- `technician_related_channel_ids(db, user_id)`

注意：

- helper 只负责通用关系计算
- 最终是否允许某动作，仍由具体 resource policy 决定

## 9. 建议的资源策略表达

### 9.1 LeadPolicy

规则来源：

- `admin`、`business`：全量
- `sales`：自己负责
- `technician`：工单关联
- `finance`：无

创建规则：

- 仅 `admin/business/sales`
- `sales` 创建时 `sales_owner_id == principal.user_id`
- 如带 `channel_id` / `source_channel_id`，必须同时通过 channel policy 的 `read`

### 9.2 CustomerPolicy

规则来源：

- `admin`、`business`：全量
- `finance`：只读全量
- `sales`：`customer_owner_id == self`
- `technician`：工单关联客户

创建规则：

- 仅 `admin/business/sales`
- `sales` 创建时 `customer_owner_id == self`
- 如带 `channel_id`，需通过 channel policy 的 `read`

### 9.3 OpportunityPolicy

规则来源：

- `admin`、`business`：全量
- `sales`：自己负责
- `technician`：工单关联
- `finance`：无

### 9.4 ChannelPolicy

规则来源：

- `admin`、`business`：全量
- `sales`：依赖 `ChannelAssignment.permission_level`
- `technician`：依赖工单关联渠道
- `finance`：无

说明：

- `channel` 仍然是特殊资源
- 但特殊性应该体现在 `ChannelPolicy` 内，而不是继续保留一套平行权限系统

### 9.5 WorkOrderPolicy

规则来源：

- `admin`、`business`：全量
- `sales`：`submitter_id == self or related_sales_id == self`
- `technician`：被分配工单
- `finance`：无

### 9.6 ProductPolicy

规则来源：

- 所有登录角色可读
- 仅 `admin/business` 可创建、更新、删除

### 9.7 UserPolicy

规则来源：

- `admin`：全量读写删
- `business/finance`：活跃用户目录只读
- `sales`：默认仅自己；如筛选 `functional_role=TECHNICIAN`，允许读技术员候选
- `technician`：仅自己只读

说明：

- 这是一个典型“能力规则 + 额外上下文参数”资源
- `scope_query` 要允许接收附加参数，例如 `functional_role`

## 10. FastAPI 集成方式

建议新增统一依赖函数：

```python
def require_policy(resource: str, action: str):
    async def checker(
        current_user: dict = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
        obj = ...
    ):
        ...
```

但不建议第一阶段强推所有 router 都改成依赖注入式。

更稳妥的做法：

- 第一阶段：router 内直接调用 `policy_service`
- 第二阶段：对高复用、固定模式接口再抽成 `Depends`

推荐写法：

```python
principal = build_principal(current_user)
query = await policy_service.scope_query(
    resource="lead",
    action="list",
    principal=principal,
    db=db,
    query=query,
    model=Lead,
)
```

## 11. 与前端的关系

统一策略层的主要目标在后端，但应为前端留下标准化能力出口。

建议后续补一个能力接口：

```text
GET /auth/me/capabilities
```

返回形式示例：

```json
{
  "role": "sales",
  "capabilities": {
    "lead:create": true,
    "channel:create": false,
    "product:update": false
  }
}
```

这样前端菜单、按钮禁用、页面级分支都可以少写猜测逻辑。

当前阶段不要求先做这个接口，但策略层设计必须兼容它。

## 12. 迁移方案

### Phase 1: 建立骨架，不改行为

新增：

- `backend/app/core/policy/` 目录
- `PrincipalContext`
- `PolicyService`
- `registry`
- `BasePolicy`

此阶段不删除旧代码，只把基础设施搭起来。

### Phase 2: 先迁移四个高频业务资源

优先迁移：

- `lead`
- `customer`
- `opportunity`
- `channel`

原因：

- 权限规则最复杂
- 历史 bug 也主要集中在这些资源
- 这些资源彼此有关联，迁移后最容易立刻降低权限漂移

### Phase 3: 迁移工单链路

继续迁移：

- `work_order`
- `follow_up`
- `project`
- `contract`

原因：

- `technician` 权限边界主要在这一组实体上
- 当前很多“技术员可读范围”逻辑散落在多个模块

### Phase 4: 迁移系统型资源

迁移：

- `user`
- `product`
- `operation_log`
- `alert`
- `alert_rule`
- `sales_target`

### Phase 5: 删除旧入口

在全部关键 router 切换完成后，逐步废弃：

- `apply_data_scope_filter(...)`
- `assert_can_mutate_entity_v2(...)`
- `channel_permissions.py` 中的平行策略入口
- router 中重复的 `if role == ...`

## 13. 实施时的强约束

实施统一策略层时，必须遵守：

- 不改变任何 API 路径
- 不改变既有响应结构
- 不在迁移过程中扩大权限边界
- 每迁移一个资源，都要同时覆盖：
  - 列表
  - 详情
  - 创建
  - 更新
  - 删除
- 每迁移一个资源，都要补至少一组权限回归测试

## 14. 验收标准

统一策略层达到可用状态时，应满足：

- router 中大多数业务权限判断不再直接写角色分支
- 同一资源的 `list/read/create/update/delete` 权限定义位于同一个 policy 文件
- `channel` 权限已接入统一 registry
- 新增角色或新改权限时，只需改 policy 文件和文档，不需要在多处搜索
- 权限矩阵文档能和 policy 文件一一对应

## 15. 当前建议的首批落地范围

如果马上开始实施，建议第一批只做以下文件：

- `backend/app/core/policy/*`
- `backend/app/routers/lead.py`
- `backend/app/routers/customer.py`
- `backend/app/routers/opportunity.py`
- `backend/app/routers/channel.py`

这是最小但最有价值的一批。

完成这一步后，再把 [docs/role-system.md](/home/jian/crm-system/docs/role-system.md:1) 改成“角色矩阵文档”，并在每个资源条目下标注对应 policy 文件路径，形成文档和代码的双向映射。
