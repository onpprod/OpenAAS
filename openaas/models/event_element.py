"""AAS metamodel model class."""

from __future__ import annotations

from .submodel_element import SubmodelElement


class EventElement(SubmodelElement):
    """Model for EventElement in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `EventElement` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    pass
