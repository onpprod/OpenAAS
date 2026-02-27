"""Pydantic AAS metamodel classes generated from aas.json definitions."""

from __future__ import annotations

from .aas_submodel_elements import AasSubmodelElements
from .abstract_lang_string import AbstractLangString
from .administrative_information import AdministrativeInformation
from .annotated_relationship_element import AnnotatedRelationshipElement
from .asset_administration_shell import AssetAdministrationShell
from .asset_information import AssetInformation
from .asset_kind import AssetKind
from .basic_event_element import BasicEventElement
from .blob import Blob
from .capability import Capability
from .concept_description import ConceptDescription
from .data_element import DataElement
from .data_element_choice import DataElement_choice
from .data_specification_content import DataSpecificationContent
from .data_specification_content_choice import DataSpecificationContent_choice
from .data_specification_iec61360 import DataSpecificationIec61360
from .data_type_def_xsd import DataTypeDefXsd
from .data_type_iec61360 import DataTypeIec61360
from .direction import Direction
from .embedded_data_specification import EmbeddedDataSpecification
from .entity import Entity
from .entity_type import EntityType
from .environment import Environment
from .event_element import EventElement
from .event_payload import EventPayload
from .extension import Extension
from .file import File
from .has_data_specification import HasDataSpecification
from .has_extensions import HasExtensions
from .has_kind import HasKind
from .has_semantics import HasSemantics
from .identifiable import Identifiable
from .key import Key
from .key_types import KeyTypes
from .lang_string_definition_type_iec61360 import LangStringDefinitionTypeIec61360
from .lang_string_name_type import LangStringNameType
from .lang_string_preferred_name_type_iec61360 import LangStringPreferredNameTypeIec61360
from .lang_string_short_name_type_iec61360 import LangStringShortNameTypeIec61360
from .lang_string_text_type import LangStringTextType
from .level_type import LevelType
from .model_type import ModelType
from .modelling_kind import ModellingKind
from .multi_language_property import MultiLanguageProperty
from .operation import Operation
from .operation_variable import OperationVariable
from .property import Property
from .qualifiable import Qualifiable
from .qualifier import Qualifier
from .qualifier_kind import QualifierKind
from .range import Range
from .referable import Referable
from .reference import Reference
from .reference_element import ReferenceElement
from .reference_types import ReferenceTypes
from .relationship_element import RelationshipElement
from .relationship_element_abstract import RelationshipElement_abstract
from .relationship_element_choice import RelationshipElement_choice
from .resource import Resource
from .specific_asset_id import SpecificAssetId
from .state_of_event import StateOfEvent
from .submodel import Submodel
from .submodel_element import SubmodelElement
from .submodel_element_collection import SubmodelElementCollection
from .submodel_element_list import SubmodelElementList
from .submodel_element_choice import SubmodelElement_choice
from .value_list import ValueList
from .value_reference_pair import ValueReferencePair


__all__ = [
    "AasSubmodelElements",
    "AbstractLangString",
    "AdministrativeInformation",
    "AnnotatedRelationshipElement",
    "AssetAdministrationShell",
    "AssetInformation",
    "AssetKind",
    "BasicEventElement",
    "Blob",
    "Capability",
    "ConceptDescription",
    "DataElement",
    "DataElement_choice",
    "DataSpecificationContent",
    "DataSpecificationContent_choice",
    "DataSpecificationIec61360",
    "DataTypeDefXsd",
    "DataTypeIec61360",
    "Direction",
    "EmbeddedDataSpecification",
    "Entity",
    "EntityType",
    "Environment",
    "EventElement",
    "EventPayload",
    "Extension",
    "File",
    "HasDataSpecification",
    "HasExtensions",
    "HasKind",
    "HasSemantics",
    "Identifiable",
    "Key",
    "KeyTypes",
    "LangStringDefinitionTypeIec61360",
    "LangStringNameType",
    "LangStringPreferredNameTypeIec61360",
    "LangStringShortNameTypeIec61360",
    "LangStringTextType",
    "LevelType",
    "ModelType",
    "ModellingKind",
    "MultiLanguageProperty",
    "Operation",
    "OperationVariable",
    "Property",
    "Qualifiable",
    "Qualifier",
    "QualifierKind",
    "Range",
    "Referable",
    "Reference",
    "ReferenceElement",
    "ReferenceTypes",
    "RelationshipElement",
    "RelationshipElement_abstract",
    "RelationshipElement_choice",
    "Resource",
    "SpecificAssetId",
    "StateOfEvent",
    "Submodel",
    "SubmodelElement",
    "SubmodelElementCollection",
    "SubmodelElementList",
    "SubmodelElement_choice",
    "ValueList",
    "ValueReferencePair",
]


_MODEL_CLASSES = [
    AbstractLangString,
    AdministrativeInformation,
    AnnotatedRelationshipElement,
    AssetAdministrationShell,
    AssetInformation,
    BasicEventElement,
    Blob,
    Capability,
    ConceptDescription,
    DataElement,
    DataElement_choice,
    DataSpecificationContent,
    DataSpecificationContent_choice,
    DataSpecificationIec61360,
    EmbeddedDataSpecification,
    Entity,
    Environment,
    EventElement,
    EventPayload,
    Extension,
    File,
    HasDataSpecification,
    HasExtensions,
    HasKind,
    HasSemantics,
    Identifiable,
    Key,
    LangStringDefinitionTypeIec61360,
    LangStringNameType,
    LangStringPreferredNameTypeIec61360,
    LangStringShortNameTypeIec61360,
    LangStringTextType,
    LevelType,
    MultiLanguageProperty,
    Operation,
    OperationVariable,
    Property,
    Qualifiable,
    Qualifier,
    Range,
    Referable,
    Reference,
    ReferenceElement,
    RelationshipElement,
    RelationshipElement_abstract,
    RelationshipElement_choice,
    Resource,
    SpecificAssetId,
    Submodel,
    SubmodelElement,
    SubmodelElementCollection,
    SubmodelElementList,
    SubmodelElement_choice,
    ValueList,
    ValueReferencePair,
]

for _model in _MODEL_CLASSES:
    _model.model_rebuild(_types_namespace=globals())
