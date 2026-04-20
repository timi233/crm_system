# 多环境部署与运维手册

> 适用版本：2026-04-17
> 适用环境：development / test / production

---

## 一、环境概览

| 环境 | 用途 | 前端地址 | 后端地址 | 数据库 |
|------|------|---------|---------|--------|
| development | 本地开发 | http://localhost:3002 | http://localhost:8000 | 本地 PostgreSQL |
| test | 测试验证 | https://crm-test.example.com | 同域 Nginx 反代 | 测试 PostgreSQL |
| production | 生产运行 | https://crm.example.com | 同域 Nginx 反代 | 生产 PostgreSQL |

## 二、配置体系

### 2.1 配置来源

所有环境敏感配置通过环境变量注入，后端使用 pydantic-settings 自动加载：

```
优先级：系统环境变量 > .env 文件 > config.py 默认值
```

### 2.2 核心环境变量

| 变量 | 说明 | 示例（dev） | 示例（prod） |
|------|------|------------|-------------|
| APP_ENV | 环境标识 | development | production |
| FRONTEND_PUBLIC_URL | 前端公开地址 | http://localhost:3002 | https://crm.example.com |
| BACKEND_PUBLIC_URL | 后端公开地址 | http://localhost:8000 | https://crm.example.com |
| ALLOWED_ORIGINS | CORS 允许源（逗号分隔） | http://localhost:3002 | https://crm.example.com |
| DATABASE_URL | 数据库连接串 | postgresql+asyncpg://user:pass@localhost:5432/crm_db | postgresql+asyncpg://user:pass@db:5432/crm_db |
| JWT_SECRET_KEY | JWT 签名密钥 | dev_secret | （强随机值） |
| FEISHU_APP_ID | 飞书应用 ID | cli_xxx | cli_xxx |
| FEISHU_APP_SECRET | 飞书应用密钥 | xxx | xxx |
| FEISHU_REDIRECT_URI | 飞书回调地址（可选） | 留空自动派生 | 留空自动派生 |
| UVICORN_HOST | 后端监听地址 | 0.0.0.0 | 0.0.0.0 |
| UVICORN_PORT | 后端监听端口 | 8000 | 8000 |

`FEISHU_REDIRECT_URI` 未设置时自动从 `FRONTEND_PUBLIC_URL + /auth/feishu/callback` 派生。

### 2.3 环境模板文件

```
backend/
├── .env.example      # 模板（提交到 git，不含真实密钥）
├── .env.test         # 测试环境模板
├── .env.production   # 生产环境模板
└── .env              # 实际使用（git 忽略）
```

部署时复制对应模板并填入真实值：

```bash
cp backend/.env.production backend/.env
# 编辑 .env 填入真实数据库密码、JWT密钥、飞书凭证
```

## 三、飞书 OAuth 配置

### 3.1 回调地址

飞书 OAuth 登录流程：前端跳转飞书授权页 → 用户授权 → 飞书回调前端页面（带 code）→ 前端调后端 `/auth/feishu/login` 换取 token。

每个环境的回调地址不同，需在飞书开放平台预先配置白名单：

| 环境 | 回调地址 |
|------|---------|
| development | http://localhost:3002/auth/feishu/callback |
| test | https://crm-test.example.com/auth/feishu/callback |
| production | https://crm.example.com/auth/feishu/callback |

### 3.2 飞书后台配置步骤

1. 登录 [飞书开放平台](https://open.feishu.cn)
2. 进入应用 → 安全设置 → 重定向 URL
3. 添加所有环境的回调地址
4. 确保应用已发布并具有 `authen:user_info` 权限

### 3.3 安全建议

- test 和 production 建议使用不同的飞书应用（不同 app_id/app_secret）
- OAuth state 参数已改为随机值，防止 CSRF 攻击
- 定期轮换 app_secret

## 四、CORS 配置

CORS 通过 `ALLOWED_ORIGINS` 环境变量控制，多个源用逗号分隔。

```env
# 开发环境
ALLOWED_ORIGINS=http://localhost:3002,http://127.0.0.1:3002

# 测试环境
ALLOWED_ORIGINS=https://crm-test.example.com

# 生产环境
ALLOWED_ORIGINS=https://crm.example.com
```

注意：当前配置 `allow_credentials=True`，不能使用 `*` 通配符。

## 五、前端 API 地址

### 5.1 推荐方案：相对路径 + Nginx 反代

前端默认使用相对路径请求 API（`REACT_APP_API_URL` 为空），由 Nginx 将 API 路径反代到后端。

优势：
- 前端镜像不需要按环境分别构建
- 无跨域问题（同域）
- 环境差异全在 Nginx 配置

### 5.2 开发模式

本地开发时，前端通过 `package.json` 的 `proxy` 字段代理到 `localhost:8000`：

```json
{
  "proxy": "http://localhost:8000"
}
```

### 5.3 备选方案：前后端分域名

如果前后端使用不同域名，设置 `REACT_APP_API_URL`：

```env
REACT_APP_API_URL=https://api-crm.example.com
```

注意：`REACT_APP_*` 是构建时变量，不同环境需要分别构建前端。

## 六、Docker 部署

### 6.1 基本部署

```bash
# 准备环境变量
cp backend/.env.production backend/.env

# 构建并启动
docker-compose up -d --build
```

### 6.2 docker-compose.yml 环境变量

后端服务已配置以下环境变量透传：

```yaml
backend:
  environment:
    - APP_ENV=${APP_ENV:-production}
    - FRONTEND_PUBLIC_URL=${FRONTEND_PUBLIC_URL}
    - ALLOWED_ORIGINS=${ALLOWED_ORIGINS}
    - FEISHU_APP_ID=${FEISHU_APP_ID}
    - FEISHU_APP_SECRET=${FEISHU_APP_SECRET}
    - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    - DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
```

### 6.3 Nginx 配置

前端 Nginx 支持通过环境变量设置 `server_name`：

```nginx
server {
    listen 80;
    server_name ${NGINX_SERVER_NAME};

    location / {
        root /usr/share/nginx/html;
        try_files $uri /index.html;
    }
    location /api/ {
        proxy_pass http://backend:8000/;
    }
}
```

Dockerfile 中通过 `envsubst` 在容器启动时渲染配置。

### 6.4 生产部署建议

- 后端端口不要直接暴露到公网，通过 Nginx/Ingress 反代
- 使用 HTTPS（Let's Encrypt 或企业证书）
- 数据库使用独立实例，不要和应用容器共用宿主机
- Redis 设置密码

## 七、数据库管理

### 7.1 迁移

```bash
cd backend && source venv/bin/activate

# 查看当前版本
alembic current

# 升级到最新
alembic upgrade head

# 回滚一个版本
alembic downgrade -1
```

### 7.2 备份与恢复

```bash
# 备份
pg_dump -h localhost -U crm_admin crm_db > backup_$(date +%Y%m%d).sql

# 恢复
psql -h localhost -U crm_admin crm_db < backup_20260417.sql
```

### 7.3 环境隔离

test 和 production 必须使用不同的数据库实例，避免测试数据污染生产。

## 八、监控与运维

### 8.1 健康检查

```bash
curl http://localhost:8000/health
# {"status":"healthy","timestamp":"..."}
```

### 8.2 日志查看

```bash
# Docker 日志
docker logs crm-backend --tail 100 -f
docker logs crm-frontend --tail 100 -f

# 本地开发日志直接在终端输出
```

### 8.3 常用运维命令

```bash
# 检查服务状态
docker-compose ps

# 重启单个服务
docker-compose restart backend

# 查看数据库连接
docker-compose exec db psql -U crm_admin -d crm_db -c "\conninfo"

# 运行测试
cd backend && source venv/bin/activate && pytest tests/ -q
```

### 8.4 故障排查

| 症状 | 可能原因 | 排查方法 |
|------|---------|---------|
| 飞书登录报 20028 | FEISHU_APP_ID 未配置或为空 | 检查 .env 中 FEISHU_APP_ID |
| 飞书登录后立即跳回登录页 | OAuth state 因后端重启丢失或旧回调 state 失效 | 重新点击飞书登录按钮发起新的授权流程；非生产环境已做宽松处理，生产环境仍需保持 state 有效 |
| CORS 错误 | ALLOWED_ORIGINS 未包含前端域名 | 检查 .env 中 ALLOWED_ORIGINS |
| 401 Unauthorized | JWT_SECRET_KEY 不一致 | 确认前后端使用同一密钥 |
| 数据库连接失败 | DATABASE_URL 错误 | 检查连接串、网络、防火墙 |
| 前端 API 404 | Nginx 反代配置错误 | 检查 nginx.conf 的 proxy_pass |

## 九、安全清单

- [ ] .env 文件不在版本控制中（.gitignore 已配置）
- [ ] 生产环境使用强随机 JWT_SECRET_KEY（至少 32 字符）
- [ ] 飞书 app_secret 定期轮换
- [ ] test/prod 使用不同的飞书应用
- [ ] 生产环境启用 HTTPS
- [ ] 数据库密码使用强密码
- [ ] 后端端口不直接暴露公网
- [ ] 定期备份数据库
