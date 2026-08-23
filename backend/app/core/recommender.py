"""
Recommender — MiniLM embeddings + FAISS + LightGBM ranker.

Content signal:  sentence-transformers/all-MiniLM-L6-v2 embeddings of course
                 descriptions vs. gap-skill descriptions, cosine similarity.
Ranking:         LightGBM LGBMRanker trained on self-labeled pairs.
                 Positive = course that closes highest-priority gap skill.
                 Negatives = sampled others.

Exposes:
  recommend(learner_id, gap_skills, known_skills, top_k) -> List[Recommendation]
"""
from __future__ import annotations
import os
import json
import pickle
import logging
from typing import List, Dict, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na < 1e-9 or nb < 1e-9:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


class Recommender:
    """
    Two-stage recommender:
    Stage 1 (retrieval): FAISS ANN search — find candidate courses by embedding
    Stage 2 (ranking):   LightGBM LGBMRanker re-scores candidates
    """

    def __init__(self):
        self._encoder = None        # SentenceTransformer
        self._faiss_index = None    # faiss.Index
        self._course_ids: List[str] = []
        self._course_embeddings: Optional[np.ndarray] = None
        self._course_catalog: Dict[str, Dict] = {}  # course_id -> metadata
        self._ranker = None         # LGBMRanker or None
        self._ranker_features: List[str] = []
        self._skill_embeddings: Dict[str, np.ndarray] = {}  # skill_id -> embedding

    # ------------------------------------------------------------------ #
    # Load                                                                  #
    # ------------------------------------------------------------------ #

    def load(self, recommender_dir: str) -> None:
        catalog_path = os.path.join(recommender_dir, "catalog.json")
        embeddings_path = os.path.join(recommender_dir, "course_embeddings.npy")
        course_ids_path = os.path.join(recommender_dir, "course_ids.json")
        ranker_path = os.path.join(recommender_dir, "ranker.pkl")
        skill_emb_path = os.path.join(recommender_dir, "skill_embeddings.pkl")
        n2v_path = os.path.join(recommender_dir, "..", "node2vec.model")
        
        self._n2v = None

        # Always load encoder (needed at inference)
        self._load_encoder()

        if os.path.exists(catalog_path):
            with open(catalog_path) as f:
                self._course_catalog = json.load(f)

        if os.path.exists(course_ids_path):
            with open(course_ids_path) as f:
                self._course_ids = json.load(f)

        if os.path.exists(embeddings_path) and self._course_ids:
            self._course_embeddings = np.load(embeddings_path)
            self._build_faiss_index()

        if os.path.exists(ranker_path):
            with open(ranker_path, "rb") as f:
                self._ranker = pickle.load(f)
            logger.info("Loaded LightGBM ranker")

        if os.path.exists(skill_emb_path):
            with open(skill_emb_path, "rb") as f:
                self._skill_embeddings = pickle.load(f)

        if os.path.exists(n2v_path):
            try:
                from gensim.models import Word2Vec
                self._n2v = Word2Vec.load(n2v_path)
                logger.info("Loaded Node2Vec structural embeddings")
            except Exception as e:
                logger.warning("Could not load Node2Vec: %s", e)

        logger.info("Recommender loaded: %d courses", len(self._course_ids))

    def _load_encoder(self):
        """Lazy loader — called at load() time but catches all errors gracefully."""
        try:
            from sentence_transformers import SentenceTransformer
            self._encoder = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Loaded MiniLM encoder")
        except Exception as e:
            logger.warning("Could not load SentenceTransformer at startup: %s — will retry on first encode call", e)
            self._encoder = None

    def _build_faiss_index(self):
        try:
            import faiss
            d = self._course_embeddings.shape[1]
            self._faiss_index = faiss.IndexFlatIP(d)  # inner product = cosine on normalized vecs
            normed = self._course_embeddings / (
                np.linalg.norm(self._course_embeddings, axis=1, keepdims=True) + 1e-9
            )
            self._faiss_index.add(normed.astype(np.float32))
            logger.info("Built FAISS index: %d vectors, dim=%d", len(self._course_ids), d)
        except Exception as e:
            logger.warning("Could not build FAISS index: %s — will use brute-force cosine", e)

    # ------------------------------------------------------------------ #
    # Encode                                                                #
    # ------------------------------------------------------------------ #

    def _encode(self, texts: list) -> np.ndarray:
        if self._encoder is None:
            # Retry loading if it failed at startup (e.g., cold-start race condition)
            try:
                from sentence_transformers import SentenceTransformer
                self._encoder = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("MiniLM encoder loaded on demand")
            except Exception as e:
                logger.warning("SentenceTransformer still unavailable: %s — using random vecs", e)
                return np.random.randn(len(texts), 384).astype(np.float32)
        return self._encoder.encode(texts, normalize_embeddings=True, show_progress_bar=False)

    def _get_skill_embedding(self, skill_id: str, skill_label: str) -> np.ndarray:
        if skill_id in self._skill_embeddings:
            return self._skill_embeddings[skill_id]
        emb = self._encode([skill_label])[0]
        self._skill_embeddings[skill_id] = emb
        return emb

    # ------------------------------------------------------------------ #
    # Retrieval                                                             #
    # ------------------------------------------------------------------ #

    def _retrieve_candidates(
        self, query_embedding: np.ndarray, top_k: int = 50
    ) -> List[Tuple[str, float]]:
        """FAISS ANN search; returns (course_id, similarity) pairs."""
        if self._faiss_index is not None and len(self._course_ids) > 0:
            q = query_embedding.reshape(1, -1).astype(np.float32)
            scores, indices = self._faiss_index.search(q, min(top_k, len(self._course_ids)))
            return [(self._course_ids[i], float(s)) for i, s in zip(indices[0], scores[0]) if i >= 0]

        if self._course_embeddings is not None:
            sims = self._course_embeddings @ query_embedding
            top_idx = np.argsort(-sims)[:top_k]
            return [(self._course_ids[i], float(sims[i])) for i in top_idx]

        # Demo fallback — return all catalog courses
        return [(cid, 0.5) for cid in list(self._course_catalog.keys())[:top_k]]

    # ------------------------------------------------------------------ #
    # Feature extraction for ranker                                         #
    # ------------------------------------------------------------------ #

    def _build_features(
        self,
        course_id: str,
        content_sim: float,
        gap_skill_priority: float,
        learner_mastery: float,
        course_difficulty_num: float,
    ) -> np.ndarray:
        return np.array([
            content_sim,
            gap_skill_priority,
            learner_mastery,
            course_difficulty_num,
            content_sim * gap_skill_priority,
            1.0 - learner_mastery,  # gap size
        ], dtype=np.float32)

    @staticmethod
    def _difficulty_to_num(diff: str) -> float:
        return {"beginner": 0.0, "intermediate": 0.5, "advanced": 1.0}.get(diff.lower(), 0.5)

    # ------------------------------------------------------------------ #
    # Main recommend API                                                    #
    # ------------------------------------------------------------------ #

    def recommend(
        self,
        gap_skills: List[Tuple[str, str]],   # [(skill_id, skill_label), ...]
        mastery: Dict[str, float],            # skill_id -> p_mastery
        top_k: int = 10,
    ) -> List[Dict]:
        """
        Return top-k recommended courses for the given gap skills.

        Returns list of dicts with keys matching Recommendation schema.
        """
        if not gap_skills:
            return []

        # Build a composite query embedding: average of gap skill embeddings,
        # weighted by priority (1 - p_mastery → biggest gaps first)
        skill_vecs = []
        priorities = []
        for skill_id, skill_label in gap_skills:
            emb = self._get_skill_embedding(skill_id, skill_label)
            p = mastery.get(skill_id, 0.2)
            weight = 1.0 - p  # bigger gap = more weight
            skill_vecs.append(emb * weight)
            priorities.append((skill_id, weight))

        query_emb = np.mean(skill_vecs, axis=0)
        query_emb = query_emb / (np.linalg.norm(query_emb) + 1e-9)

        # Build structural query embedding from Node2Vec (Stretch Goal)
        query_struct = np.zeros(32, dtype=np.float32)
        if getattr(self, "_n2v", None) is not None:
            struct_vecs = []
            for skill_id, weight in priorities:
                if skill_id in self._n2v.wv:
                    struct_vecs.append(self._n2v.wv[skill_id] * weight)
            if struct_vecs:
                query_struct = np.mean(struct_vecs, axis=0)
                if np.linalg.norm(query_struct) > 1e-9:
                    query_struct = query_struct / np.linalg.norm(query_struct)

        # Retrieve candidates
        candidates = self._retrieve_candidates(query_emb, top_k=min(50, max(20, top_k * 5)))

        # Score each candidate
        results = []
        for course_id, content_sim in candidates:
            meta = self._course_catalog.get(course_id, {})
            if not meta:
                continue

            # Which gap skills does this course close?
            course_skills = meta.get("skills", [])
            closed = [s for s, _ in gap_skills if s in course_skills]
            if not closed:
                # allow courses that teach at least partial overlap, otherwise skip
                pass

            diff_str = str(meta.get("difficulty", "intermediate"))
            diff_num = self._difficulty_to_num(diff_str)

            # Gap priority: max priority of skills this course closes
            priority = max((w for s, w in priorities if s in course_skills), default=0.2)
            learner_mastery_avg = np.mean([mastery.get(s, 0.2) for s in course_skills]) if course_skills else 0.2

            # Compute structural similarity (Node2Vec) and fuse
            struct_sim = 0.0
            if getattr(self, "_n2v", None) is not None and course_skills:
                c_struct_vecs = [self._n2v.wv[s] for s in course_skills if s in self._n2v.wv]
                if c_struct_vecs and np.linalg.norm(query_struct) > 1e-9:
                    c_struct = np.mean(c_struct_vecs, axis=0)
                    if np.linalg.norm(c_struct) > 1e-9:
                        c_struct = c_struct / np.linalg.norm(c_struct)
                        struct_sim = float(np.dot(query_struct, c_struct))
            
            fused_sim = content_sim
            if getattr(self, "_n2v", None) is not None:
                fused_sim = 0.7 * content_sim + 0.3 * struct_sim

            if self._ranker is not None:
                feats = self._build_features(
                    course_id, fused_sim, priority, float(learner_mastery_avg), diff_num
                ).reshape(1, -1)
                ranker_score = float(self._ranker.predict(feats)[0])
            else:
                ranker_score = fused_sim * (1.0 - float(learner_mastery_avg) + 0.1)

            results.append({
                "course_id": course_id,
                "course_title": str(meta.get("title", course_id)),
                "provider": str(meta.get("provider", "Unknown")),
                "skills_covered": course_skills,
                "gap_skills_closed": closed,
                "content_similarity": round(content_sim, 4),
                "ranker_score": round(ranker_score, 4),
                "difficulty": diff_str,
                "estimated_hours": float(meta.get("estimated_hours", 20.0)),
                "url": meta.get("url", ""),
                "description": str(meta.get("description", "")),
            })

        # Sort by ranker score descending
        results.sort(key=lambda x: -x["ranker_score"])
        return results[:top_k]
