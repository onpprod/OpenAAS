"""Load AAS JSON from an OPC UA server produced by opcuaserver."""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from asyncua import Client, ua

from .errors import OPCUALoaderSpecError
from .validation import validate_aas_environment

DEFAULT_TIMEOUT = 10.0

_OPERATION_GROUPS = {
    "inputvariables": "inputVariables",
    "outputvariables": "outputVariables",
    "inoutputvariables": "inoutputVariables",
}

_VARIANT_TO_XSD: dict[ua.VariantType, str] = {
    ua.VariantType.Boolean: "xs:boolean",
    ua.VariantType.SByte: "xs:byte",
    ua.VariantType.Byte: "xs:unsignedByte",
    ua.VariantType.Int16: "xs:short",
    ua.VariantType.UInt16: "xs:unsignedShort",
    ua.VariantType.Int32: "xs:int",
    ua.VariantType.UInt32: "xs:unsignedInt",
    ua.VariantType.Int64: "xs:long",
    ua.VariantType.UInt64: "xs:unsignedLong",
    ua.VariantType.Float: "xs:float",
    ua.VariantType.Double: "xs:double",
    ua.VariantType.String: "xs:string",
    ua.VariantType.DateTime: "xs:dateTime",
    ua.VariantType.Guid: "xs:string",
}

_LEGACY_METADATA_PAYLOAD_NAME = "__aas_json"
_LEGACY_METADATA_FIELD_PREFIX = "__aas_meta__"


@dataclass
class _NodeInfo:
    node: Any
    name: str
    node_class: ua.NodeClass
    is_property: bool = False


@dataclass
class _NodeMetadata:
    category: str | None = None
    fields: dict[str, Any] = field(default_factory=dict)
    payload: dict[str, Any] | None = None


class _IdShortAllocator:
    def __init__(self) -> None:
        self._used: set[str] = set()

    def allocate(self, name: str | None) -> str:
        base = _sanitize_id_short(name)
        candidate = base
        index = 2
        while candidate in self._used:
            suffix = f"_{index}"
            max_base_len = 128 - len(suffix)
            trimmed = base[:max_base_len] if max_base_len > 0 else "A"
            candidate = f"{trimmed}{suffix}"
            index += 1
        self._used.add(candidate)
        return candidate


async def load_aas_environment_from_server(
    endpoint: str,
    *,
    username: str | None = None,
    password: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    schema_path: str | Path | None = None,
    validate_schema: bool = True,
) -> dict[str, Any]:
    """Connect to an OPC UA server and reconstruct an AAS environment JSON."""
    if not endpoint or not str(endpoint).strip():
        raise OPCUALoaderSpecError("Endpoint must be a non-empty string.")

    if (username is None) != (password is None):
        raise OPCUALoaderSpecError("Username and password must be provided together.")

    client = Client(url=str(endpoint), timeout=timeout)
    if username is not None:
        client.set_user(username)
        client.set_password(password)

    async with client:
        environment = await _scan_client(client, endpoint=str(endpoint))

    if validate_schema:
        validate_aas_environment(environment, schema_path=schema_path)
    return environment


async def export_aas_environment_to_file(
    endpoint: str,
    output_path: str | Path,
    *,
    username: str | None = None,
    password: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    schema_path: str | Path | None = None,
    validate_schema: bool = True,
    pretty: bool = True,
) -> dict[str, Any]:
    """Load AAS from OPC UA endpoint and write it to a JSON file."""
    environment = await load_aas_environment_from_server(
        endpoint,
        username=username,
        password=password,
        timeout=timeout,
        schema_path=schema_path,
        validate_schema=validate_schema,
    )

    out_path = Path(output_path)
    if not out_path.is_absolute():
        out_path = Path.cwd() / out_path
    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    dump_kwargs: dict[str, Any] = {"ensure_ascii": True}
    if pretty:
        dump_kwargs["indent"] = 2
    else:
        dump_kwargs["separators"] = (",", ":")

    with out_path.open("w", encoding="utf-8") as fp:
        json.dump(environment, fp, **dump_kwargs)
    return environment


async def _scan_client(client: Client, *, endpoint: str) -> dict[str, Any]:
    aas_root = await _find_child_by_name(client.nodes.objects, "AAS")
    if aas_root is None:
        raise OPCUALoaderSpecError(
            "Could not find 'AAS' node under Objects. "
            "This endpoint does not look like an opcuaserver tree."
        )

    environment = await _scan_environment_root(aas_root, endpoint=endpoint)
    if environment is not None:
        return environment

    return await _scan_legacy_root(aas_root, endpoint=endpoint)


async def _scan_environment_root(
    aas_root: Any,
    *,
    endpoint: str,
) -> dict[str, Any] | None:
    environment_node = await _find_child_by_name(aas_root, "Environment")
    if environment_node is None:
        return None

    child_infos = await _get_child_infos(environment_node)
    child_infos, metadata = await _extract_metadata_children(child_infos)

    environment: dict[str, Any] = {}
    if isinstance(metadata.payload, dict):
        environment.update(metadata.payload)
    if metadata.fields:
        environment.update(metadata.fields)
    if metadata.category is not None and "category" not in environment:
        environment["category"] = metadata.category

    shell_entries: list[dict[str, Any]] = []
    inline_submodels_by_id: dict[str, dict[str, Any]] = {}
    shell_folder = _find_info_by_name(child_infos, "AssetAdministrationShells")
    if shell_folder is not None:
        shell_nodes = await _get_child_infos(shell_folder.node)
        shell_allocator = _IdShortAllocator()
        for index, shell_info in enumerate(shell_nodes):
            if shell_info.node_class != ua.NodeClass.Object:
                continue
            shell, inline_submodels = await _parse_shell(
                shell_info,
                endpoint=endpoint,
                shell_allocator=shell_allocator,
                path_prefix=f"AAS/Environment/AssetAdministrationShells[{index}]",
            )
            shell_entries.append(shell)
            for submodel in inline_submodels:
                inline_submodels_by_id[submodel["id"]] = submodel

    submodels_by_id: dict[str, dict[str, Any]] = {}
    submodel_folder = _find_info_by_name(child_infos, "Submodels")
    if submodel_folder is not None:
        submodel_nodes = await _get_child_infos(submodel_folder.node)
        submodel_entries = await _parse_submodels(
            submodel_nodes,
            endpoint=endpoint,
            path_prefix="AAS/Environment/Submodels",
        )
        for submodel in submodel_entries:
            submodels_by_id[submodel["id"]] = submodel

    for submodel_id, submodel in inline_submodels_by_id.items():
        submodels_by_id.setdefault(submodel_id, submodel)

    concept_descriptions: list[dict[str, Any]] = []
    concept_folder = _find_info_by_name(child_infos, "ConceptDescriptions")
    if concept_folder is not None:
        concept_nodes = await _get_child_infos(concept_folder.node)
        concept_descriptions = await _parse_concept_descriptions(
            concept_nodes,
            endpoint=endpoint,
            path_prefix="AAS/Environment/ConceptDescriptions",
        )

    if shell_entries:
        environment["assetAdministrationShells"] = shell_entries
    if submodels_by_id:
        environment["submodels"] = list(submodels_by_id.values())
    if concept_descriptions:
        environment["conceptDescriptions"] = concept_descriptions

    if environment:
        return environment

    return None


async def _scan_legacy_root(aas_root: Any, *, endpoint: str) -> dict[str, Any]:
    root_children = await _get_child_infos(aas_root)
    shell_allocator = _IdShortAllocator()

    shell_entries: list[dict[str, Any]] = []
    submodels_by_id: dict[str, dict[str, Any]] = {}
    concept_descriptions: list[dict[str, Any]] = []

    for root_index, root_child in enumerate(root_children):
        lowered = root_child.name.lower()
        if lowered in {"submodels", "unlinkedsubmodels"}:
            submodel_nodes = await _get_child_infos(root_child.node)
            submodel_entries = await _parse_submodels(
                submodel_nodes,
                endpoint=endpoint,
                path_prefix=f"AAS/{root_child.name}",
            )
            for submodel in submodel_entries:
                submodels_by_id[submodel["id"]] = submodel
            continue

        if lowered == "conceptdescriptions":
            concept_nodes = await _get_child_infos(root_child.node)
            concept_descriptions = await _parse_concept_descriptions(
                concept_nodes,
                endpoint=endpoint,
                path_prefix=f"AAS/{root_child.name}",
            )
            continue

        if root_child.node_class != ua.NodeClass.Object:
            continue

        shell, submodels = await _parse_shell(
            root_child,
            endpoint=endpoint,
            shell_allocator=shell_allocator,
            path_prefix=f"AAS/{root_child.name}[{root_index}]",
        )
        shell_entries.append(shell)
        for submodel in submodels:
            submodels_by_id[submodel["id"]] = submodel

    environment: dict[str, Any] = {}
    if shell_entries:
        environment["assetAdministrationShells"] = shell_entries
    if submodels_by_id:
        environment["submodels"] = list(submodels_by_id.values())
    if concept_descriptions:
        environment["conceptDescriptions"] = concept_descriptions

    if not environment:
        raise OPCUALoaderSpecError(
            "No AAS content was found in the OPC UA server tree."
        )

    return environment


async def _parse_shell(
    shell_info: _NodeInfo,
    *,
    endpoint: str,
    shell_allocator: _IdShortAllocator,
    path_prefix: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    shell_path = f"{path_prefix}/{shell_info.name}"

    child_infos = await _get_child_infos(shell_info.node)
    child_infos, metadata = await _extract_metadata_children(child_infos)

    shell = _model_from_metadata(metadata) or {}

    shell_id_short = _non_empty_text(shell.get("idShort"))
    if shell_id_short is None:
        shell_id_short = shell_allocator.allocate(shell_info.name)
    shell["idShort"] = shell_id_short

    shell_id = _non_empty_text(shell.get("id"))
    if shell_id is None:
        shell_id = _make_urn_uuid(
            endpoint,
            "aas-shell",
            f"{shell_path}|{shell_info.node.nodeid}",
        )
    shell["id"] = shell_id

    if metadata.category is not None:
        shell["category"] = metadata.category

    submodels: list[dict[str, Any]] = []

    legacy_submodels_folder = _find_info_by_name(child_infos, "Submodels")
    if legacy_submodels_folder is not None:
        legacy_submodel_nodes = await _get_child_infos(legacy_submodels_folder.node)
        submodels = await _parse_submodels(
            legacy_submodel_nodes,
            endpoint=endpoint,
            path_prefix=f"{shell_path}/Submodels",
        )

    submodel_references_folder = _find_info_by_name(child_infos, "SubmodelReferences")
    parsed_submodel_refs: list[dict[str, Any]] = []
    if submodel_references_folder is not None:
        parsed_submodel_refs = await _parse_reference_nodes(submodel_references_folder.node)

    if "submodels" not in shell:
        if parsed_submodel_refs:
            shell["submodels"] = parsed_submodel_refs
        elif submodels:
            shell["submodels"] = [_make_submodel_reference(sm["id"]) for sm in submodels]

    asset_information_node = _find_info_by_name(child_infos, "AssetInformation")
    if asset_information_node is not None and "assetInformation" not in shell:
        asset_information = await _parse_metadata_object(asset_information_node.node)
        if asset_information is not None:
            shell["assetInformation"] = asset_information

    if "assetInformation" not in shell:
        shell["assetInformation"] = {
            "assetKind": "Instance",
            "globalAssetId": f"urn:opcuaserver:asset:{shell_id_short}",
        }

    if "modelType" not in shell:
        shell["modelType"] = "AssetAdministrationShell"

    return shell, submodels


async def _parse_submodels(
    submodel_nodes: list[_NodeInfo],
    *,
    endpoint: str,
    path_prefix: str,
) -> list[dict[str, Any]]:
    submodels: list[dict[str, Any]] = []
    id_short_allocator = _IdShortAllocator()

    for index, submodel_info in enumerate(submodel_nodes):
        if submodel_info.node_class != ua.NodeClass.Object:
            continue

        submodel_path = f"{path_prefix}[{index}]/{submodel_info.name}"
        child_infos = await _get_child_infos(submodel_info.node)
        child_infos, metadata = await _extract_metadata_children(child_infos)

        submodel = _model_from_metadata(metadata) or {}

        has_payload = metadata.payload is not None
        if not has_payload or "submodelElements" not in submodel:
            element_infos = await _extract_submodel_element_infos(child_infos)
            submodel_elements = await _parse_infos_as_elements(
                element_infos,
                path=f"{submodel_path}/submodelElements",
            )
            if submodel_elements:
                submodel["submodelElements"] = submodel_elements

        if metadata.category is not None:
            submodel["category"] = metadata.category

        submodel_id_short = _non_empty_text(submodel.get("idShort"))
        if submodel_id_short is None:
            submodel_id_short = id_short_allocator.allocate(submodel_info.name)
        submodel["idShort"] = submodel_id_short

        submodel_id = _non_empty_text(submodel.get("id"))
        if submodel_id is None:
            submodel_id = _make_urn_uuid(
                endpoint,
                "submodel",
                f"{submodel_path}|{submodel_info.node.nodeid}",
            )
        submodel["id"] = submodel_id

        if "kind" not in submodel:
            submodel["kind"] = "Instance"
        if "modelType" not in submodel:
            submodel["modelType"] = "Submodel"

        submodels.append(submodel)

    return submodels


async def _parse_concept_descriptions(
    concept_nodes: list[_NodeInfo],
    *,
    endpoint: str,
    path_prefix: str,
) -> list[dict[str, Any]]:
    concept_descriptions: list[dict[str, Any]] = []
    id_short_allocator = _IdShortAllocator()

    for index, concept_info in enumerate(concept_nodes):
        if concept_info.node_class != ua.NodeClass.Object:
            continue

        concept_path = f"{path_prefix}[{index}]/{concept_info.name}"
        child_infos = await _get_child_infos(concept_info.node)
        _, metadata = await _extract_metadata_children(child_infos)

        concept = _model_from_metadata(metadata) or {}

        if metadata.category is not None:
            concept["category"] = metadata.category

        concept_id_short = _non_empty_text(concept.get("idShort"))
        if concept_id_short is None:
            concept_id_short = id_short_allocator.allocate(concept_info.name)
        concept["idShort"] = concept_id_short

        concept_id = _non_empty_text(concept.get("id"))
        if concept_id is None:
            concept_id = _make_urn_uuid(
                endpoint,
                "concept-description",
                f"{concept_path}|{concept_info.node.nodeid}",
            )
        concept["id"] = concept_id

        if "modelType" not in concept:
            concept["modelType"] = "ConceptDescription"

        concept_descriptions.append(concept)

    return concept_descriptions


async def _parse_reference_nodes(parent_node: Any) -> list[dict[str, Any]]:
    references: list[dict[str, Any]] = []
    child_infos = await _get_child_infos(parent_node)

    for index, child_info in enumerate(child_infos):
        if child_info.node_class != ua.NodeClass.Object:
            continue

        reference = await _parse_metadata_object(child_info.node)
        if reference is None:
            reference = _make_submodel_reference(
                _make_urn_uuid(
                    "opcuaserver",
                    "submodel-ref",
                    f"{child_info.name}|{index}|{child_info.node.nodeid}",
                )
            )
        references.append(reference)

    return references


async def _parse_metadata_object(node: Any) -> dict[str, Any] | None:
    child_infos = await _get_child_infos(node)
    _, metadata = await _extract_metadata_children(child_infos)
    return _model_from_metadata(metadata)


async def _extract_submodel_element_infos(child_infos: list[_NodeInfo]) -> list[_NodeInfo]:
    submodel_elements_folder = _find_info_by_name(child_infos, "SubmodelElements")
    if submodel_elements_folder is None:
        return child_infos
    return await _get_child_infos(submodel_elements_folder.node)


async def _parse_node_children_as_elements(
    parent_node: Any,
    *,
    path: str,
) -> list[dict[str, Any]]:
    child_infos = await _get_child_infos(parent_node)
    return await _parse_infos_as_elements(child_infos, path=path)


async def _parse_infos_as_elements(
    child_infos: list[_NodeInfo],
    *,
    path: str,
) -> list[dict[str, Any]]:
    allocator = _IdShortAllocator()
    elements: list[dict[str, Any]] = []

    for index, child_info in enumerate(child_infos):
        element = await _parse_element(
            child_info,
            path=f"{path}[{index}]",
        )
        if element is None:
            continue

        existing_id_short = _non_empty_text(element.get("idShort"))
        if existing_id_short is not None:
            element["idShort"] = existing_id_short
        else:
            element["idShort"] = allocator.allocate(child_info.name)
        elements.append(element)

    return elements


async def _parse_element(
    node_info: _NodeInfo,
    *,
    path: str,
) -> dict[str, Any] | None:
    if node_info.node_class == ua.NodeClass.Variable:
        variable_children = await _get_child_infos(node_info.node)
        _, metadata = await _extract_metadata_children(variable_children)
        payload = _model_from_metadata(metadata)
        if payload is not None:
            return payload

        parsed_property = await _parse_property(
            node_info,
            path=path,
            explicit_category=metadata.category,
        )
        return _merge_metadata(parsed_property, metadata)

    if node_info.node_class != ua.NodeClass.Object:
        return None

    child_infos = await _get_child_infos(node_info.node)
    child_infos, metadata = await _extract_metadata_children(child_infos)

    if metadata.payload is not None:
        payload = _model_from_metadata(metadata)
        if payload is not None:
            return payload

    if await _looks_like_range(child_infos):
        parsed_range = await _parse_range(
            node_info,
            child_infos,
            path=path,
            explicit_category=metadata.category,
        )
        return _merge_metadata(parsed_range, metadata)

    if _looks_like_operation(child_infos):
        parsed_operation = await _parse_operation(
            node_info,
            child_infos,
            path=path,
            explicit_category=metadata.category,
        )
        return _merge_metadata(parsed_operation, metadata)

    value = await _parse_infos_as_elements(
        child_infos,
        path=f"{path}/value",
    )

    collection: dict[str, Any] = {
        "idShort": node_info.name,
        "modelType": "SubmodelElementCollection",
    }
    if metadata.category is not None:
        collection["category"] = metadata.category
    if value:
        collection["value"] = value

    return _merge_metadata(collection, metadata)


async def _parse_property(
    node_info: _NodeInfo,
    *,
    path: str,
    explicit_category: str | None = None,
) -> dict[str, Any]:
    del path
    variant_type = await _read_variant_type(node_info.node)
    value = await _read_value(node_info.node)
    writable = await _is_writable(node_info.node)
    category = explicit_category or ("VARIABLE" if writable else "CONSTANT")

    return {
        "idShort": node_info.name,
        "category": category,
        "valueType": _variant_to_xsd(variant_type),
        "value": _value_to_aas_string(value),
        "modelType": "Property",
    }


async def _parse_range(
    node_info: _NodeInfo,
    child_infos: list[_NodeInfo],
    *,
    path: str,
    explicit_category: str | None,
) -> dict[str, Any]:
    del path
    range_item: dict[str, Any] = {
        "idShort": node_info.name,
        "modelType": "Range",
        "valueType": "xs:string",
    }

    detected_types: list[str] = []
    is_variable = False

    for child in child_infos:
        key = child.name.lower()
        if key not in {"min", "max"}:
            continue

        value = await _read_value(child.node)
        range_item[key] = _value_to_aas_string(value)

        variant_type = await _read_variant_type(child.node)
        detected_types.append(_variant_to_xsd(variant_type))

        if await _is_writable(child.node):
            is_variable = True

    if detected_types:
        if len(set(detected_types)) == 1:
            range_item["valueType"] = detected_types[0]
        else:
            range_item["valueType"] = "xs:string"

    if explicit_category:
        range_item["category"] = explicit_category
    elif is_variable:
        range_item["category"] = "VARIABLE"
    else:
        range_item["category"] = "CONSTANT"

    return range_item


async def _parse_operation(
    node_info: _NodeInfo,
    child_infos: list[_NodeInfo],
    *,
    path: str,
    explicit_category: str | None,
) -> dict[str, Any]:
    operation: dict[str, Any] = {
        "idShort": node_info.name,
        "modelType": "Operation",
    }
    if explicit_category:
        operation["category"] = explicit_category

    for child in child_infos:
        key = _OPERATION_GROUPS.get(child.name.lower())
        if key is None:
            continue

        variables = await _parse_node_children_as_elements(
            child.node,
            path=f"{path}/{child.name}",
        )
        if not variables:
            continue

        operation[key] = [{"value": item} for item in variables]

    return operation


async def _looks_like_range(child_infos: list[_NodeInfo]) -> bool:
    if not child_infos:
        return False

    names: set[str] = set()
    for child in child_infos:
        if child.node_class != ua.NodeClass.Variable:
            return False
        lowered = child.name.lower()
        if lowered not in {"min", "max"}:
            return False
        names.add(lowered)

    return bool(names)


def _looks_like_operation(child_infos: list[_NodeInfo]) -> bool:
    if not child_infos:
        return False

    for child in child_infos:
        if child.node_class != ua.NodeClass.Object:
            return False
        if child.name.lower() not in _OPERATION_GROUPS:
            return False
    return True


async def _extract_metadata_children(
    child_infos: list[_NodeInfo],
) -> tuple[list[_NodeInfo], _NodeMetadata]:
    filtered_children: list[_NodeInfo] = []
    metadata = _NodeMetadata()

    for child in child_infos:
        if not (child.node_class == ua.NodeClass.Variable and child.is_property):
            filtered_children.append(child)
            continue

        lowered = child.name.lower()
        if lowered == "category":
            if metadata.category is None:
                metadata.category = _normalize_category_value(await _read_value(child.node))
            continue

        if child.name == _LEGACY_METADATA_PAYLOAD_NAME:
            payload = _deserialize_metadata_payload(await _read_value(child.node))
            if payload is not None:
                metadata.payload = payload
            continue

        if child.name.startswith(_LEGACY_METADATA_FIELD_PREFIX):
            key = child.name[len(_LEGACY_METADATA_FIELD_PREFIX) :]
            metadata.fields[key] = _deserialize_metadata_value(await _read_value(child.node))
            continue

        metadata.fields[child.name] = _deserialize_metadata_value(await _read_value(child.node))

    return filtered_children, metadata


async def _get_child_infos(node: Any) -> list[_NodeInfo]:
    children = await node.get_children()
    infos: list[_NodeInfo] = []

    for child in children:
        try:
            node_class = await child.read_node_class()
            if node_class not in {ua.NodeClass.Object, ua.NodeClass.Variable}:
                continue
            browse_name = await child.read_browse_name()
            is_property = False
            if node_class == ua.NodeClass.Variable:
                is_property = await _is_property_node(child)
            infos.append(
                _NodeInfo(
                    node=child,
                    name=browse_name.Name,
                    node_class=node_class,
                    is_property=is_property,
                )
            )
        except Exception:
            continue

    return infos


async def _find_child_by_name(parent: Any, name: str) -> Any | None:
    for child in await parent.get_children():
        try:
            browse_name = await child.read_browse_name()
        except Exception:
            continue
        if browse_name.Name == name:
            return child
    return None


def _find_info_by_name(child_infos: list[_NodeInfo], name: str) -> _NodeInfo | None:
    for child_info in child_infos:
        if child_info.name == name:
            return child_info
    return None


async def _read_value(node: Any) -> Any:
    try:
        return await node.read_value()
    except Exception:
        return ""


async def _read_variant_type(node: Any) -> ua.VariantType:
    try:
        return await node.read_data_type_as_variant_type()
    except Exception:
        return ua.VariantType.String


async def _is_writable(node: Any) -> bool:
    try:
        access_levels = await node.get_user_access_level()
        return ua.AccessLevel.CurrentWrite in access_levels
    except Exception:
        return False


async def _is_property_node(node: Any) -> bool:
    try:
        type_definition = await node.read_type_definition()
    except Exception:
        return False

    if isinstance(type_definition, ua.NodeId):
        return type_definition.Identifier == ua.ObjectIds.PropertyType

    return False


def _model_from_metadata(metadata: _NodeMetadata) -> dict[str, Any] | None:
    model: dict[str, Any] = {}
    if isinstance(metadata.payload, dict):
        model.update(metadata.payload)
    if metadata.fields:
        model.update(metadata.fields)

    if metadata.category is not None and "category" not in model:
        model["category"] = metadata.category

    if model:
        return model
    return None


def _merge_metadata(model: dict[str, Any], metadata: _NodeMetadata) -> dict[str, Any]:
    if metadata.fields:
        model.update(metadata.fields)
    if metadata.category is not None:
        model["category"] = metadata.category
    return model


def _deserialize_metadata_payload(raw_value: Any) -> dict[str, Any] | None:
    if isinstance(raw_value, dict):
        return raw_value

    if not isinstance(raw_value, str):
        return None

    text = raw_value.strip()
    if not text:
        return None

    try:
        parsed = json.loads(text)
    except Exception:
        return None

    if isinstance(parsed, dict):
        return parsed
    return None


def _deserialize_metadata_value(raw_value: Any) -> Any:
    if not isinstance(raw_value, str):
        return raw_value

    text = raw_value.strip()
    if text.startswith("{") or text.startswith("["):
        try:
            return json.loads(text)
        except Exception:
            return raw_value

    return raw_value


def _normalize_category_value(raw_value: Any) -> str | None:
    if raw_value is None:
        return None

    text = str(raw_value).strip()
    if not text:
        return None
    return text


def _variant_to_xsd(variant_type: ua.VariantType) -> str:
    return _VARIANT_TO_XSD.get(variant_type, "xs:string")


def _value_to_aas_string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (bytes, bytearray)):
        return value.hex()
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=True, sort_keys=True)
    return str(value)


def _non_empty_text(raw_value: Any) -> str | None:
    if isinstance(raw_value, str):
        text = raw_value.strip()
        if text:
            return text
    return None


def _sanitize_id_short(name: str | None) -> str:
    text = (name or "").strip()
    if not text:
        text = "Node"

    sanitized = re.sub(r"[^A-Za-z0-9_-]", "_", text)
    if not sanitized:
        sanitized = "Node"

    if not sanitized[0].isalpha():
        sanitized = f"A{sanitized}"

    if not re.match(r".*[A-Za-z0-9_]$", sanitized):
        sanitized = sanitized.rstrip("-")
        if not sanitized:
            sanitized = "Node"
        if not re.match(r".*[A-Za-z0-9_]$", sanitized):
            sanitized = f"{sanitized}_"

    if len(sanitized) == 1:
        sanitized = f"{sanitized}_"

    if len(sanitized) > 128:
        sanitized = sanitized[:128]
        if not re.match(r".*[A-Za-z0-9_]$", sanitized):
            sanitized = f"{sanitized[:-1]}_"

    return sanitized


def _make_urn_uuid(endpoint: str, kind: str, key: str) -> str:
    namespace_seed = f"{endpoint}|{kind}|{key}"
    return f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, namespace_seed)}"


def _make_submodel_reference(submodel_id: str) -> dict[str, Any]:
    return {
        "type": "ModelReference",
        "keys": [
            {
                "type": "Submodel",
                "value": submodel_id,
            }
        ],
    }
