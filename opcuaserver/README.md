# OPCUAServer

`opcuaserver` builds and runs an OPC UA server from an AAS Environment JSON document.

The input JSON is validated against `schemas/aas.json` before node creation (unless lower-level APIs are used with a custom validation flow).

## Features

- Validates AAS JSON using the project schema.
- Builds an OPC UA tree under `Objects/AAS/Environment`.
- Preserves AAS metadata by exporting fields as OPC UA child nodes with original field names.
- Maps AAS submodels and submodel elements recursively.
- Supports anonymous mode, username/password mode, and mixed mode.
- Marks nodes writable when `category == "VARIABLE"`.
- Supports historization of writable nodes (`category == "VARIABLE"`) with backends:
  - memory (RAM, default when historization is enabled)
  - sqlite (persistent file)
  - mongodb (advanced external storage)

## Requirements

- Python 3.13+
- Project dependencies installed (`pip install -e .` or equivalent)

## CLI Usage

Start server with defaults:

```bash
opcuaserver examples/aas-environment.json
```

Validate JSON only:

```bash
opcuaserver examples/aas-environment.json --validate-only
```

Authenticated server:

```bash
opcuaserver examples/aas-environment.json --username admin --password secret
```

Authenticated + anonymous:

```bash
opcuaserver examples/aas-environment.json --username admin --password secret --allow-anonymous
```

Custom endpoint, name and namespace:

```bash
opcuaserver examples/aas-environment.json \
  --endpoint opc.tcp://0.0.0.0:4842/opcuaserver/server/ \
  --name "My OPC UA Server" \
  --namespace-uri "http://example.local/aas"
```

Historization in memory (RAM):

```bash
opcuaserver examples/aas-environment.json --historize
```

Historization in SQLite (`./history.db` by default):

```bash
opcuaserver examples/aas-environment.json --historize --history-backend sqlite
```

Historization in SQLite with explicit file:

```bash
opcuaserver examples/aas-environment.json \
  --historize \
  --history-backend sqlite \
  --history-sqlite-file ./data/opcua-history.db
```

Historization in MongoDB (basic):

```bash
opcuaserver examples/aas-environment.json \
  --historize \
  --history-backend mongodb \
  --history-mongodb-uri "mongodb://localhost:27017"
```

Historization in MongoDB (with auth and namespace):

```bash
opcuaserver examples/aas-environment.json \
  --historize \
  --history-backend mongodb \
  --history-mongodb-uri "mongodb://mongo.local:27017" \
  --history-mongodb-database openaas \
  --history-mongodb-collection history \
  --history-mongodb-username appuser \
  --history-mongodb-password secret \
  --history-mongodb-auth-source admin
```

Historization with per-node limit:

```bash
opcuaserver examples/aas-environment.json --historize --history-count 10000
```

## CLI Options

- `aas_json`: path to AAS Environment JSON.
- `--schema`: path to JSON schema. Default: `schemas/aas.json`.
- `--endpoint`: OPC UA endpoint URL. Default: `opc.tcp://0.0.0.0:4841/opcuaserver/server/`.
- `--name`: server display name. Default: `OPCUAServer`.
- `--namespace-uri`: namespace URI. Default: `http://opcuaserver.local/aas`.
- `--username`: username for authenticated mode.
- `--password`: password for authenticated mode.
- `--allow-anonymous`: allow anonymous sessions with username/password mode.
- `--validate-only`: validate JSON and exit.
- `--no-password-prompt`: disable prompt when `--username` is set without `--password`.
- `--historize`: enable historization for nodes generated from `category == "VARIABLE"`.
- `--history-backend`: `memory`, `sqlite`, or `mongodb`.
- `--history-sqlite-file`: sqlite file path. Default: `history.db` in current directory.
- `--history-mongodb-uri`: MongoDB URI.
- `--history-mongodb-database`: MongoDB database. Default: `opcuaserver_history`.
- `--history-mongodb-collection`: MongoDB collection. Default: `datachanges`.
- `--history-mongodb-username`: optional MongoDB username.
- `--history-mongodb-password`: optional MongoDB password.
- `--history-mongodb-auth-source`: optional MongoDB authSource.
- `--history-count`: max historical values per node (`0` = unlimited).

## Authentication Behavior

- No `--username/--password`: anonymous-only server.
- `--username` + `--password`: username/password mode.
- `--username` + `--password` + `--allow-anonymous`: mixed mode.
- `--allow-anonymous` without `--username`: ignored by CLI.

## AAS to OPC UA Mapping (Complete)

### Root and Environment

- `Objects/AAS` is created.
- `Objects/AAS/Environment` is created.
- Under `Environment`, these folders are created:
  - `AssetAdministrationShells`
  - `Submodels`
  - `ConceptDescriptions`
- Non-structural fields from Environment are exported as OPC UA metadata nodes using the original field name.

### AssetAdministrationShell

- Each AAS is created as an OPC UA object under `AssetAdministrationShells`.
- Node display name uses `idShort` when present, else falls back to `id`/default.
- `category` is exported as OPC UA `Property` named `category` when present.
- Other AAS fields are exported as OPC UA metadata nodes (`Property`) with the same field name.
- `assetInformation` is exported as child object `AssetInformation`, with its fields exported as metadata nodes.
- `submodels` references are exported under child folder `SubmodelReferences`.

### Submodel

- Each submodel is created as OPC UA object under `Environment/Submodels`.
- Node display name uses `idShort` when present, else `id`/default.
- `category` is exported as `Property` `category` when present.
- Other submodel fields (except `submodelElements`) are exported as metadata nodes.
- `submodelElements` are created under child folder `SubmodelElements`.

### ConceptDescription

- Each concept description is created as OPC UA object under `Environment/ConceptDescriptions`.
- `category` is exported as `Property` `category` when present.
- Other fields are exported as metadata nodes.

### Submodel Elements (by model type)

#### Property and other simple value elements

- Elements with direct scalar/serialized `value` are created as OPC UA variables.
- Variant type is resolved from AAS `valueType` (`xs:*`) when provided; otherwise inferred.
- `category == "VARIABLE"` => node writable.
- If historization is enabled, writable nodes are historized.
- Metadata fields are exported with original field names.

#### Range

- Created as OPC UA object.
- `min` and `max` are created as variables when present.
- `valueType` controls data type of `min`/`max`.
- `category == "VARIABLE"` => `min`/`max` writable and historized (if enabled).
- Metadata fields are exported.

#### Operation

- Created as OPC UA object.
- Variable groups map to folders:
  - `inputVariables` -> `InputVariables`
  - `outputVariables` -> `OutputVariables`
  - `inoutputVariables` -> `InOutputVariables`
- If operation variable contains `value` as submodel element object, it is mapped recursively.
- If operation variable value is scalar/non-object, `arg_N` string variable is created.
- Metadata fields are exported.

#### Collection-like/object elements

- Complex elements are created as OPC UA objects.
- Child elements are collected from:
  - `submodelElements`
  - `statements`
  - `annotations`
  - `value` when it contains submodel element objects
- Children are mapped recursively.
- If no child elements exist, scalar metadata keys are exported as variables.
- Metadata fields are exported.

### Metadata Export Rules

- `category` is always exported as explicit OPC UA `Property` named `category` when present.
- Other JSON fields are exported with the same field name.
- Complex values (`dict`/`list`) are serialized to JSON strings.
- Fields that are structural links of the node (`submodelElements`, operation variable groups, etc.) are not duplicated as scalar metadata nodes.

### Writability and Historization

- Writability rule: `category == "VARIABLE"`.
- Historization rule: only writable nodes generated from `VARIABLE` elements are historized when `--historize` is enabled.
- History backend:
  - `memory`: in-memory only.
  - `sqlite`: persisted in local sqlite DB file.
  - `mongodb`: persisted in MongoDB collection.

## Python API

Create and run from JSON file:

```python
import asyncio
from opcuaserver import create_server_from_aas_json

async def main() -> None:
    server = await create_server_from_aas_json(
        "examples/aas-environment.json",
        endpoint="opc.tcp://0.0.0.0:4841/opcuaserver/server/",
        username="admin",
        password="secret",
        allow_anonymous=False,
        historize_variables=True,
        history_backend="sqlite",
        history_sqlite_file="history.db",
    )
    async with server:
        await asyncio.sleep(3600)

asyncio.run(main())
```

Build from in-memory dict:

```python
import asyncio
from opcuaserver import create_server_from_aas_dict

async def main() -> None:
    env = {"assetAdministrationShells": [], "submodels": []}
    server = await create_server_from_aas_dict(env, historize_variables=False)
    async with server:
        await asyncio.sleep(60)

asyncio.run(main())
```

Main exported functions:

- `create_server_from_aas_json(...)`
- `create_server_from_aas_dict(...)`
- `populate_from_aas_dict(...)`
- `validate_aas_environment(...)`
- `load_aas_environment(...)`

## Validation and Errors

Common exceptions:

- `OPCUASchemaValidationError`: JSON does not match `schemas/aas.json`.
- `OPCUASpecError`: invalid runtime specification.
- `FileNotFoundError`: missing JSON/schema file.

Example:

```text
[opcuaserver] Invalid specification: allow_anonymous=false requires username and password.
```

## Interoperability with `opcualoader`

- `opcuaserver` exports metadata as OPC UA nodes using original AAS field names.
- `opcualoader` reads these metadata nodes first to preserve fields like `id`, `description`, `semanticId`, etc.
- For legacy server trees without metadata, `opcualoader` falls back to structural/type inference and writable/read-only inference for `category`.
