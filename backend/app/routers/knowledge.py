from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import List

from app.database import get_db
from app.core.dependencies import get_current_user
from app.core.policy.service import build_principal, policy_service
from app.models.knowledge import Knowledge, KnowledgeSourceType
from app.models.user import User
from app.schemas.knowledge import (
    KnowledgeCreate,
    KnowledgeRead,
    KnowledgeUpdate,
    KnowledgeSearchRequest,
)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


SOURCE_TYPE_DISPLAY_NAMES = {
    KnowledgeSourceType.manual: "手动录入",
    KnowledgeSourceType.work_order: "工单生成",
}


async def enrich_knowledge_read(knowledge: Knowledge, db: AsyncSession) -> dict:
    result = KnowledgeRead.model_validate(knowledge).model_dump()
    result["source_type_name"] = SOURCE_TYPE_DISPLAY_NAMES.get(knowledge.source_type)
    result["problem_type_name"] = knowledge.problem_type
    if knowledge.created_by:
        stmt = select(User).where(User.id == knowledge.created_by)
        user_result = await db.execute(stmt)
        creator = user_result.scalar_one_or_none()
        if creator:
            result["created_by_name"] = creator.name
    return result


@router.get("/", response_model=List[KnowledgeRead])
async def search_knowledge(
    keyword: str = None,
    problem_type: str = None,
    tags: str = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)
    await policy_service.authorize(
        resource="knowledge",
        action="list",
        principal=principal,
        db=db,
        obj=None,
    )
    stmt = select(Knowledge)

    if keyword:
        stmt = stmt.where(
            or_(
                Knowledge.title.ilike(f"%{keyword}%"),
                Knowledge.problem.ilike(f"%{keyword}%"),
                Knowledge.solution.ilike(f"%{keyword}%"),
            )
        )

    if problem_type:
        stmt = stmt.where(Knowledge.problem_type == problem_type)

    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
        for tag in tag_list:
            stmt = stmt.where(Knowledge.tags.any(tag))

    result = await db.execute(stmt)
    knowledge_list = result.scalars().all()
    return [await enrich_knowledge_read(k, db) for k in knowledge_list]


@router.get("/by-problem-type/{problem_type}", response_model=List[KnowledgeRead])
async def get_knowledge_by_problem_type(
    problem_type: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)
    await policy_service.authorize(
        resource="knowledge",
        action="list",
        principal=principal,
        db=db,
        obj=None,
    )
    result = await db.execute(
        select(Knowledge).where(Knowledge.problem_type == problem_type)
    )
    knowledge_list = result.scalars().all()
    return [await enrich_knowledge_read(k, db) for k in knowledge_list]


@router.get("/detail/{id}", response_model=KnowledgeRead)
async def get_knowledge(
    id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)
    result = await db.execute(select(Knowledge).where(Knowledge.id == id))
    knowledge = result.scalar_one_or_none()

    if not knowledge:
        raise HTTPException(status_code=404, detail="Knowledge not found")

    await policy_service.authorize(
        resource="knowledge",
        action="read",
        principal=principal,
        db=db,
        obj=knowledge,
    )

    knowledge.view_count += 1
    await db.commit()
    await db.refresh(knowledge)

    return await enrich_knowledge_read(knowledge, db)


@router.post("/", response_model=KnowledgeRead)
async def create_knowledge(
    request: Request,
    knowledge: KnowledgeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    principal = build_principal(current_user)
    await policy_service.authorize_create(
        resource="knowledge",
        principal=principal,
        db=db,
        payload=knowledge,
    )
    user_id = (
        current_user.get("id") if isinstance(current_user, dict) else current_user.id
    )
    new_knowledge = Knowledge(
        title=knowledge.title,
        problem_type=knowledge.problem_type,
        problem=knowledge.problem,
        solution=knowledge.solution,
        tags=knowledge.tags,
        source_type=knowledge.source_type,
        source_id=knowledge.source_id,
        created_by=user_id,
    )
    db.add(new_knowledge)
    await db.commit()
    await db.refresh(new_knowledge)

    return await enrich_knowledge_read(new_knowledge, db)


@router.put("/{id}", response_model=KnowledgeRead)
async def update_knowledge(
    id: int,
    knowledge: KnowledgeUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    principal = build_principal(current_user)
    result = await db.execute(select(Knowledge).where(Knowledge.id == id))
    existing = result.scalar_one_or_none()

    if not existing:
        raise HTTPException(status_code=404, detail="Knowledge not found")

    await policy_service.authorize(
        resource="knowledge",
        action="update",
        principal=principal,
        db=db,
        obj=existing,
    )

    update_data = knowledge.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(existing, field, value)

    await db.commit()
    await db.refresh(existing)

    return await enrich_knowledge_read(existing, db)


@router.delete("/{id}")
async def delete_knowledge(
    id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    principal = build_principal(current_user)
    result = await db.execute(select(Knowledge).where(Knowledge.id == id))
    knowledge = result.scalar_one_or_none()

    if not knowledge:
        raise HTTPException(status_code=404, detail="Knowledge not found")

    await policy_service.authorize(
        resource="knowledge",
        action="delete",
        principal=principal,
        db=db,
        obj=knowledge,
    )

    await db.delete(knowledge)
    await db.commit()

    return {"message": "Knowledge deleted successfully"}
