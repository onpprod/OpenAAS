"""AAS metamodel model class."""

from __future__ import annotations

from .has_extensions import HasExtensions


class Referable(HasExtensions):
    """Model for Referable in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `Referable` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    category: str | None = None
    idShort: str | None = None
    displayName: list[LangStringNameType] | None = None
    description: list[LangStringTextType] | None = None
    modelType: ModelType
