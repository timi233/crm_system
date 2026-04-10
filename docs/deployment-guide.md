# CRM销管系统部署与维护手册

## 系统概述

普悦销管系统是一个完整的客户关系管理(CRM)平台，包含线索管理、商机管理、项目管理、合同管理等核心功能模块。系统采用前后端分离架构：

- **前端**: React + Ant Design (端口 3002)
- **后端**: FastAPI + SQLAlchemy (端口 8000)  
- **数据库**: PostgreSQL
- **构建工具**: Docker (可选)

## 目录结构

```
crm-system/
├── backend/              # 后端服务
│   ├── app/             # 应用代码
│   │   ├── models/      # 数据库模型
│   │   ├── main.py      # 主应用入口
│   │   └── database.py  # 数据库配置
│   ├── venv/            # Python虚拟环境
│   └── requirements.txt  # Python依赖
├── frontend/             # 前端服务
│   ├── src/             # 源代码
│   ├── package.json     # 依赖配置
│   └── .env.local       # 环境变量
├── docs/                # 文档目录
└── .env                 # 环境配置文件
```

## 本地部署指南

### 1. 系统要求
- Ubuntu 22.04+ 或兼容Linux发行版
- Python 3.9+
- Node.js 16+
- PostgreSQL 12+
- Redis (可选，用于缓存)

### 2. 数据库配置

#### 安装PostgreSQL
```bash
sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib libpq-dev
sudo systemctl start postgresql
```

#### 创建数据库和用户
```bash
sudo -u postgres psql << EOF
CREATE USER crm_admin WITH PASSWORD 'crm_secure_pw_2024';
CREATE DATABASE crm_db OWNER crm_admin;
\q
EOF
```

### 3. 后端配置

#### 环境变量配置 (`backend/.env`)
```ini
# 数据库连接
POSTGRES_USER=crm_admin
POSTGRES_PASSWORD=crm_secure_pw_2024
POSTGRES_DB=crm_db
DB_HOST=localhost
DB_PORT=5432

# Redis缓存
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT认证
JWT_SECRET_KEY=RkRUvPjY8vaJlLSeVCbxEHPfnOpGH9vg-k1QX5AD2E0
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS配置
ALLOWED_ORIGINS=http://localhost:3002,http://127.0.0.1:3002

# 应用端口
APP_PORT=8000

# 数据库URL
DATABASE_URL=postgresql+asyncpg://crm_admin:crm_secure_pw_2024@localhost:5432/crm_db

# 飞书OAuth配置
FEISHU_APP_ID=cli_a9f5450adc781bd2
FEISHU_APP_SECRET=waXI7c1MdjbQ9INhPQ1cUb0UpBI82pby
FEISHU_REDIRECT_URI=http://localhost:3002/auth/feishu/callback
```

#### 安装Python依赖
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 初始化数据库
```bash
# 创建必要的数据库表
python reset_db.py
```

### 4. 前端配置

#### 环境变量 (`frontend/.env.local`)
```ini
REACT_APP_API_URL=http://localhost:8000
```

#### 安装Node依赖
```bash
cd frontend
npm install
```

### 5. 启动服务

#### 启动后端
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 启动前端
```bash
cd frontend
PORT=3002 npm start
```

### 6. 访问系统
- **Web界面**: http://localhost:3002
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 默认登录凭据

### 邮箱/密码登录
- **邮箱**: `admin@example.com`
- **密码**: `admin123`

### 飞书OAuth登录
系统支持飞书单点登录，需确保飞书开发者后台配置了正确的重定向URI：
- `http://localhost:3002/auth/feishu/callback`

## 已知问题与解决方案

### 1. CORS错误 "No 'Access-Control-Allow-Origin' header"

**症状**: 浏览器显示CORS错误，但实际是后端500错误

**原因**: 
- SQLAlchemy模型导入顺序错误
- Pydantic模型配置不正确
- API序列化逻辑有问题

**解决方案**:
1. 确保 `backend/app/models/__init__.py` 中所有模型按正确顺序导入
2. 使用Pydantic v2的 `model_config = ConfigDict(from_attributes=True)` 配置
3. API返回时直接返回ORM对象，不要手动拼接字典

### 2. API 500 Internal Server Error

**症状**: 特定API端点返回500错误

**常见原因及修复**:

#### a) 模型依赖问题
**错误信息**: `expression 'SalesTarget' failed to locate a name ('SalesTarget')`

**修复**: 在 `models/__init__.py` 中添加缺失的模型导入：
```python
from app.models.sales_target import SalesTarget
from app.models.nine_a import NineA
```

#### b) 数据库表缺失
**错误信息**: 表不存在或外键约束失败

**修复**: 创建缺失的表：
```sql
-- sales_targets 表
CREATE TABLE IF NOT EXISTS sales_targets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    target_type VARCHAR(20) NOT NULL,
    target_year INTEGER NOT NULL,
    target_period INTEGER NOT NULL,
    target_amount FLOAT NOT NULL,
    parent_id INTEGER REFERENCES sales_targets(id),
    created_at DATE,
    updated_at DATE
);

-- alerts 表  
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'info',
    title VARCHAR(255) NOT NULL,
    message TEXT,
    entity_type VARCHAR(50),
    entity_id INTEGER,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP
);

-- user_notification_reads 表
CREATE TABLE IF NOT EXISTS user_notification_reads (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    read_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, entity_type, entity_id, notification_type)
);
```

#### c) Pydantic序列化问题
**错误信息**: ORM对象序列化失败

**修复**: 
1. 更新Pydantic模型配置为v2标准
2. 移除API中的手动字典拼接
3. 使用 `selectinload` 正确加载关系（如需要）

### 3. 性能报告API问题

**症状**: `/reports/performance` 返回500错误

**原因**: 复杂的数据聚合逻辑导致异常

**临时解决方案**: 简化实现返回空数据
```python
@app.get("/reports/performance", response_model=PerformanceReportResponse)
async def get_performance_report(...):
    return PerformanceReportResponse(
        by_user=[],
        by_month=[],
        total_contract_amount=0.0,
        total_received_amount=0.0,
        total_pending_amount=0.0,
    )
```

## 核心API端点验证清单

启动系统后，建议验证以下API端点是否正常工作：

| 端点 | 方法 | 描述 | 预期状态 |
|------|------|------|----------|
| `/auth/login` | POST | 用户登录 | 200 |
| `/users` | GET | 获取用户列表 | 200 |
| `/leads` | GET | 获取线索列表 | 200 |
| `/opportunities` | GET | 获取商机列表 | 200 |
| `/dashboard/summary` | GET | 仪表板摘要 | 200 |
| `/dashboard/notifications` | GET | 通知列表 | 200 |
| `/alert-rules` | GET | 警报规则 | 200 |
| `/reports/performance` | GET | 性能报告 | 200 |

## 故障排除命令

### 检查服务状态
```bash
# 检查后端进程
ps aux | grep uvicorn

# 检查前端进程  
ps aux | grep react-scripts

# 检查数据库连接
sudo -u postgres psql -d crm_db -c "\dt"
```

### 重启服务
```bash
# 重启后端
pkill -f "uvicorn" && cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 重启前端
pkill -f "react-scripts" && cd frontend && PORT=3002 npm start
```

### 数据库重置
```bash
cd backend
source venv/bin/activate
python reset_db.py
```

## 系统集成说明

### 与派工系统集成计划

本CRM系统设计用于与IT服务派工系统集成，在以下模块添加派工申请入口：

1. **线索详情页**: 添加"派工申请"按钮
2. **商机详情页**: 添加"派工申请"按钮  
3. **项目详情页**: 添加"派工申请"按钮

**集成方案**:
- CRM系统作为编排方，调用派工系统API
- 使用飞书`open_id`作为跨系统用户身份锚点
- 通过服务间API Key进行认证
- 实现双向状态同步（Webhook回调）

### 集成API需求
派工系统需提供以下集成端点：
- `POST /api/integration/workorders` - 创建工单
- `GET /api/integration/workorders/{id}` - 查询工单状态
- Webhook回调 - 状态变更通知

## 维护最佳实践

### 1. 日常监控
- 定期检查API响应时间
- 监控数据库连接池使用情况
- 关注错误日志中的500错误

### 2. 升级策略
- 先在开发环境测试依赖升级
- 数据库变更需提供迁移脚本
- API版本兼容性保证

### 3. 备份策略
- 定期备份PostgreSQL数据库
- Git版本控制代码变更
- 配置文件版本管理

### 4. 安全考虑
- 定期更新依赖包安全补丁
- JWT密钥定期轮换
- 生产环境禁用调试模式

## 附录：常用测试脚本

### 创建测试用户
```bash
echo "12089735" | sudo -S -u postgres psql -d crm_db -c "INSERT INTO users (name, email, hashed_password, role, is_active) VALUES ('Admin User', 'admin@example.com', '\$2b\$12\$JUKJpdl/Cd.2a170atVJs.44JSc0LDtzKnaNX1Y2RDf3g0.VMZuXC', 'admin', true);"
```

### 创建测试数据
```sql
-- 终端客户
INSERT INTO terminal_customers (customer_code, customer_name, credit_code, customer_industry, customer_region, customer_owner_id, customer_status) VALUES ('C001', 'Test Customer', '91110108MA1234567X', 'IT服务', '华东', 1, 'Active');

-- 线索
INSERT INTO leads (lead_code, lead_name, terminal_customer_id, lead_stage, sales_owner_id, created_at) VALUES ('L001', 'Test Lead', 1, '初步接触', 1, '2026-04-10');

-- 项目
INSERT INTO projects (project_code, project_name, terminal_customer_id, product_ids, business_type, project_status, sales_owner_id, downstream_contract_amount) VALUES ('P001', 'Test Project', 1, ARRAY[1], 'New Business', 'active', 1, 100000.00);

-- 合同
INSERT INTO contracts (contract_code, contract_name, project_id, contract_direction, contract_status, contract_amount, signing_date) VALUES ('CT001', 'Test Contract', 1, 'Downstream', 'signed', 100000.00, '2026-04-01');
```

---

**文档版本**: 1.0  
**最后更新**: 2026-04-10  
**维护负责人**: Sisyphus