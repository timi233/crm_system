# 系统运维文档

## 服务监听配置规范

### ⚠️ 重要原则

**所有服务必须监听 `0.0.0.0` 而非 `localhost` 或 `127.0.0.1`**

原因：
- 允许局域网内其他设备访问
- 支持容器化部署和网络代理
- 确保服务在所有网络接口上可访问
- 避免外部访问时的连接拒绝错误

---

## 后端服务配置

### Systemd 服务配置

配置文件：`/etc/systemd/system/crm-backend.service`

```ini
[Unit]
Description=CRM Backend Service
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=simple
User=pytc
Group=pytc
WorkingDirectory=/home/pytc/crm_system/backend
Environment="PATH=/home/pytc/crm_system/backend/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/home/pytc/crm_system/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=crm-backend

[Install]
WantedBy=multi-user.target
```

**关键配置项**：
- `--host 0.0.0.0`：监听所有网络接口
- `--port 8000`：后端API端口

### 验证监听状态

```bash
# 检查端口监听
ss -tuln | grep :8000

# 应显示
tcp   LISTEN 0      2048   0.0.0.0:8000   0.0.0.0:*
```

---

## 前端服务配置

### Systemd 服务配置

配置文件：`/etc/systemd/system/crm-frontend.service`

```ini
[Unit]
Description=CRM Frontend Service
After=network.target crm-backend.service
Wants=crm-backend.service

[Service]
Type=simple
User=pytc
Group=pytc
WorkingDirectory=/home/pytc/crm_system/frontend
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="PORT=8081"
Environment="HOST=0.0.0.0"
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=crm-frontend

[Install]
WantedBy=multi-user.target
```

**关键配置项**：
- `Environment="HOST=0.0.0.0"`：React开发服务器监听所有网络接口
- `Environment="PORT=8081"`：前端服务端口

### 前端环境配置

配置文件：`/home/pytc/crm_system/frontend/.env`

```env
PORT=8081
HOST=0.0.0.0
```

### 开发代理配置

配置文件：`/home/pytc/crm_system/frontend/src/setupProxy.js`

```javascript
const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function (app) {
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://localhost:8000',  // 代理目标，服务器端访问
      changeOrigin: true,
      pathRewrite: { '^/api': '' },
    })
  );
};
```

**说明**：
- 代理配置中的 `target: 'http://localhost:8000'` 是正确的
- 这是Node.js开发服务器在服务端访问后端API的地址
- 不需要修改为 `0.0.0.0`

### 验证监听状态

```bash
# 检查端口监听
ss -tuln | grep :8081

# 应显示
tcp   LISTEN 0      511   0.0.0.0:8081   0.0.0.0:*
```

---

## 服务管理命令

### 查看服务状态

```bash
# 查看所有服务状态
sudo systemctl status crm-backend
sudo systemctl status crm-frontend

# 或使用项目脚本
./crmctl.sh status
```

### 启动/停止/重启服务

```bash
# 使用 systemctl
sudo systemctl start crm-backend
sudo systemctl stop crm-backend
sudo systemctl restart crm-backend

sudo systemctl start crm-frontend
sudo systemctl stop crm-frontend
sudo systemctl restart crm-frontend

# 或使用项目脚本
./crmctl.sh start          # 启动所有服务
./crmctl.sh stop backend   # 停止后端
./crmctl.sh restart all    # 重启所有服务
```

### 查看服务日志

```bash
# 使用 journalctl
sudo journalctl -u crm-backend -f
sudo journalctl -u crm-frontend -f

# 或使用项目脚本
./crmctl.sh logs backend
./crmctl.sh logs frontend
```

### 开机自启

```bash
# 启用开机自启
sudo systemctl enable crm-backend
sudo systemctl enable crm-frontend

# 禁用开机自启
sudo systemctl disable crm-backend
sudo systemctl disable crm-frontend

# 或使用项目脚本
./crmctl.sh enable
./crmctl.sh disable
```

---

## 网络架构

### 本地开发环境

```
┌─────────────────────────────────────────┐
│         客户端浏览器                      │
│                                         │
│  http://localhost:8081 (前端)           │
│  http://localhost:8000 (后端API)         │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│      前端服务 (0.0.0.0:8081)             │
│                                         │
│  React Dev Server + Proxy              │
│  /api -> http://localhost:8000         │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│      后端服务 (0.0.0.0:8000)             │
│                                         │
│  FastAPI + Uvicorn                      │
│  - PostgreSQL (5433)                    │
│  - Redis (6380)                         │
└─────────────────────────────────────────┘
```

### 生产环境

```
┌─────────────────────────────────────────┐
│         外部客户端                        │
│                                         │
│  http://server-ip:8081 (前端)           │
│  http://server-ip:8000 (后端API)        │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│    前端服务 (监听 0.0.0.0:8081)          │
│                                         │
│  可从任意网络接口访问                    │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│    后端服务 (监听 0.0.0.0:8000)          │
│                                         │
│  可从任意网络接口访问                    │
└─────────────────────────────────────────┘
```

---

## 端口分配

| 服务 | 端口 | 监听地址 | 用途 |
|------|------|----------|------|
| 后端 API | 8000 | 0.0.0.0 | FastAPI 后端服务 |
| 前端开发服务器 | 8081 | 0.0.0.0 | React 开发服务器 |
| PostgreSQL | 5433 | 0.0.0.0 | 数据库（容器） |
| Redis | 6380 | 0.0.0.0 | 缓存服务（容器） |

---

## 故障排查

### 错误：ERR_CONNECTION_REFUSED（浏览器控制台）

**现象**：
```
GET http://localhost:8000/operation-logs/?limit=200 
net::ERR_CONNECTION_REFUSED
```

**可能原因及解决方案**：

#### 1. 浏览器显示的是代理转发后的URL

**说明**：
- 前端使用 `/api` 作为 baseURL（正确配置）
- React开发服务器将 `/api/*` 代理到 `http://localhost:8000/*`
- 浏览器控制台可能会显示代理后的URL（`localhost:8000`）
- 这是**正常现象**，代理在服务器端执行转发

**验证代理是否正常**：
```bash
# 从局域网测试
curl http://192.168.101.13:8081/api/health

# 应返回
{"status":"healthy","timestamp":"..."}
```

#### 2. 未登录导致的认证错误

**现象**：
```json
{"detail":"Not authenticated"}
```

**解决方案**：
1. 访问登录页面：`http://192.168.101.13:8081/login`
2. 使用账号登录系统
3. 登录后API请求会携带认证token

#### 3. 浏览器缓存旧错误

**解决方案**：
```bash
# 硬刷新浏览器
Ctrl + Shift + R (Windows)
Cmd + Shift + R (Mac)

# 或清除浏览器缓存
开发者工具 → Application → Clear storage
```

#### 4. 服务确实未启动

**检查步骤**：
```bash
# 1. 检查服务状态
sudo systemctl status crm-backend

# 2. 检查监听地址
ss -tuln | grep :8000

# 3. 重启服务
sudo systemctl restart crm-backend
```

### 错误：前端无法从外部访问

**原因**：前端服务未监听 `0.0.0.0`

**解决方案**：
```bash
# 1. 检查环境变量
cat /home/pytc/crm_system/frontend/.env

# 2. 确认包含
# HOST=0.0.0.0
# PORT=8081

# 3. 重启前端服务
sudo systemctl restart crm-frontend
```

### 检查服务监听地址

```bash
# 方法1：使用 ss 命令
ss -tuln | grep -E ":(8000|8081)"

# 方法2：使用 netstat（如果可用）
netstat -tuln | grep -E ":(8000|8081)"

# 方法3：检查进程
ps aux | grep -E "(uvicorn|node.*react-scripts)"
```

**正确输出示例**：
```
tcp   LISTEN 0      2048   0.0.0.0:8000   0.0.0.0:*
tcp   LISTEN 0      511    0.0.0.0:8081   0.0.0.0:*
```

**错误输出示例**：
```
tcp   LISTEN 0      2048   127.0.0.1:8000   0.0.0.0:*  ❌ 仅本地访问
```

---

## 依赖服务状态

### 检查容器服务

```bash
# 查看运行中的容器
docker ps

# 应包含以下容器
# crm_system-redis-1  (端口 6380)
# crm_system-db-1     (端口 5433)
```

### 测试数据库连接

```bash
# 测试 PostgreSQL
psql -h localhost -p 5433 -U postgres -d crm_db

# 测试 Redis
redis-cli -p 6380 ping
```

---

## 配置文件清单

| 文件路径 | 用途 | 必须包含的配置 |
|---------|------|--------------|
| `/etc/systemd/system/crm-backend.service` | 后端Systemd服务 | `--host 0.0.0.0` |
| `/etc/systemd/system/crm-frontend.service` | 前端Systemd服务 | `Environment="HOST=0.0.0.0"` |
| `/home/pytc/crm_system/frontend/.env` | 前端环境变量 | `HOST=0.0.0.0` |
| `/home/pytc/crm_system/frontend/src/setupProxy.js` | 开发代理配置 | `target: 'http://localhost:8000'` |

---

## 更新历史

- 2026-05-04: 初始创建，记录服务监听配置规范