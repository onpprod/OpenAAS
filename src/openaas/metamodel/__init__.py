# openaas/metamodel/__init__.py
from .asset_information import AssetKind, Resource, SpecificAssetId, AssetInformation
from .asset_administration_shell import AssetAdministrationShell
from .submodel import Submodel
from .concept_description import ConceptDescription
from .environment import Environment
from .data_element import (
    Property, MultiLanguageProperty, Range, File, Blob,
    ReferenceElement, RelationshipElement,
    SubmodelElementCollection, SubmodelElementList,
)

# Se você usa ForwardRefs em algum ponto, pode chamar model_rebuild() aqui.
# Ex.: AssetAdministrationShell.model_rebuild() ...
