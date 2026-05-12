# Usage

`vectormeta` works with JSON arrays and newline-delimited JSON records.

## Scan

```bash
vectormeta scan chunks.json --target pinecone
```

Use JSON output in CI:

```bash
vectormeta scan chunks.json --target pinecone --format json
```

Use a custom limit:

```bash
vectormeta scan chunks.json --target custom --limit-kb 32
```

## Fix

```bash
vectormeta fix chunks.json --target pinecone --sidecar ./sidecar --out pinecone_ready.json
```

Move explicit fields:

```bash
vectormeta fix chunks.json \
  --target pinecone \
  --move-fields chunk_text,raw_html,summary \
  --keep-fields source,page,section,doc_id,chunk_id \
  --sidecar ./sidecar \
  --out pinecone_ready.json
```

Preview without writing:

```bash
vectormeta fix chunks.json --target pinecone --sidecar ./sidecar --out ready.json --dry-run
```

## Hydrate

```bash
vectormeta hydrate pinecone_ready.json --sidecar ./sidecar --out hydrated.json
```

To keep restored content outside metadata:

```bash
vectormeta hydrate pinecone_ready.json \
  --sidecar ./sidecar \
  --mode content_field \
  --content-field payload \
  --out hydrated.json
```

## Config

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
