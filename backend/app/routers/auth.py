import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.dependencies import get_current_user
from app.core.policy.service import build_principal, policy_service
from app.core.roles import normalize_role
from app.core.security import create_access_token, verify_password
from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    AuthCapabilitiesResponse,
    FeishuLoginRequest,
    FeishuLoginResponse,
    Token,
)
from app.services.feishu_service import feishu_service


router = APIRouter(prefix="/auth", tags=["auth"])
settings = Settings()
logger = logging.getLogger(__name__)


class LoginFormData:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password


async def get_login_form(
    username: str = Form(...),
    password: str = Form(...),
) -> LoginFormData:
    return LoginFormData(username=username, password=password)


class CapabilityPayload(dict):
    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError as exc:
            raise AttributeError(item) from exc


def _build_capability_payload(resource: str, user: dict) -> object:
    user_id = user["id"]
    payloads = {
        "user": CapabilityPayload(),
        "product": CapabilityPayload(),
        "channel": CapabilityPayload(),
        "lead": CapabilityPayload(
            sales_owner_id=user_id,
            channel_id=None,
            source_channel_id=None,
        ),
        "customer": CapabilityPayload(customer_owner_id=user_id, channel_id=None),
        "opportunity": CapabilityPayload(sales_owner_id=user_id, channel_id=None),
        "project": CapabilityPayload(sales_owner_id=user_id),
        "contract": CapabilityPayload(
            project_id=None,
            channel_id=None,
            terminal_customer_id=None,
        ),
        "follow_up": CapabilityPayload(
            follower_id=user_id,
            lead_id=None,
            opportunity_id=None,
            project_id=None,
            terminal_customer_id=None,
            channel_id=None,
        ),
        "unified_target": CapabilityPayload(
            target_type="channel",
            channel_id=None,
            user_id=user_id,
        ),
        "execution_plan": CapabilityPayload(
            channel_id=None,
            user_id=user_id,
            plan_type="monthly",
            plan_category="training",
            plan_period="2026-01",
            plan_content="培训计划",
            status="planned",
        ),
        "work_order": CapabilityPayload(
            submitter_id=user_id,
            related_sales_id=user_id,
        ),
        "alert_rule": CapabilityPayload(),
        "sales_target": CapabilityPayload(user_id=user_id),
        "knowledge": CapabilityPayload(),
        "dict_item": CapabilityPayload(),
    }
    return payloads.get(resource, CapabilityPayload())


async def _can_create_resource(
    resource: str,
    *,
    current_user: dict,
    db: AsyncSession,
) -> bool:
    principal = build_principal(current_user)
    payload = _build_capability_payload(resource, current_user)
    try:
        await policy_service.authorize_create(
            resource=resource,
            principal=principal,
            db=db,
            payload=payload,
        )
        return True
    except HTTPException as e:
        # Capability probes should degrade to false when contextual objects are absent.
        if e.status_code in {403, 404}:
            return False
        else:
            # Re-raise non-authorization exceptions for proper error handling
            raise
    except Exception as e:
        # Log unexpected exceptions but don't swallow them
        logger.error(f"Unexpected error in _can_create_resource: {e}")
        raise


async def _build_capabilities(
    *,
    current_user: dict,
    db: AsyncSession,
) -> dict[str, bool]:
    principal = build_principal(current_user)

    capabilities = {
        "user:create": await _can_create_resource(
            "user", current_user=current_user, db=db
        ),
        "product:create": await _can_create_resource(
            "product", current_user=current_user, db=db
        ),
        "channel:create": await _can_create_resource(
            "channel", current_user=current_user, db=db
        ),
        "lead:create": await _can_create_resource(
            "lead", current_user=current_user, db=db
        ),
        "customer:create": await _can_create_resource(
            "customer", current_user=current_user, db=db
        ),
        "opportunity:create": await _can_create_resource(
            "opportunity", current_user=current_user, db=db
        ),
        "project:create": await _can_create_resource(
            "project", current_user=current_user, db=db
        ),
        "contract:create": await _can_create_resource(
            "contract", current_user=current_user, db=db
        ),
        "follow_up:create": await _can_create_resource(
            "follow_up", current_user=current_user, db=db
        ),
        "work_order:create": await _can_create_resource(
            "work_order", current_user=current_user, db=db
        ),
        "sales_target:create": await _can_create_resource(
            "sales_target", current_user=current_user, db=db
        ),
        "unified_target:create": await _can_create_resource(
            "unified_target", current_user=current_user, db=db
        ),
        "execution_plan:create": await _can_create_resource(
            "execution_plan", current_user=current_user, db=db
        ),
        "knowledge:create": await _can_create_resource(
            "knowledge", current_user=current_user, db=db
        ),
        "dict_item:create": await _can_create_resource(
            "dict_item", current_user=current_user, db=db
        ),
    }

    capabilities["user:manage"] = capabilities["user:create"]
    capabilities["user:read"] = principal.role in {
        "admin",
        "business",
        "finance",
        "sales",
        "technician",
        "channel_ops",
    }
    common_read_roles = {"admin", "business", "finance", "sales", "technician", "channel_ops"}
    for resource in (
        "customer",
        "lead",
        "opportunity",
        "project",
        "contract",
        "follow_up",
        "product",
        "work_order",
        "knowledge",
    ):
        capabilities[f"{resource}:read"] = principal.role in common_read_roles
    capabilities["customer:admin_fields"] = principal.is_admin
    capabilities["dashboard:read"] = principal.role in common_read_roles
    capabilities["alert_rule:manage"] = principal.is_admin
    capabilities["dashboard:team_rank"] = principal.is_admin
    capabilities["report:read"] = principal.role in {
        "admin",
        "business",
        "finance",
        "sales",
    }
    capabilities["report:global"] = principal.role in {"admin", "business", "finance"}
    capabilities["channel_assignment:manage"] = principal.is_admin
    capabilities["channel:read"] = principal.role in {
        "admin",
        "business",
        "finance",
        "sales",
        "technician",
    }
    capabilities["channel_performance:read"] = capabilities["channel:read"]
    capabilities["channel_training:read"] = capabilities["channel:read"]
    # Page-level access capabilities - allow sales to enter pages, actual operations are validated by policy layer
    capabilities["channel_performance:manage_page"] = principal.role in {
        "admin",
        "business",
        "sales",
    }
    capabilities["channel_training:manage_page"] = principal.role in {
        "admin",
        "business",
        "sales",
    }
    capabilities["channel_performance:manage"] = capabilities[
        "channel_performance:manage_page"
    ]
    capabilities["channel_training:manage"] = capabilities[
        "channel_training:manage_page"
    ]
    capabilities["operation_log:read"] = principal.role in {"admin", "business"}
    capabilities["sales_target:read"] = principal.role in {
        "admin",
        "business",
        "finance",
        "sales",
        "technician",
    }
    capabilities["dict_item:read"] = principal.role in {
        "admin",
        "business",
        "finance",
        "sales",
        "technician",
    }
    capabilities["kingdee_integration:read"] = principal.role in {
        "admin",
        "finance",
        "business",
    }
    capabilities["financial_export:read"] = principal.role in {
        "admin",
        "finance",
        "business",
    }
    capabilities["financial_export:summary"] = principal.role in {"admin", "finance"}

    work_report_roles = {"admin", "business", "sales", "technician", "channel_ops"}
    capabilities["work_report:read"] = principal.role in work_report_roles
    capabilities["work_report:create"] = principal.role in work_report_roles
    capabilities["work_report:update"] = principal.role in work_report_roles
    capabilities["work_report:submit"] = principal.role in work_report_roles
    capabilities["work_report:withdraw"] = principal.role in work_report_roles
    capabilities["work_report:team_read"] = principal.role in {"admin", "business"}

    capabilities["dashboard:team"] = principal.role in {"admin", "business"}

    capabilities["handover:read"] = principal.role == "admin"

    return capabilities


@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: LoginFormData = Depends(get_login_form),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    if (
        not user
        or not user.hashed_password
        or not verify_password(form_data.password, user.hashed_password)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    normalized_role = normalize_role(user.role)
    access_token = create_access_token(
        data={"sub": str(user.id), "role": normalized_role},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    logger.info(f"User {user.email} (id={user.id}) logged in")
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout(
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user.get("id")
    user_name = current_user.get("name", "unknown")
    logger.info(f"User {user_name} (id={user_id}) logged out")
    return {"message": "Logged out successfully"}


@router.get("/feishu/url")
async def get_feishu_oauth_url():
    return {"url": feishu_service.get_oauth_url()}


@router.post("/feishu/login", response_model=FeishuLoginResponse)
async def feishu_login(
    request: FeishuLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    if settings.app_env == "production":
        if not feishu_service.consume_oauth_state(request.state):
            logger.warning(f"Feishu OAuth state expired or invalid: {request.state}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="登录链接已过期，请重新登录",
            )
    else:
        feishu_service.consume_oauth_state(request.state)

    try:
        feishu_user = await feishu_service.get_user_by_code(request.code)
    except Exception as e:
        logger.exception("Feishu OAuth login failed")
        error_detail = (
            str(e) if settings.app_env != "production" else "飞书登录失败，请重试"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_detail,
        )

    open_id = feishu_user.get("open_id")
    union_id = feishu_user.get("union_id")
    email = feishu_user.get("email")
    mobile = feishu_user.get("mobile")

    user = None
    match_method = None

    if open_id:
        result = await db.execute(select(User).where(User.feishu_id == open_id))
        user = result.scalar_one_or_none()
        if user:
            match_method = "open_id"

    if not user and union_id:
        result = await db.execute(select(User).where(User.feishu_union_id == union_id))
        user = result.scalar_one_or_none()
        if user:
            match_method = "union_id"

    if not user and email:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user:
            match_method = "email"

    if not user and mobile:
        result = await db.execute(select(User).where(User.phone == mobile))
        user = result.scalar_one_or_none()
        if user:
            match_method = "phone"

    if not user:
        logger.warning(
            f"Feishu user not found in CRM: open_id={open_id}, union_id={union_id}, email={email}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户未同步，请联系管理员",
        )

    if not user.is_active:
        logger.warning(f"Feishu login blocked: user {user.id} is inactive")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已禁用，请联系管理员",
        )

    logger.info(
        f"Feishu login matched user {user.id} via {match_method}: open_id={open_id}"
    )

    if open_id and user.feishu_id != open_id:
        user.feishu_id = open_id
    if union_id and user.feishu_union_id != union_id:
        user.feishu_union_id = union_id

    user.name = feishu_user["name"]
    if feishu_user.get("mobile"):
        user.phone = feishu_user["mobile"]
    if feishu_user.get("email"):
        user.email = feishu_user["email"]
    if feishu_user.get("avatar_url"):
        user.avatar = feishu_user["avatar_url"]
    await db.commit()
    await db.refresh(user)

    normalized_role = normalize_role(user.role)
    access_token = create_access_token(
        data={"sub": str(user.id), "role": normalized_role},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": normalized_role,
            "avatar": user.avatar,
        },
    }


@router.get("/me", response_model=dict)
async def get_my_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == current_user["id"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user.id,
        "name": user.name or "",
        "email": user.email,
        "role": normalize_role(user.role),
        "avatar": user.avatar,
    }


@router.get("/me/capabilities", response_model=AuthCapabilitiesResponse)
async def get_my_capabilities(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    normalized_role = normalize_role(current_user["role"])
    capabilities = await _build_capabilities(current_user=current_user, db=db)
    return {
        "role": normalized_role,
        "capabilities": capabilities,
    }
