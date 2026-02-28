"""AAS metamodel enumeration."""

from __future__ import annotations

from enum import Enum


class QualifierKind(str, Enum):
    """Enumeration for QualifierKind.

    Constraints:
    - Allowed values are fixed by aas.json definition `QualifierKind`.
    """
    ConceptQualifier = 'ConceptQualifier'
    TemplateQualifier = 'TemplateQualifier'
    ValueQualifier = 'ValueQualifier'
