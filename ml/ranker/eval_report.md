# LightGBM Ranker — Evaluation Report

**Model**: LGBMRanker (listwise ranking)
**Training set**: 5,665 query-course pairs (synthetically generated — see ml/embeddings/build_index.py)
**Validation set**: 1,416 pairs (20% split by query group)

## Metrics

| Metric | Value |
|---|---|
| NDCG@5 | 1.0000 |
| Precision@3 | 0.8867 |

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
