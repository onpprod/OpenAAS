from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from openaas.metamodel.reference import Reference


class AssetKind(str, Enum):
    """Enumera o tipo do ativo para AssetInformation."""
    Type = "Type"
    Instance = "Instance"
    NotApplicable = "NotApplicable"


class Resource(BaseModel):
    """Recurso binário referenciável (ex.: thumbnail).

    Attributes:
        path: Caminho/URL relativo dentro de um AASX ou absoluto (http/https/file).
        contentType: MIME type do recurso.
    """
    path: str
    contentType: str


class SpecificAssetId(BaseModel):
    """Par (name, value) que identifica o ativo em um domínio externo.

    Attributes:
        name: Nome da chave de identificação específica.
        value: Valor correspondente.
        externalSubjectId: Referência a entidade externa (opcional).
        semanticId: Referência semântica do identificador específico (opcional).
    """
    name: str
    value: str
    externalSubjectId: Optional[Reference] = None
    semanticId: Optional[Reference] = None


class AssetInformation(BaseModel):
    """

    Informações do ativo associadas ao AAS.

    Attributes:
        assetKind: Tipo do ativo (Type/Instance/NotApplicable).
        globalAssetId: Identificador global do ativo (IRI/UUID/IRDI).
        specificAssetIds: Lista de identificadores específicos.
        assetType: Tipo do ativo (livre ou taxonomizado externamente).
        defaultThumbnail: Recurso com miniatura do ativo.
    """
    assetKind: AssetKind
    globalAssetId: Optional[str] = None
    specificAssetIds: List[SpecificAssetId] = Field(default_factory=list)
    assetType: Optional[str] = None
    defaultThumbnail: Optional[Resource] = None
