You are a math terminology expert. Given the following list of concept names extracted from a textbook, identify groups of duplicates or near-duplicates that refer to the same underlying concept.

## Concept Names
{concept_names}

## Instructions
Group names that refer to the same concept. For each group, pick the best canonical name.

Only group names that truly refer to the same mathematical concept. Do NOT group related but distinct concepts (e.g. "span" and "basis" are different concepts).

Respond ONLY with valid JSON:

```json
{{
  "groups": [
    {{
      "canonical": "Span",
      "duplicates": ["Vector span", "Span of a set", "Linear span"]
    }}
  ]
}}
```

If there are no duplicates, return: {{"groups": []}}