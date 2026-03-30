import os
from dotenv import load_dotenv
from jose import jwt
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv()

# JWT settings
SECRET_KEY = os.environ.get(
    "JWT_SECRET_KEY", "your-secret-key-here-change-in-production"
)
ALGORITHM = "HS256"

# Create a token with sub as integer (like the backend does)
expire = datetime.utcnow() + timedelta(minutes=30)
to_encode = {"sub": 1, "role": "admin", "exp": expire}
encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

print(f"Encoded token: {encoded_jwt}")

# Decode it
try:
    payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=[ALGORITHM])
    print(f"Decoded payload: {payload}")
    user_id = payload.get("sub")
    print(f"User ID type: {type(user_id)}, value: {user_id}")
    # This should work in the backend
except Exception as e:
    print(f"Decode error: {e}")
