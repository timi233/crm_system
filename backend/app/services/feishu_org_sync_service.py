import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, FeishuEmploymentStatus
from app.models.feishu_org_sync_run import FeishuOrgSyncRun
from app.models.employee_handover_request import EmployeeHandoverRequest, HandoverRequestStatus
from app.services.feishu_service import feishu_service, FeishuAPIError
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

DEPARTURE_THRESHOLD = 0.10


class FeishuOrgSyncService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def resolve_team_managers(self, user: User) -> List[User]:
        managers = []
        if user.department_manager_id:
            result = await self.db.execute(
                select(User).where(
                    User.id == user.department_manager_id,
                    User.is_active == True,
                )
            )
            manager = result.scalar_one_or_none()
            if manager:
                managers.append(manager)
        if not managers:
            result = await self.db.execute(
                select(User).where(
                    User.role == "admin",
                    User.is_active == True,
                )
            )
            admins = result.scalars().all()
            managers.extend(admins)
        return managers

    async def sync_users_with_tracking(
        self,
        trigger: str = "manual",
        triggered_by_user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        sync_run = FeishuOrgSyncRun(
            trigger=trigger,
            triggered_by_user_id=triggered_by_user_id,
            status="running",
        )
        self.db.add(sync_run)
        await self.db.commit()
        await self.db.refresh(sync_run)

        created_users: List[Dict[str, Any]] = []
        updated_users: List[Dict[str, Any]] = []
        error_details: List[Dict[str, Any]] = []

        try:
            departments = await feishu_service.get_departments()
        except FeishuAPIError as e:
            logger.error(f"Failed to get departments: {e}")
            sync_run.status = "failed"
            sync_run.error_message = str(e)
            sync_run.completed_at = datetime.utcnow()
            await self.db.commit()
            return {
                "run_id": sync_run.id,
                "created": 0,
                "updated": 0,
                "left_detected": 0,
                "errors": 1,
                "error_details": [{"type": "departments", "error": str(e)}],
            }

        department_path_map = self._build_department_path_map(departments)
        seen_feishu_keys: set[str] = set()
        all_members: Dict[str, Dict[str, Any]] = {}

        for dept in departments:
            dept_id = dept.get("open_department_id", dept.get("department_id"))
            if not dept_id:
                continue
            try:
                members = await feishu_service.get_department_members(dept_id)
                for member in members:
                    self._merge_member(all_members, member, dept_id)
                    open_id = member.get("open_id")
                    union_id = member.get("union_id")
                    if open_id:
                        seen_feishu_keys.add(f"open:{open_id}")
                    if union_id:
                        seen_feishu_keys.add(f"union:{union_id}")
            except FeishuAPIError as e:
                logger.warning(f"Failed to get members for dept {dept_id}: {e}")
                error_details.append(
                    {"type": "department_members", "department_id": dept_id, "error": str(e)}
                )

        for member in all_members.values():
            try:
                result = await self._sync_single_user_with_tracking(
                    member, department_path_map, sync_run.id
                )
                if result["action"] == "created":
                    created_users.append(result["user"])
                elif result["action"] == "updated":
                    updated_users.append(result["user"])
            except Exception as e:
                logger.error(f"Failed to sync user {member.get('open_id')}: {e}")
                error_details.append(
                    {
                        "type": "user_sync",
                        "open_id": member.get("open_id"),
                        "name": member.get("name"),
                        "error": str(e),
                    }
                )

        sync_run.total_seen = len(all_members)
        sync_run.created_count = len(created_users)
        sync_run.updated_count = len(updated_users)

        left_result = await self._detect_departures(seen_feishu_keys, sync_run)
        sync_run.left_detected_count = left_result["left_detected"]

        if left_result["threshold_exceeded"]:
            sync_run.status = "skipped"
            sync_run.error_message = (
                f"Departure threshold exceeded: {left_result['left_detected']} / {left_result['active_seen_before']} "
                f"= {left_result['ratio']:.2%} > {DEPARTURE_THRESHOLD:.0%}"
            )
        else:
            sync_run.status = "success"

        sync_run.completed_at = datetime.utcnow()
        await self.db.commit()

        return {
            "run_id": sync_run.id,
            "created": len(created_users),
            "updated": len(updated_users),
            "left_detected": left_result["left_detected"],
            "left_threshold_exceeded": left_result["threshold_exceeded"],
            "errors": len(error_details),
            "created_users": created_users,
            "updated_users": updated_users,
            "error_details": error_details,
        }

    async def _detect_departures(
        self,
        seen_feishu_keys: set[str],
        sync_run: FeishuOrgSyncRun,
    ) -> Dict[str, Any]:
        result_previous_runs = await self.db.execute(
            select(FeishuOrgSyncRun)
            .where(FeishuOrgSyncRun.status == "success")
            .order_by(FeishuOrgSyncRun.completed_at.desc())
            .limit(1)
        )
        previous_run = result_previous_runs.scalar_one_or_none()

        if not previous_run:
            logger.info("No previous successful sync run, skipping departure detection")
            return {
                "left_detected": 0,
                "threshold_exceeded": False,
                "active_seen_before": 0,
                "ratio": 0.0,
            }

        result_active_users = await self.db.execute(
            select(User).where(
                or_(User.feishu_id.isnot(None), User.feishu_union_id.isnot(None)),
                User.feishu_employment_status == FeishuEmploymentStatus.ACTIVE,
                User.feishu_last_sync_run_id == previous_run.id,
            )
        )
        active_users_before = result_active_users.scalars().all()
        # Seen users are updated to the current run before departure detection.
        # Use the previous run total as the threshold denominator so a small
        # number of missing users is not misread as a 100% departure batch.
        active_seen_before_count = previous_run.total_seen or len(active_users_before)

        departed_users = []
        for user in active_users_before:
            open_seen = bool(user.feishu_id and f"open:{user.feishu_id}" in seen_feishu_keys)
            union_seen = bool(
                user.feishu_union_id and f"union:{user.feishu_union_id}" in seen_feishu_keys
            )
            if not open_seen and not union_seen:
                departed_users.append(user)

        left_detected = len(departed_users)
        if active_seen_before_count > 0:
            ratio = left_detected / active_seen_before_count
        else:
            ratio = 0.0

        threshold_exceeded = ratio > DEPARTURE_THRESHOLD

        if threshold_exceeded:
            logger.warning(
                f"Departure threshold exceeded: {left_detected} / {active_seen_before_count} = {ratio:.2%}"
            )
            return {
                "left_detected": left_detected,
                "threshold_exceeded": True,
                "active_seen_before": active_seen_before_count,
                "ratio": ratio,
            }

        for user in departed_users:
            user.feishu_left_at = datetime.utcnow()
            user.feishu_employment_status = FeishuEmploymentStatus.PENDING_HANDOVER
            user.is_active = False
            user.feishu_last_sync_run_id = sync_run.id

            managers = await self.resolve_team_managers(user)
            handover_request = EmployeeHandoverRequest(
                from_user_id=user.id,
                team_manager_user_id=managers[0].id if managers else None,
                sync_run_id=sync_run.id,
                status=HandoverRequestStatus.PENDING_ASSIGNMENT,
            )
            self.db.add(handover_request)
            await self.db.flush()

            if managers:
                notification_service = NotificationService(self.db)
                for manager in managers:
                    await notification_service.create(
                        user_id=manager.id,
                        notification_type="handover_pending",
                        title=f"员工离职待交接：{user.name}",
                        content=f"员工 {user.name} 已从飞书离职，需要进行交接处理。",
                        entity_type="handover_request",
                        entity_id=handover_request.id,
                    )

        await self.db.commit()

        return {
            "left_detected": left_detected,
            "threshold_exceeded": False,
            "active_seen_before": active_seen_before_count,
            "ratio": ratio,
        }

    async def _sync_single_user_with_tracking(
        self,
        member: Dict[str, Any],
        department_path_map: Optional[Dict[str, str]] = None,
        sync_run_id: int = None,
    ) -> Dict[str, Any]:
        open_id = member.get("open_id")
        union_id = member.get("union_id")
        name = member.get("name")
        mobile = member.get("mobile")
        email = member.get("email")
        avatar_url = member.get("avatar", {}).get("avatar_origin") or member.get("avatar_url")
        department_path = self._get_department_path(member, department_path_map or {})

        user = None
        match_method = None

        if open_id:
            result = await self.db.execute(select(User).where(User.feishu_id == open_id))
            user = result.scalar_one_or_none()
            if user:
                match_method = "open_id"

        if not user and union_id:
            result = await self.db.execute(
                select(User).where(User.feishu_union_id == union_id)
            )
            user = result.scalar_one_or_none()
            if user:
                match_method = "union_id"

        if not user and email:
            result = await self.db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            if user:
                match_method = "email"

        if not user and mobile:
            result = await self.db.execute(select(User).where(User.phone == mobile))
            user = result.scalar_one_or_none()
            if user:
                match_method = "phone"

        now = datetime.utcnow()

        if user:
            if open_id:
                user.feishu_id = open_id
            if union_id:
                user.feishu_union_id = union_id
            if name:
                user.name = name
            if mobile:
                user.phone = mobile
            if email:
                user.email = email
            if avatar_url:
                user.avatar = avatar_url
            if department_path:
                user.department = department_path
            user.feishu_last_seen_at = now
            user.feishu_last_sync_run_id = sync_run_id
            if user.feishu_employment_status in (
                FeishuEmploymentStatus.LEFT,
                FeishuEmploymentStatus.PENDING_HANDOVER,
            ):
                user.feishu_employment_status = FeishuEmploymentStatus.ACTIVE
                user.feishu_left_at = None
                user.is_active = True
                logger.info(f"User {user.name} reappeared after being marked as left")

            await self.db.commit()
            await self.db.refresh(user)

            return {
                "action": "updated",
                "match_method": match_method,
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "feishu_id": user.feishu_id,
                    "department": user.department,
                    "is_active": user.is_active,
                    "role": user.role,
                    "feishu_employment_status": user.feishu_employment_status,
                },
            }

        new_user = User(
            feishu_id=open_id,
            feishu_union_id=union_id,
            name=name,
            phone=mobile,
            email=email,
            avatar=avatar_url,
            department=department_path,
            is_active=True,
            role="sales",
            hashed_password=None,
            feishu_last_seen_at=now,
            feishu_last_sync_run_id=sync_run_id,
            feishu_employment_status=FeishuEmploymentStatus.ACTIVE,
        )
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)

        logger.info(f"Created new user from Feishu: {name} (id={new_user.id})")

        return {
            "action": "created",
            "user": {
                "id": new_user.id,
                "name": new_user.name,
                "email": new_user.email,
                "feishu_id": new_user.feishu_id,
                "department": new_user.department,
                "is_active": new_user.is_active,
                "role": new_user.role,
                "feishu_employment_status": new_user.feishu_employment_status,
            },
        }

    async def sync_users(self) -> Dict[str, Any]:
        return await self.sync_users_with_tracking(trigger="manual")

    async def get_last_successful_run(self) -> Optional[FeishuOrgSyncRun]:
        result = await self.db.execute(
            select(FeishuOrgSyncRun)
            .where(FeishuOrgSyncRun.status == "success")
            .order_by(FeishuOrgSyncRun.completed_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    def _get_department_name(self, department: Dict[str, Any]) -> Optional[str]:
        name = department.get("name")
        if name:
            return name
        i18n_name = department.get("i18n_name") or {}
        return i18n_name.get("zh_cn") or i18n_name.get("en_us")

    def _build_department_path_map(
        self, departments: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        department_by_id: Dict[str, Dict[str, Any]] = {}
        for department in departments:
            for key in ("open_department_id", "department_id"):
                department_id = department.get(key)
                if department_id:
                    department_by_id[department_id] = department

        path_cache: Dict[str, str] = {}

        def build_path(department_id: str, seen: Optional[set[str]] = None) -> str:
            if department_id in path_cache:
                return path_cache[department_id]

            department = department_by_id.get(department_id)
            if not department:
                return department_id

            seen = seen or set()
            if department_id in seen:
                return self._get_department_name(department) or department_id
            seen.add(department_id)

            name = self._get_department_name(department) or department_id
            parent_id = department.get("parent_department_id")
            if parent_id and parent_id != "0" and parent_id in department_by_id:
                path = f"{build_path(parent_id, seen)} / {name}"
            else:
                path = name

            for key in ("open_department_id", "department_id"):
                key_id = department.get(key)
                if key_id:
                    path_cache[key_id] = path
            return path

        for department_id in list(department_by_id.keys()):
            build_path(department_id)

        return path_cache

    def _merge_member(
        self,
        members_by_key: Dict[str, Dict[str, Any]],
        member: Dict[str, Any],
        source_department_id: str,
    ) -> None:
        member_key = (
            member.get("open_id")
            or member.get("union_id")
            or member.get("email")
            or member.get("mobile")
        )
        if not member_key:
            member_key = f"anonymous:{len(members_by_key)}"

        existing = members_by_key.setdefault(member_key, dict(member))
        department_ids = list(existing.get("department_ids") or [])
        member_department_ids = member.get("department_ids") or []
        for department_id in member_department_ids:
            if department_id not in department_ids:
                department_ids.append(department_id)
        if not member_department_ids and source_department_id not in department_ids:
            department_ids.append(source_department_id)
        existing["department_ids"] = department_ids

    def _get_department_path(
        self,
        member: Dict[str, Any],
        department_path_map: Dict[str, str],
    ) -> Optional[str]:
        paths: List[str] = []
        for department_id in member.get("department_ids") or []:
            path = department_path_map.get(department_id, department_id)
            if path and path not in paths:
                paths.append(path)
        return "; ".join(paths) if paths else None

    async def preview_sync_users(self) -> Dict[str, Any]:
        preview_users: List[Dict[str, Any]] = []

        try:
            departments = await feishu_service.get_departments()
        except FeishuAPIError as e:
            return {
                "total_members": 0,
                "preview_users": [],
                "error": str(e),
            }

        department_path_map = self._build_department_path_map(departments)
        all_members: Dict[str, Dict[str, Any]] = {}
        for dept in departments:
            dept_id = dept.get("open_department_id", dept.get("department_id"))
            if not dept_id:
                continue
            try:
                members = await feishu_service.get_department_members(dept_id)
                for member in members:
                    self._merge_member(all_members, member, dept_id)
            except FeishuAPIError:
                pass

        member_list = list(all_members.values())
        for member in member_list[:20]:
            open_id = member.get("open_id")
            union_id = member.get("union_id")
            email = member.get("email")
            mobile = member.get("mobile")
            department_path = self._get_department_path(member, department_path_map)

            user = None
            if open_id:
                result = await self.db.execute(select(User).where(User.feishu_id == open_id))
                user = result.scalar_one_or_none()
            if not user and union_id:
                result = await self.db.execute(
                    select(User).where(User.feishu_union_id == union_id)
                )
                user = result.scalar_one_or_none()
            if not user and email:
                result = await self.db.execute(select(User).where(User.email == email))
                user = result.scalar_one_or_none()
            if not user and mobile:
                result = await self.db.execute(select(User).where(User.phone == mobile))
                user = result.scalar_one_or_none()

            preview_users.append({
                "feishu_name": member.get("name"),
                "feishu_email": email,
                "feishu_mobile": mobile,
                "feishu_open_id": open_id,
                "feishu_union_id": union_id,
                "feishu_department": department_path,
                "crm_user_id": user.id if user else None,
                "crm_user_name": user.name if user else None,
                "will_create": user is None,
            })

        return {
            "total_members": len(member_list),
            "preview_users": preview_users,
        }
