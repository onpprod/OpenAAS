"""AAS metamodel model class."""

from __future__ import annotations

from .referable import Referable


class Identifiable(Referable):
    """Model for Identifiable in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `Identifiable` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    administration: AdministrativeInformation | None = None
    id: str
