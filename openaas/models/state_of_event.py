"""AAS metamodel enumeration."""

from __future__ import annotations

from enum import Enum


class StateOfEvent(str, Enum):
    """Enumeration for StateOfEvent.

    Constraints:
    - Allowed values are fixed by aas.json definition `StateOfEvent`.
    """
    off = 'off'
    on = 'on'
