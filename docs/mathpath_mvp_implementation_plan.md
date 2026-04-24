# MathPath MVP Implementation Plan

> **Product goal:** Turn any uploaded math textbook/chapter into a stable, textbook-grounded daily learning path.
>
> **MVP strategy:** Build the backend learning engine first, then build the mobile-first frontend on top of stable API contracts.

---

# 1. Product Definition

MathPath is an AI learning app that takes a math textbook/chapter and creates:

```text
Uploaded math book/chapter
  -> auto-detected subject and book profile
  -> textbook-grounded concept inventory
  -> prerequisite/concept graph
  -> stable tidbit roadmap
  -> layered explanations
  -> intuition-to-formal bridges
  -> iterative proof ladders
  -> care notes and correlation notes
  -> oral quizzes
  -> AI grading
  -> progress and mastery tracking
  -> optional review/remedial lessons
```

Core promise:

```text
Any math book in -> daily mastery path out.
```

---

# 2. Product Rules

## 2.1 Textbook-grounded first

Generated content must be grounded in the uploaded textbook.

Every important generated object should reference:

```text
source_chunk_ids
page numbers if available
chapter/section if available
definitions/theorems/examples used
```

The app should not become a generic ChatGPT math tutor. It should teach from the uploaded source.

## 2.2 Auto-identify book type

The user should not need to manually choose the subject.

The backend should infer:

```text
subject
topics
level
book style
proof density
computation density
diagram dependency
recommended learning strategy
```

Example output:

```json
{
  "detected_subjects": [
    {"subject": "linear_algebra", "confidence": 0.91}
  ],
  "level": "undergraduate",
  "style": "definition_theorem_proof",
  "proof_density": "medium",
  "computation_density": "medium",
  "diagram_dependency": "low"
}
```

## 2.3 Stable original plan

The original tidbit plan should not be rewritten once generated.

```text
Original plan:
T1 -> T2 -> T3 -> T4 -> T5

User path after struggle:
T1 -> T2 -> Review1 -> T3 -> Remedial1 -> T4 -> T5
```

Adaptation inserts support lessons; it does not mutate the original plan.

## 2.4 Structured JSON, not prose blobs

Store generated learning content as structured JSON.

This allows the frontend to render cards, collapsible sections, audio mode, quiz mode, and review mode.

## 2.5 Voice-first assessment, transcript-first backend

Backend MVP accepts text transcripts.

Mobile frontend records audio, transcribes it, allows editing, then sends transcript to grading endpoint.

---

# 3. MVP Scope

## 3.1 Must build

```text
1. Backend project skeleton
2. Database schema
3. Manual text ingestion
4. PDF extraction
5. Book profiling / auto-identification
6. Concept extraction
7. Concept graph generation
8. Stable tidbit planner
9. Layered lesson generator
10. Proof ladder generator
11. Care note generator
12. Quiz generator
13. Transcript-based answer grader
14. Progression/mastery engine
15. Memory event tables
16. CLI scripts for every pipeline stage
17. Basic API endpoints
18. Mobile frontend after backend APIs stabilize
19. Voice answer UX
20. Progress dashboard
```

## 3.2 Not required for MVP

```text
1. Handwritten math grading
2. Payments
3. Teacher dashboard
4. Social features
5. Full offline mode
6. Perfect PDF layout parsing
7. External memory systems like MemPalace
8. Complex auto-remediation
9. Multi-user classroom workflows
```

---

# 4. Recommended Stack

## 4.1 Backend

```text
Backend: FastAPI
Database: Postgres
Vector DB: pgvector
ORM: SQLAlchemy or SQLModel
Migrations: Alembic
Workers: RQ/Celery/Arq or simple background jobs first
Storage: local files first, S3 later
PDF extraction: PyMuPDF + pdfplumber
LLM: provider abstraction over OpenAI/Claude/Gemini
Speech-to-text: OpenAI transcription or equivalent
```

## 4.2 Frontend

```text
Mobile app: React Native + Expo
Navigation: Expo Router or React Navigation
State/data fetching: TanStack Query
Local state: Zustand or React Context
Forms: React Hook Form if needed
Audio recording: expo-av or expo-audio
File upload: expo-document-picker
Push notifications: expo-notifications
Auth: Clerk, Supabase Auth, or custom JWT
Math rendering: react-native-math-view or WebView/KaTeX fallback
```

---

# 5. High-Level Architecture

```text
React Native Mobile App
          |
          v
FastAPI Backend
          |
          v
Services Layer
  - ingestion
  - book profiling
  - concept extraction
  - graph building
  - tidbit planning
  - lesson generation
  - proof generation
  - quiz generation
  - grading
  - progression
  - memory
          |
          v
Postgres + pgvector
          |
          v
LLM Provider + File Storage
```

---

# 6. Repository Structure

```text
mathpath/
  backend/
    app/
      main.py

      api/
        routes/
          health.py
          books.py
          profiles.py
          concepts.py
          plans.py
          tidbits.py
          lessons.py
          quizzes.py
          grading.py
          progress.py
          memory.py

      core/
        config.py
        logging.py
        errors.py

      db/
        session.py
        base.py
        migrations/

      models/
        book.py
        chunk.py
        profile.py
        concept.py
        graph.py
        plan.py
        tidbit.py
        lesson.py
        proof.py
        quiz.py
        grading.py
        progress.py
        memory.py

      schemas/
        book.py
        profile.py
        concept.py
        plan.py
        tidbit.py
        lesson.py
        proof.py
        quiz.py
        grading.py
        progress.py

      services/
        ingestion/
          text_ingestor.py
          pdf_extractor.py
          chunker.py

        profiling/
          book_profiler.py
          section_profiler.py

        concept_extraction/
          concept_extractor.py
          concept_normalizer.py

        graph/
          concept_graph_builder.py

        planning/
          tidbit_planner.py

        lesson_generation/
          lesson_generator.py
          care_note_generator.py

        proof_generation/
          proof_ladder_generator.py

        quiz_generation/
          quiz_generator.py

        grading/
          answer_grader.py

        progression/
          mastery_engine.py
          next_item_selector.py

        memory/
          memory_event_writer.py
          memory_retriever.py

      llm/
        clients/
          base.py
          openai_client.py
        prompts/
          book_profile.md
          concept_extraction.md
          concept_graph.md
          tidbit_planning.md
          lesson_generation.md
          proof_ladder.md
          quiz_generation.md
          answer_grading.md
        validators/
          json_validator.py
          schema_validator.py

    scripts/
      seed_math_text.py
      ingest_pdf.py
      profile_book.py
      extract_concepts.py
      build_graph.py
      generate_plan.py
      generate_lesson.py
      generate_proof_ladder.py
      generate_quiz.py
      grade_answer.py
      run_pipeline.py

    tests/
      fixtures/
        calculus_limit_source.txt
        linear_algebra_span_source.txt
        probability_bayes_source.txt
        real_analysis_sequence_source.txt
      test_book_profile.py
      test_concept_extraction.py
      test_tidbit_planning.py
      test_lesson_generation.py
      test_quiz_generation.py
      test_answer_grading.py
      test_progression.py

  mobile/
    app/
      _layout.tsx
      index.tsx
      onboarding.tsx
      upload.tsx
      books/
        index.tsx
        [bookId].tsx
      tidbits/
        [tidbitId].tsx
        [tidbitId]/quiz.tsx
        [tidbitId]/ask.tsx
      progress.tsx
      settings.tsx

    src/
      api/
        client.ts
        books.ts
        tidbits.ts
        quizzes.ts
        grading.ts
        progress.ts
      components/
        LessonCard.tsx
        ProofLadder.tsx
        CareNoteList.tsx
        QuizQuestion.tsx
        VoiceRecorder.tsx
        ProgressBar.tsx
        MathText.tsx
      hooks/
        useBook.ts
        useTidbit.ts
        useVoiceRecording.ts
      stores/
        authStore.ts
      types/
        api.ts
      utils/
        upload.ts
        mathRendering.ts

  docs/
    MVP_IMPLEMENTATION_PLAN.md
```

---

# 7. Backend Database Schema

## 7.1 `books`

```sql
id
user_id
title
source_type              -- pdf, text, manual_seed
file_url
status                   -- uploaded, processing, processed, failed
created_at
updated_at
```

## 7.2 `book_chunks`

```sql
id
book_id
chunk_index
chapter_title
section_title
page_start
page_end
raw_text
clean_text
token_count
embedding
created_at
```

## 7.3 `book_profiles`

```sql
id
book_id
profile_json
detected_subject
level
style
proof_density
computation_density
diagram_dependency
confidence
created_at
```

## 7.4 `concepts`

```sql
id
book_id
name
normalized_name
concept_type             -- definition, theorem, technique, example, proof, application
difficulty               -- 1-5
importance               -- core, supporting, optional
source_chunk_ids          -- JSON/list
prerequisite_names        -- JSON/list from LLM
common_confusions         -- JSON/list
confidence
created_at
```

## 7.5 `concept_edges`

```sql
id
book_id
source_concept_id
target_concept_id
edge_type                 -- prerequisite, related, contrasts_with, application_of
confidence
created_at
```

## 7.6 `study_plans`

```sql
id
book_id
user_id
status
created_at
```

## 7.7 `tidbits`

```sql
id
study_plan_id
book_id
order_index
title
concept_id
learning_goal
source_chunk_ids
estimated_minutes
difficulty
is_original_plan
inserted_after_tidbit_id
tidbit_type               -- original, remedial, review, challenge
created_at
```

## 7.8 `tidbit_lessons`

```sql
id
tidbit_id
lesson_json
version
created_at
```

## 7.9 `proof_ladders`

```sql
id
tidbit_id
theorem_statement
proof_ladder_json
created_at
```

## 7.10 `tidbit_quizzes`

```sql
id
tidbit_id
quiz_json
created_at
```

## 7.11 `answer_attempts`

```sql
id
user_id
tidbit_id
question_id
input_mode                -- transcript, voice, typed
audio_url
transcript_raw
transcript_final
score
feedback_json
misconception
created_at
```

## 7.12 `user_tidbit_progress`

```sql
id
user_id
tidbit_id
status                   -- locked, available, started, completed
started_at
completed_at
quiz_score
created_at
updated_at
```

## 7.13 `concept_mastery`

```sql
id
user_id
concept_id
mastery_score             -- 0.0-1.0
confidence                -- 0.0-1.0
last_seen_at
created_at
updated_at
```

## 7.14 `learning_memory_events`

```sql
id
user_id
event_type                -- question_asked, quiz_answered, mistake_detected, lesson_completed
book_id
tidbit_id
concept_id
payload_json
embedding
created_at
```

---

# 8. Backend JSON Contracts

## 8.1 Book Profile JSON

```json
{
  "title_guess": "Linear Algebra Chapter 2",
  "detected_subjects": [
    {"subject": "linear_algebra", "confidence": 0.91}
  ],
  "topics": ["span", "basis", "linear independence"],
  "level": "undergraduate",
  "style": "definition_theorem_proof",
  "proof_density": "medium",
  "computation_density": "medium",
  "diagram_dependency": "low",
  "content_structure": {
    "has_definitions": true,
    "has_theorems": true,
    "has_proofs": true,
    "has_worked_examples": true,
    "has_exercises": true
  },
  "learning_strategy": {
    "proof_ladder_weight": "medium",
    "drill_practice_weight": "medium",
    "visual_intuition_weight": "high",
    "application_weight": "medium"
  }
}
```

## 8.2 Tidbit JSON

```json
{
  "title": "Span as all linear combinations",
  "concept_name": "Span",
  "learning_goal": "Understand span as all vectors reachable by linear combinations.",
  "prerequisites": ["Vector", "Scalar multiplication", "Linear combination"],
  "source_chunk_ids": [14, 15],
  "estimated_minutes": 15,
  "difficulty": 2,
  "grounding_notes": "Based on the source definition of span and the following worked example."
}
```

## 8.3 Lesson JSON

```json
{
  "title": "Span as Reachability",
  "concept": "Span",
  "learning_goal": "Understand span as all vectors reachable by linear combinations.",
  "grounding": {
    "primary_source_chunk_ids": [14, 15],
    "page_refs": [21, 22],
    "used_definitions": ["Definition of span"],
    "used_examples": ["Example after span definition"]
  },
  "core_idea": "Span is the set of all vectors you can create by scaling and adding given vectors.",
  "why_it_matters": "Span explains what a set of vectors can generate.",
  "explain_like_10th_grader": "Think of vectors as arrows. Span is all the places you can reach by stretching and adding those arrows.",
  "explain_like_engineer": "Span describes the output space reachable by combining available input directions.",
  "explain_like_math_mature": "The span of vectors v1,...,vk is the set of all linear combinations a1v1 + ... + akvk.",
  "intuition_bridge": {
    "simple_phrase": "All places you can reach using arrows.",
    "mathematical_translation": "All linear combinations of the given vectors.",
    "formal_bridge": "Stretching means scalar multiplication; adding arrows means vector addition."
  },
  "formal_definition_or_statement": "span(v1,...,vk) = {a1v1 + ... + akvk | ai are scalars}",
  "worked_examples": [
    {
      "title": "Two non-parallel vectors in R2",
      "problem": "Do two non-parallel vectors in R2 span R2?",
      "solution": "Yes. Since they point in different directions, their linear combinations can reach any vector in the plane.",
      "teaching_note": "This shows why direction diversity matters."
    }
  ],
  "common_mistakes": [
    {
      "mistake": "Confusing span with basis.",
      "correction": "A spanning set can have redundant vectors. A basis is a minimal independent spanning set."
    }
  ],
  "care_notes": [
    {
      "type": "connection",
      "note": "Column space is the span of matrix columns."
    },
    {
      "type": "warning",
      "note": "One nonzero vector in R2 spans only a line through the origin, not all of R2."
    }
  ],
  "real_world_connections": [
    {
      "domain": "Machine Learning",
      "connection": "Features span a space of possible representations."
    }
  ],
  "memory_hooks": [
    "Span = reachability using allowed directions."
  ],
  "quick_summary": "Span tells you everything a set of vectors can generate."
}
```

## 8.4 Proof Ladder JSON

```json
{
  "theorem": "The span of a set of vectors is a subspace.",
  "grounding": {
    "source_chunk_ids": [20, 21],
    "page_refs": [25]
  },
  "level_0_intuition": "If span contains all combinations, then combining things already in the span keeps you inside the span.",
  "level_1_proof_sketch": "Take two vectors in the span. Write them as linear combinations. Add them. The result is also a linear combination.",
  "level_2_guided_proof": [
    {
      "step": "Let x and y be in span(S).",
      "prompt": "What does it mean for x and y to be in span(S)?",
      "expected_answer": "They can be written as linear combinations of vectors in S.",
      "why_this_step_matters": "We translate set membership into algebra."
    }
  ],
  "level_3_formal_proof": "Let x,y be in span(S)...",
  "level_4_proof_commentary": [
    "The proof is mostly about unpacking the definition.",
    "Closure is the central idea."
  ]
}
```

## 8.5 Quiz JSON

```json
{
  "questions": [
    {
      "id": "q1",
      "type": "oral_concept_check",
      "question": "What does span mean in your own words?",
      "target_skill": "definition_understanding",
      "expected_answer": "Span is the set of all linear combinations of a given set of vectors.",
      "rubric": [
        "Mentions linear combinations",
        "Mentions given vectors",
        "Understands span is a set of possible resulting vectors"
      ],
      "difficulty": "easy",
      "grounding": {
        "source_chunk_ids": [14]
      }
    }
  ]
}
```

## 8.6 Grading Output JSON

```json
{
  "score": 0.75,
  "correctness": "mostly_correct",
  "feedback": "Good answer. You correctly said span involves combinations of vectors. To make it complete, mention scalar multiplication and addition.",
  "missing_points": [
    "Did not explicitly mention scalar multiplication"
  ],
  "misconception_detected": null,
  "follow_up_question": "Can a single nonzero vector span all of R2?",
  "mastery_updates": [
    {
      "concept": "Span",
      "delta": 0.07
    }
  ],
  "next_action": {
    "type": "continue",
    "reason": "Answer shows adequate conceptual understanding."
  }
}
```

---

# 9. Backend API Contracts

## 9.1 Health

```http
GET /health
```

Response:

```json
{"status": "ok"}
```

## 9.2 Create book from text

```http
POST /books/text
```

Request:

```json
{
  "title": "Sample Linear Algebra Chapter",
  "text": "..."
}
```

Response:

```json
{
  "book_id": "uuid",
  "status": "processed"
}
```

## 9.3 Upload PDF

```http
POST /books/upload
Content-Type: multipart/form-data
```

Response:

```json
{
  "book_id": "uuid",
  "status": "uploaded"
}
```

## 9.4 Run processing pipeline

```http
POST /books/{book_id}/process
```

Request:

```json
{
  "steps": ["profile", "concepts", "graph", "plan"]
}
```

Response:

```json
{
  "book_id": "uuid",
  "status": "processing"
}
```

For MVP this can run synchronously for small files or return job status.

## 9.5 Get book profile

```http
GET /books/{book_id}/profile
```

Response:

```json
{
  "book_id": "uuid",
  "profile": {}
}
```

## 9.6 Get study plan

```http
GET /books/{book_id}/plan
```

Response:

```json
{
  "book_id": "uuid",
  "study_plan_id": "uuid",
  "tidbits": []
}
```

## 9.7 Get tidbit

```http
GET /tidbits/{tidbit_id}
```

Response:

```json
{
  "tidbit": {},
  "lesson": {},
  "quiz": {},
  "progress": {}
}
```

## 9.8 Generate lesson

```http
POST /tidbits/{tidbit_id}/lesson/generate
```

Response:

```json
{
  "tidbit_id": "uuid",
  "lesson": {}
}
```

## 9.9 Generate quiz

```http
POST /tidbits/{tidbit_id}/quiz/generate
```

Response:

```json
{
  "tidbit_id": "uuid",
  "quiz": {}
}
```

## 9.10 Grade transcript answer

```http
POST /tidbits/{tidbit_id}/quiz/grade
```

Request:

```json
{
  "question_id": "q1",
  "transcript_final": "Span is all the combinations of given vectors."
}
```

Response:

```json
{
  "attempt_id": "uuid",
  "grading": {}
}
```

## 9.11 Ask question under tidbit

```http
POST /tidbits/{tidbit_id}/questions
```

Request:

```json
{
  "question": "Why is span different from basis?"
}
```

Response:

```json
{
  "answer_id": "uuid",
  "answer": "...",
  "grounding": {}
}
```

## 9.12 Get progress

```http
GET /progress
```

Response:

```json
{
  "active_book": {},
  "current_tidbit": {},
  "streak": 4,
  "overall_progress": 0.32,
  "weak_concepts": [],
  "recent_activity": []
}
```

---

# 10. Backend Implementation Order

## Milestone B1: Project skeleton

Tasks:

```text
1. Create FastAPI backend.
2. Add config management.
3. Add logging.
4. Add Postgres connection.
5. Add Alembic migrations.
6. Add health endpoint.
```

Acceptance criteria:

```text
- `uvicorn app.main:app --reload` starts.
- `GET /health` returns ok.
- DB connection works.
- First migration runs.
```

Coding agent prompt:

```text
Create a FastAPI backend with SQLAlchemy/Postgres, Alembic migrations, settings management, and a /health endpoint. Keep code modular under backend/app.
```

---

## Milestone B2: Data models and migrations

Tasks:

```text
1. Create models for books, chunks, profiles, concepts, edges, study_plans, tidbits, lessons, proof_ladders, quizzes, answer_attempts, progress, mastery, memory_events.
2. Create Pydantic schemas.
3. Create CRUD helpers.
```

Acceptance criteria:

```text
- All tables can be created through Alembic.
- Unit test can create a book, chunks, concept, tidbit, lesson, quiz, attempt.
```

---

## Milestone B3: Manual text ingestion

Tasks:

```text
1. Implement text ingestion endpoint/script.
2. Implement basic chunker.
3. Save chunks with indexes and token counts.
```

Acceptance criteria:

```text
- `scripts/seed_math_text.py` creates a book from a .txt fixture.
- Chunks are saved.
```

---

## Milestone B4: LLM client abstraction

Tasks:

```text
1. Create BaseLLMClient interface.
2. Create one provider implementation.
3. Add JSON response parsing.
4. Add retry handling.
5. Add schema validation helpers.
```

Acceptance criteria:

```text
- Any service can call `llm.generate_json(prompt, schema=...)`.
- Invalid JSON is retried or fails cleanly.
```

---

## Milestone B5: Book profiling

Tasks:

```text
1. Create book profiling prompt.
2. Feed sample chunks.
3. Save `book_profiles`.
```

Acceptance criteria:

```text
- Given calculus, linear algebra, probability, and real analysis fixtures, profiler returns reasonable subject/style metadata.
- Output stored in DB.
```

---

## Milestone B6: Concept extraction

Tasks:

```text
1. Extract concepts from chunks.
2. Normalize duplicate concepts.
3. Save concepts with source_chunk_ids.
```

Acceptance criteria:

```text
- For span source fixture, concepts include linear combination and span.
- Concepts include difficulty, importance, common confusions.
```

---

## Milestone B7: Concept graph

Tasks:

```text
1. Build prerequisite/related edges from concepts.
2. Store concept_edges.
```

Acceptance criteria:

```text
- Span depends on linear combination.
- Basis relates to span and linear independence.
```

---

## Milestone B8: Stable tidbit planning

Tasks:

```text
1. Generate study plan from concepts, graph, chunks, and book profile.
2. Save original tidbits.
3. Preserve order.
```

Acceptance criteria:

```text
- A book gets a study_plan.
- Plan has ordered tidbits.
- Each tidbit has source_chunk_ids and learning_goal.
```

---

## Milestone B9: Lesson generation

Tasks:

```text
1. Generate lesson_json for a tidbit.
2. Include layered explanations.
3. Include intuition bridge.
4. Include grounding fields.
5. Save lesson.
```

Acceptance criteria:

```text
- Lesson JSON passes schema.
- Lesson references source chunks.
- Lesson includes simple, engineer, and math-mature explanations.
```

---

## Milestone B10: Proof ladder generation

Tasks:

```text
1. Detect whether tidbit needs proof ladder.
2. Generate proof ladder when relevant.
3. Save proof ladder.
```

Acceptance criteria:

```text
- Theorem/proof fixture creates proof ladder.
- Non-proof concept can skip proof ladder.
```

---

## Milestone B11: Quiz generation

Tasks:

```text
1. Generate oral quiz JSON.
2. Include recall, explain-in-own-words, misconception, application, and proof-step if relevant.
3. Save quiz.
```

Acceptance criteria:

```text
- Quiz has 3-5 questions.
- Each question has expected_answer and rubric.
```

---

## Milestone B12: Answer grading

Tasks:

```text
1. Accept transcript answer.
2. Grade against question rubric.
3. Return feedback, score, missing points, next action.
4. Save answer_attempt.
```

Acceptance criteria:

```text
- "span is all combinations of vectors" is graded mostly/correct for span definition.
- Grading JSON passes schema.
```

---

## Milestone B13: Progression and mastery

Tasks:

```text
1. Update user_tidbit_progress.
2. Update concept_mastery.
3. Determine next action: continue, review, remedial.
4. Save memory event.
```

Acceptance criteria:

```text
- High score unlocks next tidbit.
- Medium score schedules review.
- Low score recommends remedial.
```

---

## Milestone B14: PDF ingestion

Tasks:

```text
1. Upload PDF.
2. Extract text page-by-page.
3. Chunk extracted text.
4. Save chunks with page refs.
```

Acceptance criteria:

```text
- A small PDF chapter can be uploaded and processed.
- Chunks have page_start/page_end.
```

---

## Milestone B15: End-to-end backend pipeline

Tasks:

```text
1. Create `scripts/run_pipeline.py`.
2. Run: ingest -> profile -> concepts -> graph -> plan.
3. Generate first lesson and quiz.
```

Acceptance criteria:

```text
One command can produce:
- book profile
- concepts
- graph
- study plan
- first lesson
- first quiz
```

---

# 11. Frontend MVP

The frontend should be mobile-first.

Use React Native + Expo.

The first frontend should consume backend APIs. Do not duplicate backend logic in the app.

---

# 12. Frontend Screens

## 12.1 Onboarding screen

Purpose:

```text
Introduce app and ask minimal preferences.
```

Fields:

```text
daily study time
preferred reminder time
optional learning goal
```

MVP can skip or hardcode this.

## 12.2 Upload screen

Purpose:

```text
User uploads a math PDF/chapter from phone.
```

Features:

```text
- Pick PDF from Files
- Upload to backend
- Show upload progress
- Trigger backend processing
- Show processing state
```

States:

```text
idle
uploading
uploaded
processing
processed
failed
```

## 12.3 Book processing screen

Purpose:

```text
Show what the backend detected.
```

Display:

```text
Detected subject
Level
Style
Proof density
Computation density
Number of tidbits generated
```

Example:

```text
Detected: Undergraduate Calculus
Style: Intuition + Worked Examples
Created: 18 daily tidbits
```

## 12.4 Books list screen

Purpose:

```text
Show uploaded books/chapters.
```

Display:

```text
Book title
Processing status
Progress percent
Current tidbit
```

## 12.5 Study plan screen

Purpose:

```text
Show stable roadmap.
```

Display:

```text
Day/order
Tidbit title
Status: locked, available, completed
Estimated minutes
```

Important:

```text
Original tidbits and inserted review/remedial lessons should be visually distinct.
```

## 12.6 Today’s tidbit screen

Purpose:

```text
Main learning screen.
```

Display as cards:

```text
Title
Core idea
Why it matters
Explain simply
Engineer explanation
Math mature explanation
Intuition bridge
Formal definition/statement
Worked examples
Proof ladder if available
Care notes
Real-world connections
Memory hooks
Quick summary
```

UX rule:

```text
Use collapsible cards. Do not show a wall of text.
```

## 12.7 Proof ladder component

Purpose:

```text
Show proof in progressive levels.
```

Levels:

```text
1. Intuition
2. Proof sketch
3. Guided proof
4. Formal proof
5. Commentary
```

UX:

```text
User can expand levels one by one.
```

## 12.8 Care notes component

Purpose:

```text
Show correlation/misconception/application notes.
```

Types:

```text
misconception
bridge
memory_hook
warning
application
future_use
proof_thinking
exam_trap
```

## 12.9 Ask question screen/panel

Purpose:

```text
User asks a question attached to current tidbit.
```

Features:

```text
- Text input first
- Voice input later
- Answer saved under tidbit
- Show previous Q&A for this tidbit
```

## 12.10 Voice quiz screen

Purpose:

```text
User answers oral questions by speaking.
```

Flow:

```text
1. Show question.
2. User taps/holds record.
3. App records audio.
4. Upload audio or transcribe.
5. Show transcript.
6. User edits transcript.
7. Submit transcript to grading endpoint.
8. Show feedback.
9. Continue to next question.
```

MVP fallback:

```text
Allow typed transcript if audio is not ready.
```

## 12.11 Quiz feedback screen

Display:

```text
Score
Correctness
Feedback
Missing points
Misconception detected
Follow-up question
Next action
```

## 12.12 Progress screen

Display:

```text
Current streak
Book progress
Current tidbit
Average quiz score
Weak concepts
Strong concepts
Recent activity
```

---

# 13. Frontend API Client

Create typed client functions.

```ts
// books.ts
uploadBookPdf(file): Promise<BookUploadResponse>
processBook(bookId): Promise<ProcessResponse>
getBooks(): Promise<Book[]>
getBookProfile(bookId): Promise<BookProfile>
getStudyPlan(bookId): Promise<StudyPlan>

// tidbits.ts
getTidbit(tidbitId): Promise<TidbitDetail>
generateLesson(tidbitId): Promise<Lesson>
generateQuiz(tidbitId): Promise<Quiz>

// grading.ts
gradeTranscript(tidbitId, questionId, transcript): Promise<GradingResponse>

// progress.ts
getProgress(): Promise<ProgressDashboard>
```

---

# 14. Frontend Implementation Order

## Milestone F1: Expo project skeleton

Tasks:

```text
1. Create Expo app.
2. Add navigation.
3. Add API client with base URL config.
4. Add basic screens.
```

Acceptance criteria:

```text
- App runs in simulator.
- Can navigate between Upload, Books, Plan, Tidbit, Progress.
- API client can call backend /health.
```

## Milestone F2: Books and upload UI

Tasks:

```text
1. Add document picker.
2. Upload PDF to backend.
3. Show upload/processing states.
4. Show book list.
```

Acceptance criteria:

```text
- User can pick PDF from phone.
- Backend receives file.
- UI shows processing status.
```

## Milestone F3: Book profile and study plan UI

Tasks:

```text
1. Show detected book profile.
2. Show tidbit roadmap.
3. Show locked/available/completed status.
```

Acceptance criteria:

```text
- Processed book displays detected subject/style.
- Study plan appears in order.
```

## Milestone F4: Tidbit lesson UI

Tasks:

```text
1. Fetch tidbit detail.
2. Render lesson cards.
3. Render math text.
4. Render care notes.
5. Render proof ladder.
```

Acceptance criteria:

```text
- Lesson JSON renders correctly.
- Long content is readable on mobile.
- Proof ladder can be expanded level by level.
```

## Milestone F5: Ask question UI

Tasks:

```text
1. Add question input.
2. Submit to backend.
3. Show answer.
4. Show saved Q&A.
```

Acceptance criteria:

```text
- User can ask question under tidbit.
- Answer persists and reloads.
```

## Milestone F6: Quiz transcript UI

Tasks:

```text
1. Show quiz question.
2. Add typed transcript input first.
3. Submit to grading endpoint.
4. Show feedback.
5. Move to next question.
```

Acceptance criteria:

```text
- User can complete quiz using typed transcript.
- Feedback screen works.
- Progress updates.
```

## Milestone F7: Voice recording

Tasks:

```text
1. Add audio recording.
2. Upload audio for transcription or transcribe through backend.
3. Show transcript.
4. Allow transcript editing.
5. Submit edited transcript to grading endpoint.
```

Acceptance criteria:

```text
- User can speak answer.
- Transcript is shown.
- User can edit transcript.
- Grading works from final transcript.
```

## Milestone F8: Progress dashboard

Tasks:

```text
1. Show streak.
2. Show book progress.
3. Show weak concepts.
4. Show recent activity.
```

Acceptance criteria:

```text
- Dashboard reflects completed tidbits and quiz scores.
```

## Milestone F9: Notifications

Tasks:

```text
1. Register push token.
2. Save token to backend.
3. Schedule reminder.
4. Show notification deep link to current tidbit.
```

Acceptance criteria:

```text
- App receives test notification.
- Tapping notification opens current tidbit.
```

---

# 15. CLI-First Backend Commands

Before frontend, backend must work through CLI.

```bash
python scripts/seed_math_text.py \
  --title "Span Fixture" \
  --file tests/fixtures/linear_algebra_span_source.txt

python scripts/profile_book.py \
  --book-id BOOK_ID

python scripts/extract_concepts.py \
  --book-id BOOK_ID

python scripts/build_graph.py \
  --book-id BOOK_ID

python scripts/generate_plan.py \
  --book-id BOOK_ID

python scripts/generate_lesson.py \
  --tidbit-id TIDBIT_ID

python scripts/generate_quiz.py \
  --tidbit-id TIDBIT_ID

python scripts/grade_answer.py \
  --tidbit-id TIDBIT_ID \
  --question-id q1 \
  --answer "span is all combinations of given vectors"
```

---

# 16. End-to-End MVP Flow

## Backend flow

```text
1. User uploads text/PDF.
2. Backend extracts/chunks source.
3. Backend profiles book.
4. Backend extracts concepts.
5. Backend builds graph.
6. Backend creates stable tidbit plan.
7. Backend generates lesson for first tidbit.
8. Backend generates quiz for first tidbit.
9. User submits transcript answer.
10. Backend grades answer.
11. Backend updates progress/mastery.
```

## Frontend flow

```text
1. Open app.
2. Upload PDF.
3. See detected subject/profile.
4. See generated roadmap.
5. Open today's tidbit.
6. Read layered explanation cards.
7. Ask question if needed.
8. Start oral quiz.
9. Speak answer.
10. Edit transcript.
11. Submit.
12. See feedback.
13. Progress updates.
```

---

# 17. Memory Strategy

Start with simple database memory.

Use:

```text
user_tidbit_progress
answer_attempts
tidbit_questions
concept_mastery
learning_memory_events
```

Then add pgvector embeddings for:

```text
user questions
AI answers
mistake summaries
feedback summaries
lesson summaries
```

Do not add MemPalace or any external memory system in MVP.

Recommended phases:

```text
Phase 1: Postgres structured memory
Phase 2: Postgres + pgvector semantic retrieval
Phase 3: Optional external memory layer only if app needs agentic long-term memory
```

---

# 18. Testing Strategy

## 18.1 Backend tests

Use golden fixtures:

```text
linear_algebra_span_source.txt
calculus_limit_source.txt
probability_bayes_source.txt
real_analysis_sequence_source.txt
```

Test that:

```text
- Book profiler identifies subject/style.
- Concept extractor finds core concepts.
- Tidbit planner creates reasonable order.
- Lesson generator includes all required sections.
- Quiz generator produces rubric-based questions.
- Grader accepts reasonable spoken-style answers.
- Progression updates mastery.
```

## 18.2 Frontend tests

Test:

```text
- Upload screen states.
- Study plan rendering.
- Lesson card rendering.
- Proof ladder expansion.
- Quiz flow.
- Transcript editing.
- Progress dashboard rendering.
```

---

# 19. Coding Agent Task List

## Backend Agent Tasks

```text
B1. Create FastAPI skeleton.
B2. Add DB models and migrations.
B3. Add text ingestion and chunking.
B4. Add LLM client abstraction.
B5. Add book profiling service.
B6. Add concept extraction service.
B7. Add concept graph builder.
B8. Add tidbit planner.
B9. Add lesson generator.
B10. Add proof ladder generator.
B11. Add quiz generator.
B12. Add answer grader.
B13. Add progression/mastery engine.
B14. Add PDF ingestion.
B15. Add end-to-end pipeline script.
B16. Add API routes.
```

## Frontend Agent Tasks

```text
F1. Create Expo app skeleton.
F2. Add API client.
F3. Add upload/book list screens.
F4. Add book profile/study plan screens.
F5. Add tidbit lesson screen.
F6. Add proof ladder and care note components.
F7. Add ask-question UI.
F8. Add typed transcript quiz flow.
F9. Add voice recording/transcript flow.
F10. Add progress dashboard.
F11. Add push notifications.
```

---

# 20. Recommended Development Order

Do this exact order:

```text
1. Backend skeleton
2. DB schema
3. Manual text ingestion
4. LLM abstraction
5. Book profiling
6. Concept extraction
7. Concept graph
8. Tidbit planner
9. Lesson generator
10. Quiz generator
11. Grader
12. Progression engine
13. PDF ingestion
14. Backend API routes
15. Mobile app skeleton
16. Upload UI
17. Plan UI
18. Lesson UI
19. Quiz transcript UI
20. Voice recording
21. Progress UI
22. Notifications
```

Reason:

```text
The app is only valuable if the backend learning objects are good.
The frontend should be built on stable content/API contracts.
```

---

# 21. MVP Definition of Done

The MVP is done when:

```text
1. User can upload a small math PDF/chapter.
2. Backend auto-detects subject/style.
3. Backend generates a stable tidbit roadmap.
4. User can open a tidbit on mobile.
5. Tidbit shows layered explanations, care notes, and proof ladder if relevant.
6. User can ask a question under the tidbit.
7. User can answer quiz by voice or transcript.
8. Backend grades the answer.
9. Progress/mastery updates.
10. User can see progress dashboard.
```

---

# 22. First Non-Goal Reminder

Do not optimize for all books perfectly in MVP.

Optimize for this:

```text
The architecture supports any math book,
but the first tests use a small set of representative math fixtures.
```

Representative fixtures:

```text
1. Linear algebra concept-heavy section
2. Calculus computation-heavy section
3. Probability concept/formula section
4. Real analysis proof-heavy section
```

---

# 23. One-Sentence Engineering Goal

```text
Build a source-grounded math learning engine that can turn textbook chunks into structured learning objects, then expose those objects through a mobile-first daily learning app.
```
