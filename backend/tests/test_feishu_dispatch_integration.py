import json
import asyncio

import pytest

from app.handlers.approval_status_handler import handle_approval_status_changed
from app.models.work_order import (
    WorkOrder,
    WorkOrderApprovalStatus,
    WorkOrderStatus,
    WorkOrderTechnician,
)
from app.services.feishu_approval_service import FeishuApprovalService
from app.services.feishu_card_service import FeishuCardService
from app.services.feishu_ws_service import FeishuWebSocketService


pytestmark = pytest.mark.asyncio


async def test_dispatch_card_payload_matches_handler_contract():
    service = FeishuCardService()

    card = service._build_dispatch_card(
        {"id": 5, "open_id": "ou_tech_1"},
        {
            "id": 9,
            "work_order_no": "WO-001",
            "customer_name": "Acme",
            "description": "Install device",
            "scheduled_start": "2026-04-24 09:00",
            "scheduled_end": "2026-04-24 18:00",
        },
    )

    actions = card["elements"][-1]["actions"]
    assert len(actions) == 2
    assert actions[0]["text"]["content"] == "确认接收"
    assert actions[0]["value"] == {
        "action_type": "confirm",
        "work_order_id": 9,
        "technician_id": 5,
    }
    assert actions[1]["value"] == {
        "action_type": "reject",
        "work_order_id": 9,
        "technician_id": 5,
    }


async def test_approval_form_maps_customer_name_and_sales_contact():
    service = FeishuApprovalService()

    form = service._build_approval_form(
        {
            "work_order_no": "WO-002",
            "description": "On-site service",
            "scheduled_start": "2026-04-24",
            "scheduled_end": "2026-04-25",
            "customer": {
                "name": "Example Customer",
                "contact_person": "Alice",
                "phone": "13800138000",
            },
        },
        {
            "open_id": "ou_tech_1",
            "sales_contact": {"open_id": "ou_sales_1"},
            "idempotency_key": "9_5",
        },
    )

    widgets = {item["id"]: item for item in form}
    assert widgets["widget17646459981630001"]["value"] == "Example Customer"
    assert widgets["widget17675834510510001"]["value"] == ["ou_sales_1"]
    assert widgets["widget17646460247810001"]["value"] == "Alice"
    assert widgets["widget17646460277440001"]["value"] == "13800138000"


async def test_ws_dispatch_routes_card_action_payload(monkeypatch):
    service = FeishuWebSocketService()
    captured = {}

    async def fake_process_card_action(**kwargs):
        captured.update(kwargs)
        return {"success": True}

    monkeypatch.setattr(
        "app.services.feishu_ws_service.process_card_action", fake_process_card_action
    )

    await service._dispatch_event(
        {
            "header": {"event_type": "im.message.card_action_trigger"},
            "event": {
                "operator": {"open_id": "ou_tech_1"},
                "message": {"message_id": "om_xxx"},
                "action": {
                    "value": json.dumps(
                        {
                            "action_type": "confirm",
                            "work_order_id": 11,
                            "technician_id": 7,
                        }
                    )
                },
            },
        }
    )

    assert captured == {
        "work_order_id": 11,
        "technician_id": 7,
        "action_type": "confirm",
        "operator_open_id": "ou_tech_1",
        "message_id": "om_xxx",
    }


async def test_ws_dispatch_routes_approval_status_event(monkeypatch):
    service = FeishuWebSocketService()
    captured = {}

    async def fake_handle_approval_status_changed(event):
        captured.update(event)
        return {"success": True}

    monkeypatch.setattr(
        "app.services.feishu_ws_service.handle_approval_status_changed",
        fake_handle_approval_status_changed,
    )

    await service._dispatch_event(
        {
            "header": {"event_type": "approval.instance.status_changed"},
            "event": {
                "instance_code": "ins_123",
                "status": "APPROVED",
            },
        }
    )

    assert captured == {
        "instance_code": "ins_123",
        "status": "APPROVED",
    }


async def test_ws_submit_coro_runs_on_active_loop():
    service = FeishuWebSocketService()
    captured = {"done": False}

    async def mark_done():
        captured["done"] = True

    service._submit_coro(mark_done())
    await asyncio.sleep(0)

    assert captured["done"] is True


async def test_approval_status_handler_updates_work_order_status(monkeypatch):
    work_order = WorkOrder(id=9, work_order_no="WO-009", customer_name="Acme", description="On-site")
    work_order.status = WorkOrderStatus.PENDING

    assignment = WorkOrderTechnician(
        id=5,
        work_order_id=9,
        technician_id=7,
        approval_instance_code="ins_123",
    )
    assignment.approval_status = WorkOrderApprovalStatus.PENDING

    approved_assignment = WorkOrderTechnician(
        id=6,
        work_order_id=9,
        technician_id=8,
        approval_instance_code="ins_approved",
    )
    approved_assignment.approval_status = WorkOrderApprovalStatus.APPROVED

    class FakeSession:
        def __init__(self):
            self.results = [
                assignment,
                None,
            ]
            self.committed = False

        async def execute(self, stmt):
            from tests.conftest import FakeResult

            item = self.results.pop(0)
            return FakeResult(items=[item] if item else [])

        async def get(self, model, obj_id):
            assert model is WorkOrder
            assert obj_id == 9
            return work_order

        async def commit(self):
            self.committed = True

    class FakeContext:
        def __init__(self, session):
            self.session = session

        async def __aenter__(self):
            return self.session

        async def __aexit__(self, exc_type, exc, tb):
            return False

    session = FakeSession()
    monkeypatch.setattr(
        "app.handlers.approval_status_handler.async_session_maker",
        lambda: FakeContext(session),
    )

    result = await handle_approval_status_changed(
        {"instance_code": "ins_123", "status": "APPROVED"}
    )

    assert result["success"] is True
    assert assignment.approval_status == WorkOrderApprovalStatus.APPROVED
    assert work_order.status == WorkOrderStatus.ACCEPTED
    assert session.committed is True


async def test_approval_rejection_waits_for_other_pending_assignments(monkeypatch):
    work_order = WorkOrder(
        id=10,
        work_order_no="WO-010",
        customer_name="Acme",
        description="On-site",
    )
    work_order.status = WorkOrderStatus.PENDING

    rejected_assignment = WorkOrderTechnician(
        id=7,
        work_order_id=10,
        technician_id=11,
        approval_instance_code="ins_rejected",
    )
    rejected_assignment.approval_status = WorkOrderApprovalStatus.PENDING
    pending_assignment = WorkOrderTechnician(
        id=8,
        work_order_id=10,
        technician_id=12,
        approval_instance_code="ins_pending",
    )
    pending_assignment.approval_status = WorkOrderApprovalStatus.PENDING

    class FakeSession:
        def __init__(self):
            self.committed = False

        async def execute(self, stmt):
            from tests.conftest import FakeResult

            if not hasattr(self, "called"):
                self.called = True
                return FakeResult(items=[rejected_assignment])
            return FakeResult(items=[rejected_assignment, pending_assignment])

        async def get(self, model, obj_id):
            assert model is WorkOrder
            assert obj_id == 10
            return work_order

        async def commit(self):
            self.committed = True

    class FakeContext:
        def __init__(self, session):
            self.session = session

        async def __aenter__(self):
            return self.session

        async def __aexit__(self, exc_type, exc, tb):
            return False

    session = FakeSession()
    monkeypatch.setattr(
        "app.handlers.approval_status_handler.async_session_maker",
        lambda: FakeContext(session),
    )

    result = await handle_approval_status_changed(
        {"instance_code": "ins_rejected", "status": "REJECTED"}
    )

    assert result["success"] is True
    assert rejected_assignment.approval_status == WorkOrderApprovalStatus.REJECTED
    assert work_order.status == WorkOrderStatus.PENDING
    assert session.committed is True
