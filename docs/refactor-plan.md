# main.py 拆分 + 测试覆盖实施方案

> 状态：agent1 + agent3 联合定稿
> 日期：2026-04-17
> agent1 review 状态：✅ 已完成，意见已合并

---

## 一、现状

- `backend/app/main.py`：5693 行，92 个端点，76 个 class（含 43 个 Pydantic Schema）
- 已有 12 个独立 router 文件（渠道/派工/财务等），61 个端点已拆出
- 已有 12 个独立 schema 文件（schemas/ 目录）
- 测试：仅 2 个健康检查测试

---

## 二、拆分方案

### 2.1 Router 拆分（按业务域）

从 main.py 中提取以下 router，每个 router 对应一个独立文件：

| 序号 | Router 文件 | 端点前缀 | 端点数 | 行数(约) | 优先级 |
|------|------------|----------|--------|----------|--------|
| R1 | `routers/customer.py` | `/customers` CRUD | 5 | ~500 | P0 |
| R1b | `routers/customer_views.py` | `/customers/{id}/full-view`, `/customers/{id}/finance-view` | 2 | ~250 | P0 |
| R2 | `routers/lead.py` | `/leads` | 6+1(convert)+1(dispatch-history) | ~350 | P0 |
| R3 | `routers/opportunity.py` | `/opportunities` | 5 | ~250 | P0 |
| R4 | `routers/contract.py` | `/contracts` | 5 | ~300 | P0 |
| R5 | `routers/follow_up.py` | `/follow-ups` | 4 | ~400 | P1 |
| R6 | `routers/user.py` | `/users` | 4 | ~120 | P1 |
| R7 | `routers/auth.py` | `/auth/*` | 3 | ~100 | P1 |
| R8 | `routers/product.py` | `/products` | 4 | ~100 | P2 |
| R9 | `routers/dict_item.py` | `/dict/*` | 6 | ~200 | P2 |
| R10 | `routers/report.py` | `/reports/*` | 3 | ~300 | P1 |
| R11 | `routers/dashboard.py` | `/dashboard/*` | 6 | ~400 | P1 |
| R12 | `routers/alert.py` | `/alerts/*`, `/alert-rules/*` | 6 | ~180 | P2 |
| R13 | `routers/sales_target.py` | `/sales-targets/*` | 6 | ~250 | P2 |
| R14 | `routers/dispatch.py` | `/dispatch/*`, `/webhooks/dispatch`, `/dispatch-records/*` | 8 | ~350 | P1 |
| R15 | `routers/customer_channel_link.py` | `/customer-channel-links/*` | 4 | ~250 | P2 |

### 2.2 Schema 拆分

每个 router 对应一个 schema 文件（已有的复用）：

| Schema 文件 | 包含的 class | 状态 |
|------------|-------------|------|
| `schemas/customer.py` | CustomerBase/Create/Read | 新建 |
| `schemas/customer_view.py` | CustomerFullView | 新建 |
| `schemas/lead.py` | LeadBase/Create/Read/Update, LeadConvertRequest | 新建 |
| `schemas/opportunity.py` | OpportunityBase/Create/Read/Update | 新建 |
| `schemas/contract.py` | ContractBase/Create/Read/Update, ContractProduct*, PaymentPlan* | 新建 |
| `schemas/follow_up.py` | FollowUpBase/Create/Read/Update | 新建 |
| `schemas/auth.py` | UserLogin, Token, FeishuLogin* | 新建 |
| `schemas/product.py` | ProductBase/Create/Read/Update | 新建 |
| `schemas/dict_item.py` | DictItemCreate/Read/Update | 新建 |
| `schemas/operation_log.py` | OperationLogRead | 新建 |
| `schemas/report.py` | SalesFunnel*, Performance*, PaymentProgress* | 新建 |
| `schemas/dashboard.py` | DashboardSummary*, TodoItem, FollowUpItem, NotificationItem | 新建 |
| `schemas/alert.py` | AlertRule schemas (如有) | 新建 |
| `schemas/sales_target.py` | SalesTarget schemas (如有) | 新建 |
| `schemas/channel.py` | ChannelBase/Create/Read/Update, ChannelFullView | 已有，需补充 |
| `schemas/user.py` | UserCreate/Read/Update | 已有 |

### 2.3 拆分后 main.py 保留内容

- FastAPI app 实例创建 + 中间件配置
- CORS 配置
- Router 注册（app.include_router）
- 启动/关闭事件
- 预计缩减到 ~100 行

---

## 三、拆分执行顺序

### Phase 0（前置 - 消除循环依赖风险）
0. 统一基础设施：将 main.py 中的安全/认证逻辑合并到 `core/security.py` 和 `core/dependencies.py`
1. 消除重复 Schema：main.py 中的 UserCreate/UserRead 与 schemas/user.py 重复，Channel* 同理，先统一
2. 标记旧 router 需重写：`routers/projects.py`、`routers/financials.py`、`routers/opportunity_conversion.py` 是同步 Session 风格，需改为 async

### Phase 1（P0 - 核心业务，最大收益）
3. 创建 schema 文件：customer, customer_view, lead, opportunity, contract
4. 创建 router 文件：customer, customer_views, lead, opportunity, contract
5. 从 main.py 移除对应代码
6. 验证：后端启动 + API 测试

### Phase 2（P1 - 重要辅助）
7. 创建 schema + router：follow_up, user, auth, report, dashboard, dispatch
8. 合并渠道重复端点：main.py 中的 `/channels/check-credit-code` 和 `/channels/{id}/full-view` 并入 `routers/channel.py`
9. 从 main.py 移除对应代码
10. 验证

### Phase 3（P2 - 收尾）
11. 创建 schema + router：product, dict_item, alert, sales_target, customer_channel_link, operation_log
12. 从 main.py 移除对应代码
13. main.py 瘦身到 ~100 行（仅保留 app 初始化 + middleware + include_router + /health）
14. 全量验证

---

## 四、测试方案

### 4.1 测试框架
- 后端：pytest + httpx (AsyncClient) + pytest-asyncio
- 测试数据库：SQLite in-memory 或独立 PostgreSQL test db

### 4.2 测试层次

| 层次 | 覆盖范围 | 优先级 |
|------|---------|--------|
| API 端点测试 | 每个 router 的 CRUD 端点 | P0 |
| 权限测试 | 各角色访问控制 | P0 |
| 业务逻辑测试 | 线索转商机、合同签约触发、目标汇总 | P1 |
| 数据完整性测试 | 外键约束、级联删除、唯一索引 | P1 |
| 集成测试 | 跨模块流程（Lead→Opportunity→Project→Contract） | P2 |

### 4.3 测试文件结构
```
backend/tests/
├── conftest.py              # 测试配置、fixtures、测试数据库
├── test_auth.py             # 认证测试
├── test_customers.py        # 客户 CRUD + 权限
├── test_leads.py            # 线索 CRUD + 转化
├── test_opportunities.py    # 商机 CRUD
├── test_contracts.py        # 合同 CRUD
├── test_follow_ups.py       # 跟进记录
├── test_channels.py         # 渠道管理 + 权限
├── test_work_orders.py      # 工单
├── test_reports.py          # 报表
├── test_dashboard.py        # 仪表盘
├── test_permissions.py      # 权限矩阵
└── test_business_rules.py   # 业务规则
```

---

## 五、分工

| 阶段 | 负责 agent | 工作内容 |
|------|-----------|---------|
| 方案设计 | agent1 + agent3 (Claude) | 本文档 |
| 代码实施 | opencode | 按 Phase 1→2→3 拆分 + 编写测试 |
| 测试验证 | agent2 | 每个 Phase 完成后运行测试、验证 API |
| 复审 | agent1 + agent3 | 每个 Phase 完成后 review |

---

## 六、风险与注意事项

1. **循环导入**：Schema 和 Router 之间可能产生循环依赖，需确保 schema 不引用 router。Phase 0 先统一基础设施就是为了避免新 router 反向 import main.py
2. **共享依赖**：`get_current_user`、`get_db`、`operation_log_service` 等在多个 router 中使用，需从 `core/dependencies.py` 统一导入
3. **渠道端点重复**：main.py 中有 `/channels/check-credit-code` 和 `/channels/{id}/full-view`，与 `routers/channel.py` 冲突，Phase 2 合并
4. **前端无需改动**：拆分是纯后端重构，API 路径不变，前端不受影响
5. **每个 Phase 必须可独立验证**：拆一批验一批，不要一次性全拆
6. **响应结构回归风险**（agent1 发现）：很多接口手工拼 `customer_owner_name`、`terminal_customer_name`、`channel_name` 等字段，前端依赖这些名字，拆分时必须原样保留
7. **事务副作用必须原样保留**（agent1 发现）：客户创建时同步 CustomerChannelLink（main.py:893）、线索转商机（main.py:1702）、合同更新时重建 products/payment_plans 并刷新渠道绩效（main.py:2322）、派工 webhook 同时改 DispatchRecord 和 WorkOrder（main.py:5121）
8. **已有重复 Schema**（agent1 发现）：UserCreate/UserRead 在 main.py 和 schemas/user.py 各有一套，Channel* 也重复，Phase 0 先统一
9. **旧 router 风格不一致**（agent1 发现）：projects.py、financials.py、opportunity_conversion.py 是同步 Session 风格，需重写为 async 后再接入
10. **潜在缺陷**（agent1 发现）：`OPPORTUNITY_STAGE_TRANSITIONS` 在 main.py:1934 被引用但未定义；`/reports/performance` 在 main.py:3688 先 return 后有死代码，需首批测试覆盖
