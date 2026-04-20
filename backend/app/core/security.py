from datetime import datetime, timedelta
from typing import Optional

from passlib.context import CryptContext
from jose import jwt
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_SECRET_KEY = os.environ.get(
    "JWT_SECRET_KEY", "dev-only-insecure-key-do-not-use-in-production"
)
JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


get_password_hash = hash_password


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt
