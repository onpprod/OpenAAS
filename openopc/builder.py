"""Builder para criar estruturas OPC UA a partir de JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from asyncua import Server, ua

DEFAULT_ENDPOINT = "opc.tcp://0.0.0.0:4840/openopc/server/"
DEFAULT_SERVER_NAME = "OpenOPC Server"
DEFAULT_NAMESPACE_URI = "http://openopc.local"


class OpenOPCSpecError(ValueError):
    """Erro de validação no JSON usado para criar a estrutura OPC UA."""


_DATATYPE_MAP: dict[str, ua.VariantType] = {
    "boolean": ua.VariantType.Boolean,
    "bool": ua.VariantType.Boolean,
    "byte": ua.VariantType.Byte,
    "sbyte": ua.VariantType.SByte,
    "int16": ua.VariantType.Int16,
    "short": ua.VariantType.Int16,
    "uint16": ua.VariantType.UInt16,
    "int32": ua.VariantType.Int32,
    "int": ua.VariantType.Int32,
    "integer": ua.VariantType.Int32,
    "uint32": ua.VariantType.UInt32,
    "int64": ua.VariantType.Int64,
    "long": ua.VariantType.Int64,
    "uint64": ua.VariantType.UInt64,
    "float": ua.VariantType.Float,
    "double": ua.VariantType.Double,
    "string": ua.VariantType.String,
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


def load_json_spec(json_path: str | Path) -> dict[str, Any]:
    """Carrega um arquivo JSON e retorna o dicionário da especificação."""
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo JSON não encontrado: {path}")

    with path.open("r", encoding="utf-8") as fp:
        spec = json.load(fp)

    if not isinstance(spec, dict):
        raise OpenOPCSpecError("O JSON deve ter um objeto (dict) na raiz.")

    return spec


async def create_server_from_json(json_path: str | Path) -> Server:
    """Cria e configura um servidor OPC UA com base no arquivo JSON."""
    spec = load_json_spec(json_path)
    server = Server()

    server_spec = spec.get("server", {})
    await _configure_server(server, server_spec)
    await populate_from_dict(server, spec)

    return server


async def build_server_from_json(json_path: str | Path) -> Server:
    """Alias para create_server_from_json."""
    return await create_server_from_json(json_path)


async def populate_from_dict(server: Server, spec: dict[str, Any]) -> int:
    """Popula um servidor OPC UA já inicializado a partir de um dicionário."""
    if not isinstance(spec, dict):
        raise OpenOPCSpecError("A especificação deve ser um dict.")

    server_spec = spec.get("server", {})
    if server_spec is None:
        server_spec = {}

    if not isinstance(server_spec, dict):
        raise OpenOPCSpecError("O campo 'server' deve ser um objeto JSON.")

    namespace_uri = str(server_spec.get("namespace_uri", DEFAULT_NAMESPACE_URI))
    namespace_idx = await server.register_namespace(namespace_uri)

    nodes = spec.get("nodes", [])
    if not isinstance(nodes, list):
        raise OpenOPCSpecError("O campo 'nodes' deve ser uma lista.")

    for index, node_spec in enumerate(nodes):
        await _add_node(
            parent=server.nodes.objects,
            node_spec=node_spec,
            namespace_idx=namespace_idx,
            path=f"nodes[{index}]",
        )

    return namespace_idx


async def _configure_server(server: Server, server_spec: dict[str, Any]) -> None:
    if not isinstance(server_spec, dict):
        raise OpenOPCSpecError("O campo 'server' deve ser um objeto JSON.")

    await server.init()

    endpoint = str(server_spec.get("endpoint", DEFAULT_ENDPOINT))
    server_name = str(server_spec.get("name", DEFAULT_SERVER_NAME))

    server.set_endpoint(endpoint)
    server.set_server_name(server_name)


async def _add_node(
    parent: Any,
    node_spec: dict[str, Any],
    namespace_idx: int,
    path: str,
) -> None:
    if not isinstance(node_spec, dict):
        raise OpenOPCSpecError(f"{path}: cada nó deve ser um objeto JSON.")

    node_type = _required_nonempty_str(node_spec, "type", path).lower()
    name = _required_nonempty_str(node_spec, "name", path)

    if node_type == "folder":
        folder = await parent.add_folder(namespace_idx, name)
        await _add_children(folder, node_spec, namespace_idx, path)
        return

    if node_type == "object":
        obj = await parent.add_object(namespace_idx, name)
        await _add_children(obj, node_spec, namespace_idx, path)
        return

    if node_type == "variable":
        datatype = _required_nonempty_str(node_spec, "datatype", path)
        variant_type = _resolve_variant_type(datatype, path)
        value = _coerce_value(node_spec.get("value"), variant_type, path)

        variable = await parent.add_variable(namespace_idx, name, value, variant_type)

        writable = node_spec.get("writable", False)
        if not isinstance(writable, bool):
            raise OpenOPCSpecError(f"{path}.writable: deve ser true ou false.")

        if writable:
            await variable.set_writable()
        return

    raise OpenOPCSpecError(
        f"{path}.type: tipo '{node_type}' inválido. Use 'folder', 'object' ou 'variable'."
    )


async def _add_children(parent: Any, node_spec: dict[str, Any], namespace_idx: int, path: str) -> None:
    children = node_spec.get("children", [])
    if children is None:
        children = []

    if not isinstance(children, list):
        raise OpenOPCSpecError(f"{path}.children: deve ser uma lista.")

    for idx, child in enumerate(children):
        await _add_node(
            parent=parent,
            node_spec=child,
            namespace_idx=namespace_idx,
            path=f"{path}.children[{idx}]",
        )


def _required_nonempty_str(data: dict[str, Any], key: str, path: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise OpenOPCSpecError(f"{path}.{key}: valor obrigatório e deve ser string não vazia.")
    return value.strip()


def _resolve_variant_type(datatype: str, path: str) -> ua.VariantType:
    variant_type = _DATATYPE_MAP.get(datatype.strip().lower())
    if variant_type is None:
        supported = ", ".join(sorted(set(_DATATYPE_MAP.keys())))
        raise OpenOPCSpecError(
            f"{path}.datatype: '{datatype}' não é suportado. Tipos aceitos: {supported}."
        )
    return variant_type


def _coerce_value(value: Any, variant_type: ua.VariantType, path: str) -> Any:
    try:
        if variant_type in _INT_VARIANTS:
            if isinstance(value, bool):
                raise TypeError
            return int(value)

        if variant_type in _FLOAT_VARIANTS:
            return float(value)

        if variant_type == ua.VariantType.Boolean:
            if isinstance(value, bool):
                return value

            if isinstance(value, str):
                normalized = value.strip().lower()
                if normalized in {"1", "true", "yes", "sim"}:
                    return True
                if normalized in {"0", "false", "no", "nao", "não"}:
                    return False

            if isinstance(value, (int, float)):
                return bool(value)

            raise TypeError

        if variant_type == ua.VariantType.String:
            return "" if value is None else str(value)

        return value

    except (TypeError, ValueError) as exc:
        raise OpenOPCSpecError(
            f"{path}.value: valor '{value}' inválido para datatype '{variant_type.name}'."
        ) from exc
