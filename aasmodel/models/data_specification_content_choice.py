"""AAS metamodel choice model."""

from __future__ import annotations

from pydantic import RootModel


class DataSpecificationContent_choice(RootModel):
    """Choice type for DataSpecificationContent_choice.

    Constraints:
    - Root value must match one of the schema options for `DataSpecificationContent_choice`.
    """
    root: DataSpecificationIec61360
