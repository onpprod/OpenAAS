from typing import List
from pydantic import BaseModel, Field
from abc import ABC

from openaas.metamodel.extension import Extension


class HasExtensions(BaseModel, ABC):
    """Elemento que pode ter extensões proprietárias.

    Attributes:
        extension: Lista de extensões aplicadas ao elemento.
    """
    extension: List[Extension] = Field(default_factory=list)
