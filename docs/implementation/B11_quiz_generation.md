# B11 — Quiz Generation

> **Objective:** Generate oral quiz questions for each tidbit with expected answers, rubrics, difficulty levels, and grounding references.

**Depends on:** B04 (LLM), B08 (tidbits), B09 (lessons for context)

---

## Tasks

### 1. Quiz generation prompt — `app/llm/prompts/quiz_generation.md`

```markdown
You are a math oral examiner. Create quiz questions for the following lesson.

## Tidbit
Title: {title}
Concept: {concept_name}
Learning Goal: {learning_goal}

## Lesson Summary
{lesson_summary}

## Source Material
{source_text}

## Book Context
Subject: {subject}, Level: {level}

## Instructions
Generate 3-5 questions covering these categories:
1. **recall**: Can the student state the definition/theorem?
2. **explain_own_words**: Can they explain it simply?
3. **misconception_check**: Does a common confusion question trip them?
4. **application**: Can they apply the concept to a new example?
5. **proof_step** (only if proof ladder exists): Can they explain a proof step?

Each question must have:
- id: q1, q2, q3...
- type: one of the categories above
- question: the question text
- target_skill: what the question tests
- expected_answer: ideal answer
- rubric: list of 2-4 criteria for grading
- difficulty: easy, medium, hard
- grounding: { source_chunk_ids }

Respond ONLY with JSON:
{schema}
```

### 2. Quiz generator service — `app/services/quiz_generation/quiz_generator.py`

```python
class QuizGenerator:
    def __init__(self, llm: BaseLLMClient):
        ...

    async def generate_quiz(self, db: Session, tidbit_id: UUID) -> TidbitQuiz:
        """
        1. Load tidbit, lesson, concept, source chunks.
        2. Build prompt with lesson summary and source text.
        3. Call LLM.
        4. Validate: ensure 3-5 questions, each has required fields.
        5. Save TidbitQuiz row.
        6. Return quiz.
        """
```

### 3. API endpoints — `app/api/routes/quizzes.py`

```python
@router.post("/tidbits/{tidbit_id}/quiz/generate")
async def generate_quiz(tidbit_id: UUID, db = Depends(get_db)):
    ...

@router.get("/tidbits/{tidbit_id}/quiz")
async def get_quiz(tidbit_id: UUID, db = Depends(get_db)):
    ...
```

### 4. CLI script — `scripts/generate_quiz.py`

```bash
python scripts/generate_quiz.py --tidbit-id TIDBIT_ID
```

---

## Quiz JSON Schema

```json
{
  "questions": [
    {
      "id": "q1",
      "type": "recall | explain_own_words | misconception_check | application | proof_step",
      "question": "string",
      "target_skill": "string",
      "expected_answer": "string",
      "rubric": ["string"],
      "difficulty": "easy | medium | hard",
      "grounding": {
        "source_chunk_ids": ["uuid"]
      }
    }
  ]
}
```

---

## Files to Create

```text
app/services/quiz_generation/__init__.py
app/services/quiz_generation/quiz_generator.py
app/llm/prompts/quiz_generation.md
app/api/routes/quizzes.py
scripts/generate_quiz.py
```

---

## Acceptance Criteria

- [ ] Quiz has 3–5 questions.
- [ ] At least one `recall` and one `explain_own_words` question.
- [ ] Each question has `expected_answer` and `rubric` with 2+ criteria.
- [ ] Questions reference source chunks.
- [ ] Quiz is stored in `tidbit_quizzes` and retrievable.
- [ ] `proof_step` question only appears when proof ladder exists.

---

## Agent Prompt

```text
Create quiz generation for MathPath:

1. app/llm/prompts/quiz_generation.md — prompt that takes tidbit + lesson summary + source text, generates 3-5 oral quiz questions across recall, explain, misconception, application, proof-step categories. Each question has id, type, question, expected_answer, rubric, difficulty, grounding.

2. app/services/quiz_generation/quiz_generator.py — loads tidbit, lesson, chunks, calls LLM, validates 3-5 questions, saves TidbitQuiz.

3. app/api/routes/quizzes.py — POST to generate, GET to retrieve.

4. scripts/generate_quiz.py — CLI.
```
