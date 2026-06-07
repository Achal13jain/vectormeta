# Metadata Reduction Logic

This document explains exactly how `vectormeta` detects oversized metadata and reduces
record size.

## Size Measurement

Metadata size is measured as compact UTF-8 JSON bytes:

```python
json.dumps(metadata, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
```

This is implemented in `vectormeta/sizing.py`.

The tool does not use `len(str(metadata))` because Python string representations are not
the payload that vector database clients serialize. Compact JSON byte sizing is more
predictable and handles Unicode correctly.

## Field Size Measurement

Field sizes are measured at the top-level metadata key:

```python
{"chunk_text": "..."}
{"raw_html": "..."}
{"nested_payload": {"tables": [...], "summary": "..."}}
```

Nested values are not split into subpaths. A nested object is measured as the serialized
JSON value of its top-level field. This keeps reports stable and makes move decisions
simple for an MVP.

## Scan Logic

`vectormeta scan` performs this flow:

1. Read records from JSON or JSONL.
2. Require each record to contain `id` or `_id`.
3. Require each record to contain a `metadata` object.
4. Resolve the target metadata limit.
5. Measure total metadata bytes.
6. Measure top-level field sizes.
7. Mark records as oversized when `metadata_size_bytes > limit_bytes`.
8. Render table output or stable JSON output.

## Fix Logic

`vectormeta fix` performs this flow for each record:

1. Copy the record so unknown fields are preserved.
2. Copy metadata into a mutable dictionary.
3. Choose move fields:
   - Explicit `--move-fields`, if provided.
   - Otherwise the built-in heavy field list.
4. Move matching fields from metadata into a sidecar payload.
5. Add `content_ref` only when at least one field is moved.
6. Recalculate metadata size.
7. If the record is still oversized, move the largest non-keep fields one at a time.
8. If the record is still oversized and keep fields are the only remaining candidates,
   move keep fields with a warning.
9. If the record still cannot fit, return a warning for that record.
10. Return cleaned records, sidecar payloads, and warnings.

Default move fields:

```text
text, chunk_text, content, page_content, raw_text, raw_html, html, markdown,
summary, tables, table_data, ocr_text, full_document, document_text, body
```

Default keep fields:

```text
doc_id, chunk_id, source, url, file_name, file_path, page, page_number,
section, title, author, created_at, updated_at, tags, category, language
```

## Sidecar Safety

Sidecar behavior is designed to avoid common filesystem mistakes:

- Sidecar filenames are sanitized from record IDs.
- Duplicate sidecar filenames get deterministic suffixes.
- Existing sidecar files are not overwritten unless `--overwrite` is passed.
- Output files are not overwritten unless `--overwrite` is passed.
- `content_ref` is relative to the output file's parent directory when possible.

## Hydration Logic

`vectormeta hydrate` reads `content_ref`, loads the matching sidecar JSON file, and then
either:

- merges sidecar fields back into metadata, or
- writes sidecar fields to a separate record field such as `payload`.

Hydration removes `content_ref` after restoring the payload.

Sidecar references are resolved only inside the provided sidecar directory or input base
directory. This reduces path traversal risk.

## Correctness Checks

The test suite covers:

- Unicode byte sizing.
- Nested metadata field sizing.
- Oversized scan reporting.
- JSON array input.
- JSONL input.
- Fixer sidecar output.
- Largest non-keep field movement.
- Unsafe sidecar filename sanitization.
- Sidecar overwrite protection.
- Hydration into metadata.
- Hydration into a separate content field.
- Rejection of sidecar references outside allowed paths.
- CLI scan exit codes.
- CLI fix and hydrate round trip.

The local acceptance workflow also verifies that the included oversized example becomes
small enough after fixing:

```bash
vectormeta scan examples/oversized_pinecone_records.json --target pinecone --no-fail
vectormeta fix examples/oversized_pinecone_records.json --target pinecone --sidecar examples/sidecar --out examples/pinecone_ready.json --overwrite
vectormeta scan examples/pinecone_ready.json --target pinecone --no-fail
```

Expected result: the first scan reports an oversized record, and the second scan reports
zero oversized records.
