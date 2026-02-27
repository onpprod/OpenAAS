"""AAS metamodel model class."""

from __future__ import annotations

from openaas.base_model import AASBaseModel


class EventPayload(AASBaseModel):
    """Model for EventPayload in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `EventPayload` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    source: Reference
    sourceSemanticId: Reference | None = None
    observableReference: Reference
    observableSemanticId: Reference | None = None
    topic: str | None = None
    subjectId: Reference | None = None
    timeStamp: str
    payload: str | None = None
