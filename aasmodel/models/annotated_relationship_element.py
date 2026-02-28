"""AAS metamodel model class."""

from __future__ import annotations

from .relationship_element_abstract import RelationshipElement_abstract
from typing import Literal


class AnnotatedRelationshipElement(RelationshipElement_abstract):
    """Model for AnnotatedRelationshipElement in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `AnnotatedRelationshipElement` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    annotations: list[DataElement_choice] | None = None
    modelType: Literal['AnnotatedRelationshipElement'] = 'AnnotatedRelationshipElement'
