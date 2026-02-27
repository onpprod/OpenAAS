"""aasmodel package exposing Pydantic AAS metamodel classes."""

from . import models as _models
from .models import *  # noqa: F401,F403
from .schema_validation import AASSchemaValidationError, validate_against_aas_schema

__all__ = [
    *_models.__all__,
    "AASSchemaValidationError",
    "validate_against_aas_schema",
    "__version__",
]

__version__ = "0.1.0"

