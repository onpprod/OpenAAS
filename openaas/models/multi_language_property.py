"""AAS metamodel model class."""

from __future__ import annotations

from .data_element import DataElement
from typing import Literal


class MultiLanguageProperty(DataElement):
    """Model for MultiLanguageProperty in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `MultiLanguageProperty` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    value: list[LangStringTextType] | None = None
    valueId: Reference | None = None
    modelType: Literal['MultiLanguageProperty'] = 'MultiLanguageProperty'
