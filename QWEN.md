# CRM System - Qwen Code Context

## Project Overview

普悦业财一体 CRM 销管系统，覆盖线索、商机、项目、合同、客户、渠道、派工工单、知识库、报表与权限控制。

- **技术栈**: FastAPI + React 18 + TypeScript + PostgreSQL + Redis
- **后端**: Python 3.11 / FastAPI / SQLAlchemy 2.x Async / Alembic
- **前端**: React 18 / Ant Design 5 / Redux Toolkit / TanStack Query
- **当前端口**: 前端开发 `3002`，后端 `8000`，Docker 前端 `8081` / 后端 `8001`
- **默认账号**: `admin@example.com` / `admin123`

## System Boundaries

**当前 CRM 系统边界**: `backend/` + `frontend/`

仓库中可能存在 `QDmgt/`（渠道管理）和 `new_task_mgt/`（派工管理）等历史/外部系统目录：
- 仅可借鉴业务结构、字段设计、流程思路
- **不得**依赖、导入、调用、修改其运行代码
- 新功能必须重构到当前 CRM 系统边界内

## Quick Start

```bash
# Docker Compose（推荐）
cp backend/.env.example backend/.env
# 编辑 .env 填入真实值
docker-compose up -d --build

# 本地开发
cd backend && source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 前端（新终端）
cd frontend && PORT=3002 npm start
```

## Backend Structure

```
backend/app/
├── main.py                 # ~80行，仅 app 初始化 + include_router + /health
├── core/                   # 配置、认证、权限、策略
├── models/                 # 31 个 SQLAlchemy 模型
├── schemas/                # 28 个 Pydantic Schema
├── routers/                # 24 个独立 Router（142 个 API 路由）
└── services/               # 业务服务层
```

### Router 清单（24 个）

auth, user, customer, customer_views, lead, opportunity, contract, follow_up, channel, channel_assignment, unified_target, execution_plan, work_order, evaluation, knowledge, product, product_installation, dispatch, customer_channel_link, report, dashboard, alert, sales_target, dict_item, operation_log

### 权限模型（RBAC）

| 角色 | 读权限 | 写权限 |
|------|--------|--------|
| `admin` | 全量数据 | 全量数据 |
| `business` | 全量业务数据 | 全量业务实体 |
| `finance` | 财务专用视图 | 财务实体 + owner 校验 |
| `sales` | owner / channel scope | owner / channel scope |
| `technician` | 工单相关数据 | 仅自己被分配的工单 |

**关键**: 主写路径使用 `assert_can_mutate_entity_v2` 做对象级授权校验。新增写接口时复用，避免权限分叉。

## Frontend Structure

```
frontend/src/
├── components/    # Lists, Forms, Modals, Common
├── pages/         # 20+ 页面（客户全景、渠道、工作台、报表等）
├── hooks/         # 数据请求 hooks
├── services/      # API 封装
├── store/         # Redux 状态
├── types/         # 类型定义
└── constants/     # 常量
```

- 表单体验：客户/项目创建编辑使用抽屉(Drawer)样式
- 权限驱动 UI：基于用户能力控制组件可见性

## Key Rules

1. **新增 Router**: 在 `main.py` 中 `include_router` 并创建对应 Schema 文件
2. **写接口**: 复用 `assert_can_mutate_entity_v2`，避免权限分叉
3. **数据字典**: 通过 `seed_dict_data.py` 脚本管理
4. **Alembic 迁移**: 当前 head: `dispatch_record_work_order_id_integer`
5. **前端代理**: 开发模式通过 `package.json` 的 `proxy` 代理到 `localhost:8000`

## Security Findings (2026-04-27)

已完成安全修复（136 passed tests）：
- ✅ 销售用户自我升级漏洞修复
- ✅ 派工 Webhook 状态机保护
- ✅ 多技术员审批聚合逻辑修复
- ✅ 产品安装凭证过曝修复
- ✅ 前端路由级能力检查

## Deployment

支持 development / test / production 三套环境：
- 后端通过 `.env` 文件切换配置
- 前端 API 走相对路径 + Nginx 反代
- 飞书 OAuth `redirect_uri` 从 `FRONTEND_PUBLIC_URL` 自动派生

详细部署见 `docs/multi-env-deployment.md`

## Testing

```bash
cd backend && source venv/bin/activate
pytest tests/ -q    # 136 个测试用例

cd frontend && npm run build    # 前端构建验证
```

## Documentation

核心文档位于 `docs/`：
- `architecture-design.md` - 架构设计
- `multi-env-deployment.md` - 多环境部署
- `dispatch-integration-guide.md` - 派工集成
- `three-system-integration-design.md` - 三系统整合
- `security-remediation-2026-04-27.md` - 安全修复报告
- `refactor-plan.md` - main.py 拆分计划

## Database

- 当前 Alembic head: `dispatch_record_work_order_id_integer`
- 快速初始化：`python reset_db.py && python create_test_user.py && python seed_dict_data.py`
- 正式环境迁移：`alembic upgrade head`
