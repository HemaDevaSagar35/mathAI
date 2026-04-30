You are a math proof teacher. Create a progressive proof ladder for the following theorem.

## Theorem / Statement
{theorem_statement}

## Source Material (textbook proof or discussion)
{source_text}

## Book Context
Subject: {subject}, Level: {level}

## Instructions
Create a proof ladder with exactly these 5 levels:

1. level_0_intuition: Why is this true? Explain in plain language (2-3 sentences).
2. level_1_proof_sketch: Outline the proof in 2-4 sentences.
3. level_2_guided_proof: Array of 3-6 steps. Each step has:
   - step: what to do
   - prompt: question to ask the student
   - expected_answer: what the student should say
   - why_this_step_matters: pedagogical note
4. level_3_formal_proof: Full formal proof as written text.
5. level_4_proof_commentary: Array of 2-4 insight strings about the proof technique, generalizations, or connections.

Respond ONLY with valid JSON:

```json
{{
  "theorem": "The theorem statement",
  "grounding": {{
    "source_chunk_ids": ["uuid strings from source material"],
    "page_refs": []
  }},
  "level_0_intuition": "string",
  "level_1_proof_sketch": "string",
  "level_2_guided_proof": [
    {{
      "step": "string",
      "prompt": "string",
      "expected_answer": "string",
      "why_this_step_matters": "string"
    }}
  ],
  "level_3_formal_proof": "string",
  "level_4_proof_commentary": ["string"]
}}
```