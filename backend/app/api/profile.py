"""
Profile API — parse goal, build learner profile, generate quiz.
POST /api/profile/create
POST /api/profile/quiz/submit
GET  /api/profile/{learner_id}
"""
from __future__ import annotations
import uuid
import datetime
import logging
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.schemas import (
    ProfileRequest, ProfileResponse, LearnerProfile,
    QuizSubmission, QuizResult, QuizQuestion, MasterySnapshot
)
from app.db import get_db, LearnerRow, MasteryRow, PathRow
from app.core.profiling import ProfilingEngine

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/create", response_model=ProfileResponse)
async def create_profile(
    body: ProfileRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Parse free-text goal → structured LearnerProfile + generate diagnostic quiz.
    """
    skill_graph = request.app.state.skill_graph
    mastery_model = request.app.state.mastery_model

    engine = ProfilingEngine(skill_graph=skill_graph)
    occ_id, target_skills, known_skills, hours = engine.parse_goal(body.goal_text)

    profile = LearnerProfile(
        learner_id=body.learner_id,
        goal=body.goal_text,
        target_occupation=occ_id,
        target_skills=target_skills,
        known_skills=known_skills,
        hours_per_week=hours,
    )

    # Pre-warm mastery model with self-reported skills
    all_skills = list(set(target_skills) | set(known_skills))
    unknown_skills = [s for s in all_skills if s not in known_skills]
    mastery_model.initialize_from_known_skills(body.learner_id, known_skills, unknown_skills)

    # Persist to DB
    existing = await db.get(LearnerRow, body.learner_id)
    if existing:
        existing.goal = body.goal_text
        existing.target_occupation = occ_id
        existing.target_skills = target_skills
        existing.known_skills = known_skills
        existing.hours_per_week = hours
        existing.updated_at = datetime.datetime.utcnow()
    else:
        db.add(LearnerRow(
            learner_id=body.learner_id,
            goal=body.goal_text,
            target_occupation=occ_id,
            target_skills=target_skills,
            known_skills=known_skills,
            hours_per_week=hours,
        ))
    await db.commit()

    # Generate quiz
    quiz_questions = engine.generate_quiz(target_skills, known_skills)
    quiz_models = [QuizQuestion(**q) for q in quiz_questions]

    return ProfileResponse(
        profile=profile,
        quiz_questions=quiz_models,
        message=f"Profile created! Answer {len(quiz_models)} questions to refine your learning path.",
    )


@router.post("/quiz/submit", response_model=QuizResult)
async def submit_quiz(
    body: QuizSubmission,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit quiz answers → update mastery model → optionally replan path.
    """
    mastery_model = request.app.state.mastery_model

    # Score responses
    updates: dict = {}
    correct_count = 0
    from app.core.profiling import SKILL_QUIZ_QUESTIONS

    responses: list = []
    for resp in body.responses:
        qid = resp.get("question_id", "")
        skill_id = resp.get("skill_id", "")
        answer_index = int(resp.get("answer_index", -1))

        q_data = SKILL_QUIZ_QUESTIONS.get(skill_id)
        correct = q_data is not None and answer_index == q_data["correct_index"]
        if correct:
            correct_count += 1
        responses.append((skill_id, correct))

    updates = mastery_model.batch_update(body.learner_id, responses)

    # Persist mastery to DB
    for skill_id, new_mastery in updates.items():
        result = await db.execute(
            select(MasteryRow).where(
                MasteryRow.learner_id == body.learner_id,
                MasteryRow.skill_id == skill_id,
            )
        )
        row = result.scalar_one_or_none()
        if row:
            row.p_mastery = new_mastery
            row.updated_at = datetime.datetime.utcnow()
        else:
            db.add(MasteryRow(learner_id=body.learner_id, skill_id=skill_id, p_mastery=new_mastery))
    await db.commit()

    return QuizResult(
        learner_id=body.learner_id,
        skill_updates=updates,
        correct_count=correct_count,
        total_count=len(body.responses),
        path_replanned=False,
    )


@router.get("/{learner_id}", response_model=LearnerProfile)
async def get_profile(learner_id: str, db: AsyncSession = Depends(get_db)):
    row = await db.get(LearnerRow, learner_id)
    if not row:
        raise HTTPException(status_code=404, detail="Learner not found")
    return LearnerProfile(
        learner_id=row.learner_id,
        name=row.name,
        goal=row.goal,
        target_occupation=row.target_occupation,
        target_skills=row.target_skills or [],
        known_skills=row.known_skills or [],
        hours_per_week=row.hours_per_week,
        preferred_difficulty=row.preferred_difficulty,
    )


@router.get("/{learner_id}/mastery", response_model=MasterySnapshot)
async def get_mastery(learner_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MasteryRow).where(MasteryRow.learner_id == learner_id)
    )
    rows = result.scalars().all()
    return MasterySnapshot(
        learner_id=learner_id,
        skill_mastery={r.skill_id: r.p_mastery for r in rows},
        snapshot_at=datetime.datetime.utcnow().isoformat(),
    )
