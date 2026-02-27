"""Run opcuaserver with MongoDB historization using OpenAAS.json."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from opcuaserver import create_server_from_aas_json


async def main() -> None:
    base_dir = Path(__file__).resolve().parent
    aas_json_path = base_dir / "OpenAAS.json"
    schema_path = base_dir.parent / "schemas" / "aas.json"
    endpoint = "opc.tcp://0.0.0.0:4844/opcuaserver/server/"

    mongodb_uri = os.getenv("OPENAAS_MONGODB_URI", "mongodb://localhost:27017")
    mongodb_database = os.getenv("OPENAAS_MONGODB_DATABASE", "openaas")
    mongodb_collection = os.getenv("OPENAAS_MONGODB_COLLECTION", "history")
    mongodb_username = os.getenv("OPENAAS_MONGODB_USERNAME")
    mongodb_password = os.getenv("OPENAAS_MONGODB_PASSWORD")
    mongodb_auth_source = os.getenv("OPENAAS_MONGODB_AUTH_SOURCE")

    server = await create_server_from_aas_json(
        aas_json_path,
        schema_path=schema_path,
        endpoint=endpoint,
        historize_variables=True,
        history_backend="mongodb",
        history_mongodb_uri=mongodb_uri,
        history_mongodb_database=mongodb_database,
        history_mongodb_collection=mongodb_collection,
        history_mongodb_username=mongodb_username,
        history_mongodb_password=mongodb_password,
        history_mongodb_auth_source=mongodb_auth_source,
        history_count=0,
    )

    async with server:
        print("[opcuaserver] Example: mongodb historization")
        print(f"[opcuaserver] Endpoint: {endpoint}")
        print("[opcuaserver] Source: OpenAAS.json")
        print(
            "[opcuaserver] Backend: mongodb "
            f"({mongodb_uri}, {mongodb_database}.{mongodb_collection})"
        )
        print("[opcuaserver] Press Ctrl+C to stop.")
        while True:
            await asyncio.sleep(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[opcuaserver] Server stopped.")
