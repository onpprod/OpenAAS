"""AAS metamodel model class."""

from __future__ import annotations

from .has_semantics import HasSemantics


class Qualifier(HasSemantics):
    """Model for Qualifier in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `Qualifier` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    kind: QualifierKind | None = None
    type: str
    valueType: DataTypeDefXsd
    value: str | None = None
    valueId: Reference | None = None
