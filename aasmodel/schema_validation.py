"""JSON schema validation helpers for AAS metamodel payloads."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft201909Validator


DEFAULT_SCHEMA_PATH = Path("schemas") / "aas.json"


class AASSchemaValidationError(ValueError):
    """Raised when a payload does not comply with aas.json schema."""

    def __init__(self, message: str, *, errors: list[str] | None = None) -> None:
        super().__init__(message)
        self.errors = errors or []


def resolve_schema_path(schema_path: str | Path | None = None) -> Path:
    """Resolve the schema file path used for compatibility validation."""
    if schema_path is not None:
        path = Path(schema_path)
        if not path.is_absolute():
            path = Path.cwd() / path
        path = path.resolve()
        if not path.exists():
            raise FileNotFoundError(f"Schema file not found: {path}")
        return path

    candidates = [
        Path.cwd() / DEFAULT_SCHEMA_PATH,
        Path(__file__).resolve().parents[1] / DEFAULT_SCHEMA_PATH,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    checked = ", ".join(str(candidate) for candidate in candidates)
    raise FileNotFoundError(
        "Could not locate aas schema file. Checked paths: "
        f"{checked}."
    )


def validate_against_aas_schema(
    payload: dict[str, Any],
    *,
    schema_path: str | Path | None = None,
) -> None:
    """Validate a dictionary payload against aas.json schema."""
    path = resolve_schema_path(schema_path)
    schema = json.loads(path.read_text(encoding="utf-8"))

    validator = Draft201909Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda err: tuple(err.absolute_path))

    if not errors:
        return

    lines: list[str] = []
    for index, error in enumerate(errors[:20], start=1):
        location = "$" + "".join(
            f"[{token}]" if isinstance(token, int) else f".{token}"
            for token in error.absolute_path
        )
        lines.append(f"{index}. {location}: {error.message}")

    if len(errors) > 20:
        lines.append(f"... and {len(errors) - 20} additional schema errors.")

    raise AASSchemaValidationError(
        "Payload is not compatible with aas.json schema.",
        errors=lines,
    )
