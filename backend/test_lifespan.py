import asyncio
import os
import time

from app.main import lifespan
from app.db import init_db
from fastapi import FastAPI
from app.core.skill_graph import SkillGraph
from app.core.mastery_model import MasteryModel
from app.core.recommender import Recommender

async def test():
    app = FastAPI()
    print("Test: About to call lifespan")
    try:
        print("Test: init_db")
        await init_db()
        print("Test: init_db done")
        
        print("Test: SkillGraph load")
        sg = SkillGraph()
        sg.load(os.getenv("SKILL_GRAPH_PATH", "data/processed/skill_graph.pkl"))
        print("Test: SkillGraph done")
        
        print("Test: MasteryModel load")
        mm = MasteryModel()
        mm.load(os.getenv("BKT_MODEL_DIR", "data/processed/bkt_models"))
        print("Test: MasteryModel done")

        print("Test: Recommender load")
        rec = Recommender()
        rec.load(os.getenv("RECOMMENDER_DIR", "data/processed/recommender"))
        print("Test: Recommender done")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
