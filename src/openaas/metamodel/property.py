# openaas/metamodel/property.py
from __future__ import annotations

from enum import Enum
from decimal import Decimal, InvalidOperation
from typing import Optional
import base64
import binascii
import datetime as dt
import re
from urllib.parse import urlparse

from pydantic import BaseModel, Field, model_validator, model_serializer, SerializationInfo
from pydantic import SerializerFunctionWrapHandler

from openaas.metamodel.submodel_element import SubmodelElement
from openaas.metamodel.reference import Reference


class DataTypeDefXsd(str, Enum):
    string = "string"
    normalizedString = "normalizedString"
    boolean = "boolean"
    decimal = "decimal"
    float = "float"
    double = "double"
    byte = "byte"
    short = "short"
    int = "int"
    long = "long"
    unsignedByte = "unsignedByte"
    unsignedShort = "unsignedShort"
    unsignedInt = "unsignedInt"
    unsignedLong = "unsignedLong"
    nonPositiveInteger = "nonPositiveInteger"
    negativeInteger = "negativeInteger"
    nonNegativeInteger = "nonNegativeInteger"
    positiveInteger = "positiveInteger"
    date = "date"
    dateTime = "dateTime"
    time = "time"
    anyURI = "anyURI"
    base64Binary = "base64Binary"
    hexBinary = "hexBinary"


class Property(SubmodelElement):
    """Propriedade com valor atômico e validação por `valueType`.

    Rule:
        - `valueType` define o domínio do `value`.

    Tips:
        Para converter automaticamente o `value` para o tipo Python ao fazer dump,
        use `model_dump(context={"typed_values": True})` (ou `model_dump_json(...)`).
    """
    valueType: DataTypeDefXsd
    value: Optional[str] = Field(default=None, description="Valor literal coerente com valueType.")
    valueId: Optional[Reference] = Field(default=None, description="Referência a valor codificado.")

    # ---------------------------
    # Validação cross-field
    # ---------------------------
    @model_validator(mode="after")
    def _validate_value_and_type(self) -> "Property":
        if self.value:
            _validate_xsd_value(self.valueType, self.value)
        return self

    # ---------------------------
    # Serialização tipada (opt-in)
    # ---------------------------
    @model_serializer(mode="wrap")
    def _serialize_typed(
        self,
        handler: SerializerFunctionWrapHandler,
        info: SerializationInfo,
    ):
        """Converte `value` para o tipo Python quando `typed_values=True` no contexto."""
        data = handler(self)
        ctx = info.context or {}
        if not (ctx.get("typed_values") or ctx.get("coerce_values")):
            return data

        raw = data.get("value", None)
        if raw not in (None, ""):
            data["value"] = _coerce_for_dump(self.valueType, str(raw))
        return data


# ========================
# Helpers de validação XSD
# ========================

_INT_RANGES = {
    DataTypeDefXsd.byte: (-128, 127),
    DataTypeDefXsd.short: (-32768, 32767),
    DataTypeDefXsd.int: (-2147483648, 2147483647),
    DataTypeDefXsd.long: (-(2**63), 2**63 - 1),
    DataTypeDefXsd.unsignedByte: (0, 255),
    DataTypeDefXsd.unsignedShort: (0, 65535),
    DataTypeDefXsd.unsignedInt: (0, 4294967295),
    DataTypeDefXsd.unsignedLong: (0, 18446744073709551615),
}

_HEX_RE = re.compile(r"^[0-9A-Fa-f]*$")  # comprimento par (inclui vazio)
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# time: HH:MM[:SS[.frac]][Z|±HH:MM]
_TIME_NAMED_RE = re.compile(
    r"^(?P<h>\d{2}):(?P<m>\d{2})"
    r"(?::(?P<s>\d{2})(?:\.(?P<f>\d{1,9}))?)?"
    r"(?:(?P<z>Z)|(?P<sign>[+\-])(?P<tzh>\d{2}):(?P<tzm>\d{2}))?$"
)

# dateTime: YYYY-MM-DDThh:mm[:ss[.frac]][Z|±HH:MM]
_DT_NAMED_RE = re.compile(
    r"^(?P<Y>\d{4})-(?P<M>\d{2})-(?P<D>\d{2})T"
    r"(?P<h>\d{2}):(?P<m>\d{2})(?::(?P<s>\d{2})(?:\.(?P<f>\d{1,9}))?)?"
    r"(?:(?P<z>Z)|(?P<sign>[+\-])(?P<tzh>\d{2}):(?P<tzm>\d{2}))?$"
)


def _validate_xsd_value(dtype: DataTypeDefXsd, value: str) -> None:
    """Lança ValueError se `value` não for coerente com `dtype`."""
    if dtype is DataTypeDefXsd.string:
        return
    if dtype is DataTypeDefXsd.normalizedString:
        if any(c in value for c in ("\r", "\n", "\t")):
            raise ValueError("normalizedString não pode conter CR/LF/TAB.")
        return
    if dtype is DataTypeDefXsd.boolean:
        if value not in ("true", "false", "1", "0", ""):
            raise ValueError("boolean deve ser 'true'/'false' ou '1'/'0'.")
        return
    if dtype is DataTypeDefXsd.decimal:
        try:
            Decimal(value)
        except (InvalidOperation, ValueError):
            raise ValueError("decimal inválido.")
        return
    if dtype in (DataTypeDefXsd.float, DataTypeDefXsd.double):
        try:
            float(value)
        except ValueError:
            raise ValueError(f"{dtype.value} inválido.")
        return
    if dtype in _INT_RANGES:
        try:
            iv = int(value)
        except ValueError:
            raise ValueError(f"{dtype.value} deve ser inteiro.")
        lo, hi = _INT_RANGES[dtype]
        if not (lo <= iv <= hi):
            raise ValueError(f"{dtype.value} fora do intervalo [{lo}, {hi}].")
        return
    if dtype is DataTypeDefXsd.nonPositiveInteger:
        try:
            iv = int(value)
        except ValueError:
            raise ValueError("nonPositiveInteger deve ser inteiro.")
        if iv > 0:
            raise ValueError("nonPositiveInteger deve ser <= 0.")
        return
    if dtype is DataTypeDefXsd.negativeInteger:
        try:
            iv = int(value)
        except ValueError:
            raise ValueError("negativeInteger deve ser inteiro.")
        if iv >= 0:
            raise ValueError("negativeInteger deve ser < 0.")
        return
    if dtype is DataTypeDefXsd.nonNegativeInteger:
        try:
            iv = int(value)
        except ValueError:
            raise ValueError("nonNegativeInteger deve ser inteiro.")
        if iv < 0:
            raise ValueError("nonNegativeInteger deve ser >= 0.")
        return
    if dtype is DataTypeDefXsd.positiveInteger:
        try:
            iv = int(value)
        except ValueError:
            raise ValueError("positiveInteger deve ser inteiro.")
        if iv <= 0:
            raise ValueError("positiveInteger deve ser > 0.")
        return
    if dtype is DataTypeDefXsd.date:
        if not _DATE_RE.fullmatch(value):
            raise ValueError("date deve estar em formato YYYY-MM-DD.")
        try:
            dt.date.fromisoformat(value)
        except ValueError:
            raise ValueError("date inválido.")
        return
    if dtype is DataTypeDefXsd.time:
        m = _TIME_NAMED_RE.fullmatch(value)
        if not m:
            raise ValueError("time deve estar em formato HH:MM[:SS[.fff]][Z|±HH:MM].")
        h = int(m["h"]); mi = int(m["m"]); s = int(m["s"]) if m["s"] else None
        if not (0 <= h <= 23): raise ValueError("hora deve ser 00..23.")
        if not (0 <= mi <= 59): raise ValueError("minuto deve ser 00..59.")
        if s is not None and not (0 <= s <= 59): raise ValueError("segundo deve ser 00..59.")
        if m["sign"]:
            tz_h = int(m["tzh"]); tz_m = int(m["tzm"])
            if not (0 <= tz_h <= 14 and 0 <= tz_m <= 59):
                raise ValueError("fuso horário deve ser ±HH:MM (HH 00..14, MM 00..59).")
        return
    if dtype is DataTypeDefXsd.dateTime:
        m = _DT_NAMED_RE.fullmatch(value)
        if not m:
            raise ValueError("dateTime deve estar em formato YYYY-MM-DDThh:mm[:ss[.fff]][Z|±HH:MM].")
        Y, M, D = int(m["Y"]), int(m["M"]), int(m["D"])
        try:
            dt.date(Y, M, D)
        except ValueError:
            raise ValueError("dateTime com data inválida.")
        h = int(m["h"]); mi = int(m["m"]); s = int(m["s"]) if m["s"] else None
        if not (0 <= h <= 23): raise ValueError("dateTime: hora deve ser 00..23.")
        if not (0 <= mi <= 59): raise ValueError("dateTime: minuto deve ser 00..59.")
        if s is not None and not (0 <= s <= 59): raise ValueError("dateTime: segundo deve ser 00..59.")
        if m["sign"]:
            tz_h = int(m["tzh"]); tz_m = int(m["tzm"])
            if not (0 <= tz_h <= 14 and 0 <= tz_m <= 59):
                raise ValueError("dateTime: fuso deve ser ±HH:MM (HH 00..14, MM 00..59).")
        return
    if dtype is DataTypeDefXsd.anyURI:
        p = urlparse(value)
        if not (p.scheme or p.path):
            raise ValueError("anyURI inválido.")
        return
    if dtype is DataTypeDefXsd.base64Binary:
        try:
            base64.b64decode(value, validate=True)
        except (binascii.Error, ValueError):
            raise ValueError("base64Binary inválido.")
        return
    if dtype is DataTypeDefXsd.hexBinary:
        if len(value) % 2 != 0 or _HEX_RE.fullmatch(value) is None:
            raise ValueError("hexBinary inválido (hex e comprimento par).")
        return
    raise ValueError(f"Validação para '{dtype.value}' ainda não implementada.")


# ========================
# Coerção para dump tipado
# ========================

def _coerce_for_dump(dtype: DataTypeDefXsd, value: str):
    """Converte string validada para o tipo Python mais adequado."""
    if dtype is DataTypeDefXsd.boolean:
        if not value:
            return ''
        return True if value in ("true", "1") else False
    if dtype in (DataTypeDefXsd.float, DataTypeDefXsd.double):
        return float(value)
    if dtype in _INT_RANGES or dtype in (
        DataTypeDefXsd.nonPositiveInteger,
        DataTypeDefXsd.negativeInteger,
        DataTypeDefXsd.nonNegativeInteger,
        DataTypeDefXsd.positiveInteger,
    ):
        return int(value)
    if dtype is DataTypeDefXsd.decimal:
        # escolha pragmática: float facilita JSON. Troque por Decimal(value) se preferir.
        return float(Decimal(value))
    if dtype is DataTypeDefXsd.date:
        return dt.date.fromisoformat(value)
    if dtype is DataTypeDefXsd.time:
        v = value[:-1] + "+00:00" if value.endswith("Z") else value
        try:
            return dt.time.fromisoformat(v)
        except ValueError:
            return value  # fallback seguro
    if dtype is DataTypeDefXsd.dateTime:
        v = value[:-1] + "+00:00" if value.endswith("Z") else value
        try:
            return dt.datetime.fromisoformat(v)
        except ValueError:
            return value
    # tipos “textuais” permanecem string
    return value
