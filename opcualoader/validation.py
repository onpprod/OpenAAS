"""Schema validation helpers for opcualoader."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft201909Validator

from .errors import OPCUALoaderSchemaError, OPCUALoaderSpecError

DEFAULT_SCHEMA_RELATIVE_PATH = Path("schemas") / "aas.json"


def resolve_schema_path(schema_path: str | Path | None = None) -> Path:
    """Resolve a schema path, defaulting to schemas/aas.json."""
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

    checked = ", ".join(str(candidate) for candidate in candidates)
    raise FileNotFoundError(
        "Could not locate aas schema file. Checked paths: "
        f"{checked}. Use --schema to provide an explicit path."
    )


def load_schema(schema_path: str | Path | None = None) -> dict[str, Any]:
    """Load the AAS schema document."""
    path = resolve_schema_path(schema_path)
    with path.open("r", encoding="utf-8") as fp:
        schema = json.load(fp)

    if not isinstance(schema, dict):
        raise OPCUALoaderSpecError(f"Schema root must be a JSON object: {path}")
    return schema


def validate_aas_environment(
    environment: dict[str, Any],
    *,
    schema_path: str | Path | None = None,
) -> None:
    """Validate an AAS environment dictionary against schema."""
    if not isinstance(environment, dict):
        raise OPCUALoaderSpecError("AAS environment must be a dictionary.")

    schema = load_schema(schema_path)
    validator = Draft201909Validator(schema)
    errors = sorted(
        validator.iter_errors(environment),
        key=lambda err: tuple(err.absolute_path),
    )

    if not errors:
        return

    formatted: list[str] = []
    max_errors = 20
    for index, error in enumerate(errors[:max_errors], start=1):
        location = _format_path(error.absolute_path)
        formatted.append(f"{index}. {location}: {error.message}")

    if len(errors) > max_errors:
        formatted.append(
            f"... and {len(errors) - max_errors} additional schema validation errors."
        )

    raise OPCUALoaderSchemaError(
        "Generated JSON is not valid according to AAS schema.",
        errors=formatted,
    )


def _format_path(path_tokens: Iterable[Any]) -> str:
    parts = ["$"]
    for token in path_tokens:
        if isinstance(token, int):
            parts.append(f"[{token}]")
        else:
            parts.append(f".{token}")
    return "".join(parts)
