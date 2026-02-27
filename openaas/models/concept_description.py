"""AAS metamodel model class."""

from __future__ import annotations

from .identifiable import Identifiable
from .has_data_specification import HasDataSpecification
from typing import Literal


class ConceptDescription(Identifiable, HasDataSpecification):
    """Model for ConceptDescription in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `ConceptDescription` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    isCaseOf: list[Reference] | None = None
    modelType: Literal['ConceptDescription'] = 'ConceptDescription'
