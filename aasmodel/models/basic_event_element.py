"""AAS metamodel model class."""

from __future__ import annotations

from .event_element import EventElement
from typing import Literal


class BasicEventElement(EventElement):
    """Model for BasicEventElement in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `BasicEventElement` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    observed: Reference
    direction: Direction
    state: StateOfEvent
    messageTopic: str | None = None
    messageBroker: Reference | None = None
    lastUpdate: str | None = None
    minInterval: str | None = None
    maxInterval: str | None = None
    modelType: Literal['BasicEventElement'] = 'BasicEventElement'
