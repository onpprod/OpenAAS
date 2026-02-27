"""AAS metamodel model class."""

from __future__ import annotations

from .identifiable import Identifiable
from .has_kind import HasKind
from .has_semantics import HasSemantics
from .qualifiable import Qualifiable
from .has_data_specification import HasDataSpecification
from typing import Literal


class Submodel(Identifiable, HasKind, HasSemantics, Qualifiable, HasDataSpecification):
    """Model for Submodel in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `Submodel` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    submodelElements: list[SubmodelElement_choice] | None = None
    modelType: Literal['Submodel'] = 'Submodel'
