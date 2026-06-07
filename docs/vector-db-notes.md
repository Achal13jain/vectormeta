# Vector Database Notes

`vectormeta` is intentionally careful about vector database limit claims.

## Pinecone

Pinecone is the primary MVP target. This tool uses a 40 KB default metadata limit for
Pinecone scans and fixes. Users should still verify current official Pinecone
documentation for production systems.

## Chroma

Chroma is often local or deployment-configurable. `vectormeta` uses an advisory scan
default so teams can catch large payloads early, but it does not claim a universal
cloud-style Chroma metadata limit.

The CLI prints an advisory warning when using this preset.

## Qdrant

`vectormeta` uses a conservative advisory default for Qdrant. Configure `--limit-kb`
for your own cluster, ingestion process, and operational preferences.

The CLI prints an advisory warning when using this preset.

## Weaviate

`vectormeta` uses a conservative advisory default for Weaviate. Configure `--limit-kb`
for your own schema, deployment, and ingestion process.

The CLI prints an advisory warning when using this preset.

## Custom

Use `--target custom --limit-kb <number>` when your team has a known policy or a
vendor-specific limit not captured by the built-in presets.
