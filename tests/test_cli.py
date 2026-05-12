from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from vectormeta.cli import app


def test_scan_exits_one_when_oversized(tmp_path: Path) -> None:
    input_path = tmp_path / "records.json"
    input_path.write_text(
        '[{"id":"doc","metadata":{"text":"' + ("x" * 200) + '"}}]',
        encoding="utf-8",
    )
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["scan", str(input_path), "--target", "custom", "--limit-kb", "0.05"],
    )

    assert result.exit_code == 1
    assert "Oversized records" in result.output


def test_scan_no_fail_exits_zero_when_oversized(tmp_path: Path) -> None:
    input_path = tmp_path / "records.json"
    input_path.write_text(
        '[{"id":"doc","metadata":{"text":"' + ("x" * 200) + '"}}]',
        encoding="utf-8",
    )
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["scan", str(input_path), "--target", "custom", "--limit-kb", "0.05", "--no-fail"],
    )

    assert result.exit_code == 0
    assert "Oversized records" in result.output


def test_fix_and_hydrate_cli_round_trip(tmp_path: Path) -> None:
    input_path = tmp_path / "records.json"
    ready_path = tmp_path / "ready.json"
    hydrated_path = tmp_path / "hydrated.json"
    sidecar_path = tmp_path / "sidecar"
    input_path.write_text(
        '[{"id":"doc","values":[0.1],"metadata":{"source":"paper.pdf","chunk_text":"payload"}}]',
        encoding="utf-8",
    )
    runner = CliRunner()

    fix_result = runner.invoke(
        app,
        [
            "fix",
            str(input_path),
            "--target",
            "pinecone",
            "--sidecar",
            str(sidecar_path),
            "--out",
            str(ready_path),
        ],
    )
    hydrate_result = runner.invoke(
        app,
        [
            "hydrate",
            str(ready_path),
            "--sidecar",
            str(sidecar_path),
            "--out",
            str(hydrated_path),
        ],
    )

    assert fix_result.exit_code == 0
    assert hydrate_result.exit_code == 0
    assert ready_path.exists()
    assert (sidecar_path / "doc.json").exists()
    assert "chunk_text" in hydrated_path.read_text(encoding="utf-8")
