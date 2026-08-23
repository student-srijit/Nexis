"""
Path API — generate and replan learning paths.
POST /api/path/generate
POST /api/path/replan
GET  /api/path/{learner_id}/current
"""
from __future__ import annotations
import uuid
import json
import datetime
import logging
from typing import List, Optional
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.schemas import LearningPath, PathStep, QuizSubmission, QuizResult
from app.db import get_db, LearnerRow, MasteryRow, PathRow
from app.core.planner import PathPlanner

logger = logging.getLogger(__name__)
router = APIRouter()
_planner = PathPlanner()


async def _get_learner_mastery(learner_id: str, db: AsyncSession) -> dict:
    result = await db.execute(
        select(MasteryRow).where(MasteryRow.learner_id == learner_id)
    )
    rows = result.scalars().all()
    return {r.skill_id: r.p_mastery for r in rows}


@router.post("/generate", response_model=LearningPath)
async def generate_path(
    learner_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Full pipeline: profile → gap analysis → recommend → plan → save path.
    """
    skill_graph = request.app.state.skill_graph
    mastery_model = request.app.state.mastery_model
    recommender = request.app.state.recommender

    # Load learner
    learner = await db.get(LearnerRow, learner_id)
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found. Create profile first.")

    known_skills = learner.known_skills or []
    target_occupation = learner.target_occupation
    hours_per_week = learner.hours_per_week or 10.0

    # Gap analysis via skill graph
    gap_skills_ordered = skill_graph.shortest_gap_path(known_skills, target_occupation or "occ_ds")
    if not gap_skills_ordered:
        # fallback: use all target skills not yet mastered
        gap_skills_ordered = [s for s in (learner.target_skills or []) if s not in known_skills]

    # Get mastery
    mastery = await _get_learner_mastery(learner_id, db)
    # Also include mastery from in-memory model
    for sk in gap_skills_ordered:
        if sk not in mastery:
            mastery[sk] = mastery_model.p_mastery(learner_id, sk)

    # Build gap skill pairs for recommender
    gap_skill_pairs = [
        (sid, skill_graph.get_skill_label(sid))
        for sid in gap_skills_ordered
    ]

    # Get recommendations
    recommendations = recommender.recommend(gap_skill_pairs, mastery, top_k=10)

    # Generate path
    path = _planner.generate_path(
        learner_id=learner_id,
        target_occupation=target_occupation,
        gap_skills_ordered=gap_skills_ordered,
        skill_labels={sid: skill_graph.get_skill_label(sid) for sid in gap_skills_ordered},
        recommendations=recommendations,
        mastery=mastery,
        hours_per_week=hours_per_week,
        version=1,
    )

    # Generate explainer summaries for each step
    explainer = request.app.state.__dict__.get("explainer_agent")
    if not explainer:
        from app.core.explainer_agent import ExplainerAgent
        explainer = ExplainerAgent()
        request.app.state.explainer_agent = explainer

    learner_dict = {
        "goal": learner.goal, "target_occupation": target_occupation,
        "hours_per_week": hours_per_week
    }
    path_steps_dicts = [s.model_dump() for s in path.steps]

    for step in path.steps:
        try:
            step.why_recommended = explainer.explain_course(
                step.course_id, learner_dict, path_steps_dicts, mastery,
                conversation_history=[],
            )
        except Exception as e:
            logger.warning("Explainer failed for %s: %s", step.course_id, e)
            step.why_recommended = f"Recommended to close your gap in {', '.join(step.skills_taught[:2])}."

    # Save path to DB
    path_row = PathRow(
        path_id=path.path_id,
        learner_id=learner_id,
        path_data=path.model_dump(),
        version=1,
    )
    db.add(path_row)
    await db.commit()

    return path


@router.get("/{learner_id}/current", response_model=LearningPath)
async def get_current_path(learner_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PathRow)
        .where(PathRow.learner_id == learner_id)
        .order_by(PathRow.created_at.desc())
    )
    row = result.scalars().first()
    if not row:
        raise HTTPException(status_code=404, detail="No path found. Generate one first.")
    return LearningPath(**row.path_data)


@router.post("/replan", response_model=LearningPath)
async def replan_path(
    learner_id: str,
    completed_course_ids: List[str],
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Replan path after quiz updates mastery. Keeps completed steps, re-ranks remaining.
    """
    skill_graph = request.app.state.skill_graph
    mastery_model = request.app.state.mastery_model
    recommender = request.app.state.recommender

    # Get current path
    result = await db.execute(
        select(PathRow)
        .where(PathRow.learner_id == learner_id)
        .order_by(PathRow.created_at.desc())
    )
    path_row = result.scalars().first()
    if not path_row:
        raise HTTPException(status_code=404, detail="No existing path to replan.")

    existing_path = LearningPath(**path_row.path_data)
    learner = await db.get(LearnerRow, learner_id)
    mastery = await _get_learner_mastery(learner_id, db)
    for sk in mastery_model._learner_states.get(learner_id, {p: 0 for p in []}).p_know:
        mastery[sk] = mastery_model.p_mastery(learner_id, sk)

    # Get remaining gap skills
    completed_skills = set()
    for step in existing_path.steps:
        if step.course_id in completed_course_ids:
            completed_skills.update(step.skills_taught)
    remaining_gaps = [
        s for s in (learner.target_skills or [])
        if s not in (learner.known_skills or []) and s not in completed_skills
        and mastery.get(s, 0) < 0.8
    ]
    gap_pairs = [(sid, skill_graph.get_skill_label(sid)) for sid in remaining_gaps]
    new_recs = recommender.recommend(gap_pairs, mastery, top_k=10) if gap_pairs else []

    new_path = _planner.replan(
        existing_path, completed_course_ids, new_recs, mastery, learner.hours_per_week or 10.0
    )

    # Save replanned path
    db.add(PathRow(
        path_id=new_path.path_id,
        learner_id=learner_id,
        path_data=new_path.model_dump(),
        version=new_path.version,
    ))
    await db.commit()
    return new_path
