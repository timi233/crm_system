from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from dotenv import load_dotenv
import os

load_dotenv()

from app.database import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

JWT_SECRET_KEY = os.environ.get(
    "JWT_SECRET_KEY", "dev-only-insecure-key-do-not-use-in-production"
)
JWT_ALGORITHM = "HS256"


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
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


async def require_admin(
    current_user: dict = Depends(get_current_user),
) -> dict:
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限"
        )
    return current_user


def require_roles(allowed_roles: list):
    async def checker(
        current_user: dict = Depends(get_current_user),
    ) -> dict:
        if current_user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要以下角色之一: {', '.join(allowed_roles)}",
            )
        return current_user

    return checker


def apply_data_scope_filter(query, model, current_user: dict, db: AsyncSession):
    """Apply data scope filtering based on user role.

    - admin: full access (no filter)
    - sales: only data where sales_owner_id matches user id
    - business: full access to business data (leads, opportunities, projects, contracts, work_orders, evaluations)
    - finance: only access to financial data (projects, contracts, TerminalCustomer for contract context)
    - technician: only data related to work orders they are assigned to
    - others: no access

    Returns filtered query.
    """
    user_role = current_user.get("role")
    user_id = current_user.get("id")

    if user_role == "admin":
        return query

    if user_role == "business":
        return query

    if user_role == "finance":
        from app.models.project import Project
        from app.models.contract import Contract
        from app.models.customer import TerminalCustomer

        if model.__name__ == "Project":
            return query
        if model.__name__ == "Contract":
            return query
        if model.__name__ == "TerminalCustomer":
            return query
        return query.where(False)

    if user_role == "sales":
        if hasattr(model, "sales_owner_id"):
            return query.where(model.sales_owner_id == user_id)
        elif hasattr(model, "user_id") and not hasattr(model, "sales_owner_id"):
            if hasattr(model, "target_type"):
                from app.models.channel_assignment import ChannelAssignment

                user_channels = select(ChannelAssignment.channel_id).where(
                    ChannelAssignment.user_id == user_id
                )
                return query.where(
                    or_(model.user_id == user_id, model.channel_id.in_(user_channels))
                )
            return query.where(model.user_id == user_id)
        elif hasattr(model, "submitter_id"):
            return query.where(
                or_(
                    model.submitter_id == user_id,
                    model.related_sales_id == user_id
                    if hasattr(model, "related_sales_id")
                    else model.submitter_id == user_id,
                )
            )
        else:
            return query.where(False)

    if user_role == "technician":
        from app.models.work_order import WorkOrder, WorkOrderTechnician
        from app.models.lead import Lead
        from app.models.opportunity import Opportunity
        from app.models.project import Project

        technician_work_orders = select(WorkOrderTechnician.work_order_id).where(
            WorkOrderTechnician.technician_id == user_id
        )

        if model.__name__ == "WorkOrder":
            return query.where(WorkOrder.id.in_(technician_work_orders))

        if hasattr(model, "lead_id"):
            leads_from_work_orders = select(WorkOrder.lead_id).where(
                and_(
                    WorkOrder.id.in_(technician_work_orders),
                    WorkOrder.lead_id.isnot(None),
                )
            )
            if model.__name__ == "Lead":
                return query.where(Lead.id.in_(leads_from_work_orders))
            return query.where(model.lead_id.in_(leads_from_work_orders))

        if hasattr(model, "opportunity_id"):
            opps_from_work_orders = select(WorkOrder.opportunity_id).where(
                and_(
                    WorkOrder.id.in_(technician_work_orders),
                    WorkOrder.opportunity_id.isnot(None),
                )
            )
            if model.__name__ == "Opportunity":
                return query.where(Opportunity.id.in_(opps_from_work_orders))
            return query.where(model.opportunity_id.in_(opps_from_work_orders))

        if hasattr(model, "project_id"):
            projects_from_work_orders = select(WorkOrder.project_id).where(
                and_(
                    WorkOrder.id.in_(technician_work_orders),
                    WorkOrder.project_id.isnot(None),
                )
            )
            if model.__name__ == "Project":
                return query.where(Project.id.in_(projects_from_work_orders))
            return query.where(model.project_id.in_(projects_from_work_orders))

        return query.where(False)

    return query.where(False)
