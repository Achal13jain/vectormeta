from __future__ import annotations

from pathlib import Path

import pytest

from vectormeta.errors import InvalidInputError
from vectormeta.fixer import FixOptions, fix_records
from vectormeta.hydrate import hydrate_records
from vectormeta.io import write_sidecars


def test_hydrate_restores_sidecar_fields_to_metadata(tmp_path: Path) -> None:
    records = [{"id": "doc", "metadata": {"source": "paper.pdf", "chunk_text": "payload"}}]
    result = fix_records(
        records,
        FixOptions(
            target="custom",
            limit_bytes=1024,
            sidecar_dir=tmp_path / "sidecar",
            output_path=tmp_path / "ready.json",
        ),
    )
    write_sidecars(result.sidecars)

    hydrated = hydrate_records(
        result.cleaned_records,
        sidecar_dir=tmp_path / "sidecar",
        input_base_dir=tmp_path,
    )

    assert hydrated[0]["metadata"] == {"source": "paper.pdf", "chunk_text": "payload"}


def test_hydrate_can_restore_to_content_field(tmp_path: Path) -> None:
    records = [{"id": "doc", "metadata": {"source": "paper.pdf", "summary": "payload"}}]
    result = fix_records(
        records,
        FixOptions(
            target="custom",
            limit_bytes=1024,
            sidecar_dir=tmp_path / "sidecar",
            output_path=tmp_path / "ready.json",
        ),
    )
    write_sidecars(result.sidecars)

    hydrated = hydrate_records(
        result.cleaned_records,
        sidecar_dir=tmp_path / "sidecar",
        mode="content_field",
        content_field="payload",
        input_base_dir=tmp_path,
    )

    assert hydrated[0]["metadata"] == {"source": "paper.pdf"}
    assert hydrated[0]["payload"] == {"summary": "payload"}


def test_hydrate_rejects_sidecar_reference_outside_allowed_paths(tmp_path: Path) -> None:
    outside_path = tmp_path.parent / "outside-sidecar.json"
    outside_path.write_text('{"id":"doc","chunk_text":"secret"}\n', encoding="utf-8")
    records = [
        {
            "id": "doc",
            "metadata": {
                "source": "paper.pdf",
                "content_ref": str(outside_path.resolve()),
            },
        }
    ]

    with pytest.raises(InvalidInputError, match="allowed sidecar paths"):
        hydrate_records(
            records,
            sidecar_dir=tmp_path / "sidecar",
            input_base_dir=tmp_path,
        )


def test_hydrate_preserves_nested_sidecar_reference(tmp_path: Path) -> None:
    sidecar_dir = tmp_path / "sidecar"
    nested_dir = sidecar_dir / "subdir"
    nested_dir.mkdir(parents=True)
    (sidecar_dir / "doc.json").write_text(
        '{"id":"wrong","chunk_text":"wrong"}\n',
        encoding="utf-8",
    )
    (nested_dir / "doc.json").write_text(
        '{"id":"doc","chunk_text":"expected"}\n',
        encoding="utf-8",
    )
    records = [
        {
            "id": "doc",
            "metadata": {
                "source": "paper.pdf",
                "content_ref": "sidecar/subdir/doc.json",
            },
        }
    ]

    hydrated = hydrate_records(records, sidecar_dir=sidecar_dir)

    assert hydrated[0]["metadata"]["chunk_text"] == "expected"
