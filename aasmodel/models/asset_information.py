"""AAS metamodel model class."""

from __future__ import annotations

from aasmodel.base_model import AASBaseModel


class AssetInformation(AASBaseModel):
    """Model for AssetInformation in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `AssetInformation` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    assetKind: AssetKind
    globalAssetId: str | None = None
    specificAssetIds: list[SpecificAssetId] | None = None
    assetType: str | None = None
    defaultThumbnail: Resource | None = None

