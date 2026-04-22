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
