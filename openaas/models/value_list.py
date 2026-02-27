"""AAS metamodel model class."""

from __future__ import annotations

from openaas.base_model import AASBaseModel


class ValueList(AASBaseModel):
    """Model for ValueList in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `ValueList` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    valueReferencePairs: list[ValueReferencePair]
