# CRM System

普悦业财一体 CRM 销管系统。主应用由 `FastAPI + React` 组成，覆盖线索、商机、项目、合同、客户、渠道、派工工单、知识库、报表与权限控制等核心能力。

## 项目状态

- 主应用目录：`backend/` + `frontend/`
- 默认启动方式：`docker-compose` 或前后端本地分别启动
- 当前前端构建工具：`react-scripts`，不是 Vite
- 当前前端本地开发端口：`3002`
- 当前 Docker 暴露端口：
  - 前端：`8081`
  - 后端：`8000`
  - PostgreSQL：`15432`
  - Redis：`6379`

仓库中还包含 `QDmgt/` 和 `new_task_mgt/` 两个独立目录，但主应用启动和日常开发不依赖它们。

## 核心模块

- 销管主链路：线索 -> 商机 -> 项目 -> 合同
- 客户与渠道：终端客户、渠道档案、渠道全景视图、渠道分配、执行计划
- 派工模块：工单、技术员分配、派工记录、服务评价、知识库
- 工作台与报表：我的工作台、预警中心、销售漏斗、业绩统计、回款进度
- 系统能力：JWT 登录、飞书 OAuth、操作日志、通知、数据字典、自动编号
- 扩展能力：产品装机记录、财务专用客户视图

## 权限模型

当前代码和文档已对齐，权限语义如下：

| 角色 | 读权限 | 写权限 |
|------|--------|--------|
| `admin` | 全量数据 | 全量数据 |
| `business` | 全量业务数据 | 全量业务实体 |
| `finance` | 财务专用视图与财务相关实体 | 财务实体 + owner 校验 |
| `sales` | owner / channel scope | owner / channel scope |
| `technician` | 工单相关数据 | 仅自己被分配的工单场景 |

说明：

- `business` 当前被设计为“准管理员”，这是显式策略，不是偶然放宽。
- `finance` 访问客户全景时应走 `/customers/{id}/finance-view`，不会再复用普通 `full-view`。
- 主写路径当前使用 `assert_can_mutate_entity_v2` 做对象级授权校验。

## 技术栈

### 后端

- Python 3.11
- FastAPI
- SQLAlchemy 2.x Async
- PostgreSQL
- Alembic
- JWT / bcrypt
- Redis

### 前端

- React 18
- TypeScript
- Ant Design 5
- Redux Toolkit
- TanStack Query
- Axios
- `react-scripts`

## 目录结构

```text
crm-system/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── core/              # 配置、认证、权限
│   │   ├── crud/              # 基础 CRUD
│   │   ├── models/            # SQLAlchemy 模型
│   │   ├── routers/           # 拆分路由
│   │   ├── schemas/           # Pydantic schema
│   │   ├── services/          # 业务服务
│   │   └── main.py            # 主应用入口
│   ├── alembic/               # 迁移脚本
│   ├── sql/                   # SQL 初始化/字典脚本
│   ├── tests/                 # 后端测试
│   ├── reset_db.py            # 重建表结构
│   └── create_test_user.py    # 创建测试管理员
├── frontend/                   # React 前端
│   ├── src/
│   │   ├── components/        # 组件
│   │   ├── hooks/             # 数据请求 hooks
│   │   ├── pages/             # 页面
│   │   ├── services/          # API 封装
│   │   ├── store/             # Redux 状态
│   │   ├── types/             # 类型定义
│   │   └── constants/         # 常量
│   ├── package.json
│   └── nginx.conf
├── docs/                       # 架构、部署、派工集成说明
├── docker-compose.yml
├── quick-start.sh
└── README.md
```

## 快速开始

### 方式一：Docker Compose

1. 复制环境变量：

```bash
cp .env.example .env
```

2. 按需修改 `.env` 中的数据库密码、JWT 密钥等。

3. 启动服务：

```bash
docker-compose up -d --build
```

4. 访问：

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:8081 |
| 后端 API | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |
| 健康检查 | http://localhost:8000/health |
| PostgreSQL | localhost:15432 |
| Redis | localhost:6379 |

### 方式二：本地开发

#### 1. 后端

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

本地开发建议准备 `.env`，至少包含：

```env
DATABASE_URL=postgresql+asyncpg://crm_admin:your_password@localhost:5432/crm_db
JWT_SECRET_KEY=change_me
APP_PORT=8000
```

启动后端：

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 2. 前端

```bash
cd frontend
npm install
PORT=3002 npm start
```

如果后端不在 `http://localhost:8000`，请设置：

```env
REACT_APP_API_URL=http://your-backend-host:8000
```

## 数据库初始化

项目当前同时存在两套能力：

- 快速本地初始化：`reset_db.py`
- 迁移管理：`alembic`

### 快速初始化

适合本地重建测试环境：

```bash
cd backend
source venv/bin/activate
python reset_db.py
python create_test_user.py
```

### Alembic 迁移

如果你按迁移链维护数据库：

```bash
cd backend
source venv/bin/activate
alembic upgrade head
```

## 默认测试账号

执行 `python create_test_user.py` 后会生成：

| 邮箱 | 密码 | 角色 |
|------|------|------|
| `admin@example.com` | `admin123` | `admin` |

登录接口：

- `POST /auth/login`
- 飞书 OAuth 回调页面：`/auth/feishu/callback`

## 常用命令

### 后端

```bash
cd backend
source venv/bin/activate
pytest tests/
python -m py_compile app/main.py app/core/dependencies.py app/core/permissions.py
```

### 前端

```bash
cd frontend
npm run build
npm test
```

## 当前实现说明

- 前端通过 Axios interceptor 统一处理大部分错误提示。
- `authSlice` 当前会同时持久化 `token` 和 `user`，用于刷新后恢复角色信息。
- 客户全景页按角色分流：
  - `finance` -> `/customers/{id}/finance-view`
  - 其他业务角色 -> `/customers/{id}/full-view`
- `WorkOrderList` 当前仍存在删除失败时本地 toast 与全局拦截器重复提示的低风险问题，后续建议统一错误展示责任边界。

## 相关文档

- [架构设计](docs/architecture-design.md)
- [部署指南](docs/deployment-guide.md)
- [派工集成指南](docs/dispatch-integration-guide.md)
- [三系统整合设计](docs/three-system-integration-design.md)
- [故障排查](docs/troubleshooting-guide.md)

## 维护建议

- 新增写接口时优先复用 `assert_can_mutate_entity_v2`，避免权限分叉。
- 新增前端页面时尽量复用全局错误处理，不要在局部重复 `message.error(...)`。
- 更新权限模型、端口、启动方式时，应同时更新 `README.md` 和 `docs/architecture-design.md`。
