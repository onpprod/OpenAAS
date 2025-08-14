from abc import ABC
from typing import List

from pydantic import BaseModel, Field

from openaas.metamodel.reference import Reference


class HasDataSpecification(BaseModel, ABC):
    """Liga o elemento a templates de data specification (Part 3).

    Attributes:
        dataSpecification: Referências (globais) a templates de data specification.
    """
    dataSpecification: List[Reference] = Field(default_factory=list)