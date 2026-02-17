from __future__ import annotations

from typing import List, Optional

from pydantic import Field, field_validator

from openaas.metamodel.identifiable import Identifiable
from openaas.metamodel.has_data_specification import HasDataSpecification
from openaas.metamodel.reference import Reference
from openaas.metamodel.reference_type import ReferenceType
from openaas.metamodel.asset_information import AssetInformation


class AssetAdministrationShell(Identifiable, HasDataSpecification):
    """
    Shell que representa digitalmente um ativo.

    Attributes:
        assetInformation: Informações do ativo (obrigatório).
        derivedFrom: Referência a outro AAS do qual este deriva (opcional).
        submodels: Referências aos Submodels deste AAS.
    """
    assetInformation: AssetInformation
    derivedFrom: Optional[Reference] = None
    submodels: List[Reference] = Field(default_factory=list)

    @field_validator("derivedFrom")
    @classmethod
    def _check_derived_from(cls, v: Optional[Reference]):
        """Se existir, deve ser ModelReference cujo 1º key seja AssetAdministrationShell."""
        if v and (v.type != ReferenceType.ModelReference or v.keys[0].type != "AssetAdministrationShell"):
            raise ValueError("derivedFrom deve referenciar um AssetAdministrationShell (ModelReference).")
        return v

    @field_validator("submodels")
    @classmethod
    def _check_submodels(cls, v: List[Reference]):
        """Cada referência deve apontar para Submodel (ModelReference)."""
        for r in v:
            if r.type != ReferenceType.ModelReference or r.keys[0].type != "Submodel":
                raise ValueError("Cada item em submodels deve referenciar um Submodel (ModelReference).")
        return v
