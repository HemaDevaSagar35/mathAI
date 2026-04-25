from pathlib import Path

PROMPTS_DIR = Path(__file__).parent


def load_prompt(name: str, **variables: str) -> str:
    """Load a .md prompt template and substitute {variables} using format_map."""
    path = PROMPTS_DIR / f"{name}.md"
    template = path.read_text(encoding="utf-8")
    if variables:
        template = template.format_map(variables)
    return template
