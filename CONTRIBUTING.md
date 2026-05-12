# Contributing

Thanks for helping make `vectormeta` better.

## Local Setup

```bash
git clone https://github.com/Achal13jain/vectormeta.git
cd vectormeta
pip install -e ".[dev]"
```

## Checks

Run these before opening a pull request:

```bash
python -m pytest
ruff check .
ruff format --check .
mypy vectormeta
```

## Commit Style

Use Conventional Commits where practical:

- `feat: add new behavior`
- `fix: correct a bug`
- `test: add coverage`
- `docs: update documentation`
- `chore: maintain tooling or metadata`

## Development Notes

- Keep core logic independent from Typer and Rich.
- Preserve record order and unknown fields.
- Do not silently overwrite files.
- Add focused tests for behavior changes.
- Be careful with vector database limit claims; link or defer to official docs where
  exact limits matter.
