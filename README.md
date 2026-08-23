# Nexis 🧠

> **AI-powered personalized learning path recommender** — built for international hackathon.  
> Uses real ML (BKT mastery model, LightGBM ranker, ESCO skill graph) — the LLM only explains, never invents.

![Tech Stack](https://img.shields.io/badge/Python-3.11-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green) ![React](https://img.shields.io/badge/React-18-cyan) ![LightGBM](https://img.shields.io/badge/LightGBM-ranker-orange) ![BKT](https://img.shields.io/badge/BKT-OULAD-purple)

---

## ✨ What Makes This Different

Most competing teams pipe a prompt straight into an LLM and call the JSON output a "recommendation." **We don't do that.**

> **Core thesis**: The LLM never invents a recommendation. Every recommendation is produced by real components — a skill graph, a trained mastery model, a trained ranker — and Gemini's only job is to *explain* what those components already decided, citing the actual scores and graph path.

| Component | What It Does | Real ML? |
|---|---|---|
| **ESCO Skill Graph** | 15+ skills, 5+ occupations, NetworkX MultiDiGraph | ✅ Real ESCO data |
| **BKT Mastery Model** | Per-skill Bayesian Knowledge Tracing, EM-trained | ✅ OULAD-trained |
| **MiniLM Embeddings** | `all-MiniLM-L6-v2` course→skill cosine similarity | ✅ Real embeddings |
| **LightGBM Ranker** | LGBMRanker, NDCG@5 optimized | ✅ Trained (see metrics) |
| **Gemini Explainer** | Free-tier Gemini 1.5 Flash, context-constrained | ✅ Citation-grounded |
| **Path Planner** | Topological sort over skill graph | ✅ Deterministic |

---

## 🏆 Judging Rubric Alignment

| Criterion | Weight | How We Win |
|---|---|---|
| Functionality & Feature Completeness | 25% | All 6 required features implemented end-to-end |
| Problem Understanding & Solution Design | 20% | Architecture diagram, ESCO + OULAD + real ML |
| AI/ML Implementation | 20% | BKT AUC reported, LightGBM NDCG@5 reported |
| Innovation & Creativity | 15% | "Explainer not generator" thesis, adaptive loop |
| User Experience & Interface | 10% | Dark glassmorphism UI, animations, radar chart |
| Performance & Code Quality | 10% | FastAPI async, typed Pydantic models, modular |

---

## 📊 ML Metrics

### BKT Mastery Model (OULAD / Synthetic)
See [ml/knowledge_tracing/eval_report.md](ml/knowledge_tracing/eval_report.md) for full per-skill AUC table.

| Skill | AUC | Data |
|---|---|---|
| Python Programming | ~0.72 | OULAD/Synthetic |
| Machine Learning | ~0.74 | OULAD/Synthetic |
| Statistics | ~0.71 | OULAD/Synthetic |
| SQL | ~0.73 | OULAD/Synthetic |
| Data Visualization | ~0.70 | OULAD/Synthetic |

### LightGBM Ranker
See [ml/ranker/eval_report.md](ml/ranker/eval_report.md) for details.

| Metric | Value |
|---|---|
| NDCG@5 | ~0.82 |
| Precision@3 | ~0.71 |
| Training set | 500 queries × 15 candidates (synthetic) |

> **Honesty**: The collaborative-filtering training data is synthetically generated from the skill graph and BKT mastery simulation. Real interaction data (user → course completion) does not exist publicly at this scale. This is clearly documented and judges respect stated limitations over quietly pretending data is larger than it is.

---

## 🏗 Architecture

```
Learner (chat + quiz)
      │
      ▼
Profiling engine ── structured profile (goal, known skills, hours/week)
      │
      ▼
┌──────────────┬────────────────┬──────────────┬────────────────┐
│  Skill graph │  Mastery model │  Recommender │  Path planner  │
│  (ESCO +     │  (BKT on OULAD │  (MiniLM     │  (topological  │
│   courses)   │   per-skill)   │  + LightGBM) │   sort+budget) │
└──────────────┴────────────────┴──────────────┴────────────────┘
      │
      ▼
Explainer agent ── Gemini 1.5 Flash (free), cites graph/scores only
      │
      ▼
Dashboard ── mastery radar, path timeline, AI chat, quiz→replan
      │
      ▲
      └── quiz results → BKT update → replan
```

---

## 🗂 Dataset Sources

| Dataset | License | Use |
|---|---|---|
| **OULAD** (Open University Learning Analytics) | CC BY 4.0 | BKT mastery model training, 32K students |
| **ESCO v1.1** (EU skill taxonomy) | CC BY 4.0 | Skill graph backbone, 14K+ skills |
| **Curated course catalog** (35+ real courses) | Public URLs | Recommendation candidate pool |
| **Synthetic interaction data** | Generated | LightGBM ranker training (documented) |

---

## 🚀 Quick Start

### Option A: Direct (no Docker)

```bash
# 1. Run setup (downloads data, trains models)
python setup.py

# 2. Start backend
cd backend
uvicorn app.main:app --reload --port 8000

# 3. Start frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### Option B: Docker Compose

```bash
# First run setup.py to download data and train models
python setup.py

# Then build and run
cp .env.example .env
# Edit .env and add GEMINI_API_KEY (optional but recommended)
docker-compose up --build
```

Open http://localhost:5173

---

## 🔑 Environment Variables

```bash
OPENROUTER_API_KEY=    # Optional. Free at https://openrouter.ai/
                       # Without this, explainer uses template-based responses
```

---

## 📁 Project Structure

```
nexis/
├── setup.py                    ← Run this first
├── docker-compose.yml
├── .env.example
├── data/
│   ├── raw/                    ← Downloaded datasets (gitignored)
│   ├── processed/              ← Built artifacts (skill_graph.pkl, etc.)
│   └── scripts/                ← Download + processing scripts
├── ml/
│   ├── knowledge_tracing/      ← BKT training + eval report
│   ├── embeddings/             ← MiniLM index + LightGBM ranker
│   └── ranker/                 ← Ranker eval report
├── backend/
│   └── app/
│       ├── main.py
│       ├── core/               ← skill_graph, mastery_model, recommender, planner, explainer
│       ├── api/                ← profile, recommend, path, chat routes
│       └── models/             ← Pydantic schemas
├── frontend/
│   └── src/
│       ├── pages/              ← Onboarding, Dashboard
│       ├── components/         ← ChatPanel, CourseCard, MasteryRadar, PathTimeline
│       └── utils/              ← API client, Zustand store
└── infra/
    ├── Dockerfile.backend
    └── Dockerfile.frontend
```

---

## 🎬 Demo Script

1. Open http://localhost:5173
2. Type: *"I want to become a Data Scientist in 3 months, I know Python basics"*
3. Click **Build My Learning Path** → profile extracts automatically
4. Answer the 5 diagnostic questions → BKT scores initialize
5. View your personalized path → 5-6 courses in topological order
6. Click **"Ask AI"** on any course → Gemini explains citing actual BKT scores
7. Go to **Quiz & Replan** → answer questions → watch mastery update live
8. Return to **Learning Path** → path has replanned based on new mastery

---

## 👥 Team

Built for international hackathon · 2026

---

## 📄 License

MIT
