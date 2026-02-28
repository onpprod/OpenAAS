"""AAS metamodel model class."""

from __future__ import annotations

from aasmodel.base_model import AASBaseModel


class HasExtensions(AASBaseModel):
    """Model for HasExtensions in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `HasExtensions` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    extensions: list[Extension] | None = None

