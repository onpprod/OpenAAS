"""AAS metamodel model class."""

from __future__ import annotations

from .submodel_element import SubmodelElement
from typing import Literal


class SubmodelElementCollection(SubmodelElement):
    """Model for SubmodelElementCollection in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `SubmodelElementCollection` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    value: list[SubmodelElement_choice] | None = None
    modelType: Literal['SubmodelElementCollection'] = 'SubmodelElementCollection'
