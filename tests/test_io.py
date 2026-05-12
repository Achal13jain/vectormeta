from __future__ import annotations

from pathlib import Path

import pytest

from vectormeta.errors import OutputExistsError
from vectormeta.io import read_records, write_records


def test_read_records_supports_json_array(tmp_path: Path) -> None:
    path = tmp_path / "records.json"
    path.write_text('[{"id":"a","metadata":{"text":"one"}}]', encoding="utf-8")

    records, input_format = read_records(path)

    assert input_format == "json"
    assert records == [{"id": "a", "metadata": {"text": "one"}}]


def test_read_records_supports_jsonl(tmp_path: Path) -> None:
    path = tmp_path / "records.jsonl"
    path.write_text(
        '{"id":"a","metadata":{"text":"one"}}\n{"id":"b","metadata":{"text":"two"}}\n',
        encoding="utf-8",
    )

    records, input_format = read_records(path)

    assert input_format == "jsonl"
    assert [record["id"] for record in records] == ["a", "b"]


def test_write_records_protects_existing_output(tmp_path: Path) -> None:
    path = tmp_path / "out.json"
    path.write_text("[]\n", encoding="utf-8")

    with pytest.raises(OutputExistsError):
        write_records([], path, "json", overwrite=False)
