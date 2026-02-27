"""AAS metamodel model class."""

from __future__ import annotations

from openaas.base_model import AASBaseModel


class HasSemantics(AASBaseModel):
    """Model for HasSemantics in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `HasSemantics` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    semanticId: Reference | None = None
    supplementalSemanticIds: list[Reference] | None = None
