from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from typing import List
from datetime import datetime
from jose import JWTError, jwt

from app.database import get_db
from app.models.product_installation import ProductInstallation
from app.models.customer import TerminalCustomer
from app.models.user import User
from app.models.lead import Lead
from app.models.opportunity import Opportunity
from app.models.project import Project
from app.models.work_order import WorkOrder, WorkOrderTechnician
from app.schemas.product_installation import (
    ProductInstallationCreate,
    ProductInstallationUpdate,
    ProductInstallationRead,
    ProductInstallationWithCredentials,
)
import os

router = APIRouter(prefix="/product-installations", tags=["product-installations"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
SECRET_KEY = os.environ.get(
    "JWT_SECRET_KEY", "dev-only-insecure-key-do-not-use-in-production"
)
ALGORITHM = "HS256"

MANUFACTURERS = ["爱数", "安恒", "IPG", "绿盟", "深信服", "其他"]


def mask_sensitive(value: str | None) -> str | None:
    if not value:
        return None
    return "******"


async def get_current_user_from_token(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的认证凭据"
            )
        user_id = int(user_id_str)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的认证凭据"
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的认证凭据"
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在"
        )

    return {"id": user.id, "role": user.role, "name": user.name}


async def check_user_relationship(
    db: AsyncSession, user_id: int, customer_id: int
) -> bool:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return False

    if user.role == "admin":
        return True

    result = await db.execute(
        select(TerminalCustomer).where(TerminalCustomer.id == customer_id)
    )
    customer = result.scalar_one_or_none()
    if not customer:
        return False

    if customer.customer_owner_id == user_id:
        return True

    leads_result = await db.execute(
        select(Lead)
        .where(
            and_(
                Lead.terminal_customer_id == customer_id, Lead.sales_owner_id == user_id
            )
        )
        .limit(1)
    )
    if leads_result.scalar_one_or_none():
        return True

    opps_result = await db.execute(
        select(Opportunity)
        .where(
            and_(
                Opportunity.terminal_customer_id == customer_id,
                Opportunity.sales_owner_id == user_id,
            )
        )
        .limit(1)
    )
    if opps_result.scalar_one_or_none():
        return True

    projects_result = await db.execute(
        select(Project)
        .where(
            and_(
                Project.terminal_customer_id == customer_id,
                Project.sales_owner_id == user_id,
            )
        )
        .limit(1)
    )
    if projects_result.scalar_one_or_none():
        return True

    tech_result = await db.execute(
        select(WorkOrderTechnician.technician_id)
        .join(WorkOrder, WorkOrderTechnician.work_order_id == WorkOrder.id)
        .join(Lead, WorkOrder.lead_id == Lead.id, isouter=True)
        .join(Opportunity, WorkOrder.opportunity_id == Opportunity.id, isouter=True)
        .join(Project, WorkOrder.project_id == Project.id, isouter=True)
        .where(
            and_(
                WorkOrderTechnician.technician_id == user_id,
                or_(
                    Lead.terminal_customer_id == customer_id,
                    Opportunity.terminal_customer_id == customer_id,
                    Project.terminal_customer_id == customer_id,
                ),
            )
        )
        .limit(1)
    )
    if tech_result.scalar_one_or_none():
        return True

    return False


@router.get("/customer/{customer_id}", response_model=List[ProductInstallationRead])
async def list_by_customer(
    customer_id: int,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user["id"]
    has_relationship = await check_user_relationship(db, user_id, customer_id)

    if not has_relationship:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限查看此客户的产品装机记录",
        )

    result = await db.execute(
        select(ProductInstallation)
        .where(ProductInstallation.customer_id == customer_id)
        .order_by(ProductInstallation.created_at.desc())
    )
    installations = result.scalars().all()

    customer_result = await db.execute(
        select(TerminalCustomer.customer_name).where(TerminalCustomer.id == customer_id)
    )
    customer_name = customer_result.scalar_one_or_none()

    response_list = []
    for inst in installations:
        created_by_name = None
        if inst.created_by_id:
            creator_result = await db.execute(
                select(User.name).where(User.id == inst.created_by_id)
            )
            created_by_name = creator_result.scalar_one_or_none()

        inst_dict = {
            "id": inst.id,
            "customer_id": inst.customer_id,
            "customer_name": customer_name,
            "manufacturer": inst.manufacturer,
            "product_type": inst.product_type,
            "product_model": inst.product_model,
            "license_scale": inst.license_scale,
            "system_version": inst.system_version,
            "online_date": inst.online_date,
            "maintenance_expiry": inst.maintenance_expiry,
            "username": mask_sensitive(inst.username)
            if not has_relationship
            else inst.username,
            "password": mask_sensitive(inst.password)
            if not has_relationship
            else inst.password,
            "login_url": mask_sensitive(inst.login_url)
            if not has_relationship
            else inst.login_url,
            "notes": inst.notes,
            "created_at": inst.created_at,
            "updated_at": inst.updated_at,
            "created_by_id": inst.created_by_id,
            "created_by_name": created_by_name,
            "can_view_credentials": has_relationship,
        }
        response_list.append(ProductInstallationRead(**inst_dict))

    return response_list


@router.post(
    "/", response_model=ProductInstallationRead, status_code=status.HTTP_201_CREATED
)
async def create(
    installation: ProductInstallationCreate,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    if installation.manufacturer not in MANUFACTURERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"厂商必须是以下之一: {', '.join(MANUFACTURERS)}",
        )

    customer_result = await db.execute(
        select(TerminalCustomer).where(TerminalCustomer.id == installation.customer_id)
    )
    customer = customer_result.scalar_one_or_none()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="终端客户不存在"
        )

    has_relationship = await check_user_relationship(
        db, current_user["id"], installation.customer_id
    )
    if not has_relationship:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限为此客户创建产品装机记录",
        )

    new_installation = ProductInstallation(
        customer_id=installation.customer_id,
        manufacturer=installation.manufacturer,
        product_type=installation.product_type,
        product_model=installation.product_model,
        license_scale=installation.license_scale,
        system_version=installation.system_version,
        online_date=installation.online_date,
        maintenance_expiry=installation.maintenance_expiry,
        username=installation.username,
        password=installation.password,
        login_url=installation.login_url,
        notes=installation.notes,
        created_by_id=current_user["id"],
    )
    db.add(new_installation)
    await db.commit()
    await db.refresh(new_installation)

    has_relationship = await check_user_relationship(
        db, current_user["id"], installation.customer_id
    )

    return ProductInstallationRead(
        id=new_installation.id,
        customer_id=new_installation.customer_id,
        customer_name=customer.customer_name,
        manufacturer=new_installation.manufacturer,
        product_type=new_installation.product_type,
        product_model=new_installation.product_model,
        license_scale=new_installation.license_scale,
        system_version=new_installation.system_version,
        online_date=new_installation.online_date,
        maintenance_expiry=new_installation.maintenance_expiry,
        username=mask_sensitive(new_installation.username)
        if not has_relationship
        else new_installation.username,
        password=mask_sensitive(new_installation.password)
        if not has_relationship
        else new_installation.password,
        login_url=mask_sensitive(new_installation.login_url)
        if not has_relationship
        else new_installation.login_url,
        notes=new_installation.notes,
        created_at=new_installation.created_at,
        updated_at=new_installation.updated_at,
        created_by_id=new_installation.created_by_id,
        created_by_name=current_user.get("name"),
        can_view_credentials=has_relationship,
    )


@router.put("/{installation_id}", response_model=ProductInstallationRead)
async def update(
    installation_id: int,
    installation_update: ProductInstallationUpdate,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProductInstallation).where(ProductInstallation.id == installation_id)
    )
    installation = result.scalar_one_or_none()
    if not installation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="产品装机记录不存在"
        )

    has_relationship = await check_user_relationship(
        db, current_user["id"], installation.customer_id
    )
    if not has_relationship:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限修改此产品装机记录",
        )

    update_data = installation_update.model_dump(exclude_unset=True)

    if (
        "manufacturer" in update_data
        and update_data["manufacturer"] not in MANUFACTURERS
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"厂商必须是以下之一: {', '.join(MANUFACTURERS)}",
        )

    for key, value in update_data.items():
        setattr(installation, key, value)

    installation.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(installation)

    customer_result = await db.execute(
        select(TerminalCustomer.customer_name).where(
            TerminalCustomer.id == installation.customer_id
        )
    )
    customer_name = customer_result.scalar_one_or_none()

    created_by_name = None
    if installation.created_by_id:
        creator_result = await db.execute(
            select(User.name).where(User.id == installation.created_by_id)
        )
        created_by_name = creator_result.scalar_one_or_none()

    has_relationship = await check_user_relationship(
        db, current_user["id"], installation.customer_id
    )

    return ProductInstallationRead(
        id=installation.id,
        customer_id=installation.customer_id,
        customer_name=customer_name,
        manufacturer=installation.manufacturer,
        product_type=installation.product_type,
        product_model=installation.product_model,
        license_scale=installation.license_scale,
        system_version=installation.system_version,
        online_date=installation.online_date,
        maintenance_expiry=installation.maintenance_expiry,
        username=mask_sensitive(installation.username)
        if not has_relationship
        else installation.username,
        password=mask_sensitive(installation.password)
        if not has_relationship
        else installation.password,
        login_url=mask_sensitive(installation.login_url)
        if not has_relationship
        else installation.login_url,
        notes=installation.notes,
        created_at=installation.created_at,
        updated_at=installation.updated_at,
        created_by_id=installation.created_by_id,
        created_by_name=created_by_name,
        can_view_credentials=has_relationship,
    )


@router.delete("/{installation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    installation_id: int,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProductInstallation).where(ProductInstallation.id == installation_id)
    )
    installation = result.scalar_one_or_none()
    if not installation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="产品装机记录不存在"
        )

    has_relationship = await check_user_relationship(
        db, current_user["id"], installation.customer_id
    )
    if not has_relationship:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限删除此产品装机记录",
        )

    await db.delete(installation)
    await db.commit()

    return None


@router.get(
    "/{installation_id}/credentials", response_model=ProductInstallationWithCredentials
)
async def get_credentials(
    installation_id: int,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProductInstallation).where(ProductInstallation.id == installation_id)
    )
    installation = result.scalar_one_or_none()
    if not installation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="产品装机记录不存在"
        )

    has_relationship = await check_user_relationship(
        db, current_user["id"], installation.customer_id
    )

    if not has_relationship:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您没有权限查看此产品装机的敏感信息",
        )

    customer_result = await db.execute(
        select(TerminalCustomer.customer_name).where(
            TerminalCustomer.id == installation.customer_id
        )
    )
    customer_name = customer_result.scalar_one_or_none()

    created_by_name = None
    if installation.created_by_id:
        creator_result = await db.execute(
            select(User.name).where(User.id == installation.created_by_id)
        )
        created_by_name = creator_result.scalar_one_or_none()

    return ProductInstallationWithCredentials(
        id=installation.id,
        customer_id=installation.customer_id,
        customer_name=customer_name,
        manufacturer=installation.manufacturer,
        product_type=installation.product_type,
        product_model=installation.product_model,
        license_scale=installation.license_scale,
        system_version=installation.system_version,
        online_date=installation.online_date,
        maintenance_expiry=installation.maintenance_expiry,
        username=installation.username,
        password=installation.password,
        login_url=installation.login_url,
        notes=installation.notes,
        created_at=installation.created_at,
        updated_at=installation.updated_at,
        created_by_id=installation.created_by_id,
        created_by_name=created_by_name,
        can_view_credentials=True,
        username_actual=installation.username,
        password_actual=installation.password,
        login_url_actual=installation.login_url,
    )
