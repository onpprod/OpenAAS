"""AAS metamodel choice model."""

from __future__ import annotations

from pydantic import RootModel


class RelationshipElement_choice(RootModel):
    """Choice type for RelationshipElement_choice.

    Constraints:
    - Root value must match one of the schema options for `RelationshipElement_choice`.
    """
    root: RelationshipElement | AnnotatedRelationshipElement
