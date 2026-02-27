"""AAS metamodel model class."""

from __future__ import annotations

from openaas.base_model import AASBaseModel


class EmbeddedDataSpecification(AASBaseModel):
    """Model for EmbeddedDataSpecification in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `EmbeddedDataSpecification` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    dataSpecification: Reference
    dataSpecificationContent: DataSpecificationContent_choice
