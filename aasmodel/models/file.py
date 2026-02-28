"""AAS metamodel model class."""

from __future__ import annotations

from .data_element import DataElement
from typing import Literal


class File(DataElement):
    """Model for File in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `File` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    value: str | None = None
    contentType: str | None = None
    modelType: Literal['File'] = 'File'
