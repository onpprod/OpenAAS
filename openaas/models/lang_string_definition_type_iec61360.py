"""AAS metamodel model class."""

from __future__ import annotations

from .abstract_lang_string import AbstractLangString
from typing import Any


class LangStringDefinitionTypeIec61360(AbstractLangString):
    """Model for LangStringDefinitionTypeIec61360 in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `LangStringDefinitionTypeIec61360` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    text: Any | None = None
