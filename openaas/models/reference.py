"""AAS metamodel model class."""

from __future__ import annotations

from openaas.base_model import AASBaseModel


class Reference(AASBaseModel):
    """Model for Reference in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `Reference` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    type: ReferenceTypes
    referredSemanticId: Reference | None = None
    keys: list[Key]
