"""CLI for opcualoader."""

from __future__ import annotations

import argparse
import asyncio
import getpass
import json
from pathlib import Path
from typing import Sequence

from .errors import OPCUALoaderSchemaError, OPCUALoaderSpecError
from .loader import DEFAULT_TIMEOUT, load_aas_environment_from_server


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="opcualoader",
        description=(
            "Scan an OPC UA server produced by opcuaserver and export AAS JSON."
        ),
    )
    parser.add_argument("endpoint", help="OPC UA endpoint (opc.tcp://...).")
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Output JSON file path. If omitted, prints to stdout.",
    )
    parser.add_argument(
        "--schema",
        default="schemas/aas.json",
        help="AAS schema path. Default: schemas/aas.json",
    )
    parser.add_argument(
        "--username",
        default=None,
        help="Username for authenticated OPC UA endpoint.",
    )
    parser.add_argument(
        "--password",
        default=None,
        help="Password for authenticated OPC UA endpoint.",
    )
    parser.add_argument(
        "--no-password-prompt",
        action="store_true",
        help="Do not prompt for password when --username is set without --password.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=f"Connection timeout in seconds. Default: {DEFAULT_TIMEOUT}",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Output compact JSON without indentation.",
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip schema validation of generated JSON.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.password and not args.username:
        parser.error("--password requires --username.")

    if args.username and args.password is None and not args.no_password_prompt:
        args.password = getpass.getpass("Password: ")

    if args.timeout <= 0:
        parser.error("--timeout must be greater than 0.")

    try:
        environment = asyncio.run(
            load_aas_environment_from_server(
                args.endpoint,
                username=args.username,
                password=args.password,
                timeout=args.timeout,
                schema_path=args.schema,
                validate_schema=not args.no_validate,
            )
        )

        dump_kwargs = {"ensure_ascii": True}
        if args.compact:
            dump_kwargs["separators"] = (",", ":")
        else:
            dump_kwargs["indent"] = 2

        output_json = json.dumps(environment, **dump_kwargs)
        if args.output:
            output_path = Path(args.output)
            if not output_path.is_absolute():
                output_path = Path.cwd() / output_path
            output_path = output_path.resolve()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(output_json + "\n", encoding="utf-8")
            print(f"[opcualoader] AAS JSON exported to: {output_path}")
        else:
            print(output_json)
        return 0

    except KeyboardInterrupt:
        print("\n[opcualoader] Operation cancelled by user.")
        return 0
    except FileNotFoundError as exc:
        print(f"[opcualoader] File error: {exc}")
        return 1
    except OPCUALoaderSchemaError as exc:
        print(f"[opcualoader] Schema validation error: {exc}")
        for error in exc.errors:
            print(f"  - {error}")
        return 1
    except OPCUALoaderSpecError as exc:
        print(f"[opcualoader] Invalid OPC UA structure: {exc}")
        return 1
    except Exception as exc:  # pragma: no cover
        print(f"[opcualoader] Unexpected error: {exc}")
        return 1
