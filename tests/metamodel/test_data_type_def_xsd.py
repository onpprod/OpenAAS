import pytest

from openaas.metamodel.property import DataTypeDefXsd


def test_enum_members_exist():
    # spot-check de membros principais
    assert DataTypeDefXsd.string.value == "string"
    assert DataTypeDefXsd.boolean.value == "boolean"
    assert DataTypeDefXsd.decimal.value == "decimal"
    assert DataTypeDefXsd.float.value == "float"
    assert DataTypeDefXsd.double.value == "double"
    assert DataTypeDefXsd.int.value == "int"
    assert DataTypeDefXsd.date.value == "date"
    assert DataTypeDefXsd.dateTime.value == "dateTime"
    assert DataTypeDefXsd.time.value == "time"
    assert DataTypeDefXsd.anyURI.value == "anyURI"
    assert DataTypeDefXsd.base64Binary.value == "base64Binary"
    assert DataTypeDefXsd.hexBinary.value == "hexBinary"


def test_unique_values():
    # todos os valores do Enum são únicos
    vals = [m.value for m in DataTypeDefXsd]
    assert len(vals) == len(set(vals))
