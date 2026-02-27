"""AAS metamodel model class."""

from __future__ import annotations

from .has_semantics import HasSemantics


class SpecificAssetId(HasSemantics):
    """Model for SpecificAssetId in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `SpecificAssetId` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    name: str
    value: str
    externalSubjectId: Reference | None = None
