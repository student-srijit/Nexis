"""
Pydantic schemas for Nexis.
All data models are defined here and shared across API and core layers.
"""
from __future__ import annotations
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class LearnerProfile(BaseModel):
    learner_id: str
    name: Optional[str] = None
    goal: str  # free-text original goal
    target_occupation: Optional[str] = None  # ESCO occupation label
    target_skills: List[str] = Field(default_factory=list)  # ESCO skill IDs
    known_skills: List[str] = Field(default_factory=list)   # ESCO skill IDs
    hours_per_week: float = 10.0
    preferred_difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    quiz_answers: Dict[str, bool] = Field(default_factory=dict)  # skill_id -> correct


class PathStep(BaseModel):
    step_index: int
    course_id: str
    course_title: str
    skills_taught: List[str]
    prerequisite_skills: List[str]
    estimated_hours: float
    difficulty: DifficultyLevel
    mastery_score_before: float = 0.0   # p_mastery at time of recommendation
    recommendation_score: float = 0.0  # LightGBM ranker score
    milestone_week: int  # which week this step targets
    why_recommended: str = ""  # explainer summary (populated post-hoc)


class LearningPath(BaseModel):
    learner_id: str
    path_id: str
    target_occupation: Optional[str]
    steps: List[PathStep]
    total_estimated_hours: float
    total_weeks: int
    generated_at: str  # ISO timestamp
    version: int = 1  # increments on replan


class Recommendation(BaseModel):
    course_id: str
    course_title: str
    provider: str
    skills_covered: List[str]
    gap_skills_closed: List[str]
    content_similarity: float  # cosine sim to gap skill description
    ranker_score: float         # LightGBM score
    difficulty: DifficultyLevel
    estimated_hours: float
    url: Optional[str] = None
    description: str = ""


class QuizQuestion(BaseModel):
    question_id: str
    skill_id: str
    skill_label: str
    question_text: str
    options: List[str]
    correct_index: int


class QuizSubmission(BaseModel):
    learner_id: str
    responses: List[Dict[str, Any]]  # [{question_id, skill_id, answer_index}]


class QuizResult(BaseModel):
    learner_id: str
    skill_updates: Dict[str, float]  # skill_id -> new p_mastery
    correct_count: int
    total_count: int
    path_replanned: bool
    new_path: Optional[LearningPath] = None


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    learner_id: str
    message: str
    conversation_history: List[ChatMessage] = Field(default_factory=list)
    # context automatically populated from learner state
    course_id: Optional[str] = None  # if asking about a specific course


class ChatResponse(BaseModel):
    reply: str
    sources: List[str] = Field(default_factory=list)  # graph paths / scores cited


class ProfileRequest(BaseModel):
    learner_id: str
    goal_text: str  # free-text goal statement


class ProfileResponse(BaseModel):
    profile: LearnerProfile
    quiz_questions: List[QuizQuestion]
    message: str


class MasterySnapshot(BaseModel):
    learner_id: str
    skill_mastery: Dict[str, float]  # skill_id -> p_mastery
    snapshot_at: str
