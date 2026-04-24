# B12 — Answer Grading

> **Objective:** Grade a student's transcript answer against a quiz question's rubric. Return score, feedback, missing points, misconception detection, and next action recommendation.

**Depends on:** B04 (LLM), B11 (quiz exists)

---

## Tasks

### 1. Answer grading prompt — `app/llm/prompts/answer_grading.md`

```markdown
You are a math tutor grading an oral quiz answer.

## Question
{question_text}

## Expected Answer
{expected_answer}

## Rubric
{rubric_json}

## Student's Answer (transcript)
{transcript}

## Concept Context
Concept: {concept_name}
Learning Goal: {learning_goal}

## Instructions
Grade the student's answer and provide:
- score: 0.0 to 1.0
- correctness: one of [correct, mostly_correct, partially_correct, incorrect, off_topic]
- feedback: 1-3 sentences of constructive feedback
- missing_points: list of rubric items the student missed
- misconception_detected: null or a string describing the misconception
- follow_up_question: a follow-up question to deepen understanding (or null)
- mastery_updates: list of {concept, delta} where delta is -0.1 to +0.1
- next_action: {type, reason} where type is one of [continue, review_question, remedial, retry]

Be generous with spoken-style answers. Accept informal language if the core idea is correct.

Respond ONLY with JSON:
{schema}
```

### 2. Answer grader service — `app/services/grading/answer_grader.py`

```python
class AnswerGrader:
    def __init__(self, llm: BaseLLMClient):
        ...

    async def grade_answer(
        self,
        db: Session,
        tidbit_id: UUID,
        question_id: str,
        transcript_final: str,
        user_id: UUID | None = None,
    ) -> AnswerAttempt:
        """
        1. Load tidbit quiz.
        2. Find the question by question_id.
        3. Load tidbit concept for context.
        4. Build grading prompt.
        5. Call LLM.
        6. Validate grading output.
        7. Create AnswerAttempt row.
        8. Return attempt with grading.
        """
```

### 3. API endpoint — `app/api/routes/grading.py`

```python
@router.post("/tidbits/{tidbit_id}/quiz/grade")
async def grade_transcript(
    tidbit_id: UUID,
    data: GradeRequest,  # { question_id, transcript_final }
    db = Depends(get_db),
):
    ...
```

Response:

```json
{
  "attempt_id": "uuid",
  "grading": {
    "score": 0.75,
    "correctness": "mostly_correct",
    "feedback": "...",
    "missing_points": ["..."],
    "misconception_detected": null,
    "follow_up_question": "...",
    "mastery_updates": [{"concept": "Span", "delta": 0.07}],
    "next_action": {"type": "continue", "reason": "..."}
  }
}
```

### 4. CLI script — `scripts/grade_answer.py`

```bash
python scripts/grade_answer.py \
  --tidbit-id TIDBIT_ID \
  --question-id q1 \
  --answer "span is all combinations of given vectors"
```

---

## Grading Output Schema

```json
{
  "score": 0.0,
  "correctness": "correct | mostly_correct | partially_correct | incorrect | off_topic",
  "feedback": "string",
  "missing_points": ["string"],
  "misconception_detected": "string | null",
  "follow_up_question": "string | null",
  "mastery_updates": [
    {"concept": "string", "delta": 0.0}
  ],
  "next_action": {
    "type": "continue | review_question | remedial | retry",
    "reason": "string"
  }
}
```

---

## Files to Create

```text
app/services/grading/__init__.py
app/services/grading/answer_grader.py
app/llm/prompts/answer_grading.md
app/api/routes/grading.py
scripts/grade_answer.py
```

---

## Acceptance Criteria

- [ ] "Span is all combinations of given vectors" → `mostly_correct` or `correct` for span definition question.
- [ ] Missing "scalar multiplication" is flagged in `missing_points`.
- [ ] Score is between 0.0 and 1.0.
- [ ] `next_action.type` is reasonable for the score.
- [ ] `AnswerAttempt` is saved with score, feedback_json, transcript_final.
- [ ] API returns grading JSON matching the schema.

---

## Agent Prompt

```text
Create answer grading for MathPath:

1. app/llm/prompts/answer_grading.md — prompt that takes question, expected answer, rubric, and student transcript; returns score, correctness, feedback, missing_points, misconception, follow_up_question, mastery_updates, next_action. Be generous with spoken-style answers.

2. app/services/grading/answer_grader.py — loads quiz question, builds prompt, calls LLM, validates, creates AnswerAttempt row.

3. app/api/routes/grading.py — POST /tidbits/{tidbit_id}/quiz/grade accepting {question_id, transcript_final}.

4. scripts/grade_answer.py — CLI.
```
