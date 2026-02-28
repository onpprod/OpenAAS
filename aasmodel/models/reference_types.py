"""AAS metamodel enumeration."""

from __future__ import annotations

from enum import Enum


class ReferenceTypes(str, Enum):
    """Enumeration for ReferenceTypes.

    Constraints:
    - Allowed values are fixed by aas.json definition `ReferenceTypes`.
    """
    ExternalReference = 'ExternalReference'
    ModelReference = 'ModelReference'
