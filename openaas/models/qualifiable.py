"""AAS metamodel model class."""

from __future__ import annotations

from openaas.base_model import AASBaseModel


class Qualifiable(AASBaseModel):
    """Model for Qualifiable in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `Qualifiable` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    qualifiers: list[Qualifier] | None = None
    modelType: ModelType
