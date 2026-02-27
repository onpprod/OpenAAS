"""AAS metamodel enumeration."""

from __future__ import annotations

from enum import Enum


class DataTypeIec61360(str, Enum):
    """Enumeration for DataTypeIec61360.

    Constraints:
    - Allowed values are fixed by aas.json definition `DataTypeIec61360`.
    """
    BLOB = 'BLOB'
    BOOLEAN = 'BOOLEAN'
    DATE = 'DATE'
    FILE = 'FILE'
    HTML = 'HTML'
    INTEGER_COUNT = 'INTEGER_COUNT'
    INTEGER_CURRENCY = 'INTEGER_CURRENCY'
    INTEGER_MEASURE = 'INTEGER_MEASURE'
    IRDI = 'IRDI'
    IRI = 'IRI'
    RATIONAL = 'RATIONAL'
    RATIONAL_MEASURE = 'RATIONAL_MEASURE'
    REAL_COUNT = 'REAL_COUNT'
    REAL_CURRENCY = 'REAL_CURRENCY'
    REAL_MEASURE = 'REAL_MEASURE'
    STRING = 'STRING'
    STRING_TRANSLATABLE = 'STRING_TRANSLATABLE'
    TIME = 'TIME'
    TIMESTAMP = 'TIMESTAMP'
