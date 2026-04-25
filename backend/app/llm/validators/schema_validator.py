import jsonschema
from pydantic import BaseModel, ValidationError


def validate_against_schema(data: dict, schema: dict | type[BaseModel]) -> dict:
    """Validate parsed JSON against a Pydantic model or JSON Schema dict."""
    if isinstance(schema, type) and issubclass(schema, BaseModel):
        validated = schema.model_validate(data)
        return validated.model_dump()
    elif isinstance(schema, dict):
        jsonschema.validate(data, schema)
        return data
    return data


def format_validation_error(error: ValidationError | Exception) -> str:
    """Format a validation error into a string for retry prompts."""
    if isinstance(error, ValidationError):
        issues = []
        for e in error.errors():
            loc = " → ".join(str(part) for part in e["loc"])
            issues.append(f"  - {loc}: {e['msg']}")
        return "Validation errors:\n" + "\n".join(issues)
    return str(error)
