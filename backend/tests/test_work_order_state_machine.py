import pytest

from app.models.work_order import WorkOrderStatus, WorkOrderTechnician, WorkOrderApprovalStatus
from app.routers.work_order import (
    VALID_STATUS_TRANSITIONS,
    _is_valid_status_transition,
    _has_approved_assignment,
)


def test_valid_status_transitions_pending():
    assert WorkOrderStatus.ACCEPTED in VALID_STATUS_TRANSITIONS[WorkOrderStatus.PENDING]
    assert WorkOrderStatus.CANCELLED in VALID_STATUS_TRANSITIONS[WorkOrderStatus.PENDING]
    assert WorkOrderStatus.REJECTED in VALID_STATUS_TRANSITIONS[WorkOrderStatus.PENDING]
    assert WorkOrderStatus.IN_SERVICE not in VALID_STATUS_TRANSITIONS[WorkOrderStatus.PENDING]
    assert WorkOrderStatus.DONE not in VALID_STATUS_TRANSITIONS[WorkOrderStatus.PENDING]


def test_valid_status_transitions_accepted():
    assert WorkOrderStatus.IN_SERVICE in VALID_STATUS_TRANSITIONS[WorkOrderStatus.ACCEPTED]
    assert WorkOrderStatus.CANCELLED in VALID_STATUS_TRANSITIONS[WorkOrderStatus.ACCEPTED]
    assert WorkOrderStatus.REJECTED in VALID_STATUS_TRANSITIONS[WorkOrderStatus.ACCEPTED]
    assert WorkOrderStatus.PENDING not in VALID_STATUS_TRANSITIONS[WorkOrderStatus.ACCEPTED]
    assert WorkOrderStatus.DONE not in VALID_STATUS_TRANSITIONS[WorkOrderStatus.ACCEPTED]


def test_valid_status_transitions_in_service():
    assert WorkOrderStatus.DONE in VALID_STATUS_TRANSITIONS[WorkOrderStatus.IN_SERVICE]
    assert WorkOrderStatus.CANCELLED in VALID_STATUS_TRANSITIONS[WorkOrderStatus.IN_SERVICE]
    assert WorkOrderStatus.ACCEPTED not in VALID_STATUS_TRANSITIONS[WorkOrderStatus.IN_SERVICE]
    assert WorkOrderStatus.PENDING not in VALID_STATUS_TRANSITIONS[WorkOrderStatus.IN_SERVICE]


def test_valid_status_transitions_done():
    assert len(VALID_STATUS_TRANSITIONS[WorkOrderStatus.DONE]) == 0


def test_valid_status_transitions_cancelled():
    assert len(VALID_STATUS_TRANSITIONS[WorkOrderStatus.CANCELLED]) == 0


def test_valid_status_transitions_rejected():
    assert len(VALID_STATUS_TRANSITIONS[WorkOrderStatus.REJECTED]) == 0


def test_is_valid_status_transition_returns_true():
    assert _is_valid_status_transition(WorkOrderStatus.PENDING, WorkOrderStatus.ACCEPTED)
    assert _is_valid_status_transition(WorkOrderStatus.ACCEPTED, WorkOrderStatus.IN_SERVICE)
    assert _is_valid_status_transition(WorkOrderStatus.IN_SERVICE, WorkOrderStatus.DONE)


def test_is_valid_status_transition_returns_false():
    assert not _is_valid_status_transition(WorkOrderStatus.PENDING, WorkOrderStatus.IN_SERVICE)
    assert not _is_valid_status_transition(WorkOrderStatus.PENDING, WorkOrderStatus.DONE)
    assert not _is_valid_status_transition(WorkOrderStatus.ACCEPTED, WorkOrderStatus.PENDING)
    assert not _is_valid_status_transition(WorkOrderStatus.IN_SERVICE, WorkOrderStatus.ACCEPTED)
    assert not _is_valid_status_transition(WorkOrderStatus.DONE, WorkOrderStatus.CANCELLED)
    assert not _is_valid_status_transition(WorkOrderStatus.CANCELLED, WorkOrderStatus.PENDING)


def test_is_valid_status_transition_invalid_current_status():
    assert not _is_valid_status_transition("unknown_status", WorkOrderStatus.ACCEPTED)


class MockWorkOrderTechnician:
    def __init__(self, approval_status):
        self.approval_status = approval_status


class MockWorkOrder:
    def __init__(self, technicians):
        self.technicians = technicians


def test_has_approved_assignment_returns_true_when_approved():
    technicians = [
        MockWorkOrderTechnician(WorkOrderApprovalStatus.APPROVED),
        MockWorkOrderTechnician(WorkOrderApprovalStatus.PENDING),
    ]
    work_order = MockWorkOrder(technicians)
    assert _has_approved_assignment(work_order)


def test_has_approved_assignment_returns_false_when_no_approved():
    technicians = [
        MockWorkOrderTechnician(WorkOrderApprovalStatus.PENDING),
        MockWorkOrderTechnician(WorkOrderApprovalStatus.REJECTED),
    ]
    work_order = MockWorkOrder(technicians)
    assert not _has_approved_assignment(work_order)


def test_has_approved_assignment_returns_false_when_empty():
    work_order = MockWorkOrder([])
    assert not _has_approved_assignment(work_order)


def test_has_approved_assignment_with_all_rejected():
    technicians = [
        MockWorkOrderTechnician(WorkOrderApprovalStatus.REJECTED),
        MockWorkOrderTechnician(WorkOrderApprovalStatus.REJECTED),
    ]
    work_order = MockWorkOrder(technicians)
    assert not _has_approved_assignment(work_order)


def test_has_approved_assignment_with_multiple_approved():
    technicians = [
        MockWorkOrderTechnician(WorkOrderApprovalStatus.APPROVED),
        MockWorkOrderTechnician(WorkOrderApprovalStatus.APPROVED),
    ]
    work_order = MockWorkOrder(technicians)
    assert _has_approved_assignment(work_order)


def test_has_approved_assignment_returns_false_when_no_approved():
    technicians = [
        MockWorkOrderTechnician(WorkOrderApprovalStatus.PENDING),
        MockWorkOrderTechnician(WorkOrderApprovalStatus.REJECTED),
    ]
    work_order = MockWorkOrder(technicians)
    assert not _has_approved_assignment(work_order)


def test_has_approved_assignment_returns_false_when_empty():
    work_order = MockWorkOrder([])
    assert not _has_approved_assignment(work_order)


def test_has_approved_assignment_with_all_rejected():
    technicians = [
        MockWorkOrderTechnician(WorkOrderApprovalStatus.REJECTED),
        MockWorkOrderTechnician(WorkOrderApprovalStatus.REJECTED),
    ]
    work_order = MockWorkOrder(technicians)
    assert not _has_approved_assignment(work_order)


def test_has_approved_assignment_with_multiple_approved():
    technicians = [
        MockWorkOrderTechnician(WorkOrderApprovalStatus.APPROVED),
        MockWorkOrderTechnician(WorkOrderApprovalStatus.APPROVED),
    ]
    work_order = MockWorkOrder(technicians)
    assert _has_approved_assignment(work_order)