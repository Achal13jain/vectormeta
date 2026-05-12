from __future__ import annotations

import json

from vectormeta.sizing import field_sizes, metadata_size_bytes


def test_metadata_size_uses_utf8_compact_json() -> None:
    metadata = {"text": "hello 世界"}

    expected = len(
        json.dumps(metadata, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    )

    assert metadata_size_bytes(metadata) == expected
    assert metadata_size_bytes(metadata) != len(str(metadata))


def test_field_sizes_measure_top_level_nested_values() -> None:
    metadata = {
        "source": "paper.pdf",
        "nested": {"summary": "x" * 100, "tables": [{"a": 1, "b": "y" * 50}]},
    }

    sizes = field_sizes(metadata)

    assert sizes[0].field_name == "nested"
    assert sizes[0].size_bytes > sizes[1].size_bytes
    assert sizes[0].size_kb == sizes[0].size_bytes / 1024
