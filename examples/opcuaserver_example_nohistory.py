"""Run opcuaserver without historization using OpenAAS.json."""

from __future__ import annotations

import asyncio
from pathlib import Path

from opcuaserver import create_server_from_aas_json


async def main() -> None:
    base_dir = Path(__file__).resolve().parent
    aas_json_path = base_dir / "OpenAAS.json"
    schema_path = base_dir.parent / "schemas" / "aas.json"
    endpoint = "opc.tcp://0.0.0.0:4841/opcuaserver/server/"

    server = await create_server_from_aas_json(
        aas_json_path,
        schema_path=schema_path,
        endpoint=endpoint,
        historize_variables=False,
    )

    async with server:
        print("[opcuaserver] Example: no historization")
        print(f"[opcuaserver] Endpoint: {endpoint}")
        print("[opcuaserver] Source: OpenAAS.json")
        print("[opcuaserver] Press Ctrl+C to stop.")
        while True:
            await asyncio.sleep(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[opcuaserver] Server stopped.")
