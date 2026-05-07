# CRM Security Remediation - 2026-04-27

## Scope Boundary

This remediation applies only to the current CRM system:

- Backend: `backend/`
- Frontend: `frontend/`
- Documentation: `docs/`, root project documentation

`QDmgt/` and `new_task_mgt/` are external reference systems. They may be used to understand business structure and implementation ideas, but they must not be modified, imported, depended on, or mixed into the current CRM runtime.

## Cross Review Inputs

The review combines:

- Local Codex review and existing subagent findings.
- `opencode` parallel review report received on 2026-04-27.
- Current working tree verification in the CRM codebase.

## Ownership Split

Codex owns CRITICAL and HIGH remediation in the current CRM:

1. Sales self-escalation through user update.
2. Dispatch webhook bypass of work order state machine and approval gate.
3. Multi-technician approval aggregation order bug.
4. CRM dispatch creation missing Feishu dispatch cards.
5. Product installation credential overexposure.
6. Frontend route-level capability enforcement.
7. Financial export scope filtering after verification.

`opencode` owns MEDIUM/LOW remediation and focused test or robustness improvements, with the same scope boundary. The async CCB job is `job_60e31c7969a7`.

## High Priority Findings

### Critical: Sales User Self-Escalation

`UserPolicy.authorize()` allowed a sales user to update their own user record, and `PUT /users/{id}` accepts role, functional role, active state, and sales hierarchy fields. A sales user could promote themselves or modify protected account state.

Required fix: non-admin self-update must not be able to write privileged fields. Admin-only fields include `role`, `functional_role`, `is_active`, `sales_leader_id`, `sales_region`, and `sales_product_line`.

### High: Dispatch Webhook Bypasses State Machine

The dispatch webhook directly maps external status to `WorkOrder.status`, bypassing local transition validation and the requirement that `IN_SERVICE` or `DONE` requires at least one approved technician assignment.

Required fix: webhook must validate the target work order exists, reject invalid state transitions, and enforce the same approval gate as the main work order status endpoint.

### High: Multi-Technician Approval Aggregation

One rejected or canceled assignment can currently move the entire work order to `REJECTED` before other pending technicians have responded. Later approval cannot reliably recover the main status.

Required fix: individual rejection must not reject the main work order while other assignments are still pending. Main rejection should happen only when every assignment is terminal rejected/canceled and none is approved.

### High: Dispatch Creation Missing Feishu Cards

The CRM dispatch creation path creates `WorkOrder`, `WorkOrderTechnician`, and `DispatchRecord`, but does not trigger the same Feishu dispatch-card notification used by manual assignment.

Required fix: share the card notification/update behavior between dispatch creation and manual assignment.

### High: Product Installation Credentials Overexposed

Product installation credentials are stored and returned broadly. Passwords should not be included in list/detail payloads for broad related-user access.

Required fix: mask or omit passwords from normal responses and reserve raw credential access for an explicit privileged path in a later hardening step.

### High: Frontend Routes Lack Capability Guard

Menus hide unauthorized pages, but direct URL navigation can mount protected pages and call APIs.

Required fix: add route-level capability checks after authentication/capability bootstrap and render a 403 view instead of mounting protected pages.

### High: Financial Exports Need Scope Verification

Financial export endpoints must be verified and, if needed, changed to apply policy scope filtering for project, contract, and summary exports.

Required fix: use the existing policy service for export queries so exports cannot exceed the caller's data scope.

## Validation Targets

- `cd backend && venv/bin/python -m pytest -q`
- `cd frontend && npm run build`

## Completion Update

`opencode` completed `job_60e31c7969a7` and reported MEDIUM/LOW remediation across backend authorization checks, dashboard policy, work order technician active checks, JWT/logout tests, localStorage parsing hardening, and Kingdee integration async cleanup.

Post-review adjustment by Codex:

- Added Alembic migration `dispatch_record_work_order_id_integer` for the `dispatch_records.work_order_id` integer foreign key change.
- Aligned `LocalDispatchService` and `DispatchIntegrationService` to write integer local CRM work order IDs after the model type change.
- Verified `QDmgt/` and `new_task_mgt/` remain untouched.

Final validation on 2026-04-27:

- `cd backend && venv/bin/python -m pytest -q`: `136 passed, 13 warnings`
- `cd frontend && npm run build`: successful
- `cd backend && venv/bin/alembic heads`: `dispatch_record_work_order_id_integer`
- `cd backend && venv/bin/alembic upgrade head --sql`: generated successfully
