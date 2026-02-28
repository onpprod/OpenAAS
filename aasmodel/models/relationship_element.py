"""AAS metamodel model class."""

from __future__ import annotations

from .relationship_element_abstract import RelationshipElement_abstract
from typing import Literal


class RelationshipElement(RelationshipElement_abstract):
    """Model for RelationshipElement in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `RelationshipElement` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    modelType: Literal['RelationshipElement'] = 'RelationshipElement'
