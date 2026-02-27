"""AAS metamodel model class."""

from __future__ import annotations

from openaas.base_model import AASBaseModel


class DataSpecificationContent(AASBaseModel):
    """Model for DataSpecificationContent in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `DataSpecificationContent` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    modelType: ModelType
