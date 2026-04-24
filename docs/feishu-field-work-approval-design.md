# 飞书外勤审批联动方案设计

> 创建时间: 2026-04-24
> 状态: 设计阶段

## 一、背景与需求

### 业务需求
1. CRM派工创建后，需要工程师确认接单
2. 确认接单后，自动创建外勤审批实例
3. 外勤审批需要同步到飞书考勤系统
4. **审批归属模型**：每名工程师各自独立创建一个审批实例（一人一审批）

### 技术约束
- 飞书内置控件组（tripGroup/outGroup）不支持API直接创建审批实例
- 出差/外出审批需同步考勤，必须使用飞书内置控件
- 需要通过WebSocket长连接接收卡片交互回调

---

## 二、方案选择

### 方案对比

| 方案 | 审批发起 | 关联方式 | 同步考勤 | 推荐度 |
|------|---------|---------|---------|-------|
| A: 长连接卡片交互 | 工程师点击确认后自动创建 | 直接关联 | ✅ 支持 | ⭐⭐⭐⭐ |
| B: 三方审批接入 | 手动在飞书发起 | 表单字段关联 | ✅ 支持 | ⭐⭐⭐ |
| C: 自定义审批 | 自动创建 | 直接关联 | ❌ 不支持 | ⭐ |

### 最终选择：方案A（WebSocket长连接 + 卡片交互）

---

## 三、核心流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CRM系统                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐           │
│  │ FastAPI 主服务│    │ WebSocket    │    │ 消息卡片     │           │
│  │ (HTTP API)   │    │ 长连接服务    │    │ 发送服务     │           │
│  └──────────────┘    └──────────────┘    └──────────────┘           │
│         │                   │                   │                   │
│         │                   │                   │                   │
│         │ 创建派工           │ 监听事件          │ 发送卡片消息       │
│         └───────────────────┼───────────────────┘                   │
│                             │                                        │
│                             │ 接收卡片交互回调                        │
│                             │ (im.message.card_action_trigger)       │
│                             │                                        │
│                             ↓                                        │
│                     ┌──────────────┐                                │
│                     │ 处理回调      │                                │
│                     │ 1. 更新状态   │                                │
│                     │ 2. 创建审批   │                                │
│                     └──────────────┘                                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                              ↑↓ WebSocket 长连接
┌─────────────────────────────────────────────────────────────────────┐
│                         飞书开放平台                                  │
└─────────────────────────────────────────────────────────────────────┘
                              ↑↓
┌─────────────────────────────────────────────────────────────────────┐
│                      飞书客户端（工程师）                              │
│                                                                      │
│  收到卡片消息 → 点击"确认接单" → 触发事件 → WebSocket 推送回调        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 四、审批配置

### 4.1 外勤审批定义

| 属性 | 值 |
|------|---|
| **审批名称** | 外勤申请 |
| **Approval Code** | `1E9D3E8F-15CF-45C9-BC93-2483DDBF9A9A` |
| **状态** | ACTIVE（已启用） |
| **是否可API创建** | ✅ 可以（使用普通控件） |

### 4.2 表单字段映射

| 字段名 | Widget ID | 控件类型 | 是否必填 | 数据来源 |
|-------|-----------|---------|---------|---------|
| 工单编号 | `widget17646459880240001` | input | ✅ 必填 | `work_order.work_order_no` |
| 关联销售 | `widget17675834510510001` | contact | 可选 | `work_order.related_sales.feishu_id` |
| 客户名称 | `widget17646459981630001` | input | ✅ 必填 | `work_order.customer_name` |
| 服务内容 | `widget17646460011860001` | input | ✅ 必填 | `work_order.description` |
| 外勤类型 | `widget17657823368860001` | input | ✅ 必填 | 固定值："派工服务" |
| 预计时间 | `widget17646460191710001` | dateInterval | ✅ 必填 | `work_order.estimated_start_date/end_date` |
| 客户联系人 | `widget17646460247810001` | input | ✅ 必填 | `work_order.customer_contact` |
| 联系电话 | `widget17646460277440001` | input | ✅ 必填 | `work_order.customer_phone` |

---

## 五、技术实现

### 5.1 新增组件清单

| 组件 | 文件路径 | 功能 |
|------|----------|------|
| WebSocket 长连接服务 | `backend/app/services/feishu_ws_service.py` | 建立长连接，监听卡片交互事件 |
| 卡片消息服务 | `backend/app/services/feishu_card_service.py` | 发送/更新卡片消息 |
| 审批创建服务 | `backend/app/services/feishu_approval_service.py` | 创建外勤审批实例 |
| 卡片交互处理器 | `backend/app/handlers/card_action_handler.py` | 处理卡片回调事件 |
| 派工通知任务 | `backend/app/tasks/dispatch_notification_task.py` | 异步发送派工通知 |

### 5.2 配置项

```ini
# backend/.env 新增配置

# 飞书外勤审批配置
FEISHU_FIELD_WORK_APPROVAL_CODE=1E9D3E8F-15CF-45C9-BC93-2483DDBF9A9A

# 飞书消息卡片模板ID（可选，如使用模板）
FEISHU_CARD_TEMPLATE_DISPATCH=AAAqkV2hten9
```

---

## 六、详细设计

### 6.1 派工创建流程

```python
# 派工创建时触发
async def create_work_order_with_notification(work_order_data, technician_ids, submitter_id):
    # 1. 创建派工记录
    work_order = await create_work_order(work_order_data)
    
    # 2. 创建技术员分配记录
    for tech_id in technician_ids:
        await create_work_order_technician(work_order.id, tech_id)
    
    # 3. 异步发送飞书通知给每个工程师
    for tech_id in technician_ids:
        technician = await get_user(tech_id)
        await send_dispatch_notification_card(
            technician=technician,
            work_order=work_order,
            action_callback=True  # 启用交互按钮
        )
    
    return work_order
```

### 6.2 卡片消息设计

```json
{
  "config": {
    "wide_screen_mode": true
  },
  "header": {
    "title": { "tag": "plain_text", "content": "🆕 新派工通知" },
    "template": "blue"
  },
  "elements": [
    {
      "tag": "div",
      "text": {
        "tag": "lark_md",
        "content": "**派工单号:** {{work_order_no}}\n**客户名称:** {{customer_name}}\n**服务地址:** {{service_address}}\n**预计时间:** {{estimated_time}}\n**工作类型:** {{work_type}}\n**紧急程度:** {{priority}}"
      }
    },
    {
      "tag": "hr"
    },
    {
      "tag": "div",
      "text": {
        "tag": "lark_md",
        "content": "**工作描述:**\n{{description}}"
      }
    },
    {
      "tag": "hr"
    },
    {
      "tag": "action",
      "actions": [
        {
          "tag": "button",
          "text": { "tag": "plain_text", "content": "✅ 确认接单" },
          "type": "primary",
          "value": {
            "work_order_id": "{{work_order_id}}",
            "technician_id": "{{technician_id}}",
            "action_type": "confirm"
          }
        },
        {
          "tag": "button",
          "text": { "tag": "plain_text", "content": "❌ 拒绝接单" },
          "type": "danger",
          "value": {
            "work_order_id": "{{work_order_id}}",
            "technician_id": "{{technician_id}}",
            "action_type": "reject"
          }
        },
        {
          "tag": "button",
          "text": { "tag": "plain_text", "content": "📋 查看详情" },
          "type": "default",
          "url": "{{crm_detail_url}}"
        }
      ]
    },
    {
      "tag": "note",
      "elements": [
        {
          "tag": "plain_text",
          "content": "点击确认接单后将自动创建外勤审批"
        }
      ]
    }
  ]
}
```

### 6.3 WebSocket 长连接服务

```python
# backend/app/services/feishu_ws_service.py

import lark_oapi as lark
from lark_oapi.api.im.v1 import P2MessageCardActionTriggerV1
import asyncio
import logging

from app.core.config import get_settings
from app.handlers.card_action_handler import process_card_action

settings = get_settings()
logger = logging.getLogger(__name__)


class FeishuWebSocketService:
    """飞书 WebSocket 长连接服务"""
    
    def __init__(self):
        self.event_handler = lark.EventDispatcherHandler.builder("", "") \
            .register_p2_im_message_card_action_trigger_v1(self._handle_card_action) \
            .build()
        
        self.client = lark.ws.Client(
            settings.feishu_app_id,
            settings.feishu_app_secret,
            event_handler=self.event_handler,
            log_level=lark.LogLevel.INFO
        )
        
        self._running = False
    
    def _handle_card_action(self, event: P2MessageCardActionTriggerV1) -> None:
        """处理卡片交互事件"""
        try:
            logger.info(f"收到卡片交互事件: {lark.JSON.marshal(event.event, indent=4)}")
            
            # 提取交互数据
            action_value = event.event.action.value
            open_id = event.event.open_id  # 操作用户的 open_id
            message_id = event.event.message_id  # 消息ID，用于更新卡片
            
            work_order_id = action_value.get("work_order_id")
            technician_id = action_value.get("technician_id")
            action_type = action_value.get("action_type")  # "confirm" / "reject"
            
            # 异步处理（避免阻塞WebSocket）
            asyncio.create_task(
                process_card_action(
                    work_order_id=work_order_id,
                    technician_id=technician_id,
                    action_type=action_type,
                    operator_open_id=open_id,
                    message_id=message_id
                )
            )
            
        except Exception as e:
            logger.error(f"处理卡片交互失败: {e}")
    
    def start(self):
        """启动长连接"""
        logger.info("启动飞书 WebSocket 长连接服务...")
        self._running = True
        self.client.start()
    
    def stop(self):
        """停止长连接"""
        self._running = False
        # lark SDK 的 ws.Client 没有 stop 方法，需要关闭进程


# 全局实例
ws_service = FeishuWebSocketService()


def run_ws_service():
    """运行 WebSocket 服务（用于独立进程）"""
    ws_service.start()


async def start_ws_in_background():
    """在后台线程启动 WebSocket 服务"""
    import threading
    thread = threading.Thread(target=run_ws_service, daemon=True)
    thread.start()
    logger.info("WebSocket 服务已在后台线程启动")
```

### 6.4 卡片交互处理器

```python
# backend/app/handlers/card_action_handler.py
# 【示意代码】实际实现需补齐 import 和完善异常处理

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime

from app.core.database import get_db_context
from app.models.work_order import WorkOrder, WorkOrderTechnician, WorkOrderStatus
from app.models.user import User
from app.services.feishu_approval_service import feishu_approval_service
from app.services.feishu_card_service import feishu_card_service

logger = logging.getLogger(__name__)


async def process_card_action(
    work_order_id: str,
    technician_id: str,
    action_type: str,
    operator_open_id: str,
    message_id: str
):
    """处理卡片交互回调（含身份校验、幂等控制）"""
    
    async with get_db_context() as db:
        # ========== 第一步：身份校验 ==========
        technician = await db.get(User, int(technician_id))
        if not technician:
            logger.error(f"技术员不存在: technician_id={technician_id}")
            await feishu_card_service.update_card_message(
                message_id=message_id,
                card_content=_generate_error_card("系统错误：技术员不存在")
            )
            return
        
        # 校验操作者身份是否匹配目标技术员
        if technician.feishu_id != operator_open_id:
            logger.warning(
                f"身份校验失败: operator={operator_open_id}, expected={technician.feishu_id}"
            )
            await feishu_card_service.update_card_message(
                message_id=message_id,
                card_content=_generate_error_card("身份验证失败，只能由本人操作")
            )
            return
        
        # 校验该用户是否为被派工技术员
        stmt = select(WorkOrderTechnician).where(
            WorkOrderTechnician.work_order_id == int(work_order_id),
            WorkOrderTechnician.technician_id == int(technician_id)
        )
        result = await db.execute(stmt)
        assignment = result.scalar_one_or_none()
        
        if not assignment:
            logger.warning(f"非被派工技术员: operator={operator_open_id}")
            await feishu_card_service.update_card_message(
                message_id=message_id,
                card_content=_generate_error_card("您不是该派工的技术员")
            )
            return
        
        # ========== 第二步：幂等校验 ==========
        if assignment.status != "PENDING":
            logger.info(f"幂等拦截: 已处理过，status={assignment.status}")
            # 返回当前状态卡片
            if assignment.status == "ACCEPTED" and assignment.approval_instance_code:
                await feishu_card_service.update_card_message(
                    message_id=message_id,
                    card_content=_generate_accepted_card_simple(
                        work_order_id=work_order_id,
                        instance_code=assignment.approval_instance_code
                    )
                )
            elif assignment.status == "REJECTED":
                await feishu_card_service.update_card_message(
                    message_id=message_id,
                    card_content=_generate_rejected_card_simple(work_order_id)
                )
            return
        
        # ========== 第三步：获取派工信息并校验必填字段 ==========
        work_order = await db.get(WorkOrder, int(work_order_id))
        if not work_order:
            logger.error(f"派工不存在: work_order_id={work_order_id}")
            await feishu_card_service.update_card_message(
                message_id=message_id,
                card_content=_generate_error_card("派工不存在")
            )
            return
        
        # 根据操作类型处理
        if action_type == "confirm":
            # 必填字段校验
            is_valid, missing_fields = await validate_required_fields(work_order)
            if not is_valid:
                logger.warning(f"必填字段缺失: {missing_fields}")
                await feishu_card_service.update_card_message(
                    message_id=message_id,
                    card_content=_generate_missing_fields_card(missing_fields)
                )
                # TODO: 发送通知给销售提醒补充字段
                return
            
            await _handle_confirm_action(
                db=db,
                work_order=work_order,
                assignment=assignment,
                technician=technician,
                message_id=message_id
            )
        
        elif action_type == "reject":
            await _handle_reject_action(
                db=db,
                assignment=assignment,
                message_id=message_id
            )


async def validate_required_fields(work_order: WorkOrder) -> tuple[bool, list[str]]:
    """校验审批必填字段"""
    missing = []
    
    if not work_order.customer_name:
        missing.append("客户名称")
    if not work_order.description:
        missing.append("服务内容")
    if not work_order.estimated_start_date:
        missing.append("预计开始时间")
    if not work_order.estimated_end_date:
        missing.append("预计结束时间")
    if not work_order.customer_contact:
        missing.append("客户联系人")
    if not work_order.customer_phone:
        missing.append("联系电话")
    
    return (len(missing) == 0, missing)


async def _handle_confirm_action(
    db: AsyncSession,
    work_order: WorkOrder,
    assignment: WorkOrderTechnician,
    technician: User,
    message_id: str
):
    """处理确认接单（含幂等审批创建）"""
    
    # 1. 更新技术员状态
    assignment.status = "ACCEPTED"
    assignment.accepted_at = datetime.utcnow()
    
    # 2. 幂等审批创建
    idempotency_key = f"{work_order.id}_{technician.id}"
    
    if assignment.approval_instance_code:
        # 已有审批实例，幂等返回
        instance_code = assignment.approval_instance_code
        logger.info(f"审批已存在: instance_code={instance_code}")
    else:
        # 创建新审批
        try:
            approval_result = await feishu_approval_service.create_field_work_approval(
                work_order=work_order,
                technician=technician
            )
            
            instance_code = approval_result.get("instance_code")
            logger.info(f"外勤审批创建成功: instance_code={instance_code}")
            
            # 记录审批信息
            assignment.approval_instance_code = instance_code
            assignment.approval_status = "PENDING"
            assignment.approval_created_at = datetime.utcnow()
            assignment.idempotency_key = idempotency_key
            
        except Exception as e:
            logger.error(f"创建外勤审批失败: {e}")
            await db.rollback()
            await feishu_card_service.update_card_message(
                message_id=message_id,
                card_content=_generate_error_card("审批创建失败，请联系管理员")
            )
            return
    
    await db.commit()
    
    # 3. 更新飞书卡片消息
    await feishu_card_service.update_card_message(
        message_id=message_id,
        card_content=_generate_accepted_card(work_order, instance_code)
    )


async def _handle_reject_action(
    db: AsyncSession,
    assignment: WorkOrderTechnician,
    message_id: str
):
    """处理拒绝接单"""
    
    assignment.status = "REJECTED"
    assignment.rejected_at = datetime.utcnow()
    
    await db.commit()
    
    await feishu_card_service.update_card_message(
        message_id=message_id,
        card_content=_generate_rejected_card()
    )


# ===== 卡片生成函数 =====

def _generate_accepted_card(work_order: WorkOrder, instance_code: str) -> dict:
    """生成已确认的卡片内容"""
    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": "✅ 已确认接单"},
            "template": "green"
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**派工单号:** {work_order.work_order_no}\n**客户名称:** {work_order.customer_name}\n**外勤审批已创建**\n**审批实例码:** {instance_code}"
                }
            },
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "📋 查看审批详情"},
                        "type": "primary",
                        "url": f"https://www.feishu.cn/approval/approval/instance?instance_code={instance_code}"
                    }
                ]
            }
        ]
    }


def _generate_accepted_card_simple(work_order_id: str, instance_code: str) -> dict:
    """生成已确认卡片（幂等返回时使用）"""
    return {
        "config": {"wide_screen_mode": True},
        "header": {"title": {"tag": "plain_text", "content": "✅ 已确认接单"}, "template": "green"},
        "elements": [
            {"tag": "div", "text": {"tag": "lark_md", "content": f"审批实例码: {instance_code}"}}
        ]
    }


def _generate_rejected_card() -> dict:
    """生成已拒绝的卡片内容"""
    return {
        "config": {"wide_screen_mode": True},
        "header": {"title": {"tag": "plain_text", "content": "❌ 已拒绝接单"}, "template": "red"},
        "elements": [
            {"tag": "div", "text": {"tag": "lark_md", "content": "您已拒绝此派工"}}
        ]
    }


def _generate_rejected_card_simple(work_order_id: str) -> dict:
    """生成已拒绝卡片（幂等返回时使用）"""
    return _generate_rejected_card()


def _generate_error_card(error_msg: str) -> dict:
    """生成错误卡片"""
    return {
        "config": {"wide_screen_mode": True},
        "header": {"title": {"tag": "plain_text", "content": "⚠️ 操作失败"}, "template": "orange"},
        "elements": [{"tag": "div", "text": {"tag": "lark_md", "content": error_msg}}]
    }


def _generate_missing_fields_card(missing_fields: list[str]) -> dict:
    """生成缺失字段提示卡片"""
    fields_str = "、".join(missing_fields)
    return {
        "config": {"wide_screen_mode": True},
        "header": {"title": {"tag": "plain_text", "content": "⚠️ 无法创建审批"}, "template": "orange"},
        "elements": [
            {"tag": "div", "text": {"tag": "lark_md", "content": f"缺少必填字段：{fields_str}\n请联系销售补充后再确认接单"}}
        ]
    }
```

### 6.5 审批创建服务

```python
# backend/app/services/feishu_approval_service.py
# 【示意代码】实际实现需补齐 import（datetime, time, json, httpx）

import json
import logging
import httpx
import time

from app.core.config import get_settings
from app.models.work_order import WorkOrder
from app.models.user import User

settings = get_settings()
logger = logging.getLogger(__name__)


class FeishuApprovalService:
    """飞书审批服务"""
    
    BASE_URL = "https://open.feishu.cn/open-apis"
    
    def __init__(self):
        self._tenant_access_token = None
        self._token_expire_time = 0
    
    async def get_tenant_access_token(self) -> str:
        """获取 tenant_access_token"""
        if self._tenant_access_token and self._is_token_valid():
            return self._tenant_access_token
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/auth/v3/tenant_access_token/internal",
                json={
                    "app_id": settings.feishu_app_id,
                    "app_secret": settings.feishu_app_secret,
                }
            )
            data = response.json()
            
            if data.get("code") != 0:
                raise Exception(f"获取飞书Token失败: {data.get('msg')}")
            
            self._tenant_access_token = data["tenant_access_token"]
            self._token_expire_time = time.time() + int(data.get("expire", 7200))
            
            return self._tenant_access_token
    
    def _is_token_valid(self) -> bool:
        return time.time() < self._token_expire_time - 60
    
    async def create_field_work_approval(
        self,
        work_order: WorkOrder,
        technician: User,
        uuid: str = None  # 幂等键，格式: "{work_order_id}_{technician_id}"
    ) -> dict:
        """创建外勤审批实例（含幂等控制）"""
        
        token = await self.get_tenant_access_token()
        
        # 构建表单数据
        form_data = [
            # 工单编号
            {
                "id": "widget17646459880240001",
                "type": "input",
                "value": work_order.work_order_no
            },
            # 关联销售（可选）
            {
                "id": "widget17675834510510001",
                "type": "contact",
                "value": []  # 如有销售飞书ID，填入 [sales.feishu_id]
            },
            # 客户名称
            {
                "id": "widget17646459981630001",
                "type": "input",
                "value": work_order.customer_name or ""
            },
            # 服务内容
            {
                "id": "widget17646460011860001",
                "type": "input",
                "value": work_order.description or ""
            },
            # 外勤类型
            {
                "id": "widget17657823368860001",
                "type": "input",
                "value": "派工服务"
            },
            # 预计时间（dateInterval格式）
            {
                "id": "widget17646460191710001",
                "type": "dateInterval",
                "value": {
                    "start": work_order.estimated_start_date.isoformat() if work_order.estimated_start_date else "",
                    "end": work_order.estimated_end_date.isoformat() if work_order.estimated_end_date else "",
                    "interval": ""  # 自动计算
                }
            },
            # 客户联系人
            {
                "id": "widget17646460247810001",
                "type": "input",
                "value": work_order.customer_contact or ""
            },
            # 联系电话
            {
                "id": "widget17646460277440001",
                "type": "input",
                "value": work_order.customer_phone or ""
            },
        ]
        
        # 构建请求体
        request_body = {
            "approval_code": settings.feishu_field_work_approval_code,
            "open_id": technician.feishu_id,  # 审批发起人
            "form": json.dumps(form_data),
        }
        
        # 幂等键（防止重复创建）
        if uuid:
            request_body["uuid"] = uuid
            logger.info(f"审批创建幂等键: uuid={uuid}")
        
        # 调用创建审批实例API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/approval/v4/instances",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json=request_body
            )
            
            result = response.json()
            
            if result.get("code") != 0:
                logger.error(f"创建审批失败: {result}")
                raise Exception(f"创建外勤审批失败: {result.get('msg')}")
            
            return result.get("data", {})
    
    async def get_approval_instance(self, instance_code: str) -> dict:
        """获取审批实例详情"""
        token = await self.get_tenant_access_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/approval/v4/instances/{instance_code}",
                headers={"Authorization": f"Bearer {token}"},
                params={"user_id_type": "open_id"}
            )
            
            result = response.json()
            
            if result.get("code") != 0:
                raise Exception(f"获取审批实例失败: {result.get('msg')}")
            
            return result.get("data", {})


# 全局实例
feishu_approval_service = FeishuApprovalService()
```

### 6.7 身份校验设计（卡片交互安全）

**问题**：回调中的 `operator_open_id` 可能与目标技术员不一致，存在越权确认风险。

**校验流程**：

```python
async def validate_operator_identity(
    db: AsyncSession,
    work_order_id: int,
    technician_id: int,
    operator_open_id: str
) -> tuple[bool, str]:
    """
    校验操作者身份
    
    Returns:
        (is_valid, error_message)
    """
    
    # 1. 获取目标技术员
    technician = await db.get(User, technician_id)
    if not technician:
        return (False, "技术员不存在")
    
    # 2. 校验飞书身份匹配
    if technician.feishu_id != operator_open_id:
        logger.warning(
            f"身份校验失败: operator_open_id={operator_open_id}, "
            f"expected={technician.feishu_id}"
        )
        return (False, "身份不匹配，只能由本人确认接单")
    
    # 3. 校验该用户确实是被派工的技术员
    stmt = select(WorkOrderTechnician).where(
        WorkOrderTechnician.work_order_id == work_order_id,
        WorkOrderTechnician.technician_id == technician_id
    )
    result = await db.execute(stmt)
    assignment = result.scalar_one_or_none()
    
    if not assignment:
        return (False, "您不是该派工的技术员")
    
    return (True, "")
```

**校验失败处理**：

| 失败类型 | 处理方式 |
|---------|---------|
| 身份不匹配 | 记录审计日志，更新卡片显示错误提示："身份验证失败，只能由本人操作" |
| 非被派工技术员 | 记录审计日志，更新卡片显示错误提示："您不是该派工的技术员" |
| 技术员不存在 | 记录错误日志，更新卡片显示："系统错误，请联系管理员" |

### 6.8 必填字段前置校验策略

**问题**：审批表单有必填字段，但派工数据可能缺失，导致审批创建失败。

**校验时机**：工程师点击"确认接单"时，先校验必填字段。

**必填字段清单**（对应审批表单）：

| 字段 | WorkOrder 字段 | 校验规则 |
|------|----------------|---------|
| 工单编号 | `work_order_no` | 自动生成，必有值 |
| 客户名称 | `customer_name` | 必须非空 |
| 服务内容 | `description` | 必须非空 |
| 预计开始时间 | `estimated_start_date` | 必须有值 |
| 预计结束时间 | `estimated_end_date` | 必须有值 |
| 客户联系人 | `customer_contact` | 必须非空 |
| 联系电话 | `customer_phone` | 必须非空 |

**校验实现**：

```python
async def validate_required_fields(work_order: WorkOrder) -> tuple[bool, list[str]]:
    """
    校验审批必填字段
    
    Returns:
        (is_valid, missing_fields)
    """
    
    missing = []
    
    if not work_order.customer_name:
        missing.append("客户名称")
    
    if not work_order.description:
        missing.append("服务内容")
    
    if not work_order.estimated_start_date:
        missing.append("预计开始时间")
    
    if not work_order.estimated_end_date:
        missing.append("预计结束时间")
    
    if not work_order.customer_contact:
        missing.append("客户联系人")
    
    if not work_order.customer_phone:
        missing.append("联系电话")
    
    return (len(missing) == 0, missing)
```

**缺失处理策略**：

| 缺失类型 | 处理方式 |
|---------|---------|
| 任何必填字段缺失 | 拦断审批创建，更新卡片提示缺失字段列表 |
| 卡片提示内容 | "审批创建失败，缺少必填字段：{字段列表}，请联系销售补充" |
| 后续动作 | 自动发送飞书消息给 `related_sales` 提醒补充字段 |

### 6.9 审批结果回写闭环设计

**问题**：审批创建后，状态变更需要同步回 CRM。

**事件订阅**：`approval.instance.status_changed`（已在飞书开放平台配置）

**回写处理器**：

```python
# backend/app/handlers/approval_status_handler.py

import logging
from sqlalchemy import select, update
from datetime import datetime

from app.core.database import get_db_context
from app.models.work_order import WorkOrderTechnician

logger = logging.getLogger(__name__)


async def handle_approval_status_changed(event_data: dict):
    """
    处理审批状态变更事件
    
    Args:
        event_data: 飞书审批事件 payload，包含:
            - instance_code: 审批实例码
            - status: 新状态（PENDING/APPROVED/REJECTED/CANCELED）
            - open_id: 审批发起人
    """
    
    instance_code = event_data.get("instance_code")
    new_status = event_data.get("status")
    operator_open_id = event_data.get("open_id")
    
    logger.info(f"审批状态变更: instance_code={instance_code}, status={new_status}")
    
    async with get_db_context() as db:
        # 1. 通过 instance_code 反查 work_order_technician
        stmt = select(WorkOrderTechnician).where(
            WorkOrderTechnician.approval_instance_code == instance_code
        )
        result = await db.execute(stmt)
        assignment = result.scalar_one_or_none()
        
        if not assignment:
            logger.warning(f"找不到对应的技术员分配记录: instance_code={instance_code}")
            return
        
        # 2. 状态映射与更新
        status_mapping = {
            "PENDING": "PENDING",
            "APPROVED": "APPROVED",
            "REJECTED": "REJECTED",
            "CANCELED": "CANCELED"
        }
        
        mapped_status = status_mapping.get(new_status, "UNKNOWN")
        
        # 3. 更新审批状态
        assignment.approval_status = mapped_status
        
        if new_status == "APPROVED":
            assignment.approved_at = datetime.utcnow()
            logger.info(
                f"审批通过: work_order_id={assignment.work_order_id}, "
                f"technician_id={assignment.technician_id}"
            )
        elif new_status == "REJECTED":
            assignment.rejected_at = datetime.utcnow()
            # 可选：自动将技术员状态改为 REJECTED
        
        await db.commit()
        
        # 4. 可选：更新飞书卡片消息
        # await update_card_for_approval_result(assignment, new_status)
```

**状态映射规则**：

| 飞书审批状态 | CRM approval_status | 业务含义 |
|-------------|-------------------|---------|
| PENDING | PENDING | 审批进行中 |
| APPROVED | APPROVED | 审批通过，可开始外勤 |
| REJECTED | REJECTED | 审批拒绝，需重新申请 |
| CANCELED | CANCELED | 审批撤回 |

**WebSocket 注册**：

```python
# 在 feishu_ws_service.py 中添加审批事件监听
from lark_oapi.api.approval.v1 import P2ApprovalInstanceStatusChangedV1

self.event_handler = lark.EventDispatcherHandler.builder("", "") \
    .register_p2_im_message_card_action_trigger_v1(self._handle_card_action) \
    .register_p2_approval_instance_status_changed_v1(self._handle_approval_status) \
    .build()

def _handle_approval_status(self, event: P2ApprovalInstanceStatusChangedV1) -> None:
    asyncio.create_task(
        handle_approval_status_changed(event.event)
    )
```

### 6.10 幂等与并发控制设计

**问题**：WebSocket 事件可能重试、用户可能重复点击、审批可能重复创建。

**控制策略**：

#### 6.10.1 卡片回调幂等

```python
async def process_card_action_with_idempotency(
    work_order_id: str,
    technician_id: str,
    action_type: str,
    operator_open_id: str,
    message_id: str
):
    """幂等的卡片回调处理"""
    
    async with get_db_context() as db:
        # 1. 查询当前技术员状态
        stmt = select(WorkOrderTechnician).where(
            WorkOrderTechnician.work_order_id == int(work_order_id),
            WorkOrderTechnician.technician_id == int(technician_id)
        )
        result = await db.execute(stmt)
        assignment = result.scalar_one_or_none()
        
        if not assignment:
            logger.warning(f"找不到分配记录")
            return
        
        # 2. 幂等校验：如果已处理，直接返回当前状态
        if assignment.status != "PENDING":
            logger.info(
                f"幂等拦截: 已处理过，当前状态={assignment.status}"
            )
            # 返回当前状态卡片，不重复执行
            if assignment.status == "ACCEPTED":
                await feishu_card_service.update_card_message(
                    message_id=message_id,
                    card_content=_generate_accepted_card(
                        work_order_id, 
                        assignment.approval_instance_code
                    )
                )
            elif assignment.status == "REJECTED":
                await feishu_card_service.update_card_message(
                    message_id=message_id,
                    card_content=_generate_rejected_card(work_order_id)
                )
            return
        
        # 3. 加锁防止并发（使用数据库行级锁）
        stmt = select(WorkOrderTechnician).where(
            WorkOrderTechnician.id == assignment.id
        ).with_for_update()
        result = await db.execute(stmt)
        locked_assignment = result.scalar_one_or_none()
        
        if locked_assignment.status != "PENDING":
            # 锁定后发现状态已变更，返回当前状态
            await db.rollback()
            return
        
        # 4. 执行业务逻辑
        # ... 后续处理
```

#### 6.10.2 审批创建幂等

**幂等键设计**：`idempotency_key = "{work_order_id}_{technician_id}"`

```python
async def create_field_work_approval_with_idempotency(
    db: AsyncSession,
    work_order: WorkOrder,
    technician: User
) -> dict:
    """幂等的审批创建"""
    
    idempotency_key = f"{work_order.id}_{technician.id}"
    
    # 1. 检查是否已创建过
    stmt = select(WorkOrderTechnician).where(
        WorkOrderTechnician.idempotency_key == idempotency_key
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing and existing.approval_instance_code:
        logger.info(f"幂等拦截: 审批已存在, instance_code={existing.approval_instance_code}")
        return {"instance_code": existing.approval_instance_code}
    
    # 2. 创建审批实例（API 调用）
    approval_result = await feishu_approval_service.create_field_work_approval(
        work_order=work_order,
        technician=technician,
        uuid=idempotency_key  # 飞书 API 层面的幂等键
    )
    
    instance_code = approval_result.get("instance_code")
    
    # 3. 记录幂等键和实例码
    assignment.idempotency_key = idempotency_key
    assignment.approval_instance_code = instance_code
    assignment.approval_status = "PENDING"
    assignment.approval_created_at = datetime.utcnow()
    
    await db.commit()
    
    return approval_result
```

#### 6.10.3 重复点击处理

| 场景 | 处理方式 |
|------|---------|
| 技术员重复点击"确认接单" | 幂等校验拦截，返回当前状态卡片 |
| 技术员重复点击"拒绝接单" | 幂等校验拦截，返回当前状态卡片 |
| 点击后卡片按钮失效 | 更新卡片时移除交互按钮，显示当前状态 |
| WebSocket 重试 | 幂等校验拦截，不重复执行 |

### 6.11 示例代码标注说明

> **重要提示**：本文档第六章节中的代码示例均为**示意代码**，用于说明设计思路，并非可直接执行的完整实现代码。
> 
> 在实际开发时需要：
> 1. 补齐缺失的 `import` 语句（如 `datetime`, `time`, `json` 等）
> 2. 根据项目实际结构调整模块引用路径
> 3. 完善异常处理和日志记录
> 4. 添加类型注解和文档字符串

```python
# backend/app/services/feishu_card_service.py

import json
import logging
import httpx

from app.core.config import get_settings
from app.models.work_order import WorkOrder
from app.models.user import User

settings = get_settings()
logger = logging.getLogger(__name__)


class FeishuCardService:
    """飞书卡片消息服务"""
    
    BASE_URL = "https://open.feishu.cn/open-apis"
    
    def __init__(self):
        self._tenant_access_token = None
        self._token_expire_time = 0
    
    async def get_tenant_access_token(self) -> str:
        """获取 tenant_access_token（复用）"""
        # 同 approval_service，可提取为公共方法
        ...
    
    async def send_dispatch_notification_card(
        self,
        technician: User,
        work_order: WorkOrder
    ) -> str:
        """发送派工通知卡片消息"""
        
        token = await self.get_tenant_access_token()
        
        # 构建卡片内容
        card_content = {
            "type": "interactive",
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": "🆕 新派工通知"},
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**派工单号:** {work_order.work_order_no}\n"
                                   f"**客户名称:** {work_order.customer_name}\n"
                                   f"**服务内容:** {work_order.description or '无'}\n"
                                   f"**预计时间:** {work_order.estimated_start_date or '待定'}\n"
                                   f"**紧急程度:** {work_order.priority.value}"
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "✅ 确认接单"},
                            "type": "primary",
                            "value": {
                                "work_order_id": str(work_order.id),
                                "technician_id": str(technician.id),
                                "action_type": "confirm"
                            }
                        },
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "❌ 拒绝接单"},
                            "type": "danger",
                            "value": {
                                "work_order_id": str(work_order.id),
                                "technician_id": str(technician.id),
                                "action_type": "reject"
                            }
                        }
                    ]
                },
                {
                    "tag": "note",
                    "elements": [
                        {"tag": "plain_text", "content": "点击确认接单后将自动创建外勤审批"}
                    ]
                }
            ]
        }
        
        # 发送消息
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/im/v1/messages?receive_id_type=open_id",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={
                    "receive_id": technician.feishu_id,
                    "msg_type": "interactive",
                    "content": json.dumps(card_content)
                }
            )
            
            result = response.json()
            
            if result.get("code") != 0:
                logger.error(f"发送卡片消息失败: {result}")
                raise Exception(f"发送派工通知失败: {result.get('msg')}")
            
            message_id = result.get("data", {}).get("message_id")
            logger.info(f"派工通知发送成功: message_id={message_id}, technician={technician.name}")
            
            return message_id
    
    async def update_card_message(self, message_id: str, card_content: dict) -> bool:
        """更新卡片消息内容"""
        
        token = await self.get_tenant_access_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self.BASE_URL}/im/v1/messages/{message_id}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={
                    "content": json.dumps(card_content)
                }
            )
            
            result = response.json()
            
            if result.get("code") != 0:
                logger.error(f"更新卡片消息失败: {result}")
                return False
            
            return True


# 全局实例
feishu_card_service = FeishuCardService()
```

---

## 七、数据库变更

### 7.1 新增字段

```sql
-- work_order_technicians 表新增审批相关字段（一人一审批模型）
ALTER TABLE work_order_technicians ADD COLUMN status VARCHAR(20) DEFAULT 'PENDING';
ALTER TABLE work_order_technicians ADD COLUMN accepted_at TIMESTAMP;
ALTER TABLE work_order_technicians ADD COLUMN rejected_at TIMESTAMP;
ALTER TABLE work_order_technicians ADD COLUMN feishu_message_id VARCHAR(100);
ALTER TABLE work_order_technicians ADD COLUMN approval_instance_code VARCHAR(100);
ALTER TABLE work_order_technicians ADD COLUMN approval_status VARCHAR(20) DEFAULT 'PENDING';
ALTER TABLE work_order_technicians ADD COLUMN approval_created_at TIMESTAMP;
ALTER TABLE work_order_technicians ADD COLUMN idempotency_key VARCHAR(100) UNIQUE;
```

### 7.2 字段说明

| 表 | 字段 | 说明 |
|------|------|------|
| work_order_technicians | status | 技术员接单状态（PENDING/ACCEPTED/REJECTED） |
| work_order_technicians | accepted_at | 确认接单时间 |
| work_order_technicians | rejected_at | 拒绝接单时间 |
| work_order_technicians | feishu_message_id | 飞书卡片消息ID（用于更新卡片） |
| work_order_technicians | approval_instance_code | **外勤审批实例码**（一人一审批） |
| work_order_technicians | approval_status | 审批状态（PENDING/APPROVED/REJECTED/CANCELED） |
| work_order_technicians | approval_created_at | 审批创建时间 |
| work_order_technicians | idempotency_key | **幂等键**（防重复创建审批） |

> **设计说明**：采用"一人一审批"模型，审批实例码存储在 `work_order_technicians` 表中，每个工程师确认接单后创建独立的审批实例。`idempotency_key` 格式为 `{work_order_id}_{technician_id}`，用于防止重复创建。

---

## 八、飞书开放平台配置

### 8.1 订阅方式

1. 登录飞书开放平台：https://open.feishu.cn/app
2. 选择应用 → 事件订阅
3. **订阅方式**：选择"使用长连接接收"
4. **订阅事件**：添加以下事件

### 8.2 需订阅的事件

| 事件类型 | 事件名称 | 说明 |
|---------|---------|------|
| `im.message.card_action_trigger` | 卡片交互触发 | 用户点击卡片按钮时触发 |
| `approval.instance.status_changed` | 审批实例状态变更 | 审批状态变化时触发 |

### 8.3 权限配置

| 权限名称 | 权限ID | 用途 |
|---------|--------|------|
| 获取与发送单聊、群聊消息 | `im:message` | 发送卡片消息 |
| 以应用身份发消息 | `im:message:send_as_bot` | Bot发消息 |
| 查看、创建、更新审批 | `approval:approval` | 创建审批实例 |
| 获取用户基本信息 | `contact:user.base:readonly` | 获取用户信息 |

---

## 九、启动方式

### 9.1 方式一：集成到 FastAPI

```python
# backend/app/main.py

from app.services.feishu_ws_service import start_ws_in_background

@app.on_event("startup")
async def startup_event():
    # 启动 WebSocket 长连接服务（后台线程）
    await start_ws_in_background()
    logger.info("飞书 WebSocket 服务已启动")
```

### 9.2 方式二：独立进程

```bash
# 启动独立 WebSocket 服务
python -m app.services.feishu_ws_service
```

---

## 十、测试验证

### 10.1 测试流程

1. 创建派工 → 发送飞书卡片消息
2. 工程师点击"确认接单" → WebSocket 接收回调
3. 自动创建外勤审批 → 更新卡片内容
4. 审批通过 → 更新派工状态

### 10.2 验证点

- [ ] WebSocket 长连接建立成功
- [ ] 卡片消息发送成功
- [ ] 卡片交互回调接收成功
- [ ] 外勤审批创建成功
- [ ] 卡片内容更新成功

---

## 十一、注意事项

1. **WebSocket 消息处理超时**：必须在 3 秒内处理完毕，否则触发重试
2. **连接数限制**：每个应用最多 50 个连接
3. **消息推送模式**：集群模式，不支持广播，同一应用多实例只有随机一个收到
4. **工程师必须有飞书ID**：确保 `users.feishu_id` 字段有值
5. **多工程师场景**：每人独立审批，审批实例码存储到 `work_order_technicians` 表

---

## 十二、后续扩展

1. **审批结果同步**：监听审批状态变更事件，更新派工状态
2. **出差/外出关联**：工程师手动发起出差审批，关联审批实例码
3. **催办通知**：审批超时自动发送催办消息
4. **批量派工**：支持批量创建派工 + 批量发送通知

---

## 附录

### A. 参考资料

- [飞书 WebSocket 长连接文档](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/event-subscription-guide/event-subscription-configure-/request-url-configuration-case)
- [飞书卡片消息文档](https://open.feishu.cn/document/client-docs/bot-v3/add-bot-card-message)
- [飞书审批 API 文档](https://open.feishu.cn/document/server-docs/approval-v4/approval-overview)
- [外勤审批定义](https://www.feishu.cn/approval/admin/createApproval?id=7579097404528397276&definitionCode=1E9D3E8F-15CF-45C9-BC93-2483DDBF9A9A)

### B. 相关 Approval Code

| 审批名称 | Approval Code |
|---------|---------------|
| 外勤申请 | `1E9D3E8F-15CF-45C9-BC93-2483DDBF9A9A` |
| 出差审批 | `92F6F3C9-D5EC-4955-A1D3-726552137B7D` |

---
