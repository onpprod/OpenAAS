"""AAS metamodel enumeration."""

from __future__ import annotations

from enum import Enum


class EntityType(str, Enum):
    """Enumeration for EntityType.

    Constraints:
    - Allowed values are fixed by aas.json definition `EntityType`.
    """
    CoManagedEntity = 'CoManagedEntity'
    SelfManagedEntity = 'SelfManagedEntity'
