"""Create an AASX package from an AAS JSON file."""

from __future__ import annotations

from pathlib import Path

from aasxpackage import create_aasx_from_json


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    input_json = base_dir / "aas-environment.json"
    output_aasx = base_dir / "example-from-json.aasx"

    created = create_aasx_from_json(
        input_json,
        output_aasx,
        schema_path=base_dir.parent / "schemas" / "aas.json",
    )
    print(f"[aasxpackage] Created: {created}")


if __name__ == "__main__":
    main()
