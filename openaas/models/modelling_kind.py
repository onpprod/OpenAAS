"""AAS metamodel enumeration."""

from __future__ import annotations

from enum import Enum


class ModellingKind(str, Enum):
    """Enumeration for ModellingKind.

    Constraints:
    - Allowed values are fixed by aas.json definition `ModellingKind`.
    """
    Instance = 'Instance'
    Template = 'Template'
