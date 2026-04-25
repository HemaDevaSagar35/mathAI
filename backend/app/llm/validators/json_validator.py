import json
import re


def extract_json(text: str) -> dict:
    """Extract JSON from an LLM response, handling common formatting issues."""
    text = text.strip()

    # 1. Raw parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. Fenced code block: ```json ... ``` or ``` ... ```
    fenced = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 3. Brace extraction: first { to last }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

        # 4. Fix trailing commas
        cleaned = re.sub(r",\s*([}\]])", r"\1", candidate)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not extract valid JSON from LLM response ({len(text)} chars)")
