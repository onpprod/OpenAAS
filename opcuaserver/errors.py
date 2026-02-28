"""Error types used by opcuaserver."""

from __future__ import annotations


class OPCUAServerError(Exception):
    """Base exception for opcuaserver."""


class OPCUASpecError(OPCUAServerError, ValueError):
    """Raised when the AAS JSON content is invalid for server generation."""


class OPCUASchemaValidationError(OPCUASpecError):
    """Raised when the AAS JSON does not match the JSON Schema."""

    def __init__(self, message: str, *, errors: list[str] | None = None) -> None:
        super().__init__(message)
        self.errors = errors or []
