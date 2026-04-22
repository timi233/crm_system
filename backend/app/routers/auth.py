import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
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
        # Only catch authorization exceptions (403)
        if e.status_code == 403:
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
    }
    capabilities["customer:admin_fields"] = principal.is_admin
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
    # Object-level manage capabilities are handled by policy layer, not exposed globally
    capabilities["channel_performance:manage"] = False
    capabilities["channel_training:manage"] = False
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

    return capabilities


@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.hashed_password):
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
    return {"access_token": access_token, "token_type": "bearer"}


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
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired OAuth state",
            )
    else:
        # 非生产环境允许后端重启后继续完成 OAuth 回调，避免内存态 state 丢失导致登录失败。
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
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )
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
