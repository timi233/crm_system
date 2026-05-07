import pytest
import calendar
from datetime import datetime, timedelta

from jose import jwt, JWTError
from app.core.security import JWT_SECRET_KEY, JWT_ALGORITHM, create_access_token


def test_create_access_token_includes_expiry():
    token = create_access_token(data={"sub": "1", "role": "admin"})
    decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    assert "exp" in decoded
    assert decoded["sub"] == "1"
    assert decoded["role"] == "admin"


def test_create_access_token_with_custom_expiry():
    custom_delta = timedelta(minutes=10)
    token = create_access_token(data={"sub": "2", "role": "sales"}, expires_delta=custom_delta)
    decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    assert "exp" in decoded
    exp_timestamp = decoded["exp"]
    expected_exp = calendar.timegm((datetime.utcnow() + custom_delta).utctimetuple())
    assert abs(exp_timestamp - expected_exp) < 10


def test_expired_token_decode_raises_error():
    expired_payload = {
        "sub": "3",
        "role": "technician",
        "exp": datetime.utcnow().timestamp() - 3600,
    }
    expired_token = jwt.encode(expired_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    with pytest.raises(JWTError):
        jwt.decode(expired_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])


def test_invalid_signature_raises_error():
    fake_token = jwt.encode({"sub": "4", "role": "sales"}, "wrong-secret", algorithm=JWT_ALGORITHM)
    with pytest.raises(JWTError):
        jwt.decode(fake_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])


def test_malformed_token_raises_error():
    malformed_token = "not-a-valid.jwt.token"
    with pytest.raises(JWTError):
        jwt.decode(malformed_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])


def test_token_without_required_fields_still_decodes():
    token = jwt.encode({"foo": "bar"}, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    assert decoded["foo"] == "bar"
    assert "sub" not in decoded


async def test_logout_endpoint_returns_success(client, auth_as, admin_user):
    auth_as(admin_user)
    response = await client.post("/auth/logout")
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"


async def test_logout_requires_authentication(client):
    response = await client.post("/auth/logout")
    assert response.status_code == 401
