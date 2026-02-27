"""AAS metamodel choice model."""

from __future__ import annotations

from pydantic import RootModel


class DataElement_choice(RootModel):
    """Choice type for DataElement_choice.

    Constraints:
    - Root value must match one of the schema options for `DataElement_choice`.
    """
    root: Blob | File | MultiLanguageProperty | Property | Range | ReferenceElement
