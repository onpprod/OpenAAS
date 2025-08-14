from abc import ABC
from typing import Optional

from openaas.metamodel.base import NameType, MultiLanguageNameType, MultiLanguageTextType
from openaas.metamodel.has_extensions import HasExtensions


class Referable(HasExtensions, ABC):
    """Elemento referenciável.

    Attributes:
        category: Categoria (obsoleto na V3.x; manter apenas para compatibilidade).
        idShort: Identificador curto, único no contexto local.
        displayName: Nome multilíngua exibível.
        description: Descrição multilíngua.
    """
    category: Optional[NameType] = None  # deprecated na V3
    idShort: Optional[NameType] = None
    displayName: Optional[MultiLanguageNameType] = None
    description: Optional[MultiLanguageTextType] = None
