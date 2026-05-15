# 项目联合 Review 计划

日期：2026-05-15
协调负责人：agent2
协作对象：agent1

## Review 目标

检查本轮已推送到 `origin/main` 的阶段建设成果是否存在遗漏、漏洞或交付风险。

当前基线：

- 分支：`main`
- 已推送提交：`bab56e9 feat: complete CRM operations workflow modules`
- 当前重点能力：
  - 销售任务管理闭环
  - 日报/周报与角色化工作台
  - 飞书诊断、组织同步与离职交接
  - 离职交接前端入口
  - 通知中心最小闭环
  - 任务/日程/提醒中心最小闭环
  - Vite/Vitest 迁移与前端构建基础

## Review 重点

### P0：安全与部署风险

- 是否误提交真实环境变量、密钥或生产配置。
- `.env.production`、`.env.test` 删除后是否有 README/example 覆盖部署说明。
- Alembic 是否单 head，迁移顺序是否可部署。
- 新增 router 是否全部接入认证与权限。
- 列表接口是否有分页上限。

### P1：权限与数据隔离

- 通知中心是否只返回当前用户通知。
- 待办中心是否只返回当前用户或其角色允许处理的待办。
- 离职交接是否仅 admin 可管理，是否存在未授权执行/取消风险。
- 日报/周报团队视图是否存在越权读取。
- `channel_ops`、`department_manager_id` 能力是否影响既有角色。

### P2：业务闭环遗漏

- 日报/周报评论通知是否能跳转报告详情。
- 通知中心和待办中心职责是否混淆。
- 待办来源是否遗漏关键对象或跳转错误。
- 工作台摘要是否与 `/todos`、`/notifications` 保持一致。
- 离职交接前端是否覆盖列表、详情、资产预览、分配、执行、取消。

### P3：测试与回归风险

- 后端测试是否覆盖新增 API 权限、分页、越权、空状态。
- 前端测试是否覆盖新增基础 hooks 或关键渲染。
- 仅 mock 测试的飞书能力是否在文档中明确真实联调未完成。
- 是否存在测试通过但部署会失败的问题。

### P4：前端可用性

- 菜单入口是否完整。
- API 路径是否使用相对 `/api`，未硬编码 localhost/IP。
- Vite 迁移是否遗漏 CRA 相关入口。
- 大 chunk 警告是否仍为非阻断项。

## 输出要求

agent1 返回时请按 code review 格式输出：

1. Findings：按严重程度排序，包含文件/行号或明确路径。
2. Open questions：需要用户或 agent2 拍板的问题。
3. Residual risks：当前无法完全验证但应记录的风险。
4. Suggested next actions：建议交给 agent3 修复或补测的任务。

## 当前已知状态

- 推送前本地验证：
  - 后端全量：`290 passed, 10 warnings`
  - 前端 Vitest：`26 passed`
  - 前端构建：通过，仍有 `antd`、`echarts` 大 chunk 警告
  - Alembic：单 head `work_report_comments_20260515`
  - `git diff --check`：通过
- 真实飞书租户联调仍未执行。
- P5.4 定时提醒/飞书推送仍延期。

## 派发记录

- 2026-05-15：agent2 创建本 review 计划，准备派发 agent1 做核心问题审查。
- 2026-05-15：agent2 已通过 CCB 派发 agent1 做核心问题审查，Job：`job_fc3e0bd71ac2`。

## agent1 Review 结论

状态：已完成。

### Findings 汇总

HIGH：

- H1：通知中心 `total` 使用当前页 `len(items)`，分页元数据失真。位置：`backend/app/routers/notification.py`。
- H2：离职交接前后端权限不一致，team manager 可绕过前端直接操作后端 API。位置：`backend/app/routers/auth.py`、`backend/app/services/handover_service.py`、`backend/app/routers/handover.py`。
- H3：待办中心对 business 角色返回全局离职交接待办，未按 `team_manager_user_id` 过滤。位置：`backend/app/services/todo_service.py`。

MEDIUM：

- M1：工作报告评论响应缺少 `user_name`，前端显示“未知用户”。
- M2：评论通知 content 使用 `current_user.get("name")`，可能生成空用户名。
- M3：通知中心 entity 跳转映射只覆盖 `work_report/handover_request/work_order`。
- M4：通知 router 尾斜杠风格与前端请求不统一。
- M5：`NotificationService.create()` 内部 commit，和评论创建事务边界混乱。

LOW / residual：

- business 工单待办全局视野可能噪音高。
- 评论缺少独立 `work_report:comment` action。
- 部门负责人 team scope 缺否定测试。
- 测试以 MockDB 为主，缺少 HTTP 越权集成测试。
- 真实飞书租户联调仍未完成。

### agent2 默认修复口径

- H2 采用方案 A：离职交接首版仅 `admin` 可分配、执行、取消；后端 router 必须与前端 capability 保持一致。
- H3：business 用户不应看到全局离职交接待办；非 admin 只能看 `team_manager_user_id == 当前用户` 的交接待办，若前端入口未开放则不返回死链。
- H1：通知列表 `total` 必须是真实总数，不是当前页大小。
- M1/M2：评论接口返回 `user_name`，通知 content 使用显式查询到的用户名称。
- M4：通知列表路由统一为无尾斜杠，避免 307。
- M5：列入第二批修复，避免一次改动扩大事务语义；但本轮修复中不得新增更多内部 commit 调用。

## 修复派发计划

### R1：高优先级权限与分页修复

目标：修复 H1/H2/H3/M1/M2/M4，并补充最小回归测试。

建议交给 `agent3`：

- 修复通知 `total` 真实计数。
- 修复通知 router 尾斜杠。
- 修复 handover assign/execute/cancel 仅 admin 可操作。
- 修复 todo handover 聚合的 business 越权。
- 修复评论 `user_name` 和通知 content 用户名。
- 增加对应测试。

状态：已派发给 `agent3`。
CCB job：`job_896659c115d9`。

完成状态：已完成，agent2 已复核。

修复结果：

- H1：`NotificationService.count_user_notifications()` 已补齐，通知列表 `total` 返回真实总数。
- M4：通知列表路由统一为无尾斜杠。
- H2：handover assign/execute/cancel 改为 `Depends(require_admin)`，非 admin 不能绕过前端直接操作。
- H3：handover todos 仅 admin 聚合，business 不再看到全局交接待办。
- M1/M2：工作报告评论返回 `user_name`，评论通知 content 使用显式查询到的用户名。

复核结果：

- `cd backend && APP_ENV=test ./venv/bin/python -m pytest tests/test_notifications.py tests/test_todos.py tests/test_handover.py tests/test_work_report_comments.py -q`：`42 passed, 10 warnings`。
- `cd backend && APP_ENV=test ./venv/bin/python -m pytest -q`：`300 passed, 10 warnings`。
- `cd frontend && npm test -- --run`：`3 test files, 26 passed`。
- `cd frontend && npm run build`：通过，仍有既有 `antd`、`echarts` 大 chunk 警告。
- `cd backend && ./venv/bin/alembic heads`：`work_report_comments_20260515 (head)`。
- `git diff --check`：通过。

剩余事项：

- M5：`NotificationService.create()` 内部 commit 的事务边界问题仍建议作为 R2 独立处理。
- 后续仍建议补 HTTP/router 越权集成测试，降低 MockDB 单测遗漏风险。

### R2：事务边界与集成测试补强

目标：修复 M5，并补充通知/待办/交接 HTTP 越权测试。

建议 R1 通过后再做，避免权限修复和事务重构混在一起。
