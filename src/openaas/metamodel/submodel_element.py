from abc import ABC

from openaas.metamodel.has_data_specification import HasDataSpecification
from openaas.metamodel.has_semantics import HasSemantics
from openaas.metamodel.qualifiable import Qualifiable
from openaas.metamodel.referable import Referable


class SubmodelElement(Referable, HasSemantics, Qualifiable, HasDataSpecification, ABC):
    """Base abstrata para todos os Submodel Elements.

    Nota:
        Desde a V3, SME **não** herda mais HasKind; o 'kind' fica no Submodel.
    """
    pass