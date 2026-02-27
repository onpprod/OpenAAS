"""CLI entrypoint for running an OPC UA server from an AAS JSON file."""

from __future__ import annotations

import argparse
import asyncio
import getpass
from typing import Sequence

from .builder import (
    DEFAULT_ENDPOINT,
    DEFAULT_HISTORY_MONGODB_COLLECTION,
    DEFAULT_HISTORY_MONGODB_DATABASE,
    DEFAULT_HISTORY_SQLITE_FILE,
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
    parser.add_argument(
        "--historize",
        action="store_true",
        help="Enable historization for all nodes generated from elements with category VARIABLE.",
    )
    parser.add_argument(
        "--history-backend",
        choices=("memory", "sqlite", "mongodb"),
        default=None,
        help=(
            "History backend. If omitted and --historize is set, memory is used. "
            "Use sqlite for local persistence or mongodb for advanced external storage."
        ),
    )
    parser.add_argument(
        "--history-sqlite-file",
        default=DEFAULT_HISTORY_SQLITE_FILE,
        help=(
            "SQLite filename/path for history persistence. "
            f"Default: {DEFAULT_HISTORY_SQLITE_FILE}"
        ),
    )
    parser.add_argument(
        "--history-mongodb-uri",
        default=None,
        help="MongoDB connection URI for history backend mongodb.",
    )
    parser.add_argument(
        "--history-mongodb-database",
        default=DEFAULT_HISTORY_MONGODB_DATABASE,
        help=f"MongoDB database name. Default: {DEFAULT_HISTORY_MONGODB_DATABASE}",
    )
    parser.add_argument(
        "--history-mongodb-collection",
        default=DEFAULT_HISTORY_MONGODB_COLLECTION,
        help=f"MongoDB collection name. Default: {DEFAULT_HISTORY_MONGODB_COLLECTION}",
    )
    parser.add_argument(
        "--history-mongodb-username",
        default=None,
        help="MongoDB username (optional; usually included in URI).",
    )
    parser.add_argument(
        "--history-mongodb-password",
        default=None,
        help="MongoDB password (optional; usually included in URI).",
    )
    parser.add_argument(
        "--history-mongodb-auth-source",
        default=None,
        help="MongoDB authSource database (optional).",
    )
    parser.add_argument(
        "--history-count",
        type=int,
        default=0,
        help="Maximum number of historical values per node (0 = unlimited).",
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
    mongo_opts_used = any(
        (
            args.history_mongodb_uri,
            args.history_mongodb_username,
            args.history_mongodb_password,
            args.history_mongodb_auth_source,
        )
    )

    history_backend = args.history_backend
    if history_backend is None:
        if mongo_opts_used:
            history_backend = "mongodb"
        else:
            history_backend = "memory"

    historize_variables = bool(args.historize or args.history_backend or mongo_opts_used)

    if args.history_mongodb_password and not args.history_mongodb_username:
        raise OPCUASpecError(
            "--history-mongodb-password requires --history-mongodb-username."
        )

    server = await create_server_from_aas_json(
        args.aas_json,
        schema_path=args.schema,
        endpoint=args.endpoint,
        server_name=args.name,
        namespace_uri=args.namespace_uri,
        username=args.username,
        password=args.password,
        allow_anonymous=args.allow_anonymous,
        historize_variables=historize_variables,
        history_backend=history_backend,
        history_count=args.history_count,
        history_sqlite_file=args.history_sqlite_file,
        history_mongodb_uri=args.history_mongodb_uri,
        history_mongodb_database=args.history_mongodb_database,
        history_mongodb_collection=args.history_mongodb_collection,
        history_mongodb_username=args.history_mongodb_username,
        history_mongodb_password=args.history_mongodb_password,
        history_mongodb_auth_source=args.history_mongodb_auth_source,
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

    if historize_variables:
        print(f"[opcuaserver] Historization: enabled ({history_backend})")
        if history_backend == "sqlite":
            print(f"[opcuaserver] History SQLite file: {args.history_sqlite_file}")
        if history_backend == "mongodb":
            print(f"[opcuaserver] History MongoDB URI: {args.history_mongodb_uri}")
            print(
                "[opcuaserver] History MongoDB namespace: "
                f"{args.history_mongodb_database}.{args.history_mongodb_collection}"
            )
        print(
            "[opcuaserver] History count per node: "
            f"{args.history_count if args.history_count else 'unlimited'}"
        )
    else:
        print("[opcuaserver] Historization: disabled")

    async with server:
        print("[opcuaserver] Server is running. Press Ctrl+C to stop.")
        while True:
            await asyncio.sleep(1)
