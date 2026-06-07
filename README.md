# vectormeta

[![CI](https://github.com/Achal13jain/vectormeta/actions/workflows/ci.yml/badge.svg)](https://github.com/Achal13jain/vectormeta/actions/workflows/ci.yml)
[![Pages](https://github.com/Achal13jain/vectormeta/actions/workflows/pages.yml/badge.svg)](https://github.com/Achal13jain/vectormeta/actions/workflows/pages.yml)

Stop vector DB metadata limit errors before upsert.

Website: <https://achal13jain.github.io/vectormeta/>

`vectormeta` is a Python CLI package for detecting and fixing oversized metadata in
vector database records. It scans JSON or JSONL vector records, reports the largest
metadata fields, and can move heavy content fields into local JSON sidecar files while
leaving clean filterable metadata in the vector database payload.

The project is designed for developers preparing records for Pinecone, Chroma, Qdrant,
Weaviate, or a custom metadata policy. Pinecone is the clearest strict-limit target in
the MVP. Other targets use conservative advisory limits that should be adjusted for each
deployment.

## Why This Exists

Vector database metadata should usually stay small and filterable:

- `source`
- `page`
- `section`
- `doc_id`
- `chunk_id`
- `tags`
- `language`

Large payloads such as full chunk text, raw HTML, Markdown, OCR text, summaries, tables,
or full documents can push records over service metadata limits and make upserts fail.
`vectormeta` catches that problem before upload and can rewrite records into a safer
shape:

```text
vector record metadata -> small filterable fields + content_ref
sidecar JSON file      -> large text, HTML, tables, summaries, payloads
```

## Features

- Scan JSON arrays and newline-delimited JSON records.
- Measure metadata using compact UTF-8 JSON bytes.
- Report oversized records, largest fields, byte counts, KB counts, and suggested moves.
- Exit with code `1` when oversized records are found, which makes scans useful in CI.
- Move heavy metadata fields into sidecar JSON files.
- Preserve unknown record fields and original record order.
- Sanitize sidecar filenames derived from record IDs.
- Protect output files and sidecars from accidental overwrite.
- Hydrate records back from sidecar references for debugging and migrations.
- Keep core logic independent from Typer and Rich so it can be tested and reused.

## Tech Stack

- Python 3.10+
- Typer for the CLI
- Rich for human-readable terminal reports
- Pydantic for YAML config validation
- PyYAML for config loading
- Pytest for tests
- Ruff for linting and formatting
- Mypy for strict type checks
- Setuptools and `python -m build` for packaging

## Installation

Clone and install locally:

```bash
git clone https://github.com/Achal13jain/vectormeta.git
cd vectormeta
pip install -e ".[dev]"
```

Check the CLI:

```bash
vectormeta --help
vectormeta --version
python -m vectormeta --help
```

After the package is published to PyPI, the intended install command is:

```bash
pip install vectormeta
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

Each record must contain:

- `id` or `_id`
- `metadata` as a JSON object

Vector fields such as `values`, `vector`, or `embedding` are preserved but not deeply
validated by the MVP.

## Quickstart

Scan the included oversized Pinecone example:

```bash
vectormeta scan examples/oversized_pinecone_records.json --target pinecone --no-fail
```

Fix the records:

```bash
vectormeta fix examples/oversized_pinecone_records.json \
  --target pinecone \
  --sidecar examples/sidecar \
  --out examples/pinecone_ready.json \
  --overwrite
```

Verify the cleaned file now fits the Pinecone-sized policy:

```bash
vectormeta scan examples/pinecone_ready.json --target pinecone --no-fail
```

Hydrate records for local inspection:

```bash
vectormeta hydrate examples/pinecone_ready.json \
  --sidecar examples/sidecar \
  --out examples/hydrated.json \
  --overwrite
```

## Commands

### Scan

```bash
vectormeta scan chunks.json --target pinecone
```

Useful options:

- `--target pinecone|chroma|qdrant|weaviate|custom`
- `--limit-kb <number>` for custom or overridden limits
- `--top <number>` for the largest oversized records to show
- `--format table|json`
- `--no-fail` to exit `0` even when oversized records are found

Exit codes:

- `0`: all records fit, or `--no-fail` was passed
- `1`: oversized records were found
- `2`: expected user-facing input, config, target, or overwrite error

### Fix

```bash
vectormeta fix chunks.json --target pinecone --sidecar ./sidecar --out pinecone_ready.json
```

Move explicit fields:

```bash
vectormeta fix chunks.json \
  --target pinecone \
  --move-fields chunk_text,raw_html,summary \
  --keep-fields source,page,section,doc_id,chunk_id \
  --content-ref-field content_ref \
  --sidecar ./sidecar \
  --out pinecone_ready.json
```

Preview without writing:

```bash
vectormeta fix chunks.json --target pinecone --sidecar ./sidecar --out ready.json --dry-run
```

`fix` does not overwrite files unless `--overwrite` is passed.

If your input metadata already contains `content_ref`, choose another reference field:

```bash
vectormeta fix chunks.json \
  --target pinecone \
  --content-ref-field vectormeta_content_ref \
  --sidecar ./sidecar \
  --out pinecone_ready.json
```

### Hydrate

```bash
vectormeta hydrate pinecone_ready.json --sidecar ./sidecar --out hydrated.json
```

Hydrate sidecar content into a separate record field:

```bash
vectormeta hydrate pinecone_ready.json \
  --sidecar ./sidecar \
  --mode content_field \
  --content-field payload \
  --out hydrated.json
```

### Limits

```bash
vectormeta limits
```

Current MVP defaults:

| Target | Default | Meaning |
| --- | ---: | --- |
| `pinecone` | 40 KB | Primary strict-limit target for this MVP |
| `chroma` | 256 KB | Advisory local/configurable policy |
| `qdrant` | 64 KB | Conservative advisory policy |
| `weaviate` | 64 KB | Conservative advisory policy |
| `custom` | none | Requires `--limit-kb` |

Limits and provider behavior can change. Verify official vector database documentation
before treating any preset as a production guarantee.

## How Metadata Reduction Works

`vectormeta` sizes metadata exactly as compact UTF-8 JSON:

```python
json.dumps(metadata, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
```

The fixer reduces metadata in this order:

1. Move explicit `--move-fields`, if provided.
2. Otherwise move known heavy fields such as `text`, `chunk_text`, `raw_html`,
   `markdown`, `summary`, `tables`, and `ocr_text`.
3. If metadata is still above the limit, move the largest non-keep fields one at a
   time until the record fits.
4. Keep fields such as `source`, `page`, `doc_id`, and `tags` are preserved unless the
   record cannot fit without moving them.
5. When fields are moved, metadata receives a `content_ref`, and moved fields are
   written to a sidecar JSON payload.

The logic is covered by tests for Unicode byte sizing, nested metadata sizing,
JSON/JSONL input, fixer output, sidecar overwrite protection, hydration, and CLI exit
codes. See [docs/metadata-reduction.md](docs/metadata-reduction.md).

## Local Verification

Run the same checks used in CI:

```bash
python -m pytest
ruff check .
ruff format --check .
mypy vectormeta
python -m build
```

Run the acceptance workflow:

```bash
vectormeta scan examples/oversized_pinecone_records.json --target pinecone --no-fail
vectormeta fix examples/oversized_pinecone_records.json --target pinecone --sidecar examples/sidecar --out examples/pinecone_ready.json --overwrite
vectormeta scan examples/pinecone_ready.json --target pinecone --no-fail
vectormeta hydrate examples/pinecone_ready.json --sidecar examples/sidecar --out examples/hydrated.json --overwrite
```

Expected result:

- The original example reports one oversized record.
- The fixed output reports zero oversized records.
- Sidecar files are created under `examples/sidecar`.
- Hydration restores moved fields for inspection.

## Documentation

- [Project website](https://achal13jain.github.io/vectormeta/)
- [Architecture overview](docs/architecture.md)
- [Metadata reduction logic](docs/metadata-reduction.md)
- [Usage guide](docs/usage.md)
- [Testing checklist](docs/testing.md)
- [Vector database notes](docs/vector-db-notes.md)

## Limitations

- Local JSON sidecars only. Keep the cleaned output file and sidecar directory together;
  the MVP does not provide an atomic database-backed sidecar store.
- Sidecars are one file per changed record. The MVP does not deduplicate repeated fields
  such as shared `raw_html` across chunks from the same document.
- Input support is JSON arrays and JSONL records, but files are currently read into
  memory. Streaming JSONL scan/fix is planned for larger embedding datasets.
- Vector values are preserved but not deeply validated.
- Non-Pinecone target limits are conservative advisory defaults, not vendor claims.
- The fixer is policy-based; review cleaned outputs before production ingestion.

## Roadmap

Planned ideas include:

- SQLite sidecar backend
- Content-addressed sidecar deduplication
- Streaming JSONL scan/fix
- S3 sidecar backend
- LangChain `Document` adapter
- LlamaIndex `Node` adapter
- Pinecone upsert wrapper
- GitHub Action for metadata checks
- HTML report output

See [ROADMAP.md](ROADMAP.md).

## License

MIT. See [LICENSE](LICENSE).
