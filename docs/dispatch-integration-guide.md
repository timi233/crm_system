# 派工系统集成实施指南

## 概述

本文档提供了CRM系统与IT派工系统集成的详细实施指南，包括配置、使用和故障排除。

## 前置条件

### 系统要求
- CRM系统运行正常（端口8000后端，端口3002前端）
- 派工系统可访问（需要API地址和认证Token）
- 用户具有派工系统访问权限

### 权限要求
- CRM系统：销售、商务或管理员角色
- 派工系统：SALES或TECHNICIAN角色

## 快速开始

### 1. 启动CRM系统

```bash
# 启动后端
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 启动前端
cd frontend
npm start
```

### 2. 配置派工系统连接

派工系统连接信息在创建派工申请时提供：
- **API地址**: 派工系统的API端点（例如：http://localhost:3000）
- **认证Token**: 从派工系统获取的JWT Token

### 3. 创建派工申请

#### 从线索创建
1. 登录CRM系统
2. 进入"线索管理"
3. 点击线索编号进入详情页
4. 点击"派工申请"按钮
5. 填写派工系统API地址和Token
6. 点击"创建派工"

#### 从商机创建
1. 登录CRM系统
2. 进入"商机管理"
3. 点击商机编号进入详情页
4. 点击"派工申请"按钮
5. 填写派工系统API地址和Token
6. 点击"创建派工"

#### 从项目创建
1. 登录CRM系统
2. 进入"项目管理"
3. 点击项目编号进入详情页
4. 点击"派工申请"按钮
5. 填写派工系统API地址和Token
6. 点击"创建派工"

## 技术实现

### 后端实现

#### 服务层
文件位置：`backend/app/services/dispatch_integration_service.py`

主要功能：
- 数据转换：CRM实体 → 派工工单格式
- API调用：与派工系统通信
- 错误处理：网络错误、认证错误等

#### API端点
文件位置：`backend/app/main.py`

新增端点：
- `POST /leads/{id}/create-dispatch`
- `POST /opportunities/{id}/create-dispatch`
- `POST /projects/{id}/create-dispatch`

### 前端实现

#### 组件结构
```
frontend/src/
├── components/
│   └── common/
│       └── DispatchModal.tsx       # 派工申请对话框
├── hooks/
│   └── useDispatch.ts              # 派工相关hooks
├── services/
│   └── dispatchService.ts          # 派工API服务
└── types/
    └── dispatch.ts                 # 类型定义
```

#### 页面集成
- `LeadFullViewPage.tsx` - 线索详情页添加派工按钮
- `OpportunityFullViewPage.tsx` - 商机详情页添加派工按钮
- `ProjectFullViewPage.tsx` - 项目详情页添加派工按钮

## 数据映射规则

### 工单类型判断
```python
if source == 'opportunity':
    order_type = 'CF' if has_channel else 'CO'
elif source == 'project':
    order_type = 'CF'
elif source == 'lead':
    order_type = 'CO'
```

### 优先级判断
```python
priority = 'URGENT' if expected_contract_amount > 500000 else 'NORMAL'
```

### 字段映射表

| CRM字段 | 派工字段 | 说明 |
|---------|---------|------|
| terminal_customer.customer_name | customerName | 客户名称 |
| main_contact | customerContact | 联系人 |
| phone | customerPhone | 联系电话 |
| channel.company_name | channelName | 渠道名称 |
| opportunity_name/project_name | description | 工单描述 |

## 测试

### 使用模拟服务器测试

1. 启动模拟派工服务器：
```bash
python3 mock_dispatch_server.py
```

2. 测试创建派工：
```bash
# 获取Token
TOKEN=$(curl -s -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin123" | jq -r '.access_token')

# 创建派工
curl -X POST "http://localhost:8000/leads/1/create-dispatch" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dispatch_api_url": "http://localhost:3005",
    "dispatch_token": "mock-token"
  }'
```

### 预期输出
```json
{
  "success": true,
  "message": "Dispatch work order created successfully",
  "work_order_id": "workorder_123",
  "work_order_no": "MOCK-123"
}
```

## 故障排除

### 常见问题

#### 1. "Lead not found" / "Opportunity not found" / "Project not found"
**原因**: 指定的CRM记录不存在
**解决**: 确认记录ID正确，检查数据库中是否存在该记录

#### 2. "Not authenticated"
**原因**: 未提供认证Token或Token无效
**解决**: 确保已登录CRM系统，Token格式正确

#### 3. "Dispatch API error: 401"
**原因**: 派工系统Token无效或过期
**解决**: 重新获取派工系统Token

#### 4. "Dispatch API timeout"
**原因**: 派工系统无响应
**解决**: 
- 检查派工系统是否运行
- 确认API地址正确
- 检查网络连接

#### 5. "Missing required fields"
**原因**: 派工数据缺少必填字段
**解决**: 
- 检查CRM数据完整性
- 确保客户信息完整
- 查看后端日志获取详细错误信息

### 日志查看

#### 后端日志
```bash
# 查看最近的错误
tail -100 backend/uvicorn.log

# 搜索特定错误
grep "DispatchIntegrationError" backend/uvicorn.log
```

#### 前端控制台
打开浏览器开发者工具 → Console 标签页，查看错误信息。

## 安全考虑

### 1. Token安全
- 不要在前端代码中硬编码Token
- Token应通过安全渠道获取
- 定期刷新Token

### 2. API安全
- 使用HTTPS进行通信
- 验证API响应来源
- 实施请求频率限制

### 3. 数据安全
- 不记录敏感信息到日志
- 客户联系方式部分脱敏
- 实施审计日志

## 性能优化

### 1. 并发控制
- 限制派工申请频率
- 实施请求队列
- 批量操作优化

### 2. 缓存策略
- 缓存派工系统Token
- 缓存工单类型配置
- 实施响应缓存

### 3. 异步处理
- 后台创建派工
- 状态更新通知
- 批量同步优化

## 未来扩展

### 计划功能
1. **Webhook回调**: 接收派工系统状态更新
2. **状态同步**: 在CRM中显示工单状态
3. **批量派工**: 一次创建多个工单
4. **派工历史**: 查看派工记录和工单详情
5. **智能推荐**: 根据业务规则推荐技术员

### API扩展
- `GET /dispatch-history` - 查询派工历史
- `GET /dispatch-orders/{id}` - 查询工单详情
- `POST /dispatch-batch` - 批量创建工单
- `POST /webhooks/dispatch` - 接收派工系统回调

## 参考资料

- [CRM系统架构设计文档](./architecture-design.md)
- [派工系统集成规范](../integration-spec.md)
- [API文档](http://localhost:8000/docs)
- [派工系统API文档](http://localhost:3000/api/docs)

---

**文档版本**: 1.0  
**最后更新**: 2026-04-10  
**维护者**: Sisyphus