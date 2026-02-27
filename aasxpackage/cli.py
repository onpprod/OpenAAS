"""CLI for creating AASX package files."""

from __future__ import annotations

import argparse
from typing import Sequence

from .builder import create_aasx_from_json
from .errors import AASXPackageSpecError, AASXPackageValidationError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aasxpackage",
        description="Create .aasx package files from AAS JSON payloads.",
    )
    parser.add_argument(
        "--json",
        required=True,
        help="Path to an AAS environment JSON file.",
    )
    parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Output .aasx file path.",
    )
    parser.add_argument(
        "--schema",
        default="schemas/aas.json",
        help="AAS JSON schema path. Default: schemas/aas.json",
    )
    parser.add_argument(
        "--supplementary-source-dir",
        default=None,
        help=(
            "Directory used to resolve relative File element paths "
            "for supplementary files."
        ),
    )
    parser.add_argument(
        "--no-supplementary",
        action="store_true",
        help="Do not include supplementary files in the package.",
    )
    parser.add_argument(
        "--strict-supplementary",
        action="store_true",
        help="Fail if a referenced supplementary file is missing.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        output = create_aasx_from_json(
            args.json,
            args.output,
            schema_path=args.schema,
            supplementary_source_dir=args.supplementary_source_dir,
            include_supplementary=not args.no_supplementary,
            strict_supplementary=args.strict_supplementary,
        )
        print(f"[aasxpackage] AASX package created: {output}")
        return 0
    except FileNotFoundError as exc:
        print(f"[aasxpackage] File error: {exc}")
        return 1
    except AASXPackageValidationError as exc:
        print(f"[aasxpackage] Schema validation error: {exc}")
        for line in exc.errors:
            print(f"  - {line}")
        return 1
    except AASXPackageSpecError as exc:
        print(f"[aasxpackage] Invalid specification: {exc}")
        return 1
    except Exception as exc:  # pragma: no cover
        print(f"[aasxpackage] Unexpected error: {exc}")
        return 1
