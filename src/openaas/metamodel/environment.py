from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field

from openaas.metamodel.asset_administration_shell import AssetAdministrationShell
from openaas.metamodel.submodel import Submodel
from openaas.metamodel.concept_description import ConceptDescription


class Environment(BaseModel):
    """Raiz do metamodelo AAS (troca/serialização).

    Attributes:
        assetAdministrationShells: Lista de AAS.
        submodels: Lista de Submodels.
        conceptDescriptions: Lista de CDs.
    """
    modelType: str = "Environment"
    assetAdministrationShells: List[AssetAdministrationShell] = Field(default_factory=list)
    submodels: List[Submodel] = Field(default_factory=list)
    conceptDescriptions: List[ConceptDescription] = Field(default_factory=list)
