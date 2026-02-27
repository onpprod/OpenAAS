"""AAS JSON loading and schema validation helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft201909Validator

from .errors import OPCUASchemaValidationError, OPCUASpecError

DEFAULT_SCHEMA_RELATIVE_PATH = Path("schemas") / "aas.json"


def resolve_schema_path(schema_path: str | Path | None = None) -> Path:
    """Resolve the schema path used to validate an AAS environment JSON."""
    if schema_path is not None:
        path = Path(schema_path)
        if not path.is_absolute():
            path = Path.cwd() / path
        path = path.resolve()
        if not path.exists():
            raise FileNotFoundError(f"Schema file not found: {path}")
        return path

    candidates = [
        Path.cwd() / DEFAULT_SCHEMA_RELATIVE_PATH,
        Path(__file__).resolve().parents[1] / DEFAULT_SCHEMA_RELATIVE_PATH,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    checked_paths = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError(
        "Could not locate aas schema file. Checked paths: "
        f"{checked_paths}. Use --schema to provide an explicit path."
    )


def load_json_document(json_path: str | Path) -> dict[str, Any]:
    """Load a JSON file and return a dictionary root object."""
    path = Path(json_path)
    if not path.is_absolute():
        path = Path.cwd() / path
    path = path.resolve()

    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")

    with path.open("r", encoding="utf-8") as fp:
        document = json.load(fp)

    if not isinstance(document, dict):
        raise OPCUASpecError("AAS JSON must contain an object at the root level.")

    return document


def load_schema(schema_path: str | Path | None = None) -> dict[str, Any]:
    """Load the JSON schema document."""
    path = resolve_schema_path(schema_path)
    with path.open("r", encoding="utf-8") as fp:
        schema = json.load(fp)

    if not isinstance(schema, dict):
        raise OPCUASpecError(f"Schema must be a JSON object: {path}")

    return schema


def validate_aas_environment(
    aas_environment: dict[str, Any],
    *,
    schema_path: str | Path | None = None,
) -> None:
    """Validate the AAS environment dictionary using the configured schema."""
    if not isinstance(aas_environment, dict):
        raise OPCUASpecError("AAS environment must be a dictionary.")

    schema = load_schema(schema_path)
    validator = Draft201909Validator(schema)
    errors = sorted(
        validator.iter_errors(aas_environment),
        key=lambda err: tuple(err.absolute_path),
    )

    if not errors:
        return

    formatted_errors = []
    max_errors = 20
    for index, error in enumerate(errors[:max_errors], start=1):
        location = _format_json_path(error.absolute_path)
        formatted_errors.append(f"{index}. {location}: {error.message}")

    if len(errors) > max_errors:
        formatted_errors.append(
            f"... and {len(errors) - max_errors} additional schema validation errors."
        )

    raise OPCUASchemaValidationError(
        "AAS JSON is not valid according to the configured schema.",
        errors=formatted_errors,
    )


def load_aas_environment(
    json_path: str | Path,
    *,
    schema_path: str | Path | None = None,
) -> dict[str, Any]:
    """Load and validate an AAS environment JSON file."""
    environment = load_json_document(json_path)
    validate_aas_environment(environment, schema_path=schema_path)
    return environment


def _format_json_path(path_tokens: Iterable[Any]) -> str:
    parts = ["$"]
    for token in path_tokens:
        if isinstance(token, int):
            parts.append(f"[{token}]")
        else:
            parts.append(f".{token}")
    return "".join(parts)
