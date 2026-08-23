# Architecture — Nexis

## System Overview

Nexis is a full-stack AI-powered personalized learning path recommender.
The key architectural principle: **LLM explains, ML decides**.

## Component Diagram

```
Learner Input (chat)
      |
      v
[Profiling Engine]
  - Gemini function-calling parses free-text goal
  - Extracts: target_occupation, known_skills, hours/week
  - Generates diagnostic quiz (5 questions)
      |
      v
[BKT Mastery Model]
  - Per-skill Bayesian Knowledge Tracing
  - Params estimated via EM on synthetic OULAD-consistent data
  - p_mastery(learner, skill) updated after each quiz answer
      |
      v
[Skill Graph] (NetworkX MultiDiGraph)
  - Nodes: skills (ESCO), courses (catalog), occupations (ESCO)
  - Edges: prerequisite (skill->skill), teaches (course->skill), essential (occ->skill)
  - shortest_gap_path(known_skills, target_occupation) -> topo-ordered gap skills
      |
      v
[Recommender] (Two-stage)
  Stage 1: MiniLM (all-MiniLM-L6-v2) embeddings + FAISS ANN retrieval
  Stage 2: LightGBM LGBMRanker re-scores candidates
  Features: content_sim, gap_priority, learner_mastery, difficulty
      |
      v
[Path Planner] (Deterministic)
  - Topological sort over gap skills
  - Schedule into milestone weeks (hours/week budget)
  - Produces: LearningPath with steps, milestones, prerequisite links
      |
      v
[Explainer Agent] (Gemini 1.5 Flash, free tier)
  - System prompt hard-constrains: only reference actual scores from context
  - Injects: BKT mastery values, ranker scores, graph paths
  - Returns: natural language explanation citing specific numbers
      |
      v
[Dashboard] (React + Vite)
  - Mastery radar chart (Recharts)
  - Path timeline with milestones
  - Course cards with "Why recommended?" expansion
  - Quiz -> BKT update -> replan (adaptive loop)
```

## Data Flow

1. User types goal -> Gemini parses to structured LearnerProfile
2. BKT initializes mastery priors (known skills = 0.85, unknown = 0.1)
3. Quiz answers -> BKT update -> new p_mastery per skill
4. Skill graph: gap_skills = occ_required - known_skills (topo-sorted)
5. FAISS retrieves top-50 candidate courses for gap query embedding
6. LightGBM re-ranks candidates -> top-10 recommendations
7. Path planner assigns courses to milestone weeks
8. Explainer generates citations for each step
9. User takes quiz -> BKT update -> if mastery > 0.8, skill marked as learned -> replan

## Database Schema (SQLite)

```
learners   (learner_id, goal, target_occupation, known_skills, hours_per_week)
mastery    (learner_id, skill_id, p_mastery, updated_at)
paths      (path_id, learner_id, path_data JSON, version)
```

## API Endpoints

```
POST /api/profile/create          # parse goal -> profile + quiz
POST /api/profile/quiz/submit     # score quiz -> BKT update
GET  /api/profile/{id}            # get profile
GET  /api/profile/{id}/mastery    # get all p_mastery values
POST /api/path/generate           # full pipeline -> learning path
GET  /api/path/{id}/current       # get current path
POST /api/path/replan             # replan after mastery update
GET  /api/recommend/{id}          # fresh recommendations
POST /api/chat                    # explainer chat (HTTP)
WS   /api/chat/ws/{id}            # explainer chat (WebSocket)
```
