from __future__ import annotations

import re
import shutil
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture
def tmp_path(request: pytest.FixtureRequest) -> Generator[Path, None, None]:
    """Provide a workspace-local temp path for sandboxed test runs."""
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", request.node.name)
    path = Path.cwd() / ".test-tmp" / safe_name
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
