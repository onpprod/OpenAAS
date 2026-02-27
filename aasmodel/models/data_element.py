"""AAS metamodel model class."""

from __future__ import annotations

from .submodel_element import SubmodelElement


class DataElement(SubmodelElement):
    """Model for DataElement in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `DataElement` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    pass
