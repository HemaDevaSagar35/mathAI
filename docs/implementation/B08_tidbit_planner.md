# B08 — Stable Tidbit Planner

> **Objective:** Generate an ordered study plan of tidbits from concepts, the prerequisite graph, and book profile. The plan is stable and never rewritten once generated.

**Depends on:** B05 (profile), B06 (concepts), B07 (graph)

---

## Tasks

### 1. Planning prompt — `app/llm/prompts/tidbit_planning.md`

```markdown
You are a math curriculum planner. Given the concept graph and book profile below, create an ordered list of learning tidbits.

## Book Profile
{profile_json}

## Concepts
{concepts_json}

## Concept Graph Edges
{edges_json}

## Rules
- Respect prerequisite order: a concept's prerequisites must appear before it.
- Each tidbit teaches ONE concept (or a small related cluster).
- Estimate minutes (5-20) and difficulty (1-5) per tidbit.
- Include source_chunk_ids from the concept.
- Write a clear learning_goal for each tidbit.

## Output Format
Respond ONLY with JSON:
{schema}
```

### 2. Tidbit planner service — `app/services/planning/tidbit_planner.py`

```python
class TidbitPlanner:
    def __init__(self, llm: BaseLLMClient):
        ...

    async def generate_plan(self, db: Session, book_id: UUID, user_id: UUID | None = None) -> StudyPlan:
        """
        1. Load profile, concepts, edges.
        2. Topologically sort concepts using prerequisite edges.
        3. Call LLM with sorted concepts + profile for tidbit generation.
        4. Create StudyPlan row.
        5. Create Tidbit rows with order_index, is_original_plan=True.
        6. Return plan with tidbits.
        """
```

### 3. Topological sort utility

```python
def topological_sort_concepts(
    concepts: list[Concept],
    edges: list[ConceptEdge],
) -> list[Concept]:
    """
    Sort concepts respecting prerequisite edges.
    If cycles exist, break them and warn.
    """
```

### 4. API endpoints — `app/api/routes/plans.py`

```python
@router.post("/books/{book_id}/plan/generate")
async def generate_plan(book_id: UUID, db = Depends(get_db)):
    ...

@router.get("/books/{book_id}/plan")
async def get_plan(book_id: UUID, db = Depends(get_db)):
    """Return study plan with ordered tidbits."""
```

### 5. CLI script — `scripts/generate_plan.py`

```bash
python scripts/generate_plan.py --book-id BOOK_ID
```

Prints plan with tidbit titles and order.

---

## Key Design Rule

The original plan is **immutable**. All tidbits created here have `is_original_plan=True`. Later adaptations (review, remedial) are inserted *alongside* the plan, never replacing existing tidbits.

```text
Original: T1 → T2 → T3 → T4 → T5
Adapted:  T1 → T2 → [Review1] → T3 → [Remedial1] → T4 → T5
```

Inserted tidbits use `inserted_after_tidbit_id` and `is_original_plan=False`.

---

## Files to Create

```text
app/services/planning/__init__.py
app/services/planning/tidbit_planner.py
app/llm/prompts/tidbit_planning.md
app/api/routes/plans.py
scripts/generate_plan.py
```

---

## Acceptance Criteria

- [ ] A book with concepts gets a `StudyPlan` with ordered `Tidbit` rows.
- [ ] Prerequisite concepts appear before dependent concepts.
- [ ] Each tidbit has `title`, `learning_goal`, `source_chunk_ids`, `estimated_minutes`, `difficulty`.
- [ ] All tidbits have `is_original_plan=True` and `tidbit_type='original'`.
- [ ] `GET /books/{book_id}/plan` returns the ordered tidbit list.
- [ ] Re-running plan generation for the same book does not mutate the existing plan.

---

## Agent Prompt

```text
Create tidbit planner for MathPath:

1. app/services/planning/tidbit_planner.py — loads profile + concepts + edges, topologically sorts concepts, calls LLM to generate ordered tidbits, creates StudyPlan and Tidbit rows with is_original_plan=True.

2. app/llm/prompts/tidbit_planning.md — prompt template.

3. app/api/routes/plans.py — POST /books/{book_id}/plan/generate and GET /books/{book_id}/plan.

4. scripts/generate_plan.py — CLI.

Include a topological_sort_concepts utility that handles cycles gracefully.
```
