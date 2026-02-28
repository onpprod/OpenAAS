"""AAS metamodel choice model."""

from __future__ import annotations

from pydantic import RootModel


class SubmodelElement_choice(RootModel):
    """Choice type for SubmodelElement_choice.

    Constraints:
    - Root value must match one of the schema options for `SubmodelElement_choice`.
    """
    root: RelationshipElement | AnnotatedRelationshipElement | BasicEventElement | Blob | Capability | Entity | File | MultiLanguageProperty | Operation | Property | Range | ReferenceElement | SubmodelElementCollection | SubmodelElementList
