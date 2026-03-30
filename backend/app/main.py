from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Union, Dict, Any
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import bcrypt
import secrets
import re
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.environ.get(
    "JWT_SECRET_KEY", "your-secret-key-here-change-in-production"
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# In-memory database (replace with real database in production)
db = {
    "users": {},
    "customers": {},
    "channels": {},
    "opportunities": {},
    "projects": {},
    "contracts": {},
    "followups": {},
    "products": {},
    "refresh_tokens": set(),
    "blacklisted_tokens": set(),
}


# Seed some initial data for testing
def seed_initial_data():
    # Create admin user
    admin_user = {
        "id": 1,
        "name": "Admin User",
        "email": "admin@example.com",
        "hashed_password": pwd_context.hash("admin123"),
        "role": "admin",
        "sales_leader_id": None,
        "sales_region": None,
    }
    db["users"][1] = admin_user

    # Create sales user
    sales_user = {
        "id": 2,
        "name": "Sales User",
        "email": "sales@example.com",
        "hashed_password": pwd_context.hash("sales123"),
        "role": "sales",
        "sales_leader_id": 1,
        "sales_region": "Jinan",
    }
    db["users"][2] = sales_user

    # Create business user
    business_user = {
        "id": 3,
        "name": "Business User",
        "email": "business@example.com",
        "hashed_password": pwd_context.hash("business123"),
        "role": "business",
        "sales_leader_id": 1,
        "sales_region": "Qingdao",
    }
    db["users"][3] = business_user

    # Create finance user
    finance_user = {
        "id": 4,
        "name": "Finance User",
        "email": "finance@example.com",
        "hashed_password": pwd_context.hash("finance123"),
        "role": "finance",
        "sales_leader_id": None,
        "sales_region": None,
    }
    db["users"][4] = finance_user


seed_initial_data()


# Models and Schemas
class UserBase(BaseModel):
    name: str
    email: str
    sales_leader_id: Optional[int] = None
    sales_region: Optional[str] = None


class UserCreate(UserBase):
    password: str
    role: str = Field(..., pattern="^(admin|sales|business|finance)$")


class UserRead(UserBase):
    id: int
    role: str


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: int
    role: str


# Customer schemas
class CustomerBase(BaseModel):
    customer_name: str
    customer_nickname: Optional[str] = None
    customer_industry: str = Field(
        ...,
        pattern="^(Manufacturing|Finance|Government|Healthcare|Education|Energy|Other)$",
    )
    customer_region: str
    customer_owner_id: int
    main_contact: Optional[str] = None
    phone: Optional[str] = None
    customer_status: str = Field(..., pattern="^(Potential|Active|Existing|Lost)$")
    maintenance_expiry: Optional[str] = None
    notes: Optional[str] = None


class CustomerCreate(CustomerBase):
    pass


class CustomerRead(CustomerBase):
    id: int
    customer_code: str


# Channel schemas
class ChannelBase(BaseModel):
    company_name: str
    channel_type: str = Field(
        ..., pattern="^(Primary Channel|Secondary Channel|Direct Terminal Customer)$"
    )
    main_contact: Optional[str] = None
    phone: Optional[str] = None
    billing_info: Optional[str] = None
    notes: Optional[str] = None


class ChannelCreate(ChannelBase):
    pass


class ChannelRead(ChannelBase):
    id: int
    channel_code: str


# Opportunity schemas
class OpportunityBase(BaseModel):
    opportunity_name: str
    terminal_customer_id: int
    opportunity_source: str = Field(
        ..., pattern="^(Direct Sales|Channel|Customer Referral|Renewal/Expansion)$"
    )
    product_ids: Optional[List[int]] = None
    opportunity_stage: str = Field(
        ...,
        pattern="^(Initial Contact|Needs Confirmation|Proposal|Vendor Registration|Decision Pending|Won→Project|Lost)$",
    )
    lead_grade: str = Field(..., pattern="^(A|B|C)$")
    expected_contract_amount: float
    expected_close_date: Optional[str] = None
    sales_owner_id: int
    channel_id: Optional[int] = None
    vendor_registration_status: Optional[str] = None
    vendor_discount: Optional[float] = None
    loss_reason: Optional[str] = None
    project_id: Optional[int] = None

    @validator("loss_reason", always=True)
    def validate_loss_reason(cls, v, values):
        if values.get("opportunity_stage") == "Lost" and not v:
            raise ValueError('loss_reason is required when opportunity_stage is "Lost"')
        return v


class OpportunityCreate(OpportunityBase):
    pass


class OpportunityRead(OpportunityBase):
    id: int
    opportunity_code: str
    created_at: str


# Project schemas
class ProjectBase(BaseModel):
    project_name: str
    terminal_customer_id: int
    channel_id: Optional[int] = None
    source_opportunity_id: Optional[int] = None
    product_ids: List[int]
    business_type: str = Field(
        ..., pattern="^(New Project|Renewal/Maintenance|Expansion|Additional Purchase)$"
    )
    project_status: str = Field(
        ...,
        pattern="^(Initiating|Executing|Pending Acceptance|Accepted|Paid|Terminated)$",
    )
    sales_owner_id: int
    downstream_contract_amount: float
    upstream_procurement_amount: Optional[float] = None
    direct_project_investment: Optional[float] = None
    additional_investment: Optional[float] = None
    winning_date: Optional[str] = None
    acceptance_date: Optional[str] = None
    first_payment_date: Optional[str] = None
    actual_payment_amount: Optional[float] = None
    notes: Optional[str] = None

    @validator("downstream_contract_amount")
    def validate_downstream_amount(cls, v):
        if v <= 0:
            raise ValueError("downstream_contract_amount must be positive")
        return v


class ProjectCreate(ProjectBase):
    pass


class ProjectRead(ProjectBase):
    id: int
    project_code: str
    gross_margin: Optional[float] = None


# Contract schemas
class ContractBase(BaseModel):
    contract_code: str
    contract_name: str
    project_id: int
    contract_direction: str = Field(..., pattern="^(Downstream|Upstream)$")
    contract_status: str = Field(..., pattern="^(Draft|Signing|Effective|Terminated)$")
    counterparty_id: Optional[int] = None
    contract_amount: float
    signing_date: Optional[str] = None
    contract_file_url: Optional[str] = None
    notes: Optional[str] = None


class ContractCreate(ContractBase):
    pass


class ContractRead(ContractBase):
    id: int


# Follow-up schemas
class FollowUpBase(BaseModel):
    terminal_customer_id: int
    opportunity_id: Optional[int] = None
    project_id: Optional[int] = None
    follow_up_date: str
    follow_up_method: str = Field(..., pattern="^(Phone|Visit|WeChat|Email|Meeting)$")
    follow_up_content: str
    follow_up_conclusion: str = Field(
        ...,
        pattern="^(Progressing Well|Needs Support|Customer Hesitant|Pause Progress|Lost Deal)$",
    )
    next_action: Optional[str] = None
    next_follow_up_date: Optional[str] = None
    follower_id: int

    @validator("opportunity_id", "project_id")
    def validate_xor(cls, v, values):
        opportunity_id = values.get("opportunity_id")
        project_id = values.get("project_id")
        if opportunity_id is None and project_id is None:
            raise ValueError("Either opportunity_id or project_id must be provided")
        if opportunity_id is not None and project_id is not None:
            raise ValueError("Only one of opportunity_id or project_id can be provided")
        return v


class FollowUpCreate(FollowUpBase):
    pass


class FollowUpRead(FollowUpBase):
    id: int
    system_created_at: str


# Product schemas
class ProductBase(BaseModel):
    product_name: str
    product_type: str = Field(
        ...,
        pattern="^(Endpoint Security|Data Backup|Network Security|Maintenance Service \(SVC\)|Other)$",
    )
    brand_manufacturer: str
    is_active: bool = True
    notes: Optional[str] = None


class ProductCreate(ProductBase):
    pass


class ProductRead(ProductBase):
    id: int
    product_code: str


# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})

    # Convert user_id to string for JWT compliance
    if "sub" in to_encode and isinstance(to_encode["sub"], int):
        to_encode["sub"] = str(to_encode["sub"])

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict):
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = data.copy()
    to_encode.update({"exp": expire, "jti": secrets.token_urlsafe(32)})

    # Convert user_id to string for JWT compliance
    if "sub" in to_encode and isinstance(to_encode["sub"], int):
        to_encode["sub"] = str(to_encode["sub"])

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_user(email: str, password: str):
    for user in db["users"].values():
        if user["email"] == email:
            if verify_password(password, user["hashed_password"]):
                return user
    return None


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        role: str = payload.get("role")
        if user_id_str is None or role is None:
            raise credentials_exception

        # Convert user_id back to integer for database lookup
        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            raise credentials_exception

        token_data = TokenData(user_id=user_id, role=role)
    except JWTError:
        raise credentials_exception

    if token in db["blacklisted_tokens"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db["users"].get(token_data.user_id)
    if user is None:
        raise credentials_exception
    return user


def check_admin_access(current_user: dict):
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )


def check_sales_access(current_user: dict, resource_owner_id: int):
    if (
        current_user["role"] not in ["admin", "business"]
        and current_user["id"] != resource_owner_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )


def check_business_access(current_user: dict):
    if current_user["role"] not in ["admin", "business"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Business access required"
        )


def check_finance_access(current_user: dict):
    if current_user["role"] not in ["admin", "finance"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Finance access required"
        )


# Auto-numbering functions
def generate_customer_code():
    year_month = datetime.now().strftime("%Y%m")
    count = len(db["customers"]) + 1
    return f"CUS-{year_month}-{count:03d}"


def generate_channel_code():
    year_month = datetime.now().strftime("%Y%m")
    count = len(db["channels"]) + 1
    return f"CH-{year_month}-{count:03d}"


def generate_opportunity_code():
    year_month = datetime.now().strftime("%Y%m")
    count = len(db["opportunities"]) + 1
    return f"OPP-{year_month}-{count:03d}"


def generate_project_code(is_renewal=False):
    year_month = datetime.now().strftime("%Y%m")
    count = len(db["projects"]) + 1
    suffix = "-SVC" if is_renewal else ""
    return f"PRJ-{year_month}-{count:03d}{suffix}"


def generate_product_code():
    count = len(db["products"]) + 1
    return f"PRD-{count:03d}"


# FastAPI app
app = FastAPI(title="CRM System API", description="业财一体CRM系统API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)


@app.middleware("http")
async def add_current_user_to_request(request: Request, call_next):
    # This middleware would normally extract user from token and attach to request
    # For simplicity in this demo, we'll handle it in each endpoint
    response = await call_next(request)
    return response


# Authentication endpoints
@app.post("/auth/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["id"], "role": user["role"]},
        expires_delta=access_token_expires,
    )
    refresh_token = create_refresh_token(data={"sub": user["id"], "role": user["role"]})

    # Store refresh token
    db["refresh_tokens"].add(refresh_token)

    return {"access_token": access_token, "refresh_token": refresh_token}


@app.post("/auth/refresh", response_model=Token)
async def refresh_access_token(refresh_token: str):
    if refresh_token not in db["refresh_tokens"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        role: str = payload.get("role")
        jti: str = payload.get("jti")

        if user_id is None or role is None or jti is None:
            raise JWTError

        # Verify user still exists
        if user_id not in db["users"]:
            raise JWTError

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_id, "role": role}, expires_delta=access_token_expires
        )

        new_refresh_token = create_refresh_token(data={"sub": user_id, "role": role})

        # Replace old refresh token with new one
        db["refresh_tokens"].discard(refresh_token)
        db["refresh_tokens"].add(new_refresh_token)

        return {"access_token": access_token, "refresh_token": new_refresh_token}

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.post("/auth/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    # In a real implementation, you'd blacklist the access token
    # For now, we'll just remove the refresh token
    # Note: This is simplified - in production, you'd need proper token revocation
    pass


# User management endpoints
@app.post("/users", response_model=UserRead)
async def create_user(user: UserCreate, current_user: dict = Depends(get_current_user)):
    check_admin_access(current_user)

    # Check if email already exists
    for existing_user in db["users"].values():
        if existing_user["email"] == user.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    user_id = max(db["users"].keys(), default=0) + 1
    hashed_password = get_password_hash(user.password)

    new_user = {
        "id": user_id,
        "name": user.name,
        "email": user.email,
        "hashed_password": hashed_password,
        "role": user.role,
        "sales_leader_id": user.sales_leader_id,
        "sales_region": user.sales_region,
    }

    db["users"][user_id] = new_user
    return new_user


@app.get("/users", response_model=List[UserRead])
async def list_users(current_user: dict = Depends(get_current_user)):
    check_admin_access(current_user)
    return list(db["users"].values())


@app.get("/users/{user_id}", response_model=UserRead)
async def get_user(user_id: int, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin" and current_user["id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    if user_id not in db["users"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return db["users"][user_id]


@app.put("/users/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int, user: UserBase, current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "admin" and current_user["id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    if user_id not in db["users"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    db["users"][user_id].update(
        {
            "name": user.name,
            "email": user.email,
            "sales_leader_id": user.sales_leader_id,
            "sales_region": user.sales_region,
        }
    )

    return db["users"][user_id]


@app.delete("/users/{user_id}")
async def delete_user(user_id: int, current_user: dict = Depends(get_current_user)):
    check_admin_access(current_user)

    if user_id not in db["users"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    del db["users"][user_id]
    return {"message": "User deleted successfully"}


# Terminal Customers endpoints
@app.post("/customers", response_model=CustomerRead)
async def create_customer(
    customer: CustomerCreate, current_user: dict = Depends(get_current_user)
):
    if current_user["role"] not in ["admin", "sales", "business"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    # Validate customer owner exists
    if customer.customer_owner_id not in db["users"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid customer owner ID"
        )

    customer_id = max(db["customers"].keys(), default=0) + 1
    customer_code = generate_customer_code()

    new_customer = {
        "id": customer_id,
        "customer_code": customer_code,
        **customer.dict(),
    }

    db["customers"][customer_id] = new_customer
    return new_customer


@app.get("/customers", response_model=List[CustomerRead])
async def list_customers(current_user: dict = Depends(get_current_user)):
    if current_user["role"] == "sales":
        # Sales can only see customers they own
        return [
            c
            for c in db["customers"].values()
            if c["customer_owner_id"] == current_user["id"]
        ]
    else:
        return list(db["customers"].values())


@app.get("/customers/{customer_id}", response_model=CustomerRead)
async def get_customer(
    customer_id: int, current_user: dict = Depends(get_current_user)
):
    if customer_id not in db["customers"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )

    customer = db["customers"][customer_id]
    if (
        current_user["role"] == "sales"
        and customer["customer_owner_id"] != current_user["id"]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    return customer


@app.put("/customers/{customer_id}", response_model=CustomerRead)
async def update_customer(
    customer_id: int,
    customer: CustomerBase,
    current_user: dict = Depends(get_current_user),
):
    if customer_id not in db["customers"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )

    existing_customer = db["customers"][customer_id]
    if (
        current_user["role"] == "sales"
        and existing_customer["customer_owner_id"] != current_user["id"]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    # Validate customer owner exists
    if customer.customer_owner_id not in db["users"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid customer owner ID"
        )

    db["customers"][customer_id].update(customer.dict())
    return db["customers"][customer_id]


@app.delete("/customers/{customer_id}")
async def delete_customer(
    customer_id: int, current_user: dict = Depends(get_current_user)
):
    check_business_access(current_user)

    if customer_id not in db["customers"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )

    del db["customers"][customer_id]
    return {"message": "Customer deleted successfully"}


# Channels endpoints
@app.post("/channels", response_model=ChannelRead)
async def create_channel(
    channel: ChannelCreate, current_user: dict = Depends(get_current_user)
):
    check_business_access(current_user)

    channel_id = max(db["channels"].keys(), default=0) + 1
    channel_code = generate_channel_code()

    new_channel = {"id": channel_id, "channel_code": channel_code, **channel.dict()}

    db["channels"][channel_id] = new_channel
    return new_channel


@app.get("/channels", response_model=List[ChannelRead])
async def list_channels(current_user: dict = Depends(get_current_user)):
    return list(db["channels"].values())


@app.get("/channels/{channel_id}", response_model=ChannelRead)
async def get_channel(channel_id: int, current_user: dict = Depends(get_current_user)):
    if channel_id not in db["channels"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found"
        )

    return db["channels"][channel_id]


@app.put("/channels/{channel_id}", response_model=ChannelRead)
async def update_channel(
    channel_id: int,
    channel: ChannelBase,
    current_user: dict = Depends(get_current_user),
):
    check_business_access(current_user)

    if channel_id not in db["channels"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found"
        )

    db["channels"][channel_id].update(channel.dict())
    return db["channels"][channel_id]


@app.delete("/channels/{channel_id}")
async def delete_channel(
    channel_id: int, current_user: dict = Depends(get_current_user)
):
    check_business_access(current_user)

    if channel_id not in db["channels"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found"
        )

    del db["channels"][channel_id]
    return {"message": "Channel deleted successfully"}


# Opportunities endpoints
@app.post("/opportunities", response_model=OpportunityRead)
async def create_opportunity(
    opportunity: OpportunityCreate, current_user: dict = Depends(get_current_user)
):
    if current_user["role"] not in ["admin", "sales", "business"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    # Validate terminal customer exists
    if opportunity.terminal_customer_id not in db["customers"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid terminal customer ID",
        )

    # Validate sales owner exists
    if opportunity.sales_owner_id not in db["users"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid sales owner ID"
        )

    # Validate channel if provided
    if opportunity.channel_id and opportunity.channel_id not in db["channels"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid channel ID"
        )

    opportunity_id = max(db["opportunities"].keys(), default=0) + 1
    opportunity_code = generate_opportunity_code()

    new_opportunity = {
        "id": opportunity_id,
        "opportunity_code": opportunity_code,
        "created_at": datetime.now().isoformat(),
        **opportunity.dict(),
    }

    db["opportunities"][opportunity_id] = new_opportunity
    return new_opportunity


@app.get("/opportunities", response_model=List[OpportunityRead])
async def list_opportunities(current_user: dict = Depends(get_current_user)):
    if current_user["role"] == "sales":
        # Sales can only see opportunities they own
        return [
            o
            for o in db["opportunities"].values()
            if o["sales_owner_id"] == current_user["id"]
        ]
    else:
        return list(db["opportunities"].values())


@app.get("/opportunities/{opportunity_id}", response_model=OpportunityRead)
async def get_opportunity(
    opportunity_id: int, current_user: dict = Depends(get_current_user)
):
    if opportunity_id not in db["opportunities"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found"
        )

    opportunity = db["opportunities"][opportunity_id]
    if (
        current_user["role"] == "sales"
        and opportunity["sales_owner_id"] != current_user["id"]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    return opportunity


@app.put("/opportunities/{opportunity_id}", response_model=OpportunityRead)
async def update_opportunity(
    opportunity_id: int,
    opportunity: OpportunityBase,
    current_user: dict = Depends(get_current_user),
):
    if opportunity_id not in db["opportunities"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found"
        )

    existing_opportunity = db["opportunities"][opportunity_id]
    if (
        current_user["role"] == "sales"
        and existing_opportunity["sales_owner_id"] != current_user["id"]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    # Validate terminal customer exists
    if opportunity.terminal_customer_id not in db["customers"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid terminal customer ID",
        )

    # Validate sales owner exists
    if opportunity.sales_owner_id not in db["users"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid sales owner ID"
        )

    # Validate channel if provided
    if opportunity.channel_id and opportunity.channel_id not in db["channels"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid channel ID"
        )

    db["opportunities"][opportunity_id].update(opportunity.dict())
    return db["opportunities"][opportunity_id]


@app.delete("/opportunities/{opportunity_id}")
async def delete_opportunity(
    opportunity_id: int, current_user: dict = Depends(get_current_user)
):
    check_business_access(current_user)

    if opportunity_id not in db["opportunities"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found"
        )

    del db["opportunities"][opportunity_id]
    return {"message": "Opportunity deleted successfully"}


# Projects endpoints
@app.post("/projects", response_model=ProjectRead)
async def create_project(
    project: ProjectCreate, current_user: dict = Depends(get_current_user)
):
    if current_user["role"] not in ["admin", "sales", "business"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    # Validate terminal customer exists
    if project.terminal_customer_id not in db["customers"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid terminal customer ID",
        )

    # Validate sales owner exists
    if project.sales_owner_id not in db["users"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid sales owner ID"
        )

    # Validate channel if provided
    if project.channel_id and project.channel_id not in db["channels"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid channel ID"
        )

    # Validate source opportunity if provided
    if (
        project.source_opportunity_id
        and project.source_opportunity_id not in db["opportunities"]
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid source opportunity ID",
        )

    project_id = max(db["projects"].keys(), default=0) + 1
    # Check if this is a renewal project (you might want to add more logic here)
    is_renewal = "Renewal" in project.business_type
    project_code = generate_project_code(is_renewal=is_renewal)

    # Calculate gross margin
    gross_margin = project.downstream_contract_amount - (
        project.upstream_procurement_amount or 0
    )

    new_project = {
        "id": project_id,
        "project_code": project_code,
        "gross_margin": gross_margin,
        **project.dict(),
    }

    db["projects"][project_id] = new_project
    return new_project


@app.get("/projects", response_model=List[ProjectRead])
async def list_projects(current_user: dict = Depends(get_current_user)):
    if current_user["role"] == "sales":
        # Sales can only see projects they own
        return [
            p
            for p in db["projects"].values()
            if p["sales_owner_id"] == current_user["id"]
        ]
    else:
        return list(db["projects"].values())


@app.get("/projects/{project_id}", response_model=ProjectRead)
async def get_project(project_id: int, current_user: dict = Depends(get_current_user)):
    if project_id not in db["projects"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    project = db["projects"][project_id]
    if (
        current_user["role"] == "sales"
        and project["sales_owner_id"] != current_user["id"]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    return project


@app.put("/projects/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: int,
    project: ProjectBase,
    current_user: dict = Depends(get_current_user),
):
    if project_id not in db["projects"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    existing_project = db["projects"][project_id]
    if (
        current_user["role"] == "sales"
        and existing_project["sales_owner_id"] != current_user["id"]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    # Validate terminal customer exists
    if project.terminal_customer_id not in db["customers"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid terminal customer ID",
        )

    # Validate sales owner exists
    if project.sales_owner_id not in db["users"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid sales owner ID"
        )

    # Validate channel if provided
    if project.channel_id and project.channel_id not in db["channels"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid channel ID"
        )

    # Validate source opportunity if provided
    if (
        project.source_opportunity_id
        and project.source_opportunity_id not in db["opportunities"]
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid source opportunity ID",
        )

    # Recalculate gross margin
    gross_margin = project.downstream_contract_amount - (
        project.upstream_procurement_amount or 0
    )

    db["projects"][project_id].update(project.dict())
    db["projects"][project_id]["gross_margin"] = gross_margin

    return db["projects"][project_id]


@app.delete("/projects/{project_id}")
async def delete_project(
    project_id: int, current_user: dict = Depends(get_current_user)
):
    check_business_access(current_user)

    if project_id not in db["projects"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    del db["projects"][project_id]
    return {"message": "Project deleted successfully"}


# Contracts endpoints
@app.post("/contracts", response_model=ContractRead)
async def create_contract(
    contract: ContractCreate, current_user: dict = Depends(get_current_user)
):
    check_business_access(current_user)

    # Validate project exists
    if contract.project_id not in db["projects"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid project ID"
        )

    # Validate counterparty for downstream contracts
    if contract.contract_direction == "Downstream" and contract.counterparty_id:
        if contract.counterparty_id not in db["channels"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid counterparty ID for downstream contract",
            )

    # Upstream contracts should not have counterparty_id
    if contract.contract_direction == "Upstream" and contract.counterparty_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upstream contracts should not have counterparty_id",
        )

    contract_id = max(db["contracts"].keys(), default=0) + 1

    new_contract = {"id": contract_id, **contract.dict()}

    db["contracts"][contract_id] = new_contract
    return new_contract


@app.get("/contracts", response_model=List[ContractRead])
async def list_contracts(current_user: dict = Depends(get_current_user)):
    return list(db["contracts"].values())


@app.get("/contracts/{contract_id}", response_model=ContractRead)
async def get_contract(
    contract_id: int, current_user: dict = Depends(get_current_user)
):
    if contract_id not in db["contracts"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found"
        )

    return db["contracts"][contract_id]


@app.put("/contracts/{contract_id}", response_model=ContractRead)
async def update_contract(
    contract_id: int,
    contract: ContractBase,
    current_user: dict = Depends(get_current_user),
):
    check_business_access(current_user)

    if contract_id not in db["contracts"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found"
        )

    # Validate project exists
    if contract.project_id not in db["projects"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid project ID"
        )

    # Validate counterparty for downstream contracts
    if contract.contract_direction == "Downstream" and contract.counterparty_id:
        if contract.counterparty_id not in db["channels"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid counterparty ID for downstream contract",
            )

    # Upstream contracts should not have counterparty_id
    if contract.contract_direction == "Upstream" and contract.counterparty_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upstream contracts should not have counterparty_id",
        )

    db["contracts"][contract_id].update(contract.dict())
    return db["contracts"][contract_id]


@app.delete("/contracts/{contract_id}")
async def delete_contract(
    contract_id: int, current_user: dict = Depends(get_current_user)
):
    check_business_access(current_user)

    if contract_id not in db["contracts"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found"
        )

    del db["contracts"][contract_id]
    return {"message": "Contract deleted successfully"}


# Follow-ups endpoints
@app.post("/follow-ups", response_model=FollowUpRead)
async def create_follow_up(
    follow_up: FollowUpCreate, current_user: dict = Depends(get_current_user)
):
    if current_user["role"] not in ["admin", "sales", "business"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    # Validate terminal customer exists
    if follow_up.terminal_customer_id not in db["customers"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid terminal customer ID",
        )

    # Validate follower exists
    if follow_up.follower_id not in db["users"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid follower ID"
        )

    # Validate opportunity if provided
    if follow_up.opportunity_id and follow_up.opportunity_id not in db["opportunities"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid opportunity ID"
        )

    # Validate project if provided
    if follow_up.project_id and follow_up.project_id not in db["projects"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid project ID"
        )

    # XOR validation (already done by Pydantic validator)

    follow_up_id = max(db["followups"].keys(), default=0) + 1

    new_follow_up = {
        "id": follow_up_id,
        "system_created_at": datetime.now().isoformat(),
        **follow_up.dict(),
    }

    db["followups"][follow_up_id] = new_follow_up
    return new_follow_up


@app.get("/follow-ups", response_model=List[FollowUpRead])
async def list_follow_ups(current_user: dict = Depends(get_current_user)):
    if current_user["role"] == "sales":
        # Sales can only see follow-ups they created
        return [
            f
            for f in db["followups"].values()
            if f["follower_id"] == current_user["id"]
        ]
    else:
        return list(db["followups"].values())


@app.get("/follow-ups/{follow_up_id}", response_model=FollowUpRead)
async def get_follow_up(
    follow_up_id: int, current_user: dict = Depends(get_current_user)
):
    if follow_up_id not in db["followups"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Follow-up not found"
        )

    follow_up = db["followups"][follow_up_id]
    if (
        current_user["role"] == "sales"
        and follow_up["follower_id"] != current_user["id"]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    return follow_up


@app.put("/follow-ups/{follow_up_id}", response_model=FollowUpRead)
async def update_follow_up(
    follow_up_id: int,
    follow_up: FollowUpBase,
    current_user: dict = Depends(get_current_user),
):
    if follow_up_id not in db["followups"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Follow-up not found"
        )

    existing_follow_up = db["followups"][follow_up_id]
    if (
        current_user["role"] == "sales"
        and existing_follow_up["follower_id"] != current_user["id"]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    # Validate terminal customer exists
    if follow_up.terminal_customer_id not in db["customers"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid terminal customer ID",
        )

    # Validate follower exists
    if follow_up.follower_id not in db["users"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid follower ID"
        )

    # Validate opportunity if provided
    if follow_up.opportunity_id and follow_up.opportunity_id not in db["opportunities"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid opportunity ID"
        )

    # Validate project if provided
    if follow_up.project_id and follow_up.project_id not in db["projects"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid project ID"
        )

    # XOR validation (already done by Pydantic validator)

    db["followups"][follow_up_id].update(follow_up.dict())
    return db["followups"][follow_up_id]


@app.delete("/follow-ups/{follow_up_id}")
async def delete_follow_up(
    follow_up_id: int, current_user: dict = Depends(get_current_user)
):
    check_business_access(current_user)

    if follow_up_id not in db["followups"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Follow-up not found"
        )

    del db["followups"][follow_up_id]
    return {"message": "Follow-up deleted successfully"}


# Products endpoints
@app.post("/products", response_model=ProductRead)
async def create_product(
    product: ProductCreate, current_user: dict = Depends(get_current_user)
):
    check_business_access(current_user)

    product_id = max(db["products"].keys(), default=0) + 1
    product_code = generate_product_code()

    new_product = {"id": product_id, "product_code": product_code, **product.dict()}

    db["products"][product_id] = new_product
    return new_product


@app.get("/products", response_model=List[ProductRead])
async def list_products(current_user: dict = Depends(get_current_user)):
    return list(db["products"].values())


@app.get("/products/{product_id}", response_model=ProductRead)
async def get_product(product_id: int, current_user: dict = Depends(get_current_user)):
    if product_id not in db["products"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    return db["products"][product_id]


@app.put("/products/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: int,
    product: ProductBase,
    current_user: dict = Depends(get_current_user),
):
    check_business_access(current_user)

    if product_id not in db["products"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    db["products"][product_id].update(product.dict())
    return db["products"][product_id]


@app.delete("/products/{product_id}")
async def delete_product(
    product_id: int, current_user: dict = Depends(get_current_user)
):
    check_business_access(current_user)

    if product_id not in db["products"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    del db["products"][product_id]
    return {"message": "Product deleted successfully"}


# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
