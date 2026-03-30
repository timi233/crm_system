import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# JWT settings
SECRET_KEY = os.environ.get(
    "JWT_SECRET_KEY", "your-secret-key-here-change-in-production"
)

print(f"SECRET_KEY length: {len(SECRET_KEY)}")
print(f"SECRET_KEY preview: {SECRET_KEY[:10]}...")

# Test JWT encoding/decoding
from jose import jwt
from datetime import datetime, timedelta


def create_test_token():
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode = {"sub": 1, "role": "admin", "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def decode_test_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except Exception as e:
        return f"Decode error: {e}"


token = create_test_token()
print(f"Test token: {token}")
decoded = decode_test_token(token)
print(f"Decoded token: {decoded}")
