"""AAS metamodel enumeration."""

from __future__ import annotations

from enum import Enum


class Direction(str, Enum):
    """Enumeration for Direction.

    Constraints:
    - Allowed values are fixed by aas.json definition `Direction`.
    """
    input = 'input'
    output = 'output'
