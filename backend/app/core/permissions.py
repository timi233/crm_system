"""
Object-level authorization module - LEGACY SHIM.

All permission logic has been migrated to the policy_service layer.
See: app/core/policy/

This file is kept for backwards compatibility and may be removed after
a stable observation period.

For new permission checks, use:
- policy_service.scope_query() for list filtering
- policy_service.authorize() for single object authorization
- policy_service.authorize_create() for creation validation

Legacy functions removed:
- apply_data_scope_filter -> use policy_service.scope_query()
- assert_can_mutate_entity_v2 -> use policy_service.authorize()
- assert_can_access_entity_v2 -> use policy_service.authorize()
- EntityPermissionChecker -> replaced by BasePolicy subclasses
- permission_checker -> use policy_service instead

No active router should add new dependencies on this module.
Use `app.core.policy` for all new authorization logic.
"""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.policy import build_principal, policy_service


async def assert_can_mutate_entity_v2(
    current_user: dict,
    db: AsyncSession,
    resource: str,
    obj: Any,
) -> None:
    """Backward-compatible shim for older tests and call sites."""
    await policy_service.authorize(
        resource=resource,
        action="update",
        principal=build_principal(current_user),
        db=db,
        obj=obj,
    )


async def assert_can_access_entity_v2(
    current_user: dict,
    db: AsyncSession,
    resource: str,
    obj: Any,
) -> None:
    """Backward-compatible shim for older tests and call sites."""
    await policy_service.authorize(
        resource=resource,
        action="read",
        principal=build_principal(current_user),
        db=db,
        obj=obj,
    )


async def apply_data_scope_filter(
    current_user: dict,
    db: AsyncSession,
    resource: str,
    query: Any,
    model: Any,
    action: str = "list",
) -> Any:
    """Backward-compatible shim for older tests and call sites."""
    return await policy_service.scope_query(
        resource=resource,
        action=action,
        principal=build_principal(current_user),
        db=db,
        query=query,
        model=model,
    )


class EntityPermissionChecker:
    """Compatibility wrapper around policy_service."""

    async def assert_can_access(self, *args: Any, **kwargs: Any) -> None:
        await assert_can_access_entity_v2(*args, **kwargs)

    async def assert_can_mutate(self, *args: Any, **kwargs: Any) -> None:
        await assert_can_mutate_entity_v2(*args, **kwargs)


permission_checker = EntityPermissionChecker()
