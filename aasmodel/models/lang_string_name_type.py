"""AAS metamodel model class."""

from __future__ import annotations

from .abstract_lang_string import AbstractLangString
from typing import Any


class LangStringNameType(AbstractLangString):
    """Model for LangStringNameType in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `LangStringNameType` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    text: Any | None = None
