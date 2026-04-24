# B07 — Concept Graph

> **Objective:** Build a prerequisite/relationship graph between extracted concepts. Store as `concept_edges`.

**Depends on:** B06 (concepts exist)

---

## Tasks

### 1. Graph generation prompt — `app/llm/prompts/concept_graph.md`

```markdown
You are a math curriculum designer. Given the following concepts from a {subject} textbook, create a prerequisite and relationship graph.

## Concepts
{concepts_json}

## Instructions
For each pair of related concepts, create an edge with:
- source: the prerequisite or related concept name
- target: the dependent or related concept name
- edge_type: one of [prerequisite, related, contrasts_with, application_of]
- confidence: 0.0-1.0

Rules:
- "prerequisite" means source MUST be understood before target.
- "related" means they are connected but neither depends on the other.
- "contrasts_with" means they are often confused.
- "application_of" means target is a practical use of source.

Respond ONLY with JSON:
{schema}
```

### 2. Concept graph builder — `app/services/graph/concept_graph_builder.py`

```python
class ConceptGraphBuilder:
    def __init__(self, llm: BaseLLMClient):
        ...

    async def build_graph(self, db: Session, book_id: UUID) -> list[ConceptEdge]:
        """
        1. Load all concepts for the book.
        2. If few concepts (≤20), send all at once.
        3. If many, batch into groups and merge edges.
        4. Also use prerequisite_names from concepts as seed edges.
        5. Validate: no self-loops, no duplicate edges.
        6. Save ConceptEdge rows.
        7. Return edges.
        """
```

### 3. Graph validation

```python
def validate_graph(concepts: list[Concept], edges: list[dict]) -> list[dict]:
    """
    - Remove edges referencing unknown concept names.
    - Remove self-loops.
    - Deduplicate (same source+target+type).
    - Warn on cycles in prerequisite edges (optional for MVP).
    """
```

### 4. API endpoint — `app/api/routes/concepts.py` (extend)

```python
@router.post("/books/{book_id}/graph/build")
async def build_graph(book_id: UUID, db = Depends(get_db)):
    ...

@router.get("/books/{book_id}/graph")
async def get_graph(book_id: UUID, db = Depends(get_db)):
    """Return concepts + edges as a graph structure."""
```

### 5. CLI script — `scripts/build_graph.py`

```bash
python scripts/build_graph.py --book-id BOOK_ID
```

Prints edge count and sample edges.

---

## Files to Create

```text
app/services/graph/__init__.py
app/services/graph/concept_graph_builder.py
app/llm/prompts/concept_graph.md
scripts/build_graph.py
```

---

## Acceptance Criteria

- [ ] `Span` depends on `Linear combination` (prerequisite edge exists).
- [ ] `Basis` relates to both `Span` and `Linear independence`.
- [ ] No self-loop edges.
- [ ] No edges referencing concepts not in the book.
- [ ] `GET /books/{book_id}/graph` returns `{"concepts": [...], "edges": [...]}`.

---

## Agent Prompt

```text
Create concept graph builder for MathPath:

1. app/llm/prompts/concept_graph.md — prompt that takes a list of concepts and returns edges with source, target, edge_type, confidence.

2. app/services/graph/concept_graph_builder.py — loads concepts, calls LLM, also seeds edges from concepts' prerequisite_names field, validates (no self-loops, no unknown refs, no duplicates), saves ConceptEdge rows.

3. Extend app/api/routes/concepts.py with POST /books/{book_id}/graph/build and GET /books/{book_id}/graph.

4. scripts/build_graph.py — CLI script.
```
