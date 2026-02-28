"""AAS metamodel model class."""

from __future__ import annotations

from aasmodel.base_model import AASBaseModel


class Resource(AASBaseModel):
    """Model for Resource in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `Resource` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    path: str
    contentType: str | None = None

