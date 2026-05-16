# 金额单位与展示规范

## 口径

- 系统内所有预算、金额、价格、合同额、回款、业绩、目标、毛利等金额类数据均为人民币口径。
- 数据库和后端 API 继续以“元”为存储和传输单位，不在接口层改为万元，避免破坏历史数据、迁移脚本和前后端契约。
- 前端页面负责输入和展示换算：用户看到和输入的单位统一为“万元”。

## 前端展示规则

- 金额字段标签统一追加“(万元)”，例如：
  - `预估预算(万元)`
  - `预计合同金额(万元)`
  - `合同金额(万元)`
  - `计划回款(万元)`
  - `营收目标(万元)`
  - `毛利目标(万元)`
- 金额数字统一保留 1 位小数。
- 列表、详情、表单、统计卡片、图表 tooltip、图例和汇总行应使用同一格式。
- 空值显示为 `-`，不要显示 `0.0`，除非业务含义确认为金额为 0。
- 百分比、数量、日期、折扣率等非金额字段不适用该规则。

## 换算规则

- 后端返回元，前端展示万元：`display = amount / 10000`。
- 前端输入万元，提交后端元：`payload = input * 10000`。
- 展示格式：`display.toLocaleString('zh-CN', { minimumFractionDigits: 1, maximumFractionDigits: 1 })`。

## 需要覆盖的主要字段

| 业务对象 | 字段 |
|---|---|
| 线索 | `estimated_budget`, `expected_contract_amount` |
| 商机 / 9A | `expected_contract_amount`, `budget` |
| 项目 | `downstream_contract_amount`, `upstream_procurement_amount`, `direct_project_investment`, `additional_investment`, `actual_payment_amount`, `gross_margin` |
| 合同 | `contract_amount`, `unit_price`, `amount`, `plan_amount`, `actual_amount` |
| 报表 | `total_amount`, `contract_amount`, `received_amount`, `pending_amount`, `total_plan_amount`, `total_actual_amount`, `overdue_amount` |
| 销售目标 | `target_amount`, `gross_profit_target`, `amount_actual`, `gross_profit_actual` |
| 渠道绩效 | `performance_target`, `achieved_performance`, `total_contract_amount` |
| 预警规则 | `threshold_amount` |

## 验收

- 前端执行 `npm test` 和 `npm run build`。
- 搜索页面文案，确认金额字段不再只显示“金额/预算/目标”而缺少“(万元)”。
- 抽查金额展示，确认小数位为 1 位。
