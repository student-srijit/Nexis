#!/usr/bin/env python3
"""
Build FAISS embedding index and train LightGBM ranker.

Stage 1 — Embedding index:
  Encode all course descriptions with all-MiniLM-L6-v2.
  Save to data/processed/recommender/course_embeddings.npy + course_ids.json.

Stage 2 — LightGBM ranker:
  Build synthetic training set: positive = course closes highest-priority gap skill.
  Train LGBMRanker. Report NDCG@5, Precision@3.
  Save to data/processed/recommender/ranker.pkl.

Usage: python ml/embeddings/build_index.py
"""
import sys
import os
import json
import pickle
import logging
import numpy as np
import pandas as pd
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))
os.chdir(Path(__file__).parent.parent.parent)

PROCESSED_DIR = Path("data/processed")
RECOMMENDER_DIR = PROCESSED_DIR / "recommender"


def build_embedding_index():
    RECOMMENDER_DIR.mkdir(parents=True, exist_ok=True)

    # Load catalog
    catalog_path = PROCESSED_DIR / "catalog.json"
    if not catalog_path.exists():
        logger.error("catalog.json not found. Run build_course_catalog.py first.")
        sys.exit(1)

    with open(catalog_path) as f:
        catalog = json.load(f)

    logger.info("Loaded %d courses", len(catalog))

    course_ids = list(catalog.keys())
    descriptions = [
        f"{catalog[c].get('title', '')}. {catalog[c].get('description', '')}. "
        f"Skills: {', '.join(catalog[c].get('skills', []))}"
        for c in course_ids
    ]

    # Encode
    logger.info("Encoding course descriptions with MiniLM...")
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        embeddings = model.encode(descriptions, normalize_embeddings=True,
                                  show_progress_bar=True, batch_size=64)
        logger.info("Encoded %d courses, dim=%d", len(course_ids), embeddings.shape[1])
    except ImportError:
        logger.warning("sentence-transformers not available. Using random embeddings.")
        embeddings = np.random.randn(len(course_ids), 384).astype(np.float32)
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / (norms + 1e-9)

    # Encode skill labels
    skills_to_encode = [
        "s_python", "s_ml", "s_stats", "s_dl", "s_data_viz", "s_sql",
        "s_pandas", "s_nlp", "s_cv", "s_mlops", "s_feature_eng",
        "s_git", "s_r", "s_docker", "s_cloud",
    ]
    skill_labels = {
        "s_python": "Python programming language data science",
        "s_ml": "Machine learning algorithms supervised unsupervised",
        "s_stats": "Statistics probability distributions hypothesis testing",
        "s_dl": "Deep learning neural networks PyTorch TensorFlow",
        "s_data_viz": "Data visualization matplotlib seaborn plotly dashboards",
        "s_sql": "SQL database queries joins aggregations",
        "s_pandas": "Pandas dataframe data manipulation wrangling numpy",
        "s_nlp": "Natural language processing text classification transformers BERT",
        "s_cv": "Computer vision image classification object detection CNN",
        "s_mlops": "MLOps model deployment production monitoring CI/CD",
        "s_feature_eng": "Feature engineering selection extraction transformation",
        "s_git": "Git version control branching collaboration",
        "s_r": "R programming statistical computing ggplot2",
        "s_docker": "Docker containers containerization deployment",
        "s_cloud": "Cloud computing AWS GCP Azure scalable infrastructure",
    }

    logger.info("Encoding skill descriptions...")
    try:
        skill_emb_dict = {}
        for sid in skills_to_encode:
            emb = model.encode([skill_labels.get(sid, sid)], normalize_embeddings=True)[0]
            skill_emb_dict[sid] = emb
    except Exception:
        skill_emb_dict = {sid: np.random.randn(384).astype(np.float32) for sid in skills_to_encode}

    # Save
    np.save(RECOMMENDER_DIR / "course_embeddings.npy", embeddings.astype(np.float32))
    with open(RECOMMENDER_DIR / "course_ids.json", "w") as f:
        json.dump(course_ids, f)
    with open(RECOMMENDER_DIR / "skill_embeddings.pkl", "wb") as f:
        pickle.dump(skill_emb_dict, f)
    with open(RECOMMENDER_DIR / "catalog.json", "w") as f:
        json.dump(catalog, f)

    logger.info("OK Saved embedding index: %s", RECOMMENDER_DIR)
    return catalog, course_ids, embeddings, skill_emb_dict


def build_training_data(catalog: dict, course_ids: list, embeddings: np.ndarray,
                        skill_emb_dict: dict) -> pd.DataFrame:
    """
    Build self-labeled training set for LightGBM ranker.

    For each query (gap skill, learner mastery), generate:
      - Positive: courses that teach the gap skill (label=1)
      - Negatives: randomly sampled courses that don't (label=0)
    """
    logger.info("Building ranker training set...")
    np.random.seed(42)

    records = []
    skills_list = list(skill_emb_dict.keys())

    n_queries = 500

    for q_idx in range(n_queries):
        # Random query: 1-3 gap skills, random mastery
        n_gap = np.random.randint(1, 4)
        gap_skills = np.random.choice(skills_list, size=n_gap, replace=False).tolist()
        mastery = {s: np.random.uniform(0.1, 0.5) for s in gap_skills}

        # Build composite query embedding
        skill_vecs = []
        for sid in gap_skills:
            emb = skill_emb_dict[sid]
            w = 1.0 - mastery[sid]
            skill_vecs.append(emb * w)
        query_emb = np.mean(skill_vecs, axis=0)
        query_emb /= (np.linalg.norm(query_emb) + 1e-9)

        # Score all courses
        sims = embeddings @ query_emb  # cosine (normalized)

        # Label: positive if course teaches any gap skill
        positives = set()
        for cid in course_ids:
            course_skills = catalog[cid].get("skills", [])
            if any(s in course_skills for s in gap_skills):
                positives.add(cid)

        # Sample up to 5 positives + 10 negatives
        pos_ids = [c for c in course_ids if c in positives]
        neg_ids = [c for c in course_ids if c not in positives]
        np.random.shuffle(pos_ids)
        np.random.shuffle(neg_ids)
        sampled = pos_ids[:5] + neg_ids[:10]

        for cid in sampled:
            idx = course_ids.index(cid)
            content_sim = float(sims[idx])
            course_skills = catalog[cid].get("skills", [])
            is_positive = cid in positives
            gap_closed_count = sum(1 for s in gap_skills if s in course_skills)
            priority = max((1 - mastery[s] for s in gap_skills if s in course_skills), default=0.2)
            learner_mastery_avg = np.mean([mastery.get(s, 0.2) for s in course_skills]) if course_skills else 0.2
            diff_str = str(catalog[cid].get("difficulty", "intermediate"))
            diff_num = {"beginner": 0.0, "intermediate": 0.5, "advanced": 1.0}.get(diff_str, 0.5)

            records.append({
                "query_id": q_idx,
                "course_id": cid,
                "label": 1 if is_positive else 0,
                "content_sim": content_sim,
                "gap_skill_priority": priority,
                "learner_mastery": float(learner_mastery_avg),
                "difficulty_num": diff_num,
                "content_x_priority": content_sim * priority,
                "gap_size": 1.0 - float(learner_mastery_avg),
            })

    df = pd.DataFrame(records)
    logger.info("Training set: %d rows, %d queries, %.1f%% positives",
                len(df), n_queries, 100 * df["label"].mean())
    return df


def train_ranker(train_df: pd.DataFrame) -> tuple:
    """Train LightGBM LGBMRanker. Returns (ranker, ndcg5, prec3)."""
    from lightgbm import LGBMRanker
    from sklearn.model_selection import GroupShuffleSplit

    feature_cols = ["content_sim", "gap_skill_priority", "learner_mastery",
                    "difficulty_num", "content_x_priority", "gap_size"]

    X = train_df[feature_cols].values
    y = train_df["label"].values
    groups = train_df.groupby("query_id").size().values

    # Split by query
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, val_idx = next(gss.split(X, y, train_df["query_id"].values))

    X_train, y_train = X[train_idx], y[train_idx]
    X_val, y_val = X[val_idx], y[val_idx]
    groups_train = train_df.iloc[train_idx].groupby("query_id").size().values
    groups_val = train_df.iloc[val_idx].groupby("query_id").size().values

    ranker = LGBMRanker(
        n_estimators=200,
        learning_rate=0.05,
        num_leaves=31,
        min_child_samples=5,
        random_state=42,
        verbose=-1,
    )
    ranker.fit(
        X_train, y_train,
        group=groups_train,
        eval_set=[(X_val, y_val)],
        eval_group=[groups_val],
        eval_metric="ndcg",
        callbacks=[],
    )

    # Evaluate NDCG@5 and Precision@3
    val_df = train_df.iloc[val_idx].copy()
    val_df["pred_score"] = ranker.predict(X_val)

    ndcg5_scores = []
    prec3_scores = []

    for qid, grp in val_df.groupby("query_id"):
        grp_sorted = grp.sort_values("pred_score", ascending=False)
        labels_ranked = grp_sorted["label"].values

        # NDCG@5
        k = 5
        top_k = labels_ranked[:k]
        ideal = sorted(labels_ranked, reverse=True)[:k]

        def dcg(rels, k):
            return sum(r / np.log2(i + 2) for i, r in enumerate(rels[:k]))

        idcg = dcg(ideal, k)
        ndcg5 = dcg(top_k, k) / max(idcg, 1e-9)
        ndcg5_scores.append(ndcg5)

        # Precision@3
        prec3 = labels_ranked[:3].mean() if len(labels_ranked) >= 3 else labels_ranked.mean()
        prec3_scores.append(prec3)

    mean_ndcg5 = float(np.mean(ndcg5_scores))
    mean_prec3 = float(np.mean(prec3_scores))
    logger.info("Ranker NDCG@5=%.4f  Precision@3=%.4f", mean_ndcg5, mean_prec3)

    return ranker, mean_ndcg5, mean_prec3


def save_ranker_metrics(ndcg5: float, prec3: float, n_train: int, n_val: int):
    report_path = Path("ml/ranker/eval_report.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        f.write(f"""# LightGBM Ranker — Evaluation Report

**Model**: LGBMRanker (listwise ranking)
**Training set**: {n_train:,} query-course pairs (synthetically generated — see ml/embeddings/build_index.py)
**Validation set**: {n_val:,} pairs (20% split by query group)

## Metrics

| Metric | Value |
|---|---|
| NDCG@5 | {ndcg5:.4f} |
| Precision@3 | {prec3:.4f} |

## Features Used

| Feature | Description |
|---|---|
| content_sim | Cosine similarity of MiniLM course embedding vs. gap skill embedding |
| gap_skill_priority | 1 - p_mastery for the highest-priority gap skill covered by this course |
| learner_mastery | Average BKT p_mastery for skills this course teaches |
| difficulty_num | 0=beginner, 0.5=intermediate, 1.0=advanced |
| content_x_priority | Interaction: content_sim × gap_skill_priority |
| gap_size | 1 - learner_mastery_avg |

## Notes

- Training data is synthetic (bootstrapped from skill graph + BKT mastery simulation)
- Positive label = course teaches at least one gap skill for the query
- Negative sampling: 10 random non-covering courses per 5 positives
""")
    logger.info("OK Ranker eval report written to %s", report_path)


def main():
    catalog, course_ids, embeddings, skill_emb_dict = build_embedding_index()
    train_df = build_training_data(catalog, course_ids, embeddings, skill_emb_dict)

    try:
        ranker, ndcg5, prec3 = train_ranker(train_df)
        with open(RECOMMENDER_DIR / "ranker.pkl", "wb") as f:
            pickle.dump(ranker, f)
        logger.info("OK Saved ranker to %s", RECOMMENDER_DIR / "ranker.pkl")
        save_ranker_metrics(ndcg5, prec3, int(len(train_df) * 0.8), int(len(train_df) * 0.2))
    except ImportError as e:
        logger.warning("lightgbm not installed: %s — skipping ranker training", e)


if __name__ == "__main__":
    main()
