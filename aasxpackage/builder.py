"""Create AASX package files from JSON payloads or aasmodel Environment instances."""

from __future__ import annotations

import json
import mimetypes
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import unquote, urlsplit
from xml.etree.ElementTree import Element, ElementTree, SubElement
from zipfile import ZIP_DEFLATED, ZipFile

from aasmodel.schema_validation import AASSchemaValidationError, validate_against_aas_schema

from .constants import (
    CONTENT_TYPE_BINARY,
    CONTENT_TYPE_JSON,
    CONTENT_TYPE_RELS,
    CONTENT_TYPE_TEXT,
    CONTENT_TYPE_XML,
    CONTENT_TYPES_PART,
    DEFAULT_DATA_JSON_PART,
    DEFAULT_ORIGIN_PART,
    OPC_CT_NS,
    OPC_REL_NS,
    REL_AAS_SPEC,
    REL_AAS_SUPPL,
    REL_AASX_ORIGIN,
    ROOT_RELS_PART,
)
from .errors import AASXPackageSpecError, AASXPackageValidationError


@dataclass(frozen=True)
class SupplementaryPart:
    """Represents one supplementary file inside an AASX package."""

    part_name: str
    source_file: Path
    content_type: str


def create_aasx_from_json(
    json_input: str | Path | dict[str, Any],
    output_path: str | Path,
    *,
    schema_path: str | Path | None = None,
    supplementary_source_dir: str | Path | None = None,
    include_supplementary: bool = True,
    strict_supplementary: bool = False,
) -> Path:
    """Create an AASX package from a JSON path or dictionary payload."""
    payload, payload_base_dir = _load_json_payload(json_input)
    if supplementary_source_dir is not None:
        payload_base_dir = _resolve_path(supplementary_source_dir)

    return _create_aasx_from_payload(
        payload,
        output_path=output_path,
        schema_path=schema_path,
        supplementary_source_dir=payload_base_dir,
        include_supplementary=include_supplementary,
        strict_supplementary=strict_supplementary,
    )


def create_aasx_from_environment(
    environment: Any,
    output_path: str | Path,
    *,
    schema_path: str | Path | None = None,
    supplementary_source_dir: str | Path | None = None,
    include_supplementary: bool = True,
    strict_supplementary: bool = False,
) -> Path:
    """Create an AASX package from an aasmodel `Environment` instance."""
    if environment is None:
        raise AASXPackageSpecError("Environment instance cannot be None.")

    if not hasattr(environment, "model_dump"):
        raise AASXPackageSpecError(
            "Environment instance must expose `model_dump` (Pydantic model)."
        )

    payload = environment.model_dump(mode="json", exclude_none=True)
    if not isinstance(payload, dict):
        raise AASXPackageSpecError("Environment serialization must produce a dictionary.")

    source_dir = None
    if supplementary_source_dir is not None:
        source_dir = _resolve_path(supplementary_source_dir)

    return _create_aasx_from_payload(
        payload,
        output_path=output_path,
        schema_path=schema_path,
        supplementary_source_dir=source_dir,
        include_supplementary=include_supplementary,
        strict_supplementary=strict_supplementary,
    )


def _create_aasx_from_payload(
    payload: dict[str, Any],
    *,
    output_path: str | Path,
    schema_path: str | Path | None,
    supplementary_source_dir: Path | None,
    include_supplementary: bool,
    strict_supplementary: bool,
) -> Path:
    _validate_payload(payload, schema_path=schema_path)

    output_file = _resolve_output_path(output_path)
    supplementary_parts: list[SupplementaryPart] = []

    if include_supplementary:
        supplementary_parts = _collect_supplementary_parts(
            payload,
            source_dir=supplementary_source_dir,
            strict=strict_supplementary,
        )

    package_parts: dict[str, bytes] = {}
    package_parts[DEFAULT_ORIGIN_PART] = b"Intentionally empty"
    package_parts[DEFAULT_DATA_JSON_PART] = _dump_json_bytes(payload)

    for supplementary in supplementary_parts:
        package_parts[supplementary.part_name] = supplementary.source_file.read_bytes()

    relationships_root = _build_relationships_xml(
        [
            {
                "Id": "RaasxOrigin",
                "Type": REL_AASX_ORIGIN,
                "Target": "/" + DEFAULT_ORIGIN_PART,
            }
        ]
    )
    package_parts[ROOT_RELS_PART] = relationships_root

    origin_rels_part = _rels_part_for_source(DEFAULT_ORIGIN_PART)
    origin_relationships = _build_relationships_xml(
        [
            {
                "Id": "RaasSpecJson",
                "Type": REL_AAS_SPEC,
                "Target": _relative_target(
                    source_part=DEFAULT_ORIGIN_PART,
                    target_part=DEFAULT_DATA_JSON_PART,
                ),
            }
        ]
    )
    package_parts[origin_rels_part] = origin_relationships

    if supplementary_parts:
        data_rels_part = _rels_part_for_source(DEFAULT_DATA_JSON_PART)
        data_relationships = []
        for index, supplementary in enumerate(supplementary_parts, start=1):
            data_relationships.append(
                {
                    "Id": f"RaasSuppl{index}",
                    "Type": REL_AAS_SUPPL,
                    "Target": _relative_target(
                        source_part=DEFAULT_DATA_JSON_PART,
                        target_part=supplementary.part_name,
                    ),
                }
            )
        package_parts[data_rels_part] = _build_relationships_xml(data_relationships)

    content_types_xml = _build_content_types_xml(
        data_part=DEFAULT_DATA_JSON_PART,
        supplementary_parts=supplementary_parts,
    )
    package_parts[CONTENT_TYPES_PART] = content_types_xml

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output_file, mode="w", compression=ZIP_DEFLATED) as archive:
        for part_name in sorted(package_parts):
            archive.writestr(part_name, package_parts[part_name])

    return output_file


def _load_json_payload(json_input: str | Path | dict[str, Any]) -> tuple[dict[str, Any], Path | None]:
    if isinstance(json_input, dict):
        return json_input, None

    path = _resolve_path(json_input)
    if not path.exists():
        raise FileNotFoundError(f"JSON input file not found: {path}")

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AASXPackageSpecError("AAS JSON root must be an object.")
    return payload, path.parent


def _validate_payload(payload: dict[str, Any], *, schema_path: str | Path | None) -> None:
    try:
        validate_against_aas_schema(payload, schema_path=schema_path)
    except AASSchemaValidationError as exc:
        raise AASXPackageValidationError(str(exc), errors=exc.errors) from exc


def _collect_supplementary_parts(
    payload: dict[str, Any],
    *,
    source_dir: Path | None,
    strict: bool,
) -> list[SupplementaryPart]:
    if source_dir is None:
        source_dir = Path.cwd()

    values = _find_file_element_values(payload)
    if not values:
        return []

    result: list[SupplementaryPart] = []
    seen_part_names: set[str] = set()
    for value in values:
        relative_uri = _normalize_relative_file_uri(value)
        if relative_uri is None:
            continue

        part_name = str(PurePosixPath("aasx") / relative_uri)
        if part_name in seen_part_names:
            continue
        seen_part_names.add(part_name)

        source_file = (source_dir / PurePosixPath(relative_uri)).resolve()
        if not source_file.exists() or not source_file.is_file():
            if strict:
                raise AASXPackageSpecError(
                    f"Supplementary file referenced in AAS was not found: {value}"
                )
            continue

        content_type = _guess_content_type(part_name)
        result.append(
            SupplementaryPart(
                part_name=part_name,
                source_file=source_file,
                content_type=content_type,
            )
        )

    return result


def _find_file_element_values(node: Any) -> list[str]:
    found: list[str] = []
    if isinstance(node, dict):
        model_type = node.get("modelType")
        if model_type == "File":
            value = node.get("value")
            if isinstance(value, str) and value.strip():
                found.append(value.strip())

        for value in node.values():
            found.extend(_find_file_element_values(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(_find_file_element_values(item))
    return found


def _normalize_relative_file_uri(value: str) -> str | None:
    parsed = urlsplit(value)
    if parsed.scheme:
        return None

    path = unquote(parsed.path or "")
    if not path:
        return None

    path = path.replace("\\", "/").strip()
    if path.startswith("/"):
        return None

    normalized = []
    for token in path.split("/"):
        if token in {"", "."}:
            continue
        if token == "..":
            raise AASXPackageSpecError(
                f"Supplementary file path cannot navigate upwards: {value}"
            )
        normalized.append(token)

    if not normalized:
        return None

    return "/".join(normalized)


def _guess_content_type(part_name: str) -> str:
    mime, _ = mimetypes.guess_type(part_name)
    return mime or CONTENT_TYPE_BINARY


def _build_content_types_xml(
    *,
    data_part: str,
    supplementary_parts: list[SupplementaryPart],
) -> bytes:
    types = Element("Types", xmlns=OPC_CT_NS)
    SubElement(
        types,
        "Default",
        Extension="rels",
        ContentType=CONTENT_TYPE_RELS,
    )
    SubElement(
        types,
        "Default",
        Extension="xml",
        ContentType=CONTENT_TYPE_XML,
    )
    SubElement(
        types,
        "Override",
        PartName="/" + DEFAULT_ORIGIN_PART,
        ContentType=CONTENT_TYPE_TEXT,
    )
    SubElement(
        types,
        "Override",
        PartName="/" + data_part,
        ContentType=CONTENT_TYPE_JSON,
    )

    for supplementary in sorted(supplementary_parts, key=lambda item: item.part_name):
        SubElement(
            types,
            "Override",
            PartName="/" + supplementary.part_name,
            ContentType=supplementary.content_type,
        )

    return _serialize_xml(types)


def _build_relationships_xml(relationships: list[dict[str, str]]) -> bytes:
    root = Element("Relationships", xmlns=OPC_REL_NS)
    for relationship in relationships:
        SubElement(
            root,
            "Relationship",
            Id=relationship["Id"],
            Type=relationship["Type"],
            Target=relationship["Target"],
        )
    return _serialize_xml(root)


def _serialize_xml(root: Element) -> bytes:
    from io import BytesIO

    buffer = BytesIO()
    tree = ElementTree(root)
    tree.write(buffer, encoding="utf-8", xml_declaration=True)
    return buffer.getvalue()


def _rels_part_for_source(source_part: str) -> str:
    source = PurePosixPath(source_part)
    return str(source.parent / "_rels" / f"{source.name}.rels")


def _relative_target(*, source_part: str, target_part: str) -> str:
    source_dir = PurePosixPath(source_part).parent
    source_tokens = source_dir.parts
    target_tokens = PurePosixPath(target_part).parts

    common = 0
    for src_token, tgt_token in zip(source_tokens, target_tokens):
        if src_token == tgt_token:
            common += 1
        else:
            break

    up_levels = [".."] * (len(source_tokens) - common)
    down_levels = list(target_tokens[common:])
    relative_tokens = up_levels + down_levels
    if not relative_tokens:
        return "."
    return "/".join(relative_tokens)


def _dump_json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=True, indent=2).encode("utf-8")


def _resolve_output_path(path: str | Path) -> Path:
    resolved = _resolve_path(path)
    if resolved.suffix.lower() != ".aasx":
        resolved = resolved.with_suffix(".aasx")
    return resolved


def _resolve_path(path: str | Path) -> Path:
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = Path.cwd() / resolved
    return resolved.resolve()

