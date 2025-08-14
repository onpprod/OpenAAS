from __future__ import annotations

from abc import ABC

from typing import Dict, List, Optional
from pydantic import BaseModel, Base64Bytes, Field, field_validator

from openaas.metamodel.reference import Reference
from openaas.metamodel.reference_type import ReferenceType
from openaas.metamodel.submodel_element import SubmodelElement


class DataElement(SubmodelElement, ABC):
    """Abstração de SME com 'valor' (ex.: Property, Range, File)."""
    pass

# -----------------------
# Data elements concretos
# -----------------------

class Property(SubmodelElement):
    """Propriedade com valor atômico.

    Attributes:
        valueType: Tipo do valor (ex.: 'string', 'double', 'dateTime' – alinhe com DataTypeDefXsd).
        value: Valor literal (opcional).
        valueId: Referência a valor codificado (opcional).
    Rules:
        - Pelo menos um de (value, valueId) deve ser informado.
    """
    valueType: str
    value: Optional[str] = None
    valueId: Optional[Reference] = None

    @field_validator("valueId")
    @classmethod
    def _value_or_valueid(cls, v, info):
        val = info.data.get("value")
        if v is None and (val is None or str(val) == ""):
            raise ValueError("Property requer 'value' ou 'valueId'.")
        return v


class MultiLanguageProperty(SubmodelElement):
    """Propriedade multilíngua.

    Attributes:
        value: Dicionário língua→texto (ex.: {'en': 'Motor', 'pt': 'Motor'}).
        valueId: Referência a valor codificado (opcional).
    """
    value: Dict[str, str]
    valueId: Optional[Reference] = None


class Range(SubmodelElement):
    """Intervalo de valores.

    Attributes:
        valueType: Tipo associado ao intervalo.
        min: Valor mínimo (opcional).
        max: Valor máximo (opcional).
    Rules:
        - Pelo menos um de (min, max) deve existir.
    """
    valueType: str
    min: Optional[str] = None
    max: Optional[str] = None

    @field_validator("max")
    @classmethod
    def _min_or_max(cls, v, info):
        if v is None and info.data.get("min") is None:
            raise ValueError("Range requer 'min' ou 'max'.")
        return v


class File(SubmodelElement):
    """Referência a arquivo.

    Attributes:
        contentType: MIME type do arquivo.
        value: Caminho/URL do arquivo.
    """
    contentType: str
    value: str


class Blob(SubmodelElement):
    """Bloco binário embutido.

    Attributes:
        contentType: MIME type do blob.
        value: Conteúdo em base64 (decodificado automaticamente em Base64Bytes).
    """
    contentType: str
    value: Base64Bytes


class ReferenceElement(SubmodelElement):
    """Elemento cujo valor é uma Reference (model ou externa)."""

    value: Reference


class RelationshipElement(SubmodelElement):
    """Relacionamento entre dois alvos referenciados.

    Attributes:
        first: Referência ao primeiro alvo (ModelReference).
        second: Referência ao segundo alvo (ModelReference).
    """
    first: Reference
    second: Reference

    @field_validator("first", "second")
    @classmethod
    def _check_is_model_ref(cls, v: Reference):
        if v.type != ReferenceType.ModelReference:
            raise ValueError("RelationshipElement requer ModelReference em 'first' e 'second'.")
        return v


class SubmodelElementCollection(SubmodelElement):
    """Coleção de elementos.

    Attributes:
        value: Lista de SubmodelElements.
        orderRelevant: Define se a ordem é relevante (default True).
    """
    value: List[SubmodelElement] = Field(default_factory=list)
    orderRelevant: bool = True


class SubmodelElementList(SubmodelElement):
    """Lista homogênea de elementos (opcionalmente tipada).

    Attributes:
        value: Lista de elementos.
        typeValueListElement: Nome do tipo esperado dos elementos (ex.: 'Property').
        semanticIdListElement: Semântica comum aos elementos (opcional).
        valueTypeListElement: Tipo do valor quando a lista é de DataElements atômicos (opcional).
        orderRelevant: Define se a ordem é relevante (default True).
    Rules:
        - Se 'typeValueListElement' for informado, cada item de 'value' deve ter
          o tipo de classe correspondente (ex.: 'Property' → isinstance(Property)).
    """
    value: List[SubmodelElement] = Field(default_factory=list)
    typeValueListElement: Optional[str] = None
    semanticIdListElement: Optional[Reference] = None
    valueTypeListElement: Optional[str] = None
    orderRelevant: bool = True

    @field_validator("value")
    @classmethod
    def _check_homogeneous_type(cls, v, info):
        expected = info.data.get("typeValueListElement")
        if expected:
            for it in v:
                if it.__class__.__name__ != expected:
                    raise ValueError(
                        f"SubmodelElementList espera elementos do tipo '{expected}', "
                        f"mas encontrou '{it.__class__.__name__}'."
                    )
        return v
