"""AAS metamodel model class."""

from __future__ import annotations

from .has_data_specification import HasDataSpecification


class AdministrativeInformation(HasDataSpecification):
    """Model for AdministrativeInformation in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `AdministrativeInformation` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    version: str | None = None
    revision: str | None = None
    creator: Reference | None = None
    templateId: str | None = None
