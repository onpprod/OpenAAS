"""Base Pydantic model for AAS metamodel classes."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class AASBaseModel(BaseModel):
    """Base class for all generated AAS metamodel models.

    Constraints:
    - Uses strict field mapping with extra fields forbidden.
    - Keeps original JSON field names compatible with aas.json schema.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)
