"""
Nexis — FastAPI main entry point.
"""
from __future__ import annotations
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.api import profile, recommend, path, chat
from app.core.skill_graph import SkillGraph
from app.core.mastery_model import MasteryModel
from app.core.recommender import Recommender
from app.db import init_db

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize heavy singletons once at startup."""
    import asyncio
    print("[START] Nexis starting up...")
    await init_db()

    # Load skill graph (fast — pre-built NetworkX pickle)
    app.state.skill_graph = SkillGraph()
    app.state.skill_graph.load(os.getenv("SKILL_GRAPH_PATH", "data/processed/skill_graph.pkl"))

    # Load mastery model (pre-trained BKT per skill) — fast
    app.state.mastery_model = MasteryModel()
    app.state.mastery_model.load(os.getenv("BKT_MODEL_DIR", "data/processed/bkt_models"))

    # Load recommender — in background so Render health checks pass immediately
    app.state.recommender = Recommender()

    async def _load_recommender():
        recommender_dir = os.getenv("RECOMMENDER_DIR", "data/processed/recommender")
        await asyncio.to_thread(app.state.recommender.load, recommender_dir)
        print("[OK] Recommender loaded in background.")

    asyncio.create_task(_load_recommender())

    print("[OK] Core components loaded. Recommender loading in background.")
    yield
    print("[STOP] Nexis shutting down.")


app = FastAPI(
    title="Nexis",
    description="AI-powered personalized learning path recommender",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profile.router, prefix="/api/profile", tags=["Profile"])
app.include_router(recommend.router, prefix="/api/recommend", tags=["Recommend"])
app.include_router(path.router, prefix="/api/path", tags=["Path"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "Nexis"}
