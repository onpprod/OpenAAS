from typing import Optional, List

from pydantic import Field

from openaas.metamodel.base import NameType
from openaas.metamodel.has_semantics import HasSemantics
from openaas.metamodel.reference import Reference


class Extension(HasSemantics):
    """Extensão proprietária aplicada a elementos com HasExtensions.

    Attributes:
        name: Nome da extensão.
        valueType: Tipo do valor (default xs:string).
        value: Valor literal (opcional).
        refersTo: Referências a elementos afetados/relacionados.
    """
    name: NameType
    valueType: Optional[str] = None
    value: Optional[str] = None
    refersTo: List[Reference] = Field(default_factory=list)