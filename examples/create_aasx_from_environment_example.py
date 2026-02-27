"""Create an AASX package from an aasmodel Environment instance."""

from __future__ import annotations

from pathlib import Path

from aasxpackage import create_aasx_from_environment
from aasmodel import Environment


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    input_json = base_dir / "aas-environment.json"
    output_aasx = base_dir / "example-from-environment.aasx"

    payload = input_json.read_text(encoding="utf-8")
    environment = Environment.model_validate_json(payload)

    created = create_aasx_from_environment(
        environment,
        output_aasx,
        schema_path=base_dir.parent / "schemas" / "aas.json",
    )
    print(f"[aasxpackage] Created: {created}")


if __name__ == "__main__":
    main()

