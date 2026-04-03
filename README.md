# CRM System - 业财一体CRM系统

## 项目概述

这是一个基于FastAPI + React的现代化CRM系统，专为企业财务一体化（业财一体）场景设计。系统包含7个核心数据表，完全遵循《业财一体CRM系统落地方案》中定义的业务规范。

## 功能特性

- **7表完整实现**：终端客户档案、渠道/交易对象档案、商机管理、项目管理、合同管理、跟进记录、产品字典
- **自动编号系统**：支持CUS/CH/OPP/PRJ/PRD格式的自动编号，续保项目自动添加-SVC后缀
- **五条映射规则**：完整实现业财一体的5条核心业务规则
- **金蝶集成支持**：通过项目编号实现与金蝶系统的无缝对接
- **角色权限控制**：销售、商务、财务三重角色权限体系
- **实时协作功能**：多用户同时操作，实时通知和状态同步

## 技术栈

### 后端
- **框架**: FastAPI (Python 3.10+)
- **数据库**: PostgreSQL 14+
- **缓存**: Redis
- **部署**: Docker + Docker Compose

### 前端
- **框架**: React 18 + TypeScript
- **UI库**: Ant Design
- **状态管理**: Redux Toolkit
- **数据获取**: React Query
- **表单处理**: React Hook Form + Yup

## 快速开始

### 1. 环境准备

确保已安装以下工具：
- Docker 20.10+
- Docker Compose 2.0+
- Git

### 2. 克隆项目

```bash
git clone <repository-url>
cd crm-system
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库密码等敏感信息
```

### 4. 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

### 5. 访问应用

- **前端应用**: http://localhost:8080
- **后端API**: http://localhost:8000/docs (Swagger UI)
- **健康检查**: http://localhost:8000/health

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
├── backend/                    # FastAPI后端
│   ├── app/
│   │   ├── api/               # API路由
│   │   ├── core/              # 核心功能(配置,安全)
│   │   ├── models/            # 数据库模型
│   │   ├── schemas/           # Pydantic模式
│   │   ├── crud/              # CRUD操作
│   │   └── main.py            # 应用入口
│   ├── tests/                 # 后端测试
│   ├── alembic/               # 数据库迁移
│   └── requirements.txt       # Python依赖
├── frontend/                  # React前端
│   ├── public/                # 静态资源
│   ├── src/
│   │   ├── components/        # 可重用组件
│   │   ├── pages/             # 页面组件
│   │   ├── store/             # Redux存储
│   │   ├── services/          # API服务
│   │   └── App.tsx            # 主应用组件
│   └── package.json           # 前端依赖
├── docker-compose.yml         # Docker编排
└── README.md                  # 项目文档
```

## 阶段实施计划

### 阶段一：MVP核心功能 (4-6周)
- ✅ 项目结构和工具链设置
- ✅ 数据库Schema设计
- ✅ 核心API实现（CRUD + 认证）
- ✅ 前端基础架构（React Query + Ant Design）
- ✅ 数据迁移框架（SQLAlchemy ORM）
- ✅ 核心UI组件（8个列表页面 + 筛选 + 弹窗）
- ⏳ 执行数据迁移（从旧系统导入）
- ⏳ MVP业务逻辑（自动编号、商机转化等）

### 阶段二：业务逻辑完善 (3-4周)
- ⏳ 高级业务规则实现
- ⏳ 自动编号系统
- ⏳ 利润计算引擎
- ⏳ 续保检测和SVC后缀
- ⏳ 商机到项目转化流程
- ⏳ 飞书 OAuth 认证集成

## 当前服务状态

| 服务 | 地址 | 说明 |
|------|------|------|
| 后端 API | http://localhost:8000 | FastAPI 服务 |
| API 文档 | http://localhost:8000/docs | Swagger UI |
| 前端应用 | http://localhost:3002 | React 开发服务器 |
| PostgreSQL | 172.18.0.2:5432 | 数据库 |
| Redis | 172.18.0.3:6379 | 缓存（可选） |

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

### 安全与性能
- ✅ CORS安全配置（环境变量控制允许来源）
- ✅ JWT密钥管理（环境变量+缺失警告）
- ✅ 统一错误处理（axios interceptor）
- ✅ N+1查询优化（dashboard、reports）
- ✅ 数据一致性校验（目标分解金额校验）

### 后端 API
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

### 前端页面
- ✅ 登录页面
- ️ 飞书OAuth回调
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
- ️ 操作日志列表
- ✅ 销售漏斗报表
- ✅ 业绩统计报表
- ✅ 回款进度报表

### 数据库表
- ✅ users（用户/销售人员）
- ✅ products（产品字典）
- ✅ channels（渠道/交易对象）
- ✅ terminal_customers（终端客户）
- ✅ opportunities（商机）
- ✅ projects（项目）
- ✅ contracts（合同）
- ✅ follow_ups（跟进记录）

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
