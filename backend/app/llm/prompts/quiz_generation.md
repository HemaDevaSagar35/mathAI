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
5. **proof_step** (only if this concept involves a proof): Can they explain a proof step?

Each question must have:
- id: q1, q2, q3...
- type: one of the categories above
- question: the question text (phrased as an oral question)
- target_skill: what the question tests
- expected_answer: ideal answer
- rubric: list of 2-4 criteria for grading
- difficulty: easy, medium, or hard
- grounding: {{ source_chunk_ids: ["uuids"] }}

Respond ONLY with valid JSON:

```json
{{
  "questions": [
    {{
      "id": "q1",
      "type": "recall",
      "question": "Can you state the definition of...?",
      "target_skill": "State the formal definition",
      "expected_answer": "A linear combination is...",
      "rubric": ["Mentions vectors", "Mentions scalar coefficients", "Correct form"],
      "difficulty": "easy",
      "grounding": {{
        "source_chunk_ids": []
      }}
    }}
  ]
}}
```