# CRM 系统项目结构与架构文档

## 1. 项目概述

普悦业财一体 CRM 销管系统是一个现代化的企业级客户关系管理系统，采用 **FastAPI + React** 技术栈构建，覆盖线索、商机、项目、合同、客户、渠道、派工工单、知识库、报表与权限控制等核心能力。

### 技术栈
- **后端**: Python 3.11 / FastAPI / SQLAlchemy 2.x Async / PostgreSQL / Alembic / JWT+bcrypt / Redis
- **前端**: React 18 / TypeScript / Ant Design 5 / Redux Toolkit / TanStack Query / Axios

## 2. 目录结构概览

```
crm-system/                              # Root project directory
├── backend/                             # Backend FastAPI application
│   ├── app/                            # Main application code
│   │   ├── core/                       # Core functionality (config, auth, security, permissions)
│   │   ├── models/                     # SQLAlchemy ORM models (31 models)
│   │   ├── routers/                    # API route handlers (24 routers, 142 endpoints)
│   │   ├── schemas/                    # Pydantic data validation schemas (28 schemas)
│   │   ├── services/                   # Business logic layer
│   │   └── main.py                     # FastAPI entry point (~80 lines)
│   ├── alembic/                        # Database migration system (11+ versions)
│   ├── tests/                          # Pytest unit and integration tests (25+ test files)
│   ├── scripts/                        # Utility scripts
│   └── requirements.txt                # Python dependencies
├── frontend/                           # React frontend application
│   ├── src/                           # Source code
│   │   ├── components/                # Reusable UI components
│   │   ├── pages/                     # Major application pages (20+ views)
│   │   ├── hooks/                     # React hooks for state management and API interactions
│   │   ├── services/                  # API service wrappers
│   │   ├── store/                     # Redux store configuration
│   │   ├── types/                     # TypeScript type definitions
│   │   └── utils/                     # Utility functions
│   ├── package.json                   # Node.js dependencies
│   └── Dockerfile                     # Frontend Docker configuration
├── docs/                              # Project documentation (19+ documents)
├── deploy/                            # Deployment configurations
└── docker-compose.yml                 # Container orchestration
```

## 3. 后端架构详解

### 3.1 模块化架构

后端采用完全模块化结构，`main.py` 仅作为入口文件（约80行），所有业务逻辑分散在独立的模块中。

#### 核心目录结构
- **`core/`**: 配置、认证、安全、权限控制
  - `config.py`: 多环境配置管理
  - `security.py`: JWT/密码哈希
  - `dependencies.py`: 共享依赖（数据库连接、当前用户）
  - `permissions.py`: RBAC权限控制（旧式）
  - `policy/`: 统一策略层（新式权限系统）
  - `channel_permissions.py`: 渠道级权限
  - `roles.py`: 角色定义

- **`models/`**: 31个SQLAlchemy模型
  - 客户 (`customer.py`)
  - 渠道 (`channel.py`, `channel_contact.py`)
  - 线索 (`lead.py`)
  - 商机 (`opportunity.py`)
  - 项目 (`project.py`)
  - 合同 (`contract.py`)
  - 工单 (`work_order.py`, `dispatch_record.py`)
  - 产品 (`product.py`, `product_installation.py`)
  - 字典项 (`dict_item.py`)
  - 等等...

- **`routers/`**: 24个独立Router（142个API路由）
  - `auth`: 登录、飞书OAuth
  - `user`: 用户管理
  - `customer`: 客户CRUD
  - `customer_views`: 客户全景/财务视图
  - `lead`: 线索管理 + 转商机
  - `opportunity`: 商机管理
  - `contract`: 合同管理
  - `follow_up`: 跟进记录
  - `channel`: 渠道管理 + 全景视图
  - `dict_item`: 数据字典
  - `report`: 报表（漏斗/业绩/回款）
  - `dashboard`: 工作台
  - 等等...

- **`schemas/`**: 28个Pydantic Schema文件
  - 请求/响应数据验证和序列化
  - 严格的类型定义

- **`services/`**: 业务服务层
  - `feishu_service.py`: 飞书集成
  - `alert_service.py`: 预警服务
  - `auto_number_service.py`: 自动编号
  - `finance_view_service.py`: 财务视图
  - `business_rules_service.py`: 业务规则
  - `dispatch_integration_service.py`: 派工集成

### 3.2 权限系统

#### RBAC角色模型
| 角色 | 读权限 | 写权限 | 说明 |
|------|--------|--------|------|
| `admin` | 全量数据 | 全量数据 | 系统管理员 |
| `business` | 全量业务数据 | 全量业务实体 | 准管理员 |
| `finance` | 财务专用视图与财务相关实体 | 财务实体 + owner校验 | 财务人员 |
| `sales` | owner / channel scope | owner / channel scope | 销售人员 |
| `technician` | 工单相关数据 | 仅自己被分配的工单场景 | 技术员 |

#### 权限架构演进
- **旧式实现**: 直接在路由中进行角色判断，使用 `apply_data_scope_filter()` 和 `assert_can_mutate_entity_v2()`
- **新式统一策略层**: 通过 `policy_service` 统一入口，遵循 `scope_query()`、`authorize()`、`authorize_create()` 接口模式
- **统一切换策略**: 新旧并存，逐步迁移，保持向后兼容

#### 核心组件
- **Policy Service**: 中央授权服务，包含26+个资源特定策略
- **Resource Policies**: 针对不同资源类型的具体权限实现
- **RBAC Middleware**: 路由和字段级别的访问控制
- **Dependency Injection**: 通过FastAPI依赖注入传递权限上下文

### 3.3 数据字典系统

#### 功能特性
- **标准化参考数据**: 提供业务操作的标准词汇表
- **层级结构支持**: 支持树状层级关系（如地区→城市）
- **动态管理**: 支持运行时动态添加/修改字典项
- **权限控制**: 所有角色可读，仅admin可写

#### 内置数据集
1. **地区字典**: 山东省及16个地级市的完整行政区划
2. **行业字典**: 政府单位、事业单位、制造业、医疗、金融等标准分类
3. **商机来源**: 客户推荐、网络推广、展会、电话营销等标准来源
4. **客户状态**: 潜在、活跃、已签约、休眠、流失等标准状态
5. **拜访目的**: 商务洽谈、技术支持、关系维护、产品培训等标准目的
6. **产品目录**: 产品类型→品牌→型号的完整层级结构

#### API接口
- `GET /dict/items`: 字典项列表（支持按类别和父ID筛选）
- `GET /dict/types`: 字典类别列表
- `POST/PUT/DELETE /dict/items`: CRUD操作（仅admin）

## 4. 前端架构详解

### 4.1 技术架构

#### 核心技术栈
- **React 18**: 组件化UI开发
- **TypeScript**: 静态类型检查
- **Redux Toolkit**: 全局状态管理
- **TanStack Query**: 服务器状态管理和缓存
- **Ant Design 5**: UI组件库
- **React Router 6**: 客户端路由
- **Axios**: HTTP客户端

### 4.2 状态管理架构

#### 全局状态（Redux Toolkit）
- **Auth State**: 认证信息、用户详情、权限能力
- **UI State**: 加载状态、侧边栏状态、通知管理

#### 服务器状态（TanStack Query）
- **Custom Hooks**: 每个实体都有专用的数据获取钩子（`useCustomers`、`useProjects`等）
- **Client-side Caching**: 自动缓存和失效机制
- **Mutation Handling**: 创建、更新、删除操作的统一处理

### 4.3 组件架构

#### 页面结构（/src/pages/）
- **20+个主要页面**: 包括客户全景、渠道管理、工作台、报表等
- **抽屉式表单**: 客户/项目创建编辑表单采用Drawer样式
- **权限驱动UI**: 基于用户能力控制组件可见性

#### 组件分类（/src/components/）
- **Lists**: 数据表格和列表组件
- **Forms**: 创建/编辑表单（通常为抽屉形式）
- **Modals**: 模态对话框
- **Common**: 共享UI组件（布局脚手架、通用组件）

### 4.4 API集成层

#### 核心特性
- **Centralized Axios Instance**: 统一的HTTP客户端配置
- **Authentication Interceptors**: 自动添加JWT令牌
- **Error Handling**: 统一的错误处理和用户反馈
- **Environment-aware URLs**: 环境感知的API基础URL

### 4.5 安全与权限

#### 权限控制
- **Capabilities System**: 基于用户能力的UI控制
- **Automatic Token Management**: JWT令牌自动存储到localStorage
- **Permission-based Controls**: 基于权限的UI元素控制（创建、编辑等）

## 5. 部署与运维

### 5.1 部署方式

#### Docker Compose（推荐）
```bash
cp backend/.env.example backend/.env
# 编辑 .env 填入真实值
docker-compose up -d --build
```

#### 本地开发
```bash
# 后端
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# 前端（新终端）
cd frontend
npm install
PORT=3002 npm start
```

### 5.2 环境配置

#### 多环境支持
- **development**: 本地开发环境
- **test**: 测试验证环境  
- **production**: 生产运行环境

#### 核心配置机制
- **后端**: 通过 `.env` 文件切换配置，敏感值从环境变量读取
- **前端**: API走相对路径 + Nginx反代，无需按环境分别构建
- **飞书OAuth**: `redirect_uri` 从 `FRONTEND_PUBLIC_URL` 自动派生
- **Docker部署**: 通过 `env_file` 注入环境变量

### 5.3 数据库管理

#### 当前Alembic Head
`target_uniqueness_001`

#### 初始化脚本
```bash
# 快速初始化（本地开发）
python reset_db.py
python create_test_user.py
python seed_dict_data.py  # 加载数据字典默认数据

# 正式环境迁移
alembic upgrade head
```

## 6. 测试与质量保证

### 6.1 测试覆盖
- **50+个测试用例**: 覆盖所有主要功能模块
- **单元测试**: 核心业务逻辑验证
- **集成测试**: API端到端测试
- **权限测试**: 各角色权限验证

### 6.2 质量工具
- **Git Pre-commit Hooks**: 代码格式化和质量检查
- **TypeScript**: 静态类型安全
- **Linter**: 代码风格一致性
- **Code Review Process**: 双人代码审查

## 7. 文档体系

### 7.1 核心文档
- **README.md**: 项目概览和快速开始指南
- **架构设计**: 系统架构详细说明
- **多环境部署手册**: 部署和运维指南
- **派工集成指南**: 外部系统集成文档
- **渠道集成实施方案**: 渠道管理详细方案

### 7.2 专项文档
- **统一权限策略方案**: 权限系统设计文档
- **角色系统设计**: RBAC角色模型说明
- **渠道管理模块化方案**: 渠道功能架构
- **渠道跟进优化方案**: 业务流程优化
- **测试环境包管理指南**: 开发环境配置

## 8. 维护建议

### 8.1 开发规范
- **新增写接口**: 复用 `assert_can_mutate_entity_v2`，避免权限分叉
- **新增Router**: 在 `main.py` 中 `include_router` 并创建对应Schema文件
- **数据字典**: 通过 `seed_dict_data.py` 脚本管理，默认数据应提交到版本控制
- **抽屉式表单**: 继承自统一的Drawer基础组件，保持UI一致性

### 8.2 版本控制
- **提交信息规范**: 遵循Conventional Commits规范
- **功能分支**: 大型功能应在独立分支开发
- **文档同步**: 更新功能时同步更新相关文档

## 9. 系统特色亮点

### 9.1 业务功能亮点
- **销管主链路**: 线索 → 商机 → 项目 → 合同的完整销售流程
- **渠道全景视图**: 渠道档案、跟进记录、线索、联系人等多Tab视图
- **派工集成**: 工单、技术员分配、派工记录、服务评价完整流程
- **财务专用视图**: 针对财务人员的特殊数据视图
- **自动化能力**: 自动编号、预警中心、销售漏斗、业绩统计

### 9.2 技术架构亮点
- **完全模块化**: 后端24个独立Router，前端20+个页面组件
- **统一权限策略**: 新旧权限系统平滑过渡，确保数据安全
- **数据字典标准化**: 内置完整的业务参考数据
- **抽屉式用户体验**: 改善表单操作体验
- **多环境支持**: 开发、测试、生产环境一键切换

---

*本文档基于项目当前状态生成，最后更新时间：2026年4月22日*