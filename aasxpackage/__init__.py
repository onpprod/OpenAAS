"""Create AASX package files compatible with AAS Part 5 conventions."""

from .builder import create_aasx_from_environment, create_aasx_from_json
from .errors import AASXPackageError, AASXPackageSpecError, AASXPackageValidationError

__all__ = [
    "create_aasx_from_json",
    "create_aasx_from_environment",
    "AASXPackageError",
    "AASXPackageSpecError",
    "AASXPackageValidationError",
    "__version__",
]

__version__ = "0.1.0"
