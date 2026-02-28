"""AAS metamodel model class."""

from __future__ import annotations

from .data_element import DataElement
from typing import Literal


class ReferenceElement(DataElement):
    """Model for ReferenceElement in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `ReferenceElement` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    value: Reference | None = None
    modelType: Literal['ReferenceElement'] = 'ReferenceElement'
