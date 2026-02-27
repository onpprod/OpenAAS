"""AAS metamodel model class."""

from __future__ import annotations

from openaas.base_model import AASBaseModel


class HasDataSpecification(AASBaseModel):
    """Model for HasDataSpecification in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `HasDataSpecification` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    embeddedDataSpecifications: list[EmbeddedDataSpecification] | None = None
