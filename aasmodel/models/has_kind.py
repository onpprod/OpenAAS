"""AAS metamodel model class."""

from __future__ import annotations

from aasmodel.base_model import AASBaseModel
from typing import Optional


class HasKind(AASBaseModel):
    """Model for HasKind in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `HasKind` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    kind: Optional[ModellingKind] = None

