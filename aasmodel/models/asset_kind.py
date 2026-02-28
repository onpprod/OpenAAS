"""AAS metamodel enumeration."""

from __future__ import annotations

from enum import Enum


class AssetKind(str, Enum):
    """Enumeration for AssetKind.

    Constraints:
    - Allowed values are fixed by aas.json definition `AssetKind`.
    """
    Instance = 'Instance'
    NotApplicable = 'NotApplicable'
    Role = 'Role'
    Type = 'Type'
