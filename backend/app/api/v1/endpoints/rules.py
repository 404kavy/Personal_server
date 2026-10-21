from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.activity import CategoryRule
from app.schemas.activity import (
    CategoryRuleCreate,
    CategoryRuleResponse,
    UnclassifiedAppResponse,
)
from app.services.session_service import (
    get_unclassified_apps_summary,
    save_user_rule_and_retroactively_tag,
)

router = APIRouter(prefix="/rules", tags=["Category Classification Rules"])


@router.get(
    "/",
    response_model=List[CategoryRuleResponse],
    summary="List all user-defined classification rules",
)
async def list_rules(db: Session = Depends(get_db)):
    """Returns all custom user category rules. User rules override baseline fallbacks."""
    return db.query(CategoryRule).order_by(CategoryRule.created_at.desc()).all()


@router.post(
    "/",
    response_model=CategoryRuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create or update a category rule",
)
async def create_or_update_rule(
    payload: CategoryRuleCreate,
    db: Session = Depends(get_db),
):
    """
    Creates or updates a rule (e.g. 'blender.exe' -> 'study').
    Optionally retroactively reclassifies all past sessions for this app.
    """
    rule = save_user_rule_and_retroactively_tag(
        db=db,
        pattern=payload.pattern,
        category=payload.category,
        apply_to_past=payload.apply_to_past,
    )
    return rule


@router.delete(
    "/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a classification rule",
)
async def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    """Deletes a custom user rule."""
    rule = db.query(CategoryRule).filter(CategoryRule.id == rule_id).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule with id {rule_id} not found",
        )
    db.delete(rule)
    db.commit()
    return None


@router.get(
    "/unclassified",
    response_model=List[UnclassifiedAppResponse],
    summary="Get unclassified apps and domains for UI tagging",
)
async def get_unclassified_apps(db: Session = Depends(get_db)):
    """
    Returns all applications/domains with 'unclassified' status,
    sorted by total duration, ready for one-click tagging in the UI.
    """
    return get_unclassified_apps_summary(db)

