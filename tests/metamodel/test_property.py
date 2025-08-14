import base64
import pytest
from pydantic import ValidationError

from openaas.metamodel.property import Property, DataTypeDefXsd
from openaas.metamodel.reference import Reference
from openaas.metamodel.reference_type import ReferenceType
from openaas.metamodel.key import Key


def _ext_ref(val: str) -> Reference:
    return Reference(
        type=ReferenceType.ExternalReference,
        keys=[Key(type="GlobalReference", value=val)],
    )


# -----------------------
# Presença value/valueId
# -----------------------

def test_property_not_requires_value_or_valueid():
    property = Property(valueType=DataTypeDefXsd.string)

    assert property.valueType == DataTypeDefXsd.string


def test_property_with_valueid_only_ok():
    p = Property(valueType=DataTypeDefXsd.string, valueId=_ext_ref("0173-1#..."))
    assert p.valueId is not None and p.value is None


def test_property_with_value_and_valueid_ok():
    p = Property(valueType=DataTypeDefXsd.string, value="hello", valueId=_ext_ref("X"))
    assert p.value == "hello" and p.valueId is not None


# ------------
# string types
# ------------

def test_string_ok():
    Property(valueType=DataTypeDefXsd.string, value="anything\nok\ttoo")


def test_normalized_string_ok_and_invalid():
    Property(valueType=DataTypeDefXsd.normalizedString, value="abc DEF 123")
    with pytest.raises(ValidationError):
        Property(valueType=DataTypeDefXsd.normalizedString, value="has\nnewline")


# --------
# boolean
# --------

@pytest.mark.parametrize("val", ["true", "false", "1", "0", ""])
def test_boolean_ok(val):
    Property(valueType=DataTypeDefXsd.boolean, value=val)


@pytest.mark.parametrize("val", ["True", "yes", "2"])
def test_boolean_invalid(val):
    with pytest.raises(ValidationError):
        Property(valueType=DataTypeDefXsd.boolean, value=val)


# --------
# decimal
# --------

def test_decimal_ok_and_invalid():
    Property(valueType=DataTypeDefXsd.decimal, value="123.456")
    with pytest.raises(ValidationError):
        Property(valueType=DataTypeDefXsd.decimal, value="12.34.56")


# -------------
# float/double
# -------------

@pytest.mark.parametrize("dtype,val", [
    (DataTypeDefXsd.float, "1.0"),
    (DataTypeDefXsd.double, "1e-3"),
])
def test_float_double_ok(dtype, val):
    Property(valueType=dtype, value=val)


@pytest.mark.parametrize("dtype,val", [
    (DataTypeDefXsd.float, "abc"),
    (DataTypeDefXsd.double, "1,2"),
])
def test_float_double_invalid(dtype, val):
    with pytest.raises(ValidationError):
        Property(valueType=dtype, value=val)


# --------------
# integer ranges
# --------------

@pytest.mark.parametrize("dtype,good,bad", [
    (DataTypeDefXsd.byte, "127", "128"),
    (DataTypeDefXsd.short, "32767", "32768"),
    (DataTypeDefXsd.int, "2147483647", "2147483648"),
    (DataTypeDefXsd.long, "9223372036854775807", "9223372036854775808"),
    (DataTypeDefXsd.unsignedByte, "255", "256"),
    (DataTypeDefXsd.unsignedShort, "65535", "65536"),
    (DataTypeDefXsd.unsignedInt, "4294967295", "4294967296"),
    (DataTypeDefXsd.unsignedLong, "18446744073709551615", "18446744073709551616"),
])
def test_integer_ranges(dtype, good, bad):
    Property(valueType=dtype, value=good)
    with pytest.raises(ValidationError):
        Property(valueType=dtype, value=bad)


@pytest.mark.parametrize("dtype,val,msg", [
    (DataTypeDefXsd.nonPositiveInteger, "0", None),
    (DataTypeDefXsd.nonPositiveInteger, "1", "deve ser <= 0"),
    (DataTypeDefXsd.negativeInteger, "-1", None),
    (DataTypeDefXsd.negativeInteger, "0", "deve ser < 0"),
    (DataTypeDefXsd.nonNegativeInteger, "0", None),
    (DataTypeDefXsd.nonNegativeInteger, "-1", "deve ser >= 0"),
    (DataTypeDefXsd.positiveInteger, "1", None),
    (DataTypeDefXsd.positiveInteger, "0", "deve ser > 0"),
])
def test_integer_sign_classes(dtype, val, msg):
    if msg is None:
        Property(valueType=dtype, value=val)
    else:
        with pytest.raises(ValidationError) as exc:
            Property(valueType=dtype, value=val)
        assert msg in str(exc.value)


# -----
# date
# -----

def test_date_ok_and_invalid():
    Property(valueType=DataTypeDefXsd.date, value="2024-02-29")   # bissexto ok
    with pytest.raises(ValidationError):
        Property(valueType=DataTypeDefXsd.date, value="2024-02-30")


# -----
# time
# -----

@pytest.mark.parametrize("val", ["12:34", "23:59:59", "12:34:56Z", "12:34:56+03:00"])
def test_time_ok(val):
    Property(valueType=DataTypeDefXsd.time, value=val)


@pytest.mark.parametrize("val", ["24:00", "12:60:00", "12:34:56+0300"])
def test_time_invalid(val):
    with pytest.raises(ValidationError):
        Property(valueType=DataTypeDefXsd.time, value=val)


# ---------
# dateTime
# ---------

def test_datetime_ok_and_invalid():
    Property(valueType=DataTypeDefXsd.dateTime, value="2024-05-01T13:20:30Z")
    with pytest.raises(ValidationError):
        Property(valueType=DataTypeDefXsd.dateTime, value="2024-13-01T00:00:00")


# -------
# anyURI
# -------

def test_anyuri_ok_and_invalid():
    Property(valueType=DataTypeDefXsd.anyURI, value="http://example.com/x")
    Property(valueType=DataTypeDefXsd.anyURI, value="/relative/path")  # aceita relativo


# -------------
# base64Binary
# -------------

def test_base64_ok_and_invalid():
    blob = base64.b64encode(b"hello").decode()
    Property(valueType=DataTypeDefXsd.base64Binary, value=blob)
    with pytest.raises(ValidationError):
        Property(valueType=DataTypeDefXsd.base64Binary, value="@@@not-base64")


# ----------
# hexBinary
# ----------

@pytest.mark.parametrize("val", ["", "00", "DEADBEEF", "deadBEEF01"])
def test_hex_ok(val):
    Property(valueType=DataTypeDefXsd.hexBinary, value=val)


@pytest.mark.parametrize("val", ["A", "XYZ", "123", "0xFF"])
def test_hex_invalid(val):
    with pytest.raises(ValidationError):
        Property(valueType=DataTypeDefXsd.hexBinary, value=val)
