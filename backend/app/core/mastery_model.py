"""
Mastery Model — BKT-based per-skill mastery estimation.

Uses pyBKT for Bayesian Knowledge Tracing. One model per skill.
Pre-trained on OULAD assessment sequences.

Exposes:
  p_mastery(learner_id, skill_id) -> float
  update(learner_id, skill_id, correct: bool) -> float
"""
from __future__ import annotations
import os
import json
import logging
import pickle
from typing import Dict, Optional, List, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class LearnerState:
    """In-memory state for a single learner — p_know per skill."""
    def __init__(self):
        self.p_know: Dict[str, float] = {}  # skill_id -> current p(know)

    def get(self, skill_id: str, default: float = 0.2) -> float:
        return self.p_know.get(skill_id, default)

    def set(self, skill_id: str, value: float):
        self.p_know[skill_id] = float(np.clip(value, 0.0, 1.0))


class BKTParams:
    """Per-skill BKT parameters."""
    def __init__(self, learn: float, forget: float, slip: float, guess: float, prior: float):
        self.learn = learn    # P(transit)
        self.forget = forget  # P(forget)
        self.slip = slip      # P(slip)
        self.guess = guess    # P(guess)
        self.prior = prior    # P(L_0)

    def to_dict(self) -> dict:
        return {
            "learn": self.learn, "forget": self.forget,
            "slip": self.slip, "guess": self.guess, "prior": self.prior
        }

    @staticmethod
    def from_dict(d: dict) -> "BKTParams":
        return BKTParams(
            learn=d.get("learn", 0.3),
            forget=d.get("forget", 0.0),
            slip=d.get("slip", 0.1),
            guess=d.get("guess", 0.2),
            prior=d.get("prior", 0.2),
        )

    @staticmethod
    def default() -> "BKTParams":
        # Reasonable defaults from BKT literature
        return BKTParams(learn=0.3, forget=0.0, slip=0.1, guess=0.2, prior=0.2)


class MasteryModel:
    """
    Bayesian Knowledge Tracing mastery model.
    Stores trained per-skill BKT params, updates learner state in-memory.
    """

    def __init__(self):
        self._params: Dict[str, BKTParams] = {}  # skill_id -> BKT params
        self._learner_states: Dict[str, LearnerState] = {}
        self._default_params = BKTParams.default()

    # ------------------------------------------------------------------ #
    # Persistence                                                           #
    # ------------------------------------------------------------------ #

    def load(self, model_dir: str) -> None:
        params_path = os.path.join(model_dir, "bkt_params.json")
        if not os.path.exists(params_path):
            logger.warning("BKT params not found at %s — using defaults", params_path)
            return
        with open(params_path) as f:
            raw = json.load(f)
        self._params = {k: BKTParams.from_dict(v) for k, v in raw.items()}
        logger.info("Loaded BKT params for %d skills", len(self._params))

    def save(self, model_dir: str) -> None:
        os.makedirs(model_dir, exist_ok=True)
        params_path = os.path.join(model_dir, "bkt_params.json")
        with open(params_path, "w") as f:
            json.dump({k: v.to_dict() for k, v in self._params.items()}, f, indent=2)
        logger.info("Saved BKT params to %s", params_path)

    def set_params(self, skill_id: str, params: BKTParams) -> None:
        self._params[skill_id] = params

    # ------------------------------------------------------------------ #
    # BKT update equations                                                  #
    # ------------------------------------------------------------------ #

    def _bkt_update(self, p_know: float, correct: bool, params: BKTParams) -> float:
        """
        One BKT update step.
        Returns new p(L_t | evidence).
        """
        p_L = p_know
        # P(correct | L) = 1 - slip; P(correct | not L) = guess
        if correct:
            p_obs_given_L = 1.0 - params.slip
            p_obs_given_nL = params.guess
        else:
            p_obs_given_L = params.slip
            p_obs_given_nL = 1.0 - params.guess

        # Bayes update
        p_obs = p_obs_given_L * p_L + p_obs_given_nL * (1.0 - p_L)
        if p_obs < 1e-9:
            p_know_given_obs = p_L
        else:
            p_know_given_obs = (p_obs_given_L * p_L) / p_obs

        # Learning opportunity (transit)
        p_know_new = p_know_given_obs + (1.0 - p_know_given_obs) * params.learn
        # Forgetting (usually 0 in standard BKT)
        p_know_new = p_know_new * (1.0 - params.forget)
        return float(np.clip(p_know_new, 0.0, 1.0))

    # ------------------------------------------------------------------ #
    # Public API                                                            #
    # ------------------------------------------------------------------ #

    def _get_state(self, learner_id: str) -> LearnerState:
        if learner_id not in self._learner_states:
            self._learner_states[learner_id] = LearnerState()
        return self._learner_states[learner_id]

    def p_mastery(self, learner_id: str, skill_id: str) -> float:
        """Return current p(mastery) for learner on skill."""
        state = self._get_state(learner_id)
        params = self._params.get(skill_id, self._default_params)
        return state.get(skill_id, default=params.prior)

    def update(self, learner_id: str, skill_id: str, correct: bool) -> float:
        """
        Update mastery estimate after a quiz answer.
        Returns new p_mastery.
        """
        state = self._get_state(learner_id)
        params = self._params.get(skill_id, self._default_params)
        p_current = state.get(skill_id, default=params.prior)
        p_new = self._bkt_update(p_current, correct, params)
        state.set(skill_id, p_new)
        logger.debug("BKT update learner=%s skill=%s correct=%s: %.3f → %.3f",
                     learner_id, skill_id, correct, p_current, p_new)
        return p_new

    def batch_update(
        self, learner_id: str, responses: List[Tuple[str, bool]]
    ) -> Dict[str, float]:
        """
        Apply multiple quiz responses at once.
        responses: [(skill_id, correct), ...]
        Returns: {skill_id: new_p_mastery}
        """
        updates = {}
        for skill_id, correct in responses:
            updates[skill_id] = self.update(learner_id, skill_id, correct)
        return updates

    def initialize_from_known_skills(
        self, learner_id: str, known_skills: List[str], unknown_skills: Optional[List[str]] = None
    ) -> None:
        """
        Pre-warm learner state: known skills → high mastery, unknown → low.
        Called when a new learner profile is created.
        """
        state = self._get_state(learner_id)
        for skill_id in known_skills:
            state.set(skill_id, 0.85)  # strong prior for self-reported known
        if unknown_skills:
            for skill_id in unknown_skills:
                state.set(skill_id, 0.1)

    def get_all_mastery(self, learner_id: str, skill_ids: List[str]) -> Dict[str, float]:
        """Return p_mastery for all requested skills."""
        return {s: self.p_mastery(learner_id, s) for s in skill_ids}

    def is_mastered(self, learner_id: str, skill_id: str, threshold: float = 0.8) -> bool:
        return self.p_mastery(learner_id, skill_id) >= threshold
