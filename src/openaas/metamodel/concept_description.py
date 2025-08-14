from __future__ import annotations

from typing import List

from pydantic import Field

from openaas.metamodel.identifiable import Identifiable
from openaas.metamodel.has_data_specification import HasDataSpecification
from openaas.metamodel.reference import Reference


class ConceptDescription(Identifiable, HasDataSpecification):
    """
    Descrição de conceito usada para dar semântica a elementos.

    Attributes:
        isCaseOf: Referências a conceitos externos equivalentes/relacionados.
    """
    isCaseOf: List[Reference] = Field(default_factory=list)
