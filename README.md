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
- 🔄 核心API实现
- 🔄 前端基础架构
- 🔄 数据迁移框架
- 🔄 核心UI组件
- 🔄 执行数据迁移
- 🔄 MVP业务逻辑

### 阶段二：业务逻辑完善 (3-4周)
- 🔄 高级业务规则实现
- 🔄 自动编号系统
- 🔄 利润计算引擎
- 🔄 续保检测和SVC后缀
- 🔄 商机到项目转化流程

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
