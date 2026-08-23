"""
Recommend API — returns ranked course recommendations for a learner.
POST /api/recommend
GET  /api/recommend/{learner_id}
"""
from __future__ import annotations
import logging
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.schemas import Recommendation
from app.db import get_db, LearnerRow, MasteryRow

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{learner_id}", response_model=list)
async def get_recommendations(
    learner_id: str,
    top_k: int = 10,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    """Return fresh recommendations for a learner based on current mastery."""
    skill_graph = request.app.state.skill_graph
    mastery_model = request.app.state.mastery_model
    recommender = request.app.state.recommender

    learner = await db.get(LearnerRow, learner_id)
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    # Get current mastery
    result = await db.execute(
        select(MasteryRow).where(MasteryRow.learner_id == learner_id)
    )
    mastery_rows = result.scalars().all()
    mastery = {r.skill_id: r.p_mastery for r in mastery_rows}

    # Gap skills
    gap_skills = skill_graph.shortest_gap_path(
        learner.known_skills or [], learner.target_occupation or "occ_ds"
    )
    if not gap_skills:
        gap_skills = [s for s in (learner.target_skills or []) if s not in (learner.known_skills or [])]

    gap_pairs = [(sid, skill_graph.get_skill_label(sid)) for sid in gap_skills]
    recommendations = recommender.recommend(gap_pairs, mastery, top_k=top_k)
    return recommendations
