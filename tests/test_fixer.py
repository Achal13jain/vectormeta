from __future__ import annotations

from pathlib import Path

import pytest

from vectormeta.errors import SidecarConflictError
from vectormeta.fixer import FixOptions, fix_records, sanitize_sidecar_filename
from vectormeta.io import write_sidecars


def test_fix_records_moves_heavy_fields_to_sidecar(tmp_path: Path) -> None:
    records = [
        {
            "id": "doc/123 chunk",
            "values": [0.1, 0.2],
            "metadata": {
                "source": "paper.pdf",
                "page": 12,
                "section": "Intro",
                "chunk_text": "x" * 200,
                "raw_html": "<p>large</p>",
            },
            "unknown": "preserved",
        }
    ]

    result = fix_records(
        records,
        FixOptions(
            target="pinecone",
            limit_bytes=40 * 1024,
            sidecar_dir=tmp_path / "sidecar",
            output_path=tmp_path / "ready.json",
        ),
    )

    cleaned = result.cleaned_records[0]
    metadata = cleaned["metadata"]
    assert cleaned["unknown"] == "preserved"
    assert metadata == {
        "source": "paper.pdf",
        "page": 12,
        "section": "Intro",
        "content_ref": "sidecar/doc_123_chunk.json",
    }
    assert result.sidecars[0].payload == {
        "id": "doc/123 chunk",
        "chunk_text": "x" * 200,
        "raw_html": "<p>large</p>",
    }


def test_fix_records_moves_largest_non_keep_fields_until_under_limit(tmp_path: Path) -> None:
    records = [
        {
            "id": "doc",
            "metadata": {
                "source": "paper.pdf",
                "notes": "n" * 120,
                "extra": "e" * 80,
            },
        }
    ]

    result = fix_records(
        records,
        FixOptions(
            target="custom",
            limit_bytes=80,
            sidecar_dir=tmp_path / "sidecar",
            output_path=tmp_path / "ready.json",
            move_fields=(),
            keep_fields=("source",),
        ),
    )

    metadata = result.cleaned_records[0]["metadata"]
    assert "source" in metadata
    assert "notes" not in metadata
    assert "extra" not in metadata
    assert result.sidecars[0].payload["notes"] == "n" * 120


def test_sanitize_sidecar_filename_removes_unsafe_characters() -> None:
    assert sanitize_sidecar_filename("../doc/1?") == "doc_1"


def test_write_sidecars_protects_existing_files(tmp_path: Path) -> None:
    records = [{"id": "doc", "metadata": {"chunk_text": "payload"}}]
    result = fix_records(
        records,
        FixOptions(target="custom", limit_bytes=1024, sidecar_dir=tmp_path, output_path=tmp_path / "out"),
    )
    write_sidecars(result.sidecars)

    with pytest.raises(SidecarConflictError):
        write_sidecars(result.sidecars)
