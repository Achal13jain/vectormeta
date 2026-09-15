# Troubleshooting Guide

This guide helps diagnose and resolve common errors and symptoms encountered when using the `vectormeta` CLI.

For command syntax and options, see the [Usage Guide](usage.md). For provider-specific behavior, see [Vector Database Notes](vector-db-notes.md).

---

## Quick Diagnostic Commands

Before troubleshooting specific errors, run these non-destructive diagnostics:

```bash
# Check installed CLI version
vectormeta --version

# View built-in presets and limits
vectormeta limits

# Test scan without writing files or failing CI
vectormeta scan chunks.json --target pinecone --no-fail

# Preview fixer modifications without writing outputs
vectormeta fix chunks.json --target pinecone --sidecar ./sidecar --out ready.json --dry-run
```

---

## Input Format and Parsing Errors

### Symptom: `InvalidInputError: Expected a JSON list of records or JSONL records in <path>; got a single object`

- **Cause:** The input file contains a single JSON object (`{...}`) instead of an array of vector records or newline-delimited JSON.
- **Resolution:**
  - If the file represents a single vector record, wrap it in square brackets: `[{...}]`.
  - If the file is newline-delimited JSON (JSONL), ensure each record is on its own line and verify the first character is `{`.
  - Run `vectormeta scan input.json --target pinecone` to verify the structure.

### Symptom: `InvalidInputError: Invalid JSONL at <path>:<line>`

- **Cause:** A specific line in your JSONL file contains invalid JSON syntax (e.g., trailing comma, unquoted key, or truncated line).
- **Resolution:**
  - Inspect the exact line number referenced in the error message.
  - Verify each line is an independent, valid JSON object formatted in compact UTF-8.
  - Test the stream using `vectormeta scan chunks.jsonl --stream --no-fail` to isolate problematic records.

### Symptom: `InvalidInputError: Input file is empty: <path>`

- **Cause:** The specified file is zero bytes or contains only whitespace.
- **Resolution:**
  - Check your upstream ingestion or extraction pipeline to ensure vector records are being written before invoking `vectormeta`.

### Symptom: Memory exhaustion or slow performance on large datasets

- **Cause:** Using standard array-based scanning or fixing on multi-gigabyte JSON files loads the entire document into memory.
- **Resolution:**
  - Convert your dataset to JSONL format (one record per line).
  - Use the `--stream` flag with `scan`, `validate`, or `fix`:
    ```bash
    vectormeta scan chunks.jsonl --target pinecone --stream --no-fail
    vectormeta validate chunks.jsonl --target pinecone --stream --no-fail
    vectormeta fix chunks.jsonl --target pinecone --stream --format jsonl --sidecar-store sqlite --sidecar sidecars.sqlite --out ready.jsonl
    ```

---

## Target and Limit Configuration

### Symptom: `UnsupportedTargetError: Target 'custom' requires --limit-kb`

- **Cause:** `--target custom` was specified without declaring the required metadata byte ceiling.
- **Resolution:**
  - Pass the `--limit-kb` option with your target threshold:
    ```bash
    vectormeta scan chunks.json --target custom --limit-kb 32
    vectormeta fix chunks.json --target custom --limit-kb 32 --sidecar ./sidecar --out ready.json
    ```

### Symptom: `UnsupportedTargetError: Unsupported target '<name>'`

- **Cause:** The specified target name does not match any recognized preset.
- **Resolution:**
  - Valid targets are `pinecone`, `chroma`, `qdrant`, `weaviate`, and `custom`.
  - Check available presets by running `vectormeta limits`.

### Advisory Warnings for Non-Pinecone Providers

- **Symptom:** The CLI emits an advisory warning (e.g., `Chroma/Qdrant/Weaviate uses an advisory metadata limit preset...`).
- **Explanation:** Pinecone has a strict 40 KB metadata limit. Other vector databases (such as Chroma, Qdrant, and Weaviate) are often self-hosted or cluster-configurable; `vectormeta` uses conservative advisory presets to help catch runaway metadata early. These presets are not vendor guarantees.
- **Resolution:**
  - If your deployment supports larger metadata, override the default using `--limit-kb <number>`.
  - See [Vector Database Notes](vector-db-notes.md) for full context on provider limits.

---

## Overwrite Protection and File Collisions

### Symptom: `OutputExistsError: Output file already exists: <path>`

- **Cause:** `vectormeta fix` and `vectormeta hydrate` protect existing files from accidental overwrites.
- **Resolution:**
  - To overwrite the existing file intentionally, add the `--overwrite` flag:
    ```bash
    vectormeta fix chunks.json --target pinecone --sidecar ./sidecar --out ready.json --overwrite
    ```
  - Alternatively, specify a new output destination using `--out <new_path>`.

### Symptom: `SidecarConflictError: Sidecar file already exists with different contents: <path>`

- **Cause:** When using default JSON file sidecars (`--sidecar-store json`), an existing sidecar file shares the record ID but has different payload contents, indicating an ID clash or rerun against an existing folder.
- **Resolution:**
  - Point `--sidecar` to an empty directory for the new run: `--sidecar ./sidecars_run2`.
  - Or switch to content-addressed storage (`--sidecar-store file` or `--sidecar-store sqlite`), which hashes payload contents to prevent clashes:
    ```bash
    vectormeta fix chunks.json --target pinecone --sidecar-store sqlite --sidecar sidecars.sqlite --out ready.json
    ```

---

## Content Reference (`content_ref`) Collisions

### Symptom: Existing metadata attributes overwritten by `content_ref`

- **Cause:** When moving heavy fields into a sidecar, `vectormeta fix` inserts a reference key named `content_ref` into the record's metadata. If your source records already use `content_ref` for another purpose, that field would collide.
- **Resolution:**
  - Use `--content-ref-field` to configure a distinct reference key:
    ```bash
    vectormeta fix chunks.json \
      --target pinecone \
      --content-ref-field vectormeta_sidecar_ref \
      --sidecar ./sidecar \
      --out ready.json
    ```

---

## Sidecar Storage and Hydration Issues

### Symptom: Missing sidecars or broken references during `hydrate`

- **Cause:** `vectormeta hydrate` cannot locate the external payload referenced in `content_ref`. This commonly occurs when sidecar directories are moved, deleted, or relative paths do not resolve.
- **Resolution:**
  - Verify the path passed to `--sidecar` matches the location where sidecars were written during `fix`:
    ```bash
    vectormeta hydrate ready.json --sidecar ./sidecar --out hydrated.json
    ```
  - Keep cleaned JSON records and their sidecar directory or SQLite database together in the same storage layout.

### Symptom: Store backend mismatch during hydration

- **Cause:** The records were fixed using `--sidecar-store sqlite` or `--sidecar-store file`, but `hydrate` was called with default JSON storage (or vice versa).
- **Resolution:**
  - Match the `--sidecar-store` and `--sidecar` parameters used during the fix:
    ```bash
    vectormeta hydrate ready.json \
      --sidecar-store sqlite \
      --sidecar vectormeta-sidecars.sqlite \
      --out hydrated.json
    ```

---

## Preflight Validation Failures

`vectormeta validate` acts as a preflight linter before upsert.

### CLI Exit Codes

- `0`: All checks passed, or `--no-fail` was supplied.
- `1`: Validation errors detected (e.g., oversized records, invalid metadata types, dimension mismatches).
- `2`: CLI usage, configuration, or input path error.

### Symptom: Record ID Validation Errors

- **Cause:** Records have missing, empty, or duplicate `id` fields.
- **Resolution:**
  - Ensure every record dictionary has a non-empty string `id` (or `_id`).
  - Eliminate duplicate record IDs in the input dataset before upsert.

### Symptom: Vector Dimension Mismatch

- **Cause:** Vector lengths differ across records or do not match the expected `--dim` argument.
- **Resolution:**
  - Specify the expected embedding dimension: `vectormeta validate chunks.json --dim 1536`.
  - Check embedding generation to ensure all vectors match your model's output dimensionality.

### Symptom: Pinecone Schema Violations

- **Cause:** Pinecone enforces strict constraints on metadata fields:
  - Keys must be strings and must not start with `$`.
  - Values must be strings, finite numbers, booleans, or lists of strings.
  - Values cannot be `null` or nested dictionaries / objects.
- **Resolution:**
  - Review the validation error output for specific field names and record IDs.
  - Flatten nested dictionaries into dot-delimited string keys or move them to sidecars using `--move-fields`.
  - Filter or serialize `null` values before validation.
