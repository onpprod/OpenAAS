"""AAS metamodel model class."""

from __future__ import annotations

from .data_element import DataElement
from typing import Literal


class Property(DataElement):
    """Model for Property in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `Property` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    valueType: DataTypeDefXsd
    value: str | None = None
    valueId: Reference | None = None
    modelType: Literal['Property'] = 'Property'
