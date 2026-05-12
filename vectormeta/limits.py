"""Known metadata limit presets for vector database targets."""

from __future__ import annotations

from collections.abc import Mapping

from vectormeta.errors import UnsupportedTargetError
from vectormeta.models import TargetLimit

KB = 1024

TARGET_LIMITS: Mapping[str, TargetLimit] = {
    "pinecone": TargetLimit(
        name="pinecone",
        limit_bytes=40 * KB,
        note="Default Pinecone metadata limit used by this tool. Verify current official docs.",
    ),
    "chroma": TargetLimit(
        name="chroma",
        limit_bytes=256 * KB,
        note=(
            "Advisory scan limit. Chroma deployments are often local/configurable; this is not "
            "a cloud-style hard-limit claim."
        ),
    ),
    "qdrant": TargetLimit(
        name="qdrant",
        limit_bytes=64 * KB,
        note="Conservative advisory default. Configure --limit-kb for your deployment.",
    ),
    "weaviate": TargetLimit(
        name="weaviate",
        limit_bytes=64 * KB,
        note="Conservative advisory default. Configure --limit-kb for your deployment.",
    ),
    "custom": TargetLimit(
        name="custom",
        limit_bytes=None,
        note="Requires --limit-kb.",
    ),
}


def normalize_target(target: str) -> str:
    """Normalize and validate a target name."""
    normalized = target.strip().lower()
    if normalized not in TARGET_LIMITS:
        supported = ", ".join(sorted(TARGET_LIMITS))
        raise UnsupportedTargetError(f"Unsupported target '{target}'. Supported targets: {supported}.")
    return normalized


def resolve_limit_bytes(target: str, limit_kb: float | None = None) -> int:
    """Resolve a metadata limit in bytes for a target."""
    normalized = normalize_target(target)
    if limit_kb is not None:
        if limit_kb <= 0:
            raise UnsupportedTargetError("--limit-kb must be greater than 0.")
        return int(limit_kb * KB)

    target_limit = TARGET_LIMITS[normalized]
    if target_limit.limit_bytes is None:
        raise UnsupportedTargetError("Target 'custom' requires --limit-kb.")
    return target_limit.limit_bytes


def get_target_limits() -> list[TargetLimit]:
    """Return known target limit presets in display order."""
    return [TARGET_LIMITS[name] for name in ("pinecone", "chroma", "qdrant", "weaviate", "custom")]
