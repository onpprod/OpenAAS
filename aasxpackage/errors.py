"""Error types for AASX package creation."""

from __future__ import annotations


class AASXPackageError(Exception):
    """Base error for aasxpackage operations."""


class AASXPackageSpecError(AASXPackageError, ValueError):
    """Raised when provided AAS data cannot be converted into an AASX package."""


class AASXPackageValidationError(AASXPackageSpecError):
    """Raised when payload is not compatible with AAS schema."""

    def __init__(self, message: str, *, errors: list[str] | None = None) -> None:
        super().__init__(message)
        self.errors = errors or []
