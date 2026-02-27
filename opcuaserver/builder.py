"""Build OPC UA servers from AAS environment JSON."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Any

from asyncua import Server, ua
from asyncua.crypto.permission_rules import User, UserRole

from .errors import OPCUASpecError
from .history_storage import MongoHistoryStorage, SafeHistoryDict, SafeHistorySQLite
from .validation import load_aas_environment, validate_aas_environment

DEFAULT_ENDPOINT = "opc.tcp://0.0.0.0:4841/opcuaserver/server/"
DEFAULT_SERVER_NAME = "OPCUAServer"
DEFAULT_NAMESPACE_URI = "http://opcuaserver.local/aas"
DEFAULT_HISTORY_SQLITE_FILE = "history.db"
DEFAULT_HISTORY_MONGODB_DATABASE = "opcuaserver_history"
DEFAULT_HISTORY_MONGODB_COLLECTION = "datachanges"

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
    "assetInformation",
    "submodels",
    "conceptDescriptions",
}

_OPERATION_VARIABLE_GROUPS = {
    "inputVariables": "InputVariables",
    "outputVariables": "OutputVariables",
    "inoutputVariables": "InOutputVariables",
}


@dataclass(frozen=True)
class _HistoryOptions:
    enabled: bool = False
    period: timedelta | None = None
    count: int = 0

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
    historize_variables: bool = False,
    history_backend: str = "memory",
    history_period: timedelta | None = None,
    history_count: int = 0,
    history_sqlite_file: str | Path = DEFAULT_HISTORY_SQLITE_FILE,
    history_mongodb_uri: str | None = None,
    history_mongodb_database: str = DEFAULT_HISTORY_MONGODB_DATABASE,
    history_mongodb_collection: str = DEFAULT_HISTORY_MONGODB_COLLECTION,
    history_mongodb_username: str | None = None,
    history_mongodb_password: str | None = None,
    history_mongodb_auth_source: str | None = None,
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
        historize_variables=historize_variables,
        history_backend=history_backend,
        history_period=history_period,
        history_count=history_count,
        history_sqlite_file=history_sqlite_file,
        history_mongodb_uri=history_mongodb_uri,
        history_mongodb_database=history_mongodb_database,
        history_mongodb_collection=history_mongodb_collection,
        history_mongodb_username=history_mongodb_username,
        history_mongodb_password=history_mongodb_password,
        history_mongodb_auth_source=history_mongodb_auth_source,
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
    historize_variables: bool = False,
    history_backend: str = "memory",
    history_period: timedelta | None = None,
    history_count: int = 0,
    history_sqlite_file: str | Path = DEFAULT_HISTORY_SQLITE_FILE,
    history_mongodb_uri: str | None = None,
    history_mongodb_database: str = DEFAULT_HISTORY_MONGODB_DATABASE,
    history_mongodb_collection: str = DEFAULT_HISTORY_MONGODB_COLLECTION,
    history_mongodb_username: str | None = None,
    history_mongodb_password: str | None = None,
    history_mongodb_auth_source: str | None = None,
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
        historize_variables=historize_variables,
        history_backend=history_backend,
        history_period=history_period,
        history_count=history_count,
        history_sqlite_file=history_sqlite_file,
        history_mongodb_uri=history_mongodb_uri,
        history_mongodb_database=history_mongodb_database,
        history_mongodb_collection=history_mongodb_collection,
        history_mongodb_username=history_mongodb_username,
        history_mongodb_password=history_mongodb_password,
        history_mongodb_auth_source=history_mongodb_auth_source,
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
    historize_variables: bool = False,
    history_backend: str = "memory",
    history_period: timedelta | None = None,
    history_count: int = 0,
    history_sqlite_file: str | Path = DEFAULT_HISTORY_SQLITE_FILE,
    history_mongodb_uri: str | None = None,
    history_mongodb_database: str = DEFAULT_HISTORY_MONGODB_DATABASE,
    history_mongodb_collection: str = DEFAULT_HISTORY_MONGODB_COLLECTION,
    history_mongodb_username: str | None = None,
    history_mongodb_password: str | None = None,
    history_mongodb_auth_source: str | None = None,
) -> Server:
    """Create and configure an OPC UA server from an AAS dictionary."""
    validate_aas_environment(aas_environment)

    server = Server()
    history_options = await _configure_server(
        server,
        endpoint=endpoint,
        server_name=server_name,
        username=username,
        password=password,
        allow_anonymous=allow_anonymous,
        historize_variables=historize_variables,
        history_backend=history_backend,
        history_period=history_period,
        history_count=history_count,
        history_sqlite_file=history_sqlite_file,
        history_mongodb_uri=history_mongodb_uri,
        history_mongodb_database=history_mongodb_database,
        history_mongodb_collection=history_mongodb_collection,
        history_mongodb_username=history_mongodb_username,
        history_mongodb_password=history_mongodb_password,
        history_mongodb_auth_source=history_mongodb_auth_source,
    )
    await populate_from_aas_dict(
        server,
        aas_environment,
        namespace_uri=namespace_uri,
        validate_schema=False,
        historize_variables=history_options.enabled,
        history_period=history_options.period,
        history_count=history_options.count,
    )
    return server


async def populate_from_aas_dict(
    server: Server,
    aas_environment: dict[str, Any],
    *,
    namespace_uri: str = DEFAULT_NAMESPACE_URI,
    schema_path: str | Path | None = None,
    validate_schema: bool = True,
    historize_variables: bool = False,
    history_period: timedelta | None = None,
    history_count: int = 0,
) -> int:
    """Populate an initialized OPC UA server from an AAS dictionary."""
    if not isinstance(aas_environment, dict):
        raise OPCUASpecError("AAS environment must be a dictionary.")

    if validate_schema:
        validate_aas_environment(aas_environment, schema_path=schema_path)

    history_options = _HistoryOptions(
        enabled=historize_variables,
        period=history_period,
        count=history_count,
    )

    namespace_idx = await server.register_namespace(namespace_uri)
    allocator = _BrowseNameAllocator()

    root = await _add_folder(server.nodes.objects, namespace_idx, "AAS", allocator)
    environment_node = await _add_object(root, namespace_idx, "Environment", allocator)

    shells = _ensure_list(
        aas_environment.get("assetAdministrationShells"),
        "assetAdministrationShells",
    )
    submodels = _ensure_list(aas_environment.get("submodels"), "submodels")
    concept_descriptions = _ensure_list(
        aas_environment.get("conceptDescriptions"),
        "conceptDescriptions",
    )

    await _add_model_metadata(
        environment_node,
        namespace_idx,
        aas_environment,
        path="AAS/Environment",
        skip_keys={"assetAdministrationShells", "submodels", "conceptDescriptions"},
    )

    shells_folder = await _add_folder(
        environment_node,
        namespace_idx,
        "AssetAdministrationShells",
        allocator,
    )
    for shell_index, shell in enumerate(shells):
        if not isinstance(shell, dict):
            raise OPCUASpecError(
                f"assetAdministrationShells[{shell_index}] must be an object."
            )
        await _add_shell(
            server,
            shells_folder,
            shell,
            namespace_idx,
            allocator,
            history_options=history_options,
            path=f"AAS/Environment/AssetAdministrationShells[{shell_index}]",
        )

    submodels_folder = await _add_folder(
        environment_node,
        namespace_idx,
        "Submodels",
        allocator,
    )
    for submodel_index, submodel in enumerate(submodels):
        if not isinstance(submodel, dict):
            raise OPCUASpecError(f"submodels[{submodel_index}] must be an object.")
        await _add_submodel(
            server,
            submodels_folder,
            submodel,
            namespace_idx,
            allocator,
            history_options=history_options,
            path=f"AAS/Environment/Submodels[{submodel_index}]",
        )

    concept_descriptions_folder = await _add_folder(
        environment_node,
        namespace_idx,
        "ConceptDescriptions",
        allocator,
    )
    for concept_index, concept_description in enumerate(concept_descriptions):
        if not isinstance(concept_description, dict):
            raise OPCUASpecError(
                f"conceptDescriptions[{concept_index}] must be an object."
            )
        await _add_concept_description(
            concept_descriptions_folder,
            concept_description,
            namespace_idx,
            allocator,
            path=f"AAS/Environment/ConceptDescriptions[{concept_index}]",
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
    historize_variables: bool,
    history_backend: str,
    history_period: timedelta | None,
    history_count: int,
    history_sqlite_file: str | Path,
    history_mongodb_uri: str | None,
    history_mongodb_database: str,
    history_mongodb_collection: str,
    history_mongodb_username: str | None,
    history_mongodb_password: str | None,
    history_mongodb_auth_source: str | None,
) -> _HistoryOptions:
    history_options = _configure_history_storage(
        server,
        historize_variables=historize_variables,
        history_backend=history_backend,
        history_period=history_period,
        history_count=history_count,
        history_sqlite_file=history_sqlite_file,
        history_mongodb_uri=history_mongodb_uri,
        history_mongodb_database=history_mongodb_database,
        history_mongodb_collection=history_mongodb_collection,
        history_mongodb_username=history_mongodb_username,
        history_mongodb_password=history_mongodb_password,
        history_mongodb_auth_source=history_mongodb_auth_source,
    )

    await server.init()
    server.set_endpoint(endpoint)
    server.set_server_name(server_name)
    _configure_authentication(
        server,
        username=username,
        password=password,
        allow_anonymous=allow_anonymous,
    )
    return history_options


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


def _configure_history_storage(
    server: Server,
    *,
    historize_variables: bool,
    history_backend: str,
    history_period: timedelta | None,
    history_count: int,
    history_sqlite_file: str | Path,
    history_mongodb_uri: str | None,
    history_mongodb_database: str,
    history_mongodb_collection: str,
    history_mongodb_username: str | None,
    history_mongodb_password: str | None,
    history_mongodb_auth_source: str | None,
) -> _HistoryOptions:
    if not historize_variables:
        return _HistoryOptions()

    if history_count < 0:
        raise OPCUASpecError("history_count must be greater than or equal to zero.")

    backend = _normalize_history_backend(history_backend)
    if backend == "memory":
        server.iserver.history_manager.set_storage(SafeHistoryDict())
        return _HistoryOptions(enabled=True, period=history_period, count=history_count)

    if backend == "sqlite":
        sqlite_path = _resolve_history_sqlite_path(history_sqlite_file)
        server.iserver.history_manager.set_storage(
            SafeHistorySQLite(path=str(sqlite_path))
        )
        return _HistoryOptions(enabled=True, period=history_period, count=history_count)

    if backend == "mongodb":
        uri = _non_empty_text(history_mongodb_uri)
        if uri is None:
            raise OPCUASpecError(
                "history_mongodb_uri must be provided when history_backend is mongodb."
            )
        if (history_mongodb_username is None) != (history_mongodb_password is None):
            raise OPCUASpecError(
                "history_mongodb_username and history_mongodb_password must be provided together."
            )
        server.iserver.history_manager.set_storage(
            MongoHistoryStorage(
                uri=uri,
                database=history_mongodb_database,
                collection=history_mongodb_collection,
                username=history_mongodb_username,
                password=history_mongodb_password,
                auth_source=history_mongodb_auth_source,
            )
        )
        return _HistoryOptions(enabled=True, period=history_period, count=history_count)

    raise OPCUASpecError(
        f"Unsupported history backend '{history_backend}'. "
        "Use one of: memory, sqlite, mongodb."
    )


def _normalize_history_backend(history_backend: str) -> str:
    backend = (history_backend or "").strip().lower()
    if backend in {"memory", "ram"}:
        return "memory"
    if backend in {"sqlite", "sqlite3"}:
        return "sqlite"
    if backend in {"mongodb", "mongo"}:
        return "mongodb"
    raise OPCUASpecError(
        f"Unsupported history backend '{history_backend}'. "
        "Use one of: memory, sqlite, mongodb."
    )


def _resolve_history_sqlite_path(path: str | Path) -> Path:
    sqlite_path = Path(path)
    if not sqlite_path.is_absolute():
        sqlite_path = Path.cwd() / sqlite_path
    sqlite_path = sqlite_path.resolve()
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite_path


async def _add_shell(
    server: Server,
    parent: Any,
    shell: dict[str, Any],
    namespace_idx: int,
    allocator: _BrowseNameAllocator,
    *,
    history_options: _HistoryOptions,
    path: str,
) -> None:
    del server
    del history_options
    shell_name = _display_name(
        shell,
        fallback=_non_empty_text(shell.get("id")) or "AssetAdministrationShell",
    )
    shell_node = await _add_object(parent, namespace_idx, shell_name, allocator)

    await _add_category_property(shell_node, namespace_idx, shell)
    await _add_model_metadata(
        shell_node,
        namespace_idx,
        shell,
        path=path,
        skip_keys={"assetInformation", "submodels"},
    )

    asset_information = shell.get("assetInformation")
    if asset_information is not None:
        if not isinstance(asset_information, dict):
            raise OPCUASpecError(f"{path}.assetInformation must be an object.")
        asset_information_node = await _add_object(
            shell_node,
            namespace_idx,
            "AssetInformation",
            allocator,
        )
        await _add_model_metadata(
            asset_information_node,
            namespace_idx,
            asset_information,
            path=f"{path}.assetInformation",
        )

    submodel_references = _ensure_list(shell.get("submodels"), f"{path}.submodels")
    if submodel_references:
        references_node = await _add_folder(
            shell_node,
            namespace_idx,
            "SubmodelReferences",
            allocator,
        )
        for reference_index, reference in enumerate(submodel_references):
            if not isinstance(reference, dict):
                raise OPCUASpecError(
                    f"{path}.submodels[{reference_index}] must be an object."
                )
            reference_name = _reference_display_name(reference, reference_index)
            reference_node = await _add_object(
                references_node,
                namespace_idx,
                reference_name,
                allocator,
            )
            await _add_model_metadata(
                reference_node,
                namespace_idx,
                reference,
                path=f"{path}.submodels[{reference_index}]",
            )


async def _add_submodel(
    server: Server,
    parent: Any,
    submodel: dict[str, Any],
    namespace_idx: int,
    allocator: _BrowseNameAllocator,
    *,
    history_options: _HistoryOptions,
    path: str,
) -> None:
    submodel_name = _display_name(
        submodel,
        fallback=_non_empty_text(submodel.get("id")) or "Submodel",
    )
    submodel_node = await _add_object(parent, namespace_idx, submodel_name, allocator)

    await _add_category_property(submodel_node, namespace_idx, submodel)
    await _add_model_metadata(
        submodel_node,
        namespace_idx,
        submodel,
        path=path,
        skip_keys={"submodelElements"},
    )

    elements_folder = await _add_folder(
        submodel_node,
        namespace_idx,
        "SubmodelElements",
        allocator,
    )

    elements = _ensure_list(submodel.get("submodelElements"), f"{path}.submodelElements")
    for index, element in enumerate(elements):
        await _add_submodel_element(
            server,
            elements_folder,
            element,
            namespace_idx,
            allocator,
            history_options=history_options,
            path=f"{path}.submodelElements[{index}]",
        )


async def _add_concept_description(
    parent: Any,
    concept_description: dict[str, Any],
    namespace_idx: int,
    allocator: _BrowseNameAllocator,
    *,
    path: str,
) -> None:
    concept_name = _display_name(
        concept_description,
        fallback=_non_empty_text(concept_description.get("id")) or "ConceptDescription",
    )
    concept_node = await _add_object(parent, namespace_idx, concept_name, allocator)
    await _add_category_property(concept_node, namespace_idx, concept_description)
    await _add_model_metadata(
        concept_node,
        namespace_idx,
        concept_description,
        path=path,
    )


async def _add_submodel_element(
    server: Server,
    parent: Any,
    element: Any,
    namespace_idx: int,
    allocator: _BrowseNameAllocator,
    *,
    history_options: _HistoryOptions,
    path: str,
) -> None:
    if not isinstance(element, dict):
        raise OPCUASpecError(f"{path} must be an object.")

    model_type = _non_empty_text(element.get("modelType")) or "SubmodelElement"
    element_name = _display_name(element, fallback=model_type)

    if model_type == "Operation":
        await _add_operation_element(
            server,
            parent,
            element,
            namespace_idx,
            allocator,
            history_options=history_options,
            path=path,
            element_name=element_name,
        )
        return

    if model_type == "Range":
        await _add_range_element(
            server,
            parent,
            element,
            namespace_idx,
            allocator,
            history_options=history_options,
            path=path,
            element_name=element_name,
        )
        return

    if _is_simple_value_element(element):
        await _add_value_element(
            server,
            parent,
            element,
            namespace_idx,
            allocator,
            history_options=history_options,
            path=path,
            element_name=element_name,
        )
        return

    object_node = await _add_object(parent, namespace_idx, element_name, allocator)
    child_elements = _extract_child_elements(element, path)
    if child_elements:
        for index, child in enumerate(child_elements):
            await _add_submodel_element(
                server,
                object_node,
                child,
                namespace_idx,
                allocator,
                history_options=history_options,
                path=f"{path}.children[{index}]",
            )
    else:
        await _add_scalar_metadata_variables(
            server,
            object_node,
            element,
            namespace_idx,
            allocator,
            history_options=history_options,
            path=path,
            writable=_is_writable(element),
        )

    await _add_category_property(object_node, namespace_idx, element)
    await _add_model_metadata(
        object_node,
        namespace_idx,
        element,
        path=path,
        skip_keys=_submodel_element_metadata_skip_keys(element),
    )


async def _add_operation_element(
    server: Server,
    parent: Any,
    element: dict[str, Any],
    namespace_idx: int,
    allocator: _BrowseNameAllocator,
    *,
    history_options: _HistoryOptions,
    path: str,
    element_name: str,
) -> None:
    operation_node = await _add_object(parent, namespace_idx, element_name, allocator)

    for key, group_name in _OPERATION_VARIABLE_GROUPS.items():
        variables = _ensure_list(element.get(key), f"{path}.{key}")
        if not variables:
            continue

        group_node = await _add_folder(
            operation_node,
            namespace_idx,
            group_name,
            allocator,
        )
        for index, operation_variable in enumerate(variables):
            if not isinstance(operation_variable, dict):
                raise OPCUASpecError(f"{path}.{key}[{index}] must be an object.")

            value_element = operation_variable.get("value")
            if isinstance(value_element, dict):
                await _add_submodel_element(
                    server,
                    group_node,
                    value_element,
                    namespace_idx,
                    allocator,
                    history_options=history_options,
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
    await _add_model_metadata(
        operation_node,
        namespace_idx,
        element,
        path=path,
        skip_keys=set(_OPERATION_VARIABLE_GROUPS),
    )


async def _add_range_element(
    server: Server,
    parent: Any,
    element: dict[str, Any],
    namespace_idx: int,
    allocator: _BrowseNameAllocator,
    *,
    history_options: _HistoryOptions,
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
            await _maybe_enable_history(server, variable, history_options)

    await _add_category_property(range_node, namespace_idx, element)
    await _add_model_metadata(
        range_node,
        namespace_idx,
        element,
        path=path,
        skip_keys={"min", "max"},
    )


async def _add_value_element(
    server: Server,
    parent: Any,
    element: dict[str, Any],
    namespace_idx: int,
    allocator: _BrowseNameAllocator,
    *,
    history_options: _HistoryOptions,
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
    await _add_model_metadata(
        variable,
        namespace_idx,
        element,
        path=path,
    )

    if _is_writable(element):
        await variable.set_writable()
        await _maybe_enable_history(server, variable, history_options)


async def _add_scalar_metadata_variables(
    server: Server,
    parent: Any,
    element: dict[str, Any],
    namespace_idx: int,
    allocator: _BrowseNameAllocator,
    *,
    history_options: _HistoryOptions,
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
            await _maybe_enable_history(server, variable, history_options)


async def _add_category_property(
    node: Any,
    namespace_idx: int,
    element: dict[str, Any],
) -> None:
    category = _non_empty_text(element.get("category"))
    if not category:
        return

    await _add_property(
        node,
        namespace_idx,
        "category",
        category,
        ua.VariantType.String,
    )


async def _add_model_metadata(
    node: Any,
    namespace_idx: int,
    data: dict[str, Any],
    *,
    path: str,
    skip_keys: set[str] | None = None,
) -> None:
    if not isinstance(data, dict):
        return

    skipped = set(skip_keys or set())
    skipped.add("category")
    for key, value in data.items():
        if key in skipped or value is None:
            continue
        await _add_metadata_property(
            node,
            namespace_idx,
            key,
            value,
            path=f"{path}.{key}",
        )


async def _add_metadata_property(
    node: Any,
    namespace_idx: int,
    name: str,
    value: Any,
    *,
    path: str,
) -> None:
    raw_value = _serialize_complex_value(value)
    variant_type = _resolve_variant_type(None, raw_value, path)
    coerced_value = _coerce_value(raw_value, variant_type, path)
    await _add_property(node, namespace_idx, name, coerced_value, variant_type)


async def _add_property(
    node: Any,
    namespace_idx: int,
    name: str,
    value: Any,
    variant_type: ua.VariantType,
) -> None:
    try:
        await node.add_property(namespace_idx, name, value, variant_type)
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


def _submodel_element_metadata_skip_keys(element: dict[str, Any]) -> set[str]:
    model_type = _non_empty_text(element.get("modelType")) or ""
    if model_type == "Operation":
        return set(_OPERATION_VARIABLE_GROUPS)
    if model_type == "Range":
        return {"min", "max"}

    skip_keys = {"submodelElements", "statements", "annotations"}
    if _contains_submodel_elements(element.get("value")):
        skip_keys.add("value")
    return skip_keys


def _ensure_list(raw_value: Any, field_path: str) -> list[Any]:
    if raw_value is None:
        return []
    if not isinstance(raw_value, list):
        raise OPCUASpecError(f"Field '{field_path}' must be a list.")
    return raw_value


async def _maybe_enable_history(
    server: Server,
    variable_node: Any,
    history_options: _HistoryOptions,
) -> None:
    if not history_options.enabled:
        return

    await server.historize_node_data_change(
        variable_node,
        period=history_options.period,
        count=history_options.count,
    )


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


def _reference_display_name(reference: dict[str, Any], index: int) -> str:
    keys = reference.get("keys")
    if isinstance(keys, list):
        for key in reversed(keys):
            if not isinstance(key, dict):
                continue
            key_value = _non_empty_text(key.get("value"))
            if key_value:
                return _normalize_node_name(key_value)
    return f"Reference_{index + 1}"


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
