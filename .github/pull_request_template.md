## Summary

Describe the change.

## Testing

```bash
python -m pytest
ruff check .
ruff format --check .
mypy vectormeta
```

## Checklist

- [ ] Core logic remains independent from Typer/Rich where practical.
- [ ] New behavior has focused tests.
- [ ] Docs or examples are updated when user-facing behavior changes.
- [ ] Vector database limit claims are cautious and sourced where needed.
