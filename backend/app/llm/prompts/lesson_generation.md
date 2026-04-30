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
Create a lesson with ALL of the following sections. Every section is required.

Respond ONLY with valid JSON:

```json
{{
  "title": "string",
  "concept": "string",
  "learning_goal": "string",
  "grounding": {{
    "primary_source_chunk_ids": ["uuid strings from source material above"],
    "page_refs": [],
    "used_definitions": ["definition names referenced"],
    "used_examples": ["example names or descriptions referenced"]
  }},
  "core_idea": "One sentence capturing the essence of this concept",
  "why_it_matters": "One sentence on why a student should care",
  "explain_like_10th_grader": "Simple explanation using everyday language, 2-4 sentences",
  "explain_like_engineer": "Practical explanation with applications focus, 2-4 sentences",
  "explain_like_math_mature": "Rigorous explanation assuming math maturity, 2-4 sentences",
  "intuition_bridge": {{
    "simple_phrase": "A one-line analogy or intuitive description",
    "mathematical_translation": "How the intuition maps to math notation",
    "formal_bridge": "How to go from intuition to the formal definition"
  }},
  "formal_definition_or_statement": "The precise mathematical definition or theorem statement",
  "worked_examples": [
    {{
      "title": "Example title",
      "problem": "Problem statement",
      "solution": "Step-by-step solution",
      "teaching_note": "What this example teaches"
    }}
  ],
  "common_mistakes": [
    {{"mistake": "What students often get wrong", "correction": "The correct understanding"}}
  ],
  "care_notes": [
    {{"type": "misconception | bridge | memory_hook | warning | application | future_use | proof_thinking | exam_trap", "note": "The note content"}}
  ],
  "real_world_connections": [
    {{"domain": "e.g. physics, economics, engineering", "connection": "How this concept appears in that domain"}}
  ],
  "memory_hooks": ["Short memorable phrases to help retention"],
  "quick_summary": "One concise sentence summarizing the entire lesson"
}}
```