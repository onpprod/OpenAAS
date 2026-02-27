# OPCUAServer

`opcuaserver` builds and runs an OPC UA server from an AAS Environment JSON document.

The input JSON is validated against `schemas/aas.json` before node creation (unless you only call lower-level APIs with custom validation flow).

## Features

- Validates AAS JSON using the project schema.
- Builds an OPC UA tree under `Objects/AAS`.
- Maps AAS submodels and submodel elements recursively.
- Supports anonymous mode and username/password mode.
- Supports mixed mode (username/password plus optional anonymous).
- Marks variables writable when `category == "VARIABLE"`.
- Can historize all nodes generated from `category == "VARIABLE"` elements.
- Supports history backends: memory (default), SQLite, and MongoDB.
- Publishes `category` as explicit OPC UA metadata (`Property` node named `category`).

## Requirements

- Python 3.13+
- Project dependencies installed (`pip install -e .` or equivalent)

## CLI Usage

Start a server with default endpoint:

```bash
opcuaserver examples/aas-environment.json
```

Validate JSON only (do not start server):

```bash
opcuaserver examples/aas-environment.json --validate-only
```

Run with username/password authentication:

```bash
opcuaserver examples/aas-environment.json --username admin --password secret
```

Run with username/password and allow anonymous sessions too:

```bash
opcuaserver examples/aas-environment.json --username admin --password secret --allow-anonymous
```

Use custom endpoint, name, and namespace URI:

```bash
opcuaserver examples/aas-environment.json \
  --endpoint opc.tcp://0.0.0.0:4842/opcuaserver/server/ \
  --name "My OPC UA Server" \
  --namespace-uri "http://example.local/aas"
```

Enable historization in memory (RAM):

```bash
opcuaserver examples/aas-environment.json --historize
```

Enable historization persisted in SQLite (`./history.db` by default):

```bash
opcuaserver examples/aas-environment.json --historize --history-backend sqlite
```

Enable historization in MongoDB:

```bash
opcuaserver examples/aas-environment.json \
  --historize \
  --history-backend mongodb \
  --history-mongodb-uri "mongodb://localhost:27017" \
  --history-mongodb-database openaas \
  --history-mongodb-collection history
```

## CLI Options

- `aas_json` (positional): path to the AAS Environment JSON.
- `--schema`: path to JSON schema. Default: `schemas/aas.json`.
- `--endpoint`: OPC UA endpoint URL. Default: `opc.tcp://0.0.0.0:4841/opcuaserver/server/`.
- `--name`: server display name. Default: `OPCUAServer`.
- `--namespace-uri`: namespace URI for created nodes. Default: `http://opcuaserver.local/aas`.
- `--username`: username for authenticated mode.
- `--password`: password for authenticated mode.
- `--allow-anonymous`: in authenticated mode, also accept anonymous sessions.
- `--validate-only`: validate JSON and exit.
- `--no-password-prompt`: disable prompt when `--username` is set without `--password`.
- `--historize`: enable historization for nodes generated from `category == "VARIABLE"`.
- `--history-backend`: `memory`, `sqlite`, or `mongodb`.
- `--history-sqlite-file`: SQLite path/filename. Default: `history.db` in current directory.
- `--history-mongodb-uri`: MongoDB URI.
- `--history-mongodb-database`: MongoDB database name. Default: `opcuaserver_history`.
- `--history-mongodb-collection`: MongoDB collection name. Default: `datachanges`.
- `--history-mongodb-username`: optional MongoDB username.
- `--history-mongodb-password`: optional MongoDB password.
- `--history-mongodb-auth-source`: optional MongoDB authSource.
- `--history-count`: max historical values per node (`0` = unlimited).

## Authentication Behavior

- No `--username/--password`: anonymous-only server.
- `--username` and `--password`: username/password server.
- `--username` and `--password` plus `--allow-anonymous`: mixed mode.
- `--allow-anonymous` without `--username`: ignored by CLI (server remains anonymous-only).

## AAS to OPC UA Mapping

Root:
- The server creates `Objects/AAS`.

Asset Administration Shell:
- Each AAS is created as an OPC UA object.
- A `Submodels` folder is created under each AAS object.

Submodel:
- Created as an OPC UA object.
- If `category` exists in JSON, a child OPC UA `Property` named `category` is created.

Property and simple value elements:
- Created as OPC UA variables with type inferred from AAS `valueType`.
- If `category == "VARIABLE"`, write access is enabled.
- If historization is enabled, these writable nodes are historized for HistoryRead.
- If `category` exists, a child OPC UA `Property` named `category` is created on the element node.

Range:
- Created as an OPC UA object containing `min` and `max` variables.
- If `category == "VARIABLE"`, `min` and `max` are writable.
- If historization is enabled, writable `min`/`max` variables are historized.
- If `category` exists, a child OPC UA `Property` named `category` is created.

Operation:
- Created as an OPC UA object with `InputVariables`, `OutputVariables`, and `InOutputVariables` folders.
- If `category` exists, a child OPC UA `Property` named `category` is created.

Collection-like and object elements:
- Created as OPC UA objects with recursive child elements.
- Scalar metadata fields (non-structural JSON keys) are exported as variables.
- If `category` exists, a child OPC UA `Property` named `category` is created.

## Python API

Create and run directly from JSON file:

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
    )
    async with server:
        await asyncio.sleep(3600)

asyncio.run(main())
```

Build from an in-memory dictionary:

```python
import asyncio
from opcuaserver import create_server_from_aas_dict

async def main() -> None:
    env = {"assetAdministrationShells": [], "submodels": []}
    server = await create_server_from_aas_dict(env)
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
- `OPCUASpecError`: invalid runtime specification (for example invalid auth combination).
- `FileNotFoundError`: missing JSON/schema file.

Common error example:

```text
[opcuaserver] Invalid specification: allow_anonymous=false requires username and password.
```

Meaning:

- You disabled anonymous access while not providing credentials.

Fix:

- Provide `--username` and `--password`, or do not force anonymous off in API usage.

## Interoperability with `opcualoader`

- `opcuaserver` now writes explicit `category` metadata nodes.
- `opcualoader` reads these metadata nodes first.
- If metadata is not present, `opcualoader` falls back to writable/read-only inference.
