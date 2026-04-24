# B02 — Data Models & Migrations

> **Objective:** Create all SQLAlchemy models, Pydantic schemas, and CRUD helpers for the full MathPath database schema. Generate Alembic migration.

**Depends on:** B01 (project skeleton)

---

## Tables to Create

### `users`

Minimal user table for MVP. Even single-user mode needs a row to satisfy FK references.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | default uuid4 |
| email | String | unique, nullable for MVP |
| display_name | String | |
| preferences_json | JSONB | daily study time, reminder time, etc. |
| created_at | DateTime | server default |
| updated_at | DateTime | auto-update |

For MVP, seed a default user on first startup. Auth integration (Clerk/Supabase/JWT) comes post-MVP.

### `books`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | default uuid4 |
| user_id | UUID (FK → users) | nullable for MVP |
| title | String | |
| source_type | Enum | `pdf`, `text`, `manual_seed` |
| file_url | String | nullable |
| status | Enum | `uploaded`, `processing`, `processed`, `failed` |
| created_at | DateTime | server default |
| updated_at | DateTime | auto-update |

### `book_chunks`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| book_id | UUID (FK → books) | |
| chunk_index | Integer | |
| chapter_title | String | nullable |
| section_title | String | nullable |
| page_start | Integer | nullable |
| page_end | Integer | nullable |
| raw_text | Text | |
| clean_text | Text | |
| token_count | Integer | |
| embedding | Vector(3072) | pgvector, nullable — see note on dimensions |
| created_at | DateTime | |

> **Embedding dimension note:** OpenAI `text-embedding-3-large` uses 3072, `text-embedding-3-small` uses 1536. Anthropic Voyage uses 1024. Use 3072 as the column size (largest), and zero-pad shorter embeddings. Alternatively, use a configurable setting. For MVP, pick one embedding provider and stick with it.

### `book_profiles`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| book_id | UUID (FK → books) | unique |
| profile_json | JSONB | full LLM output |
| detected_subject | String | |
| level | String | |
| style | String | |
| proof_density | String | |
| computation_density | String | |
| diagram_dependency | String | |
| confidence | Float | |
| created_at | DateTime | |

### `concepts`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| book_id | UUID (FK → books) | |
| name | String | |
| normalized_name | String | lowercase, deduped key |
| concept_type | Enum | `definition`, `theorem`, `technique`, `example`, `proof`, `application` |
| difficulty | Integer | 1–5 |
| importance | Enum | `core`, `supporting`, `optional` |
| source_chunk_ids | JSONB | list of chunk UUIDs |
| prerequisite_names | JSONB | list of strings |
| common_confusions | JSONB | list of strings |
| confidence | Float | |
| created_at | DateTime | |

### `concept_edges`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| book_id | UUID (FK → books) | |
| source_concept_id | UUID (FK → concepts) | |
| target_concept_id | UUID (FK → concepts) | |
| edge_type | Enum | `prerequisite`, `related`, `contrasts_with`, `application_of` |
| confidence | Float | |
| created_at | DateTime | |

### `study_plans`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| book_id | UUID (FK → books) | |
| user_id | UUID | nullable for MVP |
| status | String | `active`, `completed` |
| created_at | DateTime | |

### `tidbits`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| study_plan_id | UUID (FK → study_plans) | |
| book_id | UUID (FK → books) | |
| order_index | Integer | |
| title | String | |
| concept_id | UUID (FK → concepts) | nullable |
| learning_goal | Text | |
| source_chunk_ids | JSONB | |
| estimated_minutes | Integer | |
| difficulty | Integer | 1–5 |
| is_original_plan | Boolean | default True |
| inserted_after_tidbit_id | UUID | nullable |
| tidbit_type | Enum | `original`, `remedial`, `review`, `challenge` |
| created_at | DateTime | |

### `tidbit_lessons`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| tidbit_id | UUID (FK → tidbits) | |
| lesson_json | JSONB | |
| version | Integer | default 1 |
| created_at | DateTime | |

### `proof_ladders`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| tidbit_id | UUID (FK → tidbits) | |
| theorem_statement | Text | |
| proof_ladder_json | JSONB | |
| created_at | DateTime | |

### `tidbit_quizzes`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| tidbit_id | UUID (FK → tidbits) | |
| quiz_json | JSONB | |
| created_at | DateTime | |

### `answer_attempts`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| user_id | UUID | |
| tidbit_id | UUID (FK → tidbits) | |
| question_id | String | references quiz question id |
| input_mode | Enum | `transcript`, `voice`, `typed` |
| audio_url | String | nullable |
| transcript_raw | Text | nullable |
| transcript_final | Text | |
| score | Float | |
| feedback_json | JSONB | |
| misconception | String | nullable |
| created_at | DateTime | |

### `user_tidbit_progress`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| user_id | UUID | |
| tidbit_id | UUID (FK → tidbits) | |
| status | Enum | `locked`, `available`, `started`, `completed` |
| started_at | DateTime | nullable |
| completed_at | DateTime | nullable |
| quiz_score | Float | nullable |
| created_at | DateTime | |
| updated_at | DateTime | |

### `concept_mastery`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| user_id | UUID | |
| concept_id | UUID (FK → concepts) | |
| mastery_score | Float | 0.0–1.0 |
| confidence | Float | 0.0–1.0 |
| last_seen_at | DateTime | |
| created_at | DateTime | |
| updated_at | DateTime | |

### `tidbit_questions`

User-asked questions under a tidbit (for the "Ask a Question" feature).

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| user_id | UUID (FK → users) | |
| tidbit_id | UUID (FK → tidbits) | |
| question_text | Text | |
| answer_text | Text | |
| answer_grounding_json | JSONB | { source_chunk_ids, page_refs } |
| created_at | DateTime | |

### `learning_memory_events`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| user_id | UUID (FK → users) | |
| event_type | Enum | `question_asked`, `quiz_answered`, `mistake_detected`, `lesson_completed` |
| book_id | UUID (FK → books) | nullable |
| tidbit_id | UUID (FK → tidbits) | nullable |
| concept_id | UUID (FK → concepts) | nullable |
| payload_json | JSONB | |
| embedding | Vector(3072) | nullable |
| created_at | DateTime | |

---

## Key Indexes

Add these for query performance:

```text
book_chunks:        idx_book_chunks_book_id ON (book_id)
concepts:           idx_concepts_book_id ON (book_id)
                    idx_concepts_normalized_name ON (book_id, normalized_name)
concept_edges:      idx_concept_edges_book_id ON (book_id)
                    idx_concept_edges_source ON (source_concept_id)
                    idx_concept_edges_target ON (target_concept_id)
tidbits:            idx_tidbits_plan_id ON (study_plan_id)
                    idx_tidbits_order ON (study_plan_id, order_index)
tidbit_lessons:     idx_tidbit_lessons_tidbit_id ON (tidbit_id)
tidbit_quizzes:     idx_tidbit_quizzes_tidbit_id ON (tidbit_id)
answer_attempts:    idx_answer_attempts_user_tidbit ON (user_id, tidbit_id)
user_tidbit_progress: idx_utp_user_tidbit ON (user_id, tidbit_id) UNIQUE
concept_mastery:    idx_cm_user_concept ON (user_id, concept_id) UNIQUE
learning_memory_events: idx_lme_user_created ON (user_id, created_at DESC)
tidbit_questions:   idx_tq_tidbit ON (tidbit_id)
```

---

## Files to Create

```text
app/models/
  __init__.py
  user.py            → User
  book.py            → Book, BookChunk
  profile.py         → BookProfile
  concept.py         → Concept, ConceptEdge
  plan.py            → StudyPlan
  tidbit.py          → Tidbit
  lesson.py          → TidbitLesson
  proof.py           → ProofLadder
  quiz.py            → TidbitQuiz
  question.py        → TidbitQuestion
  grading.py         → AnswerAttempt
  progress.py        → UserTidbitProgress, ConceptMastery
  memory.py          → LearningMemoryEvent

app/schemas/
  __init__.py
  user.py
  book.py
  profile.py
  concept.py
  plan.py
  tidbit.py
  lesson.py
  proof.py
  quiz.py
  question.py
  grading.py
  progress.py
```

---

## Pydantic Schemas (key examples)

### BookCreate / BookRead

```python
class BookCreate(BaseModel):
    title: str
    source_type: str = "text"
    text: str | None = None

class BookRead(BaseModel):
    id: UUID
    title: str
    source_type: str
    status: str
    created_at: datetime
```

### ConceptRead

```python
class ConceptRead(BaseModel):
    id: UUID
    name: str
    concept_type: str
    difficulty: int
    importance: str
    source_chunk_ids: list
    prerequisite_names: list
    common_confusions: list
```

Create similar Create/Read/Update schemas for every model.

---

## CRUD Helpers

Create thin CRUD functions in `app/crud/` or keep them as classmethods on the models:

```python
def create_book(db: Session, data: BookCreate) -> Book: ...
def get_book(db: Session, book_id: UUID) -> Book | None: ...
def get_chunks_for_book(db: Session, book_id: UUID) -> list[BookChunk]: ...
```

---

## Acceptance Criteria

- [ ] `alembic revision --autogenerate -m "add all tables"` creates a clean migration.
- [ ] `alembic upgrade head` creates all tables in Postgres.
- [ ] Unit test can create a book, add chunks, add a concept, create a tidbit, create a lesson, create a quiz, create an answer attempt — all via CRUD helpers.
- [ ] pgvector extension is enabled (`CREATE EXTENSION IF NOT EXISTS vector`).

---

## Agent Prompt

```text
In mathpath/backend/app/models/ create SQLAlchemy models for: users, books, book_chunks, book_profiles, concepts, concept_edges, study_plans, tidbits, tidbit_lessons, proof_ladders, tidbit_quizzes, tidbit_questions, answer_attempts, user_tidbit_progress, concept_mastery, learning_memory_events.

Use UUID primary keys, DateTime columns with server defaults, JSONB for flexible fields, and pgvector Vector(3072) for embedding columns.

Add indexes for all frequently queried FK columns (see index list in the doc).

Add a UNIQUE constraint on (user_id, tidbit_id) for user_tidbit_progress and (user_id, concept_id) for concept_mastery.

In app/schemas/ create Pydantic v2 schemas (Create, Read, Update) for each model.

In app/db/base.py import all models so Alembic can see them.

Generate Alembic migration. Include `CREATE EXTENSION IF NOT EXISTS vector` in the migration.

Seed a default user on first migration or in a seed script.
```
