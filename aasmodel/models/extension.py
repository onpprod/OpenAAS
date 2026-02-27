"""AAS metamodel model class."""

from __future__ import annotations

from .has_semantics import HasSemantics


class Extension(HasSemantics):
    """Model for Extension in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `Extension` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    name: str
    valueType: DataTypeDefXsd | None = None
    value: str | None = None
    refersTo: list[Reference] | None = None
