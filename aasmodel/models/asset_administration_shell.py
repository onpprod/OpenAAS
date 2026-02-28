"""AAS metamodel model class."""

from __future__ import annotations

from .identifiable import Identifiable
from .has_data_specification import HasDataSpecification
from typing import Literal


class AssetAdministrationShell(Identifiable, HasDataSpecification):
    """Model for AssetAdministrationShell in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `AssetAdministrationShell` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    derivedFrom: Reference | None = None
    assetInformation: AssetInformation
    submodels: list[Reference] | None = None
    modelType: Literal['AssetAdministrationShell'] = 'AssetAdministrationShell'
