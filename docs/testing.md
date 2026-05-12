# Testing And Release Confidence

Use this checklist to confirm `vectormeta` works locally and is likely to work for
someone else after cloning the repository.

## 1. Fresh Local Install

From the repository root:

```bash
pip install -e ".[dev]"
vectormeta --help
vectormeta --version
python -m vectormeta --help
```

This verifies the package metadata, console script, and module entry point.

## 2. Automated Checks

```bash
python -m pytest
ruff check .
ruff format --check .
mypy vectormeta
```

These cover behavior, linting, formatting, and strict typing.

## 3. Package Build

```bash
python -m build
```

This creates a source distribution and wheel in `dist/`. A successful build is a good
signal that the package can be installed outside the working tree.

## 4. CLI Smoke Test

```bash
vectormeta scan examples/oversized_pinecone_records.json --target pinecone --no-fail
vectormeta fix examples/oversized_pinecone_records.json --target pinecone --sidecar examples/sidecar --out examples/pinecone_ready.json --overwrite
vectormeta hydrate examples/pinecone_ready.json --sidecar examples/sidecar --out examples/hydrated.json --overwrite
```

Expected results:

- `scan` reports 2 records scanned and 1 oversized record.
- `fix` writes `examples/pinecone_ready.json` and sidecar JSON files.
- `hydrate` writes `examples/hydrated.json`.

Generated files under `examples/sidecar`, `examples/pinecone_ready.json`, and
`examples/hydrated.json` are ignored by git.

## 5. CI Confidence

GitHub Actions runs the same core checks on Python 3.10, 3.11, and 3.12:

- `ruff check .`
- `ruff format --check .`
- `mypy vectormeta`
- `python -m pytest`
- `python -m build`

If CI passes on a fresh clone, another developer should be able to install and run the
project with the documented commands.
