You are a math curriculum designer. Given the following concepts from a {subject} textbook, create a prerequisite and relationship graph.

## Concepts
{concepts_json}

## Instructions
For each pair of related concepts, create an edge with:
- source: the prerequisite or related concept name (must match a name from the list above)
- target: the dependent or related concept name (must match a name from the list above)
- edge_type: one of [prerequisite, related, contrasts_with, application_of]
- confidence: 0.0-1.0

Rules:
- "prerequisite" means source MUST be understood before target
- "related" means they are connected but neither strictly depends on the other
- "contrasts_with" means they are often confused or compared
- "application_of" means target is a practical application of source
- Do NOT create self-loops (source == target)
- Only reference concept names from the list above

Respond ONLY with valid JSON:

```json
{{
  "edges": [
    {{
      "source": "Linear Combination",
      "target": "Span",
      "edge_type": "prerequisite",
      "confidence": 0.95
    }}
  ]
}}
```