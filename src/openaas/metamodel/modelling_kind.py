from enum import Enum


class ModellingKind(str, Enum):
    """Enum de 'kind' (Template/Instance)."""
    Template = "Template"
    Instance = "Instance"