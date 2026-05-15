# CRM System

普悦业财一体 CRM 销管系统。主应用由 `FastAPI + React` 组成，覆盖线索、商机、项目、合同、客户、渠道、派工工单、销售目标、知识库、角色化工作台、日报/周报、通知中心、待办中心、飞书组织同步与离职交接、报表与权限控制等核心能力。

## 项目状态

- 主应用目录：`backend/` + `frontend/`
- 后端入口：`backend/app/main.py`
- 后端架构：模块化 Router + Schema + Service + Policy
- 前端构建工具：`Vite`
- 前端本地开发端口：`3002`
- 后端本地/API 端口：`8000`
- Docker 暴露端口：
  - 前端：`8081`
  - 后端：`8000`
  - PostgreSQL：`5432`
  - Redis：`6379`

## 核心业务能力

| 能力域 | 当前能力 |
|--------|----------|
| 客户与渠道管理 | 客户档案、客户全景、财务视图、渠道档案、渠道联系人、客户多渠道关系、渠道分配 |
| 销售流程管理 | 线索、商机、商机转化、项目、合同，覆盖 `线索 -> 商机 -> 项目 -> 合同` 主链路 |
| 销售任务与目标管理 | 年度、季度、月度销售任务，销售目标树，目标拆解，实际业绩录入，完成进度统计，规则校验 |
| 跟进与协同 | 商务跟进、渠道跟进、统一目标、执行计划、知识库、日报/周报草稿生成与提交流程、日报/周报评论 |
| 工单与派工 | 工单、技术员分配、派工记录、状态同步、派工 Webhook、服务评价、产品装机记录 |
| 渠道运营 | 渠道绩效、渠道培训、渠道目标、渠道线索与客户关联 |
| 报表与驾驶舱 | 角色化工作台、统一待办中心、通知中心、团队排行、预警中心、销售漏斗、业绩统计、回款进度 |
| 组织同步与交接 | 飞书组织同步、完整部门路径落库、待交接用户禁用登录、离职交接请求、资产预览、管理员前端处理入口 |
| 产品与基础资料 | 产品管理、实体产品、数据字典、自动编号、9A 相关业务数据 |
| 系统治理 | JWT 登录、飞书 OAuth、角色权限、统一策略层、操作日志、告警规则、`department_manager_id` 团队关系 |
| 外部集成 | 飞书 OAuth/WebSocket、飞书连通性诊断、组织同步、日报提醒、派工 Webhook；金蝶相关代码存在但当前主入口未注册，启用前需确认路由和部署配置 |

说明：

- 当前 CRM 主应用以 `backend/app/main.py` 注册的 Router 和 `frontend/src/App.tsx` 暴露的页面为准。
- 仓库中存在部分历史或预研模块，例如未在主入口注册的财务/金蝶相关 Router；除非明确启用，否则不按线上能力承诺。
- 审计整改后，环境文件只应跟踪 example 模板，真实 `.env`、`.env.test`、`.env.production` 等本地密钥文件不得提交。

## 下一阶段业务目标

下一阶段重点补齐尚未建设的模块，并继续完善已上线的协同、通知、待办和交接能力：

- 报价/价格/方案管理
- 附件与文档管理
- 数据导入导出
- 客户联系人与组织关系深化
- 通知与待办增强：定时提醒、飞书外发、订阅规则、日历视图、完成/延期/关闭动作
- 日报/周报增强：提醒策略、统计口径、提交规则优化
- 角色化工作台增强：继续按管理员、业务管理者、销售、财务、技术员、渠道运营补齐差异化内容
- 离职交接增强：部门负责人/当事人视图、审批协同和运维说明

详细计划见 [下一阶段业务模块建设计划](docs/next-phase-business-modules-plan-2026-05-12.md)。

## 技术栈

### 后端

- Python 3.11
- FastAPI
- SQLAlchemy 2.x Async
- PostgreSQL
- Alembic
- JWT + bcrypt
- Redis
- pytest

### 前端

- React 18
- TypeScript
- Ant Design 5
- Redux Toolkit
- TanStack Query
- React Router 6
- Axios
- ECharts

## 权限模型

| 角色 | 读权限 | 写权限 |
|------|--------|--------|
| `admin` | 全量数据 | 全量数据 |
| `business` | 全量业务数据 | 全量业务实体 |
| `finance` | 财务专用视图与财务相关实体 | 财务实体 + owner 校验 |
| `sales` | owner / channel scope | owner / channel scope |
| `technician` | 工单相关数据 | 仅自己被分配的工单场景 |
| `channel_ops` | 渠道域、日报/周报、角色工作台相关范围 | 渠道运营职责范围内写权限 |

说明：

- `business` 当前被设计为准管理员角色。
- `finance` 访问客户全景时走 `/customers/{id}/finance-view`。
- 日报/周报第一版面向 `admin`、`business`、`sales`、`technician`、`channel_ops`；`finance` 默认不参与。
- 主写路径使用对象级授权校验。
- 新增和改造模块优先接入 `backend/app/core/policy/` 下的统一策略层。
- 前端通过用户 capabilities 控制菜单、按钮和页面动作。

## 数据字典

系统内置数据字典能力，提供标准化的业务参考数据：

- 地区字典：山东省及地级市行政区划
- 行业字典：政府单位、事业单位、制造业、医疗、金融等分类
- 商机来源：客户推荐、网络推广、展会、电话营销等来源
- 客户状态：潜在、活跃、已签约、休眠、流失等状态
- 拜访目的：商务洽谈、技术支持、关系维护、产品培训等目的
- 产品目录：产品类型 -> 品牌 -> 型号的层级结构

常用接口：

- `GET /dict/items`
- `GET /dict/types`
- `POST /dict/items`
- `PUT /dict/items/{id}`
- `DELETE /dict/items/{id}`

## 后端架构

```text
backend/app/
├── main.py                 # FastAPI app 初始化、CORS、lifespan、router 注册、/health
├── core/
│   ├── config.py           # 多环境配置
│   ├── security.py         # JWT / 密码哈希
│   ├── dependencies.py     # get_db, get_current_user 等共享依赖
│   ├── permissions.py      # 兼容旧权限路径
│   └── policy/             # 统一策略层
├── models/                 # SQLAlchemy 模型
├── schemas/                # Pydantic Schema
├── routers/                # API Router
└── services/               # 业务服务层
```

当前主入口注册的 Router 包括：

| Router | 说明 |
|--------|------|
| `auth` | 登录、JWT、飞书 OAuth |
| `user` | 用户管理 |
| `customer` / `customer_views` | 客户 CRUD、客户全景、财务视图 |
| `lead` | 线索管理 |
| `opportunity` / `opportunity_conversion` | 商机管理、商机转换 |
| `project` | 项目管理 |
| `contract` | 合同管理 |
| `follow_up` | 跟进记录 |
| `channel` / `channel_assignment` | 渠道、渠道联系人、渠道分配 |
| `customer_channel_link` | 客户多渠道关系 |
| `unified_target` / `execution_plan` | 统一目标、执行计划 |
| `sales_target` | 销售目标、季度拆分、实际业绩 |
| `work_order` / `dispatch` | 工单、派工集成、Webhook |
| `evaluation` | 服务评价 |
| `knowledge` | 知识库 |
| `product` / `entity_product` / `product_installation` | 产品、实体产品、装机记录 |
| `report` / `dashboard` / `alert` | 销售报表、角色工作台、待办/通知/团队排行、预警 |
| `dict_item` | 数据字典 |
| `operation_log` | 操作日志 |
| `nine_a` | 9A 相关能力 |
| `work_report` | 日报/周报列表、团队视图、草稿生成、提交/撤回/重生成 |
| `notification` | 站内通知列表、未读数、单条/批量已读、业务对象跳转 |
| `todo` | 统一待办聚合，覆盖跟进、合同、工单、日报/周报、离职交接 |
| `integrations/feishu` | 飞书连通性诊断、组织同步预览/执行、日报提醒任务 |
| `handover` | 离职交接请求、资产预览、指派、执行、取消 |

说明：`financials.py`、`kingdee_integration.py` 等文件在代码目录中存在，但当前未在 `backend/app/main.py` 注册；需要启用时应补齐路由注册、权限、测试与部署配置。

当前前端主入口暴露的关键页面包括：

- `/dashboard`：角色化工作台首页
- `/work-reports`、`/work-reports/:id`：日报/周报列表与详情
- `/notifications`：通知中心
- `/todos`：待办中心
- `/handovers`、`/handovers/:id`：离职交接管理
- `/auth/feishu/callback`：飞书 OAuth 回调页面

## 目录结构

```text
crm-system/
├── backend/
│   ├── app/
│   │   ├── core/              # 配置、认证、权限、策略
│   │   ├── models/            # SQLAlchemy ORM 模型
│   │   ├── routers/           # API 路由
│   │   ├── schemas/           # Pydantic Schema
│   │   ├── services/          # 业务服务
│   │   └── main.py            # 后端入口
│   ├── alembic/               # 数据库迁移
│   ├── tests/                 # pytest 测试
│   ├── .env.example           # 后端环境变量模板
│   └── .env.dispatch.example  # 派工集成环境变量模板
├── frontend/
│   ├── src/
│   │   ├── components/        # UI 组件
│   │   ├── hooks/             # 数据请求 hooks
│   │   ├── pages/             # 页面
│   │   ├── services/          # API 封装
│   │   ├── store/             # Redux 状态
│   │   ├── types/             # 类型定义
│   │   └── constants/         # 常量
│   ├── index.html             # Vite 入口
│   ├── vite.config.ts         # Vite 配置
│   ├── package.json
│   ├── nginx.conf
│   └── Dockerfile
├── docs/                      # 项目文档
├── deploy/                    # 部署配置
├── docker-compose.yml
└── README.md
```

说明：仓库内的 `QDmgt/`、`new_task_mgt/` 等目录是历史或外部参考系统。当前 CRM 主应用开发应落在 `backend/` 与 `frontend/` 内，除非明确维护外部系统本身。

## 快速开始

### 方式一：Docker Compose

在仓库根目录创建环境变量文件：

```bash
cp backend/.env.example .env
```

编辑 `.env`，至少确认以下配置：

```env
APP_ENV=development
FRONTEND_PUBLIC_URL=http://localhost:8081
BACKEND_PUBLIC_URL=http://localhost:8000
ALLOWED_ORIGINS=http://localhost:8081,http://localhost:3002,http://127.0.0.1:3002
POSTGRES_USER=crm_user
POSTGRES_PASSWORD=change_me
POSTGRES_DB=crm_db
JWT_SECRET_KEY=change_me
FEISHU_WS_ENABLED=false
```

启动：

```bash
docker-compose up -d --build
```

服务地址：

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:8081 |
| 后端 API | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |
| 健康检查 | http://localhost:8000/health |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

### 方式二：本地开发

后端：

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

前端：

```bash
cd frontend
npm install
npm start
```

前端开发服务默认监听 `0.0.0.0:3002`，支持局域网访问。`/api` 请求通过 Vite 代理转发到后端。可通过 `http://<本机IP>:3002/api/health` 验证代理连通性。

## 环境变量

常用后端配置：

| 变量 | 说明 |
|------|------|
| `APP_ENV` | 运行环境：`development` / `test` / `production` |
| `FRONTEND_PUBLIC_URL` | 前端公开访问地址 |
| `BACKEND_PUBLIC_URL` | 后端公开访问地址 |
| `ALLOWED_ORIGINS` | CORS 白名单，逗号分隔 |
| `DATABASE_URL` | SQLAlchemy async 数据库连接 |
| `JWT_SECRET_KEY` | JWT 签名密钥 |
| `FEISHU_APP_ID` | 飞书应用 ID |
| `FEISHU_APP_SECRET` | 飞书应用密钥 |
| `FEISHU_REDIRECT_URI` | 飞书 OAuth 回调地址 |
| `FEISHU_WS_ENABLED` | 是否启用飞书 WebSocket 服务 |
| `DISPATCH_WEBHOOK_SECRET` | 派工 Webhook 签名密钥 |
| `DISPATCH_API_URL` | 外部派工系统 API 地址 |

## 网络配置

### 前端监听与 API 调用

- **前端开发/预览服务**：监听 `0.0.0.0:3002`，支持局域网访问。
- **前端 API 调用**：默认使用相对路径 `/api`，随客户端访问 Host 自动切换，无需硬编码 localhost/IP/域名。
- **Vite 开发代理**：`/api` 代理到 `VITE_DEV_PROXY_TARGET`（默认 `http://127.0.0.1:8000`），用于本地开发。

### 反向代理配置

生产环境推荐使用同源反向代理（nginx），确保 Host 透传：

```nginx
proxy_set_header Host $host;
proxy_set_header X-Forwarded-Host $host;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header X-Forwarded-Port $server_port;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
```

### 外部集成例外

以下场景必须显式配置完整 URL（无请求上下文）：

- `FEISHU_REDIRECT_URI`：飞书 OAuth 白名单回调地址。
- `FRONTEND_PUBLIC_URL`：后台任务生成链接、飞书消息卡片跳转。
- `BACKEND_PUBLIC_URL`：外部 Webhook 回调地址。

### CORS 建议

生产环境优先使用同源反代，避免跨域。`ALLOWED_ORIGINS` 作为兜底，不允许 `*` + credentials。

## 数据库

本地开发初始化：

```bash
cd backend
source venv/bin/activate
python reset_db.py
python create_test_user.py
python seed_dict_data.py
```

正式环境迁移：

```bash
cd backend
source venv/bin/activate
alembic upgrade head
```

## 默认测试账号

| 邮箱 | 密码 | 角色 |
|------|------|------|
| `admin@example.com` | `admin123` | `admin` |

飞书 OAuth 登录需要在飞书开放平台配置应用凭证和回调地址白名单。

## 飞书组织同步

管理员可通过 API 手动触发组织同步，也可以在服务器上配置 cron 定时执行：

```bash
cd backend
source venv/bin/activate
python -m app.cli feishu-org-sync --trigger cron
```

只查看飞书返回的用户和部门路径、不写入 CRM 数据库时，使用：

```bash
python -m app.cli feishu-org-sync --dry-run
```

该命令会同步飞书部门与人员，存储完整部门路径；首次同步不做离职检测。后续同步中，上一轮在飞书、本轮不在飞书的用户会被标记为待交接并禁用登录。单次离职比例超过 10% 时会暂停离职标记，避免飞书接口异常导致误判。

管理员也可以通过 API 运维飞书集成：

- `GET /integrations/feishu/status`
- `POST /integrations/feishu/check`
- `GET /integrations/feishu/sync-preview`
- `POST /integrations/feishu/sync-users`
- `POST /integrations/feishu/work-report-reminders/run`

## 日报/周报与角色工作台

- 前端入口：`/dashboard`、`/work-reports`、`/work-reports/:id`
- 后端入口：`/dashboard/*`、`/work-reports/*`
- 日报按用户当天系统操作生成结构化草稿，保留备注补充；周报聚合本周日报并支持周备注。
- 日报/周报详情支持评论；被评论人通过通知中心收到站内通知并可跳转详情。
- 第一版默认支持 `admin`、`business`、`sales`、`technician`、`channel_ops`；`finance` 不参与日报/周报。
- 团队视图和工作台团队范围优先使用 `department_manager_id`，不要继续扩展销售专用的 `sales_leader_id`。

## 通知中心与待办中心

通知中心：

- 前端入口：`/notifications`
- 后端入口：`/notifications`
- 支持当前用户通知列表、未读数、单条已读、全部已读、业务对象跳转。
- 当前站内通知来源包括离职交接、日报/周报评论等；飞书外发和订阅规则仍为后续增强。
- Dashboard 旧通知接口已兼容返回真实通知数据。

待办中心：

- 前端入口：`/todos`
- 后端入口：`/todos`
- 首版采用派生待办模式，不新增通用 `todos` 表。
- 当前聚合来源包括跟进提醒、合同到期、工单处理、日报/周报未提交、离职交接待处理。
- 工作台待办摘要保留，点击“查看全部”进入待办中心。
- 首版不提供通用完成、延期、关闭动作；待办处理通过跳转到原业务对象完成。

## 离职交接

飞书组织同步识别到离职用户后，会将其标记为 `pending_handover` 并禁用登录。管理员可通过前端 `/handovers` 处理交接。当前已启用的交接 API 包括：

- `GET /handover/requests`
- `GET /handover/requests/{id}`
- `GET /handover/requests/{id}/assets-preview`
- `POST /handover/requests/{id}/assign`
- `POST /handover/requests/{id}/execute`
- `POST /handover/requests/{id}/cancel`

当前首版操作权限为 `admin`；部门负责人/当事人视图仍为后续增强。

## 测试

后端测试：

```bash
cd backend
source venv/bin/activate
APP_ENV=test pytest -q
```

前端测试：

```bash
cd frontend
npm test
```

当前前端已配置 Vitest 最小测试基线，覆盖 API URL/error detail 格式化、roles/channel_ops 角色映射、useRoleDashboard hook。前端回归建议为 `npm test` + `npm run build`。

前端生产构建：

```bash
cd frontend
npm run build
```

依赖与安全检查：

```bash
cd frontend
npm audit
```

## 相关文档

- [项目结构与架构](PROJECT_STRUCTURE.md)
- [API 文档](API_DOCUMENTATION.md)
- [架构设计](docs/architecture-design.md)
- [部署指南](docs/deployment-guide.md)
- [多环境部署与运维手册](docs/multi-env-deployment.md)
- [故障排查](docs/troubleshooting-guide.md)
- [角色系统设计](docs/role-system.md)
- [统一权限策略方案](docs/unified-permission-strategy-plan.md)
- [统一权限实施报告](docs/unified-permission-implementation-report.md)
- [派工集成指南](docs/dispatch-integration-guide.md)
- [派工测试报告](docs/dispatch-test-report.md)
- [飞书外勤审批设计](docs/feishu-field-work-approval-design.md)
- [销售目标重构方案](docs/sales_target_redesign.md)
- [销售目标实施说明](docs/sales_target_implementation.md)
- [安全整改记录](docs/security-remediation-2026-04-27.md)
- [审计整改完成报告](docs/audit-remediation-completion-2026-05-12.md)
- [销售任务管理完成计划](docs/sales-target-management-completion-plan-2026-05-12.md)
- [下一阶段业务模块建设计划](docs/next-phase-business-modules-plan-2026-05-12.md)
- [日报/周报与角色化工作台设计](docs/daily-weekly-report-and-role-dashboard-design-2026-05-13.md)
- [日报/周报与角色化工作台开发拆分计划](docs/daily-weekly-report-dashboard-implementation-plan-2026-05-13.md)
- [通知中心最小闭环建设计划](docs/notification-center-plan-2026-05-15.md)
- [任务/日程/提醒中心最小闭环建设计划](docs/todo-reminder-center-plan-2026-05-15.md)
- [项目联合 Review 计划](docs/project-review-plan-2026-05-15.md)
