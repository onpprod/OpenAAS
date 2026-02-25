"""OpenOPC: constrói estruturas OPC UA a partir de arquivos JSON."""

from .builder import (
    OpenOPCSpecError,
    build_server_from_json,
    create_server_from_json,
    load_json_spec,
    populate_from_dict,
)

__all__ = [
    "build_server_from_json",
    "create_server_from_json",
    "load_json_spec",
    "OpenOPCSpecError",
    "populate_from_dict",
    "__version__",
]

__version__ = "0.1.0"
