# B13 — Progression & Mastery Engine

> **Objective:** Track user progress per tidbit, update concept mastery scores, determine next actions (continue, review, remedial), and log learning memory events.

**Depends on:** B12 (grading produces scores), B08 (tidbits), B02 (progress/mastery/memory models)

---

## Tasks

### 1. Mastery engine — `app/services/progression/mastery_engine.py`

```python
class MasteryEngine:
    def update_after_grading(
        self,
        db: Session,
        user_id: UUID,
        tidbit_id: UUID,
        grading_result: dict,
    ) -> dict:
        """
        1. Update UserTidbitProgress:
           - status → 'started' or 'completed' based on quiz completion.
           - quiz_score = average of all question scores for this tidbit.
        2. Update ConceptMastery for each concept in mastery_updates:
           - mastery_score += delta (clamped 0.0–1.0).
           - confidence adjusted by attempt count.
           - last_seen_at = now.
        3. Log LearningMemoryEvent (event_type = 'quiz_answered').
        4. Return summary: { tidbit_status, mastery_updates, next_action }.
        """

    def complete_tidbit(self, db: Session, user_id: UUID, tidbit_id: UUID) -> dict:
        """
        Triggered when ALL quiz questions for the tidbit have been answered.
        (The quiz screen submits a "complete" call after the final question.)

        1. Mark tidbit as completed.
        2. Compute quiz_score = average score across all answer_attempts for this tidbit.
        3. Determine next action based on quiz_score:
           - quiz_score >= 0.7 → continue to next tidbit.
           - quiz_score 0.4–0.7 → insert review tidbit, then continue.
           - quiz_score < 0.4 → insert remedial tidbit, then continue.
        4. Unlock next tidbit (review/remedial or next original).
        5. Log lesson_completed memory event.
        6. Return { next_tidbit_id, action, quiz_score }.
        """
```

### 2. Next item selector — `app/services/progression/next_item_selector.py`

```python
class NextItemSelector:
    def get_next_tidbit(self, db: Session, user_id: UUID, study_plan_id: UUID) -> Tidbit | None:
        """
        1. Find current position in plan.
        2. Check for pending review/remedial tidbits.
        3. If review/remedial exists → return that.
        4. Otherwise → return next original tidbit.
        5. If all done → return None.
        """

    def insert_review_tidbit(self, db: Session, after_tidbit_id: UUID, concept_id: UUID) -> Tidbit:
        """
        Create a review tidbit inserted after the specified tidbit.
        tidbit_type='review', is_original_plan=False.
        """

    def insert_remedial_tidbit(self, db: Session, after_tidbit_id: UUID, concept_id: UUID) -> Tidbit:
        """
        Create a remedial tidbit with simpler learning_goal.
        tidbit_type='remedial', is_original_plan=False.
        """
```

### 3. Memory event writer — `app/services/memory/memory_event_writer.py`

```python
class MemoryEventWriter:
    def log_event(
        self,
        db: Session,
        user_id: UUID,
        event_type: str,
        book_id: UUID | None = None,
        tidbit_id: UUID | None = None,
        concept_id: UUID | None = None,
        payload: dict = {},
    ) -> LearningMemoryEvent:
        """Create a memory event row. Optionally compute embedding later."""
```

### 4. API endpoint — `app/api/routes/progress.py`

```python
@router.get("/progress")
async def get_progress(user_id: UUID = None, db = Depends(get_db)):
    """
    Return:
    - active_book
    - current_tidbit
    - streak (consecutive days with completed tidbit)
    - overall_progress (completed / total tidbits)
    - weak_concepts (mastery_score < 0.5)
    - recent_activity (last 10 memory events)
    """

@router.get("/progress/concepts")
async def get_concept_mastery(user_id: UUID = None, db = Depends(get_db)):
    """Return all concept mastery scores."""
```

### 5. Progress calculation logic

```python
def calculate_streak(events: list[LearningMemoryEvent]) -> int:
    """Count consecutive days with lesson_completed events."""

def calculate_overall_progress(plan: StudyPlan) -> float:
    """completed_tidbits / total_tidbits"""

def get_weak_concepts(mastery: list[ConceptMastery], threshold=0.5) -> list:
    """Return concepts with mastery_score below threshold."""
```

---

## Thresholds

| Score Range | Action |
|-------------|--------|
| >= 0.7 | Continue to next tidbit |
| 0.4 – 0.7 | Insert review tidbit |
| < 0.4 | Insert remedial tidbit |

These thresholds should be configurable in settings.

---

## Important: Review/Remedial Content Generation

When a review or remedial tidbit is **inserted**, it needs lesson and quiz content too. This creates a dependency on B09 (lesson generation) and B11 (quiz generation).

Strategy for MVP:
- When `insert_review_tidbit()` or `insert_remedial_tidbit()` creates the tidbit row, mark it as needing content.
- Content (lesson + quiz) is generated **lazily** — when the user opens the tidbit for the first time, the frontend calls `POST /tidbits/{id}/lesson/generate` and `POST /tidbits/{id}/quiz/generate`.
- This avoids blocking the progression flow on LLM calls.

The inserted tidbit should have:
- A modified `learning_goal` (e.g., "Review: revisit span..." or "Remedial: simplified intro to span...").
- The same `source_chunk_ids` as the original tidbit's concept.
- `tidbit_type` set to `review` or `remedial`.

---

## Files to Create

```text
app/services/progression/__init__.py
app/services/progression/mastery_engine.py
app/services/progression/next_item_selector.py
app/services/memory/__init__.py
app/services/memory/memory_event_writer.py
app/api/routes/progress.py
```

---

## Acceptance Criteria

- [ ] After grading with score >= 0.7, tidbit is marked completed and next tidbit unlocked.
- [ ] After grading with score 0.4–0.7, a review tidbit is inserted.
- [ ] After grading with score < 0.4, a remedial tidbit is inserted.
- [ ] `ConceptMastery.mastery_score` updates correctly (clamped 0–1).
- [ ] `LearningMemoryEvent` rows are created for quiz answers and lesson completions.
- [ ] `GET /progress` returns streak, overall_progress, weak_concepts, recent_activity.
- [ ] Inserted review/remedial tidbits have `is_original_plan=False` and correct `tidbit_type`.

---

## Agent Prompt

```text
Create progression and mastery engine for MathPath:

1. app/services/progression/mastery_engine.py — update_after_grading() updates UserTidbitProgress and ConceptMastery from grading result. complete_tidbit() determines next action based on quiz score thresholds (>=0.7 continue, 0.4-0.7 review, <0.4 remedial).

2. app/services/progression/next_item_selector.py — get_next_tidbit() finds next tidbit (prioritizing pending review/remedial). insert_review_tidbit() and insert_remedial_tidbit() create non-original tidbits.

3. app/services/memory/memory_event_writer.py — log_event() creates LearningMemoryEvent rows.

4. app/api/routes/progress.py — GET /progress returns dashboard with streak, progress, weak concepts, activity.
```
