# OPCUAServer

`opcuaserver` creates an OPC UA server from an **AAS Environment JSON**.

The input JSON is validated against `schemas/aas.json` before node creation.

## Features

- AAS schema validation.
- Recursive mapping of AAS submodels/submodel elements to OPC UA nodes.
- Editable OPC UA variables when `category == "VARIABLE"`.
- CLI for running the server.
- Optional username/password authentication.

## CLI

```bash
opcuaserver examples/aas-environment.json
```

Validate only:

```bash
opcuaserver examples/aas-environment.json --validate-only
```

Run with username/password:

```bash
opcuaserver examples/aas-environment.json --username admin --password secret
```
