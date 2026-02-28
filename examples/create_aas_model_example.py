"""Create a minimal AAS Environment model using aasmodel Pydantic classes."""

from __future__ import annotations

import json

from aasmodel import (
    AssetAdministrationShell,
    AssetInformation,
    AssetKind,
    DataTypeDefXsd,
    Environment,
    Key,
    KeyTypes,
    ModellingKind,
    Property,
    Reference,
    ReferenceTypes,
    Submodel,
    SubmodelElement_choice,
    validate_against_aas_schema,
)


def main() -> None:
    submodel_id = "urn:uuid:22006ec6-e02c-4233-8230-ccdb5e6ea671"

    property_element = Property(
        idShort="Prop",
        category="VARIABLE",
        valueType=DataTypeDefXsd.xs_int,
        value="1",
    )

    submodel = Submodel(
        idShort="ExampleSM",
        id=submodel_id,
        kind=ModellingKind.Instance,
        submodelElements=[SubmodelElement_choice(root=property_element)],
    )

    shell = AssetAdministrationShell(
        idShort="ExampleAAS",
        id="urn:uuid:2fc9900b-d87f-4c8b-8943-bbc063873fd8",
        assetInformation=AssetInformation(
            assetKind=AssetKind.Instance,
            globalAssetId="AssetID",
        ),
        submodels=[
            Reference(
                type=ReferenceTypes.ModelReference,
                keys=[
                    Key(
                        type=KeyTypes.Submodel,
                        value=submodel_id,
                    )
                ],
            )
        ],
    )

    environment = Environment(
        assetAdministrationShells=[shell],
        submodels=[submodel],
    )

    payload = environment.model_dump(mode="json", exclude_none=True)
    validate_against_aas_schema(payload)

    print("Environment instance is valid according to schemas/aas.json")
    print(json.dumps(payload, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()

