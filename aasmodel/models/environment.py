"""AAS metamodel model class."""

from __future__ import annotations

from aasmodel.base_model import AASBaseModel


class Environment(AASBaseModel):
    """Model for Environment in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `Environment` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    assetAdministrationShells: list[AssetAdministrationShell] | None = None
    submodels: list[Submodel] | None = None
    conceptDescriptions: list[ConceptDescription] | None = None

