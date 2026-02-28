"""AAS metamodel model class."""

from __future__ import annotations

from aasmodel.base_model import AASBaseModel


class ValueReferencePair(AASBaseModel):
    """Model for ValueReferencePair in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `ValueReferencePair` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    value: str
    valueId: Reference | None = None

