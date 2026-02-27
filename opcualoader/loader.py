"""Load AAS JSON from an OPC UA server produced by opcuaserver."""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass
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


@dataclass
class _NodeInfo:
    node: Any
    name: str
    node_class: ua.NodeClass


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

    root_children = await _get_child_infos(aas_root)
    shell_allocator = _IdShortAllocator()

    shell_entries: list[dict[str, Any]] = []
    submodels_by_id: dict[str, dict[str, Any]] = {}

    for root_child in root_children:
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

        if root_child.node_class != ua.NodeClass.Object:
            continue

        shell, submodels = await _parse_shell(
            root_child,
            endpoint=endpoint,
            shell_allocator=shell_allocator,
        )
        shell_entries.append(shell)
        for submodel in submodels:
            submodels_by_id[submodel["id"]] = submodel

    environment: dict[str, Any] = {}
    if shell_entries:
        environment["assetAdministrationShells"] = shell_entries
    if submodels_by_id:
        environment["submodels"] = list(submodels_by_id.values())

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
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    shell_path = f"AAS/{shell_info.name}"
    shell_id_short = shell_allocator.allocate(shell_info.name)
    shell_id = _make_urn_uuid(endpoint, "aas-shell", f"{shell_path}|{shell_info.node.nodeid}")

    submodels_folder = await _find_child_by_name(shell_info.node, "Submodels")
    submodels: list[dict[str, Any]] = []
    submodel_refs: list[dict[str, Any]] = []

    if submodels_folder is not None:
        submodel_nodes = await _get_child_infos(submodels_folder)
        submodels = await _parse_submodels(
            submodel_nodes,
            endpoint=endpoint,
            path_prefix=f"{shell_path}/Submodels",
        )
        for submodel in submodels:
            submodel_refs.append(_make_submodel_reference(submodel["id"]))

    shell: dict[str, Any] = {
        "idShort": shell_id_short,
        "id": shell_id,
        "assetInformation": {
            "assetKind": "Instance",
            "globalAssetId": f"urn:opcuaserver:asset:{shell_id_short}",
        },
        "modelType": "AssetAdministrationShell",
    }
    if submodel_refs:
        shell["submodels"] = submodel_refs

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
        submodel_elements = await _parse_node_children_as_elements(
            submodel_info.node,
            path=f"{submodel_path}/submodelElements",
        )

        submodel: dict[str, Any] = {
            "idShort": id_short_allocator.allocate(submodel_info.name),
            "id": _make_urn_uuid(
                endpoint,
                "submodel",
                f"{submodel_path}|{submodel_info.node.nodeid}",
            ),
            "kind": "Instance",
            "modelType": "Submodel",
        }
        if submodel_elements:
            submodel["submodelElements"] = submodel_elements

        submodels.append(submodel)

    return submodels


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

        element["idShort"] = allocator.allocate(element.get("idShort"))
        elements.append(element)

    return elements


async def _parse_element(
    node_info: _NodeInfo,
    *,
    path: str,
) -> dict[str, Any] | None:
    if node_info.node_class == ua.NodeClass.Variable:
        return await _parse_property(node_info, path=path)

    if node_info.node_class != ua.NodeClass.Object:
        return None

    child_infos = await _get_child_infos(node_info.node)

    if await _looks_like_range(child_infos):
        return await _parse_range(node_info, child_infos, path=path)

    if _looks_like_operation(child_infos):
        return await _parse_operation(node_info, child_infos, path=path)

    value = await _parse_infos_as_elements(
        child_infos,
        path=f"{path}/value",
    )

    collection: dict[str, Any] = {
        "idShort": node_info.name,
        "modelType": "SubmodelElementCollection",
    }
    if value:
        collection["value"] = value
    return collection


async def _parse_property(
    node_info: _NodeInfo,
    *,
    path: str,
) -> dict[str, Any]:
    variant_type = await _read_variant_type(node_info.node)
    value = await _read_value(node_info.node)
    writable = await _is_writable(node_info.node)

    return {
        "idShort": node_info.name,
        "category": "VARIABLE" if writable else "CONSTANT",
        "valueType": _variant_to_xsd(variant_type),
        "value": _value_to_aas_string(value),
        "modelType": "Property",
    }


async def _parse_range(
    node_info: _NodeInfo,
    child_infos: list[_NodeInfo],
    *,
    path: str,
) -> dict[str, Any]:
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

    if is_variable:
        range_item["category"] = "VARIABLE"
    else:
        range_item["category"] = "CONSTANT"

    return range_item


async def _parse_operation(
    node_info: _NodeInfo,
    child_infos: list[_NodeInfo],
    *,
    path: str,
) -> dict[str, Any]:
    operation: dict[str, Any] = {
        "idShort": node_info.name,
        "modelType": "Operation",
    }

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


async def _get_child_infos(node: Any) -> list[_NodeInfo]:
    children = await node.get_children()
    infos: list[_NodeInfo] = []

    for child in children:
        try:
            node_class = await child.read_node_class()
            if node_class not in {ua.NodeClass.Object, ua.NodeClass.Variable}:
                continue
            browse_name = await child.read_browse_name()
            infos.append(_NodeInfo(node=child, name=browse_name.Name, node_class=node_class))
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
