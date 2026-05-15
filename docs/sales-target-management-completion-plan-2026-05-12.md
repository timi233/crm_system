# 销售任务管理补完计划

制定日期：2026-05-12
依据：当前代码审查结果、`docs/sales_target_implementation.md`、现有 `/sales-targets` 后端与前端实现。

## 目标

补完销售年度、季度、月度任务管理功能，使其从当前 MVP 状态提升为完整可维护的业务闭环：

- 年度目标可创建、查看、更新、删除。
- 年度目标可拆分到季度，季度可拆分到月度。
- 季度/月度目标可更新、删除或重新拆分，且不会重复创建脏数据。
- 实际业绩可按销售人员、年月录入、更新、删除，并正确归属。
- 年/季/月目标与实际业绩能正确汇总完成率。
- 后端有明确契约和测试覆盖，前端只调用实际存在的接口。

## 当前状态

已具备：

- 后端目标模型 `SalesTarget` 支持 `yearly / quarterly / monthly` 三层结构。
- 后端实际业绩模型 `ActualPerformance` 支持年月实际营收/毛利。
- 后端已有：
  - `GET /sales-targets/`
  - `GET /sales-targets/tree`
  - `POST /sales-targets/year`
  - `POST /sales-targets/{target_id}/decompose/`
  - `PUT /sales-targets/{target_id}`，但仅支持年度目标。
  - `DELETE /sales-targets/{target_id}`，但仅支持年度目标。
  - `/sales-targets/actual/` CRUD。
- 前端 `/sales-targets` 路由使用 `SalesTargetTree`。
- 当前专项测试：`tests/test_sales_targets.py`、`tests/test_sales_target_rules.py` 通过。

主要缺口：

1. 季度/月度目标没有完整 CRUD。
2. 拆分接口重复调用会重复创建季度/月度目标。
3. 管理员代填销售实际业绩时，前端传 `user_id`，但后端 Schema 不接收，实际可能归属到管理员。
4. `actual_summary` 接口没有真正聚合实际金额。
5. Schema 缺少年份、季度、月份、金额范围校验。
6. 旧前端 `SalesTargetList.tsx` 仍残留并调用不存在接口。
7. 测试覆盖不足，没有完整年→季→月→实际业绩闭环测试。

## 实施原则

- 优先修复实际路由使用的 `SalesTargetTree` 链路。
- 保持金额存储单位为“元”，前端展示/输入单位为“万元”。
- 不引入大规模架构重构，先完成业务闭环和契约一致性。
- 不回滚当前审计整改、Vite 迁移、环境文件移除等已有改动。
- 不触碰用户既有的 `docker-compose.yml`、`backup_pg14_20260512_102837.sql`、`docs/代码审计报告/`，除非确有必要并说明。

## 阶段 1：后端契约补完

### 1.1 完善 Schema 校验

文件建议：`backend/app/schemas/sales_target.py`

任务：

1. 为销售目标输入增加约束：
   - `target_year` 合理范围，例如 `ge=2000, le=2100`。
   - `target_amount` 大于 0。
   - `gross_profit_target` 大于等于 0。
   - 季度范围 1-4。
   - 月份范围 1-12。
2. 为实际业绩输入增加：
   - `user_id: Optional[int]`，供管理员代填。
   - `year` 范围校验。
   - `month` 范围 1-12。
   - `amount_actual`、`gross_profit_actual` 大于等于 0。
3. 区分年度更新和通用目标更新 Schema，避免 `PUT /sales-targets/{id}` 必须传 `user_id/target_year`。

验收：

- 非法年份、月份、季度、负金额返回 422。
- 管理员可通过实际业绩接口显式指定 `user_id`。

### 1.2 重构目标更新/删除为通用目标接口

文件建议：`backend/app/routers/sales_target.py`

任务：

1. 将 `PUT /sales-targets/{target_id}` 支持 yearly、quarterly、monthly。
2. 更新年度目标时：
   - 子季度合计不能超过年度目标。
   - 毛利子目标合计不能超过年度毛利目标。
3. 更新季度目标时：
   - 月度合计不能超过季度目标。
   - 更新季度目标不能导致年度季度合计超过年度目标。
4. 更新月度目标时：
   - 更新月度目标不能导致所属季度月度合计超过季度目标。
5. `DELETE /sales-targets/{target_id}` 支持删除 year/quarter/month：
   - 有子目标时禁止删除。
   - 月目标若已有实际业绩关联，默认禁止删除，除非实现明确的解绑/级联策略。
6. 返回统一的 `SalesTargetRead`。

验收：

- 年、季、月目标均可按规则更新/删除。
- 破坏父子金额约束时返回 400。
- 无权限返回 403，不存在返回 404。

### 1.3 拆分接口改为幂等/可重拆

文件建议：`backend/app/routers/sales_target.py`

任务：

1. `POST /sales-targets/{target_id}/decompose/` 不得重复创建同一季度或同一月份。
2. 对已存在季度/月度，建议采用 upsert 语义：
   - 已存在则更新金额。
   - 不存在则创建。
3. 校验季度编号和月份编号：
   - 季度只能 1-4。
   - 月份必须属于对应季度，例如 Q1 只能 1/2/3。
4. 校验同级合计不超过父目标。
5. 返回创建/更新数量，便于前端提示。

验收：

- 同一拆分请求重复提交不会产生重复季度/月度记录。
- 错误月份映射返回 400 或 422。

### 1.4 修复实际业绩归属与聚合

文件建议：

- `backend/app/schemas/sales_target.py`
- `backend/app/routers/sales_target.py`

任务：

1. `ActualPerformanceCreate` 接收可选 `user_id`。
2. 管理员可为任意销售创建/更新实际业绩；非管理员只能操作自己。
3. 创建实际业绩时，若指定 `target_id`：
   - 校验目标存在。
   - 若是月目标，校验年月与目标一致。
   - 校验目标归属销售与 `user_id` 一致。
4. 实际业绩唯一性：
   - 应按 `user_id + year + month` 防止重复。
   - 当前无数据库唯一约束时，至少保持接口级防重。
5. `GET /sales-targets/actual/summary` 返回真正聚合数据：
   - 按月聚合：year, month, user_id, amount_actual, gross_profit_actual。
   - 按季度聚合：year, quarter, user_id, amount_actual, gross_profit_actual。
   - 按年度聚合：year, user_id, amount_actual, gross_profit_actual。
   - 可用 `group_by=month|quarter|year` 参数。

验收：

- 管理员代填实际业绩记录归属到指定销售。
- 非管理员无法为他人填报。
- summary 返回包含金额聚合结果。

## 阶段 2：前端补完

### 2.1 更新 hooks

文件建议：`frontend/src/hooks/useSalesTargets.ts`

任务：

1. 增加：
   - `useUpdateSalesTarget`
   - `useDeleteSalesTarget`
   - `useActualSummary`
2. `useCreateActual` payload 加入 `user_id`。
3. 所有 mutation 成功后正确 invalidate tree、actual、summary。

验收：

- 前端不再通过未定义类型“偷偷”传 `user_id`。
- 所有调用都匹配后端存在接口。

### 2.2 补齐 SalesTargetTree 操作

文件建议：

- `frontend/src/components/lists/SalesTargetTree.tsx`
- 可新增/复用 Drawer 组件。

任务：

1. 年度目标行：
   - 管理员可编辑目标金额/毛利目标。
   - 管理员可删除无子目标年度目标。
2. 季度目标行：
   - 管理员可编辑季度目标。
   - 管理员可拆分/重拆月度目标。
   - 管理员可删除无月度子目标季度目标。
3. 月度目标行：
   - 管理员可编辑月度目标。
   - 管理员可删除没有实际业绩关联的月度目标。
   - 用户可填报/更新实际业绩。
4. 对业务规则失败展示后端错误信息。
5. 不要在 UI 中保留调用不存在接口的入口。

验收：

- UI 能完成年/季/月目标编辑删除和月度实际填报。
- 权限表现与后端一致：管理员管理目标，普通用户只填报/查看自己的。

### 2.3 清理旧组件

文件建议：`frontend/src/components/lists/SalesTargetList.tsx`

任务：

1. 该组件当前未路由使用，且调用不存在接口：
   - `/sales-targets/yearly-with-status`
   - `/sales-targets/{id}/decompose-quarterly`
   - `/sales-targets/{id}/children`
2. 选择其一：
   - 删除组件及 `App.tsx` 中的 lazy import。
   - 或重写为基于现有 `/tree` 的兼容视图。

建议：删除或标记废弃，避免误用。

验收：

- `rg "yearly-with-status|decompose-quarterly|/children" frontend/src` 无命中。
- `npm run build` 通过。

## 阶段 3：测试补齐

### 3.1 后端测试

文件建议：

- `backend/tests/test_sales_targets.py`
- `backend/tests/test_sales_target_rules.py`
- 可新增 `backend/tests/test_sales_target_flow.py`

任务：

1. 年目标创建：
   - 成功。
   - 重复用户年度目标返回 400。
   - 非管理员创建返回 403。
2. 拆分：
   - 年度拆季度/月度成功。
   - 重复提交不产生重复记录。
   - 季度合计超年目标返回 400。
   - 月份不属于季度返回 400/422。
3. 更新/删除：
   - 年/季/月目标更新成功。
   - 父子合计超额时更新失败。
   - 有子目标时删除失败。
   - 无子目标时删除成功。
4. 实际业绩：
   - 管理员代填指定销售成功。
   - 非管理员代填别人失败。
   - 同一销售年月重复创建返回 409。
   - 更新/删除权限正确。
5. Summary：
   - `group_by=month|quarter|year` 返回正确金额聚合。

验收：

- `APP_ENV=test ./venv/bin/python -m pytest tests/test_sales_targets.py tests/test_sales_target_rules.py -q` 通过。
- 完整 `APP_ENV=test ./venv/bin/python -m pytest -q` 通过。

### 3.2 前端验证

任务：

1. `cd frontend && npx tsc --noEmit`。
2. `cd frontend && npm run build`。
3. 如条件允许，启动前后端做 smoke：
   - 打开 `/sales-targets`。
   - 管理员创建年度目标。
   - 拆分季度/月度。
   - 填报月度实际业绩。
   - 页面展示完成率变化。

验收：

- TypeScript 无错误。
- Vite build 成功。
- smoke 结果记录到回复中。

## 最终验收标准

必须全部满足：

- 年/季/月目标管理闭环完整。
- 管理员代填业绩归属正确。
- 拆分幂等，不重复创建脏数据。
- Summary 聚合返回真实金额。
- 旧前端不存在接口调用已清理。
- 后端完整测试通过。
- 前端类型检查和构建通过。

## 交付说明

开发完成后请回复：

- 修改文件列表。
- 完成的功能点。
- 关键业务规则说明。
- 验证命令和结果。
- 如有未完成项，明确是否阻断“销售任务管理完整开发”。

## 最终验收记录

验收日期：2026-05-12

状态：已完成。年度、季度、月度销售任务管理闭环已补齐并通过验收。

完成范围：

- 后端 `PUT /sales-targets/{target_id}`、`DELETE /sales-targets/{target_id}` 支持年/季/月目标。
- 年度拆季度、季度拆月度接口改为幂等 upsert，不重复创建同一期间目标。
- 拆分接口按“已有同级目标 + 本次提交目标”整体校验，避免部分提交导致父级超额。
- 季度调整时校验既有月度目标合计，避免下调季度后已有月目标超额。
- 实际业绩创建和更新均校验目标类型、年月、月份和销售归属。
- 管理员可代填指定销售业绩，非管理员只能填报自己的业绩。
- `actual/summary` 支持按月、季度、年度聚合实际营收和毛利。
- 前端 `SalesTargetTree` 支持年度创建、目标编辑、季度拆分/月度重拆、实际业绩填报、目标删除。
- 删除入口按后端规则处理：存在下级目标或月度目标已关联实际业绩时禁用删除。
- 旧前端不存在接口调用已清理。

验收命令：

- `APP_ENV=test ./venv/bin/python -m pytest tests/test_sales_targets.py tests/test_sales_target_rules.py tests/test_sales_target_flow.py -q`：32 passed。
- `APP_ENV=test ./venv/bin/python -m pytest -q`：170 passed, 10 warnings。
- `cd frontend && npx tsc --noEmit`：通过。
- `cd frontend && npm run build`：通过。
- `cd frontend && npm audit --json`：total/high/critical 均为 0。

剩余非阻断项：

- 后端测试仍有第三方库 deprecation warnings。
- Vite 构建仍提示 antd/echarts chunk 较大，属于包体优化建议，不阻断销售任务管理功能交付。
