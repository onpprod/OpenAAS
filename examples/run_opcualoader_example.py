"""Example: export AAS JSON from a running opcuaserver endpoint."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from opcualoader import export_aas_environment_to_file


async def main() -> None:
    base_dir = Path(__file__).resolve().parent
    output_path = base_dir / "aas-exported-from-opcua.json"

    environment = await export_aas_environment_to_file(
        "opc.tcp://0.0.0.0:4841/opcuaserver/server/",
        output_path,
        schema_path=base_dir.parent / "schemas" / "aas.json",
        validate_schema=True,
        pretty=True,
    )
    print("[opcualoader] Export complete.")
    print(f"[opcualoader] Output file: {output_path}")
    print(f"[opcualoader] Submodels exported: {len(environment.get('submodels', []))}")
    print(
        "[opcualoader] AssetAdministrationShells exported: "
        f"{len(environment.get('assetAdministrationShells', []))}"
    )
    print("[opcualoader] Preview:")
    print(json.dumps(environment, ensure_ascii=True, indent=2)[:400] + "...")


if __name__ == "__main__":
    asyncio.run(main())
