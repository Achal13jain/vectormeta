"""Record analysis logic."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from vectormeta.errors import InvalidInputError
from vectormeta.models import RecordAnalysis, ScanReport
from vectormeta.sizing import field_sizes, metadata_size_bytes


def get_record_id(record: Mapping[str, Any]) -> str:
    """Return a vector record id from id or _id."""
    record_id = record.get("id", record.get("_id"))
    if record_id is None or str(record_id) == "":
        raise InvalidInputError("Each record must contain a non-empty 'id' or '_id'.")
    return str(record_id)


def get_metadata(record: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return metadata from a vector record."""
    metadata = record.get("metadata")
    if not isinstance(metadata, Mapping):
        record_id = record.get("id", record.get("_id", "<unknown>"))
        raise InvalidInputError(f"Record '{record_id}' must contain a metadata object.")
    return metadata


def analyze_record(record: Mapping[str, Any], limit_bytes: int) -> RecordAnalysis:
    """Analyze metadata size for a single vector record."""
    metadata = get_metadata(record)
    return RecordAnalysis(
        record_id=get_record_id(record),
        metadata_size_bytes=metadata_size_bytes(metadata),
        limit_bytes=limit_bytes,
        largest_fields=field_sizes(metadata),
    )


def analyze_records(
    records: Iterable[Mapping[str, Any]],
    target: str,
    limit_bytes: int,
) -> ScanReport:
    """Analyze vector records for oversized metadata."""
    return ScanReport(
        target=target,
        limit_bytes=limit_bytes,
        records=[analyze_record(record, limit_bytes) for record in records],
    )
