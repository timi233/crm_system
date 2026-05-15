import hashlib
import hmac
import json
import time

import pytest

from app.models.work_order import (
    WorkOrder,
    WorkOrderApprovalStatus,
    WorkOrderStatus,
    WorkOrderTechnician,
)


pytestmark = pytest.mark.asyncio


async def test_list_work_orders_requires_auth(client):
    response = await client.get("/work-orders/")
    assert response.status_code == 401


async def test_list_work_orders_with_auth_returns_200(client, auth_as, admin_user):
    auth_as(admin_user)
    response = await client.get("/work-orders/")
    assert response.status_code == 200
    assert response.status_code not in {401, 404}


async def test_create_work_order_validates_body(client, auth_as, admin_user):
    auth_as(admin_user)
    response = await client.post("/work-orders/", json={})
    assert response.status_code == 422


async def test_work_order_cannot_enter_service_without_approved_assignment(
    client, auth_as, admin_user, fake_db, monkeypatch
):
    auth_as(admin_user)

    work_order = WorkOrder(
        id=1,
        work_order_no="WO-001",
        customer_name="Acme",
        description="On-site service",
        submitter_id=1,
    )
    work_order.status = WorkOrderStatus.ACCEPTED

    assignment = WorkOrderTechnician(
        id=1,
        work_order_id=1,
        technician_id=5,
    )
    assignment.approval_status = WorkOrderApprovalStatus.PENDING
    work_order.technicians = [assignment]

    fake_db.queue_result(items=[work_order])

    async def noop_authorize(*args, **kwargs):
        return None

    monkeypatch.setattr(
        "app.routers.work_order.policy_service.authorize",
        noop_authorize,
    )

    response = await client.patch(
        "/work-orders/1/status",
        json={"status": "IN_SERVICE"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "至少需要一位审批通过的技术员后，工单才能继续流转"


async def test_dispatch_webhook_enforces_approval_gate(
    client, fake_db, monkeypatch
):
    monkeypatch.setenv("DISPATCH_WEBHOOK_SECRET", "test-webhook-secret")

    work_order = WorkOrder(
        id=1,
        work_order_no="WO-001",
        customer_name="Acme",
        description="On-site service",
        submitter_id=1,
    )
    work_order.status = WorkOrderStatus.ACCEPTED
    assignment = WorkOrderTechnician(
        id=1,
        work_order_id=1,
        technician_id=5,
    )
    assignment.approval_status = WorkOrderApprovalStatus.PENDING
    work_order.technicians = [assignment]

    fake_db.queue_result(items=[])
    fake_db.queue_result(items=[work_order])

    payload = {
        "event": "status_changed",
        "work_order_id": "1",
        "work_order_no": "WO-001",
        "status": "in_service",
        "previous_status": "accepted",
        "timestamp": "2026-04-27T00:00:00Z",
        "metadata": {},
    }
    body = json.dumps(payload).encode()
    timestamp = str(int(time.time()))
    event_id = "test-event-123"
    signed_payload = f"{timestamp}.".encode() + body
    signature = hmac.new(
        b"test-webhook-secret",
        signed_payload,
        hashlib.sha256,
    ).hexdigest()

    response = await client.post(
        "/webhooks/dispatch",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Dispatch-Signature": signature,
            "X-Dispatch-Timestamp": timestamp,
            "X-Dispatch-Event-Id": event_id,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "至少需要一位审批通过的技术员后，工单才能继续流转"
    assert work_order.status == WorkOrderStatus.ACCEPTED
