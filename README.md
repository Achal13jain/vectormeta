# vectormeta

[![CI](https://github.com/Achal13jain/vectormeta/actions/workflows/ci.yml/badge.svg)](https://github.com/Achal13jain/vectormeta/actions/workflows/ci.yml)

Stop vector DB metadata limit errors before upsert.

`vectormeta` is an open-source Python CLI for finding oversized vector database
metadata before it breaks an ingestion pipeline. It scans JSON/JSONL vector records,
shows which metadata fields are responsible for size bloat, and can move heavy payloads
into local sidecar JSON files while keeping clean, filterable metadata in the vector DB
record.

The MVP is especially useful for Pinecone workflows, where metadata size limits are a
common source of upsert failures. It also supports Chroma, Qdrant, Weaviate, and custom
limits as conservative scanning policies.

## The Problem

Vector database metadata is tempting storage. It is easy to put everything there:

- chunk text
- raw HTML
- Markdown
- OCR output
- summaries
- tables
- nested extraction payloads
- full source documents

That works until a batch fails because one record carries too much metadata. The better
pattern is usually:

- Keep metadata small and filterable: `source`, `page`, `section`, `doc_id`, `tags`.
- Move large content somewhere else: object storage, a database, or sidecar files.
- Store a stable pointer such as `content_ref` in metadata.

`vectormeta` helps you do that before records reach your vector database.

## Features

- Scan JSON arrays and JSONL files.
- Measure metadata as compact UTF-8 JSON bytes, not `len(str(metadata))`.
- Report total records, target limit, oversized count, largest fields, and suggested
  fields to move.
- Exit non-zero in CI when oversized records are found.
- Move heavy fields into sidecar JSON files.
- Preserve record order and unknown record fields.
- Protect output and sidecar files from accidental overwrites.
- Sanitize sidecar filenames generated from record IDs.
- Hydrate records back from sidecars for debugging and migrations.
- Provide typed, testable core functions independent from Typer/Rich.

## Installation

From a local clone:

```bash
git clone https://github.com/Achal13jain/vectormeta.git
cd vectormeta
pip install -e ".[dev]"
```

After the package is published to PyPI:

```bash
pip install vectormeta
```

Check the CLI:

```bash
vectormeta --help
vectormeta --version
```

## Quickstart

Scan the included oversized example:

```bash
vectormeta scan examples/oversized_pinecone_records.json --target pinecone --no-fail
```

Fix it by moving heavy metadata fields into sidecars:

```bash
vectormeta fix examples/oversized_pinecone_records.json \
  --target pinecone \
  --sidecar examples/sidecar \
  --out examples/pinecone_ready.json \
  --overwrite
```

Hydrate the fixed records for local inspection:

```bash
vectormeta hydrate examples/pinecone_ready.json \
  --sidecar examples/sidecar \
  --out examples/hydrated.json \
  --overwrite
```

## Input Format

JSON array:

```json
[
  {
    "id": "doc_1_chunk_1",
    "values": [0.1, 0.2, 0.3],
    "metadata": {
      "source": "paper.pdf",
      "page": 1,
      "chunk_text": "large text..."
    }
  }
]
```

JSONL:

```jsonl
{"id":"doc_1","values":[0.1],"metadata":{"text":"large text..."}}
{"id":"doc_2","values":[0.2],"metadata":{"text":"large text..."}}
```

Records must include `id` or `_id` and a `metadata` object. Vector values are preserved
but not deeply validated.

## Scan

```bash
vectormeta scan chunks.json --target pinecone
```

Useful options:

```bash
vectormeta scan chunks.json \
  --target custom \
  --limit-kb 32 \
  --top 20 \
  --format json
```

Exit codes:

- `0`: all records fit, or `--no-fail` was used
- `1`: oversized records were found
- `2`: expected input, config, or usage error

This makes `scan` useful in CI:

```bash
vectormeta scan chunks.json --target pinecone --format json
```

## Fix

```bash
vectormeta fix chunks.json --target pinecone --sidecar ./sidecar --out pinecone_ready.json
```

Default fields moved to sidecars:

```text
text, chunk_text, content, page_content, raw_text, raw_html, html, markdown,
summary, tables, table_data, ocr_text, full_document, document_text, body
```

Default fields kept in vector DB metadata:

```text
doc_id, chunk_id, source, url, file_name, file_path, page, page_number,
section, title, author, created_at, updated_at, tags, category, language
```

Customize the policy:

```bash
vectormeta fix chunks.json \
  --target pinecone \
  --move-fields chunk_text,raw_html,summary \
  --keep-fields source,page,section,doc_id,chunk_id \
  --content-ref-field content_ref \
  --sidecar ./sidecar \
  --out pinecone_ready.json
```

Preview safely:

```bash
vectormeta fix chunks.json --target pinecone --sidecar ./sidecar --out ready.json --dry-run
```

`vectormeta` does not overwrite output files or sidecars unless `--overwrite` is passed.

## Before And After

Input record:

```json
{
  "id": "doc_123_chunk_4",
  "values": [0.1, 0.2],
  "metadata": {
    "source": "paper.pdf",
    "page": 12,
    "section": "Intro",
    "chunk_text": "very long text...",
    "summary": "long summary...",
    "raw_html": "<html>...</html>"
  }
}
```

Cleaned vector record:

```json
{
  "id": "doc_123_chunk_4",
  "values": [0.1, 0.2],
  "metadata": {
    "source": "paper.pdf",
    "page": 12,
    "section": "Intro",
    "content_ref": "sidecar/doc_123_chunk_4.json"
  }
}
```

Sidecar file:

```json
{
  "id": "doc_123_chunk_4",
  "chunk_text": "very long text...",
  "summary": "long summary...",
  "raw_html": "<html>...</html>"
}
```

When `--out` is provided, `content_ref` is written relative to the output file's parent
directory where possible. For example, `examples/pinecone_ready.json` plus
`examples/sidecar` produces refs like `sidecar/doc_123_chunk_4.json`.

## Hydrate

Hydrate restores sidecar payloads for debugging, migrations, or local inspection.

```bash
vectormeta hydrate pinecone_ready.json --sidecar ./sidecar --out hydrated.json
```

Restore sidecar data into a separate record field:

```bash
vectormeta hydrate pinecone_ready.json \
  --sidecar ./sidecar \
  --mode content_field \
  --content-field payload \
  --out hydrated.json
```

Hydration only resolves sidecar references inside the provided sidecar/input paths.

## Config File

`fix` can load a small YAML config:

```yaml
target: pinecone
limit_kb: 40
move:
  - chunk_text
  - raw_html
  - summary
keep:
  - doc_id
  - chunk_id
  - source
  - page
  - section
content_ref_field: content_ref
sidecar_dir: sidecar
```

Run:

```bash
vectormeta fix chunks.json --config vectormeta.yml --out pinecone_ready.json
```

CLI flags override config values.

## Target Limits

Show current presets:

```bash
vectormeta limits
```

MVP defaults:

| Target | Default | Meaning |
| --- | ---: | --- |
| `pinecone` | 40 KB | Main strict-limit target for this MVP |
| `chroma` | 256 KB | Advisory local/configurable policy |
| `qdrant` | 64 KB | Conservative advisory policy |
| `weaviate` | 64 KB | Conservative advisory policy |
| `custom` | none | Requires `--limit-kb` |

Limits and service behavior can change. Verify official vector database docs before
using any preset as a production guarantee.

## How To Know It Works

For local confidence:

```bash
pip install -e ".[dev]"
python -m pytest
ruff check .
ruff format --check .
mypy vectormeta
python -m build
vectormeta scan examples/oversized_pinecone_records.json --target pinecone --no-fail
vectormeta fix examples/oversized_pinecone_records.json --target pinecone --sidecar examples/sidecar --out examples/pinecone_ready.json --overwrite
vectormeta hydrate examples/pinecone_ready.json --sidecar examples/sidecar --out examples/hydrated.json --overwrite
```

For confidence that it works for other people:

- CI runs tests, linting, formatting checks, type checks, and package builds on Python
  3.10, 3.11, and 3.12.
- The package installs through `pip install -e ".[dev]"`.
- The CLI entry point is tested through Typer's CLI runner.
- The README quickstart uses committed example files.
- `python -m build` verifies the source distribution and wheel can be built.

See [docs/testing.md](docs/testing.md) for a fuller checklist.

## Python API

Core logic can be used without the CLI:

```python
from pathlib import Path

from vectormeta.analyzer import analyze_records
from vectormeta.io import read_records
from vectormeta.limits import resolve_limit_bytes

records, _ = read_records(Path("chunks.json"))
limit = resolve_limit_bytes("pinecone")
report = analyze_records(records, target="pinecone", limit_bytes=limit)

print(report.oversized_count)
```

## Documentation

- [Usage](docs/usage.md)
- [Examples](docs/examples.md)
- [Architecture](docs/architecture.md)
- [Vector database notes](docs/vector-db-notes.md)
- [Testing checklist](docs/testing.md)

## Security And Privacy

`vectormeta` processes local files and writes local sidecar JSON. It does not upload
records anywhere. Sidecar files can contain sensitive source content, so treat them as
application data: keep them out of public repositories unless they are test fixtures.

Report security issues privately. See [SECURITY.md](SECURITY.md).

## Limitations

- Local JSON sidecars only; no S3, SQLite, or object-store backend yet.
- Input support is JSON arrays and JSONL records.
- Vector values are preserved but not deeply validated.
- Non-Pinecone target limits are conservative advisory defaults, not vendor claims.
- The fixer is policy-based; review cleaned outputs before using them in production.

## Roadmap

Planned ideas include:

- S3 sidecar backend
- SQLite sidecar backend
- LangChain `Document` adapter
- LlamaIndex `Node` adapter
- Pinecone upsert wrapper
- GitHub Action for metadata checks
- HTML report output

See [ROADMAP.md](ROADMAP.md).

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) and run the
local checks before opening a pull request.

## License

MIT. See [LICENSE](LICENSE).
