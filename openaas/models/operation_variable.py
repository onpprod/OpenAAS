"""AAS metamodel model class."""

from __future__ import annotations

from openaas.base_model import AASBaseModel


class OperationVariable(AASBaseModel):
    """Model for OperationVariable in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `OperationVariable` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    value: SubmodelElement_choice
