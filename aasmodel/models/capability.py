"""AAS metamodel model class."""

from __future__ import annotations

from .submodel_element import SubmodelElement
from typing import Literal


class Capability(SubmodelElement):
    """Model for Capability in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `Capability` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    modelType: Literal['Capability'] = 'Capability'
