"""AAS metamodel enumeration."""

from __future__ import annotations

from enum import Enum


class ModelType(str, Enum):
    """Enumeration for ModelType.

    Constraints:
    - Allowed values are fixed by aas.json definition `ModelType`.
    """
    AnnotatedRelationshipElement = 'AnnotatedRelationshipElement'
    AssetAdministrationShell = 'AssetAdministrationShell'
    BasicEventElement = 'BasicEventElement'
    Blob = 'Blob'
    Capability = 'Capability'
    ConceptDescription = 'ConceptDescription'
    DataSpecificationIec61360 = 'DataSpecificationIec61360'
    Entity = 'Entity'
    File = 'File'
    MultiLanguageProperty = 'MultiLanguageProperty'
    Operation = 'Operation'
    Property = 'Property'
    Range = 'Range'
    ReferenceElement = 'ReferenceElement'
    RelationshipElement = 'RelationshipElement'
    Submodel = 'Submodel'
    SubmodelElementCollection = 'SubmodelElementCollection'
    SubmodelElementList = 'SubmodelElementList'
