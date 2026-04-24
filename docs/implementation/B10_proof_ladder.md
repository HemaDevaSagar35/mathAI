# B10 — Proof Ladder Generation

> **Objective:** For tidbits containing theorems or proof-heavy concepts, generate a progressive proof ladder with 5 levels: intuition → sketch → guided → formal → commentary.

**Depends on:** B04 (LLM), B08 (tidbits), B03 (source chunks)

---

## Tasks

### 1. Proof detection logic

Not every tidbit needs a proof ladder. Generate one when:

```python
def needs_proof_ladder(tidbit: Tidbit, concept: Concept, profile: BookProfile) -> bool:
    # Primary: theorems and proofs always get a ladder
    if concept.concept_type in ("theorem", "proof"):
        return True
    # Secondary: definitions in proof-heavy books that mention "proof" in context
    if (
        profile.proof_density in ("medium", "high")
        and concept.concept_type == "definition"
        and "proof" in (tidbit.learning_goal or "").lower()
    ):
        return True
    return False
```

### 2. Proof ladder prompt — `app/llm/prompts/proof_ladder.md`

```markdown
You are a math proof teacher. Create a progressive proof ladder for the following theorem.

## Theorem / Statement
{theorem_statement}

## Source Material (textbook proof or discussion)
{source_text}

## Book Context
Subject: {subject}, Level: {level}

## Instructions
Create a proof ladder with exactly these 5 levels:

1. level_0_intuition: Why is this true? Explain in plain language.
2. level_1_proof_sketch: Outline the proof in 2-4 sentences.
3. level_2_guided_proof: Array of steps. Each step has:
   - step: what to do
   - prompt: question to ask the student
   - expected_answer: what the student should say
   - why_this_step_matters: pedagogical note
4. level_3_formal_proof: Full formal proof as written text.
5. level_4_proof_commentary: Array of insight strings about the proof technique.

Include grounding (source_chunk_ids, page_refs).

Respond ONLY with JSON:
{schema}
```

### 3. Proof ladder generator — `app/services/proof_generation/proof_ladder_generator.py`

```python
class ProofLadderGenerator:
    def __init__(self, llm: BaseLLMClient):
        ...

    async def generate(self, db: Session, tidbit_id: UUID) -> ProofLadder | None:
        """
        1. Load tidbit, concept, profile.
        2. Check needs_proof_ladder().
        3. If no, return None.
        4. Load source chunks.
        5. Extract theorem statement from concept or chunks.
        6. Call LLM with proof ladder prompt.
        7. Save ProofLadder row.
        8. Return ladder.
        """
```

### 4. API endpoint (extend lessons route or add to tidbits)

```python
@router.post("/tidbits/{tidbit_id}/proof-ladder/generate")
async def generate_proof_ladder(tidbit_id: UUID, db = Depends(get_db)):
    ...

@router.get("/tidbits/{tidbit_id}/proof-ladder")
async def get_proof_ladder(tidbit_id: UUID, db = Depends(get_db)):
    ...
```

### 5. CLI script — `scripts/generate_proof_ladder.py`

```bash
python scripts/generate_proof_ladder.py --tidbit-id TIDBIT_ID
```

---

## Proof Ladder JSON Schema

```json
{
  "theorem": "string",
  "grounding": {
    "source_chunk_ids": ["uuid"],
    "page_refs": [0]
  },
  "level_0_intuition": "string",
  "level_1_proof_sketch": "string",
  "level_2_guided_proof": [
    {
      "step": "string",
      "prompt": "string",
      "expected_answer": "string",
      "why_this_step_matters": "string"
    }
  ],
  "level_3_formal_proof": "string",
  "level_4_proof_commentary": ["string"]
}
```

---

## Files to Create

```text
app/services/proof_generation/__init__.py
app/services/proof_generation/proof_ladder_generator.py
app/llm/prompts/proof_ladder.md
scripts/generate_proof_ladder.py
```

---

## Acceptance Criteria

- [ ] Theorem/proof concept → proof ladder with all 5 levels.
- [ ] Non-proof concept (e.g., a computation technique) → returns None, no ProofLadder row.
- [ ] `level_2_guided_proof` has 3+ steps with prompts and expected answers.
- [ ] `level_4_proof_commentary` has 2+ insight strings.
- [ ] Proof ladder is stored in `proof_ladders` table.
- [ ] API returns proof ladder nested under tidbit detail.

---

## Agent Prompt

```text
Create proof ladder generation for MathPath:

1. app/services/proof_generation/proof_ladder_generator.py — checks if tidbit needs a proof ladder (theorem/proof type or medium/high proof density). If yes, loads source chunks, calls LLM, saves ProofLadder. If no, returns None.

2. app/llm/prompts/proof_ladder.md — prompt template for 5-level proof ladder (intuition, sketch, guided steps, formal proof, commentary).

3. API endpoints for generating and retrieving proof ladders.

4. scripts/generate_proof_ladder.py — CLI.
```
