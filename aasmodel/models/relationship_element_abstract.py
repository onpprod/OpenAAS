"""AAS metamodel model class."""

from __future__ import annotations

from .submodel_element import SubmodelElement


class RelationshipElement_abstract(SubmodelElement):
    """Model for RelationshipElement_abstract in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `RelationshipElement_abstract` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    first: Reference | None = None
    second: Reference | None = None
