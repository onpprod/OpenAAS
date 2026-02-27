"""Run opcuaserver with SQLite historization using OpenAAS.json."""

from __future__ import annotations

import asyncio
from pathlib import Path

from opcuaserver import create_server_from_aas_json


async def main() -> None:
    base_dir = Path(__file__).resolve().parent
    aas_json_path = base_dir / "OpenAAS.json"
    schema_path = base_dir.parent / "schemas" / "aas.json"
    endpoint = "opc.tcp://0.0.0.0:4843/opcuaserver/server/"
    sqlite_file = Path.cwd() / "history.db"

    server = await create_server_from_aas_json(
        aas_json_path,
        schema_path=schema_path,
        endpoint=endpoint,
        historize_variables=True,
        history_backend="sqlite",
        history_sqlite_file=sqlite_file,
        history_count=0,
    )

    async with server:
        print("[opcuaserver] Example: sqlite historization")
        print(f"[opcuaserver] Endpoint: {endpoint}")
        print("[opcuaserver] Source: OpenAAS.json")
        print(f"[opcuaserver] Backend: sqlite ({sqlite_file})")
        print("[opcuaserver] Press Ctrl+C to stop.")
        while True:
            await asyncio.sleep(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[opcuaserver] Server stopped.")
