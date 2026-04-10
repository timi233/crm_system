from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, validator, ConfigDict
from typing import List, Optional, Any
from datetime import datetime, timedelta, date
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import os
from dotenv import load_dotenv

from app.database import get_db
from app.models.user import User
from app.models.customer import TerminalCustomer
from app.models.channel import Channel
from app.models.opportunity import Opportunity
from app.models.project import Project
from app.models.contract import Contract
from app.models.followup import FollowUp
from app.models.product import Product
from app.models.dict_item import DictItem
from app.models.lead import Lead
from app.models.contract import Contract, ContractProduct, PaymentPlan
from app.models.operation_log import OperationLog
from app.models.nine_a import NineA
from app.models.notification import Notification
from app.models.user_notification_read import UserNotificationRead
from app.models.alert_rule import AlertRule
from app.models.sales_target import SalesTarget
from app.services.feishu_service import feishu_service
from app.services.auto_number_service import generate_code
from app.services.alert_service import AlertService
from app.services.operation_log_service import (
    log_create,
    log_update,
    log_delete,
    log_convert,
    log_stage_change,
    get_logs_by_entity,
    get_logs_by_user,
)
from app.services.dispatch_integration_service import (
    DispatchIntegrationService,
    DispatchIntegrationError,
)

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_jwt_key = os.environ.get("JWT_SECRET_KEY")
if not _jwt_key:
    import warnings

    warnings.warn(
        "JWT_SECRET_KEY未设置！请在.env文件中配置JWT_SECRET_KEY。"
        "生产环境必须使用强密钥。",
        UserWarning,
    )
    _jwt_key = "dev-only-insecure-key-do-not-use-in-production"
SECRET_KEY: str = _jwt_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

app = FastAPI(title="普悦销管系统 API", description="普悦销管系统后端接口")

# CORS配置 - 从环境变量读取允许的来源
ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:3002,http://127.0.0.1:3002",  # 默认只允许前端开发服务器
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)


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
    if "sub" in to_encode and isinstance(to_encode["sub"], int):
        to_encode["sub"] = str(to_encode["sub"])
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
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
        user_id = int(user_id_str)
    except (JWTError, ValueError, TypeError):
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return {"id": user.id, "email": user.email, "role": user.role, "name": user.name}


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str = Field(..., pattern="^(admin|sales|business|finance)$")
    sales_leader_id: Optional[int] = None
    sales_region: Optional[str] = None
    sales_product_line: Optional[str] = None


class UserRead(BaseModel):
    id: int
    name: str
    email: str
    role: str
    sales_leader_id: Optional[int] = None
    sales_region: Optional[str] = None
    sales_product_line: Optional[str] = None

    class Config:
        from_attributes = True


class CustomerBase(BaseModel):
    customer_name: str
    credit_code: str
    customer_industry: str
    customer_region: str
    customer_owner_id: int
    channel_id: Optional[int] = None
    main_contact: Optional[str] = None
    phone: Optional[str] = None
    customer_status: str = "Active"
    maintenance_expiry: Optional[str] = None
    notes: Optional[str] = None


class CustomerCreate(CustomerBase):
    pass


class CustomerRead(CustomerBase):
    id: int
    customer_code: str
    customer_owner_name: Optional[str] = None
    channel_name: Optional[str] = None

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    product_name: str
    product_type: str
    brand_manufacturer: str
    is_active: bool = True
    notes: Optional[str] = None


class ProductCreate(ProductBase):
    pass


class ProductRead(ProductBase):
    id: int
    product_code: str

    class Config:
        from_attributes = True


class OpportunityBase(BaseModel):
    opportunity_name: str
    terminal_customer_id: int
    opportunity_source: str
    opportunity_stage: str
    lead_grade: str
    expected_contract_amount: float
    expected_close_date: Optional[str] = None
    sales_owner_id: int
    channel_id: Optional[int] = None
    vendor_registration_status: Optional[str] = None
    vendor_discount: Optional[float] = None
    loss_reason: Optional[str] = None
    product_ids: Optional[List[int]] = None


class OpportunityCreate(OpportunityBase):
    pass


class OpportunityRead(OpportunityBase):
    id: int
    opportunity_code: str
    project_id: Optional[int] = None
    created_at: Optional[date] = None
    terminal_customer_name: Optional[str] = None
    sales_owner_name: Optional[str] = None
    channel_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OpportunityUpdate(BaseModel):
    opportunity_name: Optional[str] = None
    terminal_customer_id: Optional[int] = None
    opportunity_source: Optional[str] = None
    opportunity_stage: Optional[str] = None
    lead_grade: Optional[str] = None
    expected_contract_amount: Optional[float] = None
    expected_close_date: Optional[str] = None
    sales_owner_id: Optional[int] = None
    channel_id: Optional[int] = None
    vendor_registration_status: Optional[str] = None
    vendor_discount: Optional[float] = None
    loss_reason: Optional[str] = None
    product_ids: Optional[List[int]] = None
    project_id: Optional[int] = None


class ProjectBase(BaseModel):
    project_name: str
    terminal_customer_id: int
    sales_owner_id: int
    business_type: str
    project_status: str
    downstream_contract_amount: float
    upstream_procurement_amount: Optional[float] = None
    direct_project_investment: Optional[float] = None
    additional_investment: Optional[float] = None
    winning_date: Optional[str] = None
    acceptance_date: Optional[str] = None
    first_payment_date: Optional[str] = None
    actual_payment_amount: Optional[float] = None
    notes: Optional[str] = None
    product_ids: Optional[List[int]] = None
    channel_id: Optional[int] = None
    source_opportunity_id: Optional[int] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectRead(ProjectBase):
    id: int
    project_code: str
    gross_margin: Optional[float] = None
    terminal_customer_name: Optional[str] = None
    sales_owner_name: Optional[str] = None

    class Config:
        from_attributes = True


class ProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    terminal_customer_id: Optional[int] = None
    sales_owner_id: Optional[int] = None
    business_type: Optional[str] = None
    project_status: Optional[str] = None
    downstream_contract_amount: Optional[float] = None
    upstream_procurement_amount: Optional[float] = None
    direct_project_investment: Optional[float] = None
    additional_investment: Optional[float] = None
    winning_date: Optional[str] = None
    acceptance_date: Optional[str] = None
    first_payment_date: Optional[str] = None
    actual_payment_amount: Optional[float] = None
    notes: Optional[str] = None
    product_ids: Optional[List[int]] = None
    channel_id: Optional[int] = None
    source_opportunity_id: Optional[int] = None
    gross_margin: Optional[float] = None


class LeadBase(BaseModel):
    lead_name: str
    terminal_customer_id: int
    lead_stage: str = "初步接触"
    lead_source: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    estimated_budget: Optional[float] = None
    has_confirmed_requirement: bool = False
    has_confirmed_budget: bool = False
    sales_owner_id: int
    notes: Optional[str] = None


class LeadCreate(LeadBase):
    pass


class LeadRead(BaseModel):
    id: int
    lead_code: str
    lead_name: str
    terminal_customer_id: int
    lead_stage: str
    sales_owner_id: int
    created_at: Optional[date] = None

    model_config = ConfigDict(from_attributes=True)


class LeadUpdate(BaseModel):
    lead_name: Optional[str] = None
    terminal_customer_id: Optional[int] = None
    lead_stage: Optional[str] = None
    lead_source: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    estimated_budget: Optional[float] = None
    has_confirmed_requirement: Optional[bool] = None
    has_confirmed_budget: Optional[bool] = None
    sales_owner_id: Optional[int] = None
    notes: Optional[str] = None


class LeadConvertRequest(BaseModel):
    opportunity_name: str
    expected_contract_amount: float
    lead_grade: str = "B"
    opportunity_source: Optional[str] = None


# ==================== 合同 API Schema ====================


class ContractProductCreate(BaseModel):
    product_id: int
    product_name: str
    quantity: float = 1
    unit_price: float = 0
    discount: float = 1.0
    amount: float = 0
    notes: Optional[str] = None


class ContractProductRead(ContractProductCreate):
    id: int
    contract_id: int

    class Config:
        from_attributes = True


class PaymentPlanCreate(BaseModel):
    plan_stage: str
    plan_amount: float
    plan_date: Optional[str] = None
    actual_amount: Optional[float] = 0
    actual_date: Optional[str] = None
    payment_status: str = "pending"
    notes: Optional[str] = None


class PaymentPlanRead(PaymentPlanCreate):
    id: int
    contract_id: int
    plan_date: Optional[date] = None
    actual_date: Optional[date] = None

    class Config:
        from_attributes = True


class ContractBase(BaseModel):
    contract_name: str
    project_id: int
    contract_direction: str = "Downstream"
    contract_status: str = "draft"
    terminal_customer_id: Optional[int] = None
    channel_id: Optional[int] = None
    contract_amount: float = 0
    signing_date: Optional[str] = None
    effective_date: Optional[str] = None
    expiry_date: Optional[str] = None
    contract_file_url: Optional[str] = None
    notes: Optional[str] = None


class ContractCreate(ContractBase):
    products: Optional[List[ContractProductCreate]] = []
    payment_plans: Optional[List[PaymentPlanCreate]] = []


class ContractRead(ContractBase):
    id: int
    contract_code: str
    signing_date: Optional[date] = None
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    created_at: Optional[date] = None
    updated_at: Optional[date] = None
    products: List[ContractProductRead] = []
    payment_plans: List[PaymentPlanRead] = []
    project_name: Optional[str] = None
    terminal_customer_name: Optional[str] = None
    channel_name: Optional[str] = None

    class Config:
        from_attributes = True


class ContractUpdate(BaseModel):
    contract_name: Optional[str] = None
    contract_status: Optional[str] = None
    terminal_customer_id: Optional[int] = None
    channel_id: Optional[int] = None
    contract_amount: Optional[float] = None
    signing_date: Optional[str] = None
    effective_date: Optional[str] = None
    expiry_date: Optional[str] = None
    contract_file_url: Optional[str] = None
    notes: Optional[str] = None
    products: Optional[List[ContractProductCreate]] = None
    payment_plans: Optional[List[PaymentPlanCreate]] = None


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/auth/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.id, "role": user.role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}


class FeishuLoginRequest(BaseModel):
    code: str


class FeishuLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


@app.get("/auth/feishu/url")
async def get_feishu_oauth_url():
    return {"url": feishu_service.get_oauth_url()}


@app.post("/auth/feishu/login", response_model=FeishuLoginResponse)
async def feishu_login(request: FeishuLoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        feishu_user = await feishu_service.get_user_by_code(request.code)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    result = await db.execute(
        select(User).where(User.feishu_id == feishu_user["open_id"])
    )
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            feishu_id=feishu_user["open_id"],
            name=feishu_user["name"],
            email=feishu_user.get("email"),
            phone=feishu_user.get("mobile"),
            avatar=feishu_user.get("avatar_url"),
            role="sales",
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        user.name = feishu_user["name"]
        if feishu_user.get("mobile"):
            user.phone = feishu_user["mobile"]
        if feishu_user.get("email"):
            user.email = feishu_user["email"]
        if feishu_user.get("avatar_url"):
            user.avatar = feishu_user["avatar_url"]
        await db.commit()
        await db.refresh(user)

    access_token = create_access_token(
        data={"sub": user.id, "role": user.role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "avatar": user.avatar,
        },
    }


@app.get("/users", response_model=List[UserRead])
async def list_users(
    current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users


@app.post("/users", response_model=UserRead)
async def create_user(
    user: UserCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can create users")

    existing = await db.execute(select(User).where(User.email == user.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        name=user.name,
        email=user.email,
        hashed_password=get_password_hash(user.password),
        role=user.role,
        sales_leader_id=user.sales_leader_id,
        sales_region=user.sales_region,
        sales_product_line=user.sales_product_line,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = Field(None, pattern="^(admin|sales|business|finance)$")
    sales_leader_id: Optional[int] = None
    sales_region: Optional[str] = None
    sales_product_line: Optional[str] = None
    is_active: Optional[bool] = None


@app.put("/users/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    user: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can update users")

    result = await db.execute(select(User).where(User.id == user_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")

    if user.name is not None:
        existing.name = user.name
    if user.email is not None:
        existing.email = user.email
    if user.role is not None:
        existing.role = user.role
    if user.sales_leader_id is not None:
        existing.sales_leader_id = user.sales_leader_id
    if user.sales_region is not None:
        existing.sales_region = user.sales_region
    if user.sales_product_line is not None:
        existing.sales_product_line = user.sales_product_line
    if user.is_active is not None:
        existing.is_active = user.is_active

    await db.commit()
    await db.refresh(existing)
    return existing


@app.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can delete users")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(user)
    await db.commit()
    return {"message": "User deleted successfully"}


@app.get("/customers", response_model=List[CustomerRead])
async def list_customers(
    current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(TerminalCustomer).options(
            selectinload(TerminalCustomer.owner), selectinload(TerminalCustomer.channel)
        )
    )
    customers = result.scalars().all()
    return [
        {
            **c.__dict__,
            "customer_owner_name": c.owner.name if c.owner else None,
            "channel_name": c.channel.company_name if c.channel else None,
        }
        for c in customers
    ]


@app.get("/customers/check-credit-code")
async def check_credit_code(
    credit_code: str,
    exclude_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(TerminalCustomer).where(TerminalCustomer.credit_code == credit_code)
    if exclude_id:
        query = query.where(TerminalCustomer.id != exclude_id)
    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    return {"exists": existing is not None}


@app.post("/customers", response_model=CustomerRead)
async def create_customer(
    customer: CustomerCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(TerminalCustomer).where(
            TerminalCustomer.credit_code == customer.credit_code
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该统一社会信用代码已存在")

    customer_code = await generate_code(db, "customer")

    new_customer = TerminalCustomer(
        customer_code=customer_code,
        customer_name=customer.customer_name,
        credit_code=customer.credit_code,
        customer_industry=customer.customer_industry,
        customer_region=customer.customer_region,
        customer_owner_id=customer.customer_owner_id,
        channel_id=customer.channel_id,
        main_contact=customer.main_contact,
        phone=customer.phone,
        customer_status=customer.customer_status,
        maintenance_expiry=customer.maintenance_expiry,
        notes=customer.notes,
    )
    db.add(new_customer)
    await db.flush()
    await db.refresh(new_customer)

    await log_create(
        db=db,
        user_id=current_user["id"],
        user_name=current_user["name"],
        entity_type="customer",
        entity_id=new_customer.id,
        entity_code=new_customer.customer_code,
        entity_name=new_customer.customer_name,
        description=f"创建客户: {new_customer.customer_name}",
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    await db.refresh(new_customer)
    await db.refresh(new_customer, ["owner", "channel"])
    return {
        **new_customer.__dict__,
        "customer_owner_name": new_customer.owner.name if new_customer.owner else None,
        "channel_name": new_customer.channel.company_name
        if new_customer.channel
        else None,
    }


@app.put("/customers/{customer_id}", response_model=CustomerRead)
async def update_customer(
    customer_id: int,
    customer: CustomerCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TerminalCustomer).where(TerminalCustomer.id == customer_id)
    )
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Customer not found")

    old_data = {
        "customer_name": existing.customer_name,
        "credit_code": existing.credit_code,
        "customer_industry": existing.customer_industry,
        "customer_region": existing.customer_region,
        "customer_status": existing.customer_status,
    }

    if customer.credit_code != existing.credit_code:
        duplicate = await db.execute(
            select(TerminalCustomer).where(
                TerminalCustomer.credit_code == customer.credit_code
            )
        )
        if duplicate.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="该统一社会信用代码已存在")

    existing.customer_name = customer.customer_name
    existing.credit_code = customer.credit_code
    existing.customer_industry = customer.customer_industry
    existing.customer_region = customer.customer_region
    existing.customer_owner_id = customer.customer_owner_id
    existing.channel_id = customer.channel_id
    existing.main_contact = customer.main_contact
    existing.phone = customer.phone
    existing.customer_status = customer.customer_status
    existing.maintenance_expiry = customer.maintenance_expiry
    existing.notes = customer.notes

    await db.flush()

    await log_update(
        db=db,
        user_id=current_user["id"],
        user_name=current_user["name"],
        entity_type="customer",
        entity_id=existing.id,
        entity_code=existing.customer_code,
        entity_name=existing.customer_name,
        old_value=old_data,
        new_value={
            "customer_name": customer.customer_name,
            "credit_code": customer.credit_code,
            "customer_industry": customer.customer_industry,
            "customer_region": customer.customer_region,
            "customer_status": customer.customer_status,
        },
        description=f"更新客户: {existing.customer_name}",
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    await db.refresh(existing)
    await db.refresh(existing, ["owner", "channel"])
    return {
        **existing.__dict__,
        "customer_owner_name": existing.owner.name if existing.owner else None,
        "channel_name": existing.channel.company_name if existing.channel else None,
    }


@app.delete("/customers/{customer_id}")
async def delete_customer(
    customer_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TerminalCustomer).where(TerminalCustomer.id == customer_id)
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    await log_delete(
        db=db,
        user_id=current_user["id"],
        user_name=current_user["name"],
        entity_type="customer",
        entity_id=customer.id,
        entity_code=customer.customer_code,
        entity_name=customer.customer_name,
        old_value={
            "customer_name": customer.customer_name,
            "credit_code": customer.credit_code,
        },
        description=f"删除客户: {customer.customer_name}",
        ip_address=request.client.host if request.client else None,
    )

    await db.delete(customer)
    await db.commit()
    return {"message": "Customer deleted successfully"}


class CustomerFullView(BaseModel):
    customer: dict
    channel: Optional[dict] = None
    summary: dict
    leads: List[dict]
    opportunities: List[dict]
    projects: List[dict]
    follow_ups: List[dict]
    contracts: List[dict]


@app.get("/customers/{customer_id}/full-view", response_model=CustomerFullView)
async def get_customer_full_view(
    customer_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TerminalCustomer)
        .options(
            selectinload(TerminalCustomer.owner), selectinload(TerminalCustomer.channel)
        )
        .where(TerminalCustomer.id == customer_id)
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    channel_data = None
    if customer.channel:
        channel_data = {
            "id": customer.channel.id,
            "channel_code": customer.channel.channel_code,
            "company_name": customer.channel.company_name,
            "channel_type": customer.channel.channel_type,
            "status": customer.channel.status,
            "main_contact": customer.channel.main_contact,
            "phone": customer.channel.phone,
        }

    leads_result = await db.execute(
        select(Lead, User.name)
        .outerjoin(User, Lead.sales_owner_id == User.id)
        .where(Lead.terminal_customer_id == customer_id)
    )
    leads_rows = leads_result.all()
    leads = []
    for row in leads_rows:
        lead = row[0]
        owner_name = row[1]
        leads.append(
            {
                "id": lead.id,
                "lead_code": lead.lead_code,
                "lead_name": lead.lead_name,
                "lead_stage": lead.lead_stage,
                "lead_source": lead.lead_source,
                "estimated_budget": float(lead.estimated_budget)
                if lead.estimated_budget
                else None,
                "sales_owner_name": owner_name,
                "converted_to_opportunity": lead.converted_to_opportunity,
            }
        )

    opps_result = await db.execute(
        select(Opportunity, User.name, Channel.company_name)
        .outerjoin(User, Opportunity.sales_owner_id == User.id)
        .outerjoin(Channel, Opportunity.channel_id == Channel.id)
        .where(Opportunity.terminal_customer_id == customer_id)
    )
    opps_rows = opps_result.all()
    opportunities = []
    for row in opps_rows:
        opp = row[0]
        owner_name = row[1]
        channel_name = row[2]
        opportunities.append(
            {
                "id": opp.id,
                "opportunity_code": opp.opportunity_code,
                "opportunity_name": opp.opportunity_name,
                "opportunity_stage": opp.opportunity_stage,
                "expected_contract_amount": float(opp.expected_contract_amount)
                if opp.expected_contract_amount
                else None,
                "sales_owner_name": owner_name,
                "channel_name": channel_name,
                "project_id": opp.project_id,
            }
        )

    projects_result = await db.execute(
        select(Project, User.name)
        .outerjoin(User, Project.sales_owner_id == User.id)
        .where(Project.terminal_customer_id == customer_id)
    )
    projects_rows = projects_result.all()
    projects = []
    for row in projects_rows:
        proj = row[0]
        owner_name = row[1]
        projects.append(
            {
                "id": proj.id,
                "project_code": proj.project_code,
                "project_name": proj.project_name,
                "project_status": proj.project_status,
                "business_type": proj.business_type,
                "downstream_contract_amount": float(proj.downstream_contract_amount)
                if proj.downstream_contract_amount
                else None,
                "sales_owner_name": owner_name,
            }
        )

    follow_ups_result = await db.execute(
        select(FollowUp, User.name)
        .outerjoin(User, FollowUp.follower_id == User.id)
        .where(FollowUp.terminal_customer_id == customer_id)
        .order_by(FollowUp.follow_up_date.desc())
        .limit(20)
    )
    fu_rows = follow_ups_result.all()
    follow_ups = []
    for row in fu_rows:
        fu = row[0]
        follower_name = row[1]
        follow_ups.append(
            {
                "id": fu.id,
                "follow_up_date": str(fu.follow_up_date) if fu.follow_up_date else None,
                "follow_up_method": fu.follow_up_method,
                "follow_up_content": fu.follow_up_content,
                "follow_up_conclusion": fu.follow_up_conclusion,
                "follower_name": follower_name,
            }
        )

    contracts_result = await db.execute(
        select(Contract).where(Contract.terminal_customer_id == customer_id)
    )
    contracts_rows = contracts_result.all()
    contracts = []
    for row in contracts_rows:
        c = row[0]
        contracts.append(
            {
                "id": c.id,
                "contract_code": c.contract_code,
                "contract_name": c.contract_name,
                "contract_direction": c.contract_direction,
                "contract_status": c.contract_status,
                "contract_amount": float(c.contract_amount)
                if c.contract_amount
                else None,
                "signing_date": str(c.signing_date) if c.signing_date else None,
            }
        )

    return CustomerFullView(
        customer={
            "id": customer.id,
            "customer_code": customer.customer_code,
            "customer_name": customer.customer_name,
            "credit_code": customer.credit_code,
            "customer_industry": customer.customer_industry,
            "customer_region": customer.customer_region,
            "customer_status": customer.customer_status,
            "main_contact": customer.main_contact,
            "phone": customer.phone,
            "notes": customer.notes,
            "customer_owner_name": customer.owner.name if customer.owner else None,
        },
        channel=channel_data,
        summary={
            "leads_count": len(leads),
            "opportunities_count": len(opportunities),
            "projects_count": len(projects),
            "follow_ups_count": len(follow_ups),
            "contracts_count": len(contracts),
        },
        leads=leads,
        opportunities=opportunities,
        projects=projects,
        follow_ups=follow_ups,
        contracts=contracts,
    )


@app.get("/products", response_model=List[ProductRead])
async def list_products(
    current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Product))
    products = result.scalars().all()
    return products


@app.post("/products", response_model=ProductRead)
async def create_product(
    product: ProductCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count_result = await db.execute(select(Product.id))
    count = len(count_result.scalars().all()) + 1
    product_code = f"PRD-{count:03d}"

    new_product = Product(
        product_code=product_code,
        product_name=product.product_name,
        product_type=product.product_type,
        brand_manufacturer=product.brand_manufacturer,
        is_active=product.is_active,
        notes=product.notes,
    )
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    return new_product


class ProductUpdate(BaseModel):
    product_name: Optional[str] = None
    product_type: Optional[str] = None
    brand_manufacturer: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


@app.put("/products/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: int,
    product: ProductUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")

    if product.product_name is not None:
        existing.product_name = product.product_name
    if product.product_type is not None:
        existing.product_type = product.product_type
    if product.brand_manufacturer is not None:
        existing.brand_manufacturer = product.brand_manufacturer
    if product.is_active is not None:
        existing.is_active = product.is_active
    if product.notes is not None:
        existing.notes = product.notes

    await db.commit()
    await db.refresh(existing)
    return existing


@app.delete("/products/{product_id}")
async def delete_product(
    product_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    await db.delete(product)
    await db.commit()
    return {"message": "Product deleted successfully"}


# ==================== 线索 API ====================

LEAD_STAGE_TRANSITIONS = {
    "初步接触": ["意向沟通"],
    "意向沟通": ["需求挖掘中", "初步接触"],
    "需求挖掘中": ["意向沟通"],
}


@app.get("/leads", response_model=List[LeadRead])
async def list_leads(
    current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Lead))
    leads = result.scalars().all()
    return leads


@app.get("/leads/{lead_id}", response_model=LeadRead)
async def get_lead(
    lead_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@app.post("/leads", response_model=LeadRead)
async def create_lead(
    lead: LeadCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    lead_code = await generate_code(db, "lead")

    new_lead = Lead(
        lead_code=lead_code,
        lead_name=lead.lead_name,
        terminal_customer_id=lead.terminal_customer_id,
        lead_stage=lead.lead_stage,
        lead_source=lead.lead_source,
        contact_person=lead.contact_person,
        contact_phone=lead.contact_phone,
        estimated_budget=lead.estimated_budget,
        has_confirmed_requirement=lead.has_confirmed_requirement,
        has_confirmed_budget=lead.has_confirmed_budget,
        sales_owner_id=lead.sales_owner_id,
        notes=lead.notes,
        created_at=date.today(),
        updated_at=date.today(),
    )
    db.add(new_lead)
    await db.flush()
    await db.refresh(new_lead)

    await log_create(
        db=db,
        user_id=current_user["id"],
        user_name=current_user["name"],
        entity_type="lead",
        entity_id=new_lead.id,
        entity_code=new_lead.lead_code,
        entity_name=new_lead.lead_name,
        description=f"创建线索: {new_lead.lead_name}",
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    return new_lead


@app.put("/leads/{lead_id}", response_model=LeadRead)
async def update_lead(
    lead_id: int,
    lead: LeadUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Lead not found")

    if existing.converted_to_opportunity:
        raise HTTPException(status_code=400, detail="已转商机的线索不能修改")

    old_stage = existing.lead_stage
    update_data = lead.model_dump(exclude_unset=True)

    if "lead_stage" in update_data and update_data["lead_stage"] != existing.lead_stage:
        valid_transitions = LEAD_STAGE_TRANSITIONS.get(existing.lead_stage, [])
        if update_data["lead_stage"] not in valid_transitions:
            raise HTTPException(
                status_code=400,
                detail=f"线索阶段不能从 '{existing.lead_stage}' 直接流转到 '{update_data['lead_stage']}'",
            )

    for field, value in update_data.items():
        setattr(existing, field, value)

    existing.updated_at = date.today()
    await db.flush()

    if "lead_stage" in update_data and update_data["lead_stage"] != old_stage:
        await log_stage_change(
            db=db,
            user_id=current_user["id"],
            user_name=current_user["name"],
            entity_type="lead",
            entity_id=existing.id,
            entity_code=existing.lead_code,
            entity_name=existing.lead_name,
            old_stage=old_stage,
            new_stage=update_data["lead_stage"],
            ip_address=request.client.host if request.client else None,
        )
    else:
        await log_update(
            db=db,
            user_id=current_user["id"],
            user_name=current_user["name"],
            entity_type="lead",
            entity_id=existing.id,
            entity_code=existing.lead_code,
            entity_name=existing.lead_name,
            description=f"更新线索: {existing.lead_name}",
            ip_address=request.client.host if request.client else None,
        )

    await db.commit()
    await db.refresh(existing)
    return existing


@app.delete("/leads/{lead_id}")
async def delete_lead(
    lead_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if lead.converted_to_opportunity:
        raise HTTPException(status_code=400, detail="已转商机的线索不能删除")

    await log_delete(
        db=db,
        user_id=current_user["id"],
        user_name=current_user["name"],
        entity_type="lead",
        entity_id=lead.id,
        entity_code=lead.lead_code,
        entity_name=lead.lead_name,
        description=f"删除线索: {lead.lead_name}",
        ip_address=request.client.host if request.client else None,
    )

    await db.delete(lead)
    await db.commit()
    return {"message": "Lead deleted successfully"}


@app.post("/leads/{lead_id}/convert", response_model=OpportunityRead)
async def convert_lead_to_opportunity(
    lead_id: int,
    convert_request: LeadConvertRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if lead.converted_to_opportunity:
        raise HTTPException(status_code=400, detail="该线索已转换为商机")

    if not lead.has_confirmed_requirement or not lead.has_confirmed_budget:
        raise HTTPException(status_code=400, detail="线索需确认需求和预算后才能转商机")

    opportunity_code = await generate_code(db, "opportunity")

    new_opportunity = Opportunity(
        opportunity_code=opportunity_code,
        opportunity_name=convert_request.opportunity_name,
        terminal_customer_id=lead.terminal_customer_id,
        opportunity_source=convert_request.opportunity_source
        or lead.lead_source
        or "线索转化",
        opportunity_stage="需求方案",
        lead_grade=convert_request.lead_grade,
        expected_contract_amount=convert_request.expected_contract_amount,
        sales_owner_id=lead.sales_owner_id,
        created_at=date.today(),
    )
    db.add(new_opportunity)
    await db.flush()
    await db.refresh(new_opportunity)

    lead.converted_to_opportunity = True
    lead.opportunity_id = new_opportunity.id
    lead.updated_at = date.today()

    await log_convert(
        db=db,
        user_id=current_user["id"],
        user_name=current_user["name"],
        source_type="lead",
        source_id=lead.id,
        source_code=lead.lead_code,
        source_name=lead.lead_name,
        target_type="opportunity",
        target_id=new_opportunity.id,
        target_code=new_opportunity.opportunity_code,
        description=f"线索转商机: {lead.lead_name} → {new_opportunity.opportunity_name}",
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    await db.refresh(new_opportunity)
    return new_opportunity


@app.get("/opportunities", response_model=List[OpportunityRead])
async def list_opportunities(
    current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Opportunity).options(
            selectinload(Opportunity.terminal_customer),
            selectinload(Opportunity.sales_owner),
            selectinload(Opportunity.channel),
        )
    )
    opportunities = result.scalars().all()
    return opportunities


@app.get("/opportunities/{opportunity_id}", response_model=OpportunityRead)
async def get_opportunity(
    opportunity_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Opportunity)
        .where(Opportunity.id == opportunity_id)
        .options(
            selectinload(Opportunity.terminal_customer),
            selectinload(Opportunity.sales_owner),
            selectinload(Opportunity.channel),
        )
    )
    opportunity = result.scalar_one_or_none()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    return {
        **opportunity.__dict__,
        "terminal_customer_name": opportunity.terminal_customer.customer_name
        if opportunity.terminal_customer
        else None,
        "sales_owner_name": opportunity.sales_owner.name
        if opportunity.sales_owner
        else None,
        "channel_name": opportunity.channel.company_name
        if opportunity.channel
        else None,
    }


@app.post("/opportunities", response_model=OpportunityRead)
async def create_opportunity(
    opportunity: OpportunityCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    opportunity_code = await generate_code(db, "opportunity")

    new_opportunity = Opportunity(
        opportunity_code=opportunity_code,
        opportunity_name=opportunity.opportunity_name,
        terminal_customer_id=opportunity.terminal_customer_id,
        opportunity_source=opportunity.opportunity_source,
        opportunity_stage=opportunity.opportunity_stage,
        lead_grade=opportunity.lead_grade,
        expected_contract_amount=opportunity.expected_contract_amount,
        expected_close_date=opportunity.expected_close_date,
        sales_owner_id=opportunity.sales_owner_id,
        channel_id=opportunity.channel_id,
        vendor_registration_status=opportunity.vendor_registration_status,
        vendor_discount=opportunity.vendor_discount,
        loss_reason=opportunity.loss_reason,
        product_ids=opportunity.product_ids,
        created_at=datetime.now().date(),
    )
    db.add(new_opportunity)
    await db.flush()
    await db.refresh(new_opportunity)

    await log_create(
        db=db,
        user_id=current_user["id"],
        user_name=current_user["name"],
        entity_type="opportunity",
        entity_id=new_opportunity.id,
        entity_code=new_opportunity.opportunity_code,
        entity_name=new_opportunity.opportunity_name,
        description=f"创建商机: {new_opportunity.opportunity_name}",
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    return new_opportunity


@app.put("/opportunities/{opportunity_id}", response_model=OpportunityRead)
async def update_opportunity(
    opportunity_id: int,
    opportunity: OpportunityUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Opportunity).where(Opportunity.id == opportunity_id)
    )
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    if existing.opportunity_stage in ["已成交", "已流失"]:
        raise HTTPException(status_code=400, detail="已成交或已流失的商机不能修改")

    old_stage = existing.opportunity_stage
    update_data = opportunity.model_dump(exclude_unset=True)

    if (
        "opportunity_stage" in update_data
        and update_data["opportunity_stage"] != existing.opportunity_stage
    ):
        valid_transitions = OPPORTUNITY_STAGE_TRANSITIONS.get(
            existing.opportunity_stage, []
        )
        if update_data["opportunity_stage"] not in valid_transitions:
            raise HTTPException(
                status_code=400,
                detail=f"商机阶段不能从 '{existing.opportunity_stage}' 直接流转到 '{update_data['opportunity_stage']}'",
            )

        if (
            update_data["opportunity_stage"] == "已流失"
            and not update_data.get("loss_reason")
            and not existing.loss_reason
        ):
            raise HTTPException(status_code=400, detail="转入流失阶段必须填写流失原因")

    for field, value in update_data.items():
        setattr(existing, field, value)

    await db.flush()

    if (
        "opportunity_stage" in update_data
        and update_data["opportunity_stage"] != old_stage
    ):
        await log_stage_change(
            db=db,
            user_id=current_user["id"],
            user_name=current_user["name"],
            entity_type="opportunity",
            entity_id=existing.id,
            entity_code=existing.opportunity_code,
            entity_name=existing.opportunity_name,
            old_stage=old_stage,
            new_stage=update_data["opportunity_stage"],
            ip_address=request.client.host if request.client else None,
        )
    else:
        await log_update(
            db=db,
            user_id=current_user["id"],
            user_name=current_user["name"],
            entity_type="opportunity",
            entity_id=existing.id,
            entity_code=existing.opportunity_code,
            entity_name=existing.opportunity_name,
            description=f"更新商机: {existing.opportunity_name}",
            ip_address=request.client.host if request.client else None,
        )

    await db.commit()
    await db.refresh(existing)
    return existing


@app.delete("/opportunities/{opportunity_id}")
async def delete_opportunity(
    opportunity_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Opportunity).where(Opportunity.id == opportunity_id)
    )
    opportunity = result.scalar_one_or_none()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    await log_delete(
        db=db,
        user_id=current_user["id"],
        user_name=current_user["name"],
        entity_type="opportunity",
        entity_id=opportunity.id,
        entity_code=opportunity.opportunity_code,
        entity_name=opportunity.opportunity_name,
        description=f"删除商机: {opportunity.opportunity_name}",
        ip_address=request.client.host if request.client else None,
    )

    await db.delete(opportunity)
    await db.commit()
    return {"message": "Opportunity deleted successfully"}


# ==================== 9A分析 API ====================


class NineABase(BaseModel):
    key_events: Optional[str] = None
    budget: Optional[float] = None
    decision_chain_influence: Optional[str] = None
    customer_challenges: Optional[str] = None
    customer_needs: Optional[str] = None
    solution_differentiation: Optional[str] = None
    competitors: Optional[str] = None
    buying_method: Optional[str] = None


class NineACreate(NineABase):
    pass


class NineARead(NineABase):
    id: int
    opportunity_id: int

    class Config:
        from_attributes = True


class NineAUpdate(NineABase):
    pass


@app.get("/opportunities/{opportunity_id}/nine-a", response_model=Optional[NineARead])
async def get_nine_a(
    opportunity_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(NineA).where(NineA.opportunity_id == opportunity_id)
    )
    nine_a = result.scalar_one_or_none()
    return nine_a


@app.post("/opportunities/{opportunity_id}/nine-a", response_model=NineARead)
async def create_nine_a(
    opportunity_id: int,
    nine_a_data: NineACreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Opportunity).where(Opportunity.id == opportunity_id)
    )
    opportunity = result.scalar_one_or_none()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    existing = await db.execute(
        select(NineA).where(NineA.opportunity_id == opportunity_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400, detail="9A analysis already exists for this opportunity"
        )

    new_nine_a = NineA(
        opportunity_id=opportunity_id,
        key_events=nine_a_data.key_events,
        budget=nine_a_data.budget,
        decision_chain_influence=nine_a_data.decision_chain_influence,
        customer_challenges=nine_a_data.customer_challenges,
        customer_needs=nine_a_data.customer_needs,
        solution_differentiation=nine_a_data.solution_differentiation,
        competitors=nine_a_data.competitors,
        buying_method=nine_a_data.buying_method,
    )
    db.add(new_nine_a)
    await db.commit()
    await db.refresh(new_nine_a)
    return new_nine_a


@app.put("/opportunities/{opportunity_id}/nine-a", response_model=NineARead)
async def update_nine_a(
    opportunity_id: int,
    nine_a_data: NineAUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(NineA).where(NineA.opportunity_id == opportunity_id)
    )
    nine_a = result.scalar_one_or_none()
    if not nine_a:
        raise HTTPException(status_code=404, detail="9A analysis not found")

    update_data = nine_a_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(nine_a, field, value)

    await db.commit()
    await db.refresh(nine_a)
    return nine_a


OPPORTUNITY_STAGE_TRANSITIONS = {
    "需求方案": ["需求确认", "已流失"],
    "需求确认": ["报价投标", "需求方案", "已流失"],
    "报价投标": ["合同签订", "需求确认", "已流失"],
    "合同签订": ["已成交"],
    "已成交": [],
    "已流失": [],
}


class OpportunityConvertRequest(BaseModel):
    project_name: str
    business_type: str = "New Project"


@app.post("/opportunities/{opportunity_id}/convert", response_model=ProjectRead)
async def convert_opportunity_to_project(
    opportunity_id: int,
    convert_request: OpportunityConvertRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Opportunity).where(Opportunity.id == opportunity_id)
    )
    opportunity = result.scalar_one_or_none()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    if opportunity.opportunity_stage != "合同签订":
        raise HTTPException(status_code=400, detail="商机需在合同签订阶段才能转项目")

    if opportunity.project_id:
        result = await db.execute(
            select(Project).where(Project.id == opportunity.project_id)
        )
        existing_project = result.scalar_one_or_none()
        if existing_project:
            raise HTTPException(status_code=400, detail="该商机已转换为项目")

    project_code = await generate_code(db, "project")

    gross_margin = None
    if opportunity.expected_contract_amount:
        gross_margin = opportunity.expected_contract_amount

    new_project = Project(
        project_code=project_code,
        project_name=convert_request.project_name,
        terminal_customer_id=opportunity.terminal_customer_id,
        sales_owner_id=opportunity.sales_owner_id,
        business_type=convert_request.business_type,
        project_status="执行中",
        downstream_contract_amount=opportunity.expected_contract_amount,
        source_opportunity_id=opportunity.id,
        channel_id=opportunity.channel_id,
        gross_margin=gross_margin,
    )
    db.add(new_project)
    await db.flush()
    await db.refresh(new_project)

    opportunity.project_id = new_project.id
    opportunity.opportunity_stage = "已成交"

    await log_convert(
        db=db,
        user_id=current_user["id"],
        user_name=current_user["name"],
        source_type="opportunity",
        source_id=opportunity.id,
        source_code=opportunity.opportunity_code,
        source_name=opportunity.opportunity_name,
        target_type="project",
        target_id=new_project.id,
        target_code=new_project.project_code,
        description=f"商机转项目: {opportunity.opportunity_name} → {new_project.project_name}",
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    await db.refresh(new_project)
    return new_project


@app.get("/projects", response_model=List[ProjectRead])
async def list_projects(
    current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Project, TerminalCustomer.customer_name, User.name)
        .outerjoin(
            TerminalCustomer, Project.terminal_customer_id == TerminalCustomer.id
        )
        .outerjoin(User, Project.sales_owner_id == User.id)
    )
    rows = result.all()
    projects = []
    for row in rows:
        project = row[0]
        customer_name = row[1] if len(row) > 1 else None
        owner_name = row[2] if len(row) > 2 else None
        project_dict = {
            "id": project.id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "terminal_customer_id": project.terminal_customer_id,
            "sales_owner_id": project.sales_owner_id,
            "business_type": project.business_type,
            "project_status": project.project_status,
            "downstream_contract_amount": project.downstream_contract_amount,
            "upstream_procurement_amount": project.upstream_procurement_amount,
            "direct_project_investment": project.direct_project_investment,
            "additional_investment": project.additional_investment,
            "winning_date": project.winning_date,
            "acceptance_date": project.acceptance_date,
            "first_payment_date": project.first_payment_date,
            "actual_payment_amount": project.actual_payment_amount,
            "notes": project.notes,
            "product_ids": project.product_ids,
            "channel_id": project.channel_id,
            "source_opportunity_id": project.source_opportunity_id,
            "gross_margin": project.gross_margin,
            "terminal_customer_name": customer_name,
            "sales_owner_name": owner_name,
        }
        projects.append(ProjectRead(**project_dict))
    return projects


@app.get("/projects/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Project, TerminalCustomer.customer_name, User.name)
        .where(Project.id == project_id)
        .outerjoin(
            TerminalCustomer, Project.terminal_customer_id == TerminalCustomer.id
        )
        .outerjoin(User, Project.sales_owner_id == User.id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")

    project = row[0]
    customer_name = row[1] if len(row) > 1 else None
    owner_name = row[2] if len(row) > 2 else None

    return ProjectRead(
        id=project.id,
        project_code=project.project_code,
        project_name=project.project_name,
        terminal_customer_id=project.terminal_customer_id,
        sales_owner_id=project.sales_owner_id,
        business_type=project.business_type,
        project_status=project.project_status,
        downstream_contract_amount=project.downstream_contract_amount,
        upstream_procurement_amount=project.upstream_procurement_amount,
        direct_project_investment=project.direct_project_investment,
        additional_investment=project.additional_investment,
        winning_date=project.winning_date,
        acceptance_date=project.acceptance_date,
        first_payment_date=project.first_payment_date,
        actual_payment_amount=project.actual_payment_amount,
        notes=project.notes,
        product_ids=project.product_ids,
        channel_id=project.channel_id,
        source_opportunity_id=project.source_opportunity_id,
        gross_margin=project.gross_margin,
        terminal_customer_name=customer_name,
        sales_owner_name=owner_name,
    )


@app.post("/projects", response_model=ProjectRead)
async def create_project(
    project: ProjectCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project_code = await generate_code(db, "project")

    gross_margin = None
    if project.downstream_contract_amount and project.upstream_procurement_amount:
        gross_margin = (
            project.downstream_contract_amount - project.upstream_procurement_amount
        )

    new_project = Project(
        project_code=project_code,
        project_name=project.project_name,
        terminal_customer_id=project.terminal_customer_id,
        sales_owner_id=project.sales_owner_id,
        business_type=project.business_type,
        project_status=project.project_status,
        downstream_contract_amount=project.downstream_contract_amount,
        upstream_procurement_amount=project.upstream_procurement_amount,
        direct_project_investment=project.direct_project_investment,
        additional_investment=project.additional_investment,
        winning_date=project.winning_date,
        acceptance_date=project.acceptance_date,
        first_payment_date=project.first_payment_date,
        actual_payment_amount=project.actual_payment_amount,
        notes=project.notes,
        product_ids=project.product_ids,
        channel_id=project.channel_id,
        source_opportunity_id=project.source_opportunity_id,
        gross_margin=gross_margin,
    )
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)
    return new_project


@app.put("/projects/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: int,
    project: ProjectUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = project.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(existing, field, value)

    if existing.downstream_contract_amount and existing.upstream_procurement_amount:
        existing.gross_margin = (
            existing.downstream_contract_amount - existing.upstream_procurement_amount
        )

    await db.commit()
    await db.refresh(existing)
    return existing


@app.delete("/projects/{project_id}")
async def delete_project(
    project_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    await db.delete(project)
    await db.commit()
    return {"message": "Project deleted successfully"}


@app.get("/contracts", response_model=List[ContractRead])
async def list_contracts(
    project_id: Optional[int] = None,
    contract_direction: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(
            Contract,
            Project.project_name,
            TerminalCustomer.customer_name,
            Channel.company_name,
        )
        .options(selectinload(Contract.products), selectinload(Contract.payment_plans))
        .outerjoin(Project, Contract.project_id == Project.id)
        .outerjoin(
            TerminalCustomer, Contract.terminal_customer_id == TerminalCustomer.id
        )
        .outerjoin(Channel, Contract.channel_id == Channel.id)
    )
    if project_id:
        query = query.where(Contract.project_id == project_id)
    if contract_direction:
        query = query.where(Contract.contract_direction == contract_direction)
    result = await db.execute(query)
    rows = result.all()
    contracts = []
    for row in rows:
        contract = row[0]
        project_name = row[1] if len(row) > 1 else None
        customer_name = row[2] if len(row) > 2 else None
        channel_name = row[3] if len(row) > 3 else None
        contract_dict = {
            "id": contract.id,
            "contract_code": contract.contract_code,
            "contract_name": contract.contract_name,
            "project_id": contract.project_id,
            "contract_direction": contract.contract_direction,
            "contract_status": contract.contract_status,
            "terminal_customer_id": contract.terminal_customer_id,
            "channel_id": contract.channel_id,
            "contract_amount": contract.contract_amount,
            "signing_date": contract.signing_date,
            "effective_date": contract.effective_date,
            "expiry_date": contract.expiry_date,
            "contract_file_url": contract.contract_file_url,
            "notes": contract.notes,
            "created_at": contract.created_at,
            "updated_at": contract.updated_at,
            "products": contract.products,
            "payment_plans": contract.payment_plans,
            "project_name": project_name,
            "terminal_customer_name": customer_name,
            "channel_name": channel_name,
        }
        contracts.append(ContractRead(**contract_dict))
    return contracts


@app.get("/contracts/{contract_id}", response_model=ContractRead)
async def get_contract(
    contract_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Contract)
        .where(Contract.id == contract_id)
        .options(selectinload(Contract.products), selectinload(Contract.payment_plans))
    )
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract


@app.post("/contracts", response_model=ContractRead)
async def create_contract(
    contract: ContractCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if (
        contract.contract_direction == "Downstream"
        and not contract.terminal_customer_id
    ):
        raise HTTPException(status_code=400, detail="下游合同必须关联终端客户")
    if contract.contract_direction == "Upstream" and not contract.channel_id:
        raise HTTPException(status_code=400, detail="上游合同必须关联渠道/供应商")

    contract_code = await generate_code(db, "contract")

    def parse_date(d: Optional[str]) -> Optional[date]:
        if not d:
            return None
        if isinstance(d, date):
            return d
        return date.fromisoformat(d)

    new_contract = Contract(
        contract_code=contract_code,
        contract_name=contract.contract_name,
        project_id=contract.project_id,
        contract_direction=contract.contract_direction,
        contract_status=contract.contract_status,
        terminal_customer_id=contract.terminal_customer_id,
        channel_id=contract.channel_id,
        contract_amount=contract.contract_amount,
        signing_date=parse_date(contract.signing_date),
        effective_date=parse_date(contract.effective_date),
        expiry_date=parse_date(contract.expiry_date),
        contract_file_url=contract.contract_file_url,
        notes=contract.notes,
        created_at=date.today(),
        updated_at=date.today(),
    )
    db.add(new_contract)
    await db.flush()

    for product in contract.products:
        new_product = ContractProduct(
            contract_id=new_contract.id,
            product_id=product.product_id,
            product_name=product.product_name,
            quantity=product.quantity,
            unit_price=product.unit_price,
            discount=product.discount,
            amount=product.amount,
            notes=product.notes,
        )
        db.add(new_product)

    for plan in contract.payment_plans:
        new_plan = PaymentPlan(
            contract_id=new_contract.id,
            plan_stage=plan.plan_stage,
            plan_amount=plan.plan_amount,
            plan_date=parse_date(plan.plan_date),
            actual_amount=plan.actual_amount or 0,
            actual_date=parse_date(plan.actual_date),
            payment_status=plan.payment_status,
            notes=plan.notes,
        )
        db.add(new_plan)

    await log_create(
        db=db,
        user_id=current_user["id"],
        user_name=current_user["name"],
        entity_type="contract",
        entity_id=new_contract.id,
        entity_code=new_contract.contract_code,
        entity_name=new_contract.contract_name,
        description=f"创建合同: {new_contract.contract_name}",
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    result = await db.execute(
        select(Contract)
        .where(Contract.id == new_contract.id)
        .options(selectinload(Contract.products), selectinload(Contract.payment_plans))
    )
    return result.scalar_one()


@app.put("/contracts/{contract_id}", response_model=ContractRead)
async def update_contract(
    contract_id: int,
    contract: ContractUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Contract not found")

    update_data = contract.model_dump(exclude_unset=True)

    products_data = update_data.pop("products", None)
    payment_plans_data = update_data.pop("payment_plans", None)

    for field, value in update_data.items():
        setattr(existing, field, value)

    existing.updated_at = date.today()

    if products_data is not None:
        await db.execute(
            select(ContractProduct).where(ContractProduct.contract_id == existing.id)
        )
        result = await db.execute(
            select(ContractProduct).where(ContractProduct.contract_id == existing.id)
        )
        for p in result.scalars().all():
            await db.delete(p)

        for product in products_data:
            new_product = ContractProduct(
                contract_id=existing.id,
                product_id=product.product_id,
                product_name=product.product_name,
                quantity=product.quantity,
                unit_price=product.unit_price,
                discount=product.discount,
                amount=product.amount,
                notes=product.notes,
            )
            db.add(new_product)

    if payment_plans_data is not None:
        result = await db.execute(
            select(PaymentPlan).where(PaymentPlan.contract_id == existing.id)
        )
        for p in result.scalars().all():
            await db.delete(p)

        for plan in payment_plans_data:
            new_plan = PaymentPlan(
                contract_id=existing.id,
                plan_stage=plan.plan_stage,
                plan_amount=plan.plan_amount,
                plan_date=plan.plan_date,
                actual_amount=plan.actual_amount or 0,
                actual_date=plan.actual_date,
                payment_status=plan.payment_status,
                notes=plan.notes,
            )
            db.add(new_plan)

    await db.flush()

    await log_update(
        db=db,
        user_id=current_user["id"],
        user_name=current_user["name"],
        entity_type="contract",
        entity_id=existing.id,
        entity_code=existing.contract_code,
        entity_name=existing.contract_name,
        description=f"更新合同: {existing.contract_name}",
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    await db.refresh(existing)
    return existing


@app.delete("/contracts/{contract_id}")
async def delete_contract(
    contract_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    await log_delete(
        db=db,
        user_id=current_user["id"],
        user_name=current_user["name"],
        entity_type="contract",
        entity_id=contract.id,
        entity_code=contract.contract_code,
        entity_name=contract.contract_name,
        description=f"删除合同: {contract.contract_name}",
        ip_address=request.client.host if request.client else None,
    )

    await db.delete(contract)
    await db.commit()
    return {"message": "Contract deleted successfully"}


# ==================== 跟进记录 API ====================


class FollowUpBase(BaseModel):
    lead_id: Optional[int] = None
    opportunity_id: Optional[int] = None
    project_id: Optional[int] = None
    follow_up_date: date
    follow_up_method: str
    follow_up_content: str
    follow_up_conclusion: str
    next_action: Optional[str] = None
    next_follow_up_date: Optional[date] = None


class FollowUpCreate(BaseModel):
    lead_id: Optional[int] = None
    opportunity_id: Optional[int] = None
    project_id: Optional[int] = None
    follow_up_date: str
    follow_up_method: str
    follow_up_content: str
    follow_up_conclusion: str
    next_action: Optional[str] = None
    next_follow_up_date: Optional[str] = None


class FollowUpRead(FollowUpBase):
    id: int
    terminal_customer_id: Optional[int] = None
    follower_id: int
    created_at: Optional[date] = None
    terminal_customer_name: Optional[str] = None
    lead_name: Optional[str] = None
    opportunity_name: Optional[str] = None
    project_name: Optional[str] = None
    follower_name: Optional[str] = None

    class Config:
        from_attributes = True


class FollowUpUpdate(BaseModel):
    lead_id: Optional[int] = None
    opportunity_id: Optional[int] = None
    project_id: Optional[int] = None
    follow_up_date: Optional[str] = None
    follow_up_method: Optional[str] = None
    follow_up_content: Optional[str] = None
    follow_up_conclusion: Optional[str] = None
    next_action: Optional[str] = None
    next_follow_up_date: Optional[str] = None


@app.get("/follow-ups", response_model=List[FollowUpRead])
async def list_follow_ups(
    terminal_customer_id: Optional[int] = None,
    lead_id: Optional[int] = None,
    opportunity_id: Optional[int] = None,
    project_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(
            FollowUp,
            TerminalCustomer.customer_name,
            User.name,
            Lead.lead_name,
            Opportunity.opportunity_name,
            Project.project_name,
        )
        .outerjoin(
            TerminalCustomer, FollowUp.terminal_customer_id == TerminalCustomer.id
        )
        .outerjoin(User, FollowUp.follower_id == User.id)
        .outerjoin(Lead, FollowUp.lead_id == Lead.id)
        .outerjoin(Opportunity, FollowUp.opportunity_id == Opportunity.id)
        .outerjoin(Project, FollowUp.project_id == Project.id)
    )
    if terminal_customer_id:
        query = query.where(FollowUp.terminal_customer_id == terminal_customer_id)
    if lead_id:
        query = query.where(FollowUp.lead_id == lead_id)
    if opportunity_id:
        query = query.where(FollowUp.opportunity_id == opportunity_id)
    if project_id:
        query = query.where(FollowUp.project_id == project_id)
    query = query.order_by(FollowUp.follow_up_date.desc())
    result = await db.execute(query)
    rows = result.all()
    follow_ups = []
    for row in rows:
        fu = row[0]
        customer_name = row[1] if len(row) > 1 else None
        follower_name = row[2] if len(row) > 2 else None
        lead_name = row[3] if len(row) > 3 else None
        opp_name = row[4] if len(row) > 4 else None
        proj_name = row[5] if len(row) > 5 else None
        fu_dict = {
            "id": fu.id,
            "terminal_customer_id": fu.terminal_customer_id,
            "lead_id": fu.lead_id,
            "opportunity_id": fu.opportunity_id,
            "project_id": fu.project_id,
            "follow_up_date": fu.follow_up_date,
            "follow_up_method": fu.follow_up_method,
            "follow_up_content": fu.follow_up_content,
            "follow_up_conclusion": fu.follow_up_conclusion,
            "next_action": fu.next_action,
            "next_follow_up_date": fu.next_follow_up_date,
            "follower_id": fu.follower_id,
            "created_at": fu.created_at,
            "terminal_customer_name": customer_name,
            "follower_name": follower_name,
            "lead_name": lead_name,
            "opportunity_name": opp_name,
            "project_name": proj_name,
        }
        follow_ups.append(FollowUpRead(**fu_dict))
    return follow_ups


@app.post("/follow-ups", response_model=FollowUpRead)
async def create_follow_up(
    follow_up: FollowUpCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    def parse_date(d: Optional[str]) -> Optional[date]:
        if not d:
            return None
        if isinstance(d, date):
            return d
        return date.fromisoformat(d)

    # 验证至少有一个关联
    if (
        not follow_up.lead_id
        and not follow_up.opportunity_id
        and not follow_up.project_id
    ):
        raise HTTPException(
            status_code=400, detail="关联线索、关联商机、关联项目至少需要选择一个"
        )

    # 从关联对象获取 terminal_customer_id
    terminal_customer_id = None
    if follow_up.lead_id:
        result = await db.execute(select(Lead).where(Lead.id == follow_up.lead_id))
        lead = result.scalar_one_or_none()
        if lead:
            terminal_customer_id = lead.terminal_customer_id
    elif follow_up.opportunity_id:
        result = await db.execute(
            select(Opportunity).where(Opportunity.id == follow_up.opportunity_id)
        )
        opp = result.scalar_one_or_none()
        if opp:
            terminal_customer_id = opp.terminal_customer_id
    elif follow_up.project_id:
        result = await db.execute(
            select(Project).where(Project.id == follow_up.project_id)
        )
        proj = result.scalar_one_or_none()
        if proj:
            terminal_customer_id = proj.terminal_customer_id

    new_follow_up = FollowUp(
        terminal_customer_id=terminal_customer_id,
        lead_id=follow_up.lead_id,
        opportunity_id=follow_up.opportunity_id,
        project_id=follow_up.project_id,
        follow_up_date=parse_date(follow_up.follow_up_date),
        follow_up_method=follow_up.follow_up_method,
        follow_up_content=follow_up.follow_up_content,
        follow_up_conclusion=follow_up.follow_up_conclusion,
        next_action=follow_up.next_action,
        next_follow_up_date=parse_date(follow_up.next_follow_up_date),
        follower_id=current_user["id"],
        created_at=date.today(),
    )
    db.add(new_follow_up)
    await db.flush()
    await db.refresh(new_follow_up)

    entity_type = "follow_up"
    related_entity = []
    if follow_up.lead_id:
        related_entity.append(f"线索#{follow_up.lead_id}")
    if follow_up.opportunity_id:
        related_entity.append(f"商机#{follow_up.opportunity_id}")
    if follow_up.project_id:
        related_entity.append(f"项目#{follow_up.project_id}")

    await log_create(
        db=db,
        user_id=current_user["id"],
        user_name=current_user["name"],
        entity_type=entity_type,
        entity_id=new_follow_up.id,
        entity_name=f"跟进记录#{new_follow_up.id}",
        description=f"创建跟进记录: {', '.join(related_entity) if related_entity else '独立跟进'}",
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    await db.refresh(new_follow_up)

    # 获取关联名称返回
    customer_name = None
    follower_name = current_user["name"]
    lead_name = None
    opp_name = None
    proj_name = None

    if terminal_customer_id:
        result = await db.execute(
            select(TerminalCustomer.customer_name).where(
                TerminalCustomer.id == terminal_customer_id
            )
        )
        row = result.first()
        if row:
            customer_name = row[0]
    if follow_up.lead_id:
        result = await db.execute(
            select(Lead.lead_name).where(Lead.id == follow_up.lead_id)
        )
        row = result.first()
        if row:
            lead_name = row[0]
    if follow_up.opportunity_id:
        result = await db.execute(
            select(Opportunity.opportunity_name).where(
                Opportunity.id == follow_up.opportunity_id
            )
        )
        row = result.first()
        if row:
            opp_name = row[0]
    if follow_up.project_id:
        result = await db.execute(
            select(Project.project_name).where(Project.id == follow_up.project_id)
        )
        row = result.first()
        if row:
            proj_name = row[0]

    return FollowUpRead(
        id=new_follow_up.id,
        terminal_customer_id=terminal_customer_id,
        lead_id=follow_up.lead_id,
        opportunity_id=follow_up.opportunity_id,
        project_id=follow_up.project_id,
        follow_up_date=new_follow_up.follow_up_date,
        follow_up_method=new_follow_up.follow_up_method,
        follow_up_content=new_follow_up.follow_up_content,
        follow_up_conclusion=new_follow_up.follow_up_conclusion,
        next_action=new_follow_up.next_action,
        next_follow_up_date=new_follow_up.next_follow_up_date,
        follower_id=current_user["id"],
        created_at=new_follow_up.created_at,
        terminal_customer_name=customer_name,
        follower_name=follower_name,
        lead_name=lead_name,
        opportunity_name=opp_name,
        project_name=proj_name,
    )


@app.put("/follow-ups/{follow_up_id}", response_model=FollowUpRead)
async def update_follow_up(
    follow_up_id: int,
    follow_up: FollowUpUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(FollowUp).where(FollowUp.id == follow_up_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="FollowUp not found")

    update_data = follow_up.model_dump(exclude_unset=True)

    def parse_date(d: Optional[str]) -> Optional[date]:
        if not d:
            return None
        if isinstance(d, date):
            return d
        return date.fromisoformat(d)

    for field, value in update_data.items():
        if field in ["follow_up_date", "next_follow_up_date"]:
            value = parse_date(value)
        setattr(existing, field, value)

    # 如果关联对象更新，重新计算 terminal_customer_id
    if (
        "lead_id" in update_data
        or "opportunity_id" in update_data
        or "project_id" in update_data
    ):
        terminal_customer_id = None
        if existing.lead_id:
            result = await db.execute(
                select(Lead.terminal_customer_id).where(Lead.id == existing.lead_id)
            )
            row = result.first()
            if row:
                terminal_customer_id = row[0]
        elif existing.opportunity_id:
            result = await db.execute(
                select(Opportunity.terminal_customer_id).where(
                    Opportunity.id == existing.opportunity_id
                )
            )
            row = result.first()
            if row:
                terminal_customer_id = row[0]
        elif existing.project_id:
            result = await db.execute(
                select(Project.terminal_customer_id).where(
                    Project.id == existing.project_id
                )
            )
            row = result.first()
            if row:
                terminal_customer_id = row[0]
        existing.terminal_customer_id = terminal_customer_id

    await db.flush()

    await log_update(
        db=db,
        user_id=current_user["id"],
        user_name=current_user["name"],
        entity_type="follow_up",
        entity_id=existing.id,
        entity_name=f"跟进记录#{existing.id}",
        description=f"更新跟进记录#{existing.id}",
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    await db.refresh(existing)

    # 获取关联名称
    customer_name = None
    follower_name = None
    lead_name = None
    opp_name = None
    proj_name = None

    if existing.terminal_customer_id:
        result = await db.execute(
            select(TerminalCustomer.customer_name).where(
                TerminalCustomer.id == existing.terminal_customer_id
            )
        )
        row = result.first()
        if row:
            customer_name = row[0]
    if existing.follower_id:
        result = await db.execute(
            select(User.name).where(User.id == existing.follower_id)
        )
        row = result.first()
        if row:
            follower_name = row[0]
    if existing.lead_id:
        result = await db.execute(
            select(Lead.lead_name).where(Lead.id == existing.lead_id)
        )
        row = result.first()
        if row:
            lead_name = row[0]
    if existing.opportunity_id:
        result = await db.execute(
            select(Opportunity.opportunity_name).where(
                Opportunity.id == existing.opportunity_id
            )
        )
        row = result.first()
        if row:
            opp_name = row[0]
    if existing.project_id:
        result = await db.execute(
            select(Project.project_name).where(Project.id == existing.project_id)
        )
        row = result.first()
        if row:
            proj_name = row[0]

    return FollowUpRead(
        id=existing.id,
        terminal_customer_id=existing.terminal_customer_id,
        lead_id=existing.lead_id,
        opportunity_id=existing.opportunity_id,
        project_id=existing.project_id,
        follow_up_date=existing.follow_up_date,
        follow_up_method=existing.follow_up_method,
        follow_up_content=existing.follow_up_content,
        follow_up_conclusion=existing.follow_up_conclusion,
        next_action=existing.next_action,
        next_follow_up_date=existing.next_follow_up_date,
        follower_id=existing.follower_id,
        created_at=existing.created_at,
        terminal_customer_name=customer_name,
        follower_name=follower_name,
        lead_name=lead_name,
        opportunity_name=opp_name,
        project_name=proj_name,
    )


@app.delete("/follow-ups/{follow_up_id}")
async def delete_follow_up(
    follow_up_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(FollowUp).where(FollowUp.id == follow_up_id))
    follow_up = result.scalar_one_or_none()
    if not follow_up:
        raise HTTPException(status_code=404, detail="FollowUp not found")

    await log_delete(
        db=db,
        user_id=current_user["id"],
        user_name=current_user["name"],
        entity_type="follow_up",
        entity_id=follow_up.id,
        entity_name=f"跟进记录#{follow_up.id}",
        description=f"删除跟进记录#{follow_up.id}",
        ip_address=request.client.host if request.client else None,
    )

    await db.delete(follow_up)
    await db.commit()
    return {"message": "FollowUp deleted successfully"}


# ==================== 渠道 API ====================


class ChannelBase(BaseModel):
    company_name: str
    channel_type: str
    status: str = "合作中"
    main_contact: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    credit_code: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    website: Optional[str] = None
    wechat: Optional[str] = None
    cooperation_products: Optional[str] = None
    cooperation_region: Optional[str] = None
    discount_rate: Optional[float] = None
    billing_info: Optional[str] = None
    notes: Optional[str] = None


class ChannelCreate(ChannelBase):
    credit_code: str  # 创建时必填


class ChannelRead(ChannelBase):
    id: int
    channel_code: str
    created_at: Optional[date] = None
    updated_at: Optional[date] = None

    class Config:
        from_attributes = True


class ChannelUpdate(BaseModel):
    company_name: Optional[str] = None
    channel_type: Optional[str] = None
    status: Optional[str] = None
    main_contact: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    credit_code: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    website: Optional[str] = None
    wechat: Optional[str] = None
    cooperation_products: Optional[str] = None
    cooperation_region: Optional[str] = None
    discount_rate: Optional[float] = None
    billing_info: Optional[str] = None
    notes: Optional[str] = None


@app.get("/channels", response_model=List[ChannelRead])
async def list_channels(
    channel_type: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Channel)
    if channel_type:
        query = query.where(Channel.channel_type == channel_type)
    if status:
        query = query.where(Channel.status == status)
    query = query.order_by(Channel.id.desc())
    result = await db.execute(query)
    return result.scalars().all()


@app.get("/channels/check-credit-code")
async def check_channel_credit_code(
    credit_code: str,
    exclude_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Channel).where(Channel.credit_code == credit_code)
    if exclude_id:
        query = query.where(Channel.id != exclude_id)
    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    return {"exists": existing is not None}


@app.get("/channels/{channel_id}", response_model=ChannelRead)
async def get_channel(
    channel_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    return channel


@app.post("/channels", response_model=ChannelRead)
async def create_channel(
    channel: ChannelCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(Channel).where(Channel.credit_code == channel.credit_code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该统一社会信用代码已存在")

    channel_code = await generate_code(db, "channel")

    new_channel = Channel(
        channel_code=channel_code,
        company_name=channel.company_name,
        channel_type=channel.channel_type,
        status=channel.status,
        main_contact=channel.main_contact,
        phone=channel.phone,
        email=channel.email,
        province=channel.province,
        city=channel.city,
        address=channel.address,
        credit_code=channel.credit_code,
        bank_name=channel.bank_name,
        bank_account=channel.bank_account,
        website=channel.website,
        wechat=channel.wechat,
        cooperation_products=channel.cooperation_products,
        cooperation_region=channel.cooperation_region,
        discount_rate=channel.discount_rate,
        billing_info=channel.billing_info,
        notes=channel.notes,
        created_at=date.today(),
        updated_at=date.today(),
    )
    db.add(new_channel)
    await db.flush()
    await db.refresh(new_channel)

    await log_create(
        db=db,
        user_id=current_user["id"],
        user_name=current_user["name"],
        entity_type="channel",
        entity_id=new_channel.id,
        entity_code=new_channel.channel_code,
        entity_name=new_channel.company_name,
        description=f"创建渠道: {new_channel.company_name}",
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    return new_channel


@app.put("/channels/{channel_id}", response_model=ChannelRead)
async def update_channel(
    channel_id: int,
    channel: ChannelUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Channel not found")

    update_data = channel.model_dump(exclude_unset=True)

    if (
        "credit_code" in update_data
        and update_data["credit_code"] != existing.credit_code
    ):
        duplicate = await db.execute(
            select(Channel).where(Channel.credit_code == update_data["credit_code"])
        )
        if duplicate.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="该统一社会信用代码已存在")

    for field, value in update_data.items():
        setattr(existing, field, value)

    existing.updated_at = date.today()
    await db.flush()

    await log_update(
        db=db,
        user_id=current_user["id"],
        user_name=current_user["name"],
        entity_type="channel",
        entity_id=existing.id,
        entity_code=existing.channel_code,
        entity_name=existing.company_name,
        description=f"更新渠道: {existing.company_name}",
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    await db.refresh(existing)
    return existing


@app.delete("/channels/{channel_id}")
async def delete_channel(
    channel_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    await log_delete(
        db=db,
        user_id=current_user["id"],
        user_name=current_user["name"],
        entity_type="channel",
        entity_id=channel.id,
        entity_code=channel.channel_code,
        entity_name=channel.company_name,
        description=f"删除渠道: {channel.company_name}",
        ip_address=request.client.host if request.client else None,
    )

    await db.delete(channel)
    await db.commit()
    return {"message": "Channel deleted successfully"}


class ChannelFullView(BaseModel):
    channel: dict
    summary: dict
    customers: List[dict]
    opportunities: List[dict]
    projects: List[dict]
    contracts: List[dict]


@app.get("/channels/{channel_id}/full-view", response_model=ChannelFullView)
async def get_channel_full_view(
    channel_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    customers_result = await db.execute(
        select(TerminalCustomer, User.name)
        .outerjoin(User, TerminalCustomer.customer_owner_id == User.id)
        .where(TerminalCustomer.channel_id == channel_id)
    )
    customers_rows = customers_result.all()
    customers = []
    for row in customers_rows:
        cust = row[0]
        owner_name = row[1]
        customers.append(
            {
                "id": cust.id,
                "customer_code": cust.customer_code,
                "customer_name": cust.customer_name,
                "customer_industry": cust.customer_industry,
                "customer_region": cust.customer_region,
                "customer_status": cust.customer_status,
                "customer_owner_name": owner_name,
            }
        )

    opps_result = await db.execute(
        select(Opportunity, TerminalCustomer.customer_name, User.name)
        .outerjoin(
            TerminalCustomer, Opportunity.terminal_customer_id == TerminalCustomer.id
        )
        .outerjoin(User, Opportunity.sales_owner_id == User.id)
        .where(Opportunity.channel_id == channel_id)
    )
    opps_rows = opps_result.all()
    opportunities = []
    for row in opps_rows:
        opp = row[0]
        customer_name = row[1]
        owner_name = row[2]
        opportunities.append(
            {
                "id": opp.id,
                "opportunity_code": opp.opportunity_code,
                "opportunity_name": opp.opportunity_name,
                "opportunity_stage": opp.opportunity_stage,
                "expected_contract_amount": float(opp.expected_contract_amount)
                if opp.expected_contract_amount
                else None,
                "terminal_customer_name": customer_name,
                "sales_owner_name": owner_name,
                "project_id": opp.project_id,
            }
        )

    projects_result = await db.execute(
        select(Project, TerminalCustomer.customer_name, User.name)
        .outerjoin(
            TerminalCustomer, Project.terminal_customer_id == TerminalCustomer.id
        )
        .outerjoin(User, Project.sales_owner_id == User.id)
        .where(Project.channel_id == channel_id)
    )
    projects_rows = projects_result.all()
    projects = []
    for row in projects_rows:
        proj = row[0]
        customer_name = row[1]
        owner_name = row[2]
        projects.append(
            {
                "id": proj.id,
                "project_code": proj.project_code,
                "project_name": proj.project_name,
                "project_status": proj.project_status,
                "business_type": proj.business_type,
                "downstream_contract_amount": float(proj.downstream_contract_amount)
                if proj.downstream_contract_amount
                else None,
                "terminal_customer_name": customer_name,
                "sales_owner_name": owner_name,
            }
        )

    contracts_result = await db.execute(
        select(Contract).where(Contract.channel_id == channel_id)
    )
    contracts_rows = contracts_result.all()
    contracts = []
    for row in contracts_rows:
        c = row[0]
        contracts.append(
            {
                "id": c.id,
                "contract_code": c.contract_code,
                "contract_name": c.contract_name,
                "contract_direction": c.contract_direction,
                "contract_status": c.contract_status,
                "contract_amount": float(c.contract_amount)
                if c.contract_amount
                else None,
                "signing_date": str(c.signing_date) if c.signing_date else None,
            }
        )

    return ChannelFullView(
        channel={
            "id": channel.id,
            "channel_code": channel.channel_code,
            "company_name": channel.company_name,
            "channel_type": channel.channel_type,
            "status": channel.status,
            "main_contact": channel.main_contact,
            "phone": channel.phone,
            "email": channel.email,
            "province": channel.province,
            "city": channel.city,
            "address": channel.address,
            "credit_code": channel.credit_code,
            "website": channel.website,
            "wechat": channel.wechat,
            "cooperation_region": channel.cooperation_region,
            "discount_rate": float(channel.discount_rate)
            if channel.discount_rate
            else None,
            "notes": channel.notes,
        },
        summary={
            "customers_count": len(customers),
            "opportunities_count": len(opportunities),
            "projects_count": len(projects),
            "contracts_count": len(contracts),
        },
        customers=customers,
        opportunities=opportunities,
        projects=projects,
        contracts=contracts,
    )


# ==================== 数据字典 API ====================


class DictItemCreate(BaseModel):
    dict_type: str
    code: str
    name: str
    parent_id: Optional[int] = None
    sort_order: int = 0
    is_active: bool = True
    extra_data: Optional[dict] = None


class DictItemRead(BaseModel):
    id: int
    dict_type: str
    code: str
    name: str
    parent_id: Optional[int] = None
    sort_order: int = 0
    is_active: bool
    extra_data: Optional[dict] = None

    class Config:
        from_attributes = True


class DictItemUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    extra_data: Optional[dict] = None


@app.get("/dict/items", response_model=List[DictItemRead])
async def list_dict_items(
    dict_type: Optional[str] = None,
    parent_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(DictItem)
    if dict_type:
        query = query.where(DictItem.dict_type == dict_type)
    if parent_id is not None:
        query = query.where(DictItem.parent_id == parent_id)
    query = query.order_by(DictItem.sort_order, DictItem.id)
    result = await db.execute(query)
    return result.scalars().all()


@app.get("/dict/types")
async def list_dict_types(
    current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(DictItem.dict_type).distinct().order_by(DictItem.dict_type)
    )
    return {"types": result.scalars().all()}


@app.post("/dict/items", response_model=DictItemRead)
async def create_dict_item(
    item: DictItemCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can create dict items")

    new_item = DictItem(
        dict_type=item.dict_type,
        code=item.code,
        name=item.name,
        parent_id=item.parent_id,
        sort_order=item.sort_order,
        is_active=item.is_active,
        extra_data=item.extra_data,
    )
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    return new_item


@app.put("/dict/items/{item_id}", response_model=DictItemRead)
async def update_dict_item(
    item_id: int,
    item: DictItemUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can update dict items")

    result = await db.execute(select(DictItem).where(DictItem.id == item_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Dict item not found")

    if item.code is not None:
        existing.code = item.code
    if item.name is not None:
        existing.name = item.name
    if item.parent_id is not None:
        existing.parent_id = item.parent_id
    if item.sort_order is not None:
        existing.sort_order = item.sort_order
    if item.is_active is not None:
        existing.is_active = item.is_active
    if item.extra_data is not None:
        existing.extra_data = item.extra_data

    await db.commit()
    await db.refresh(existing)
    return existing


@app.delete("/dict/items/{item_id}")
async def delete_dict_item(
    item_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can delete dict items")

    result = await db.execute(select(DictItem).where(DictItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Dict item not found")

    await db.delete(item)
    await db.commit()
    return {"message": "Dict item deleted successfully"}


# ==================== 操作日志 API ====================


class OperationLogRead(BaseModel):
    id: int
    user_id: int
    user_name: str
    action_type: str
    entity_type: str
    entity_id: int
    entity_code: Optional[str] = None
    entity_name: Optional[str] = None
    old_value: Optional[dict] = None
    new_value: Optional[dict] = None
    description: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


@app.get("/operation-logs", response_model=List[OperationLogRead])
async def list_operation_logs(
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    user_id: Optional[int] = None,
    action_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(OperationLog).order_by(OperationLog.created_at.desc())

    if entity_type:
        query = query.where(OperationLog.entity_type == entity_type)
    if entity_id:
        query = query.where(OperationLog.entity_id == entity_id)
    if user_id:
        query = query.where(OperationLog.user_id == user_id)
    if action_type:
        query = query.where(OperationLog.action_type == action_type)
    if start_date:
        query = query.where(OperationLog.created_at >= start_date)
    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        query = query.where(OperationLog.created_at <= end_datetime)

    query = query.limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@app.get("/operation-logs/{log_id}", response_model=OperationLogRead)
async def get_operation_log(
    log_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(OperationLog).where(OperationLog.id == log_id))
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=404, detail="Operation log not found")
    return log


@app.get(
    "/operation-logs/entity/{entity_type}/{entity_id}",
    response_model=List[OperationLogRead],
)
async def get_entity_logs(
    entity_type: str,
    entity_id: int,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_logs_by_entity(db, entity_type, entity_id, limit)


@app.get("/operation-logs/user/{user_id}", response_model=List[OperationLogRead])
async def get_user_logs(
    user_id: int,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_logs_by_user(db, user_id, limit)


# ==================== 报表统计 API ====================


class SalesFunnelResponse(BaseModel):
    leads: dict
    opportunities: dict
    projects: dict
    contracts: dict
    conversion_rates: dict


class PerformanceByUser(BaseModel):
    user_id: int
    user_name: str
    contract_count: int
    contract_amount: float
    received_amount: float
    pending_amount: float
    gross_margin: float


class PerformanceReportResponse(BaseModel):
    by_user: List[PerformanceByUser]
    by_month: List[dict]
    total_contract_amount: float
    total_received_amount: float
    total_pending_amount: float


class PaymentProgressResponse(BaseModel):
    total_plan_amount: float
    total_actual_amount: float
    total_pending_amount: float
    overdue_amount: float
    overdue_count: int
    contracts: List[dict]
    progress_percentage: float


@app.get("/reports/sales-funnel", response_model=SalesFunnelResponse)
async def get_sales_funnel(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    sales_owner_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    lead_query = select(Lead)
    if start_date:
        lead_query = lead_query.where(Lead.created_at >= start_date)
    if end_date:
        lead_query = lead_query.where(Lead.created_at <= end_date)
    if sales_owner_id:
        lead_query = lead_query.where(Lead.sales_owner_id == sales_owner_id)
    lead_result = await db.execute(lead_query)
    leads = lead_result.scalars().all()

    lead_stages = {}
    for lead in leads:
        stage = lead.lead_stage
        lead_stages[stage] = lead_stages.get(stage, 0) + 1

    converted_leads = sum(1 for l in leads if l.converted_to_opportunity)
    lost_leads = sum(1 for l in leads if l.lead_stage == "已流失")

    opp_query = select(Opportunity)
    if start_date:
        opp_query = opp_query.where(Opportunity.created_at >= start_date)
    if end_date:
        opp_query = opp_query.where(Opportunity.created_at <= end_date)
    if sales_owner_id:
        opp_query = opp_query.where(Opportunity.sales_owner_id == sales_owner_id)
    opp_result = await db.execute(opp_query)
    opportunities = opp_result.scalars().all()

    opp_stages = {}
    for opp in opportunities:
        stage = opp.opportunity_stage
        opp_stages[stage] = opp_stages.get(stage, 0) + 1

    opp_total_amount = sum(
        float(o.expected_contract_amount or 0) for o in opportunities
    )
    won_opps = sum(1 for o in opportunities if o.opportunity_stage == "已成交")
    lost_opps = sum(1 for o in opportunities if o.opportunity_stage == "已流失")

    proj_query = select(Project)
    if start_date:
        proj_query = proj_query.where(Project.created_at >= start_date)
    if end_date:
        proj_query = proj_query.where(Project.created_at <= end_date)
    if sales_owner_id:
        proj_query = proj_query.where(Project.sales_owner_id == sales_owner_id)
    proj_result = await db.execute(proj_query)
    projects = proj_result.scalars().all()

    proj_statuses = {}
    for proj in projects:
        status = proj.project_status
        proj_statuses[status] = proj_statuses.get(status, 0) + 1

    proj_total_amount = sum(float(p.downstream_contract_amount or 0) for p in projects)

    contract_query = select(Contract).where(Contract.contract_direction == "Downstream")
    if start_date:
        contract_query = contract_query.where(Contract.signing_date >= start_date)
    if end_date:
        contract_query = contract_query.where(Contract.signing_date <= end_date)
    if sales_owner_id:
        contract_query = contract_query.join(
            Project, Contract.project_id == Project.id
        ).where(Project.sales_owner_id == sales_owner_id)
    contract_result = await db.execute(contract_query)
    contracts = contract_result.scalars().all()

    contract_statuses = {}
    for contract in contracts:
        status = contract.contract_status
        contract_statuses[status] = contract_statuses.get(status, 0) + 1

    contract_total_amount = sum(float(c.contract_amount or 0) for c in contracts)

    lead_to_opp_rate = round(converted_leads / len(leads) * 100, 2) if leads else 0
    opp_to_proj_rate = (
        round(won_opps / len(opportunities) * 100, 2) if opportunities else 0
    )

    return SalesFunnelResponse(
        leads={
            "total": len(leads),
            "by_stage": lead_stages,
            "converted": converted_leads,
            "lost": lost_leads,
        },
        opportunities={
            "total": len(opportunities),
            "by_stage": opp_stages,
            "total_amount": opp_total_amount,
            "won": won_opps,
            "lost": lost_opps,
        },
        projects={
            "total": len(projects),
            "by_status": proj_statuses,
            "total_amount": proj_total_amount,
        },
        contracts={
            "total": len(contracts),
            "by_status": contract_statuses,
            "total_amount": contract_total_amount,
        },
        conversion_rates={
            "lead_to_opportunity": lead_to_opp_rate,
            "opportunity_to_project": opp_to_proj_rate,
        },
    )


@app.get("/reports/performance", response_model=PerformanceReportResponse)
async def get_performance_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    sales_owner_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        # Simplified version for now
        return PerformanceReportResponse(
            by_user=[],
            by_month=[],
            total_contract_amount=0.0,
            total_received_amount=0.0,
            total_pending_amount=0.0,
        )
    except Exception as e:
        print(f"Performance report error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    if start_date:
        contract_query = contract_query.where(Contract.signing_date >= start_date)
    if end_date:
        contract_query = contract_query.where(Contract.signing_date <= end_date)
    if sales_owner_id:
        contract_query = contract_query.where(Project.sales_owner_id == sales_owner_id)

    contract_result = await db.execute(contract_query)
    contract_rows = contract_result.all()

    user_stats = {}
    for row in contract_rows:
        contract = row[0]
        owner_id = row[1]
        owner_name = row[2]
        if owner_id not in user_stats:
            user_stats[owner_id] = {
                "user_id": owner_id,
                "user_name": owner_name,
                "contract_count": 0,
                "contract_amount": 0,
                "received_amount": 0,
                "pending_amount": 0,
                "gross_margin": 0,
            }
        user_stats[owner_id]["contract_count"] += 1
        user_stats[owner_id]["contract_amount"] += float(contract.contract_amount or 0)

    payment_query = (
        select(PaymentPlan, Contract, Project.sales_owner_id)
        .join(Contract)
        .join(Project, Contract.project_id == Project.id)
    )
    if start_date:
        payment_query = payment_query.where(PaymentPlan.actual_date >= start_date)
    if end_date:
        payment_query = payment_query.where(PaymentPlan.actual_date <= end_date)

    payment_result = await db.execute(payment_query)
    payment_rows = payment_result.all()

    for row in payment_rows:
        payment = row[0]
        owner_id = row[2]
        if owner_id in user_stats:
            user_stats[owner_id]["received_amount"] += float(payment.actual_amount or 0)

    for uid in user_stats:
        user_stats[uid]["pending_amount"] = (
            user_stats[uid]["contract_amount"] - user_stats[uid]["received_amount"]
        )
        user_stats[uid]["gross_margin"] = (
            round(
                user_stats[uid]["received_amount"]
                / user_stats[uid]["contract_amount"]
                * 100,
                2,
            )
            if user_stats[uid]["contract_amount"] > 0
            else 0
        )

    month_stats = []
    for row in contract_rows:
        contract = row[0]
        if contract.signing_date:
            month_key = contract.signing_date.strftime("%Y-%m")
            found = False
            for m in month_stats:
                if m["month"] == month_key:
                    m["contract_amount"] += float(contract.contract_amount or 0)
                    m["contract_count"] += 1
                    found = True
                    break
            if not found:
                month_stats.append(
                    {
                        "month": month_key,
                        "contract_amount": float(contract.contract_amount or 0),
                        "contract_count": 1,
                    }
                )

    month_stats.sort(key=lambda x: x["month"])

    total_contract = sum(u["contract_amount"] for u in user_stats.values())
    total_received = sum(u["received_amount"] for u in user_stats.values())
    total_pending = total_contract - total_received

    return PerformanceReportResponse(
        by_user=[PerformanceByUser(**u) for u in user_stats.values()],
        by_month=month_stats,
        total_contract_amount=total_contract,
        total_received_amount=total_received,
        total_pending_amount=total_pending,
    )


@app.get("/reports/payment-progress", response_model=PaymentProgressResponse)
async def get_payment_progress(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    sales_owner_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    contract_query = select(Contract).where(Contract.contract_direction == "Downstream")
    if sales_owner_id:
        contract_query = contract_query.join(
            Project, Contract.project_id == Project.id
        ).where(Project.sales_owner_id == sales_owner_id)
    contract_result = await db.execute(contract_query)
    contracts = contract_result.scalars().all()

    contract_data = []
    total_plan = 0
    total_actual = 0
    overdue_amount = 0
    overdue_count = 0

    today = date.today()

    for contract in contracts:
        payment_query = select(PaymentPlan).where(
            PaymentPlan.contract_id == contract.id
        )
        payment_result = await db.execute(payment_query)
        payments = payment_result.scalars().all()

        plan_sum = sum(float(p.plan_amount or 0) for p in payments)
        actual_sum = sum(float(p.actual_amount or 0) for p in payments)

        contract_overdue = 0
        for p in payments:
            if p.plan_date and p.plan_date < today and p.payment_status != "completed":
                contract_overdue += float(p.plan_amount or 0) - float(
                    p.actual_amount or 0
                )
                overdue_count += 1

        progress = round(actual_sum / plan_sum * 100, 2) if plan_sum > 0 else 0

        contract_data.append(
            {
                "contract_id": contract.id,
                "contract_code": contract.contract_code,
                "contract_name": contract.contract_name,
                "contract_amount": float(contract.contract_amount or 0),
                "plan_amount": plan_sum,
                "actual_amount": actual_sum,
                "pending_amount": plan_sum - actual_sum,
                "overdue_amount": contract_overdue,
                "progress_percentage": progress,
                "payment_count": len(payments),
                "completed_count": sum(
                    1 for p in payments if p.payment_status == "completed"
                ),
            }
        )

        total_plan += plan_sum
        total_actual += actual_sum
        overdue_amount += contract_overdue

    total_pending = total_plan - total_actual
    overall_progress = (
        round(total_actual / total_plan * 100, 2) if total_plan > 0 else 0
    )

    return PaymentProgressResponse(
        total_plan_amount=total_plan,
        total_actual_amount=total_actual,
        total_pending_amount=total_pending,
        overdue_amount=overdue_amount,
        overdue_count=overdue_count,
        contracts=contract_data,
        progress_percentage=overall_progress,
    )


class DashboardSummaryResponse(BaseModel):
    leads_count: int
    opportunities_count: int
    projects_count: int
    contracts_count: int
    pending_followups: int
    alerts_count: int
    won_opportunities: int
    lost_opportunities: int
    quarterly_target: float
    quarterly_achieved: float
    monthly_target: float
    monthly_achieved: float
    quarterly_forecast_amount: float


class DashboardTodoItem(BaseModel):
    id: int
    type: str
    title: str
    customer_name: str
    due_date: Optional[str]
    priority: str
    entity_type: str
    entity_id: int


class DashboardFollowUpItem(BaseModel):
    id: int
    customer_name: str
    follow_up_date: str
    follow_up_method: str
    follow_up_content: str
    follower_name: str
    entity_type: str
    entity_id: int


class DashboardNotificationItem(BaseModel):
    id: int
    type: str
    title: str
    content: str
    created_at: str
    is_read: bool
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    entity_code: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


@app.get("/dashboard/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user["id"]
    is_admin = current_user["role"] == "admin"

    lead_query = select(Lead)
    if not is_admin:
        lead_query = lead_query.where(Lead.sales_owner_id == user_id)
    lead_result = await db.execute(lead_query)
    leads = lead_result.scalars().all()

    opp_query = select(Opportunity)
    if not is_admin:
        opp_query = opp_query.where(Opportunity.sales_owner_id == user_id)
    opp_result = await db.execute(opp_query)
    opportunities = opp_result.scalars().all()

    project_query = select(Project)
    if not is_admin:
        project_query = project_query.where(Project.sales_owner_id == user_id)
    project_result = await db.execute(project_query)
    projects = project_result.scalars().all()

    contract_query = (
        select(Contract)
        .join(Project, Contract.project_id == Project.id)
        .where(Contract.contract_direction == "Downstream")
    )
    if not is_admin:
        contract_query = contract_query.where(Project.sales_owner_id == user_id)
    contract_result = await db.execute(contract_query)
    contracts = contract_result.scalars().all()

    today = date.today()
    month_start = today.replace(day=1)
    quarter = (today.month - 1) // 3 + 1
    quarter_start_month = (quarter - 1) * 3 + 1
    quarter_start = today.replace(month=quarter_start_month, day=1)

    month_contract_query = (
        select(Contract)
        .join(Project, Contract.project_id == Project.id)
        .where(Contract.contract_direction == "Downstream")
        .where(Contract.signing_date >= month_start)
    )
    if not is_admin:
        month_contract_query = month_contract_query.where(
            Project.sales_owner_id == user_id
        )
    month_contract_result = await db.execute(month_contract_query)
    month_contracts = month_contract_result.scalars().all()
    monthly_achieved = sum(float(c.contract_amount or 0) for c in month_contracts)

    quarter_contract_query = (
        select(Contract)
        .join(Project, Contract.project_id == Project.id)
        .where(Contract.contract_direction == "Downstream")
        .where(Contract.signing_date >= quarter_start)
    )
    if not is_admin:
        quarter_contract_query = quarter_contract_query.where(
            Project.sales_owner_id == user_id
        )
    quarter_contract_result = await db.execute(quarter_contract_query)
    quarter_contracts = quarter_contract_result.scalars().all()
    quarterly_achieved = sum(float(c.contract_amount or 0) for c in quarter_contracts)

    target_query = select(SalesTarget).where(
        SalesTarget.target_year == today.year,
        SalesTarget.target_type == "monthly",
        SalesTarget.target_period == today.month,
    )
    if not is_admin:
        target_query = target_query.where(SalesTarget.user_id == user_id)
    target_result = await db.execute(target_query)
    monthly_targets = target_result.scalars().all()
    monthly_target = sum(float(t.target_amount or 0) for t in monthly_targets)

    qtarget_query = select(SalesTarget).where(
        SalesTarget.target_year == today.year,
        SalesTarget.target_type == "quarterly",
        SalesTarget.target_period == quarter,
    )
    if not is_admin:
        qtarget_query = qtarget_query.where(SalesTarget.user_id == user_id)
    qtarget_result = await db.execute(qtarget_query)
    quarterly_targets = qtarget_result.scalars().all()
    quarterly_target = sum(float(t.target_amount or 0) for t in quarterly_targets)

    quarter_end_month = quarter_start_month + 2
    quarter_end = today.replace(month=quarter_end_month, day=28)
    forecast_query = select(Opportunity).where(
        Opportunity.opportunity_stage.notin_(["已成交", "已流失"]),
        Opportunity.expected_close_date >= quarter_start,
        Opportunity.expected_close_date <= quarter_end,
        Opportunity.expected_contract_amount != None,
    )
    if not is_admin:
        forecast_query = forecast_query.where(Opportunity.sales_owner_id == user_id)
    forecast_result = await db.execute(forecast_query)
    forecast_opps = forecast_result.scalars().all()
    quarterly_forecast_amount = sum(
        float(o.expected_contract_amount or 0) for o in forecast_opps
    )

    followup_query = select(FollowUp)
    if not is_admin:
        followup_query = followup_query.where(FollowUp.follower_id == user_id)
    followup_result = await db.execute(followup_query)
    followups = followup_result.scalars().all()

    pending_followups = sum(1 for f in followups if not f.next_action)

    won_count = sum(1 for o in opportunities if o.opportunity_stage == "已成交")
    lost_count = sum(1 for o in opportunities if o.opportunity_stage == "已流失")

    stalled_query = select(Opportunity).where(
        Opportunity.opportunity_stage.notin_(["已成交", "已流失"])
    )
    if not is_admin:
        stalled_query = stalled_query.where(Opportunity.sales_owner_id == user_id)
    stalled_result = await db.execute(stalled_query)
    stalled_opps = stalled_result.scalars().all()

    alerts_count = pending_followups + len(stalled_opps)

    return DashboardSummaryResponse(
        leads_count=len(leads),
        opportunities_count=len(opportunities),
        projects_count=len(projects),
        contracts_count=len(contracts),
        pending_followups=pending_followups,
        alerts_count=alerts_count,
        won_opportunities=won_count,
        lost_opportunities=lost_count,
        quarterly_target=quarterly_target,
        quarterly_achieved=quarterly_achieved,
        monthly_target=monthly_target,
        monthly_achieved=monthly_achieved,
        quarterly_forecast_amount=quarterly_forecast_amount,
    )


@app.get("/dashboard/todos", response_model=List[DashboardTodoItem])
async def get_dashboard_todos(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user["id"]
    is_admin = current_user["role"] == "admin"
    today = date.today()
    todos = []

    followup_query = (
        select(FollowUp)
        .options(selectinload(FollowUp.terminal_customer))
        .where(FollowUp.follow_up_date >= today)
    )
    if not is_admin:
        followup_query = followup_query.where(FollowUp.follower_id == user_id)
    followup_query = followup_query.order_by(FollowUp.follow_up_date).limit(10)
    followup_result = await db.execute(followup_query)
    followups = followup_result.scalars().all()

    for f in followups:
        entity_type = ""
        entity_id = 0

        if f.lead_id:
            entity_type = "lead"
            entity_id = f.lead_id
        elif f.opportunity_id:
            entity_type = "opportunity"
            entity_id = f.opportunity_id
        elif f.project_id:
            entity_type = "project"
            entity_id = f.project_id

        customer_name = f.terminal_customer.customer_name if f.terminal_customer else ""

        todos.append(
            DashboardTodoItem(
                id=f.id,
                type="跟进提醒",
                title=f.follow_up_content[:50] if f.follow_up_content else "跟进任务",
                customer_name=customer_name,
                due_date=str(f.follow_up_date) if f.follow_up_date else None,
                priority="高"
                if f.follow_up_date and f.follow_up_date <= today
                else "中",
                entity_type=entity_type,
                entity_id=entity_id,
            )
        )

    return todos


@app.get("/dashboard/recent-followups", response_model=List[DashboardFollowUpItem])
async def get_dashboard_recent_followups(
    limit: int = 5,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user["id"]
    is_admin = current_user["role"] == "admin"

    followup_query = (
        select(FollowUp)
        .options(
            selectinload(FollowUp.terminal_customer), selectinload(FollowUp.follower)
        )
        .order_by(FollowUp.follow_up_date.desc())
        .limit(limit)
    )
    if not is_admin:
        followup_query = followup_query.where(FollowUp.follower_id == user_id)
    followup_result = await db.execute(followup_query)
    followups = followup_result.scalars().all()

    items = []
    for f in followups:
        entity_type = ""
        entity_id = 0

        if f.lead_id:
            entity_type = "lead"
            entity_id = f.lead_id
        elif f.opportunity_id:
            entity_type = "opportunity"
            entity_id = f.opportunity_id
        elif f.project_id:
            entity_type = "project"
            entity_id = f.project_id

        customer_name = f.terminal_customer.customer_name if f.terminal_customer else ""
        follower_name = f.follower.name if f.follower else ""

        items.append(
            DashboardFollowUpItem(
                id=f.id,
                customer_name=customer_name,
                follow_up_date=str(f.follow_up_date) if f.follow_up_date else "",
                follow_up_method=f.follow_up_method or "",
                follow_up_content=f.follow_up_content[:100]
                if f.follow_up_content
                else "",
                follower_name=follower_name,
                entity_type=entity_type,
                entity_id=entity_id,
            )
        )

    return items


@app.get("/dashboard/notifications", response_model=List[DashboardNotificationItem])
async def get_dashboard_notifications(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Simplified version for testing
    return []


class TeamRankItem(BaseModel):
    rank: int
    user_id: int
    user_name: str
    amount: float


@app.get("/dashboard/team-rank", response_model=List[TeamRankItem])
async def get_team_rank(
    limit: int = 5,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")

    today = date.today()
    month_start = today.replace(day=1)

    users_result = await db.execute(select(User).where(User.role == "sales"))
    users = users_result.scalars().all()

    user_stats = []
    for user in users:
        contract_query = (
            select(Contract)
            .join(Project, Contract.project_id == Project.id)
            .where(Contract.contract_direction == "Downstream")
            .where(Contract.signing_date >= month_start)
            .where(Project.sales_owner_id == user.id)
        )
        contract_result = await db.execute(contract_query)
        contracts = contract_result.scalars().all()
        total_amount = sum(float(c.contract_amount or 0) for c in contracts)
        user_stats.append(
            {
                "user_id": user.id,
                "user_name": user.name or f"用户{user.id}",
                "amount": total_amount,
            }
        )

    user_stats.sort(key=lambda x: x["amount"], reverse=True)
    result = []
    for i, stat in enumerate(user_stats[:limit]):
        result.append(
            TeamRankItem(
                rank=i + 1,
                user_id=stat["user_id"],
                user_name=stat["user_name"],
                amount=stat["amount"],
            )
        )
    return result


class MarkNotificationsReadRequest(BaseModel):
    notifications: List[dict]


@app.post("/dashboard/notifications/mark-read")
async def mark_notifications_read(
    request: MarkNotificationsReadRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user["id"]
    now = datetime.utcnow()

    for item in request.notifications:
        if item.get("entity_type") and item.get("entity_id") and item.get("type"):
            existing = await db.execute(
                select(UserNotificationRead).where(
                    UserNotificationRead.user_id == user_id,
                    UserNotificationRead.entity_type == item["entity_type"],
                    UserNotificationRead.entity_id == item["entity_id"],
                    UserNotificationRead.notification_type == item["type"],
                )
            )
            if existing.scalars().first():
                continue

            read_record = UserNotificationRead(
                user_id=user_id,
                entity_type=item["entity_type"],
                entity_id=item["entity_id"],
                notification_type=item["type"],
                created_at=now,
            )
            db.add(read_record)

    await db.commit()
    return {"success": True}


class AlertItem(BaseModel):
    alert_type: str
    priority: str
    title: str
    content: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    entity_code: Optional[str] = None
    entity_name: Optional[str] = None
    created_at: str


class AlertSummary(BaseModel):
    high: int
    medium: int
    low: int
    total: int


class AlertRuleCreate(BaseModel):
    rule_code: str
    rule_name: str
    rule_type: str
    entity_type: str
    priority: str = "medium"
    threshold_days: int = 0
    threshold_amount: int = 0
    description: Optional[str] = None
    is_active: bool = True


class AlertRuleRead(AlertRuleCreate):
    id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


@app.get("/alerts", response_model=List[AlertItem])
async def get_alerts(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user["id"]
    is_admin = current_user["role"] == "admin"
    alerts = await AlertService.calculate_alerts(db, user_id, is_admin)
    return alerts


@app.get("/alerts/summary", response_model=AlertSummary)
async def get_alert_summary(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user["id"]
    is_admin = current_user["role"] == "admin"
    summary = await AlertService.get_alert_summary(db, user_id, is_admin)
    return summary


@app.get("/alert-rules", response_model=List[AlertRuleRead])
async def get_alert_rules(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    rules = await AlertService.get_alert_rules(db, active_only=False)
    return rules


@app.post("/alert-rules", response_model=AlertRuleRead)
async def create_alert_rule(
    rule: AlertRuleCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")

    existing = await db.execute(
        select(AlertRule).where(AlertRule.rule_code == rule.rule_code)
    )
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="规则编码已存在")

    new_rule = AlertRule(
        rule_code=rule.rule_code,
        rule_name=rule.rule_name,
        rule_type=rule.rule_type,
        entity_type=rule.entity_type,
        priority=rule.priority,
        threshold_days=rule.threshold_days,
        threshold_amount=rule.threshold_amount,
        description=rule.description,
        is_active=rule.is_active,
        created_at=date.today(),
    )
    db.add(new_rule)
    await db.commit()
    await db.refresh(new_rule)
    return new_rule


@app.put("/alert-rules/{rule_id}", response_model=AlertRuleRead)
async def update_alert_rule(
    rule_id: int,
    rule: AlertRuleCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")

    existing = await db.execute(select(AlertRule).where(AlertRule.id == rule_id))
    db_rule = existing.scalars().first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    db_rule.rule_name = rule.rule_name
    db_rule.rule_type = rule.rule_type
    db_rule.entity_type = rule.entity_type
    db_rule.priority = rule.priority
    db_rule.threshold_days = rule.threshold_days
    db_rule.threshold_amount = rule.threshold_amount
    db_rule.description = rule.description
    db_rule.is_active = rule.is_active
    db_rule.updated_at = str(date.today())

    await db.commit()
    await db.refresh(db_rule)
    return db_rule


@app.delete("/alert-rules/{rule_id}")
async def delete_alert_rule(
    rule_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")

    existing = await db.execute(select(AlertRule).where(AlertRule.id == rule_id))
    db_rule = existing.scalars().first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    await db.delete(db_rule)
    await db.commit()
    return {"success": True}


class SalesTargetCreate(BaseModel):
    user_id: int
    target_year: int
    target_amount: float


class SalesTargetRead(BaseModel):
    id: int
    user_id: int
    target_type: str
    target_year: int
    target_period: int
    target_amount: float
    parent_id: Optional[int] = None
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None

    class Config:
        from_attributes = True


class QuarterDecomposeRequest(BaseModel):
    q1: float = 0
    q2: float = 0
    q3: float = 0
    q4: float = 0


@app.get("/sales-targets", response_model=List[SalesTargetRead])
async def get_sales_targets(
    year: Optional[int] = None,
    target_type: Optional[str] = None,
    user_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(SalesTarget)
    if year:
        query = query.where(SalesTarget.target_year == year)
    if target_type:
        query = query.where(SalesTarget.target_type == target_type)
    if user_id:
        query = query.where(SalesTarget.user_id == user_id)
    if current_user["role"] != "admin":
        query = query.where(SalesTarget.user_id == current_user["id"])
    result = await db.execute(query)
    return result.scalars().all()


@app.post("/sales-targets/year", response_model=SalesTargetRead)
async def create_year_target(
    target: SalesTargetCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")

    existing = await db.execute(
        select(SalesTarget).where(
            SalesTarget.user_id == target.user_id,
            SalesTarget.target_type == "yearly",
            SalesTarget.target_year == target.target_year,
        )
    )
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="该用户此年度目标已存在")

    new_target = SalesTarget(
        user_id=target.user_id,
        target_type="yearly",
        target_year=target.target_year,
        target_period=1,
        target_amount=target.target_amount,
        created_at=date.today(),
    )
    db.add(new_target)
    await db.commit()
    await db.refresh(new_target)
    return new_target


@app.post("/sales-targets/{target_id}/decompose-quarterly")
async def decompose_yearly_to_quarterly(
    target_id: int,
    request: QuarterDecomposeRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")

    year_target_result = await db.execute(
        select(SalesTarget).where(SalesTarget.id == target_id)
    )
    year_target = year_target_result.scalars().first()
    if not year_target or year_target.target_type != "yearly":
        raise HTTPException(status_code=404, detail="年目标不存在")

    total = request.q1 + request.q2 + request.q3 + request.q4
    if abs(total - year_target.target_amount) > 0.01:
        raise HTTPException(
            status_code=400,
            detail=f"季度目标总和({total})必须等于年目标({year_target.target_amount})",
        )

    existing_quarters = await db.execute(
        select(SalesTarget).where(
            SalesTarget.parent_id == target_id,
            SalesTarget.target_type == "quarterly",
        )
    )
    if existing_quarters.scalars().first():
        raise HTTPException(status_code=400, detail="该年目标已分解过季度目标")

    quarters = [
        (1, request.q1),
        (2, request.q2),
        (3, request.q3),
        (4, request.q4),
    ]

    created_targets = []
    for q_num, q_amount in quarters:
        q_target = SalesTarget(
            user_id=year_target.user_id,
            target_type="quarterly",
            target_year=year_target.target_year,
            target_period=q_num,
            target_amount=q_amount,
            parent_id=year_target.id,
            created_at=date.today(),
        )
        db.add(q_target)
        await db.flush()

        m_amount = round(q_amount / 3, 2)
        start_month = (q_num - 1) * 3 + 1
        for m_offset in range(3):
            m_target = SalesTarget(
                user_id=year_target.user_id,
                target_type="monthly",
                target_year=year_target.target_year,
                target_period=start_month + m_offset,
                target_amount=m_amount,
                parent_id=q_target.id,
                created_at=date.today(),
            )
            db.add(m_target)

        created_targets.append(q_target)

    await db.commit()
    return {
        "success": True,
        "created_quarterly": len(created_targets),
        "created_monthly": len(created_targets) * 3,
    }


@app.get("/sales-targets/{target_id}/children")
async def get_target_children(
    target_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SalesTarget).where(SalesTarget.id == target_id))
    target = result.scalars().first()
    if not target:
        raise HTTPException(status_code=404, detail="目标不存在")

    children_result = await db.execute(
        select(SalesTarget)
        .where(SalesTarget.parent_id == target_id)
        .order_by(SalesTarget.target_period)
    )
    children = children_result.scalars().all()

    return {
        "parent": {
            "id": target.id,
            "target_type": target.target_type,
            "target_amount": target.target_amount,
        },
        "children": [
            {
                "id": c.id,
                "target_type": c.target_type,
                "target_period": c.target_period,
                "target_amount": c.target_amount,
                "has_children": c.target_type == "quarterly",
            }
            for c in children
        ],
    }


@app.get("/sales-targets/yearly-with-status")
async def get_yearly_targets_with_status(
    year: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(SalesTarget).where(SalesTarget.target_type == "yearly")
    if year:
        query = query.where(SalesTarget.target_year == year)
    if current_user["role"] != "admin":
        query = query.where(SalesTarget.user_id == current_user["id"])
    result = await db.execute(query)
    year_targets = result.scalars().all()

    response = []
    for yt in year_targets:
        children_result = await db.execute(
            select(SalesTarget).where(SalesTarget.parent_id == yt.id)
        )
        children = children_result.scalars().all()
        response.append(
            {
                "id": yt.id,
                "user_id": yt.user_id,
                "target_year": yt.target_year,
                "target_amount": yt.target_amount,
                "decomposed": len(children) > 0,
                "quarterly_count": len(
                    [c for c in children if c.target_type == "quarterly"]
                ),
                "monthly_count": len(
                    [c for c in children if c.target_type == "monthly"]
                ),
                "created_at": str(yt.created_at) if yt.created_at else None,
            }
        )
    return response


@app.put("/sales-targets/{target_id}", response_model=SalesTargetRead)
async def update_sales_target(
    target_id: int,
    target: SalesTargetCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")

    existing = await db.execute(select(SalesTarget).where(SalesTarget.id == target_id))
    db_target = existing.scalars().first()
    if not db_target:
        raise HTTPException(status_code=404, detail="目标不存在")

    db_target.target_amount = target.target_amount
    db_target.updated_at = str(date.today())

    await db.commit()
    await db.refresh(db_target)
    return db_target


@app.delete("/sales-targets/{target_id}")
async def delete_sales_target(
    target_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")

    existing = await db.execute(select(SalesTarget).where(SalesTarget.id == target_id))
    db_target = existing.scalars().first()
    if not db_target:
        raise HTTPException(status_code=404, detail="目标不存在")

    await db.delete(db_target)
    await db.commit()
    return {"success": True}


# ==================== Dispatch Integration API ====================

# ==================== Pydantic Schemas ====================


class DispatchRecordBase(BaseModel):
    work_order_id: str
    work_order_no: Optional[str]
    source_type: str
    status: str = "pending"
    order_type: Optional[str]
    customer_name: Optional[str]
    priority: Optional[str]
    description: Optional[str]


class DispatchRecordRead(DispatchRecordBase):
    id: int
    lead_id: Optional[int]
    opportunity_id: Optional[int]
    project_id: Optional[int]
    previous_status: Optional[str]
    status_updated_at: Optional[datetime]
    created_at: datetime
    dispatched_at: Optional[datetime]
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class DispatchWebhookPayload(BaseModel):
    event: str
    work_order_id: str
    work_order_no: Optional[str]
    status: str
    previous_status: Optional[str]
    timestamp: str
    metadata: Optional[dict] = None


class DispatchApplicationRequest(BaseModel):
    dispatch_api_url: str
    dispatch_token: str


class DispatchApplicationResponse(BaseModel):
    success: bool
    message: str
    work_order_id: Optional[str] = None
    work_order_no: Optional[str] = None


@app.post(
    "/leads/{lead_id}/create-dispatch", response_model=DispatchApplicationResponse
)
async def create_dispatch_from_lead(
    lead_id: int,
    request: DispatchApplicationRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a dispatch work order from a Lead."""
    # Get the lead
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Initialize dispatch service
    dispatch_service = DispatchIntegrationService(request.dispatch_api_url)

    try:
        # Get customer data from lead
        crm_data = await dispatch_service.get_customer_data_from_lead(db, lead)

        # Transform to work order format
        work_order_data = dispatch_service.transform_crm_to_work_order(
            "lead", crm_data, request.dispatch_token
        )

        # Create work order in dispatch system
        response = await dispatch_service.create_work_order(
            work_order_data, request.dispatch_token
        )

        work_order_id = response.get("id")
        work_order_no = response.get("orderNo")

        # Save dispatch record
        await dispatch_service.save_dispatch_record(
            db=db,
            work_order_id=work_order_id or "",
            work_order_no=work_order_no,
            source_type="lead",
            source_id=lead.id,
            customer_name=crm_data.get("customer_name"),
            priority=work_order_data.get("priority"),
            order_type=work_order_data.get("orderType"),
            description=work_order_data.get("description"),
            dispatch_data=work_order_data,
        )

        await dispatch_service.close()

        return DispatchApplicationResponse(
            success=True,
            message="Dispatch work order created successfully",
            work_order_id=work_order_id,
            work_order_no=work_order_no,
        )

    except DispatchIntegrationError as e:
        await dispatch_service.close()
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)
    except Exception as e:
        await dispatch_service.close()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.post(
    "/opportunities/{opportunity_id}/create-dispatch",
    response_model=DispatchApplicationResponse,
)
async def create_dispatch_from_opportunity(
    opportunity_id: int,
    request: DispatchApplicationRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a dispatch work order from an Opportunity."""
    # Get the opportunity
    result = await db.execute(
        select(Opportunity).where(Opportunity.id == opportunity_id)
    )
    opportunity = result.scalar_one_or_none()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    # Initialize dispatch service
    dispatch_service = DispatchIntegrationService(request.dispatch_api_url)

    try:
        # Get customer data from opportunity
        crm_data = await dispatch_service.get_customer_data_from_opportunity(
            db, opportunity
        )

        # Transform to work order format
        work_order_data = dispatch_service.transform_crm_to_work_order(
            "opportunity", crm_data, request.dispatch_token
        )

        # Create work order in dispatch system
        response = await dispatch_service.create_work_order(
            work_order_data, request.dispatch_token
        )

        work_order_id = response.get("id")
        work_order_no = response.get("orderNo")

        # Save dispatch record
        await dispatch_service.save_dispatch_record(
            db=db,
            work_order_id=work_order_id or "",
            work_order_no=work_order_no,
            source_type="opportunity",
            source_id=opportunity.id,
            customer_name=crm_data.get("customer_name"),
            priority=work_order_data.get("priority"),
            order_type=work_order_data.get("orderType"),
            description=work_order_data.get("description"),
            dispatch_data=work_order_data,
        )

        await dispatch_service.close()

        return DispatchApplicationResponse(
            success=True,
            message="Dispatch work order created successfully",
            work_order_id=work_order_id,
            work_order_no=work_order_no,
        )

    except DispatchIntegrationError as e:
        await dispatch_service.close()
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)
    except Exception as e:
        await dispatch_service.close()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.post(
    "/projects/{project_id}/create-dispatch", response_model=DispatchApplicationResponse
)
async def create_dispatch_from_project(
    project_id: int,
    request: DispatchApplicationRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a dispatch work order from a Project."""
    # Get the project
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Initialize dispatch service
    dispatch_service = DispatchIntegrationService(request.dispatch_api_url)

    try:
        # Get customer data from project
        crm_data = await dispatch_service.get_customer_data_from_project(db, project)

        # Transform to work order format
        work_order_data = dispatch_service.transform_crm_to_work_order(
            "project", crm_data, request.dispatch_token
        )

        # Create work order in dispatch system
        response = await dispatch_service.create_work_order(
            work_order_data, request.dispatch_token
        )

        work_order_id = response.get("id")
        work_order_no = response.get("orderNo")

        # Save dispatch record
        await dispatch_service.save_dispatch_record(
            db=db,
            work_order_id=work_order_id or "",
            work_order_no=work_order_no,
            source_type="project",
            source_id=project.id,
            customer_name=crm_data.get("customer_name"),
            priority=work_order_data.get("priority"),
            order_type=work_order_data.get("orderType"),
            description=work_order_data.get("description"),
            dispatch_data=work_order_data,
        )

        await dispatch_service.close()

        return DispatchApplicationResponse(
            success=True,
            message="Dispatch work order created successfully",
            work_order_id=work_order_id,
            work_order_no=work_order_no,
        )

    except DispatchIntegrationError as e:
        await dispatch_service.close()
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)
    except Exception as e:
        await dispatch_service.close()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")




# ==================== Webhook Endpoint ====================


@app.post("/webhooks/dispatch")
async def dispatch_webhook(
    request: Request,
    payload: DispatchWebhookPayload,
    db: AsyncSession = Depends(get_db),
):
    """Handle webhook events from dispatch system."""
    # Verify webhook signature
    dispatch_webhook_secret = os.environ.get("DISPATCH_WEBHOOK_SECRET")
    if not dispatch_webhook_secret:
        raise HTTPException(
            status_code=500, detail="DISPATCH_WEBHOOK_SECRET not configured"
        )

    # Get signature from headers
    signature = request.headers.get("X-Dispatch-Signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing X-Dispatch-Signature header")

    # Compute HMAC-SHA256 signature
    import hmac
    import hashlib

    # Get raw request body for signature verification
    body = await request.body()
    expected_signature = hmac.new(
        dispatch_webhook_secret.encode(), body, hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # Find existing dispatch record or create new one
    from app.models.dispatch_record import DispatchRecord
    from sqlalchemy import or_

    result = await db.execute(
        select(DispatchRecord).where(
            DispatchRecord.work_order_id == payload.work_order_id
        )
    )
    dispatch_record = result.scalar_one_or_none()

    try:
        if not dispatch_record:
            # Create new dispatch record from webhook payload
            # Try to find linked entity by metadata
            dispatch_record = DispatchRecord(
                work_order_id=payload.work_order_id,
                work_order_no=payload.work_order_no,
                source_type=payload.metadata.get("source_type", "unknown")
                if payload.metadata
                else "unknown",
                status=payload.status,
                previous_status=payload.previous_status,
                status_updated_at=datetime.utcnow(),
                order_type=payload.metadata.get("order_type")
                if payload.metadata
                else None,
                dispatch_data=payload.model_dump(),
            )
            db.add(dispatch_record)

        else:
            # Update existing record
            dispatch_record.status = payload.status
            dispatch_record.previous_status = payload.previous_status
            dispatch_record.status_updated_at = datetime.utcnow()
            dispatch_record.work_order_no = payload.work_order_no

            # Update dispatch_data with latest info
            if dispatch_record.dispatch_data:
                dispatch_record.dispatch_data.update(payload.model_dump())
            else:
                dispatch_record.dispatch_data = payload.model_dump()

        await db.commit()
        await db.refresh(dispatch_record)

        return {"success": True, "message": "Webhook processed successfully"}

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to process webhook: {str(e)}")


# ==================== Dispatch History API Endpoints ====================


@app.get("/leads/{lead_id}/dispatch-history", response_model=List[DispatchRecordRead])
async def get_lead_dispatch_history(
    lead_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get dispatch records for a lead."""
    result = await db.execute(
        select(DispatchRecord)
        .where(DispatchRecord.lead_id == lead_id)
        .order_by(DispatchRecord.created_at.desc())
    )
    records = result.scalars().all()
    return records


@app.get(
    "/opportunities/{opportunity_id}/dispatch-history",
    response_model=List[DispatchRecordRead],
)
async def get_opportunity_dispatch_history(
    opportunity_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get dispatch records for an opportunity."""
    result = await db.execute(
        select(DispatchRecord)
        .where(DispatchRecord.opportunity_id == opportunity_id)
        .order_by(DispatchRecord.created_at.desc())
    )
    records = result.scalars().all()
    return records


@app.get(
    "/projects/{project_id}/dispatch-history", response_model=List[DispatchRecordRead]
)
async def get_project_dispatch_history(
    project_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get dispatch records for a project."""
    result = await db.execute(
        select(DispatchRecord)
        .where(DispatchRecord.project_id == project_id)
        .order_by(DispatchRecord.created_at.desc())
    )
    records = result.scalars().all()
    return records


@app.get("/dispatch-records", response_model=List[DispatchRecordRead])
async def list_dispatch_records(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all dispatch records (admin only)."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can list all dispatch records")

    result = await db.execute(
        select(DispatchRecord).order_by(DispatchRecord.created_at.desc())
    )
    records = result.scalars().all()
    return records


@app.get(
    "/dispatch-records/{record_id}", response_model=DispatchRecordRead
)
async def get_dispatch_record(
    record_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get single dispatch record details."""
    result = await db.execute(
        select(DispatchRecord).where(DispatchRecord.id == record_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Dispatch record not found")
    return record
