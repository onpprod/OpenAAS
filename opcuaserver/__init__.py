"""Open OPC UA Server from AAS JSON package."""

from .builder import (
    DEFAULT_ENDPOINT,
    DEFAULT_NAMESPACE_URI,
    DEFAULT_SERVER_NAME,
    build_server_from_aas_json,
    create_server_from_aas_dict,
    create_server_from_aas_json,
    populate_from_aas_dict,
)
from .errors import OPCUASchemaValidationError, OPCUAServerError, OPCUASpecError
from .validation import load_aas_environment, validate_aas_environment

__all__ = [
    "DEFAULT_ENDPOINT",
    "DEFAULT_SERVER_NAME",
    "DEFAULT_NAMESPACE_URI",
    "build_server_from_aas_json",
    "create_server_from_aas_json",
    "create_server_from_aas_dict",
    "populate_from_aas_dict",
    "load_aas_environment",
    "validate_aas_environment",
    "OPCUAServerError",
    "OPCUASpecError",
    "OPCUASchemaValidationError",
    "__version__",
]

__version__ = "0.1.0"
