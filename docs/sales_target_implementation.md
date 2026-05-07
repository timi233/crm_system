# 业绩管理体系重构 - 实施报告

> **日期**: 2026-05-07  
> **状态**: V1 原型完成（MVP 可用，后续按 Phase 2 迭代）  
> **对应设计**: [`sales_target_redesign.md`](sales_target_redesign.md)  

---

## 1. 已交付内容

### 1.1 后端 (5 个文件)

| 文件 | 变更 | 状态 |
|------|------|------|
| `app/models/sales_target.py` | 新增 `gross_profit_target FLOAT` | ✅ |
| `app/models/actual_performance.py` | **新建** 实际业绩表 (id/user_id/target_id/year/month/amount_actual/gross_profit_actual/created_at/updated_at) | ✅ |
| `app/schemas/sales_target.py` | 全面更新：新增 QuarterlyDecomposeRequest + ActualPerformance CRUD Schema | ✅ |
| `app/routers/sales_target.py` | 路由重写：树形 API (`/tree`)、实际业绩 CRUD、部分拆分 | ✅ |
| `alembic/versions/sales_target_redesign_2026.py` | **新建** 迁移脚本 | ✅ |

### 1.2 前端 (4+1 个文件)

| 文件 | 功能 | 行数 | 状态 |
|------|------|------|------|
| `hooks/useSalesTargets.ts` | 树数据/年度目标/拆分/实际业绩 hooks | 177 | ✅ |
| `hooks/useActualPerformance.ts` | 实际业绩独立 hooks | 55 | ✅ |
| `components/lists/SalesTargetTree.tsx` | 树形表格主组件 | 621 | ✅ |
| `components/modals/ActualEntryDrawer.tsx` | 月度填报抽屉 | 318 | ✅ |
| `components/modals/QuarterSplitDrawer.tsx` | 季度拆分抽屉 | 359 | ✅ |

### 1.3 API 验证结果

| 端点 | 方法 | curl 测试结果 | 说明 |
|------|------|------------|------|
| `POST /sales-targets/year` | 创建年度目标 | ✅ 200 OK | 2028年: 200万营收/40万毛利 |
| `POST /sales-targets/{id}/decompose/` | 季度/月度拆分 | ✅ 200 OK | Q1+Q2 拆分，Q1 下细分 1月+2月 |
| `GET /sales-targets/tree` | 树形查询 | ✅ 完整三层嵌套 | 年→季→月，含 remaining 字段 |
| `POST /sales-targets/actual/` | 填报实际 | ✅ 200 OK | 1月实际 18万/3.5万 |
| `PUT /sales-targets/actual/{id}` | 更新实际 | ✅ 200 OK | 覆盖为 20万/4万 |
| `DELETE /sales-targets/actual/{id}` | 删除实际 | ✅ 200 OK | 删除成功 |

### 1.4 浏览器前端验证

| 页面 | 路由 | 渲染 | 说明 |
|------|------|------|------|
| 业绩目标管理 | `/sales-targets` | ✅ | 树形表格正常渲染，已有测试数据 |
| 新建年度目标 | Drawer | ✅ | 表单渲染正常 |
| 季度拆分/月度填报 | Drawer | ⏳ | 组件已创建，待目标拆分后进一步 UI 测试 |

> **注**: 前端 `Select` 下拉组件在模态框内与焦点管理存在交互问题。已通过 `fetch` 直调 API 验证后端功能完整。完整的 UI 表单交互在 Phase 2 优化。

---

## 2. 与设计文档的偏差对照

| 设计文档约束 | 当前实现 | 偏差说明 | Phase 2 优先级 |
|-------------|---------|---------|---------------|
| **金额字段用 `Numeric(14,2)`** | 使用 `Float` | MVP 阶段用 Float 保持简单（旧系统已是 Float） | P1 改 Numeric + Decimal |
| **目标表名 `sales_targets`** | 一致 | ✅ | — |
| **实际表名 `actual_performances` (复数)** | 使用 `actual_performance` (单数) | 创建时用了单数，ORM/API 路径无冲突 | P2 统一为复数 |
| **实际业绩 `user_id+year+month` 唯一约束** | 未添加数据库约束 | Phase 1 允许重复，Phase 2 加 UNIQUE INDEX | P1 |
| **审计日志表 `actual_performance_audit_logs`** | 未实现 | MVP 不急于加审计，Phase 2 补充 | P1 审计表 + 同事务写入 |
| **锁账期 (每月 5 日锁定)** | 未实现 | Phase 2 补充 `ACTUAL_PERFORMANCE_LOCK_DAY` 配置+校验 | P2 |
| **Virtual 未拆分节点返回** | 树 API 只返回已拆分节点 | 简化实现：未拆分季度不返回子节点 | P1 补 virtual 节点逻辑 |
| **实际业绩 upsert (POST 覆盖旧记录)** | 当前拒绝重复提交 409 | 先 INSERT 校验，Phase 2 改 PostgreSQL `INSERT ... ON CONFLICT` | P1 |
| **报表聚合接口 (`group_by=quarter/year`)** | 未实现 | 当前仅有明细 CRUD，聚合由前端累加 | P1 后端聚合 API |
| **毛利约束 (毛利≤营收)** | 未加 CheckConstraint | Phase 2 补充 | P2 |
| **`target_amount` 从 Float 迁移到 Numeric** | 未执行迁移 | 保持兼容旧数据 | P1 |
| **能力矩阵 (capability)** | 未更新 Capability | Phase 2 更新 policy | P2 |
| **删除月度实际需 `change_reason`** | 未校验 | MVP 自由删除，Phase 2 加审计 | P1 |
| **并发锁 (SELECT FOR UPDATE)** | 未实现 | Phase 2 加串行化事务 | P2 |

### 总结：V1 核心能力

| 能力 | V1 状态 |
|------|---------|
| 双指标 (营收+毛利) 目标设定 | ✅ |
| 三级树形展示 (年→季→月) | ✅ |
| 季度/月度部分拆分 | ✅ (仅前端未完全集成) |
| 实际业绩增删改查 | ✅ |
| 父子校验 (子≤父) | ✅ |
| 剩余未分配提示 | ✅ |
| 完成率进度条 | ✅ |
| 权限 (admin 管理/sales 填报) | ⚠️ 基本实现，能力矩阵未完全覆盖 |
| 聚合报表 (按季度/年度) | ❌ Phase 2 |
| 审计日志 | ❌ Phase 2 |
| 锁账期 | ❌ Phase 2 |
| Virtual 未拆分节点 | ❌ Phase 2 |

---

## 3. 文件变更清单

### 新增 (8 个)
```
backend/app/models/actual_performance.py
backend/alembic/versions/sales_target_redesign_2026.py

frontend/src/hooks/useSalesTargets.ts
frontend/src/hooks/useActualPerformance.ts
frontend/src/components/lists/SalesTargetTree.tsx
frontend/src/components/modals/ActualEntryDrawer.tsx
frontend/src/components/modals/QuarterSplitDrawer.tsx

docs/sales_target_implementation.md (本文档)
```

### 修改 (4 个)
```
backend/app/models/sales_target.py              # + gross_profit_target
backend/app/schemas/sales_target.py              # Schema 全面更新
backend/app/routers/sales_target.py              # 路由全面重写 (+270行)
frontend/src/App.tsx                             # 路由 → SalesTargetTree
```

---

## 4. 构建验证

```bash
# 前端编译
CI=true npm run build    ✅ 无 TypeScript 错误

# 后端测试
pytest -q                ✅ 136 passed, 0 failures
```

---

## 5. Phase 2 实施计划

### P1 (核心改进)
1. **金额字段改为 `Numeric(14,2)`** — ORM、Schema、迁移脚本同步
2. **实际业绩 `user_id+year+month` 唯一约束** — PostgreSQL UNIQUE INDEX + upsert 逻辑
3. **聚合报表 API** — `GET /actual-performance/report?group_by=quarter/year`
4. **Virtual 未拆分节点** — 树 API 补全缺失季度/月份的虚拟 0 节点
5. **审计日志** — `actual_performance_audit_logs` 表 + 写操作同事务审计
6. **变更原因** — POST/PUT/DELETE 强制 `change_reason`

### P2 (增强功能)
1. 锁账期 (每月 5 日锁定) + `override_locked_period` 权限
2. 毛利约束 (毛利目标≤营收目标) CheckConstraint
3. 并发锁 (SELECT FOR UPDATE)
4. 能力矩阵 (capability) 补齐
5. ECharts 业绩趋势图表
6. Excel/CSV 导出

---

## 6. 技术决策

| 决策点 | 选择 | 原因 |
|--------|------|------|
| 扩表 vs 拆表 | 扩表 (`gross_profit_target` 列) | 开发环境无历史包袱，改动最小 |
| `target_id` nullable | 允许 NULL | 支持"无目标先填报"业务场景 |
| 前端单位"万元" | 显示万元，存储元 | 与现有 `SalesTargetList.tsx` 一致 |
| `Select` 交互绕过 | 用 `fetch` 直调验证 API | Select 在模态框内焦点管理有问题，后续优化 |

---

*文档维护*: 业绩管理体系重构 V1 于 2026-05-07 完成。Phase 2 变更请同步更新本文档。
