"""Build OPC UA servers from AAS environment JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from asyncua import Server, ua
from asyncua.crypto.permission_rules import User, UserRole

from .errors import OPCUASpecError
from .validation import load_aas_environment, validate_aas_environment

DEFAULT_ENDPOINT = "opc.tcp://0.0.0.0:4841/opcuaserver/server/"
DEFAULT_SERVER_NAME = "OPCUAServer"
DEFAULT_NAMESPACE_URI = "http://opcuaserver.local/aas"

_XSD_TO_VARIANT_TYPE: dict[str, ua.VariantType] = {
    "xs:anyURI": ua.VariantType.String,
    "xs:base64Binary": ua.VariantType.String,
    "xs:boolean": ua.VariantType.Boolean,
    "xs:byte": ua.VariantType.SByte,
    "xs:date": ua.VariantType.String,
    "xs:dateTime": ua.VariantType.String,
    "xs:decimal": ua.VariantType.Double,
    "xs:double": ua.VariantType.Double,
    "xs:duration": ua.VariantType.String,
    "xs:float": ua.VariantType.Float,
    "xs:gDay": ua.VariantType.String,
    "xs:gMonth": ua.VariantType.String,
    "xs:gMonthDay": ua.VariantType.String,
    "xs:gYear": ua.VariantType.String,
    "xs:gYearMonth": ua.VariantType.String,
    "xs:hexBinary": ua.VariantType.String,
    "xs:int": ua.VariantType.Int32,
    "xs:integer": ua.VariantType.Int64,
    "xs:long": ua.VariantType.Int64,
    "xs:negativeInteger": ua.VariantType.Int64,
    "xs:nonNegativeInteger": ua.VariantType.UInt64,
    "xs:nonPositiveInteger": ua.VariantType.Int64,
    "xs:positiveInteger": ua.VariantType.UInt64,
    "xs:short": ua.VariantType.Int16,
    "xs:string": ua.VariantType.String,
    "xs:time": ua.VariantType.String,
    "xs:unsignedByte": ua.VariantType.Byte,
    "xs:unsignedInt": ua.VariantType.UInt32,
    "xs:unsignedLong": ua.VariantType.UInt64,
    "xs:unsignedShort": ua.VariantType.UInt16,
}

_INT_VARIANTS = {
    ua.VariantType.Byte,
    ua.VariantType.SByte,
    ua.VariantType.Int16,
    ua.VariantType.UInt16,
    ua.VariantType.Int32,
    ua.VariantType.UInt32,
    ua.VariantType.Int64,
    ua.VariantType.UInt64,
}

_FLOAT_VARIANTS = {
    ua.VariantType.Float,
    ua.VariantType.Double,
}

_STRUCTURAL_KEYS = {
    "idShort",
    "modelType",
    "category",
    "value",
    "valueType",
    "submodelElements",
    "statements",
    "annotations",
    "inputVariables",
    "outputVariables",
    "inoutputVariables",
    "min",
    "max",
}

_OPERATION_VARIABLE_GROUPS = {
    "inputVariables": "InputVariables",
    "outputVariables": "OutputVariables",
    "inoutputVariables": "InOutputVariables",
}


class _StaticUserManager:
    """Simple static username/password manager for asyncua server."""

    def __init__(self, username: str, password: str) -> None:
        self._username = username
        self._password = password

    def get_user(
        self,
        iserver: Any,
        username: str | None = None,
        password: str | None = None,
        certificate: Any | None = None,
    ) -> User | None:
        del iserver
        del certificate
        if username == self._username and password == self._password:
            return User(role=UserRole.User, name=username)
        return None


class _BrowseNameAllocator:
    def __init__(self) -> None:
        self._used_by_parent: dict[str, set[str]] = {}

    def next_name(self, parent: Any, preferred_name: str) -> str:
        key = str(getattr(parent, "nodeid", id(parent)))
        used = self._used_by_parent.setdefault(key, set())
        base_name = _normalize_node_name(preferred_name)
        name = base_name
        suffix = 2
        while name in used:
            name = f"{base_name}_{suffix}"
            suffix += 1
        used.add(name)
        return name


async def create_server_from_aas_json(
    json_path: str | Path,
    *,
    schema_path: str | Path | None = None,
    endpoint: str = DEFAULT_ENDPOINT,
    server_name: str = DEFAULT_SERVER_NAME,
    namespace_uri: str = DEFAULT_NAMESPACE_URI,
    username: str | None = None,
    password: str | None = None,
    allow_anonymous: bool | None = None,
) -> Server:
    """Create and configure an OPC UA server from an AAS JSON file."""
    aas_environment = load_aas_environment(json_path, schema_path=schema_path)
    return await create_server_from_aas_dict(
        aas_environment,
        endpoint=endpoint,
        server_name=server_name,
        namespace_uri=namespace_uri,
        username=username,
        password=password,
        allow_anonymous=allow_anonymous,
    )


async def build_server_from_aas_json(
    json_path: str | Path,
    *,
    schema_path: str | Path | None = None,
    endpoint: str = DEFAULT_ENDPOINT,
    server_name: str = DEFAULT_SERVER_NAME,
    namespace_uri: str = DEFAULT_NAMESPACE_URI,
    username: str | None = None,
    password: str | None = None,
    allow_anonymous: bool | None = None,
) -> Server:
    """Alias for create_server_from_aas_json."""
    return await create_server_from_aas_json(
        json_path,
        schema_path=schema_path,
        endpoint=endpoint,
        server_name=server_name,
        namespace_uri=namespace_uri,
        username=username,
        password=password,
        allow_anonymous=allow_anonymous,
    )


async def create_server_from_aas_dict(
    aas_environment: dict[str, Any],
    *,
    endpoint: str = DEFAULT_ENDPOINT,
    server_name: str = DEFAULT_SERVER_NAME,
    namespace_uri: str = DEFAULT_NAMESPACE_URI,
    username: str | None = None,
    password: str | None = None,
    allow_anonymous: bool | None = None,
) -> Server:
    """Create and configure an OPC UA server from an AAS dictionary."""
    validate_aas_environment(aas_environment)

    server = Server()
    await _configure_server(
        server,
        endpoint=endpoint,
        server_name=server_name,
        username=username,
        password=password,
        allow_anonymous=allow_anonymous,
    )
    await populate_from_aas_dict(
        server,
        aas_environment,
        namespace_uri=namespace_uri,
        validate_schema=False,
    )
    return server


async def populate_from_aas_dict(
    server: Server,
    aas_environment: dict[str, Any],
    *,
    namespace_uri: str = DEFAULT_NAMESPACE_URI,
    schema_path: str | Path | None = None,
    validate_schema: bool = True,
) -> int:
    """Populate an initialized OPC UA server from an AAS dictionary."""
    if not isinstance(aas_environment, dict):
        raise OPCUASpecError("AAS environment must be a dictionary.")

    if validate_schema:
        validate_aas_environment(aas_environment, schema_path=schema_path)

    namespace_idx = await server.register_namespace(namespace_uri)
    allocator = _BrowseNameAllocator()

    root = await _add_folder(server.nodes.objects, namespace_idx, "AAS", allocator)
    submodels_by_id = _index_submodels(aas_environment)

    linked_submodel_ids: set[str] = set()
    shells = aas_environment.get("assetAdministrationShells") or []
    if not isinstance(shells, list):
        raise OPCUASpecError("Field 'assetAdministrationShells' must be a list.")

    for shell_index, shell in enumerate(shells):
        if not isinstance(shell, dict):
            raise OPCUASpecError(
                f"assetAdministrationShells[{shell_index}] must be an object."
            )

        shell_name = _display_name(shell, fallback=f"AAS_{shell_index + 1}")
        shell_node = await _add_object(root, namespace_idx, shell_name, allocator)
        submodel_folder = await _add_folder(
            shell_node, namespace_idx, "Submodels", allocator
        )

        submodel_ids = _extract_submodel_ids_from_shell(shell)
        for submodel_id in submodel_ids:
            submodel = submodels_by_id.get(submodel_id)
            if submodel is None:
                continue
            linked_submodel_ids.add(submodel_id)
            await _add_submodel(
                submodel_folder,
                submodel,
                namespace_idx,
                allocator,
                path=f"AAS/{shell_name}/Submodels/{submodel_id}",
            )

    if shells:
        unlinked_submodels = [
            submodel
            for submodel_id, submodel in submodels_by_id.items()
            if submodel_id not in linked_submodel_ids
        ]
        if unlinked_submodels:
            orphan_folder = await _add_folder(
                root, namespace_idx, "UnlinkedSubmodels", allocator
            )
            for idx, submodel in enumerate(unlinked_submodels):
                await _add_submodel(
                    orphan_folder,
                    submodel,
                    namespace_idx,
                    allocator,
                    path=f"AAS/UnlinkedSubmodels[{idx}]",
                )
    else:
        submodel_folder = await _add_folder(root, namespace_idx, "Submodels", allocator)
        for idx, submodel in enumerate(submodels_by_id.values()):
            await _add_submodel(
                submodel_folder,
                submodel,
                namespace_idx,
                allocator,
                path=f"AAS/Submodels[{idx}]",
            )

    return namespace_idx


async def _configure_server(
    server: Server,
    *,
    endpoint: str,
    server_name: str,
    username: str | None,
    password: str | None,
    allow_anonymous: bool | None,
) -> None:
    await server.init()
    server.set_endpoint(endpoint)
    server.set_server_name(server_name)
    _configure_authentication(
        server,
        username=username,
        password=password,
        allow_anonymous=allow_anonymous,
    )


def _configure_authentication(
    server: Server,
    *,
    username: str | None,
    password: str | None,
    allow_anonymous: bool | None,
) -> None:
    if (username is None) != (password is None):
        raise OPCUASpecError("Username and password must be provided together.")

    if username is None:
        if allow_anonymous is False:
            raise OPCUASpecError(
                "allow_anonymous=false requires username and password."
            )
        server.set_identity_tokens([ua.AnonymousIdentityToken])
        return

    if allow_anonymous is None:
        allow_anonymous = False

    tokens = [ua.UserNameIdentityToken]
    if allow_anonymous:
        tokens.insert(0, ua.AnonymousIdentityToken)

    server.set_identity_tokens(tokens)
    server.iserver.set_user_manager(_StaticUserManager(username, password))


def _index_submodels(aas_environment: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw_submodels = aas_environment.get("submodels") or []
    if not isinstance(raw_submodels, list):
        raise OPCUASpecError("Field 'submodels' must be a list.")

    submodels_by_id: dict[str, dict[str, Any]] = {}
    for index, submodel in enumerate(raw_submodels):
        if not isinstance(submodel, dict):
            raise OPCUASpecError(f"submodels[{index}] must be an object.")

        submodel_id = _non_empty_text(submodel.get("id")) or f"submodel_{index + 1}"
        if submodel_id in submodels_by_id:
            raise OPCUASpecError(
                f"Duplicate submodel id detected: '{submodel_id}'."
            )
        submodels_by_id[submodel_id] = submodel

    return submodels_by_id


def _extract_submodel_ids_from_shell(shell: dict[str, Any]) -> list[str]:
    references = shell.get("submodels") or []
    if not isinstance(references, list):
        raise OPCUASpecError("AAS field 'submodels' must be a list.")

    submodel_ids: list[str] = []
    seen: set[str] = set()

    for reference in references:
        if not isinstance(reference, dict):
            continue

        keys = reference.get("keys") or []
        if not isinstance(keys, list):
            continue

        ref_submodel_id: str | None = None
        for key in reversed(keys):
            if not isinstance(key, dict):
                continue
            key_type = _non_empty_text(key.get("type"))
            key_value = _non_empty_text(key.get("value"))
            if key_type and key_type.lower() == "submodel" and key_value:
                ref_submodel_id = key_value
                break

        if ref_submodel_id and ref_submodel_id not in seen:
            seen.add(ref_submodel_id)
            submodel_ids.append(ref_submodel_id)

    return submodel_ids


async def _add_submodel(
    parent: Any,
    submodel: dict[str, Any],
    namespace_idx: int,
    allocator: _BrowseNameAllocator,
    *,
    path: str,
) -> None:
    submodel_name = _display_name(
        submodel, fallback=_non_empty_text(submodel.get("id")) or "Submodel"
    )
    submodel_node = await _add_object(parent, namespace_idx, submodel_name, allocator)

    elements = submodel.get("submodelElements") or []
    if not isinstance(elements, list):
        raise OPCUASpecError(f"{path}.submodelElements must be a list.")

    for index, element in enumerate(elements):
        await _add_submodel_element(
            submodel_node,
            element,
            namespace_idx,
            allocator,
            path=f"{path}.submodelElements[{index}]",
        )

    await _add_category_property(submodel_node, namespace_idx, submodel)


async def _add_submodel_element(
    parent: Any,
    element: Any,
    namespace_idx: int,
    allocator: _BrowseNameAllocator,
    *,
    path: str,
) -> None:
    if not isinstance(element, dict):
        raise OPCUASpecError(f"{path} must be an object.")

    model_type = _non_empty_text(element.get("modelType")) or "SubmodelElement"
    element_name = _display_name(element, fallback=model_type)

    if model_type == "Operation":
        await _add_operation_element(
            parent,
            element,
            namespace_idx,
            allocator,
            path=path,
            element_name=element_name,
        )
        return

    if model_type == "Range":
        await _add_range_element(
            parent,
            element,
            namespace_idx,
            allocator,
            path=path,
            element_name=element_name,
        )
        return

    if _is_simple_value_element(element):
        await _add_value_element(
            parent,
            element,
            namespace_idx,
            allocator,
            path=path,
            element_name=element_name,
        )
        return

    object_node = await _add_object(parent, namespace_idx, element_name, allocator)
    child_elements = _extract_child_elements(element, path)
    if child_elements:
        for index, child in enumerate(child_elements):
            await _add_submodel_element(
                object_node,
                child,
                namespace_idx,
                allocator,
                path=f"{path}.children[{index}]",
            )
    else:
        await _add_scalar_metadata_variables(
            object_node,
            element,
            namespace_idx,
            allocator,
            path=path,
            writable=_is_writable(element),
        )

    await _add_category_property(object_node, namespace_idx, element)


async def _add_operation_element(
    parent: Any,
    element: dict[str, Any],
    namespace_idx: int,
    allocator: _BrowseNameAllocator,
    *,
    path: str,
    element_name: str,
) -> None:
    operation_node = await _add_object(parent, namespace_idx, element_name, allocator)

    for key, group_name in _OPERATION_VARIABLE_GROUPS.items():
        variables = element.get(key) or []
        if not isinstance(variables, list):
            raise OPCUASpecError(f"{path}.{key} must be a list.")
        if not variables:
            continue

        group_node = await _add_folder(operation_node, namespace_idx, group_name, allocator)
        for index, operation_variable in enumerate(variables):
            if not isinstance(operation_variable, dict):
                raise OPCUASpecError(f"{path}.{key}[{index}] must be an object.")

            value_element = operation_variable.get("value")
            if isinstance(value_element, dict):
                await _add_submodel_element(
                    group_node,
                    value_element,
                    namespace_idx,
                    allocator,
                    path=f"{path}.{key}[{index}].value",
                )
                continue

            raw_value = _serialize_complex_value(value_element)
            await _add_variable(
                group_node,
                namespace_idx,
                f"arg_{index + 1}",
                _coerce_value(raw_value, ua.VariantType.String, path),
                ua.VariantType.String,
                allocator,
            )

    await _add_category_property(operation_node, namespace_idx, element)


async def _add_range_element(
    parent: Any,
    element: dict[str, Any],
    namespace_idx: int,
    allocator: _BrowseNameAllocator,
    *,
    path: str,
    element_name: str,
) -> None:
    range_node = await _add_object(parent, namespace_idx, element_name, allocator)
    writable = _is_writable(element)
    value_type = _non_empty_text(element.get("valueType"))

    for boundary_key in ("min", "max"):
        if boundary_key not in element:
            continue

        raw_value = _serialize_complex_value(element.get(boundary_key))
        variant_type = _resolve_variant_type(value_type, raw_value, path)
        coerced_value = _coerce_value(raw_value, variant_type, path)
        variable = await _add_variable(
            range_node,
            namespace_idx,
            boundary_key,
            coerced_value,
            variant_type,
            allocator,
        )
        if writable:
            await variable.set_writable()

    await _add_category_property(range_node, namespace_idx, element)


async def _add_value_element(
    parent: Any,
    element: dict[str, Any],
    namespace_idx: int,
    allocator: _BrowseNameAllocator,
    *,
    path: str,
    element_name: str,
) -> None:
    value_type = _non_empty_text(element.get("valueType"))
    raw_value = _serialize_complex_value(element.get("value"))
    variant_type = _resolve_variant_type(value_type, raw_value, path)
    coerced_value = _coerce_value(raw_value, variant_type, path)
    variable = await _add_variable(
        parent,
        namespace_idx,
        element_name,
        coerced_value,
        variant_type,
        allocator,
    )
    await _add_category_property(variable, namespace_idx, element)

    if _is_writable(element):
        await variable.set_writable()


async def _add_scalar_metadata_variables(
    parent: Any,
    element: dict[str, Any],
    namespace_idx: int,
    allocator: _BrowseNameAllocator,
    *,
    path: str,
    writable: bool,
) -> None:
    for key, value in element.items():
        if key in _STRUCTURAL_KEYS:
            continue
        if value is None:
            continue

        raw_value = _serialize_complex_value(value)
        variant_type = _resolve_variant_type(None, raw_value, f"{path}.{key}")
        coerced_value = _coerce_value(raw_value, variant_type, f"{path}.{key}")

        variable = await _add_variable(
            parent,
            namespace_idx,
            key,
            coerced_value,
            variant_type,
            allocator,
        )
        if writable:
            await variable.set_writable()


async def _add_category_property(
    node: Any,
    namespace_idx: int,
    element: dict[str, Any],
) -> None:
    category = _non_empty_text(element.get("category"))
    if not category:
        return

    try:
        await node.add_property(namespace_idx, "category", category, ua.VariantType.String)
    except Exception as exc:
        if _is_duplicate_browse_name_error(exc):
            return
        raise


def _extract_child_elements(element: dict[str, Any], path: str) -> list[dict[str, Any]]:
    child_elements: list[dict[str, Any]] = []

    for key in ("submodelElements", "statements", "annotations"):
        raw_children = element.get(key)
        if raw_children is None:
            continue
        if not isinstance(raw_children, list):
            raise OPCUASpecError(f"{path}.{key} must be a list.")
        for index, raw_child in enumerate(raw_children):
            if not isinstance(raw_child, dict):
                raise OPCUASpecError(f"{path}.{key}[{index}] must be an object.")
            child_elements.append(raw_child)

    raw_value = element.get("value")
    if _contains_submodel_elements(raw_value):
        for index, raw_child in enumerate(raw_value):
            if not isinstance(raw_child, dict):
                raise OPCUASpecError(f"{path}.value[{index}] must be an object.")
            child_elements.append(raw_child)

    return child_elements


def _contains_submodel_elements(raw_value: Any) -> bool:
    if not isinstance(raw_value, list) or not raw_value:
        return False
    return all(isinstance(item, dict) and "modelType" in item for item in raw_value)


def _is_simple_value_element(element: dict[str, Any]) -> bool:
    if "value" not in element:
        return False

    model_type = _non_empty_text(element.get("modelType")) or ""
    if model_type in {"SubmodelElementCollection", "SubmodelElementList"}:
        return False

    return not _contains_submodel_elements(element.get("value"))


def _is_writable(element: dict[str, Any]) -> bool:
    category = _non_empty_text(element.get("category"))
    return bool(category and category.upper() == "VARIABLE")


def _resolve_variant_type(
    value_type: str | None,
    value: Any,
    path: str,
) -> ua.VariantType:
    if value_type:
        variant_type = _XSD_TO_VARIANT_TYPE.get(value_type)
        if variant_type is None:
            supported_types = ", ".join(sorted(_XSD_TO_VARIANT_TYPE))
            raise OPCUASpecError(
                f"{path}.valueType '{value_type}' is not supported. "
                f"Supported types: {supported_types}."
            )
        return variant_type

    if isinstance(value, bool):
        return ua.VariantType.Boolean
    if isinstance(value, int) and not isinstance(value, bool):
        return ua.VariantType.Int64
    if isinstance(value, float):
        return ua.VariantType.Double
    return ua.VariantType.String


def _serialize_complex_value(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=True, sort_keys=True)
    return value


def _coerce_value(value: Any, variant_type: ua.VariantType, path: str) -> Any:
    try:
        if variant_type in _INT_VARIANTS:
            if value is None:
                return 0
            if isinstance(value, bool):
                raise TypeError
            if isinstance(value, str) and not value.strip():
                return 0
            return int(value)

        if variant_type in _FLOAT_VARIANTS:
            if value is None:
                return 0.0
            if isinstance(value, str) and not value.strip():
                return 0.0
            return float(value)

        if variant_type == ua.VariantType.Boolean:
            if value is None:
                return False
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                normalized = value.strip().lower()
                if normalized in {"1", "true", "yes", "sim"}:
                    return True
                if normalized in {"0", "false", "no", "nao"}:
                    return False
            if isinstance(value, (int, float)):
                return bool(value)
            raise TypeError

        if variant_type == ua.VariantType.String:
            if value is None:
                return ""
            return str(value)

        return value
    except (TypeError, ValueError) as exc:
        raise OPCUASpecError(
            f"{path}: value '{value}' is invalid for OPC UA type '{variant_type.name}'."
        ) from exc


async def _add_folder(
    parent: Any,
    namespace_idx: int,
    name: str,
    allocator: _BrowseNameAllocator,
) -> Any:
    for _ in range(1000):
        browse_name = allocator.next_name(parent, name)
        try:
            return await parent.add_folder(namespace_idx, browse_name)
        except Exception as exc:
            if not _is_duplicate_browse_name_error(exc):
                raise
    raise OPCUASpecError(
        f"Could not allocate unique browse name for folder '{name}'."
    )


async def _add_object(
    parent: Any,
    namespace_idx: int,
    name: str,
    allocator: _BrowseNameAllocator,
) -> Any:
    for _ in range(1000):
        browse_name = allocator.next_name(parent, name)
        try:
            return await parent.add_object(namespace_idx, browse_name)
        except Exception as exc:
            if not _is_duplicate_browse_name_error(exc):
                raise
    raise OPCUASpecError(
        f"Could not allocate unique browse name for object '{name}'."
    )


async def _add_variable(
    parent: Any,
    namespace_idx: int,
    name: str,
    value: Any,
    variant_type: ua.VariantType,
    allocator: _BrowseNameAllocator,
) -> Any:
    for _ in range(1000):
        browse_name = allocator.next_name(parent, name)
        try:
            return await parent.add_variable(
                namespace_idx, browse_name, value, variant_type
            )
        except Exception as exc:
            if not _is_duplicate_browse_name_error(exc):
                raise
    raise OPCUASpecError(
        f"Could not allocate unique browse name for variable '{name}'."
    )


def _display_name(data: dict[str, Any], *, fallback: str) -> str:
    id_short = _non_empty_text(data.get("idShort"))
    if id_short:
        return id_short
    return _normalize_node_name(fallback)


def _normalize_node_name(name: Any) -> str:
    if isinstance(name, str):
        text = name.strip()
    elif name is None:
        text = ""
    else:
        text = str(name).strip()

    if not text:
        return "Node"
    return text


def _non_empty_text(value: Any) -> str | None:
    if isinstance(value, str):
        text = value.strip()
        if text:
            return text
    return None


def _is_duplicate_browse_name_error(exc: Exception) -> bool:
    message = str(exc)
    return "BadBrowseNameDuplicated" in message
