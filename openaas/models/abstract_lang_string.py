"""AAS metamodel model class."""

from __future__ import annotations

from openaas.base_model import AASBaseModel


class AbstractLangString(AASBaseModel):
    """Model for AbstractLangString in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `AbstractLangString` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    language: str
    text: str
