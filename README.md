# CRM System

普悦业财一体 CRM 销管系统。主应用由 `FastAPI + React` 组成，覆盖线索、商机、项目、合同、客户、渠道、派工工单、知识库、报表与权限控制等核心能力。

## 项目状态

- 主应用目录：`backend/` + `frontend/`
- 后端架构：模块化 Router + Schema，main.py 为纯入口文件（~80行）
- 默认启动方式：`docker-compose` 或前后端本地分别启动
- 支持多环境部署：development / test / production
- 当前前端构建工具：`react-scripts`
- 当前前端本地开发端口：`3002`
- 当前 Docker 暴露端口：
  - 前端：`8081`
  - 后端：`8000`
  - PostgreSQL：`15432`
  - Redis：`6379`

## 核心模块

- 销管主链路：线索 -> 商机 -> 项目 -> 合同
- 客户与渠道：终端客户、渠道档案、渠道全景视图（8Tab）、渠道分配、执行计划、客户多渠道关系
- 派工模块：工单、技术员分配、派工记录、服务评价、知识库、Webhook 状态同步
- 工作台与报表：我的工作台、预警中心、销售漏斗、业绩统计、回款进度
- 系统能力：JWT 登录、飞书 OAuth、操作日志、通知、数据字典、自动编号
- 扩展能力：产品装机记录、财务专用客户视图、渠道绩效自动汇总

## 权限模型

| 角色 | 读权限 | 写权限 |
|------|--------|--------|
| `admin` | 全量数据 | 全量数据 |
| `business` | 全量业务数据 | 全量业务实体 |
| `finance` | 财务专用视图与财务相关实体 | 财务实体 + owner 校验 |
| `sales` | owner / channel scope | owner / channel scope |
| `technician` | 工单相关数据 | 仅自己被分配的工单场景 |

说明：
- `business` 当前被设计为"准管理员"，这是显式策略。
- `finance` 访问客户全景时走 `/customers/{id}/finance-view`。
- 主写路径使用 `assert_can_mutate_entity_v2` 做对象级授权校验。

## 技术栈

### 后端
- Python 3.11 / FastAPI / SQLAlchemy 2.x Async / PostgreSQL / Alembic / JWT+bcrypt / Redis

### 前端
- React 18 / TypeScript / Ant Design 5 / Redux Toolkit / TanStack Query / Axios

## 后端架构

重构后的后端采用完全模块化结构，main.py 仅作为入口文件：

```text
backend/app/
├── main.py                 # ~80行，仅 app 初始化 + include_router + /health
├── core/
│   ├── config.py           # 多环境配置（Settings）
│   ├── security.py         # JWT / 密码哈希
│   ├── dependencies.py     # 共享依赖（get_db, get_current_user）
│   ├── permissions.py      # RBAC 权限控制
│   └── channel_permissions.py  # 渠道级权限
├── models/                 # 31 个 SQLAlchemy 模型
├── schemas/                # 28 个 Pydantic Schema 文件
├── routers/                # 24 个独立 Router（142 个 API 路由）
└── services/               # 业务服务层
```

### Router 清单

| Router | 端点前缀 | 说明 |
|--------|---------|------|
| auth | /auth | 登录、飞书 OAuth |
| user | /users | 用户管理 |
| customer | /customers | 客户 CRUD |
| customer_views | /customers/{id}/full-view | 客户全景/财务视图 |
| lead | /leads | 线索管理 + 转商机 |
| opportunity | /opportunities | 商机管理 |
| contract | /contracts | 合同管理 |
| follow_up | /follow-ups | 跟进记录 |
| channel | /channels | 渠道管理 + 全景视图 |
| channel_assignment | /channel-assignments | 渠道分配 |
| unified_target | /unified-targets | 统一目标 |
| execution_plan | /execution-plans | 执行计划 |
| work_order | /work-orders | 工单管理 |
| evaluation | /evaluations | 服务评价 |
| knowledge | /knowledge | 知识库 |
| product | /products | 产品管理 |
| product_installation | /product-installations | 产品装机 |
| dispatch | /dispatch, /webhooks | 派工集成 + Webhook |
| customer_channel_link | /customer-channel-links | 客户多渠道关系 |
| report | /reports | 报表（漏斗/业绩/回款） |
| dashboard | /dashboard | 工作台 |
| alert | /alerts, /alert-rules | 预警中心 |
| sales_target | /sales-targets | 销售目标 |
| dict_item | /dict | 数据字典 |
| operation_log | /operation-logs | 操作日志 |

## 目录结构

```text
crm-system/
├── backend/
│   ├── app/
│   │   ├── core/              # 配置、认证、权限
│   │   ├── models/            # SQLAlchemy 模型（31个）
│   │   ├── routers/           # API 路由（24个）
│   │   ├── schemas/           # Pydantic Schema（28个）
│   │   ├── services/          # 业务服务
│   │   └── main.py            # 入口文件
│   ├── alembic/               # 数据库迁移（9个版本）
│   ├── tests/                 # pytest 测试（42个用例）
│   ├── .env.example           # 环境变量模板
│   ├── .env.test              # 测试环境模板
│   └── .env.production        # 生产环境模板
├── frontend/
│   ├── src/
│   │   ├── components/        # UI 组件
│   │   ├── hooks/             # 数据请求 hooks
│   │   ├── pages/             # 页面（16个）
│   │   ├── services/          # API 封装
│   │   ├── store/             # Redux 状态
│   │   ├── types/             # 类型定义
│   │   └── constants/         # 常量
│   ├── nginx.conf             # Nginx 配置（支持环境变量）
│   └── Dockerfile
├── docs/                       # 项目文档
├── docker-compose.yml          # Docker 编排（支持多环境）
└── README.md
```

## 快速开始

### 方式一：Docker Compose

```bash
# 复制环境变量模板
cp backend/.env.example backend/.env
# 编辑 .env 填入真实值（数据库密码、JWT密钥、飞书凭证等）

# 启动
docker-compose up -d --build
```

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:8081 |
| 后端 API | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |
| 健康检查 | http://localhost:8000/health |

### 方式二：本地开发

```bash
# 后端
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # 编辑填入真实值
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 前端（新终端）
cd frontend
npm install
PORT=3002 npm start
```

前端开发模式通过 `package.json` 的 `proxy` 字段将 API 请求代理到 `localhost:8000`。

## 多环境部署

系统支持 development / test / production 三套环境，详见 [多环境部署与运维手册](docs/multi-env-deployment.md)。

核心机制：
- 后端通过 `.env` 文件切换配置，所有环境敏感值从环境变量读取
- 前端 API 走相对路径 + Nginx 反代，不需要按环境分别构建
- 飞书 OAuth redirect_uri 从 `FRONTEND_PUBLIC_URL` 自动派生
- Docker 部署通过 `env_file` 注入环境变量

## 数据库

### 快速初始化（本地开发）

```bash
cd backend && source venv/bin/activate
python reset_db.py
python create_test_user.py
```

### Alembic 迁移（正式环境）

```bash
cd backend && source venv/bin/activate
alembic upgrade head
```

## 默认测试账号

| 邮箱 | 密码 | 角色 |
|------|------|------|
| admin@example.com | admin123 | admin |

支持飞书 OAuth 单点登录（需在飞书开放平台配置回调地址白名单）。

## 测试

```bash
cd backend && source venv/bin/activate
pytest tests/ -q    # 42 个测试用例
```

## 相关文档

- [多环境部署与运维手册](docs/multi-env-deployment.md)
- [架构设计](docs/architecture-design.md)
- [派工集成指南](docs/dispatch-integration-guide.md)
- [渠道集成实施方案](docs/channel-integration-implementation-plan.md)
- [故障排查](docs/troubleshooting-guide.md)

## 维护建议

- 新增写接口时复用 `assert_can_mutate_entity_v2`，避免权限分叉
- 新增 Router 后在 main.py 中 `include_router` 并创建对应 Schema 文件
- 更新权限模型、端口、启动方式时同步更新本文档
