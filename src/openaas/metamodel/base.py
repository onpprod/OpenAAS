# py313 / pydantic v2
from __future__ import annotations
from typing import Dict


# =========================
# Tipos básicos
# =========================

Identifier = str  # ID global (IRI/IRDI/UUID). Validações específicas podem ser acrescentadas.
NameType = str
MultiLanguageNameType = Dict[str, str]
MultiLanguageTextType = Dict[str, str]

