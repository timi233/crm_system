# CRM System Agent Guide

本文件是仓库级 agent 指南。所有参与本项目的 agent 在执行需求分析、开发、审查或交付前，应优先读取本文件，并结合 [.agents/business-domain.md](.agents/business-domain.md) 理解业务边界。

## 项目定位

- 系统名称：普悦业财一体 CRM 销管系统。
- 主应用范围：`backend/` + `frontend/`。
- 当前业务目标：围绕客户、渠道、销售过程、销售任务、项目合同、派工工单和经营报表，形成销售经营管理闭环。
- 历史或外部参考目录不属于默认开发范围，除非用户明确要求。

## 当前核心业务能力

- 客户与渠道管理：客户档案、客户全景、财务视图、渠道档案、渠道联系人、客户多渠道关系、渠道分配。
- 销售流程管理：线索、商机、商机转化、项目、合同，主链路为 `线索 -> 商机 -> 项目 -> 合同`。
- 销售任务与目标管理：年度、季度、月度销售任务，销售目标树，目标拆解，实际业绩录入，完成进度统计，规则校验。
- 跟进与协同：商务跟进、渠道跟进、统一目标、执行计划、知识库、日报/周报草稿生成与提交流程、日报/周报评论。
- 工单与派工：工单、技术员分配、派工记录、状态同步、派工 Webhook、服务评价、产品装机记录。
- 渠道运营：渠道绩效、渠道培训、渠道目标、渠道线索与客户关联。
- 报表与驾驶舱：角色化工作台、统一待办中心、通知中心、团队排行、预警中心、销售漏斗、业绩统计、回款进度。
- 组织同步与交接：飞书组织同步、完整部门路径落库、待交接用户禁用登录、离职交接请求、资产预览、管理员前端处理入口。
- 产品与基础资料：产品管理、实体产品、数据字典、自动编号、9A 相关业务数据。
- 系统治理：JWT 登录、飞书 OAuth、角色权限、统一策略层、操作日志、告警规则、`department_manager_id` 团队关系。
- 外部集成：飞书 OAuth/WebSocket、飞书连通性诊断、组织同步、日报提醒、派工 Webhook。金蝶/财务相关代码存在，但当前主入口未注册，`financial_export:*` 与 `kingdee_integration:read` capability 已隐藏，不能默认视为已启用线上能力。

## 下一阶段业务目标

下一阶段已确定的建设目标：

- 报价/价格/方案管理
- 附件与文档管理
- 数据导入导出
- 客户联系人与组织关系深化
- 通知与待办增强：定时提醒、飞书外发、订阅规则、日历视图、完成/延期/关闭动作。
- 日报/周报增强：提醒策略、统计口径、提交规则优化。
- 角色化工作台增强：继续按管理员、业务管理者、销售、财务、技术员、渠道运营补齐差异化首页内容。
- 离职交接增强：部门负责人/当事人视图、审批协同和运维说明。
- 新增渠道运营角色，建议编码为 `channel_ops`。
- 新增部门负责人关系，建议字段为 `department_manager_id`，用于日报/周报团队视图和角色化工作台团队范围。
- 日报/周报暂不强制提交，财务角色第一版不参与日报/周报。

详细范围参考 `docs/next-phase-business-modules-plan-2026-05-12.md`。

## 事实来源

- 后端启用能力以 `backend/app/main.py` 注册的 Router 为准。
- 前端启用页面以 `frontend/src/App.tsx` 注册的 Route 为准。
- 销售任务管理的业务规则优先参考：
  - `backend/app/routers/sales_target.py`
  - `backend/app/schemas/sales_target.py`
  - `frontend/src/components/lists/SalesTargetTree.tsx`
  - `frontend/src/hooks/useSalesTargets.ts`
  - `backend/tests/test_sales_target_rules.py`
  - `backend/tests/test_sales_target_flow.py`
- 日报/周报与角色工作台优先参考：
  - `backend/app/routers/work_report.py`
  - `backend/app/services/work_report_service.py`
  - `backend/app/routers/dashboard.py`
  - `backend/app/services/dashboard_workbench_service.py`
  - `frontend/src/pages/WorkReportPage.tsx`
  - `frontend/src/pages/WorkReportDetailPage.tsx`
  - `frontend/src/components/dashboard/RoleDashboard.tsx`
- 通知中心与待办中心优先参考：
  - `backend/app/routers/notification.py`
  - `backend/app/services/notification_service.py`
  - `backend/app/routers/todo.py`
  - `backend/app/services/todo_service.py`
  - `frontend/src/pages/NotificationCenterPage.tsx`
  - `frontend/src/pages/TodoCenterPage.tsx`
  - `frontend/src/hooks/useNotifications.ts`
  - `frontend/src/hooks/useTodos.ts`
- 飞书组织同步与离职交接优先参考：
  - `backend/app/routers/integrations/feishu.py`
  - `backend/app/services/feishu_org_sync_service.py`
  - `backend/app/services/work_report_reminder_service.py`
  - `backend/app/routers/handover.py`
  - `backend/app/services/handover_service.py`
  - `frontend/src/pages/HandoverListPage.tsx`
  - `frontend/src/pages/HandoverDetailPage.tsx`
- README 是对外项目说明，`.ccb/ccb_memory.md` 是 CCB agent 共享记忆。
- 下一阶段业务模块计划见 `docs/next-phase-business-modules-plan-2026-05-12.md`。
- 日报/周报与角色化工作台设计见 `docs/daily-weekly-report-and-role-dashboard-design-2026-05-13.md`。
- 日报/周报与角色化工作台开发拆分计划见 `docs/daily-weekly-report-dashboard-implementation-plan-2026-05-13.md`。
- 通知中心计划见 `docs/notification-center-plan-2026-05-15.md`。
- 任务/日程/提醒中心计划见 `docs/todo-reminder-center-plan-2026-05-15.md`。
- 阶段 Review 记录见 `docs/project-review-plan-2026-05-15.md`。

## 开发原则

- 不要默认修改历史参考系统、备份文件、生成文件或未被主应用引用的模块。
- 不要提交真实环境变量文件。只允许提交 example 模板，例如 `backend/.env.example`、`backend/.env.dispatch.example`。
- 新增接口必须接入认证、权限策略、输入校验、分页上限和测试。
- 列表接口应保持有界分页，常用约束为 `skip >= 0`、`limit <= 100`。
- 权限策略默认拒绝，只有明确业务规则允许时才放行。
- 团队范围相关新功能优先使用 `department_manager_id`，不要继续扩展销售专用的 `sales_leader_id`。
- 日报/周报第一版默认面向 `admin`、`business`、`sales`、`technician`、`channel_ops`；不要把 `finance` 纳入默认提交流程。
- 离职交接首版操作权限为 `admin`；非 admin 不应直接执行分配、执行或取消。
- 待办中心首版为派生待办，不新增通用 `todos` 表；不要把通知表当待办表使用。
- 前端已迁移到 Vite，不要重新引入 CRA 或 `react-scripts`。
- 业务功能开发应同时考虑后端 API、前端页面、类型定义、错误提示、空状态、回归测试和 README/计划文档。

## 验收建议

后端常用验证：

```bash
cd backend
APP_ENV=test pytest -q
```

前端常用验证：

```bash
cd frontend
npm test
npm run build
npm audit
```

当前前端已配置 Vitest 最小测试基线，覆盖 API URL/error detail 格式化、roles/channel_ops 角色映射、useRoleDashboard hook。测试应通过后再执行构建验证。

如果改动涉及前端交互，还应启动本地服务进行 smoke 检查：

```bash
cd frontend
npm start
```

默认前端监听 `0.0.0.0:3002`，后端监听 `0.0.0.0:8000`。前端 API 使用相对路径 `/api`，通过 Vite 代理或 nginx 反代转发。

## 网络配置原则

- 前端开发/预览服务监听 `0.0.0.0`，支持局域网访问。
- 前端 API 默认使用相对路径 `/api`，不硬编码 localhost/IP/域名。
- Vite 开发代理 target 使用 `VITE_DEV_PROXY_TARGET`（默认 `http://127.0.0.1:8000`）。
- Nginx 必须透传 `Host`、`X-Forwarded-*` 头。
- 飞书 OAuth `FEISHU_REDIRECT_URI` 和后台推送链接 `FRONTEND_PUBLIC_URL` 是例外，必须显式配置完整 URL。
- CORS 生产建议同源反代；`ALLOWED_ORIGINS` 保留兜底，不允许 `*` + credentials。

## 飞书组织同步与交接

- 飞书组织同步可由管理员 API 触发，也可由 cron 调用 `cd backend && python -m app.cli feishu-org-sync --trigger cron`。
- 只读预览使用 `python -m app.cli feishu-org-sync --dry-run`，不得写入 CRM 用户。
- 同步用户应存储完整部门路径；新同步用户默认启用。
- 首次成功同步不做离职检测；后续同步中，上一轮存在、本轮缺失的飞书用户标记为 `pending_handover` 并立即禁用登录。
- 单轮离职比例超过 10% 时暂停离职标记并记录异常。
- 离职交接转移主责人类业务数据，业绩/目标/日报/审计类数据不得转移。

## CCB 协作

- 需要交给其他可见 agent 时，优先使用 CCB `ask`，不要使用隐藏子代理替代项目协作。
- 委派时必须说明目标、相关文件、允许编辑范围、验收命令和期望输出。
- 回复其他 agent 时应包含：发现的问题、修改文件、阻塞点、验证结果。
