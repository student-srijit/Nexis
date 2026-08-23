"""
SQLite database setup via SQLAlchemy async.
Stores learner profiles, mastery snapshots, and learning paths.
"""
from __future__ import annotations
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import Column, String, Float, Integer, JSON, Text, DateTime, Boolean
import datetime

DB_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./nexis.db")
engine = create_async_engine(DB_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class LearnerRow(Base):
    __tablename__ = "learners"
    learner_id = Column(String, primary_key=True)
    name = Column(String, nullable=True)
    goal = Column(Text)
    target_occupation = Column(String, nullable=True)
    target_skills = Column(JSON, default=[])
    known_skills = Column(JSON, default=[])
    hours_per_week = Column(Float, default=10.0)
    preferred_difficulty = Column(String, default="intermediate")
    quiz_answers = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class MasteryRow(Base):
    __tablename__ = "mastery"
    id = Column(Integer, primary_key=True, autoincrement=True)
    learner_id = Column(String, index=True)
    skill_id = Column(String)
    p_mastery = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)


class PathRow(Base):
    __tablename__ = "paths"
    path_id = Column(String, primary_key=True)
    learner_id = Column(String, index=True)
    path_data = Column(JSON)  # full LearningPath serialized
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
