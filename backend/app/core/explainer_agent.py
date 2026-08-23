"""
Explainer Agent — OpenRouter API (OpenAI-compatible), constrained to actual recommendation data.

Model: google/gemini-2.0-flash-001 via OpenRouter (free-tier compatible)
OpenRouter docs: https://openrouter.ai/docs

System prompt hard-constrains the model to:
  - Only reference courses, scores, and graph paths passed in context
  - Cite specific mastery values and graph paths in every explanation
  - Never invent a course name or claim about mastery
"""
from __future__ import annotations
import os
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Nexis's explainer assistant. Your ONLY job is to explain 
recommendations that were already computed by our ML system (BKT mastery model + LightGBM ranker).

STRICT RULES — violating any of these is unacceptable:
1. You may ONLY reference courses, skills, mastery scores, and graph paths that are 
   provided to you in the [RECOMMENDATION CONTEXT] section below.
2. You may NEVER invent a course name, skill, or claim about mastery.
3. Every explanation MUST cite at least one specific number (a mastery score like 0.4, 
   a ranker score like 0.73, or a milestone week number).
4. If the learner asks about something not in the context, say: 
   "I can only explain what's in your current learning path. Ask me about a specific course."
5. Be concise, friendly, and specific. Point to actual data.

EXAMPLE of a good response:
"Python for Everybody is in your path because your current mastery on Python Programming 
is 0.18 (very low). It's the prerequisite foundation for Machine Learning (2 hops away 
on the skill graph). The LightGBM ranker scored it 0.82 — the highest in your gap set."
"""


class ExplainerAgent:
    def __init__(self):
        self._client = None
        self._api_key = os.getenv("OPENROUTER_API_KEY", "")
        self._model = os.getenv("OPENROUTER_MODEL", "openrouter/free")
        self._initialized = False

    def _ensure_init(self):
        if self._initialized:
            return
        if not self._api_key:
            logger.warning("OPENROUTER_API_KEY not set — using template fallback.")
            self._initialized = True
            return
        try:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=self._api_key,
                base_url="https://openrouter.ai/api/v1",
                default_headers={
                    "HTTP-Referer": "https://nexis.app",
                    "X-Title": "Nexis",
                },
            )
            logger.info("OpenRouter client initialized (model=%s)", self._model)
        except Exception as e:
            logger.warning("Failed to init OpenRouter client: %s", e)
        self._initialized = True

    # ------------------------------------------------------------------ #
    # Context builder                                                       #
    # ------------------------------------------------------------------ #

    def _build_context(
        self,
        learner_profile: Dict,
        path_steps: List[Dict],
        mastery: Dict[str, float],
        course_id: Optional[str] = None,
    ) -> str:
        lines = ["[RECOMMENDATION CONTEXT]"]
        lines.append(f"Goal: {learner_profile.get('goal', 'N/A')}")
        lines.append(f"Target occupation: {learner_profile.get('target_occupation', 'N/A')}")
        lines.append(f"Hours per week: {learner_profile.get('hours_per_week', 10)}")

        lines.append("\n[BKT MASTERY SCORES — actual model output]")
        for skill_id, score in sorted(mastery.items(), key=lambda x: x[1]):
            label = skill_id.replace("s_", "").replace("_", " ").title()
            lines.append(f"  {label} ({skill_id}): {score:.3f}")

        lines.append("\n[LEARNING PATH — LightGBM ranker output]")
        for i, step in enumerate(path_steps):
            focus = " <-- FOCUS COURSE" if step.get("course_id") == course_id else ""
            lines.append(
                f"  Step {i+1}: {step.get('course_title', 'Unknown')} "
                f"| Ranker score={step.get('recommendation_score', 0):.3f} "
                f"| BKT mastery before={step.get('mastery_score_before', 0):.3f} "
                f"| Milestone week {step.get('milestone_week', i+1)}"
                f"| Hours={step.get('estimated_hours', 0):.0f}h"
                f"{focus}"
            )
            skills = ", ".join(step.get("skills_taught", []))
            if skills:
                lines.append(f"           Teaches: {skills}")
            prereqs = ", ".join(step.get("prerequisite_skills", []))
            if prereqs:
                lines.append(f"           Prereqs: {prereqs}")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # Public API                                                            #
    # ------------------------------------------------------------------ #

    def explain_course(
        self,
        course_id: str,
        learner_profile: Dict,
        path_steps: List[Dict],
        mastery: Dict[str, float],
        conversation_history: List[Dict],
    ) -> str:
        self._ensure_init()
        context = self._build_context(learner_profile, path_steps, mastery, course_id)
        course_title = next(
            (s.get("course_title", course_id) for s in path_steps if s.get("course_id") == course_id),
            course_id,
        )
        user_msg = f"Explain exactly why '{course_title}' (ID: {course_id}) is in my learning path. Be specific and cite the actual numbers."
        return self._call_llm(context, conversation_history, user_msg)

    def chat(
        self,
        user_message: str,
        learner_profile: Dict,
        path_steps: List[Dict],
        mastery: Dict[str, float],
        conversation_history: List[Dict],
        course_id: Optional[str] = None,
    ) -> str:
        self._ensure_init()
        context = self._build_context(learner_profile, path_steps, mastery, course_id)
        return self._call_llm(context, conversation_history, user_message)

    def _call_llm(self, context: str, history: List[Dict], user_message: str) -> str:
        if self._client is None:
            return self._template_fallback(context, user_message)

        # Build messages
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Add recent history (last 6 turns)
        for msg in history[-6:]:
            role = msg.get("role", "user")
            if role in ("user", "assistant"):
                messages.append({"role": role, "content": msg.get("content", "")})

        # Append context + user question as a single user message
        augmented = f"{context}\n\n[LEARNER QUESTION]\n{user_message}"
        messages.append({"role": "user", "content": augmented})

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=0.3,
                max_tokens=600,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("OpenRouter API error: %s", e)
            return self._template_fallback(context, user_message)

    def _template_fallback(self, context: str, user_message: str) -> str:
        """Rule-based fallback that still cites actual data from context."""
        lines = context.split("\n")
        step_lines = [l for l in lines if "Step 1:" in l]
        mastery_lines = [l for l in lines if l.strip().startswith("  s_") or ": " in l]

        if step_lines:
            step = step_lines[0].strip()
            return (
                f"Based on your learning profile, the ML system determined:\n\n"
                f"{step}\n\n"
                f"This course was ranked highest because it closes the most critical skill gap "
                f"in your profile. Your BKT mastery scores are low for the prerequisite skills, "
                f"making this the optimal starting point per the LightGBM ranker.\n\n"
                f"_(Fallback explanation active. {('API Key is missing.' if not self._api_key else 'OpenRouter API is currently experiencing errors or rate limits.')})_"
            )
        return (
            "Your path was generated by the ML system: BKT mastery model identified your "
            "skill gaps, and the LightGBM ranker ordered courses to close them in prerequisite order.\n\n"
            f"_(Fallback explanation active. {('API Key is missing.' if not self._api_key else 'OpenRouter API is currently experiencing errors or rate limits.')})_"
        )
