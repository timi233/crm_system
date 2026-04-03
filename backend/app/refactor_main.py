import re

with open("main.py.backup", "r") as f:
    content = f.read()

# 替换 imports
new_imports = """from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Union, Dict, Any
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
import bcrypt
import secrets
import re
import os
from dotenv import load_dotenv

from app.database import get_db, async_session_maker
from app.models.user import User
from app.models.customer import TerminalCustomer
from app.models.channel import Channel
from app.models.opportunity import Opportunity
from app.models.project import Project
from app.models.contract import Contract
from app.models.followup import FollowUp
from app.models.product import Product

load_dotenv()
"""

content = re.sub(
    r"from fastapi import.*?load_dotenv\(\)", new_imports, content, flags=re.DOTALL
)

# 删除内存数据库定义和种子数据
content = re.sub(
    r"# In-memory database.*?seed_initial_data\(\)\s*\n", "", content, flags=re.DOTALL
)

with open("main.py", "w") as f:
    f.write(content)

print("第一步完成：imports 和删除内存数据库")
