"""AAS metamodel model class."""

from __future__ import annotations

from .submodel_element import SubmodelElement
from typing import Literal


class Operation(SubmodelElement):
    """Model for Operation in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `Operation` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    inputVariables: list[OperationVariable] | None = None
    outputVariables: list[OperationVariable] | None = None
    inoutputVariables: list[OperationVariable] | None = None
    modelType: Literal['Operation'] = 'Operation'
