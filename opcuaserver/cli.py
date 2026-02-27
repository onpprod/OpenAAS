"""CLI entrypoint for running an OPC UA server from an AAS JSON file."""

from __future__ import annotations

import argparse
import asyncio
import getpass
from typing import Sequence

from .builder import (
    DEFAULT_ENDPOINT,
    DEFAULT_NAMESPACE_URI,
    DEFAULT_SERVER_NAME,
    create_server_from_aas_json,
)
from .errors import OPCUASchemaValidationError, OPCUASpecError
from .validation import load_aas_environment


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="opcuaserver",
        description=(
            "Run an OPC UA server from an AAS JSON environment, validated by schema."
        ),
    )
    parser.add_argument("aas_json", help="Path to the AAS environment JSON file.")
    parser.add_argument(
        "--schema",
        default="schemas/aas.json",
        help="Path to AAS JSON schema. Default: schemas/aas.json",
    )
    parser.add_argument(
        "--endpoint",
        default=DEFAULT_ENDPOINT,
        help=f"OPC UA endpoint. Default: {DEFAULT_ENDPOINT}",
    )
    parser.add_argument(
        "--name",
        default=DEFAULT_SERVER_NAME,
        help=f"Server display name. Default: {DEFAULT_SERVER_NAME}",
    )
    parser.add_argument(
        "--namespace-uri",
        default=DEFAULT_NAMESPACE_URI,
        help=f"Namespace URI. Default: {DEFAULT_NAMESPACE_URI}",
    )
    parser.add_argument(
        "--username",
        default=None,
        help="Username for password authentication.",
    )
    parser.add_argument(
        "--password",
        default=None,
        help="Password for password authentication.",
    )
    parser.add_argument(
        "--allow-anonymous",
        action="store_true",
        default=None,
        help="Allow anonymous sessions together with username/password mode.",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate the JSON against schema and exit.",
    )
    parser.add_argument(
        "--no-password-prompt",
        action="store_true",
        help="Do not prompt for password when --username is provided without --password.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.password and not args.username:
        parser.error("--password requires --username.")

    if args.username and args.password is None and not args.no_password_prompt:
        args.password = getpass.getpass("Password: ")

    if args.username is None and args.allow_anonymous:
        print(
            "[opcuaserver] --allow-anonymous was ignored because username/password mode is disabled."
        )

    try:
        if args.validate_only:
            load_aas_environment(args.aas_json, schema_path=args.schema)
            print("[opcuaserver] AAS JSON is valid according to the schema.")
            return 0

        asyncio.run(_run_server(args))
        return 0
    except KeyboardInterrupt:
        print("\n[opcuaserver] Server stopped by user.")
        return 0
    except FileNotFoundError as exc:
        print(f"[opcuaserver] File error: {exc}")
        return 1
    except OPCUASchemaValidationError as exc:
        print(f"[opcuaserver] Schema validation error: {exc}")
        for error in exc.errors:
            print(f"  - {error}")
        return 1
    except OPCUASpecError as exc:
        print(f"[opcuaserver] Invalid specification: {exc}")
        return 1
    except Exception as exc:  # pragma: no cover
        print(f"[opcuaserver] Unexpected error: {exc}")
        return 1


async def _run_server(args: argparse.Namespace) -> None:
    server = await create_server_from_aas_json(
        args.aas_json,
        schema_path=args.schema,
        endpoint=args.endpoint,
        server_name=args.name,
        namespace_uri=args.namespace_uri,
        username=args.username,
        password=args.password,
        allow_anonymous=args.allow_anonymous,
    )

    print(f"[opcuaserver] Endpoint: {args.endpoint}")
    print(f"[opcuaserver] Name: {args.name}")
    print(f"[opcuaserver] Namespace URI: {args.namespace_uri}")
    if args.username:
        print("[opcuaserver] Authentication: username/password")
        if args.allow_anonymous:
            print("[opcuaserver] Anonymous access: enabled")
        else:
            print("[opcuaserver] Anonymous access: disabled")
    else:
        print("[opcuaserver] Authentication: anonymous")

    async with server:
        print("[opcuaserver] Server is running. Press Ctrl+C to stop.")
        while True:
            await asyncio.sleep(1)
