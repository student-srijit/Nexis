"""
Chat API — explainer agent chat endpoint.
POST /api/chat
WebSocket /api/chat/ws/{learner_id}
"""
from __future__ import annotations
import json
import logging
from fastapi import APIRouter, Request, Depends, WebSocket, WebSocketDisconnect, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.schemas import ChatRequest, ChatResponse
from app.db import get_db, LearnerRow, MasteryRow, PathRow
from app.core.explainer_agent import ExplainerAgent

logger = logging.getLogger(__name__)
router = APIRouter()

_explainer = ExplainerAgent()  # singleton


def _get_explainer(request: Request) -> ExplainerAgent:
    if not hasattr(request.app.state, "explainer_agent"):
        request.app.state.explainer_agent = ExplainerAgent()
    return request.app.state.explainer_agent


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """HTTP chat endpoint — returns a single reply."""
    explainer = _get_explainer(request)

    learner = await db.get(LearnerRow, body.learner_id)
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    result = await db.execute(
        select(MasteryRow).where(MasteryRow.learner_id == body.learner_id)
    )
    mastery = {r.skill_id: r.p_mastery for r in result.scalars().all()}

    path_result = await db.execute(
        select(PathRow)
        .where(PathRow.learner_id == body.learner_id)
        .order_by(PathRow.created_at.desc())
    )
    path_row = path_result.scalars().first()
    path_steps = path_row.path_data.get("steps", []) if path_row else []

    learner_dict = {
        "goal": learner.goal,
        "target_occupation": learner.target_occupation,
        "hours_per_week": learner.hours_per_week,
    }
    history = [m.model_dump() for m in body.conversation_history]

    reply = explainer.chat(
        user_message=body.message,
        learner_profile=learner_dict,
        path_steps=path_steps,
        mastery=mastery,
        conversation_history=history,
        course_id=body.course_id,
    )

    return ChatResponse(reply=reply, sources=[])


@router.websocket("/ws/{learner_id}")
async def chat_ws(
    websocket: WebSocket,
    learner_id: str,
    db: AsyncSession = Depends(get_db),
):
    """WebSocket chat for real-time streaming feel."""
    await websocket.accept()
    explainer = ExplainerAgent()

    # Load context once
    learner = await db.get(LearnerRow, learner_id)
    if not learner:
        await websocket.close(code=1008, reason="Learner not found")
        return

    result = await db.execute(
        select(MasteryRow).where(MasteryRow.learner_id == learner_id)
    )
    mastery = {r.skill_id: r.p_mastery for r in result.scalars().all()}

    path_result = await db.execute(
        select(PathRow)
        .where(PathRow.learner_id == learner_id)
        .order_by(PathRow.created_at.desc())
    )
    path_row = path_result.scalars().first()
    path_steps = path_row.path_data.get("steps", []) if path_row else []
    learner_dict = {
        "goal": learner.goal, "target_occupation": learner.target_occupation,
        "hours_per_week": learner.hours_per_week,
    }
    history = []

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            user_message = msg.get("message", "")

            reply = explainer.chat(
                user_message=user_message,
                learner_profile=learner_dict,
                path_steps=path_steps,
                mastery=mastery,
                conversation_history=history,
            )
            history.append({"role": "user", "content": user_message})
            history.append({"role": "assistant", "content": reply})
            if len(history) > 20:
                history = history[-20:]

            await websocket.send_text(json.dumps({"reply": reply}))
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for learner %s", learner_id)
