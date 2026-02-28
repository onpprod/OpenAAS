# aasmodel

`aasmodel` provides Pydantic models for the Asset Administration Shell (AAS) metamodel, aligned with `schemas/aas.json`.

It lets you build typed AAS payloads in Python, serialize them to JSON, parse JSON back into models, and validate payload compatibility with the AAS JSON schema.

## Features

- Pydantic-based AAS metamodel classes.
- Inheritance across base classes (for example `SubmodelElement` hierarchy).
- One class per module under `aasmodel/models`.
- Enum support for constrained value domains (for example `ModellingKind`, `DataTypeDefXsd`).
- Optional schema compatibility validation through `validate_against_aas_schema(...)`.
- Strict payload modeling (`extra="forbid"`).

## Requirements

- Python 3.13+
- Dependencies installed from the repository root:

```bash
pip install -e .
```

## Package Structure

- `aasmodel/models/`: AAS metamodel classes and enums.
- `aasmodel/base_model.py`: base Pydantic model configuration.
- `aasmodel/schema_validation.py`: validation helpers for `schemas/aas.json`.
- `aasmodel/__init__.py`: public exports for models and validation helpers.

## Quick Start

Create a minimal `Environment` containing one `Submodel` and one writable `Property`:

```python
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
            keys=[Key(type=KeyTypes.Submodel, value=submodel_id)],
        )
    ],
)

environment = Environment(
    assetAdministrationShells=[shell],
    submodels=[submodel],
)

payload = environment.model_dump(mode="json", exclude_none=True)
validate_against_aas_schema(payload)
```

You can run a complete working example at:

`examples/create_aas_model_example.py`

## Loading JSON into Models

```python
import json

from aasmodel import Environment

payload = json.loads(open("examples/aas-environment.json", encoding="utf-8").read())
environment = Environment.model_validate(payload)
```

For strict schema compatibility validation:

```python
from aasmodel import validate_against_aas_schema

validate_against_aas_schema(payload, schema_path="schemas/aas.json")
```

## Choice Models (RootModel wrappers)

Some schema unions are represented as `RootModel` wrappers.

Example:

- `Submodel.submodelElements` expects `list[SubmodelElement_choice]`.
- Wrap concrete elements with `SubmodelElement_choice(root=...)`.

This preserves compatibility with the schema's `oneOf` definitions while keeping concrete model classes strongly typed.

## Validation Errors

Schema compatibility errors raise `AASSchemaValidationError`:

```python
from aasmodel import AASSchemaValidationError, validate_against_aas_schema

try:
    validate_against_aas_schema(payload)
except AASSchemaValidationError as exc:
    print(exc)
    for line in exc.errors:
        print(line)
```

## Notes

- The models are designed to stay compatible with `schemas/aas.json`.
- Unknown fields are rejected by default (`extra="forbid"`).
- `modelType` fields use fixed literals where required by the schema.

