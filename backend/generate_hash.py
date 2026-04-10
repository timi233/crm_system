import bcrypt

password = "admin123"
hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
print(f"Password: {password}")
print(f"Hashed: {hashed.decode('utf-8')}")
