# BKT Knowledge Tracing — Evaluation Report

**Data source**: Synthetic (Synthetically generated — see data/scripts/train_bkt.py for generation logic)

**Records used**: 59,626  |  **Unique learners**: 2,000

**Model**: Bayesian Knowledge Tracing (BKT) — one model per skill, parameters estimated via EM.


## Per-Skill AUC

| Skill ID | AUC (test split) | Notes |
|---|---|---|
| s_cloud | N/A | default params (insufficient data) |
| s_cv | N/A | default params (insufficient data) |
| s_data_viz | 0.8489 | trained |
| s_dl | 0.8299 | trained |
| s_docker | N/A | default params (insufficient data) |
| s_feature_eng | 0.8548 | trained |
| s_git | 0.8440 | trained |
| s_ml | 0.8577 | trained |
| s_mlops | N/A | default params (insufficient data) |
| s_nlp | N/A | default params (insufficient data) |
| s_pandas | 0.8634 | trained |
| s_python | 0.8450 | trained |
| s_r | 0.8558 | trained |
| s_sql | 0.8618 | trained |
| s_stats | 0.8644 | trained |

**Mean AUC**: 0.8526  |  **Min**: 0.8299  |  **Max**: 0.8644


## Interpretation

AUC > 0.7 indicates the BKT model meaningfully predicts whether a learner will answer correctly given their interaction history. We use BKT in production (not DKT) because the inference cost is O(1) per update vs O(T) for the LSTM, and the AUC difference is within noise on this dataset size.
