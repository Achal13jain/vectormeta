# vectormeta

[![CI](https://github.com/Achal13jain/vectormeta/actions/workflows/ci.yml/badge.svg)](https://github.com/Achal13jain/vectormeta/actions/workflows/ci.yml)

Stop vector DB metadata limit errors before upsert.

`vectormeta` is a Python CLI package that scans vector records, explains which metadata
fields are too large, and can move heavy payload fields into sidecar JSON files before
you upload records to Pinecone, Chroma, Qdrant, Weaviate, or similar vector databases.

## Why

Vector database metadata should usually stay small and filterable: source, page, title,
URL, tags, category, language, and other fields you query with filters.

Large content belongs somewhere else. Full chunk text, raw HTML, Markdown, OCR output,
tables, summaries, and full documents can push records over service metadata limits and
make upserts fail late in a pipeline. Pinecone is the clearest target for this MVP
because metadata size limits are strict. For other vector databases, `vectormeta`
provides conservative advisory scanning and cleanup; verify current official docs for
your deployment.

## Installation

From a local clone:

```bash
pip install -e ".[dev]"
```

After publishing, the intended install will be:

```bash
pip install vectormeta
```

## Quickstart

Scan a JSON or JSONL file:

```bash
vectormeta scan examples/oversized_pinecone_records.json --target pinecone
```

Fix records by moving heavy metadata into sidecar files:

```bash
vectormeta fix examples/oversized_pinecone_records.json \
  --target pinecone \
  --sidecar examples/sidecar \
  --out examples/pinecone_ready.json
```

Hydrate cleaned records for debugging or migration checks:

```bash
vectormeta hydrate examples/pinecone_ready.json \
  --sidecar examples/sidecar \
  --out examples/hydrated.json
```

## Scan

```bash
vectormeta scan chunks.json --target pinecone
```

Options:

- `--target pinecone|chroma|qdrant|weaviate|custom`
- `--limit-kb <number>` to override the target default
- `--top N` to control how many oversized records are shown
- `--format table|json`
- `--no-fail` to exit 0 even when oversized records are found

Exit codes:

- `0` when all records fit, or when `--no-fail` is passed
- `1` when oversized records are found
- `2` for expected usage/input errors

## Fix

```bash
vectormeta fix chunks.json --target pinecone --sidecar ./sidecar --out pinecone_ready.json
```

The fixer preserves record order and unknown record fields. It moves explicit
`--move-fields` first, otherwise default heavy field names, and then the largest
non-keep metadata fields until the record fits. Keep fields are moved only when the
record cannot otherwise be reduced under the configured limit.

Default fields to move include `text`, `chunk_text`, `content`, `page_content`,
`raw_text`, `raw_html`, `html`, `markdown`, `summary`, `tables`, `table_data`,
`ocr_text`, `full_document`, `document_text`, and `body`.

Default fields to keep include `doc_id`, `chunk_id`, `source`, `url`, `file_name`,
`file_path`, `page`, `page_number`, `section`, `title`, `author`, `created_at`,
`updated_at`, `tags`, `category`, and `language`.

`content_ref` values are stored relative to the output file's parent directory when
`--out` is provided. If no output path is available, refs are relative to the current
working directory.

## Before And After

Before:

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

After:

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

Sidecar:

```json
{
  "id": "doc_123_chunk_4",
  "chunk_text": "very long text...",
  "summary": "long summary...",
  "raw_html": "<html>...</html>"
}
```

## Hydrate

```bash
vectormeta hydrate pinecone_ready.json --sidecar ./sidecar --out hydrated.json
```

Modes:

- `--mode metadata` merges sidecar fields back into `metadata`
- `--mode content_field --content-field payload` stores sidecar fields on the record
  under `payload`

## Supported Targets

Run:

```bash
vectormeta limits
```

MVP presets:

- `pinecone`: 40 KB default metadata limit
- `chroma`: advisory configurable/local scan default
- `qdrant`: conservative advisory default
- `weaviate`: conservative advisory default
- `custom`: requires `--limit-kb`

Limits can change. Always verify official vector database documentation for production
systems.

## Development

```bash
pip install -e ".[dev]"
python -m pytest
ruff check .
ruff format .
mypy vectormeta
```

## Limitations

- Local JSON sidecars only; no S3, SQLite, or object store backend yet.
- Input support is JSON arrays and JSONL records.
- Vector values are preserved but not deeply validated.
- Non-Pinecone target limits are conservative advisory defaults, not vendor claims.

## Roadmap

See [ROADMAP.md](ROADMAP.md).

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).
