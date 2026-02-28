"""AAS metamodel model class."""

from __future__ import annotations

from .data_element import DataElement
from typing import Literal


class Blob(DataElement):
    """Model for Blob in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `Blob` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    value: str | None = None
    contentType: str | None = None
    modelType: Literal['Blob'] = 'Blob'
