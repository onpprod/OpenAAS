"""AAS metamodel enumeration."""

from __future__ import annotations

from enum import Enum


class KeyTypes(str, Enum):
    """Enumeration for KeyTypes.

    Constraints:
    - Allowed values are fixed by aas.json definition `KeyTypes`.
    """
    AnnotatedRelationshipElement = 'AnnotatedRelationshipElement'
    AssetAdministrationShell = 'AssetAdministrationShell'
    BasicEventElement = 'BasicEventElement'
    Blob = 'Blob'
    Capability = 'Capability'
    ConceptDescription = 'ConceptDescription'
    DataElement = 'DataElement'
    Entity = 'Entity'
    EventElement = 'EventElement'
    File = 'File'
    FragmentReference = 'FragmentReference'
    GlobalReference = 'GlobalReference'
    Identifiable = 'Identifiable'
    MultiLanguageProperty = 'MultiLanguageProperty'
    Operation = 'Operation'
    Property = 'Property'
    Range = 'Range'
    Referable = 'Referable'
    ReferenceElement = 'ReferenceElement'
    RelationshipElement = 'RelationshipElement'
    Submodel = 'Submodel'
    SubmodelElement = 'SubmodelElement'
    SubmodelElementCollection = 'SubmodelElementCollection'
    SubmodelElementList = 'SubmodelElementList'
