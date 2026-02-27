"""AAS metamodel model class."""

from __future__ import annotations

from .referable import Referable
from .has_semantics import HasSemantics
from .qualifiable import Qualifiable
from .has_data_specification import HasDataSpecification


class SubmodelElement(Referable, HasSemantics, Qualifiable, HasDataSpecification):
    """Model for SubmodelElement in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `SubmodelElement` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    pass
