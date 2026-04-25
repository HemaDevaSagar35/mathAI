You are a math education expert. Analyze the following text excerpts from a math textbook and produce a structured profile.

## Text Excerpts
{chunks_text}

## Instructions
Identify the subject, topics, level, style, proof density, computation density, and diagram dependency. Recommend a learning strategy based on the content.

## Output Format
Respond ONLY with valid JSON matching this schema:

```json
{{
  "title_guess": "string — your best guess at the book/chapter title",
  "detected_subjects": [
    {{"subject": "string (e.g. linear_algebra, calculus, probability)", "confidence": 0.9}}
  ],
  "topics": ["string — specific topic names found"],
  "level": "high_school | undergraduate | graduate",
  "style": "definition_theorem_proof | intuition_examples | computation_drill | mixed",
  "proof_density": "none | low | medium | high",
  "computation_density": "none | low | medium | high",
  "diagram_dependency": "none | low | medium | high",
  "content_structure": {{
    "has_definitions": true,
    "has_theorems": true,
    "has_proofs": true,
    "has_worked_examples": true,
    "has_exercises": false
  }},
  "learning_strategy": {{
    "proof_ladder_weight": "none | low | medium | high",
    "drill_practice_weight": "none | low | medium | high",
    "visual_intuition_weight": "none | low | medium | high",
    "application_weight": "none | low | medium | high"
  }}
}}
```