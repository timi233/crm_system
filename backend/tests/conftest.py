import itertools
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.dependencies import get_current_user
from app.database import get_db
from app.main import app as fastapi_app


class FakeScalarResult:
    def __init__(self, items=None):
        self._items = list(items or [])

    def all(self):
        return list(self._items)

    def first(self):
        return self._items[0] if self._items else None

    def one_or_none(self):
        return self.first()

    def one(self):
        if not self._items:
            raise LookupError("No rows found")
        return self._items[0]

    def scalar_one_or_none(self):
        return self.first()

    def scalar_one(self):
        return self.one()

    def __iter__(self):
        return iter(self._items)


class FakeResult:
    def __init__(self, items=None, rows=None):
        self._items = list(items or [])
        self._rows = list(rows if rows is not None else self._items)

    def scalars(self):
        return FakeScalarResult(self._items)

    def all(self):
        return list(self._rows)

    def first(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return self.all()

    def scalar_one_or_none(self):
        return self._items[0] if self._items else None

    def scalar_one(self):
        if not self._items:
            raise LookupError("No rows found")
        return self._items[0]


class FakeAsyncSession:
    def __init__(self):
        self.storage = {}
        self._queued_results = []
        self._id_counter = itertools.count(1)

    def queue_result(self, *, items=None, rows=None):
        self._queued_results.append(FakeResult(items=items, rows=rows))

    async def execute(self, query):
        if self._queued_results:
            return self._queued_results.pop(0)
        return FakeResult(items=[], rows=[])

    def add(self, obj):
        if getattr(obj, "id", None) is None:
            setattr(obj, "id", next(self._id_counter))
        self.storage.setdefault(type(obj), []).append(obj)

    async def flush(self):
        return None

    async def commit(self):
        return None

    async def rollback(self):
        return None

    async def refresh(self, obj, attrs=None):
        defaults = {
            "converted_to_opportunity": False,
            "has_confirmed_requirement": False,
            "has_confirmed_budget": False,
            "is_active": True,
        }
        for field, value in defaults.items():
            if hasattr(obj, field) and getattr(obj, field) is None:
                setattr(obj, field, value)

        if attrs:
            for attr in attrs:
                if not hasattr(obj, attr):
                    setattr(obj, attr, None)
        return None

    async def delete(self, obj):
        items = self.storage.get(type(obj), [])
        if obj in items:
            items.remove(obj)

    async def get(self, model, obj_id):
        for item in self.storage.get(model, []):
            if getattr(item, "id", None) == obj_id:
                return item
        return None


@pytest.fixture
def app():
    fastapi_app.dependency_overrides.clear()
    yield fastapi_app
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def fake_db():
    return FakeAsyncSession()


@pytest_asyncio.fixture
async def client(app, fake_db) -> AsyncIterator[AsyncClient]:
    async def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client


@pytest.fixture
def admin_user():
    return {"id": 1, "email": "admin@example.com", "role": "admin", "name": "Admin"}


@pytest.fixture
def sales_user():
    return {"id": 2, "email": "sales@example.com", "role": "sales", "name": "Sales"}


@pytest.fixture
def finance_user():
    return {
        "id": 3,
        "email": "finance@example.com",
        "role": "finance",
        "name": "Finance",
    }


@pytest.fixture
def business_user():
    return {
        "id": 4,
        "email": "business@example.com",
        "role": "business",
        "name": "Business",
    }


@pytest.fixture
def technician_user():
    return {
        "id": 5,
        "email": "tech@example.com",
        "role": "technician",
        "name": "Technician",
    }


@pytest.fixture
def auth_as(app):
    def _auth(user):
        async def override_current_user():
            return user

        app.dependency_overrides[get_current_user] = override_current_user
        return user

    yield _auth
    app.dependency_overrides.pop(get_current_user, None)
