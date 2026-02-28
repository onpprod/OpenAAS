"""AAS metamodel enumeration."""

from __future__ import annotations

from enum import Enum


class AasSubmodelElements(str, Enum):
    """Enumeration for AasSubmodelElements.

    Constraints:
    - Allowed values are fixed by aas.json definition `AasSubmodelElements`.
    """
    AnnotatedRelationshipElement = 'AnnotatedRelationshipElement'
    BasicEventElement = 'BasicEventElement'
    Blob = 'Blob'
    Capability = 'Capability'
    DataElement = 'DataElement'
    Entity = 'Entity'
    EventElement = 'EventElement'
    File = 'File'
    MultiLanguageProperty = 'MultiLanguageProperty'
    Operation = 'Operation'
    Property = 'Property'
    Range = 'Range'
    ReferenceElement = 'ReferenceElement'
    RelationshipElement = 'RelationshipElement'
    SubmodelElement = 'SubmodelElement'
    SubmodelElementCollection = 'SubmodelElementCollection'
    SubmodelElementList = 'SubmodelElementList'
