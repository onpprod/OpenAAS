"""AAS metamodel model class."""

from __future__ import annotations

from .data_element import DataElement
from typing import Literal


class Range(DataElement):
    """Model for Range in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `Range` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    valueType: DataTypeDefXsd
    min: str | None = None
    max: str | None = None
    modelType: Literal['Range'] = 'Range'
