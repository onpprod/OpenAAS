"""Script de exemplo para subir um servidor OPC UA a partir de JSON."""

from __future__ import annotations

import asyncio
from pathlib import Path

from openopc import create_server_from_json, load_json_spec


async def main() -> None:
    base_dir = Path(__file__).resolve().parent
    json_path = base_dir / "opc_structure_example.json"

    spec = load_json_spec(json_path)
    endpoint = spec.get("server", {}).get(
        "endpoint", "opc.tcp://0.0.0.0:4840/openopc/server/"
    )

    server = await create_server_from_json(json_path)

    async with server:
        print(f"[OpenOPC] Servidor OPC UA iniciado em: {endpoint}")
        print("[OpenOPC] Estrutura carregada do JSON com sucesso.")
        print("[OpenOPC] Pressione Ctrl+C para encerrar.")

        while True:
            await asyncio.sleep(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[OpenOPC] Servidor encerrado pelo usuário.")
