# B09 — Lesson Generation

> **Objective:** Generate a richly structured lesson JSON for a tidbit, including layered explanations, intuition bridges, worked examples, care notes, memory hooks, and grounding references.

**Depends on:** B04 (LLM), B08 (tidbits exist), B03 (chunks for grounding)

---

## Tasks

### 1. Lesson generation prompt — `app/llm/prompts/lesson_generation.md`

```markdown
You are a math teacher creating a lesson for a student. The lesson must be grounded in the source textbook.

## Tidbit
Title: {title}
Concept: {concept_name}
Learning Goal: {learning_goal}

## Source Material
{source_chunks_text}

## Book Context
Subject: {subject}, Level: {level}, Style: {style}
Proof Ladder Weight: {proof_ladder_weight}

## Instructions
Create a lesson with ALL of the following sections:
- title
- concept
- learning_goal
- grounding (primary_source_chunk_ids, page_refs, used_definitions, used_examples)
- core_idea (one sentence)
- why_it_matters (one sentence)
- explain_like_10th_grader
- explain_like_engineer
- explain_like_math_mature
- intuition_bridge (simple_phrase, mathematical_translation, formal_bridge)
- formal_definition_or_statement
- worked_examples (1-3, each with title, problem, solution, teaching_note)
- common_mistakes (1-3, each with mistake, correction)
- care_notes (2-5, each with type and note; types: misconception, bridge, memory_hook, warning, application, future_use, proof_thinking, exam_trap)
- real_world_connections (1-2, each with domain and connection)
- memory_hooks (1-3 short phrases)
- quick_summary

Respond ONLY with JSON matching this schema:
{schema}
```

### 2. Lesson generator service — `app/services/lesson_generation/lesson_generator.py`

```python
class LessonGenerator:
    def __init__(self, llm: BaseLLMClient | None = None):
        self.llm = llm or get_llm_client(task="lesson_generation")

    async def generate_lesson(self, db: Session, tidbit_id: UUID) -> TidbitLesson:
        """
        1. Load tidbit and its concept.
        2. Load source chunks by tidbit.source_chunk_ids.
        3. Load book profile for context.
        4. Build prompt with all context.
        5. Call llm.generate_json() with LessonSchema.
        6. Create TidbitLesson row.
        7. Return lesson.
        """
```

### 3. Care note generator — `app/services/lesson_generation/care_note_generator.py`

If care notes from the main lesson prompt are insufficient, this can do a follow-up call:

```python
class CareNoteGenerator:
    async def generate_care_notes(
        self, concept_name: str, related_concepts: list[str], source_text: str
    ) -> list[dict]:
        """Generate additional care notes focusing on misconceptions, bridges, and exam traps."""
```

For MVP, the main lesson prompt should produce care notes. This service is a fallback.

**Provider recommendation:** Anthropic Claude excels at nuanced, layered explanations. This is one of the most important generation steps — the quality of lessons directly affects the learning experience. Configure via `LLM_LESSON_GENERATION_PROVIDER` + `LLM_LESSON_GENERATION_MODEL` in `.env`, or fall back to `LLM_ALL_*`.

**Large JSON output warning:** The lesson schema is large (~15 fields, nested objects). If a smaller/weaker model struggles to produce all fields reliably, consider splitting into 2 LLM calls: (1) core lesson (explanations, examples, formal content), (2) supplementary content (care notes, real-world connections, memory hooks).

### 4. API endpoint — `app/api/routes/lessons.py`

```python
@router.post("/tidbits/{tidbit_id}/lesson/generate")
async def generate_lesson(tidbit_id: UUID, db = Depends(get_db)):
    ...

@router.get("/tidbits/{tidbit_id}/lesson")
async def get_lesson(tidbit_id: UUID, db = Depends(get_db)):
    ...
```

### 5. CLI script — `scripts/generate_lesson.py`

```bash
python scripts/generate_lesson.py --tidbit-id TIDBIT_ID
```

---

## Lesson JSON Schema (full)

```json
{
  "title": "string",
  "concept": "string",
  "learning_goal": "string",
  "grounding": {
    "primary_source_chunk_ids": ["uuid"],
    "page_refs": [0],
    "used_definitions": ["string"],
    "used_examples": ["string"]
  },
  "core_idea": "string",
  "why_it_matters": "string",
  "explain_like_10th_grader": "string",
  "explain_like_engineer": "string",
  "explain_like_math_mature": "string",
  "intuition_bridge": {
    "simple_phrase": "string",
    "mathematical_translation": "string",
    "formal_bridge": "string"
  },
  "formal_definition_or_statement": "string",
  "worked_examples": [
    {
      "title": "string",
      "problem": "string",
      "solution": "string",
      "teaching_note": "string"
    }
  ],
  "common_mistakes": [
    {"mistake": "string", "correction": "string"}
  ],
  "care_notes": [
    {"type": "string", "note": "string"}
  ],
  "real_world_connections": [
    {"domain": "string", "connection": "string"}
  ],
  "memory_hooks": ["string"],
  "quick_summary": "string"
}
```

---

## Files to Create

```text
app/services/lesson_generation/__init__.py
app/services/lesson_generation/lesson_generator.py
app/services/lesson_generation/care_note_generator.py
app/llm/prompts/lesson_generation.md
app/api/routes/lessons.py
scripts/generate_lesson.py
```

---

## Acceptance Criteria

- [ ] Lesson JSON includes all required sections.
- [ ] `grounding.primary_source_chunk_ids` references actual chunk IDs.
- [ ] Three explanation levels are present and distinct in complexity.
- [ ] Intuition bridge connects simple phrase → math translation → formal.
- [ ] At least 1 worked example, 1 common mistake, 2 care notes.
- [ ] `quick_summary` is a single concise sentence.
- [ ] Lesson is stored in `tidbit_lessons` and retrievable via API.

---

## Agent Prompt

```text
Create lesson generation for MathPath:

1. app/llm/prompts/lesson_generation.md — prompt that takes tidbit + source chunks + book profile and returns a richly structured lesson JSON with layered explanations, intuition bridge, worked examples, common mistakes, care notes, real-world connections, memory hooks, and grounding references.

2. app/services/lesson_generation/lesson_generator.py — loads tidbit, chunks, profile; calls LLM; validates; saves TidbitLesson.

3. app/services/lesson_generation/care_note_generator.py — optional fallback for generating additional care notes.

4. app/api/routes/lessons.py — POST to generate, GET to retrieve.

5. scripts/generate_lesson.py — CLI.
```
