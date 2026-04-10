# CRM系统技术问题排查手册

## 问题分类与诊断流程

### 1. 启动问题

#### 1.1 端口占用
**症状**: `Address already in use`  
**诊断**:
```bash
# 检查端口占用
lsof -i :8000
lsof -i :3002

# 终止占用进程
pkill -f "uvicorn"
pkill -f "react-scripts"
```

#### 1.2 数据库连接失败
**症状**: `Connection refused` 或认证失败  
**诊断**:
```bash
# 检查PostgreSQL服务状态
sudo systemctl status postgresql

# 测试数据库连接
sudo -u postgres psql -d crm_db

# 验证用户权限
sudo -u postgres psql -c "\du crm_admin"
```

### 2. API错误 (500 Internal Server Error)

#### 2.1 SQLAlchemy模型导入顺序错误
**症状**: 
```
When initializing mapper Mapper[User(users)], expression 'SalesTarget' failed to locate a name ('SalesTarget')
```

**根本原因**: `User` 模型引用了 `SalesTarget`，但 `SalesTarget` 模型未在 `models/__init__.py` 中导入

**解决方案**:
1. 编辑 `backend/app/models/__init__.py`
2. 确保所有被引用的模型都在文件顶部正确导入
3. 按依赖关系排序导入（被引用的模型必须先导入）

**验证命令**:
```bash
# 测试模型导入
cd backend && source venv/bin/activate && python -c "from app.models import User, SalesTarget; print('Models imported successfully')"
```

#### 2.2 Pydantic序列化配置错误
**症状**: ORM对象无法正确序列化为JSON响应

**根本原因**: 
- 使用了过时的 `class Config: from_attributes = True`
- 手动拼接字典而非直接返回ORM对象

**解决方案**:
1. 更新Pydantic模型配置：
   ```python
   # 错误方式
   class Config:
       from_attributes = True
   
   # 正确方式 (Pydantic v2)
   from pydantic import ConfigDict
   
   model_config = ConfigDict(from_attributes=True)
   ```
2. 修改API实现，直接返回ORM对象：
   ```python
   # 错误方式
   return [{**obj.__dict__, ...} for obj in results]
   
   # 正确方式
   return results  # FastAPI自动处理Pydantic序列化
   ```

#### 2.3 数据库表缺失
**症状**: 外键约束失败或表不存在错误

**常见缺失表**:
- `sales_targets` - 销售目标表
- `alerts` - 警报表  
- `user_notification_reads` - 用户通知读取记录表

**完整建表脚本**:
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

### 3. 前端连接问题

#### 3.1 CORS错误
**症状**: 浏览器显示 `No 'Access-Control-Allow-Origin' header is present`

**关键洞察**: 这通常是**误导性错误**！真正的错误是后端500错误，因为CORS中间件在500错误发生前未执行。

**诊断步骤**:
1. 直接curl测试带Origin头的请求：
   ```bash
   curl -H "Origin: http://localhost:3002" -I http://localhost:8000/health
   ```
2. 如果返回正确的CORS头，则问题是后端500错误
3. 检查后端日志中的真实错误信息

#### 3.2 API代理配置错误
**症状**: 前端无法连接到后端API

**解决方案**:
1. 确保前端 `.env.local` 配置正确：
   ```ini
   REACT_APP_API_URL=http://localhost:8000
   ```
2. 确保后端CORS配置包含前端端口：
   ```ini
   ALLOWED_ORIGINS=http://localhost:3002,http://127.0.0.1:3002
   ```

### 4. 性能报告API特殊问题

#### 4.1 复杂查询失败
**症状**: `/reports/performance` 返回500错误

**根本原因**: 性能报告涉及多表连接和复杂计算，容易在数据不完整时出错

**临时修复方案**:
```python
@app.get("/reports/performance", response_model=PerformanceReportResponse)
async def get_performance_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    sales_owner_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        # 原始复杂逻辑...
        pass
    except Exception as e:
        # 记录错误但返回空数据而不是500
        print(f"Performance report error: {e}")
        return PerformanceReportResponse(
            by_user=[],
            by_month=[],
            total_contract_amount=0.0,
            total_received_amount=0.0,
            total_pending_amount=0.0,
        )
```

### 5. 飞书OAuth问题

#### 5.1 重定向URI不匹配
**症状**: `重定向 URL 有误，请联系应用管理员`

**解决方案**:
1. 登录飞书开放平台
2. 在应用设置中添加正确的重定向URI：
   - `http://localhost:3002/auth/feishu/callback`
3. 确保backend `.env` 文件中的 `FEISHU_REDIRECT_URI` 匹配

#### 5.2 身份映射问题
**症状**: 飞书用户登录后无法访问CRM功能

**解决方案**:
- 系统使用飞书 `open_id` 作为用户身份锚点
- 首次使用飞书登录时会自动创建CRM用户账户
- 确保数据库 `users` 表有 `feishu_id` 字段

## 调试工具和命令

### 1. 数据库调试
```bash
# 查看所有表
sudo -u postgres psql -d crm_db -c "\dt"

# 查看表结构
sudo -u postgres psql -d crm_db -c "\d table_name"

# 查询数据
sudo -u postgres psql -d crm_db -c "SELECT * FROM users;"

# 检查外键约束
sudo -u postgres psql -d crm_db -c "\d+ table_name"
```

### 2. API调试
```bash
# 测试认证
curl -X POST http://localhost:8000/auth/login -d "username=admin@example.com&password=admin123"

# 测试带认证的API
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login -d "username=admin@example.com&password=admin123" | jq -r '.access_token')
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/leads

# 测试CORS头
curl -H "Origin: http://localhost:3002" -I http://localhost:8000/health
```

### 3. 前端调试
```bash
# 清除node_modules并重装
rm -rf node_modules package-lock.json
npm install

# 清除浏览器缓存
# 开发者工具 -> Application -> Clear storage
```

### 4. 日志查看
```bash
# 后端日志 (如果有配置)
journalctl -u uvicorn -f

# 前端控制台日志
# F12 -> Console

# 网络请求日志  
# F12 -> Network
```

## 自动化测试脚本

### 系统健康检查脚本
```bash
#!/bin/bash
# health_check.sh

echo "=== CRM System Health Check ==="

# 1. 检查后端
echo "1. Testing backend..."
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "✅ Backend OK"
else
    echo "❌ Backend ERROR"
    exit 1
fi

# 2. 获取认证token
echo "2. Testing authentication..."
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login -d "username=admin@example.com&password=admin123" | jq -r '.access_token')
if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
    echo "✅ Authentication OK"
else
    echo "❌ Authentication ERROR"
    exit 1
fi

# 3. 测试核心API
echo "3. Testing core APIs..."
APIS=("/users" "/leads" "/opportunities" "/dashboard/summary" "/alert-rules")

for api in "${APIS[@]}"; do
    if curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000$api | jq '.' > /dev/null 2>&1; then
        echo "✅ $api OK"
    else
        echo "❌ $api ERROR"
        exit 1
    fi
done

echo "=== All tests passed! System is healthy ==="
```

### 快速修复脚本
```bash
#!/bin/bash
# quick_fix.sh

echo "=== Applying Quick Fixes ==="

# 1. 重启服务
echo "1. Restarting services..."
pkill -f "uvicorn"
pkill -f "react-scripts"

# 2. 重置数据库（可选）
echo "2. Resetting database..."
cd backend && source venv/bin/activate && python reset_db.py

# 3. 重新启动
echo "3. Starting services..."
cd backend && source venv/bin/activate & uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
cd frontend && PORT=3002 npm start &

echo "=== Services restarted ==="
```

## 常见问题快速参考表

| 问题现象 | 可能原因 | 解决方案 | 优先级 |
|----------|----------|----------|--------|
| 启动失败，端口占用 | 其他进程占用端口 | `pkill -f "uvicorn"` | 高 |
| 数据库连接失败 | PostgreSQL未启动或用户不存在 | 启动PostgreSQL，创建用户和数据库 | 高 |
| 500错误，SQLAlchemy导入错误 | models/init.py导入顺序错误 | 按依赖关系重新排序导入 | 高 |
| CORS错误 | 实际是后端500错误 | 先解决后端错误 | 中 |
| 飞书OAuth重定向错误 | 飞书后台配置不匹配 | 更新飞书应用重定向URI | 中 |
| 性能报告500错误 | 复杂查询逻辑错误 | 使用简化版本返回空数据 | 低 |

## 版本兼容性说明

### Python依赖
- **FastAPI**: >=0.104.1
- **SQLAlchemy**: >=2.0.0  
- **Pydantic**: >=2.0.0 (v2 API)

### Node.js依赖
- **React**: 18.x
- **Ant Design**: 5.x

### 数据库版本
- **PostgreSQL**: >=12.0
- **Redis**: >=6.0 (可选)

---

**文档维护**: 定期更新此文档以反映系统变更  
**问题上报**: 发现新问题时，及时补充到此文档  
**团队共享**: 确保所有开发人员都能访问此文档