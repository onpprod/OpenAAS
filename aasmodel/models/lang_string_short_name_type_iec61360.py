"""AAS metamodel model class."""

from __future__ import annotations

from .abstract_lang_string import AbstractLangString
from typing import Any


class LangStringShortNameTypeIec61360(AbstractLangString):
    """Model for LangStringShortNameTypeIec61360 in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `LangStringShortNameTypeIec61360` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    text: Any | None = None
