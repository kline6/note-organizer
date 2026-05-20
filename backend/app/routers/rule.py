from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.project import Project
from app.models.rule import ClassificationRule, HighlightRule
from app.schemas.rule import (
    ClassificationRuleCreate, ClassificationRuleOut,
    HighlightRuleCreate, HighlightRuleOut,
)

router = APIRouter(prefix="/api/rules", tags=["rules"])


# Classification Rules
@router.post("/classification", response_model=ClassificationRuleOut)
async def create_classification_rule(data: ClassificationRuleCreate, db: AsyncSession = Depends(get_db)):
    if not data.pattern or not data.target_file:
        raise HTTPException(400, "pattern and target_file are required")
    if not data.project_id:
        raise HTTPException(400, "project_id is required")

    rule = ClassificationRule(
        project_id=data.project_id,
        pattern=data.pattern,
        target_file=data.target_file,
        priority=data.priority,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.get("/classification/{project_id}", response_model=list[ClassificationRuleOut])
async def list_classification_rules(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ClassificationRule)
        .where(ClassificationRule.project_id == project_id)
        .order_by(ClassificationRule.priority.desc())
    )
    return list(result.scalars().all())


@router.delete("/classification/{rule_id}")
async def delete_classification_rule(rule_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ClassificationRule).where(ClassificationRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(404, "Rule not found")
    await db.delete(rule)
    await db.commit()
    return {"ok": True}


# Highlight Rules
@router.post("/highlight", response_model=HighlightRuleOut)
async def create_highlight_rule(data: HighlightRuleCreate, db: AsyncSession = Depends(get_db)):
    if not data.project_id:
        raise HTTPException(400, "project_id is required")

    rule = HighlightRule(
        project_id=data.project_id,
        pattern=data.pattern,
        color=data.color,
        style=data.style,
        label=data.label,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.get("/highlight/{project_id}", response_model=list[HighlightRuleOut])
async def list_highlight_rules(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(HighlightRule).where(HighlightRule.project_id == project_id)
    )
    return list(result.scalars().all())


@router.delete("/highlight/{rule_id}")
async def delete_highlight_rule(rule_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(HighlightRule).where(HighlightRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(404, "Rule not found")
    await db.delete(rule)
    await db.commit()
    return {"ok": True}


# Batch create rules for a project
@router.post("/batch/{project_id}")
async def batch_create_rules(
    project_id: str,
    classification_rules: list[ClassificationRuleCreate] = [],
    highlight_rules: list[HighlightRuleCreate] = [],
    db: AsyncSession = Depends(get_db),
):
    for cr in classification_rules:
        rule = ClassificationRule(
            project_id=project_id,
            pattern=cr.pattern,
            target_file=cr.target_file,
            priority=cr.priority,
        )
        db.add(rule)

    for hr in highlight_rules:
        rule = HighlightRule(
            project_id=project_id,
            pattern=hr.pattern,
            color=hr.color,
            style=hr.style,
            label=hr.label,
        )
        db.add(rule)

    await db.commit()
    return {"ok": True, "classification_count": len(classification_rules), "highlight_count": len(highlight_rules)}
