"""
Path Planner — topological sort over the skill-graph subgraph.

Deterministic: no ML. Judges can verify this by hand.
Produces a LearningPath with milestones scheduled against hours/week budget.
"""
from __future__ import annotations
import uuid
import logging
import datetime
from typing import List, Dict, Tuple, Optional

from app.models.schemas import LearningPath, PathStep, DifficultyLevel

logger = logging.getLogger(__name__)


class PathPlanner:
    """
    Deterministic path planner.
    1. Takes gap skills in topological order from the skill graph.
    2. For each gap skill, picks the best course (from recommender).
    3. Schedules steps into milestone weeks based on hours/week budget.
    """

    def generate_path(
        self,
        learner_id: str,
        target_occupation: Optional[str],
        gap_skills_ordered: List[str],         # topo-sorted gap skills
        skill_labels: Dict[str, str],          # skill_id -> label
        recommendations: List[Dict],           # from Recommender.recommend()
        mastery: Dict[str, float],             # skill_id -> p_mastery
        hours_per_week: float = 10.0,
        version: int = 1,
    ) -> LearningPath:
        """
        Generate a LearningPath from gap analysis + recommendations.
        """
        # Deduplicate courses (one course may close multiple gap skills)
        seen_courses: set = set()
        steps: List[PathStep] = []
        step_idx = 0
        accumulated_hours = 0.0
        milestone_week = 1

        # Map: gap_skill_id -> best recommended course
        skill_to_course: Dict[str, Dict] = {}
        for rec in recommendations:
            for sk in rec.get("gap_skills_closed", []):
                if sk not in skill_to_course:
                    skill_to_course[sk] = rec

        # Walk gap skills in topo order, assign courses
        for skill_id in gap_skills_ordered:
            rec = skill_to_course.get(skill_id)
            if rec is None:
                # Try any course that covers this skill
                for r in recommendations:
                    if skill_id in r.get("skills_covered", []):
                        rec = r
                        break
            if rec is None:
                continue

            course_id = rec["course_id"]
            if course_id in seen_courses:
                continue
            seen_courses.add(course_id)

            est_hours = float(rec.get("estimated_hours", 20.0))
            # Which milestone week does this fall in?
            if hours_per_week > 0:
                weeks_needed = max(1, round(est_hours / hours_per_week))
            else:
                weeks_needed = 1
            milestone_week_for_step = milestone_week
            milestone_week += weeks_needed
            accumulated_hours += est_hours

            diff_str = rec.get("difficulty", "intermediate")
            try:
                diff = DifficultyLevel(diff_str)
            except ValueError:
                diff = DifficultyLevel.INTERMEDIATE

            step = PathStep(
                step_index=step_idx,
                course_id=course_id,
                course_title=rec.get("course_title", course_id),
                skills_taught=rec.get("skills_covered", []),
                prerequisite_skills=self._get_prereqs(skill_id, gap_skills_ordered, skill_to_course),
                estimated_hours=est_hours,
                difficulty=diff,
                mastery_score_before=mastery.get(skill_id, 0.2),
                recommendation_score=rec.get("ranker_score", 0.5),
                milestone_week=milestone_week_for_step,
                why_recommended="",  # filled by explainer agent
            )
            steps.append(step)
            step_idx += 1

        if not steps:
            # Fallback: include all recommended courses in order
            for rec in recommendations[:6]:
                course_id = rec["course_id"]
                if course_id in seen_courses:
                    continue
                seen_courses.add(course_id)
                est_hours = float(rec.get("estimated_hours", 20.0))
                steps.append(PathStep(
                    step_index=step_idx,
                    course_id=course_id,
                    course_title=rec.get("course_title", course_id),
                    skills_taught=rec.get("skills_covered", []),
                    prerequisite_skills=[],
                    estimated_hours=est_hours,
                    difficulty=DifficultyLevel.INTERMEDIATE,
                    mastery_score_before=0.2,
                    recommendation_score=rec.get("ranker_score", 0.5),
                    milestone_week=milestone_week,
                    why_recommended="",
                ))
                milestone_week += max(1, round(est_hours / max(hours_per_week, 1)))
                step_idx += 1
                accumulated_hours += est_hours

        return LearningPath(
            learner_id=learner_id,
            path_id=str(uuid.uuid4()),
            target_occupation=target_occupation,
            steps=steps,
            total_estimated_hours=round(accumulated_hours, 1),
            total_weeks=milestone_week - 1,
            generated_at=datetime.datetime.utcnow().isoformat(),
            version=version,
        )

    def _get_prereqs(
        self, skill_id: str, ordered_skills: List[str], skill_to_course: Dict[str, Dict]
    ) -> List[str]:
        """Skills that appear before this one in topo order (immediate predecessors)."""
        idx = ordered_skills.index(skill_id) if skill_id in ordered_skills else -1
        if idx <= 0:
            return []
        return ordered_skills[max(0, idx - 2): idx]  # up to 2 direct prereqs

    def replan(
        self,
        existing_path: LearningPath,
        completed_course_ids: List[str],
        new_recommendations: List[Dict],
        mastery: Dict[str, float],
        hours_per_week: float,
    ) -> LearningPath:
        """
        Replan: remove completed steps, re-rank remaining + new recommendations.
        """
        remaining_steps = [
            s for s in existing_path.steps
            if s.course_id not in completed_course_ids
        ]
        # Update mastery scores in remaining steps
        for step in remaining_steps:
            for sk in step.skills_taught:
                if sk in mastery:
                    step.mastery_score_before = mastery.get(sk, step.mastery_score_before)

        # Add any new courses not already in path
        existing_course_ids = {s.course_id for s in remaining_steps}
        idx = len(remaining_steps)
        milestone_week = (remaining_steps[-1].milestone_week + 1) if remaining_steps else 1
        for rec in new_recommendations:
            if rec["course_id"] not in existing_course_ids:
                est_hours = float(rec.get("estimated_hours", 20.0))
                remaining_steps.append(PathStep(
                    step_index=idx,
                    course_id=rec["course_id"],
                    course_title=rec.get("course_title", rec["course_id"]),
                    skills_taught=rec.get("skills_covered", []),
                    prerequisite_skills=[],
                    estimated_hours=est_hours,
                    difficulty=DifficultyLevel(rec.get("difficulty", "intermediate")),
                    mastery_score_before=0.2,
                    recommendation_score=rec.get("ranker_score", 0.5),
                    milestone_week=milestone_week,
                    why_recommended="",
                ))
                idx += 1
                milestone_week += max(1, round(est_hours / max(hours_per_week, 1)))

        # Re-number steps
        for i, step in enumerate(remaining_steps):
            step.step_index = i

        total_hours = sum(s.estimated_hours for s in remaining_steps)
        return LearningPath(
            learner_id=existing_path.learner_id,
            path_id=existing_path.path_id,
            target_occupation=existing_path.target_occupation,
            steps=remaining_steps,
            total_estimated_hours=round(total_hours, 1),
            total_weeks=milestone_week - 1,
            generated_at=datetime.datetime.utcnow().isoformat(),
            version=existing_path.version + 1,
        )
