"""
Profiling Engine — extracts structured LearnerProfile from free-text goal + quiz.

Uses Gemini 1.5 Flash function-calling to parse the goal into:
  - target_occupation (ESCO label)
  - target_skills (list of skills needed)
  - known_skills (self-reported)
  - hours_per_week

Then generates a diagnostic quiz (5-10 questions) to verify self-reported skills.
"""
from __future__ import annotations
import os
import json
import uuid
import logging
import re
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Fallback occupation→skill map for when Gemini is unavailable
OCCUPATION_SKILL_MAP = {
    "data scientist": {
        "occupation_id": "occ_ds",
        "skills": ["s_python", "s_ml", "s_stats", "s_dl", "s_data_viz", "s_sql"],
    },
    "machine learning engineer": {
        "occupation_id": "occ_ml_eng",
        "skills": ["s_python", "s_ml", "s_dl", "s_pandas"],
    },
    "data analyst": {
        "occupation_id": "occ_da",
        "skills": ["s_python", "s_sql", "s_data_viz", "s_pandas", "s_stats"],
    },
    "software engineer": {
        "occupation_id": "occ_se",
        "skills": ["s_python", "s_sql", "s_pandas"],
    },
    "web developer": {
        "occupation_id": "occ_web",
        "skills": ["s_python", "s_sql"],
    },
}

SKILL_QUIZ_QUESTIONS = {
    "s_python": {
        "question_text": "What does the following Python snippet print? `print([x**2 for x in range(3)])`",
        "options": ["[0, 1, 4]", "[1, 2, 3]", "[0, 2, 4]", "SyntaxError"],
        "correct_index": 0,
    },
    "s_stats": {
        "question_text": "Which measure of central tendency is most affected by outliers?",
        "options": ["Mean", "Median", "Mode", "Range"],
        "correct_index": 0,
    },
    "s_ml": {
        "question_text": "In supervised learning, what is overfitting?",
        "options": [
            "Model performs well on training but poorly on test data",
            "Model performs poorly on both training and test data",
            "Model is too simple to capture patterns",
            "Model has too few parameters",
        ],
        "correct_index": 0,
    },
    "s_dl": {
        "question_text": "What is the role of an activation function in a neural network?",
        "options": [
            "Introduces non-linearity so the network can learn complex patterns",
            "Normalizes the input data",
            "Controls the learning rate",
            "Selects which neurons to drop",
        ],
        "correct_index": 0,
    },
    "s_sql": {
        "question_text": "Which SQL clause filters rows AFTER grouping?",
        "options": ["HAVING", "WHERE", "GROUP BY", "ORDER BY"],
        "correct_index": 0,
    },
    "s_data_viz": {
        "question_text": "Which chart type is best for showing the distribution of a continuous variable?",
        "options": ["Histogram", "Pie chart", "Line chart", "Scatter plot"],
        "correct_index": 0,
    },
    "s_pandas": {
        "question_text": "In pandas, what does `df.groupby('col').mean()` return?",
        "options": [
            "Mean of each column grouped by 'col' values",
            "A single mean of the entire dataframe",
            "Groups the dataframe without computing anything",
            "Raises an error if 'col' has NaN",
        ],
        "correct_index": 0,
    },
}


class ProfilingEngine:
    def __init__(self, skill_graph=None):
        self._client = None
        self._api_key = os.getenv("OPENROUTER_API_KEY", "")
        self._model_name = os.getenv("OPENROUTER_MODEL", "openrouter/free")
        self._initialized = False
        self.skill_graph = skill_graph  # injected at runtime

    def _ensure_init(self):
        if self._initialized:
            return
        if not self._api_key:
            logger.warning("OPENROUTER_API_KEY not set — using keyword fallback for profiling.")
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
            logger.info("OpenRouter profiling engine initialized (model=%s)", self._model_name)
        except Exception as e:
            logger.warning("Failed to init OpenRouter for profiling: %s", e)
        self._initialized = True

    def parse_goal(self, goal_text: str) -> Tuple[Optional[str], List[str], List[str], float]:
        """
        Parse free-text goal into (occupation_id, target_skill_ids, known_skill_ids, hours_per_week).
        Uses Gemini if available, otherwise keyword matching.
        """
        self._ensure_init()

        if self._client:
            return self._parse_with_llm(goal_text)
        return self._parse_with_keywords(goal_text)

    def _parse_with_llm(self, goal_text: str) -> Tuple[Optional[str], List[str], List[str], float]:
        """Parse goal using OpenRouter LLM (google/gemini-2.0-flash-001 or configured model)."""
        prompt = f"""Extract structured information from this learning goal statement.

Goal: "{goal_text}"

Respond with valid JSON only, no markdown, no explanation:
{{
  "target_occupation": "one of: data scientist, machine learning engineer, data analyst, software engineer, web developer, or null",
  "known_skills": ["list of skills the person already knows from: python, statistics, machine learning, deep learning, sql, data visualization, pandas"],
  "hours_per_week": <number between 5 and 40, default 10>
}}"""
        try:
            response = self._client.chat.completions.create(
                model=self._model_name,
                messages=[
                    {"role": "system", "content": "You are a JSON extractor. Respond with valid JSON only, no markdown."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=512,
            )
            text = response.choices[0].message.content.strip()
            # Strip markdown code fences if present
            text = re.sub(r"```json\s*", "", text)
            text = re.sub(r"```\s*", "", text)
            parsed = json.loads(text)

            occ_label = parsed.get("target_occupation", "").lower() if parsed.get("target_occupation") else ""
            occ_id = None
            target_skills = []
            if occ_label and occ_label in OCCUPATION_SKILL_MAP:
                occ_data = OCCUPATION_SKILL_MAP[occ_label]
                occ_id = occ_data["occupation_id"]
                target_skills = occ_data["skills"]
            elif self.skill_graph:
                occ_id = self.skill_graph.find_occupation_by_label(occ_label)
                if occ_id:
                    target_skills = self.skill_graph.get_occupation_skills(occ_id)

            known_raw = parsed.get("known_skills", [])
            known_ids = self._labels_to_skill_ids(known_raw)
            hours = float(parsed.get("hours_per_week", 10.0))
            logger.info("LLM profiling: occ=%s, known=%s, hours=%s", occ_id, known_ids, hours)
            return occ_id, target_skills, known_ids, hours
        except Exception as e:
            logger.warning("OpenRouter parse error: %s -- falling back to keywords", e)
            return self._parse_with_keywords(goal_text)

    def _parse_with_keywords(self, goal_text: str) -> Tuple[Optional[str], List[str], List[str], float]:
        """Keyword-based fallback profiler."""
        goal_lower = goal_text.lower()

        occ_id = None
        target_skills = []
        for occ_label, occ_data in OCCUPATION_SKILL_MAP.items():
            if occ_label in goal_lower:
                occ_id = occ_data["occupation_id"]
                target_skills = occ_data["skills"]
                break

        if not occ_id:
            # Default to data scientist
            occ_id = "occ_ds"
            target_skills = OCCUPATION_SKILL_MAP["data scientist"]["skills"]

        known_ids = []
        skill_keywords = {
            "s_python": ["python"],
            "s_stats": ["statistics", "stats"],
            "s_ml": ["machine learning", "ml"],
            "s_dl": ["deep learning", "neural"],
            "s_sql": ["sql", "database"],
            "s_data_viz": ["visualization", "matplotlib", "tableau"],
            "s_pandas": ["pandas", "numpy"],
        }
        for sid, keywords in skill_keywords.items():
            if any(k in goal_lower for k in keywords):
                known_ids.append(sid)

        # Hours extraction
        hours = 10.0
        import re
        match = re.search(r"(\d+)\s*hour", goal_lower)
        if match:
            hours = float(match.group(1))

        return occ_id, target_skills, known_ids, hours

    def _labels_to_skill_ids(self, labels: List[str]) -> List[str]:
        label_map = {
            "python": "s_python",
            "statistics": "s_stats",
            "stats": "s_stats",
            "machine learning": "s_ml",
            "ml": "s_ml",
            "deep learning": "s_dl",
            "sql": "s_sql",
            "data visualization": "s_data_viz",
            "visualization": "s_data_viz",
            "pandas": "s_pandas",
        }
        ids = []
        for label in labels:
            label_lower = label.lower().strip()
            if label_lower in label_map:
                ids.append(label_map[label_lower])
        return ids

    def generate_quiz(self, target_skills: List[str], known_skills: List[str]) -> List[Dict]:
        """
        Generate 5 quiz questions for the learner's reported known skills.
        Focuses on skills they claim to know, to validate self-report.
        """
        questions = []
        # Prioritize skills they said they know (verify them)
        quiz_skills = [s for s in known_skills if s in SKILL_QUIZ_QUESTIONS]
        # Add a couple target skills they might not know
        for s in target_skills:
            if s not in known_skills and s in SKILL_QUIZ_QUESTIONS and s not in quiz_skills:
                quiz_skills.append(s)
            if len(quiz_skills) >= 5:
                break

        # Fill to 5 from available questions
        for s in SKILL_QUIZ_QUESTIONS:
            if s not in quiz_skills and len(quiz_skills) < 5:
                quiz_skills.append(s)

        for i, skill_id in enumerate(quiz_skills[:6]):
            q_data = SKILL_QUIZ_QUESTIONS[skill_id]
            questions.append({
                "question_id": f"q_{i}_{skill_id}",
                "skill_id": skill_id,
                "skill_label": skill_id.replace("s_", "").replace("_", " ").title(),
                "question_text": q_data["question_text"],
                "options": q_data["options"],
                "correct_index": q_data["correct_index"],
            })

        return questions
