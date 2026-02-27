# AASXPackage

`aasxpackage` creates `.aasx` files based on AAS Part 5 (AASX Package File Format), using Open Packaging Conventions (OPC).

The package supports two main workflows:

- create from JSON (file path or `dict`);
- create from an `Environment` instance from `aasmodel`.

## What the package generates

Implemented OPC/AASX structure:

- `/_rels/.rels` with `aasx-origin` relationship;
- `/aasx/aasx-origin` (AASX origin file);
- `/aasx/data.json` with the AAS Environment payload;
- `/aasx/_rels/aasx-origin.rels` with `aas-spec` relationship;
- `/aasx/_rels/data.json.rels` with `aas-suppl` relationships (when applicable);
- `/[Content_Types].xml`.

## Requirements

- Python 3.13+
- project dependencies installed (`pip install -e .` or equivalent flow)

## CLI usage

Basic command:

```bash
aasxpackage --json examples/aas-environment.json --output build/example.aasx
```

You can also run it as:

```bash
python -m aasxpackage --json examples/aas-environment.json --output build/example.aasx
```

### CLI options

- `--json` (required): input AAS Environment JSON file path.
- `--output` / `-o` (required): output `.aasx` file path.
- `--schema` (optional, default `schemas/aas.json`): schema used to validate JSON before packaging.
- `--supplementary-source-dir` (optional): base directory used to resolve supplementary files referenced by `File` elements.
- `--no-supplementary` (flag): disables supplementary file inclusion.
- `--strict-supplementary` (flag): fails package creation if a referenced supplementary file is missing.

## API usage

### 1) Create AASX from JSON

```python
from aasxpackage import create_aasx_from_json

created_path = create_aasx_from_json(
    json_input="examples/aas-environment.json",
    output_path="build/example-from-json.aasx",
    schema_path="schemas/aas.json",
    supplementary_source_dir="examples",
    include_supplementary=True,
    strict_supplementary=False,
)
print(created_path)
```

Parameters of `create_aasx_from_json(...)`:

- `json_input`: `str | Path | dict[str, Any]`. Can be a JSON file path or in-memory payload.
- `output_path`: `str | Path`. Output package path.
- `schema_path`: schema path for validation (`None` uses default resolution).
- `supplementary_source_dir`: base directory used to locate supplementary files.
- `include_supplementary`: enables/disables supplementary file inclusion.
- `strict_supplementary`: when `True`, raises an error if any referenced supplementary file is missing.

Return:

- absolute `Path` of the generated `.aasx` file.

### 2) Create AASX from `Environment` (`aasmodel`)

```python
from aasxpackage import create_aasx_from_environment
from aasmodel import Environment

environment = Environment.model_validate_json(
    open("examples/aas-environment.json", "r", encoding="utf-8").read()
)

created_path = create_aasx_from_environment(
    environment=environment,
    output_path="build/example-from-environment.aasx",
    schema_path="schemas/aas.json",
    supplementary_source_dir="examples",
    include_supplementary=True,
    strict_supplementary=False,
)
print(created_path)
```

Parameters of `create_aasx_from_environment(...)`:

- `environment`: Pydantic instance exposing `model_dump` (for example `aasmodel.Environment`).
- `output_path`, `schema_path`, `supplementary_source_dir`, `include_supplementary`, `strict_supplementary`: same meaning as the JSON method.

Return:

- absolute `Path` of the generated `.aasx` file.

## Supplementary files

The package scans `File` elements in the payload and evaluates their `value` field.

Rules:

- only relative URIs are treated as package-internal supplementary files;
- external URIs (with `scheme`, like `http://...`) are ignored;
- absolute paths are ignored;
- paths containing `..` raise an error (path traversal protection);
- when the file exists, it is included under `/aasx/<relative_path>`;
- an `aas-suppl` relationship is created in `aasx/_rels/data.json.rels`;
- without `--strict-supplementary`, missing references are ignored;
- with `--strict-supplementary`, missing references fail package creation.

Example `File` element in JSON:

```json
{
  "modelType": "File",
  "idShort": "Manual",
  "contentType": "application/pdf",
  "value": "manuals/manual.pdf"
}
```

## Validation and errors

Before packaging, the payload is validated against `aas.json`.

Main errors:

- `AASXPackageValidationError`: payload is not compatible with AAS schema.
- `AASXPackageSpecError`: specification/input error (invalid path, invalid payload, etc.).
- `FileNotFoundError`: input file or schema file not found.

