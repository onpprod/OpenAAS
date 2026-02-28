"""Constants for AASX package generation."""

from __future__ import annotations

OPC_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
OPC_CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"

AASX_REL_NS = "http://admin-shell.io/aasx/relationships"
AASX_REL_NS_DEPRECATED = "http://www.admin-shell.io/aasx/relationships"

REL_AASX_ORIGIN = f"{AASX_REL_NS}/aasx-origin"
REL_AAS_SPEC = f"{AASX_REL_NS}/aas-spec"
REL_AAS_SUPPL = f"{AASX_REL_NS}/aas-suppl"

CONTENT_TYPE_RELS = "application/vnd.openxmlformats-package.relationships+xml"
CONTENT_TYPE_XML = "application/xml"
CONTENT_TYPE_JSON = "application/json"
CONTENT_TYPE_TEXT = "text/plain"
CONTENT_TYPE_BINARY = "application/octet-stream"

ROOT_RELS_PART = "_rels/.rels"
CONTENT_TYPES_PART = "[Content_Types].xml"
DEFAULT_ORIGIN_PART = "aasx/aasx-origin"
DEFAULT_DATA_JSON_PART = "aasx/data.json"
