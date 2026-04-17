from fastapi import FastAPI, Depends, HTTPException, status, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, validator, ConfigDict, computed_field
from typing import List, Optional, Any
from datetime import datetime, timedelta, date
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import os
from dotenv import load_dotenv
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ENV_PATH)

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
from app.models.nine_a_version import NineAVersion
from app.models.notification import Notification
from app.models.user_notification_read import UserNotificationRead
from app.models.alert_rule import AlertRule
from app.models.sales_target import SalesTarget
from app.models.dispatch_record import DispatchRecord
from app.models.work_order import WorkOrder, WorkOrderTechnician
from app.models.product_installation import ProductInstallation
from app.schemas.finance_view import CustomerFinanceView
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
from app.services.local_dispatch_service import LocalDispatchService
from app.models.work_order import WorkOrder, WorkOrderStatus
from app.models.channel_assignment import ChannelAssignment
from app.models.execution_plan import ExecutionPlan
from app.models.unified_target import UnifiedTarget
from app.models.customer_channel_link import CustomerChannelLink
from app.core.channel_permissions import assert_can_access_channel

# Import routers for channel management module
from app.routers.channel import router as channel_router
from app.routers.channel_assignment import router as channel_assignment_router
from app.routers.unified_target import router as unified_target_router
from app.routers.execution_plan import router as execution_plan_router
from app.routers.work_order import router as work_order_router
from app.routers.evaluation import router as evaluation_router
from app.routers.knowledge import router as knowledge_router
from app.routers.product_installation import router as product_installation_router

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


async def check_technician_access(
    db: AsyncSession, user_id: int, user_role: str, entity_type: str, entity_id: int
):
    """Check technician access to lead/opportunity/project via work order assignment.

    This function only handles technician role. Other roles should be handled
    separately with appropriate data scope checks.
    """
    if user_role != "technician":
        return

    stmt = select(WorkOrder)
    if entity_type == "lead":
        stmt = stmt.where(WorkOrder.lead_id == entity_id)
    elif entity_type == "opportunity":
        stmt = stmt.where(WorkOrder.opportunity_id == entity_id)
    elif entity_type == "project":
        stmt = stmt.where(WorkOrder.project_id == entity_id)
    else:
        raise HTTPException(status_code=403, detail="无权限访问此记录")

    result = await db.execute(stmt)
    work_orders = result.scalars().all()

    has_access = False
    for wo in work_orders:
        tech_stmt = select(WorkOrderTechnician).where(
            WorkOrderTechnician.work_order_id == wo.id,
            WorkOrderTechnician.technician_id == user_id,
        )
        tech_result = await db.execute(tech_stmt)
        if tech_result.scalar_one_or_none():
            has_access = True
            break

    if not has_access:
        raise HTTPException(
            status_code=403, detail="您没有权限访问此记录（未关联相关工单）"
        )


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

app.include_router(channel_router)
app.include_router(channel_assignment_router)
app.include_router(unified_target_router)
app.include_router(execution_plan_router)
app.include_router(work_order_router)
app.include_router(evaluation_router)
app.include_router(knowledge_router)
app.include_router(product_installation_router)


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
    expected_contract_amount: float
    expected_close_date: Optional[str] = None
    sales_owner_id: int
    channel_id: Optional[int] = None
    vendor_registration_status: Optional[str] = None
    vendor_discount: Optional[float] = None
    loss_reason: Optional[str] = None
    product_ids: Optional[List[int]] = None
    products: Optional[List[str]] = None


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
    products: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)


class OpportunityUpdate(BaseModel):
    opportunity_name: Optional[str] = None
    terminal_customer_id: Optional[int] = None
    opportunity_source: Optional[str] = None
    opportunity_stage: Optional[str] = None
    expected_contract_amount: Optional[float] = None
    expected_close_date: Optional[str] = None
    sales_owner_id: Optional[int] = None
    channel_id: Optional[int] = None
    vendor_registration_status: Optional[str] = None
    vendor_discount: Optional[float] = None
    loss_reason: Optional[str] = None
    product_ids: Optional[List[int]] = None
    products: Optional[List[str]] = None
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
    products: Optional[List[str]] = None
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
    products: Optional[List[str]] = None

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
    products: Optional[List[str]] = None
    channel_id: Optional[int] = None
    source_opportunity_id: Optional[int] = None
    gross_margin: Optional[float] = None


class LeadBase(BaseModel):
    lead_name: str
    terminal_customer_id: int
    channel_id: Optional[int] = None
    source_channel_id: Optional[int] = None
    lead_stage: str = "初步接触"
    lead_source: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    products: Optional[List[str]] = None
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
    channel_id: Optional[int] = None
    channel_name: Optional[str] = None
    source_channel_id: Optional[int] = None
    source_channel_name: Optional[str] = None
    lead_stage: str
    lead_source: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    products: Optional[List[str]] = None
    estimated_budget: Optional[float] = None
    has_confirmed_requirement: bool = False
    has_confirmed_budget: bool = False
    converted_to_opportunity: bool = False
    opportunity_id: Optional[int] = None
    sales_owner_id: int
    notes: Optional[str] = None
    created_at: Optional[date] = None
    updated_at: Optional[date] = None
    terminal_customer_name: Optional[str] = None
    sales_owner_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LeadUpdate(BaseModel):
    lead_name: Optional[str] = None
    terminal_customer_id: Optional[int] = None
    channel_id: Optional[int] = None
    source_channel_id: Optional[int] = None  # 来源渠道原则上不可修改
    lead_stage: Optional[str] = None
    lead_source: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    products: Optional[List[str]] = None
    estimated_budget: Optional[float] = None
    has_confirmed_requirement: Optional[bool] = None
    has_confirmed_budget: Optional[bool] = None
    sales_owner_id: Optional[int] = None
    notes: Optional[str] = None


class LeadConvertRequest(BaseModel):
    opportunity_name: str
    expected_contract_amount: float
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
    functional_role: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(User)
    if functional_role:
        query = query.where(User.functional_role == functional_role)
    result = await db.execute(query)
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
    user_role = current_user.get("role")
    user_id = current_user["id"]

    stmt = select(TerminalCustomer).options(
        selectinload(TerminalCustomer.owner), selectinload(TerminalCustomer.channel)
    )

    if user_role == "admin" or user_role in ["business", "finance"]:
        pass
    elif user_role == "sales":
        stmt = stmt.where(TerminalCustomer.customer_owner_id == user_id)
    elif user_role == "technician":
        from app.models.channel_assignment import ChannelAssignment

        customer_ids_from_work_orders = select(WorkOrder.lead_id).where(
            WorkOrder.lead_id.isnot(None),
            WorkOrder.id.in_(
                select(WorkOrderTechnician.work_order_id).where(
                    WorkOrderTechnician.technician_id == user_id
                )
            ),
        )
        customer_ids_from_leads = select(Lead.terminal_customer_id).where(
            Lead.id.in_(customer_ids_from_work_orders)
        )

        opp_customer_ids = select(WorkOrder.opportunity_id).where(
            WorkOrder.opportunity_id.isnot(None),
            WorkOrder.id.in_(
                select(WorkOrderTechnician.work_order_id).where(
                    WorkOrderTechnician.technician_id == user_id
                )
            ),
        )
        customer_ids_from_opps = select(Opportunity.terminal_customer_id).where(
            Opportunity.id.in_(opp_customer_ids)
        )

        proj_customer_ids = select(WorkOrder.project_id).where(
            WorkOrder.project_id.isnot(None),
            WorkOrder.id.in_(
                select(WorkOrderTechnician.work_order_id).where(
                    WorkOrderTechnician.technician_id == user_id
                )
            ),
        )
        customer_ids_from_projs = select(Project.terminal_customer_id).where(
            Project.id.in_(proj_customer_ids)
        )

        stmt = stmt.where(
            or_(
                TerminalCustomer.id.in_(customer_ids_from_leads),
                TerminalCustomer.id.in_(customer_ids_from_opps),
                TerminalCustomer.id.in_(customer_ids_from_projs),
            )
        )
    else:
        stmt = stmt.where(False)

    result = await db.execute(stmt)
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
    try:
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
            "id": new_customer.id,
            "customer_code": new_customer.customer_code,
            "customer_name": new_customer.customer_name,
            "credit_code": new_customer.credit_code,
            "customer_industry": new_customer.customer_industry,
            "customer_region": new_customer.customer_region,
            "customer_owner_id": new_customer.customer_owner_id,
            "channel_id": new_customer.channel_id,
            "main_contact": new_customer.main_contact,
            "phone": new_customer.phone,
            "customer_status": new_customer.customer_status,
            "maintenance_expiry": new_customer.maintenance_expiry,
            "notes": new_customer.notes,
            "customer_owner_name": new_customer.owner.name
            if new_customer.owner
            else None,
            "channel_name": new_customer.channel.company_name
            if new_customer.channel
            else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        import logging

        logger = logging.getLogger("uvicorn.error")
        logger.error(f"Error creating customer: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"创建客户失败: {str(e)}")


@app.put("/customers/{customer_id}", response_model=CustomerRead)
async def update_customer(
    customer_id: int,
    customer: CustomerCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.core.permissions import assert_can_mutate_entity_v2

    result = await db.execute(
        select(TerminalCustomer).where(TerminalCustomer.id == customer_id)
    )
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Customer not found")

    await assert_can_mutate_entity_v2(existing, current_user, db)

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
    from app.core.permissions import assert_can_mutate_entity_v2

    result = await db.execute(
        select(TerminalCustomer).where(TerminalCustomer.id == customer_id)
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    await assert_can_mutate_entity_v2(customer, current_user, db)

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
    user_role = current_user.get("role")
    user_id = current_user["id"]

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

    if user_role == "admin" or user_role == "business":
        pass
    elif user_role == "finance":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="财务角色请使用 /customers/{id}/finance-view 接口",
        )
    elif user_role == "sales":
        if customer.customer_owner_id != user_id:
            raise HTTPException(status_code=403, detail="无权限访问此客户")
    elif user_role == "technician":
        from sqlalchemy import and_ as sql_and

        has_access_stmt = select(WorkOrder).where(
            sql_and(
                or_(
                    WorkOrder.lead_id.in_(
                        select(Lead.id).where(Lead.terminal_customer_id == customer_id)
                    ),
                    WorkOrder.opportunity_id.in_(
                        select(Opportunity.id).where(
                            Opportunity.terminal_customer_id == customer_id
                        )
                    ),
                    WorkOrder.project_id.in_(
                        select(Project.id).where(
                            Project.terminal_customer_id == customer_id
                        )
                    ),
                ),
                WorkOrder.id.in_(
                    select(WorkOrderTechnician.work_order_id).where(
                        WorkOrderTechnician.technician_id == user_id
                    )
                ),
            )
        )
        has_access_result = await db.execute(has_access_stmt)
        if not has_access_result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="无权限访问此客户")
    else:
        raise HTTPException(status_code=403, detail="无权限访问客户数据")

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


@app.get("/customers/{customer_id}/finance-view", response_model=CustomerFinanceView)
async def get_customer_finance_view(
    customer_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Finance-specific customer view for finance role users.

    Returns only financial data: contracts, payment plans, project financials.
    Excludes sensitive business data (leads, opportunities, follow-ups, sales_owner names).

    Access: admin and finance only.
    """
    from app.services.finance_view_service import finance_view_service

    user_role = current_user.get("role")
    if user_role not in ["admin", "finance"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="财务视图仅限管理员和财务角色访问",
        )

    finance_view = await finance_view_service.get_customer_finance_view(customer_id, db)
    if not finance_view:
        raise HTTPException(status_code=404, detail="客户不存在")

    return finance_view


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
    from app.core.dependencies import apply_data_scope_filter

    query = select(Lead).options(
        selectinload(Lead.terminal_customer),
        selectinload(Lead.sales_owner),
        selectinload(Lead.channel),
        selectinload(Lead.source_channel),
    )
    query = apply_data_scope_filter(query, Lead, current_user, db)

    result = await db.execute(query)
    leads = result.scalars().all()
    # 手动填充名称字段
    lead_reads = []
    for lead in leads:
        lead_dict = {
            "id": lead.id,
            "lead_code": lead.lead_code,
            "lead_name": lead.lead_name,
            "terminal_customer_id": lead.terminal_customer_id,
            "terminal_customer_name": lead.terminal_customer.customer_name
            if lead.terminal_customer
            else None,
            "channel_id": lead.channel_id,
            "channel_name": lead.channel.company_name if lead.channel else None,
            "source_channel_id": lead.source_channel_id,
            "source_channel_name": lead.source_channel.company_name
            if lead.source_channel
            else None,
            "lead_stage": lead.lead_stage,
            "lead_source": lead.lead_source,
            "contact_person": lead.contact_person,
            "contact_phone": lead.contact_phone,
            "products": lead.products,
            "estimated_budget": lead.estimated_budget,
            "has_confirmed_requirement": lead.has_confirmed_requirement,
            "has_confirmed_budget": lead.has_confirmed_budget,
            "converted_to_opportunity": lead.converted_to_opportunity,
            "opportunity_id": lead.opportunity_id,
            "sales_owner_id": lead.sales_owner_id,
            "sales_owner_name": lead.sales_owner.name if lead.sales_owner else None,
            "notes": lead.notes,
            "created_at": lead.created_at,
            "updated_at": lead.updated_at,
        }
        lead_reads.append(lead_dict)
    return lead_reads


@app.get("/leads/{lead_id}", response_model=LeadRead)
async def get_lead(
    lead_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_role = current_user.get("role")
    user_id = current_user["id"]

    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if user_role == "admin":
        return lead

    if user_role == "sales":
        if lead.sales_owner_id != user_id:
            raise HTTPException(status_code=403, detail="无权限访问此线索")
        return lead

    if user_role == "technician":
        await check_technician_access(db, user_id, user_role, "lead", lead_id)
        return lead

    raise HTTPException(status_code=403, detail="无权限访问线索数据")


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
        channel_id=lead.channel_id,
        source_channel_id=lead.source_channel_id,
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
    from app.core.permissions import assert_can_mutate_entity_v2

    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Lead not found")

    await assert_can_mutate_entity_v2(existing, current_user, db)

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
    from app.core.permissions import assert_can_mutate_entity_v2

    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    await assert_can_mutate_entity_v2(lead, current_user, db)

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
        channel_id=lead.channel_id,
        opportunity_source=convert_request.opportunity_source
        or lead.lead_source
        or "线索转化",
        opportunity_stage="需求方案",
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
    from app.core.dependencies import apply_data_scope_filter

    query = select(Opportunity).options(
        selectinload(Opportunity.terminal_customer),
        selectinload(Opportunity.sales_owner),
        selectinload(Opportunity.channel),
    )
    query = apply_data_scope_filter(query, Opportunity, current_user, db)

    result = await db.execute(query)
    opportunities = result.scalars().all()
    # 手动填充名称字段
    opp_reads = []
    for opp in opportunities:
        opp_dict = {
            "id": opp.id,
            "opportunity_code": opp.opportunity_code,
            "opportunity_name": opp.opportunity_name,
            "terminal_customer_id": opp.terminal_customer_id,
            "terminal_customer_name": opp.terminal_customer.customer_name
            if opp.terminal_customer
            else None,
            "opportunity_source": opp.opportunity_source,
            "opportunity_stage": opp.opportunity_stage,
            "products": opp.products,
            "expected_contract_amount": opp.expected_contract_amount,
            "expected_close_date": opp.expected_close_date,
            "sales_owner_id": opp.sales_owner_id,
            "sales_owner_name": opp.sales_owner.name if opp.sales_owner else None,
            "channel_id": opp.channel_id,
            "channel_name": opp.channel.company_name if opp.channel else None,
            "project_id": opp.project_id,
            "loss_reason": opp.loss_reason,
            "created_at": opp.created_at,
        }
        opp_reads.append(opp_dict)
    return opp_reads


@app.get("/opportunities/{opportunity_id}", response_model=OpportunityRead)
async def get_opportunity(
    opportunity_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_role = current_user.get("role")
    user_id = current_user["id"]

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

    if user_role == "admin" or user_role == "business":
        pass
    elif user_role == "sales":
        if opportunity.sales_owner_id != user_id:
            raise HTTPException(status_code=403, detail="无权限访问此商机")
    elif user_role == "technician":
        await check_technician_access(
            db, user_id, user_role, "opportunity", opportunity_id
        )
    else:
        raise HTTPException(status_code=403, detail="无权限访问商机数据")

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
    from app.core.permissions import assert_can_mutate_entity_v2

    result = await db.execute(
        select(Opportunity).where(Opportunity.id == opportunity_id)
    )
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    await assert_can_mutate_entity_v2(existing, current_user, db)

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
    from app.core.permissions import assert_can_mutate_entity_v2

    result = await db.execute(
        select(Opportunity).where(Opportunity.id == opportunity_id)
    )
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    await assert_can_mutate_entity_v2(existing, current_user, db)

    await db.delete(existing)
    await db.commit()
    return {"message": "Opportunity deleted successfully"}

    await db.commit()
    await db.refresh(existing)
    return existing


@app.get("/projects", response_model=List[ProjectRead])
async def list_projects(
    current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    from app.core.dependencies import apply_data_scope_filter

    query = select(Project).options(
        selectinload(Project.terminal_customer),
        selectinload(Project.sales_owner),
    )
    query = apply_data_scope_filter(query, Project, current_user, db)

    result = await db.execute(query)
    projects = result.scalars().all()

    project_reads = []
    for proj in projects:
        proj_dict = {
            "id": proj.id,
            "project_code": proj.project_code,
            "project_name": proj.project_name,
            "terminal_customer_id": proj.terminal_customer_id,
            "terminal_customer_name": proj.terminal_customer.customer_name
            if proj.terminal_customer
            else None,
            "sales_owner_id": proj.sales_owner_id,
            "sales_owner_name": proj.sales_owner.name if proj.sales_owner else None,
            "channel_id": proj.channel_id,
            "channel_name": proj.channel.company_name if proj.channel else None,
            "source_opportunity_id": proj.source_opportunity_id,
            "business_type": proj.business_type,
            "project_status": proj.project_status,
            "products": proj.products,
            "downstream_contract_amount": proj.downstream_contract_amount,
            "upstream_procurement_amount": proj.upstream_procurement_amount,
            "gross_margin": proj.gross_margin,
            "direct_project_investment": proj.direct_project_investment,
            "additional_investment": proj.additional_investment,
            "winning_date": proj.winning_date,
            "acceptance_date": proj.acceptance_date,
            "notes": proj.notes,
            "created_at": proj.created_at,
        }
        project_reads.append(proj_dict)
    return project_reads


@app.post("/projects", response_model=ProjectRead)
async def create_project(
    project: ProjectCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.auto_number_service import generate_code

    project_code = await generate_code(db, "PJ")
    gross_margin = (project.downstream_contract_amount or 0) - (
        project.upstream_procurement_amount or 0
    )

    new_project = Project(
        project_code=project_code,
        gross_margin=gross_margin,
        **project.model_dump(),
    )
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)

    return {
        "id": new_project.id,
        "project_code": new_project.project_code,
        "project_name": new_project.project_name,
        "terminal_customer_id": new_project.terminal_customer_id,
        "terminal_customer_name": None,
        "sales_owner_id": new_project.sales_owner_id,
        "sales_owner_name": None,
        "channel_id": new_project.channel_id,
        "channel_name": None,
        "source_opportunity_id": new_project.source_opportunity_id,
        "business_type": new_project.business_type,
        "project_status": new_project.project_status,
        "products": new_project.products,
        "downstream_contract_amount": new_project.downstream_contract_amount,
        "upstream_procurement_amount": new_project.upstream_procurement_amount,
        "gross_margin": new_project.gross_margin,
        "direct_project_investment": new_project.direct_project_investment,
        "additional_investment": new_project.additional_investment,
        "winning_date": new_project.winning_date,
        "acceptance_date": new_project.acceptance_date,
        "notes": new_project.notes,
        "created_at": new_project.created_at,
    }


@app.delete("/projects/{project_id}")
async def delete_project(
    project_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.core.permissions import assert_can_mutate_entity_v2

    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    await assert_can_mutate_entity_v2(project, current_user, db)

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

    if existing.contract_status == "signed" and existing.channel_id:
        from app.services.channel_performance_service import refresh_channel_performance

        await refresh_channel_performance(db, existing.channel_id)

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


class ChannelFullView(BaseModel):
    channel: dict
    summary: dict
    customers: List[dict]
    opportunities: List[dict]
    projects: List[dict]
    contracts: List[dict]
    work_orders: List[dict]
    assignments: List[dict]
    execution_plans: List[dict]
    targets: List[dict]


@app.get("/channels/{channel_id}/full-view", response_model=ChannelFullView)
async def get_channel_full_view(
    channel_id: int,
    year: Optional[int] = Query(None, description="过滤年份"),
    quarter: Optional[int] = Query(None, ge=1, le=4, description="过滤季度"),
    active_only: bool = Query(True, description="只显示活跃记录"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await assert_can_access_channel(db, current_user, channel_id, "read")

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

    work_orders_result = await db.execute(
        select(WorkOrder).where(WorkOrder.channel_id == channel_id)
    )
    work_orders_rows = work_orders_result.all()
    work_orders = []
    for row in work_orders_rows:
        wo = row[0]
        work_orders.append(
            {
                "id": wo.id,
                "work_order_no": wo.work_order_no,
                "order_type": wo.order_type.value if wo.order_type else None,
                "status": wo.status.value if wo.status else None,
                "description": wo.description,
                "customer_name": wo.customer_name,
            }
        )

    assignments_result = await db.execute(
        select(ChannelAssignment, User.name)
        .outerjoin(User, ChannelAssignment.user_id == User.id)
        .where(ChannelAssignment.channel_id == channel_id)
    )
    assignments_rows = assignments_result.all()
    assignments = []
    for row in assignments_rows:
        assignment = row[0]
        user_name = row[1]
        assignments.append(
            {
                "id": assignment.id,
                "user_id": assignment.user_id,
                "user_name": user_name,
                "permission_level": assignment.permission_level.value
                if assignment.permission_level
                else None,
                "assigned_at": str(assignment.assigned_at)
                if assignment.assigned_at
                else None,
            }
        )

    execution_plans_query = (
        select(ExecutionPlan, User.name)
        .outerjoin(User, ExecutionPlan.user_id == User.id)
        .where(ExecutionPlan.channel_id == channel_id)
    )

    if active_only:
        execution_plans_query = execution_plans_query.where(
            ExecutionPlan.status.in_(["in-progress", "planned"])
        )

    if active_only:
        execution_plans_query = execution_plans_query.where(
            ExecutionPlan.status.in_(["in-progress", "planned"])
        )

    execution_plans_result = await db.execute(execution_plans_query)
    execution_plans_rows = execution_plans_result.all()
    execution_plans = []
    for row in execution_plans_rows:
        plan = row[0]
        user_name = row[1]
        execution_plans.append(
            {
                "id": plan.id,
                "plan_type": plan.plan_type.value if plan.plan_type else None,
                "plan_period": plan.plan_period,
                "plan_content": plan.plan_content,
                "status": plan.status.value if plan.status else None,
            }
        )

    targets_query = select(UnifiedTarget).where(UnifiedTarget.channel_id == channel_id)
    if year is not None:
        targets_query = targets_query.where(UnifiedTarget.year == year)

    targets_result = await db.execute(targets_query)
    targets_rows = targets_result.all()
    targets = []
    for row in targets_rows:
        target = row[0]
        targets.append(
            {
                "id": target.id,
                "year": target.year,
                "quarter": target.quarter,
                "month": target.month,
                "performance_target": float(target.performance_target)
                if target.performance_target
                else None,
                "achieved_performance": float(target.achieved_performance)
                if target.achieved_performance
                else None,
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
            "work_orders_count": len(work_orders),
            "assignments_count": len(assignments),
            "execution_plans_count": len(execution_plans),
            "targets_count": len(targets),
            "total_contract_amount": sum(c.contract_amount or 0 for c in contracts),
            "active_plans_count": len(
                [
                    p
                    for p in execution_plans
                    if p["status"] in ["in-progress", "planned"]
                ]
            ),
        },
        customers=customers,
        opportunities=opportunities,
        projects=projects,
        contracts=contracts,
        work_orders=work_orders,
        assignments=assignments,
        execution_plans=execution_plans,
        targets=targets,
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


@app.get("/dict-items/brands")
async def list_brands(
    product_type_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(DictItem).where(
        DictItem.dict_type.in_(["brand", "product_brand", "产品品牌"])
    )
    if product_type_id is not None:
        # Check if this is a level-1 category (no parent_id)
        type_item = await db.execute(
            select(DictItem).where(DictItem.id == product_type_id)
        )
        type_result = type_item.scalar_one_or_none()

        if type_result and type_result.parent_id is None:
            # Level-1 category: get all child category IDs
            child_types = await db.execute(
                select(DictItem.id).where(DictItem.parent_id == product_type_id)
            )
            child_ids = [row[0] for row in child_types.fetchall()]
            # Also include the parent itself for direct brands
            all_ids = child_ids + [product_type_id]
            query = query.where(DictItem.parent_id.in_(all_ids))
        else:
            # Level-2 category or specific ID: direct query
            query = query.where(DictItem.parent_id == product_type_id)

    query = query.where(DictItem.is_active == True).order_by(
        DictItem.sort_order, DictItem.id
    )
    result = await db.execute(query)
    return result.scalars().all()


@app.get("/dict-items/models")
async def list_models(
    brand_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(DictItem).where(DictItem.dict_type.in_(["model", "产品型号"]))
    if brand_id is not None:
        query = query.where(DictItem.parent_id == brand_id)
    query = query.where(DictItem.is_active == True).order_by(
        DictItem.sort_order, DictItem.id
    )
    result = await db.execute(query)
    return result.scalars().all()


@app.get("/dict-items/product-types")
async def list_product_types(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(DictItem).where(DictItem.dict_type.in_(["product_type", "产品类型"]))
    query = query.where(DictItem.is_active == True).order_by(
        DictItem.sort_order, DictItem.id
    )
    result = await db.execute(query)
    return result.scalars().all()


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
    # Trend data (环比/同比)
    monthly_target_prev: Optional[float] = None  # 上月目标
    monthly_achieved_prev: Optional[float] = None  # 上月实际
    quarterly_target_prev: Optional[float] = None  # 上季度目标
    quarterly_achieved_prev: Optional[float] = None  # 上季度实际
    leads_count_prev: Optional[int] = None  # 上月线索
    opportunities_count_prev: Optional[int] = None  # 上月商机


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

    # Calculate previous period data for trends (环比)
    from datetime import timedelta

    last_month = today - timedelta(days=1)  # Get last day of previous month
    last_month_start = last_month.replace(day=1)

    # Last month leads/opportunities
    last_month_leads = sum(
        1 for l in leads if l.created_at and l.created_at >= last_month_start
    )
    last_month_opps = sum(
        1 for o in opportunities if o.created_at and o.created_at >= last_month_start
    )

    # Get last month's target and achieved
    last_month_target_result = await db.execute(
        select(SalesTarget).where(
            SalesTarget.target_year == last_month.year,
            SalesTarget.target_type == "monthly",
            SalesTarget.target_period == last_month.month,
        )
    )
    last_month_targets = last_month_target_result.scalars().all()
    monthly_target_prev = sum(float(t.target_amount or 0) for t in last_month_targets)

    last_month_contract_query = (
        select(Contract)
        .join(Project, Contract.project_id == Project.id)
        .where(Contract.contract_direction == "Downstream")
        .where(Contract.signing_date >= last_month_start)
        .where(Contract.signing_date <= last_month)
    )
    if not is_admin:
        last_month_contract_query = last_month_contract_query.where(
            Project.sales_owner_id == user_id
        )
    last_month_contract_result = await db.execute(last_month_contract_query)
    last_month_contracts = last_month_contract_result.scalars().all()
    monthly_achieved_prev = sum(
        float(c.contract_amount or 0) for c in last_month_contracts
    )

    # Calculate last quarter data
    last_quarter = (quarter - 1) if quarter > 1 else 4
    last_quarter_year = today.year if quarter > 1 else today.year - 1
    last_quarter_start = last_quarter_start_month = (last_quarter - 1) * 3 + 1
    last_quarter_start_date = today.replace(
        year=last_quarter_year, month=last_quarter_start_month, day=1
    )
    last_quarter_end = last_quarter_start_date.replace(
        month=last_quarter_start_month + 2, day=28
    )

    # Get last quarter's target and achieved
    last_qtarget_result = await db.execute(
        select(SalesTarget).where(
            SalesTarget.target_year == last_quarter_year,
            SalesTarget.target_type == "quarterly",
            SalesTarget.target_period == last_quarter,
        )
    )
    last_quarter_targets = last_qtarget_result.scalars().all()
    quarterly_target_prev = sum(
        float(t.target_amount or 0) for t in last_quarter_targets
    )

    last_quarter_contract_query = (
        select(Contract)
        .join(Project, Contract.project_id == Project.id)
        .where(Contract.contract_direction == "Downstream")
        .where(Contract.signing_date >= last_quarter_start_date)
        .where(Contract.signing_date <= last_quarter_end)
    )
    if not is_admin:
        last_quarter_contract_query = last_quarter_contract_query.where(
            Project.sales_owner_id == user_id
        )
    last_quarter_contract_result = await db.execute(last_quarter_contract_query)
    last_quarter_contracts = last_quarter_contract_result.scalars().all()
    quarterly_achieved_prev = sum(
        float(c.contract_amount or 0) for c in last_quarter_contracts
    )

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
        monthly_target_prev=monthly_target_prev if monthly_target_prev > 0 else None,
        monthly_achieved_prev=monthly_achieved_prev
        if monthly_achieved_prev > 0
        else None,
        quarterly_target_prev=quarterly_target_prev
        if quarterly_target_prev > 0
        else None,
        quarterly_achieved_prev=quarterly_achieved_prev
        if quarterly_achieved_prev > 0
        else None,
        leads_count_prev=last_month_leads,
        opportunities_count_prev=last_month_opps,
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


class TechnicianInfo(BaseModel):
    id: int
    name: str
    phone: Optional[str]
    department: Optional[str]


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
    technician_ids: Optional[List[str]] = None
    technician_names: Optional[List[str]] = None
    estimated_start_date: Optional[date] = None
    estimated_start_period: Optional[str] = None
    estimated_end_date: Optional[date] = None
    estimated_end_period: Optional[str] = None

    @computed_field
    @property
    def source_id(self) -> Optional[int]:
        if self.source_type == "lead" and self.lead_id:
            return self.lead_id
        elif self.source_type == "opportunity" and self.opportunity_id:
            return self.opportunity_id
        elif self.source_type == "project" and self.project_id:
            return self.project_id
        return None

    model_config = ConfigDict(from_attributes=True)


class DispatchWebhookPayload(BaseModel):
    event: str
    work_order_id: str
    work_order_no: Optional[str]
    status: str
    previous_status: Optional[str]
    timestamp: str
    metadata: Optional[dict] = None


@app.get("/dispatch/technicians", response_model=List[TechnicianInfo])
async def get_dispatch_technicians(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get available technicians from local user database."""
    result = await db.execute(
        select(User).where(User.functional_role == "TECHNICIAN", User.is_active == True)
    )
    technicians = result.scalars().all()

    return [
        TechnicianInfo(
            id=tech.id,
            name=tech.name,
            phone=tech.phone,
            department=tech.department,
        )
        for tech in technicians
    ]


class DispatchApplicationRequest(BaseModel):
    technician_ids: List[int]
    service_mode: str = "offline"
    start_date: Optional[str] = None
    start_period: Optional[str] = None
    end_date: Optional[str] = None
    end_period: Optional[str] = None
    work_type: Optional[str] = None
    notes: Optional[str] = None


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
    if not request.technician_ids or len(request.technician_ids) == 0:
        raise HTTPException(status_code=400, detail="请选择服务工程师")

    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if current_user.get("role") != "admin" and lead.sales_owner_id != current_user.get(
        "id"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员或线索负责人才能创建派工",
        )

    dispatch_service = LocalDispatchService()

    try:
        crm_data = await dispatch_service.get_customer_data_from_lead(db, lead)
        await dispatch_service.validate_technicians(db, request.technician_ids)

        work_order, dispatch_record = await dispatch_service.create_dispatch_atomically(
            db=db,
            crm_data=crm_data,
            source_type="lead",
            source_id=lead.id,
            technician_ids=request.technician_ids,
            submitter_id=current_user["id"],
            service_mode=request.service_mode,
            start_date=request.start_date,
            start_period=request.start_period,
            end_date=request.end_date,
            end_period=request.end_period,
            work_type=request.work_type,
        )

        return DispatchApplicationResponse(
            success=True,
            message="派工创建成功",
            work_order_id=str(work_order.id),
            work_order_no=work_order.work_order_no,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建工单失败: {str(e)}")


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
    if not request.technician_ids or len(request.technician_ids) == 0:
        raise HTTPException(status_code=400, detail="请选择服务工程师")

    result = await db.execute(
        select(Opportunity).where(Opportunity.id == opportunity_id)
    )
    opportunity = result.scalar_one_or_none()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    if current_user.get(
        "role"
    ) != "admin" and opportunity.sales_owner_id != current_user.get("id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员或商机负责人才能创建派工",
        )

    dispatch_service = LocalDispatchService()

    try:
        await dispatch_service.validate_technicians(db, request.technician_ids)
        crm_data = await dispatch_service.get_customer_data_from_opportunity(
            db, opportunity
        )

        work_order, dispatch_record = await dispatch_service.create_dispatch_atomically(
            db=db,
            crm_data=crm_data,
            source_type="opportunity",
            source_id=opportunity.id,
            technician_ids=request.technician_ids,
            submitter_id=current_user["id"],
            service_mode=request.service_mode,
            start_date=request.start_date,
            start_period=request.start_period,
            end_date=request.end_date,
            end_period=request.end_period,
            work_type=request.work_type,
        )

        return DispatchApplicationResponse(
            success=True,
            message="派工创建成功",
            work_order_id=str(work_order.id),
            work_order_no=work_order.work_order_no,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建工单失败: {str(e)}")


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
    if not request.technician_ids or len(request.technician_ids) == 0:
        raise HTTPException(status_code=400, detail="请选择服务工程师")

    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if current_user.get(
        "role"
    ) != "admin" and project.sales_owner_id != current_user.get("id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员或项目负责人才能创建派工",
        )

    dispatch_service = LocalDispatchService()

    try:
        await dispatch_service.validate_technicians(db, request.technician_ids)
        crm_data = await dispatch_service.get_customer_data_from_project(db, project)

        work_order, dispatch_record = await dispatch_service.create_dispatch_atomically(
            db=db,
            crm_data=crm_data,
            source_type="project",
            source_id=project.id,
            technician_ids=request.technician_ids,
            submitter_id=current_user["id"],
            service_mode=request.service_mode,
            start_date=request.start_date,
            start_period=request.start_period,
            end_date=request.end_date,
            end_period=request.end_period,
            work_type=request.work_type,
        )

        return DispatchApplicationResponse(
            success=True,
            message="派工创建成功",
            work_order_id=str(work_order.id),
            work_order_no=work_order.work_order_no,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建工单失败: {str(e)}")


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
        raise HTTPException(
            status_code=400, detail="Missing X-Dispatch-Signature header"
        )

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
    result = await db.execute(
        select(DispatchRecord).where(
            DispatchRecord.work_order_id == payload.work_order_id
        )
    )
    dispatch_record = result.scalar_one_or_none()

    try:
        if not dispatch_record:
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
            dispatch_record.status = payload.status
            dispatch_record.previous_status = payload.previous_status
            dispatch_record.status_updated_at = datetime.utcnow()
            dispatch_record.work_order_no = payload.work_order_no

            if dispatch_record.dispatch_data:
                dispatch_record.dispatch_data.update(payload.model_dump())
            else:
                dispatch_record.dispatch_data = payload.model_dump()

        try:
            wo_id = int(payload.work_order_id)
            wo_result = await db.execute(select(WorkOrder).where(WorkOrder.id == wo_id))
            local_work_order = wo_result.scalar_one_or_none()
            if local_work_order:
                status_map = {
                    "pending": WorkOrderStatus.PENDING,
                    "accepted": WorkOrderStatus.ACCEPTED,
                    "in_service": WorkOrderStatus.IN_SERVICE,
                    "in_progress": WorkOrderStatus.IN_SERVICE,
                    "done": WorkOrderStatus.DONE,
                    "completed": WorkOrderStatus.DONE,
                    "cancelled": WorkOrderStatus.CANCELLED,
                    "rejected": WorkOrderStatus.REJECTED,
                }
                new_status = status_map.get(payload.status.lower())
                if new_status:
                    local_work_order.status = new_status
                    if new_status == WorkOrderStatus.ACCEPTED:
                        local_work_order.accepted_at = datetime.utcnow()
                    elif new_status == WorkOrderStatus.IN_SERVICE:
                        local_work_order.started_at = datetime.utcnow()
                    elif new_status in [
                        WorkOrderStatus.DONE,
                        WorkOrderStatus.CANCELLED,
                        WorkOrderStatus.REJECTED,
                    ]:
                        local_work_order.completed_at = datetime.utcnow()
        except (ValueError, TypeError):
            pass

        await db.commit()
        await db.refresh(dispatch_record)

        return {"success": True, "message": "Webhook processed successfully"}

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to process webhook: {str(e)}"
        )


# ==================== Dispatch History API Endpoints ====================


async def fill_technician_names(db: AsyncSession, records: list) -> list:
    """Fill technician_names and estimated dates for dispatch records."""
    all_ids = set()
    work_order_ids = set()
    for record in records:
        if record.technician_ids:
            for tid in record.technician_ids:
                try:
                    all_ids.add(int(tid))
                except (ValueError, TypeError):
                    pass
        if record.work_order_id:
            try:
                work_order_ids.add(int(record.work_order_id))
            except (ValueError, TypeError):
                pass

    user_map = {}
    if all_ids:
        result = await db.execute(
            select(User.id, User.name).where(User.id.in_(all_ids))
        )
        user_map = {row[0]: row[1] for row in result.fetchall()}

    work_order_map = {}
    if work_order_ids:
        result = await db.execute(
            select(
                WorkOrder.id,
                WorkOrder.estimated_start_date,
                WorkOrder.estimated_start_period,
                WorkOrder.estimated_end_date,
                WorkOrder.estimated_end_period,
            ).where(WorkOrder.id.in_(work_order_ids))
        )
        for row in result.fetchall():
            work_order_map[row[0]] = {
                "estimated_start_date": row[1],
                "estimated_start_period": row[2],
                "estimated_end_date": row[3],
                "estimated_end_period": row[4],
            }

    for record in records:
        if record.technician_ids:
            names = []
            for tid in record.technician_ids:
                try:
                    uid = int(tid)
                    if uid in user_map:
                        names.append(user_map[uid])
                except (ValueError, TypeError):
                    pass
            record.technician_names = names
        else:
            record.technician_names = []

        if record.work_order_id:
            try:
                wo_id = int(record.work_order_id)
                if wo_id in work_order_map:
                    wo_data = work_order_map[wo_id]
                    record.estimated_start_date = wo_data["estimated_start_date"]
                    record.estimated_start_period = wo_data["estimated_start_period"]
                    record.estimated_end_date = wo_data["estimated_end_date"]
                    record.estimated_end_period = wo_data["estimated_end_period"]
            except (ValueError, TypeError):
                pass

    return records


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
    return await fill_technician_names(db, records)


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
    return await fill_technician_names(db, records)


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
    return await fill_technician_names(db, records)


@app.get("/dispatch-records", response_model=List[DispatchRecordRead])
async def list_dispatch_records(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all dispatch records (admin only)."""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=403, detail="Only admin can list all dispatch records"
        )

    result = await db.execute(
        select(DispatchRecord).order_by(DispatchRecord.created_at.desc())
    )
    records = result.scalars().all()
    return await fill_technician_names(db, records)


@app.get("/dispatch-records/{record_id}", response_model=DispatchRecordRead)
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
    return await fill_technician_names(db, [record])[0]


# Customer Channel Link schemas
class CustomerChannelLinkBase(BaseModel):
    customer_id: int
    channel_id: int
    role: str = Field(..., pattern="^(主渠道|协作渠道|历史渠道)$")
    discount_rate: Optional[float] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    notes: Optional[str] = None


class CustomerChannelLinkCreate(CustomerChannelLinkBase):
    pass


class CustomerChannelLinkRead(CustomerChannelLinkBase):
    id: int
    channel_name: Optional[str] = None
    channel_code: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class CustomerChannelLinkUpdate(BaseModel):
    role: Optional[str] = Field(None, pattern="^(主渠道|协作渠道|历史渠道)$")
    discount_rate: Optional[float] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    notes: Optional[str] = None


# Customer Channel Link CRUD endpoints
@app.get("/customer-channel-links", response_model=List[CustomerChannelLinkRead])
async def list_customer_channel_links(
    customer_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get customer channel links, optionally filtered by customer_id."""
    from app.core.permissions import assert_can_access_entity_v2

    if not customer_id:
        raise HTTPException(status_code=400, detail="customer_id is required")

    query = (
        select(CustomerChannelLink, Channel.company_name, Channel.channel_code)
        .outerjoin(Channel, CustomerChannelLink.channel_id == Channel.id)
        .where(CustomerChannelLink.customer_id == customer_id)
    )

    customer_result = await db.execute(
        select(TerminalCustomer).where(TerminalCustomer.id == customer_id)
    )
    customer = customer_result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    await assert_can_access_entity_v2(customer, current_user, db)

    result = await db.execute(query.order_by(CustomerChannelLink.id))
    rows = result.all()
    links = []
    for row in rows:
        link = row[0]
        channel_name = row[1]
        channel_code = row[2]
        links.append(
            {
                "id": link.id,
                "customer_id": link.customer_id,
                "channel_id": link.channel_id,
                "role": link.role,
                "discount_rate": link.discount_rate,
                "start_date": link.start_date,
                "end_date": link.end_date,
                "notes": link.notes,
                "created_at": link.created_at,
                "updated_at": link.updated_at,
                "created_by": link.created_by,
                "channel_name": channel_name,
                "channel_code": channel_code,
            }
        )
    return links


@app.post("/customer-channel-links", response_model=CustomerChannelLinkRead)
async def create_customer_channel_link(
    link: CustomerChannelLinkCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new customer channel link."""
    from app.core.permissions import assert_can_access_entity_v2

    customer_result = await db.execute(
        select(TerminalCustomer).where(TerminalCustomer.id == link.customer_id)
    )
    customer = customer_result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    await assert_can_access_entity_v2(customer, current_user, db)

    channel_result = await db.execute(
        select(Channel).where(Channel.id == link.channel_id)
    )
    channel = channel_result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    new_link = CustomerChannelLink(
        customer_id=link.customer_id,
        channel_id=link.channel_id,
        role=link.role,
        discount_rate=link.discount_rate,
        start_date=datetime.strptime(link.start_date, "%Y-%m-%d").date()
        if link.start_date
        else None,
        end_date=datetime.strptime(link.end_date, "%Y-%m-%d").date()
        if link.end_date
        else None,
        notes=link.notes,
        created_by=current_user["id"],
    )

    db.add(new_link)
    try:
        await db.flush()

        if link.role == "主渠道" and link.end_date is None:
            customer = await db.get(TerminalCustomer, link.customer_id)
            if customer:
                customer.channel_id = link.channel_id

        await db.commit()
        await db.refresh(new_link)
    except Exception as e:
        await db.rollback()
        if "uq_customer_active_primary_channel" in str(e):
            raise HTTPException(
                status_code=400, detail="客户已存在生效的主渠道，请先结束现有主渠道关系"
            )
        raise HTTPException(status_code=400, detail=f"创建失败: {str(e)}")

    return {
        "id": new_link.id,
        "customer_id": new_link.customer_id,
        "channel_id": new_link.channel_id,
        "role": new_link.role,
        "discount_rate": new_link.discount_rate,
        "start_date": new_link.start_date,
        "end_date": new_link.end_date,
        "notes": new_link.notes,
        "created_at": new_link.created_at,
        "updated_at": new_link.updated_at,
        "created_by": new_link.created_by,
        "channel_name": channel.company_name if channel else None,
        "channel_code": channel.channel_code if channel else None,
    }


@app.put("/customer-channel-links/{link_id}", response_model=CustomerChannelLinkRead)
async def update_customer_channel_link(
    link_id: int,
    link_update: CustomerChannelLinkUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing customer channel link."""
    from app.core.permissions import assert_can_mutate_entity_v2

    result = await db.execute(
        select(CustomerChannelLink).where(CustomerChannelLink.id == link_id)
    )
    existing_link = result.scalar_one_or_none()
    if not existing_link:
        raise HTTPException(status_code=404, detail="Customer channel link not found")

    customer_result = await db.execute(
        select(TerminalCustomer).where(TerminalCustomer.id == existing_link.customer_id)
    )
    customer = customer_result.scalar_one_or_none()
    if customer:
        await assert_can_mutate_entity_v2(customer, current_user, db)

    update_data = link_update.model_dump(exclude_unset=True)
    original_role = existing_link.role
    original_end_date = existing_link.end_date

    for field, value in update_data.items():
        if field in ["start_date", "end_date"] and value:
            setattr(existing_link, field, datetime.strptime(value, "%Y-%m-%d").date())
        else:
            setattr(existing_link, field, value)

    try:
        await db.flush()

        customer_obj = await db.get(TerminalCustomer, existing_link.customer_id)
        if customer_obj:
            if original_role == "主渠道" and original_end_date is None:
                if existing_link.role != "主渠道" or existing_link.end_date is not None:
                    active_primary_check = await db.execute(
                        select(CustomerChannelLink).where(
                            CustomerChannelLink.customer_id
                            == existing_link.customer_id,
                            CustomerChannelLink.role == "主渠道",
                            CustomerChannelLink.end_date.is_(None),
                            CustomerChannelLink.id != link_id,
                        )
                    )
                    active_primary = active_primary_check.scalar_one_or_none()
                    if not active_primary:
                        customer_obj.channel_id = None

            if existing_link.role == "主渠道" and existing_link.end_date is None:
                customer_obj.channel_id = existing_link.channel_id

        await db.commit()
        await db.refresh(existing_link)

        channel_result = await db.execute(
            select(Channel).where(Channel.id == existing_link.channel_id)
        )
        channel = channel_result.scalar_one_or_none()

    except Exception as e:
        await db.rollback()
        if "uq_customer_active_primary_channel" in str(e):
            raise HTTPException(
                status_code=400, detail="客户已存在生效的主渠道，请先结束现有主渠道关系"
            )
        raise HTTPException(status_code=400, detail=f"更新失败: {str(e)}")

    return {
        "id": existing_link.id,
        "customer_id": existing_link.customer_id,
        "channel_id": existing_link.channel_id,
        "role": existing_link.role,
        "discount_rate": existing_link.discount_rate,
        "start_date": existing_link.start_date,
        "end_date": existing_link.end_date,
        "notes": existing_link.notes,
        "created_at": existing_link.created_at,
        "updated_at": existing_link.updated_at,
        "created_by": existing_link.created_by,
        "channel_name": channel.company_name if channel else None,
        "channel_code": channel.channel_code if channel else None,
    }


@app.delete("/customer-channel-links/{link_id}")
async def delete_customer_channel_link(
    link_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a customer channel link."""
    from app.core.permissions import assert_can_mutate_entity_v2

    result = await db.execute(
        select(CustomerChannelLink).where(CustomerChannelLink.id == link_id)
    )
    existing_link = result.scalar_one_or_none()
    if not existing_link:
        raise HTTPException(status_code=404, detail="Customer channel link not found")

    customer_result = await db.execute(
        select(TerminalCustomer).where(TerminalCustomer.id == existing_link.customer_id)
    )
    customer = customer_result.scalar_one_or_none()
    if customer:
        await assert_can_mutate_entity_v2(customer, current_user, db)

    if existing_link.role == "主渠道" and existing_link.end_date is None:
        customer_obj = await db.get(TerminalCustomer, existing_link.customer_id)
        if customer_obj:
            other_primary_check = await db.execute(
                select(CustomerChannelLink).where(
                    CustomerChannelLink.customer_id == existing_link.customer_id,
                    CustomerChannelLink.role == "主渠道",
                    CustomerChannelLink.end_date.is_(None),
                    CustomerChannelLink.id != link_id,
                )
            )
            other_primary = other_primary_check.scalar_one_or_none()
            if other_primary:
                customer_obj.channel_id = other_primary.channel_id
            else:
                customer_obj.channel_id = None

    await db.delete(existing_link)
    await db.commit()

    return {"message": "Customer channel link deleted successfully"}
