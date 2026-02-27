"""AAS metamodel model class."""

from __future__ import annotations

from .submodel_element import SubmodelElement
from typing import Literal


class Entity(SubmodelElement):
    """Model for Entity in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `Entity` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    statements: list[SubmodelElement_choice] | None = None
    entityType: EntityType | None = None
    globalAssetId: str | None = None
    specificAssetIds: list[SpecificAssetId] | None = None
    modelType: Literal['Entity'] = 'Entity'
