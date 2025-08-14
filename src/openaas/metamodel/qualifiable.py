from abc import ABC
from typing import List

from pydantic import BaseModel, Field

from openaas.metamodel.qualifier import Qualifier


class Qualifiable(BaseModel, ABC):
    """Elemento que pode possuir qualifiers.

    Attributes:
        qualifier: Lista de qualificadores.
    """
    qualifier: List[Qualifier] = Field(default_factory=list)