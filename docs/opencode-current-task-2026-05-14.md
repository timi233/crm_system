# OpenCode Current Task

Last updated: 2026-05-14
Owner: codex
Target agent: opencode
Status: pending after CCB queue reset

## Purpose

Persist the current `opencode` handoff outside `.ccb` so it survives `ccb -n` rebuilds and can be used to restore the task after queue or session failure.

## Current Task

Execute a read-only audit for backend low-risk foundation groups `P/Q/T/O`.

Do not modify files.
Do not `git add`.
Do not commit.

## Hard Constraints

- Do not execute `rtk`.
- Do not trigger `rtk` indirectly through wrappers or helper commands.
- Only use normal read-only commands such as:
  - `git diff`
  - `git status`
  - `rg`
  - `sed`
  - `head`
  - `tail`
  - `ls`
- If validation commands are needed, only propose them in the reply. Do not run commands that change the workspace.
- Do not `reset`, `checkout`, or delete files.

## Background

- Groups `A/B/C` were sampled and no real secrets were found.
- Groups `D/E` were audited and accepted as submission candidates.
- Group `N` (`docker-compose.yml`) is paused.
- Group `S` (`project.py`) is paused.
- The current goal is to verify grouping correctness, risks, and validation commands for backend low-risk foundation groups.

## Audit Scope

### Group P: Policy Foundation

Files:

- `backend/app/core/policy/base.py`

Goal:

- Confirm whether the change is only the default policy moving to deny-by-default.
- Confirm whether it affects existing policy registration behavior.
- Validation guidance must be based on real tests in the repo. Do not assume `test_policy_*.py` exists.

### Group Q: Pagination Foundation

Files:

- `backend/app/routers/operation_log.py`
- `backend/app/routers/contract.py`
- `backend/app/routers/customer.py`
- `backend/app/routers/follow_up.py`
- `backend/app/routers/lead.py`
- `backend/app/routers/opportunity.py`
- `backend/tests/test_pagination.py`

Goal:

- Confirm these changes are bounded-pagination audit fixes such as `skip >= 0` and `limit <= 100`.
- Read `backend/tests/test_pagination.py` and confirm it belongs in Group Q.

### Group T: Misc Audit Fixes

Files:

- `backend/app/routers/alert.py`

Goal:

- Confirm this is only a small audit fix, for example date serialization, and does not belong to another domain group.

### Group O: User/Role/Org Foundation

Files:

- `backend/app/core/roles.py`
- `backend/app/models/user.py`
- `backend/app/schemas/user.py`
- `backend/app/routers/user.py`
- `backend/tests/conftest.py`
- `frontend/src/components/lists/UserList.tsx`

Goal:

- Confirm these changes are the foundation for `channel_ops` and `department_manager_id`.
- Check whether `backend/tests/conftest.py` also contains unrelated test infrastructure changes and should be split out.
- Check whether `frontend/src/utils/roles.ts` should move from Group `J` into Group `O`, or stay where it is with a dependency note.

## Required Output

Return:

1. Diff summary for each group.
2. Whether each group is ready for implementation or submission.
3. Correct validation commands.
4. Grouping corrections that should be made.
5. Exact `git add -- <paths>` suggestions, but do not execute them.

## Validation Command Rule

When proposing validation commands:

- Use `cd backend && APP_ENV=test pytest -q tests/...` style paths.
- Do not propose invalid commands such as using `conftest.py` directly as the test target.

## Recovery Note

This file is the source of truth for re-sending the current `opencode` task if the session or CCB process loses queue state.
