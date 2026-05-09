# MathPath MVP — Implementation Docs

> **Goal:** Turn any uploaded math textbook into a stable, textbook-grounded daily learning path.
>
> **Open-source, self-hosted:** User clones the repo, adds one API key, runs `docker compose up`, and connects their phone.

Each file below is a self-contained implementation spec for one milestone. They are ordered by dependency — build them in sequence.

---

## Quick Start (for end users)

```bash
git clone https://github.com/you/mathpath.git
cd mathpath
cp .env.example .env        # Edit: paste your OpenAI/Anthropic/Gemini key
docker compose up            # Starts Postgres + API
# Open phone app → enter laptop IP shown in terminal → done
```

See [B00_open_source_setup.md](B00_open_source_setup.md) for full details.

---

## Build Order

### Setup

| # | Milestone | File | Depends On |
|---|-----------|------|------------|
| B00 | Open-Source Setup | [B00_open_source_setup.md](B00_open_source_setup.md) | — |

### Backend (B01–B15)

| # | Milestone | File | Depends On |
|---|-----------|------|------------|
| B01 | Project Skeleton | [B01_project_skeleton.md](B01_project_skeleton.md) | B00 |
| B02 | Data Models & Migrations | [B02_data_models.md](B02_data_models.md) | B01 |
| ~~B03~~ | ~~Text Ingestion~~ — **removed** (PDF-only) | [B03_text_ingestion.md](B03_text_ingestion.md) | — |
| B04 | LLM Client Abstraction | [B04_llm_abstraction.md](B04_llm_abstraction.md) | B01 |
| B05 | Book Profiling | [B05_book_profiling.md](B05_book_profiling.md) | B02, B04, B14v2 |
| B06 | Concept Extraction | [B06_concept_extraction.md](B06_concept_extraction.md) | B02, B04, B05, B14v2 |
| B07 | Concept Graph | [B07_concept_graph.md](B07_concept_graph.md) | B06 |
| B08 | Tidbit Planner | [B08_tidbit_planner.md](B08_tidbit_planner.md) | B05, B06, B07 |
| B09 | Lesson Generation | [B09_lesson_generation.md](B09_lesson_generation.md) | B04, B08 |
| B10 | Proof Ladder | [B10_proof_ladder.md](B10_proof_ladder.md) | B04, B08 |
| B11 | Quiz Generation | [B11_quiz_generation.md](B11_quiz_generation.md) | B04, B08, B09 |
| B12 | Answer Grading | [B12_answer_grading.md](B12_answer_grading.md) | B04, B11 |
| B13 | Progression & Mastery | [B13_progression_mastery.md](B13_progression_mastery.md) | B12, B08 |
| ~~B14~~ | ~~PDF Ingestion (legacy, text-only)~~ — **removed** | [B14_pdf_ingestion.md](B14_pdf_ingestion.md) | — |
| **B14v2** | **Vision-First PDF Ingestion** (the only ingestion path) | [B14v2_vision_ingestion.md](B14v2_vision_ingestion.md) | B01, B02, B04 |
| B15 | End-to-End Pipeline | [B15_e2e_pipeline.md](B15_e2e_pipeline.md) | B14v2 + B05–B13 |

### Frontend (F01–F09)

| # | Milestone | File | Depends On |
|---|-----------|------|------------|
| F01 | Expo App Skeleton | [F01_expo_skeleton.md](F01_expo_skeleton.md) | Backend API contracts |
| F02 | Books & Upload UI | [F02_books_upload.md](F02_books_upload.md) | F01, B14, B15 |
| F03 | Book Profile & Study Plan | [F03_profile_study_plan.md](F03_profile_study_plan.md) | F01, F02, B05, B08 |
| F04 | Tidbit Lesson UI | [F04_tidbit_lesson.md](F04_tidbit_lesson.md) | F01, B09, B10 |
| F05 | Ask Question UI | [F05_ask_question.md](F05_ask_question.md) | F01, B09 |
| F06 | Quiz Transcript UI | [F06_quiz_transcript.md](F06_quiz_transcript.md) | F01, B11, B12 |
| F07 | Voice Recording | [F07_voice_recording.md](F07_voice_recording.md) | F06 |
| F08 | Progress Dashboard | [F08_progress_dashboard.md](F08_progress_dashboard.md) | F01, B13 |
| F09 | Notifications | [F09_notifications.md](F09_notifications.md) | F01 |

---

## Each Doc Contains

- **Objective** — what the milestone delivers
- **Dependencies** — which milestones must be done first
- **Tasks** — detailed implementation steps with code snippets
- **Files to Create** — exact file paths
- **JSON Schemas** — data contracts where applicable
- **Acceptance Criteria** — testable checklist
- **Agent Prompt** — copy-paste prompt for a coding agent

---

## Recommended Workflow

1. Start with B00 (Docker Compose, Dockerfile, .env.example).
2. Work through backend milestones B01–B15 in order.
3. Validate each milestone with its acceptance criteria before moving on.
4. After B15 (pipeline works end-to-end via CLI), start frontend F01–F09.
5. Test each frontend milestone against the running backend on a real phone.

### Self-hosted architecture

```text
User's Laptop (docker compose up)        User's Phone
┌────────────────────────────┐           ┌────────────────┐
│  Postgres + pgvector       │    WiFi   │  MathPath App  │
│  FastAPI (0.0.0.0:8000)   │◄──────────│  Settings:     │
│  .env: one LLM API key    │           │  192.168.x.x   │
└────────────────────────────┘           └────────────────┘
```

No cloud, no deployment, no domain. Same WiFi is all you need.

---

## Architecture Decisions

### LLM: Multi-provider from day one

All three providers are supported in MVP. See [B04](B04_llm_abstraction.md) for details.

| Provider | Best for | Key advantage |
|----------|----------|---------------|
| OpenAI (gpt-4o) | Structured output, concept extraction | Native JSON mode |
| Anthropic (Claude 3.5) | Lesson generation, grading, proofs | Strong reasoning, nuanced output |
| Gemini (2.0 Flash) | Book profiling, large context tasks | 1M context window, low cost |

Default provider is configurable. Per-task routing lets you use the best model for each job.

### Auth: Minimal for MVP

A `users` table exists with a seeded default user. All endpoints accept `user_id` but no real auth is enforced. Auth integration (Clerk, Supabase, or custom JWT) is a post-MVP addition. See [B02](B02_data_models.md).

### Database: Sync SQLAlchemy

MVP uses synchronous SQLAlchemy for simplicity. The LLM clients are async (using `asyncio`), but DB operations are sync. This avoids async session complexity while still allowing concurrent LLM calls.

### Embedding dimensions

Embedding columns use `Vector(3072)` to accommodate the largest common model (OpenAI `text-embedding-3-large`). Shorter embeddings from other providers are zero-padded. Pick one embedding provider and stick with it per deployment.

---

## Stack Reference

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, SQLAlchemy, Alembic, Postgres, pgvector |
| LLM | OpenAI + Anthropic + Gemini (provider-abstracted) |
| PDF | PyMuPDF + pdfplumber |
| Frontend | React Native, Expo, Expo Router |
| Data Fetching | TanStack Query, Axios |
| State | Zustand |
| Audio | expo-av |
| Math Rendering | KaTeX via WebView |

---

## Test Fixtures

Four golden fixtures (created in B03) are used throughout:

| Fixture | Subject | Style | Tests |
|---------|---------|-------|-------|
| `linear_algebra_span_source.txt` | Linear Algebra | Definition-theorem-proof | Concept extraction, graph, planning |
| `calculus_limit_source.txt` | Calculus | Computation + examples | Profiling, worked examples |
| `probability_bayes_source.txt` | Probability | Mixed, formula-heavy | Profiling, applications |
| `real_analysis_sequence_source.txt` | Real Analysis | Proof-heavy | Proof ladder, formal reasoning |
