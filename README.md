# CRM System

普悦业财一体 CRM 销管系统。主应用由 `FastAPI + React` 组成，覆盖线索、商机、项目、合同、客户、渠道、派工工单、销售目标、知识库、报表、飞书集成与权限控制等核心能力。

## 项目状态

- 主应用目录：`backend/` + `frontend/`
- 后端入口：`backend/app/main.py`
- 后端架构：模块化 Router + Schema + Service + Policy
- 前端构建工具：`react-scripts`
- 前端本地开发端口：`3002`
- 后端本地/API 端口：`8000`
- Docker 暴露端口：
  - 前端：`8081`
  - 后端：`8000`
  - PostgreSQL：`5432`
  - Redis：`6379`

## 核心模块

- 销管主链路：线索 -> 商机 -> 项目 -> 合同
- 客户与渠道：终端客户、客户全景、财务视图、渠道档案、渠道联系人、渠道跟进、渠道线索、客户多渠道关系
- 派工与工单：工单、技术员分配、派工记录、状态同步、服务评价、知识库、飞书审批/卡片/WebSocket 集成
- 销售目标：年度/季度拆分、销售目标树、实际业绩录入、目标规则校验
- 工作台与报表：我的工作台、预警中心、销售漏斗、业绩统计、回款进度、财务导出
- 系统能力：JWT 登录、飞书 OAuth、角色权限、统一策略层、操作日志、通知、数据字典、自动编号
- 扩展能力：产品管理、实体产品、产品装机记录、金蝶集成入口、9A 相关模块

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

说明：

- `business` 当前被设计为准管理员角色。
- `finance` 访问客户全景时走 `/customers/{id}/finance-view`。
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
| `financials` / `kingdee_integration` | 财务导出、金蝶集成 |
| `report` / `dashboard` / `alert` | 报表、工作台、预警 |
| `dict_item` | 数据字典 |
| `operation_log` | 操作日志 |
| `nine_a` | 9A 相关能力 |

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
│   ├── .env.example           # 开发环境变量模板
│   ├── .env.test              # 测试环境变量模板
│   └── .env.production        # 生产环境变量模板
├── frontend/
│   ├── src/
│   │   ├── components/        # UI 组件
│   │   ├── hooks/             # 数据请求 hooks
│   │   ├── pages/             # 页面
│   │   ├── services/          # API 封装
│   │   ├── store/             # Redux 状态
│   │   ├── types/             # 类型定义
│   │   └── constants/         # 常量
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

前端开发服务默认运行在 `http://localhost:3002`，并通过 `frontend/package.json` 的 `proxy` 将 API 请求代理到 `http://localhost:8000`。

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

## 测试

后端测试：

```bash
cd backend
source venv/bin/activate
pytest tests/ -q
```

前端测试：

```bash
cd frontend
npm test
```

前端生产构建：

```bash
cd frontend
npm run build
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
