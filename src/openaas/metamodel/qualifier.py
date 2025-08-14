from typing import Optional

from pydantic import BaseModel

from openaas.metamodel.base import NameType
from openaas.metamodel.reference import Reference


class Qualifier(BaseModel):
    """Qualificador aplicável a elementos 'Qualifiable'.

    Attributes:
        type: Tipo do qualificador (nome).
        valueType: Tipo do valor (ex.: DataTypeDefXsd).
        value: Valor literal, se aplicável.
        valueId: Referência a valor codificado/externo.
    """
    type: NameType
    valueType: Optional[str] = None
    value: Optional[str] = None
    valueId: Optional[Reference] = None