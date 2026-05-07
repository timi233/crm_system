# 业绩管理体系重构设计文档

> **状态**: 设计草案（已补充审查约束）  
> **日期**: 2026-05-07  
> **涉及模块**: 销售目标管理 (Sales Target) & 实际业绩填报 (Actual Performance)

## 0. 审查结论与阻断项

本设计方向成立，但进入开发前必须先解决以下阻断项，否则实现会出现数据重复、汇总错误或迁移事故。

1. **实际业绩表名必须统一**：ORM、Alembic、schema、router 必须使用同一个表名。建议统一为 `actual_performances`，API 路径仍使用 `/actual-performance`。
2. **金额字段不得使用 `Float`**：目标金额、毛利目标、实际金额、实际毛利都应使用 `Numeric(14, 2)` 或以“分/元整数”存储，避免合计和阈值校验出现浮点误差。
3. **实际业绩必须定义唯一性**：同一 `user_id + year + month` 只能有一条实际业绩记录。重复填报按 upsert 处理，而不是插入多条。
4. **部分拆分规则必须替换旧逻辑**：现有“季度合计必须等于年度目标”和“季度自动均分到月份”的逻辑与本设计相反，需要在后端、前端和测试中同步重写。
5. **迁移不得默认清空生产数据**：清空 `sales_targets` 只能作为开发环境脚本，不能写进通用 Alembic 结构迁移。
6. **实际业绩写入不得信任请求体 `user_id`**：普通用户写入对象必须从登录态派生；admin 代填必须使用单独权限、审计日志和明确入口。
7. **报表口径必须固定**：季度/年度达成率优先使用父级设定目标，缺失父级目标时才使用子级目标合计；无目标但有实际时必须返回明确状态。
8. **审计日志必须与主操作同事务写入**：实际业绩新增、覆盖、修改、删除的审计失败时，主操作必须回滚。
9. **已落地错误迁移必须有补救路径**：如果环境中已存在 `actual_performance` 单数表或已执行清表迁移，必须先执行检测和补救迁移，再进入新版结构迁移。

## 1. 需求分析

### 1.1 现状痛点
- **单层结构**：当前仅有“年→季→月”的简单层级，缺乏业务深度。
- **指标单一**：仅支持“数字业绩”，无“毛利业绩”维度。
- **无实际达成**：系统只有目标值（Target），完全没有实际完成值（Actual），无法计算达成率。
- **数据死板**：月度目标由系统机械均分（÷3），无法根据实际业务节奏调整（如淡季/旺季）。

### 1.2 新需求要点
- **三维指标**：
  - **数字业绩**（Revenue Target/Actual）
  - **毛利业绩**（Gross Profit Target/Actual）
- **双向流动**：
  - **自上而下**：年度 → 季度 → 月度（目标设定）。
  - **自下而上**：月度 → 季度 → 年度（实际汇总）。
- **灵活拆分**：
  - 支持部分拆分（如年初只定 Q1，季初只定 1 月），未设定项默认视为 0。
  - 设定子级时，校验“子级之和 ≤ 父级”，超出父级则拦截。
  - 设定完成后，父级目标锁定，子级修改产生的差额以“未分配”形式提示。
- **实际录入**：
  - 仅**月度**可进行实际业绩填报（支持超额）。
  - 实际业绩可独立存在（无需先定目标再填数据）。

## 2. 设计架构与边界

### 2.1 拆分逻辑
- **部分拆分**：年度 100 万，若仅拆分 Q1=30 万，则 Q2~Q4 为 0，“未分配额度=70 万”。
- **父级锁定**：Q1 设定为 30 万后，无论后续将 1 月从 10 万改为 8 万还是 0 万，Q1 的“设定目标”保持 30 万不变。
  - 差异处理：系统显示“季度目标 30 万，当前明细汇总 28 万，差额 2 万”，仅做黄字提示，不阻断操作。
- **父级修改约束**：父级已有子级时，默认不允许把父级目标调低到低于子级合计；若需要修改父级目标，仍按 `sum(children) <= parent` 校验。
- **目标维度一致**：数字业绩与毛利业绩分别计算剩余额度，任一维度超出父级都应拦截。

### 2.2 实际业绩边界
- **录入自由度**：销售人员可以直接录入 5 月的实际业绩，即使 5 月的目标尚未被拆分出来。
- **汇总只读**：Q1 实际达成 = 1~3 月实际之和；年度实际达成 = 全年实际之和。这些值禁止直接修改，完全由底层数据决定。
- **超额不拦截**：实际业绩可以大于目标业绩（这是业务现实，不应拦截），仅在 UI 上展示“超额完成”。
- **填报语义**：同一用户同一年月再次提交实际业绩时执行 upsert，覆盖该月数值并更新 `updated_at`。
- **目标关联**：实际业绩以 `user_id/year/month` 为事实主键。`target_id` 只作为可选的月度目标引用，不参与唯一性判断；如果不存在月度目标，实际业绩仍可保存。
- **审计要求**：实际业绩每次新增、覆盖、修改、删除都必须写操作日志，记录操作者、目标用户、年月、修改前后值、修改原因和请求来源。
- **锁账期规则**：历史月份按“每月 5 日锁定上月及以前月份”的默认规则校验；锁定月份只能由具备 `actual_performance:override_locked_period` 权限的角色修改。
- **毛利约束**：默认要求 `gross_profit_target <= target_amount`、`gross_profit_actual <= amount_actual`；如业务出现负毛利或毛利高于营收的特殊场景，必须走单独异常流程，不纳入本期默认实现。

### 2.3 报表口径
- **目标口径**：月度报表使用月度目标；季度/年度报表优先使用对应父级设定目标，父级目标不存在时才使用子级目标合计，并分别返回 `amount_target_source`、`gross_profit_target_source` 字段。
- **明细口径**：`children_sum_amount` 与 `children_sum_gross_profit` 只表示已拆分明细合计，不替代父级设定目标。
- **缺失目标**：未拆分季度/月度在 API 中视为 0，并返回 `virtual: true`，前端展示为“未拆分”而不是“无数据”。
- **无目标但有实际**：当目标为 0 且实际大于 0 时，达成率返回 `null`，状态返回 `no_target_actual_exists`；聚合到季度/年度时，如果聚合目标总额仍为 0 且实际大于 0，同样返回该状态。
- **目标和实际均为 0**：达成率返回 `null`，状态返回 `no_activity`。
- **双指标状态**：数字业绩与毛利业绩分别返回 `amount_status`、`gross_profit_status`；行级 `overall_status` 仅用于摘要展示，目标缺失优先级最高：`no_target_actual_exists` > `exceeded` > `achieved` > `in_progress` > `no_activity`。
- **异常提示**：报表行额外返回 `warnings` 数组，例如 `["gross_profit_target_missing"]`、`["mixed_target_source"]`，用于提示缺目标、有实际、混合来源等治理问题。
- **多人聚合口径**：`group_user=false` 时先按用户和周期分别计算目标、实际、状态和来源，再汇总金额；聚合行必须返回 `target_source_summary`，说明各来源的用户数和金额，不能用单个 `target_source` 掩盖混合口径。

### 2.4 页面与角色路径

- **销售/业务个人填报页**：独立页面，调用 `/actual-performance/my` 和 `POST /actual-performance`，按年份展示本人 12 个月填报工作台。
- **个人 12 个月工作台**：个人填报页按年份固定展示 12 个月；未创建实际记录的月份也展示目标、实际 0、锁账状态、填报按钮和目标缺失状态，确保“无目标先填实际”有明确入口。
- **admin 自填/代填入口**：admin 可进入个人填报页填本人数据；具备 `actual_performance:write_for_others` 时额外显示代填管理页，无代填权限时隐藏代填入口。
- **admin 代填管理页**：独立管理入口，仅对 `actual_performance:write_for_others` 开放；必须先选择目标用户，再选择年月和金额，覆盖旧月份时二次确认并强制填写 `change_reason`。
- **finance/business 聚合报表页**：只读页面，调用 `/actual-performance/report`；finance 不能进入个人可编辑明细，business 可同时拥有个人填报页和聚合报表页。
- **删除/修改原因交互**：实际业绩修改和删除都必须弹出原因输入；新增可不填原因，覆盖、代填、修改、删除必须填写原因。
- **POST/PUT 边界**：空月份首次填报用 `POST /actual-performance`；已有记录编辑用 `PUT /actual-performance/{id}`；重复 `POST` 仅用于导入/快速填报场景，前端必须先检测已有记录、二次确认并提供 `change_reason`。
- **目标树展示**：`virtual=true` 展示“未拆分”，按钮为“设定/拆分”，点击后调用父级 `decompose` 创建真实节点；`virtual=false && amount=0` 展示“已设为 0”，按钮为“编辑/删除”；父级展示“设定目标、明细合计、明细差额”三项。

### 2.5 锁账期默认规则

- 默认锁账规则：每月 5 日 00:00 后锁定上月及更早月份；例如 2026-06-05 起锁定 2026 年 5 月及以前月份。
- 锁账校验覆盖 `POST /actual-performance`、`PUT /actual-performance/{id}`、`DELETE /actual-performance/{id}` 和 admin 代填。
- 普通用户修改锁定月份返回 403；具备 `actual_performance:override_locked_period` 的用户可覆盖锁账，但必须填写 `change_reason` 并写审计日志。
- 如果业务最终采用不同月结日期，只需调整配置项 `ACTUAL_PERFORMANCE_LOCK_DAY`，接口语义不变。

## 3. 数据模型设计 (ORM)

### 3.1 目标表扩表 (`sales_targets`)
在原表基础上增加毛利字段，保持结构扁平。
```python
from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy import Numeric

class SalesTarget(Base):
    __tablename__ = "sales_targets"
    __table_args__ = (
        CheckConstraint("target_type in ('yearly', 'quarterly', 'monthly')"),
        CheckConstraint("target_year >= 2000"),
        CheckConstraint(
            "(target_type = 'yearly' AND target_period = 1) OR "
            "(target_type = 'quarterly' AND target_period BETWEEN 1 AND 4) OR "
            "(target_type = 'monthly' AND target_period BETWEEN 1 AND 12)"
        ),
        CheckConstraint("target_amount >= 0"),
        CheckConstraint("gross_profit_target >= 0"),
        CheckConstraint("gross_profit_target <= target_amount"),
        UniqueConstraint("user_id", "target_type", "target_year", "target_period"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("sales_targets.id"), nullable=True)

    target_type = Column(String(20), nullable=False) # yearly, quarterly, monthly
    target_year = Column(Integer, nullable=False)
    target_period = Column(Integer, nullable=False)  # 1(Year) / 1-4(Quarter) / 1-12(Month)

    target_amount = Column(Numeric(14, 2), nullable=False, default=0)       # 数字业绩目标
    gross_profit_target = Column(Numeric(14, 2), nullable=False, default=0) # 毛利业绩目标

    created_at = Column(Date)
    updated_at = Column(Date)
```

层级约束由服务层强制：
- `yearly` 的 `target_period` 固定为 1，`parent_id` 必须为空。
- `quarterly` 的 `target_period` 必须为 1-4，`parent_id` 必须指向同一用户同一年的 `yearly`。
- `monthly` 的 `target_period` 必须为 1-12，`parent_id` 必须指向同一用户同一年的 `quarterly`，且月份必须落在该季度范围内。
- 子级创建或修改时，数字业绩和毛利业绩都必须满足 `sum(children) <= parent`。

### 3.2 新增实际表 (`actual_performances`)
独立表存储实际业绩，支持无目标状态下的数据先行录入。
```python
from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy import Numeric

class ActualPerformance(Base):
    __tablename__ = "actual_performances"
    __table_args__ = (
        CheckConstraint("year >= 2000"),
        CheckConstraint("month between 1 and 12"),
        CheckConstraint("amount_actual >= 0"),
        CheckConstraint("gross_profit_actual >= 0"),
        CheckConstraint("gross_profit_actual <= amount_actual"),
        UniqueConstraint("user_id", "year", "month", name="uq_actual_performance_user_month"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    target_id = Column(Integer, ForeignKey("sales_targets.id", ondelete="SET NULL"), nullable=True) # 可选关联月度目标

    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)

    amount_actual = Column(Numeric(14, 2), nullable=False, default=0)       # 数字业绩实际
    gross_profit_actual = Column(Numeric(14, 2), nullable=False, default=0) # 毛利业绩实际
    change_reason = Column(String(255), nullable=True)

    created_at = Column(Timestamp, default=func.now())
    updated_at = Column(Timestamp, default=func.now(), onupdate=func.now())
```

`target_id` 校验规则：
- 允许为空；为空时按 `user_id/year/month` 与目标表动态关联。
- 如果请求显式传入 `target_id`，后端必须校验该目标存在、`target_type='monthly'`、`user_id/year/month` 与实际业绩完全一致。
- 删除月度目标时，实际业绩保留，`target_id` 置空；报表仍按 `user_id/year/month` 汇总实际值。
- `target_id` 只是缓存引用，不是报表事实关联。报表永远按 `user_id/year/month` 动态查找目标；实际业绩先保存、后创建月度目标时，可以异步回填 `target_id`，但不得依赖回填结果计算报表。

### 3.3 实际业绩审计表 (`actual_performance_audit_logs`)

审计日志独立落表，不复用主表当前态字段。主操作和审计写入必须在同一事务内完成；审计写入失败时，主操作回滚。

```python
class ActualPerformanceAuditLog(Base):
    __tablename__ = "actual_performance_audit_logs"

    id = Column(Integer, primary_key=True)
    actual_performance_id = Column(Integer, ForeignKey("actual_performances.id", ondelete="SET NULL"), nullable=True, index=True)
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    target_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(20), nullable=False) # create, update, upsert_update, delete
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    before_values = Column(JSON, nullable=True)
    after_values = Column(JSON, nullable=True)
    change_reason = Column(String(255), nullable=False)
    request_source = Column(String(50), nullable=False) # web, api, system
    created_at = Column(Timestamp, default=func.now(), nullable=False)
```

审计规则：
- 新增记录：`before_values=null`，`after_values` 为新值；普通本人首次填报可用默认原因 `initial_submit`。
- 覆盖记录：`before_values` 和 `after_values` 都必须记录，`change_reason` 必填。
- 修改记录：只允许修改金额、毛利、原因；记录修改前后值。
- 删除记录：`before_values` 记录删除前完整值，`after_values=null`。
- 审计日志只允许追加，不提供更新和删除接口。
- `before_values`、`after_values` 中的金额必须用字符串序列化，例如 `"120000.00"`，不得使用 JSON number 表示 Decimal。
- 审计表只授予 INSERT/SELECT 权限，不授予 UPDATE/DELETE 权限；如数据库权限无法细化，应用层必须拒绝任何审计更新/删除路径。

## 4. 业务规则

| 维度 | 规则说明 | 异常处理 |
|------|---------|----------|
| **目标校验** | `sum(children) <= parent_amount` | 超过父级目标时，返回 400 错误，提示“超出可分配额度” |
| **毛利目标校验** | `sum(children.gross_profit_target) <= parent.gross_profit_target` | 超过父级毛利目标时，返回 400 错误 |
| **未分配提示** | `parent_amount - sum(children)` 和 `parent_gross_profit - sum(children)` | API 返回 `remaining_amount`、`remaining_gross_profit` 字段供前端展示 |
| **月度修改** | 修改 `target_amount` 或 `gross_profit_target` | 检查兄弟节点之和是否超出父级，若超出则拒绝 |
| **超额完成** | `actual > target` | 允许。API 正常保存，前端通过颜色区分（绿/红） |
| **重复填报** | 同一用户同一年月再次提交实际业绩 | 执行 upsert，覆盖原记录 |
| **月度删除** | `DELETE /actual-performance/{id}` | 季度/年度汇总值自动减少，保持数据一致性 |
| **目标删除** | 删除月度目标 | 保留实际业绩，`target_id` 置空 |
| **实际修改** | `PUT /actual-performance/{id}` | 不允许修改 `user_id/year/month`，只允许修改金额、毛利、备注/原因 |
| **并发拆分** | 多请求同时拆分同一父级 | 必须在事务内锁定父级和兄弟节点，提交前重新校验剩余额度 |
| **并发填报** | 多请求同时 upsert 同一用户年月 | 使用数据库原子 upsert，返回最终记录，不把唯一冲突作为正常 409 路径 |
| **毛利约束** | 毛利目标/实际不得大于对应营收 | 违反时返回 400 |
| **虚拟节点** | `virtual=true` 的目标节点 | 不允许删除或直接更新，必须通过父级分解接口创建真实节点 |
| **父级目标删除** | 删除年度/季度目标 | 有子节点时拒绝删除；无子节点时允许删除并重算上级 remaining |

### 4.1 事务与并发控制

- 创建、更新、删除目标节点时，必须在一个数据库事务内完成读取父级、读取兄弟节点、校验剩余额度和写入。
- 拆分子级时必须锁定父级记录；数据库支持时使用 `SELECT ... FOR UPDATE`，同时锁定同一父级下的兄弟节点。
- 实际业绩 upsert 必须使用数据库原子 upsert，以 `user_id/year/month` 唯一约束为最终保护；成功后返回最终记录和 `operation` 字段。
- upsert 实现必须先判断是否存在旧记录或使用带条件的原子语句，确保覆盖旧记录时若缺少 `change_reason` 直接返回 422，不能先覆盖再校验。
- 所有金额比较使用 `Decimal`，不得在业务规则中把 `Numeric` 转成 `float` 后比较。
- 目标层级完整性除服务层校验外，还必须提供迁移后的数据校验脚本，检查跨用户父子、跨年份父子、月度挂错季度、孤儿节点和重复节点；校验失败时阻断部署。

## 5. 权限矩阵

| 角色 | 目标制定/拆分 | 实际业绩填报 | 数据可见范围 |
|------|-------------|-------------|-------------|
| **admin** | ✅ 全局管理 | ✅ 可填报自己的 | 全局可见 |
| **sales** | ❌ 禁止 | ✅ 仅可填报自己的 | 本人可见 |
| **business** | ❌ 禁止 | ✅ 仅可填报自己的 | 本模块本人可见；若沿用全量报表权限，仅限聚合报表 |
| **finance** | ❌ 禁止 | ❌ 禁止 | 仅看汇总报表 |

实现要求：
- 新增/补齐 `SalesTargetPolicy` capability：`sales_target:read`、`sales_target:create`、`sales_target:update`、`sales_target:delete`、`sales_target:decompose`。
- 销售目标写接口仅 admin 可用；sales、business、finance 调用目标创建、更新、分解、删除接口统一返回 403。读接口按现有策略：admin 全量，sales/business 本人，finance 汇总报表只读。
- 新增 `ActualPerformancePolicy`，不要复用 `SalesTargetPolicy`。
- 新增 capability：`actual_performance:read`、`actual_performance:create`、`actual_performance:update`、`actual_performance:delete`、`actual_performance:write_for_others`、`actual_performance:override_locked_period`、`actual_performance:report_read`。
- `admin` 可读取全量实际业绩，但普通填报只能默认写自己的记录；如需代填，必须单独定义 `actual_performance:write_for_others`。
- `finance` 只能访问聚合报表接口，不应访问个人填报的写接口。
- 普通用户提交实际业绩时，请求体中的 `user_id` 必须被忽略或拒绝；后端使用当前登录用户 id 作为写入对象。
- 具备 `actual_performance:write_for_others` 时才允许传入 `user_id` 为他人代填，并强制填写 `change_reason`。
- `business` 角色在现有系统中可能拥有较高报表权限。本模块若需要保留该权限，只允许其访问聚合报表，不允许访问他人可编辑明细。

默认授权建议：

| capability | admin | sales | business | finance |
|------------|-------|-------|----------|---------|
| `actual_performance:read` | 全量 | 本人 | 本人 | 禁止 |
| `actual_performance:create` | 本人 | 本人 | 本人 | 禁止 |
| `actual_performance:update` | 本人 | 本人 | 本人 | 禁止 |
| `actual_performance:delete` | 本人 | 本人 | 本人 | 禁止 |
| `actual_performance:write_for_others` | 可配置 | 禁止 | 禁止 | 禁止 |
| `actual_performance:override_locked_period` | 可配置 | 禁止 | 禁止 | 禁止 |
| `actual_performance:report_read` | 全量 | 本人聚合 | 全量聚合 | 全量聚合 |

目标管理默认授权建议：

| capability | admin | sales | business | finance |
|------------|-------|-------|----------|---------|
| `sales_target:read` | 全量 | 本人 | 本人 | 汇总只读 |
| `sales_target:create` | 全量 | 禁止 | 禁止 | 禁止 |
| `sales_target:update` | 全量 | 禁止 | 禁止 | 禁止 |
| `sales_target:delete` | 全量 | 禁止 | 禁止 | 禁止 |
| `sales_target:decompose` | 全量 | 禁止 | 禁止 | 禁止 |

## 6. 数据流向示意

```text
        【目标设定层】自上而下逐级拆分（可部分拆分，未拆分=0）                      【实际填报层】自下而上逐月汇总
                                                                                   （仅月度可填，可超额）

  2026年度 (admin设定)                                                       2026年度
  ───────────────                                                            ───────────────
  数字业绩: 100万 ◄────╮                                                     实际完成: 105.2万 ─
  剩余未分配: 10万     │                                                     实际毛利:  21.1万 ─┤
                       │                                                     超额完成状态：✨达标
  毛利业绩:  20万 ◄────
                                                                                │
                                                                                ▼
           │                                           ┌───────────────────────────────┐
           ▼                                           │        Q1 季度 (年初拆分)      │
  Q1 季度 (30万)  │ Q2 季度 (0)  ...                    │                               │
                  │                                     │  目标设定 (锁定): 30万         │
                  │                                     │  明细差额:    2万              │
           │                                           └──────────────┬────────────────
           │                                                           │ (汇总=月度实际之和)
           ▼                                                           ▼
  Q1: 1月 (10万)  │ 2月 (8万)  │ 3月 (10万)             1月 (12万)    │ 2月 (10万)    │ 3月 (10万)
                  │            │                        ── 实际填报 ──►│─ 实际填报 ──►│─ 实际填报 ──►
                  │            │                        (用户自由录入) │(可超额)      │(可超额)
                  │            │                                       │             │
                  │            │                                       ▼             ▼             ▼
  Q1 汇总目标: 28万                                           Q1 实际: 32万 (超额 2万)
  Q1 设定目标: 30万 (不变)                                    Q1 实际毛利: 6.3 万
```

## 7. API 规划

### 7.1 目标管理 (SalesTarget)
- `PUT /sales-targets/year`：创建/更新年度目标（含毛利）。
- `POST /sales-targets/{target_id}/decompose`：按父节点类型分解子节点。`yearly` 只能拆 `quarterly`，`quarterly` 只能拆 `monthly`，不允许跨级拆分。
- `PUT /sales-targets/{id}`：允许局部修改子节点。新增校验：兄弟之和不得大于父节点。
- `GET /sales-targets/{id}`：返回结构树，新增 `remaining_amount`、`remaining_gross_profit`。
- `DELETE /sales-targets/{id}`：删除真实目标节点；虚拟节点不可删除，有子节点的年度/季度目标不可删除。

分解父子类型矩阵：

| 父级类型 | 允许 `children_type` | 合法 period | 说明 |
|----------|----------------------|-------------|------|
| yearly | quarterly | 1-4 | 创建或更新季度目标，未出现季度以虚拟 0 节点返回 |
| quarterly | monthly | 该季度对应的 3 个月 | 创建或更新月度目标，未出现月份以虚拟 0 节点返回 |
| monthly | 无 | 无 | 月度目标不可继续拆分 |

分解请求语义：
- `items` 使用 patch 语义：只创建或更新请求中出现的 period。
- 数据库中已存在但本次未出现在 `items` 中的子节点必须保留原值，不得置 0、不得删除。
- 数据库中不存在且本次未出现在 `items` 中的 period 在响应树中以 `virtual=true`、金额 0 返回。
- 如需把真实节点金额改为 0，必须显式提交该 period 且金额为 0；此时返回 `virtual=false`。
- 删除真实节点必须调用 `DELETE /sales-targets/{id}`，不得通过省略 `items` 完成。

目标节点删除规则：
- 虚拟节点没有数据库 id，不提供删除操作。
- 年度/季度目标存在子节点时返回 400，提示先处理下级目标。
- 删除月度目标时，已有实际业绩保留，`target_id` 置空；报表后续按 `user_id/year/month` 动态关联目标。
- 删除真实 0 目标后，该 period 在树中重新显示为 `virtual=true` 的未拆分节点。

目标创建/更新请求示例：
```json
{
  "user_id": 2,
  "target_year": 2026,
  "target_amount": "1000000.00",
  "gross_profit_target": "200000.00"
}
```

分解请求示例：
```json
{
  "children_type": "quarterly",
  "items": [
    {"period": 1, "target_amount": "300000.00", "gross_profit_target": "60000.00"},
    {"period": 2, "target_amount": "0.00", "gross_profit_target": "0.00"}
  ]
}
```

响应中必须包含：
```json
{
  "remaining_amount": "700000.00",
  "remaining_gross_profit": "140000.00",
  "children_sum_amount": "300000.00",
  "children_sum_gross_profit": "60000.00",
  "children": [
    {"period": 1, "target_amount": "300000.00", "gross_profit_target": "60000.00", "virtual": false},
    {"period": 2, "target_amount": "0.00", "gross_profit_target": "0.00", "virtual": false},
    {"period": 3, "target_amount": "0.00", "gross_profit_target": "0.00", "virtual": true},
    {"period": 4, "target_amount": "0.00", "gross_profit_target": "0.00", "virtual": true}
  ]
}
```

### 7.2 实际业绩 (ActualPerformance)
- `GET /actual-performance/my`：当前用户个人月度填报记录，用于可编辑列表。
- `GET /actual-performance/report`：聚合报表查询，支持按年/季/月聚合。finance/business 的全量视图只能访问该接口。
- `POST /actual-performance`：新增或覆盖月度填报（upsert）。
- `PUT /actual-performance/{id}`：修改实际数据。
- `DELETE /actual-performance/{id}`：删除实际数据。

写接口语义：
- `POST /actual-performance` 使用数据库原子 upsert。首次创建返回 HTTP 201，覆盖旧记录返回 HTTP 200。
- 响应必须包含 `operation: "created" | "updated"` 和最终记录。
- 覆盖旧记录、代填、修改、删除必须提供 `change_reason`；本人首次创建可省略，后端写入默认原因 `initial_submit`。
- `PUT /actual-performance/{id}` 的请求 schema 必须禁止额外字段；传入 `user_id/year/month/target_id` 等不可变字段时返回 400。
- `POST /actual-performance` 请求允许可选 `target_id`；若传入必须通过同用户、同年月、月度目标校验。普通用户不允许传入 `user_id`。
- 删除实际业绩统一使用 `DELETE /actual-performance/{id}`，`change_reason` 放在 JSON request body 中，并写入审计日志。

错误响应结构：
```json
{
  "code": "VALIDATION_ERROR",
  "message": "change_reason is required",
  "details": {"field": "change_reason"}
}
```

状态码约定：
- `401`：未认证或登录态失效。
- `403`：已认证但无权限，例如访问他人明细、锁账期无 override 权限、非 admin 写目标。
- `404`：资源不存在，或当前用户无权知道该资源是否存在时可隐藏为 404。
- `409`：非 upsert 路径的唯一键冲突或迁移/并发异常；`POST /actual-performance` 正常重复填报不得返回 409。
- `422`：请求体结构错误、缺少必填字段或 schema 禁止的额外字段。
- `400`：业务规则错误，例如超出父级目标、毛利大于营收、非法 period。

实际业绩填报请求示例：
```json
{
  "year": 2026,
  "month": 5,
  "amount_actual": "120000.00",
  "gross_profit_actual": "26000.00",
  "change_reason": "月度回款确认"
}
```

代填请求示例（仅 `actual_performance:write_for_others`）：
```json
{
  "user_id": 2,
  "year": 2026,
  "month": 5,
  "amount_actual": "120000.00",
  "gross_profit_actual": "26000.00",
  "change_reason": "管理员代填"
}
```

汇总查询要求：
- 查询参数：`year` 必填；`group_by=month|quarter|year`；`quarter`、`month` 按 `group_by` 可选；`user_id` 仅 admin 或 report 全量权限可用；`group_user=true|false` 控制是否按人员分组；`page/page_size/sort` 用于人员分组列表。
- `group_user=true` 时分页对象为“用户 x period”行；`group_user=false` 时返回按 period 汇总的聚合行，不返回个人可编辑记录 id。
- 数据范围：sales 只能查本人聚合；business、finance 查全量聚合但不返回记录 id；admin 查全量聚合，可按 `user_id` 过滤。
- `group_by=month` 返回每月目标、实际、毛利目标、毛利实际、达成率、毛利达成率。
- `group_by=quarter` 按 1-3、4-6、7-9、10-12 汇总月度实际，不允许直接存季度实际。
- `group_by=year` 汇总 12 个月实际，不允许直接存年度实际。
- 达成率在目标为 0 且实际大于 0 时返回 `null` 和状态 `no_target_actual_exists`，不得除以 0。
- 查询结果必须分别返回 `amount_target_source`、`gross_profit_target_source`：`monthly_target`、`parent_target`、`children_sum`、`virtual_zero`。
- 多人聚合行必须返回 `target_source_summary`，按指标和来源列出金额与用户数。
- finance 访问报表时默认返回聚合结果；按人员维度分组时只返回用户维度汇总，不返回可编辑记录 id。

报表响应单行结构：
```json
{
  "period": "2026-Q1",
  "user_id": 2,
  "user_name": "张三",
  "target_amount": "300000.00",
  "amount_actual": "320000.00",
  "amount_achievement_rate": "1.0667",
  "amount_status": "exceeded",
  "gross_profit_target": "60000.00",
  "gross_profit_actual": "63000.00",
  "gross_profit_achievement_rate": "1.0500",
  "gross_profit_status": "exceeded",
  "overall_status": "exceeded",
  "amount_target_source": "parent_target",
  "gross_profit_target_source": "parent_target",
  "target_source_summary": {
    "amount": {"parent_target": {"users": 1, "amount": "300000.00"}},
    "gross_profit": {"parent_target": {"users": 1, "amount": "60000.00"}}
  },
  "actual_source": "monthly_sum",
  "warnings": []
}
```

状态枚举：
- `exceeded`：实际大于目标。
- `achieved`：实际等于目标且目标大于 0。
- `in_progress`：实际小于目标且目标大于 0。
- `no_target_actual_exists`：目标为 0 且实际大于 0。
- `no_activity`：目标和实际都为 0。

## 8. 现有实现改造清单

当前代码中已有若干逻辑与本设计冲突，开发时必须同步调整：

1. 后端 `/sales-targets/{id}/decompose-quarterly` 需要替换为支持部分拆分的 `/sales-targets/{id}/decompose`。
2. 后端“季度合计必须等于年度目标”的校验需要改为“不得超过父级目标”。
3. 后端“季度自动均分到月份”的逻辑需要删除，月份目标必须由显式月度拆分创建。
4. 前端季度拆分表单不能再要求四个季度都大于 0，也不能要求合计等于年度目标。
5. `SalesTargetCreate`、`SalesTargetUpdate`、`SalesTargetRead` schema 必须加入 `gross_profit_target`。
6. 新增 `ActualPerformance` schema、router、policy、测试和前端入口。
7. Dashboard/报表中所有目标达成率需要接入实际业绩汇总，而不是只读取目标表。
8. 将现有 `sales_targets.target_amount` 及新增金额字段统一改为 `Numeric(14, 2)`，schema 使用 Decimal。
9. 前端目标树需要展示虚拟 0 节点、父级设定目标、明细合计和差额提示。
10. 前端实际业绩入口按角色拆分：个人填报页使用 `/actual-performance/my`，财务/管理报表使用 `/actual-performance/report`。
11. 新增实际业绩审计日志模型和写入逻辑，所有写操作与审计同事务提交。
12. 新增目标层级完整性校验脚本，作为迁移后和部署前检查项。

## 9. 迁移策略

1. Alembic 结构迁移只负责新增字段、调整字段类型、创建或修正 `actual_performances` 表和唯一索引，不得清空 `sales_targets`。
2. 开发环境如需重建目标数据，单独提供显式脚本，例如 `scripts/reset_sales_targets_dev.py`，并在脚本内检查环境变量。
3. 生产环境迁移时保留旧目标数据，新增 `gross_profit_target` 默认 0。
4. 对已有自动均分月度目标，需要单独评估是否保留为历史目标；不得在迁移中静默删除。
5. 如果历史数据存在重复年度/季度/月度目标，迁移前先输出冲突报告，由业务确认清洗策略。
6. 迁移必须把 `sales_targets.target_amount` 从浮点类型转换为 `Numeric(14, 2)`，并新增 `sales_targets(user_id, target_type, target_year, target_period)` 唯一约束。
7. 迁移必须为 `target_type`、`target_year`、`target_period`、`target_amount`、`gross_profit_target`、`actual_performances.year`、`actual_performances.month`、实际金额字段设置 `NOT NULL`。
8. 创建 `actual_performances(user_id, year, month)` 唯一约束前，必须先检查并报告重复数据。
9. 如果数据库已存在旧表 `actual_performance`，迁移必须先检测是否有数据；有数据则迁移到 `actual_performances`，无数据可重命名或删除旧表。
10. 如果错误迁移 revision 已经在环境中执行，后续迁移不得再次清空 `sales_targets`，必须通过补救 revision 修正表名、字段类型和约束。
11. Float 到 `Numeric(14, 2)` 的转换使用四舍五入到 2 位小数；NULL 金额转换为 0；负数、超出 `Numeric(14, 2)` 上限、重复唯一键、非法层级必须生成阻断报告并停止迁移。
12. 迁移后运行目标层级校验脚本，检查 yearly/quarterly/monthly 父子类型、同用户同年份、月份落季度范围、孤儿节点和重复节点。
13. 实际业绩表迁移必须做三态检测：
    - 无 `actual_performance`/`actual_performances` 表：直接创建目标结构。
    - 存在旧单数表 `actual_performance`：复制或重命名到 `actual_performances`，再补字段类型、NOT NULL、check、唯一约束和索引。
    - 已存在复数表 `actual_performances` 但结构错误：执行 `ALTER/backfill`，把 Float/nullable/缺约束结构修正到目标结构，不得直接建表失败。
14. `sales_targets` 迁移必须增加 period/type 组合 check：yearly 仅 period=1，quarterly 为 1-4，monthly 为 1-12。跨用户/跨年份父子、月度挂错季度等无法用简单 check 表达的规则，由部署前阻断脚本强制校验。

## 10. 测试验收清单

1. 年度目标 100 万，只拆 Q1=30 万成功，remaining=70 万。
2. 年度目标 100 万，拆 Q1=120 万失败。
3. Q1 30 万，只拆 1 月=10 万、2 月=8 万成功，Q1 设定目标保持 30 万，明细差额为 12 万。
4. 修改 2 月目标导致 1-3 月合计超过 Q1 时失败。
5. 未创建 5 月目标时，销售人员可填报 5 月实际业绩。
6. 同一销售同一年月重复填报时覆盖旧记录，不产生重复汇总。
7. 实际业绩超过目标时保存成功，报表展示超额状态。
8. 删除月度实际业绩后，季度和年度汇总同步减少。
9. 删除月度目标后，已有实际业绩保留且仍参与汇总。
10. finance 只能查看聚合报表，不能创建、修改、删除实际业绩。
11. 普通用户提交他人 `user_id` 时被拒绝或忽略，最终只能写入本人记录。
12. 无代填权限的 admin 不能为他人写入实际业绩；有代填权限时必须填写 `change_reason`。
13. 显式传入跨用户、跨年月或非月度目标的 `target_id` 时返回 400。
14. 两个并发拆分请求不能让子级合计超过父级目标。
15. 两个并发 upsert 同一用户年月不能产生重复记录。
16. GET 目标树返回未拆分季度/月度的虚拟 0 节点，并标记 `virtual: true`。
17. 季度报表在父级目标 30 万、月度明细合计 28 万时，达成率使用父级设定目标，并返回 `amount_target_source=parent_target`。
18. 目标为 0 且实际为 0 时返回 `status=no_activity`；目标为 0 且实际大于 0 时返回 `status=no_target_actual_exists`。
19. finance 调用个人明细接口返回 403，只能访问聚合报表接口。
20. `PUT /actual-performance/{id}` 修改 `user_id/year/month` 时返回 400。
21. 实际业绩新增、覆盖、修改、删除均写入审计日志；审计写入失败时主操作回滚。
22. `POST /actual-performance` 首次创建返回 201 和 `operation=created`，重复填报返回 200 和 `operation=updated`。
23. 覆盖、代填、修改、删除未提供 `change_reason` 时返回 422。
24. 锁定月份普通用户修改返回 403；具备 `actual_performance:override_locked_period` 时允许修改并写审计。
25. Decimal 精度校验：0.01 边界合计不产生浮点误差，金额比较不使用 float。
26. `gross_profit_target > target_amount` 或 `gross_profit_actual > amount_actual` 时返回 400。
27. 删除有子节点的年度/季度目标返回 400；删除虚拟节点不可用；删除真实 0 目标后重新显示为虚拟未拆分节点。
28. 报表接口返回 `amount_status`、`gross_profit_status`、`overall_status`、`amount_target_source`、`gross_profit_target_source`、`target_source_summary`，并支持 `group_user=true` 的人员聚合。
29. 已存在旧表 `actual_performance` 的环境可通过补救迁移迁到 `actual_performances`，且不清空 `sales_targets`。
30. `decompose` 使用 patch 语义：省略已有子节点不会置 0 或删除；显式提交 0 才把真实节点设为 0。
31. 非 admin 调用销售目标创建、更新、分解、删除接口返回 403。
32. 个人填报页按年份返回 12 个月工作台，未填月份也有填报入口并展示锁账状态。
33. `DELETE /actual-performance/{id}` 必须从 request body 接收 `change_reason`；旧的无 id 删除路径不可用。
34. 多人聚合报表混用目标来源时返回 `target_source_summary` 和 `warnings=["mixed_target_source"]`。
35. 已存在结构错误的复数表 `actual_performances` 可通过补救迁移修正字段类型、NOT NULL、check 和唯一约束。

## 11. 待决策项

1. **数据初始化**：旧系统中的季度均分数据需要迁移清洗吗？（建议：开发环境直接 truncate tables 重建）。
2. **财务数据同步**：毛利业绩目前是手动填报，未来是否对接财务系统自动拉取？（预留字段接口，目前按手动处理）。
3. **锁账期配置值**：默认每月 5 日锁定上月及以前月份，是否需要按客户月结日调整 `ACTUAL_PERFORMANCE_LOCK_DAY`。
