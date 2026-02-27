"""AAS metamodel model class."""

from __future__ import annotations

from openaas.base_model import AASBaseModel


class Key(AASBaseModel):
    """Model for Key in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `Key` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    type: KeyTypes
    value: str
