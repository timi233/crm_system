# CRM System - 普悦业财一体CRM销管系统

> 普悦销管系统 — 企业级客户关系管理平台，集成线索、商机、项目、合同、渠道管理、派工工单等核心业务模块。

## 项目概述

这是一个基于 **FastAPI + React** 的现代化 CRM 销管系统，专为企业财务一体化（业财一体）场景设计。系统以销管为核心，将渠道管理和派工系统作为附属模块深度整合，实现 **三系统合一** 的统一架构。

### 核心架构

```
┌──────────────────────────────────────────────────┐
│              普悦 CRM 销管系统                     │
├──────────────────────────────────────────────────┤
│  【销管核心】 线索 → 商机 → 项目 → 合同            │
│  【渠道模块】 渠道档案、目标分配、执行计划、全景视图  │
│  【派工模块】 工单管理、技术员调度、服务评价、知识库  │
│  【统一用户】 销售 + 技术 + 渠道管理，飞书OAuth单点登录│
│  【工作台】   业绩目标、预警中心、团队排行榜、报表    │
└──────────────────────────────────────────────────┘
```

## 功能特性

### 核心业务
- **完整业务链路**：线索 → 商机 → 项目 → 合同全生命周期管理
- **自动编号系统**：`PYCRM-{TYPE}-{YYYYMMDD}-{SEQ}` 格式自动编号
- **渠道管理模块**：渠道档案、目标分配、执行计划追踪、渠道全景视图
- **派工工单模块**：从线索/商机/项目一键创建派工，工单全生命周期管理
- **知识库 & 服务评价**：工单评价反馈 + 知识库沉淀
- **金蝶集成支持**：通过项目编号实现与金蝶系统的无缝对接

### 工作台 & 报表
- **我的工作台**：业绩目标、待办事项、快捷入口、漏斗速览
- **预警中心**：5 种预警规则（待跟进、商机停滞、目标未达成等）
- **团队排行榜**：销售业绩实时排名
- **销售漏斗报表**：线索→商机→项目→合同完整业务漏斗
- **业绩统计报表**：销售人员业绩多维分析
- **回款进度报表**：合同回款跟踪

### 集成 & 安全
- **飞书 OAuth**：单点登录 + 跨系统用户身份统一（`open_id` 锚点）
- **派工系统集成**：HTTP API + Webhook 双向同步
- **角色权限控制**：销售、商务、财务、技术员多角色体系
- **操作审计日志**：关键操作全记录

## 技术栈

### 后端
- **框架**: FastAPI 0.104+ (Python 3.10+)
- **ORM**: SQLAlchemy 2.0 (Async)
- **数据库**: PostgreSQL 14+
- **缓存**: Redis 7
- **认证**: JWT (python-jose) + bcrypt + 飞书 OAuth
- **数据验证**: Pydantic 2.5
- **部署**: Docker + Docker Compose

### 前端
- **框架**: React 18 + TypeScript
- **UI 库**: Ant Design 5.12
- **状态管理**: Redux Toolkit + React Query (TanStack)
- **路由**: React Router v6
- **表单**: React Hook Form + Yup
- **图表**: ECharts + echarts-for-react
- **HTTP**: Axios

## 快速开始

### 方式一：Docker Compose（推荐）

#### 1. 环境准备

确保已安装：
- Docker 20.10+
- Docker Compose 2.0+
- Git

#### 2. 克隆 & 配置

```bash
git clone <repository-url>
cd crm-system
cp .env.example .env
# 编辑 .env 配置数据库密码、JWT密钥、飞书OAuth等
```

#### 3. 启动服务

```bash
docker-compose up -d
docker-compose ps   # 查看服务状态
```

#### 4. 访问应用

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端应用 | http://localhost:8081 | React 生产服务器 (Nginx) |
| 后端 API | http://localhost:8000 | FastAPI 服务 |
| API 文档 | http://localhost:8000/docs | Swagger UI (交互式) |
| 健康检查 | http://localhost:8000/health | 服务健康状态 |

### 方式二：本地开发

#### 后端

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端

```bash
cd frontend
npm install
PORT=3002 npm start
```

### 数据库初始化

```bash
# 重置并创建所有数据库表
cd backend && source venv/bin/activate
python reset_db.py

# 创建测试管理员用户
python create_test_user.py
```

### 默认登录凭据

| 方式 | 账号 | 密码 |
|------|------|------|
| 邮箱登录 | `admin@example.com` | `admin123` |
| 飞书 OAuth | 需配置 `FEISHU_APP_ID` / `FEISHU_APP_SECRET` | - |

## 数据库设置

### 初始数据库迁移

首次启动后，需要运行数据库迁移：

```bash
# 进入backend容器
docker-compose exec backend bash

# 运行初始数据库脚本
psql -h db -U postgres -d crm_db -f /app/alembic/versions/0001_initial_schema.sql
```

### 数据库连接信息

- **Host**: db (Docker内部) 或 localhost (外部)
- **Port**: 5432
- **Database**: crm_db
- **User**: postgres
- **Password**: 从.env文件获取

## 开发指南

### 后端开发

```bash
# 进入backend目录
cd backend

# 安装依赖
pip install -r requirements.txt

# 本地运行 (开发模式)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端开发

```bash
# 进入frontend目录  
cd frontend

# 安装依赖
npm install

# 本地运行 (开发模式)
npm start
```

## 目录结构

```
crm-system/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/            # API 路由 (v1) - 11个路由模块
│   │   ├── core/              # 核心配置、安全
│   │   ├── crud/              # CRUD 操作层
│   │   ├── models/            # SQLAlchemy 模型 (26+ 个实体)
│   │   ├── schemas/           # Pydantic 模式
│   │   ├── services/          # 业务服务层 (含飞书集成、自动编号等)
│   │   ├── middleware/        # RBAC 中间件
│   │   └── main.py            # 应用入口 (5000+ 行)
│   ├── alembic/               # 数据库迁移
│   ├── sql/                   # 原生 SQL 脚本
│   └── tools/                 # 辅助工具脚本
├── frontend/                  # React 前端
│   ├── src/
│   │   ├── pages/             # 页面组件 (13+ 个详细页面)
│   │   ├── components/        # 可复用组件
│   │   ├── services/          # API 服务层
│   │   ├── hooks/             # 自定义 Hooks
│   │   ├── store/             # Redux 状态管理
│   │   ├── types/             # TypeScript 类型定义
│   │   └── config/            # 配置文件
│   └── nginx.conf             # Nginx 生产配置
├── docs/                      # 项目文档
│   ├── architecture-design.md         # 系统架构设计
│   ├── deployment-guide.md            # 部署与维护手册
│   ├── dispatch-integration-guide.md  # 派工集成指南
│   ├── three-system-integration-design.md  # 三系统整合方案
│   ├── dispatch-merge-design.md       # 派工合并设计
│   ├── dispatch-test-report.md        # 派工测试报告
│   └── troubleshooting-guide.md       # 故障排除指南
├── new_task_mgt/              # 任务管理子项目 (独立的Node.js + Vue系统)
├── QDmgt/                     # 渠道管理子项目 (独立的FastAPI + React系统)
├── docker-compose.yml         # Docker 编排 (生产环境)
├── quick-start.sh             # 一键启动脚本
└── .env.example               # 环境变量模板
```

## 三系统集成架构

本项目采用 **微前端 + 微服务** 架构，包含三个相互集成的子系统：

### 1. 主CRM系统 (backend/frontend)
- **职责**: 核心业务流程管理（线索→商机→项目→合同）
- **技术栈**: FastAPI + React + PostgreSQL
- **集成点**: 提供统一用户认证、主数据管理、工作台聚合

### 2. 渠道管理系统 (QDmgt/)
- **职责**: 渠道档案管理、目标分配、执行计划追踪
- **技术栈**: FastAPI + React + PostgreSQL  
- **集成方式**: 共享用户表、API调用、数据同步

### 3. 派工系统 (new_task_mgt/)
- **职责**: 工单管理、技术员调度、服务评价
- **技术栈**: Node.js + Express + Vue + SQLite
- **集成方式**: HTTP API + Webhook 双向同步

### 集成数据流
```
CRM系统 → (创建工单) → 派工系统
派工系统 → (状态更新) → CRM系统 (Webhook)
←→ 统一用户认证 ←→
←→ 渠道数据同步 ←→
```

## 当前服务状态

| 服务 | 地址 | 说明 |
|------|------|------|
| 后端 API | http://localhost:8000 | FastAPI 服务 |
| API 文档 | http://localhost:8000/docs | Swagger UI |
| 前端应用 | http://localhost:8081 | React 生产服务器 (Nginx) |
| PostgreSQL | 172.18.0.2:5432 | 数据库 |
| Redis | 172.18.0.3:6379 | 缓存 |

## 已实现功能

### 核心业务功能
- ✅ 线索管理（Leads）- 线索录入、转化商机、阶段管理
- ✅ 商机管理（Opportunities）- 商机跟进、9A分析、转化项目
- ✅ 项目管理（Projects）- 项目生命周期管理
- ✅ 合同管理（Contracts）- 合同签订、回款计划
- ✅ 跟进记录（Follow-ups）- 跟进提醒、记录查询
- ✅ 产品字典（Products）- 产品信息管理
- ✅ 渠道管理（Channels）- 渠道档案管理
- ✅ 终端客户（Customers）- 客户信息管理
- ✅ 用户管理（Users）- 用户权限、角色管理
- ✅ 操作日志（Operation Logs）- 操作审计
- ✅ 数据字典（Dict Items）- 系统字典配置

### 工作台与报表
- ✅ 我的工作台 - 业绩目标、待办事项、快捷入口、漏斗速览
- ✅ 预警中心 - 5种预警规则（待跟进、商机停滞、目标未达成等）
- ✅ 目标管理 - 年目标创建、季度分解、月度自动生成
- ✅ 团队排行榜 - 销售业绩排名
- ✅ 通知中心 - 新线索、新商机、成交等通知提醒
- ✅ 销售漏斗报表 - 业务流程展示（线索→商机→项目→合同）
- ✅ 业绩统计报表 - 销售人员业绩分析
- ✅ 回款进度报表 - 合同回款跟踪

### 技术实现
- ✅ 飞书OAuth集成
- ✅ 自动编号系统（PYCRM-{TYPE}-{YYYYMMDD}-{SEQ}）
- ✅ 详情页独立页面设计（Tabs布局）
- ✅ 工作台快捷按钮（新建页面跳转）
- ✅ RBAC权限控制中间件
- ✅ 异步数据库操作（SQLAlchemy 2.0 Async）

### 安全与性能
- ✅ CORS安全配置（环境变量控制允许来源）
- ✅ JWT密钥管理（环境变量+缺失警告）
- ✅ 统一错误处理（axios interceptor）
- ✅ N+1查询优化（dashboard、reports）
- ✅ 数据一致性校验（目标分解金额校验）

### 后端 API (11个路由模块)
- ✅ 用户认证（JWT + bcrypt）
- ✅ 用户管理 CRUD
- ✅ 终端客户 CRUD
- ✅ 产品字典 CRUD
- ✅ 渠道档案 CRUD
- ✅ 商机管理 CRUD
- ✅ 项目管理 CRUD
- ✅ 合同管理 CRUD
- ✅ 跟进记录 CRUD
- ✅ 线索管理 CRUD
- ✅ 目标管理 CRUD
- ✅ 预警规则 CRUD
- ✅ 操作日志查询
- ✅ 派工工单 CRUD
- ✅ 知识库管理
- ✅ 金蝶集成接口

### 前端页面 (13+ 详细页面)
- ✅ 登录页面
- ✅ 飞书OAuth回调
- ✅ 我的工作台
- ✅ 终端客户列表（筛选 + 新建页面）
- ✅ 产品字典列表（筛选 + 弹窗 CRUD）
- ✅ 渠道档案列表（筛选 + 详情页）
- ✅ 商机管理列表（筛选 + 新建页面）
- ✅ 项目管理列表（筛选 + 详情页）
- ✅ 合同管理列表（筛选 + 新建页面）
- ✅ 跟进记录列表（筛选 + 新建页面）
- ✅ 线索管理列表（筛选 + 新建页面）
- ✅ 用户管理列表（筛选 + 弹窗 CRUD）
- ✅ 目标管理列表（年目标分解）
- ✅ 预警规则列表
- ✅ 操作日志列表
- ✅ 销售漏斗报表
- ✅ 业绩统计报表
- ✅ 回款进度报表
- ✅ 工单详情页面

## 数据库表

系统共包含 **26+ 核心数据表**，按模块划分：

### 销管核心
| 表名 | 说明 |
|------|------|
| `users` | 统一用户表（销售/技术/渠道管理/管理员） |
| `terminal_customers` | 终端客户档案 |
| `leads` | 线索管理（含转化商机追踪） |
| `opportunities` | 商机管理（含 9A 分析） |
| `projects` | 项目管理（全生命周期） |
| `contracts` | 合同管理（上/下游合同 + 回款计划） |
| `follow_ups` | 跟进记录 |
| `products` | 产品字典 |
| `channels` | 渠道/交易对象档案（增强版） |

### 渠道管理模块
| 表名 | 说明 |
|------|------|
| `channel_assignments` | 渠道用户分配 |
| `unified_targets` | 统一目标（个人/渠道） |
| `execution_plans` | 执行计划追踪 |

### 派工模块
| 表名 | 说明 |
|------|------|
| `work_orders` | 工单完整生命周期 |
| `work_order_technicians` | 工单-技术员关联 |
| `dispatch_records` | 派工记录（CRM 侧追踪） |
| `evaluations` | 服务评价 |
| `knowledge` | 知识库 |

### 系统支撑
| 表名 | 说明 |
|------|------|
| `sales_targets` | 销售目标（年/季/月分解） |
| `alert_rules` | 预警规则 |
| `operation_logs` | 操作审计日志 |
| `notifications` | 系统通知 |
| `user_notification_reads` | 用户通知已读状态 |
| `dict_items` | 数据字典配置 |
| `auto_numbers` | 自动编号序列 |
| `nine_a` | 商机 9A 分析记录 |
| `entity_products` | 实体-产品关联 |
| `customer_autocomplete` | 客户联想输入 |

## 测试

### 后端测试

```bash
cd backend
pytest tests/
```

### 前端测试

```bash
cd frontend  
npm test
```

## 部署

### 生产部署

修改`docker-compose.yml`中的配置，使用生产环境的环境变量和SSL证书。

### 备份策略

- **数据库**: 每日全量备份 + 每小时增量备份
- **文件存储**: 实时同步到对象存储(S3/Azure Blob)

## 贡献指南

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 许可证

[MIT License](LICENSE)

## 联系方式

项目经理: [Your Name]  
邮箱: [your.email@example.com]