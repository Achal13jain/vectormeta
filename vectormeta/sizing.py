"""Metadata byte sizing utilities."""

from __future__ import annotations

import json
from typing import Any, Mapping

from vectormeta.errors import InvalidInputError
from vectormeta.models import FieldSize


def compact_json_bytes(value: Any) -> bytes:
    """Serialize a value as compact UTF-8 JSON bytes."""
    try:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise InvalidInputError(f"Value is not JSON serializable: {exc}") from exc


def metadata_size_bytes(metadata: Mapping[str, Any]) -> int:
    """Return the compact JSON UTF-8 byte size of a metadata object."""
    return len(compact_json_bytes(dict(metadata)))


def field_sizes(metadata: Mapping[str, Any]) -> list[FieldSize]:
    """Return top-level metadata field sizes sorted from largest to smallest."""
    sizes = [
        FieldSize(field_name=str(field_name), size_bytes=len(compact_json_bytes({field_name: value})))
        for field_name, value in metadata.items()
    ]
    return sorted(sizes, key=lambda field_size: field_size.size_bytes, reverse=True)
