# GitHub Action

Use the vectormeta metadata check Action to scan or validate vector records in pull
request CI before they reach an upsert pipeline.

## Example

```yaml
name: Vector metadata check

on:
  pull_request:

jobs:
  vectormeta:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: Achal13jain/vectormeta/actions/check-metadata@v0.5.1
        with:
          input: examples/oversized_pinecone_records.json
          target: pinecone
          mode: validate
          dim: "1536"
```

## JSONL Streaming

For large newline-delimited JSON inputs, enable streaming mode:

```yaml
- uses: Achal13jain/vectormeta/actions/check-metadata@v0.5.1
  with:
    input: data/chunks.jsonl
    target: pinecone
    mode: both
    stream: "true"
    dim: "1536"
    fail-on-warning: "true"
```

`scan --stream` and `validate --stream` require JSONL input.

## Inputs

| Input | Default | Description |
| --- | --- | --- |
| `input` | required | Path to a JSON or JSONL vector records file. |
| `target` | `pinecone` | Target vector DB: `pinecone`, `chroma`, `qdrant`, `weaviate`, or `custom`. |
| `mode` | `validate` | Check mode: `scan`, `validate`, or `both`. |
| `limit-kb` | empty | Override metadata size limit in KB. Required for `target: custom`. |
| `dim` | empty | Expected vector dimension for validation. |
| `top` | `20` | Number of oversized records or validation issues to display. |
| `format` | `table` | Output format passed to vectormeta: `table` or `json`. |
| `stream` | `false` | Use streaming JSONL mode. |
| `fail-on-warning` | `false` | Fail validation when warning-level issues are found. |
| `no-fail` | `false` | Report issues without failing the workflow. |

## Exit Behavior

The Action uses the packaged vectormeta CLI:

- `scan` fails when oversized records are found unless `no-fail: "true"` is set.
- `validate` fails when error-level validation issues are found unless `no-fail: "true"` is set.
- `fail-on-warning: "true"` makes validation fail on warning-level issues too.
- input, target, or configuration errors fail with exit code `2`.

When both `fail-on-warning` and `no-fail` are enabled, `fail-on-warning` takes
precedence for validation warnings and errors. Invalid boolean input values are rejected
instead of being treated as `false`.

For non-Pinecone targets, vectormeta uses advisory limit presets. Verify provider
configuration and official service documentation for production limits.
