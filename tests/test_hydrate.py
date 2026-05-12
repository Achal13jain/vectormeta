from __future__ import annotations

from pathlib import Path

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
