You are a math concept extraction expert. Given the following text from a {level} {subject} textbook, extract all mathematical concepts.

## Text
{chunk_text}

## Book Context
Subject: {subject}
Level: {level}
Style: {style}

## Instructions
For each concept found in the text, provide:
- name: canonical mathematical name
- concept_type: one of [definition, theorem, technique, example, proof, application]
- difficulty: 1-5 (1=introductory, 5=advanced)
- importance: one of [core, supporting, optional]
- prerequisite_names: list of concept names this depends on (use canonical names)
- common_confusions: list of common mistakes or misconceptions students have

Only include concepts that are explicitly discussed or defined in the text. Do not infer concepts that are merely mentioned in passing.

Respond ONLY with valid JSON:

```json
{{
  "concepts": [
    {{
      "name": "Linear Combination",
      "concept_type": "definition",
      "difficulty": 2,
      "importance": "core",
      "prerequisite_names": ["Vector", "Scalar"],
      "common_confusions": ["Confusing with linear transformation"]
    }}
  ]
}}
```