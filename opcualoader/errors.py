"""Error types for opcualoader."""

from __future__ import annotations


class OPCUALoaderError(Exception):
    """Base exception for opcualoader."""


class OPCUALoaderSpecError(OPCUALoaderError, ValueError):
    """Raised when the OPC UA source cannot be mapped to valid AAS content."""


class OPCUALoaderSchemaError(OPCUALoaderSpecError):
    """Raised when generated JSON does not match the AAS schema."""

    def __init__(self, message: str, *, errors: list[str] | None = None) -> None:
        super().__init__(message)
        self.errors = errors or []
