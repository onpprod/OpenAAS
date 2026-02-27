"""AAS metamodel model class."""

from __future__ import annotations

from .submodel_element import SubmodelElement
from typing import Literal


class SubmodelElementList(SubmodelElement):
    """Model for SubmodelElementList in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `SubmodelElementList` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    orderRelevant: bool | None = None
    semanticIdListElement: Reference | None = None
    typeValueListElement: AasSubmodelElements
    valueTypeListElement: DataTypeDefXsd | None = None
    value: list[SubmodelElement_choice] | None = None
    modelType: Literal['SubmodelElementList'] = 'SubmodelElementList'
