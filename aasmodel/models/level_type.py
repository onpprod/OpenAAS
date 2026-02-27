"""AAS metamodel model class."""

from __future__ import annotations

from aasmodel.base_model import AASBaseModel


class LevelType(AASBaseModel):
    """Model for LevelType in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `LevelType` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    min: bool
    nom: bool
    typ: bool
    max: bool

