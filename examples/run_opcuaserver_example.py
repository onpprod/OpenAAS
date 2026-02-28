"""Example script to run opcuaserver from AAS JSON."""

from __future__ import annotations

import asyncio
from pathlib import Path

from opcuaserver import create_server_from_aas_json


async def main() -> None:
    base_dir = Path(__file__).resolve().parent
    aas_json_path = base_dir / "aas-environment.json"

    server = await create_server_from_aas_json(
        aas_json_path,
        schema_path=base_dir.parent / "schemas" / "aas.json",
    )

    async with server:
        print("[opcuaserver] Example server running.")
        print("[opcuaserver] Endpoint: opc.tcp://0.0.0.0:4841/opcuaserver/server/")
        print("[opcuaserver] Press Ctrl+C to stop.")
        while True:
            await asyncio.sleep(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[opcuaserver] Server stopped.")
