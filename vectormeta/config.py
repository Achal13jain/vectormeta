"""Configuration loading for vectormeta."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from vectormeta.errors import InvalidInputError


class VectorMetaConfig(BaseModel):
    """Optional project configuration."""

    model_config = ConfigDict(extra="forbid")

    target: str | None = None
    limit_kb: float | None = None
    move: list[str] | None = Field(default=None)
    keep: list[str] | None = Field(default=None)
    content_ref_field: str | None = None
    sidecar_dir: Path | None = None


def load_config(path: Path | None) -> VectorMetaConfig:
    """Load a YAML config file, returning defaults when no path is provided."""
    if path is None:
        return VectorMetaConfig()
    if not path.exists():
        raise InvalidInputError(f"Config file does not exist: {path}")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise InvalidInputError(f"Invalid YAML config in {path}: {exc}") from exc
    if raw is None:
        return VectorMetaConfig()
    if not isinstance(raw, dict):
        raise InvalidInputError(f"Config file must contain a YAML object: {path}")
    try:
        return VectorMetaConfig.model_validate(raw)
    except ValueError as exc:
        raise InvalidInputError(f"Invalid config in {path}: {exc}") from exc
