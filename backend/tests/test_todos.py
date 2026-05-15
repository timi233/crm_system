from datetime import date, timedelta
from typing import Any


class MockSession:
    def __init__(self):
        self._data = []

    def add_data(self, data: list):
        self._data = data

    async def execute(self, query: Any):
        return MockResult(self._data)


class MockResult:
    def __init__(self, data: list):
        self._data = data

    def scalars(self):
        return MockScalars(self._data)

    def scalar_one_or_none(self):
        return self._data[0] if self._data else None


class MockScalars:
    def __init__(self, data: list):
        self._data = data

    def all(self):
        return self._data


class MockFollowUp:
    def __init__(self, id, next_follow_up_date, next_action=None, follow_up_content=None, lead_id=None, opportunity_id=None, project_id=None, terminal_customer_id=None, channel_id=None, follow_up_type="business"):
        self.id = id
        self.next_follow_up_date = next_follow_up_date
        self.next_action = next_action
        self.follow_up_content = follow_up_content
        self.lead_id = lead_id
        self.opportunity_id = opportunity_id
        self.project_id = project_id
        self.terminal_customer_id = terminal_customer_id
        self.channel_id = channel_id
        self.follow_up_type = follow_up_type


class MockWorkOrder:
    def __init__(self, id, work_order_no, status, priority, description=None, customer_name="客户", estimated_start_date=None, estimated_end_date=None):
        self.id = id
        self.work_order_no = work_order_no
        self.status = MockEnumValue(status)
        self.priority = MockEnumValue(priority)
        self.description = description
        self.customer_name = customer_name
        self.estimated_start_date = estimated_start_date
        self.estimated_end_date = estimated_end_date


class MockEnumValue:
    def __init__(self, value):
        self._value = value

    @property
    def value(self):
        return self._value


class MockWorkOrderTechnician:
    def __init__(self, work_order_id, technician_id, status="PENDING"):
        self.work_order_id = work_order_id
        self.technician_id = technician_id
        self.status = status


class MockContract:
    def __init__(self, id, contract_code, contract_name, expiry_date, contract_status="signed"):
        self.id = id
        self.contract_code = contract_code
        self.contract_name = contract_name
        self.expiry_date = expiry_date
        self.contract_status = contract_status


class MockWorkReport:
    def __init__(self, id, owner_id, report_type, report_date, status="draft"):
        self.id = id
        self.owner_id = owner_id
        self.report_type = report_type
        self.report_date = report_date
        self.status = status


class MockHandoverRequest:
    def __init__(self, id, from_user_id, status):
        self.id = id
        self.from_user_id = from_user_id
        self.status = status


def test_todo_schema_fields():
    from app.schemas.todo import TodoRead, TodoListResponse

    todo = TodoRead(
        key="follow_up:1",
        type="follow_up",
        title="跟进提醒",
        description="跟进内容",
        priority="high",
        due_date="2026-05-15",
        entity_type="lead",
        entity_id=1,
        link="/leads/1/full",
        source="follow_up",
        status="open",
    )
    assert todo.key == "follow_up:1"
    assert todo.type == "follow_up"
    assert todo.priority == "high"

    response = TodoListResponse(items=[todo], total=1)
    assert response.total == 1
    assert len(response.items) == 1


def test_todo_filter_params():
    from app.schemas.todo import TodoFilterParams

    filters = TodoFilterParams(
        type="follow_up",
        priority="high",
        date_from=date.today(),
        date_to=date.today() + timedelta(days=7),
        skip=0,
        limit=50,
    )
    assert filters.type == "follow_up"
    assert filters.priority == "high"
    assert filters.limit == 50


def test_todo_service_resolve_followup_link_lead():
    from app.services.todo_service import TodoService

    service = TodoService(None)
    f = MockFollowUp(id=1, next_follow_up_date=date.today(), lead_id=100)
    entity_type, entity_id, link = service._resolve_followup_link(f)
    assert entity_type == "lead"
    assert entity_id == 100
    assert link == "/leads/100/full"


def test_todo_service_resolve_followup_link_opportunity():
    from app.services.todo_service import TodoService

    service = TodoService(None)
    f = MockFollowUp(id=1, next_follow_up_date=date.today(), opportunity_id=200)
    entity_type, entity_id, link = service._resolve_followup_link(f)
    assert entity_type == "opportunity"
    assert entity_id == 200
    assert link == "/opportunities/200/full"


def test_todo_service_resolve_followup_link_default():
    from app.services.todo_service import TodoService

    service = TodoService(None)
    f = MockFollowUp(id=1, next_follow_up_date=date.today(), follow_up_type="business")
    entity_type, entity_id, link = service._resolve_followup_link(f)
    assert entity_type is None
    assert entity_id is None
    assert link == "/business-follow-ups"


def test_todo_service_map_work_order_priority_urgent():
    from app.services.todo_service import TodoService

    service = TodoService(None)
    priority = service._map_work_order_priority(MockEnumValue("URGENT"))
    assert priority == "high"


def test_todo_service_map_work_order_priority_normal():
    from app.services.todo_service import TodoService

    service = TodoService(None)
    priority = service._map_work_order_priority(MockEnumValue("NORMAL"))
    assert priority == "normal"


def test_todo_service_map_work_order_priority_none():
    from app.services.todo_service import TodoService

    service = TodoService(None)
    priority = service._map_work_order_priority(None)
    assert priority == "normal"


def test_todo_service_apply_filters_type():
    from app.schemas.todo import TodoRead, TodoFilterParams
    from app.services.todo_service import TodoService

    service = TodoService(None)
    todos = [
        TodoRead(key="1", type="follow_up", title="跟进", source="follow_up"),
        TodoRead(key="2", type="work_order", title="工单", source="work_order"),
    ]
    filters = TodoFilterParams(type="follow_up")
    filtered = service._apply_filters(todos, filters)
    assert len(filtered) == 1
    assert filtered[0].type == "follow_up"


def test_todo_service_apply_filters_priority():
    from app.schemas.todo import TodoRead, TodoFilterParams
    from app.services.todo_service import TodoService

    service = TodoService(None)
    todos = [
        TodoRead(key="1", type="follow_up", title="跟进", priority="high", source="follow_up"),
        TodoRead(key="2", type="work_order", title="工单", priority="normal", source="work_order"),
    ]
    filters = TodoFilterParams(priority="high")
    filtered = service._apply_filters(todos, filters)
    assert len(filtered) == 1
    assert filtered[0].priority == "high"


def test_todo_service_apply_filters_date_range():
    from app.schemas.todo import TodoRead, TodoFilterParams
    from app.services.todo_service import TodoService

    service = TodoService(None)
    todos = [
        TodoRead(key="1", type="follow_up", title="跟进", due_date="2026-05-15", source="follow_up"),
        TodoRead(key="2", type="work_order", title="工单", due_date="2026-05-20", source="work_order"),
        TodoRead(key="3", type="handover", title="交接", due_date=None, source="handover"),
    ]
    filters = TodoFilterParams(date_from=date(2026, 5, 14), date_to=date(2026, 5, 16))
    filtered = service._apply_filters(todos, filters)
    assert len(filtered) == 1
    assert filtered[0].due_date == "2026-05-15"