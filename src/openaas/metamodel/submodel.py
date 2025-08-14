from __future__ import annotations

from typing import List

from pydantic import Field

from openaas.metamodel.identifiable import Identifiable
from openaas.metamodel.has_semantics import HasSemantics
from openaas.metamodel.has_data_specification import HasDataSpecification
from openaas.metamodel.qualifiable import Qualifiable
from openaas.metamodel.has_kind import HasKind
from openaas.metamodel.submodel_element import SubmodelElement


class Submodel(Identifiable, HasSemantics, HasDataSpecification, Qualifiable, HasKind):
    """Conjunto de elementos que descreve um aspecto do ativo.

    Attributes:
        submodelElements: Lista de SubmodelElements deste submodelo.
    """
    submodelElements: List[SubmodelElement] = Field(default_factory=list)
