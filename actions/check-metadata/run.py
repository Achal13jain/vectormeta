"""GitHub Action runner for vectormeta metadata checks."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class ActionConfig:
    """Inputs accepted by the GitHub Action."""

    input_path: str
    target: str
    mode: str
    limit_kb: str | None
    dim: str | None
    top: str
    output_format: str
    stream: bool
    fail_on_warning: bool
    no_fail: bool


def config_from_env(env: dict[str, str]) -> ActionConfig:
    """Build action configuration from GitHub-provided environment variables."""
    input_path = env.get("INPUT_INPUT", "").strip()
    if not input_path:
        raise ValueError("The 'input' action input is required.")

    mode = env.get("INPUT_MODE", "validate").strip().lower()
    if mode not in {"scan", "validate", "both"}:
        raise ValueError("The 'mode' action input must be one of: scan, validate, both.")
    output_format = env.get("INPUT_FORMAT", "table").strip().lower() or "table"
    if output_format not in {"table", "json"}:
        raise ValueError("The 'format' action input must be one of: table, json.")

    return ActionConfig(
        input_path=input_path,
        target=env.get("INPUT_TARGET", "pinecone").strip() or "pinecone",
        mode=mode,
        limit_kb=_optional(env.get("INPUT_LIMIT_KB", "")),
        dim=_optional(env.get("INPUT_DIM", "")),
        top=env.get("INPUT_TOP", "20").strip() or "20",
        output_format=output_format,
        stream=_bool(env.get("INPUT_STREAM", "false")),
        fail_on_warning=_bool(env.get("INPUT_FAIL_ON_WARNING", "false")),
        no_fail=_bool(env.get("INPUT_NO_FAIL", "false")),
    )


def build_commands(config: ActionConfig) -> list[list[str]]:
    """Return vectormeta CLI commands for the requested action mode."""
    commands: list[list[str]] = []
    if config.mode in {"scan", "both"}:
        commands.append(_scan_command(config))
    if config.mode in {"validate", "both"}:
        commands.append(_validate_command(config))
    return commands


def run(config: ActionConfig) -> int:
    """Execute configured vectormeta checks."""
    exit_code = 0
    for command in build_commands(config):
        print(f"::group::{_group_name(command)}", flush=True)
        completed = subprocess.run(
            command,
            check=False,
            text=True,
            capture_output=_captures_output(config, command),
        )
        if completed.stdout:
            print(completed.stdout, end="")
        if completed.stderr:
            print(completed.stderr, end="", file=sys.stderr)
        print("::endgroup::", flush=True)
        if completed.returncode != 0:
            exit_code = completed.returncode
        elif _should_fail_on_warning(config, command, completed.stdout):
            exit_code = 1
    return exit_code


def main() -> int:
    """Run the action from process environment."""
    try:
        config = config_from_env(os.environ)
    except ValueError as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 2
    return run(config)


def _scan_command(config: ActionConfig) -> list[str]:
    command = [
        sys.executable,
        "-m",
        "vectormeta",
        "scan",
        config.input_path,
        "--target",
        config.target,
        "--top",
        config.top,
        "--format",
        config.output_format,
    ]
    _append_common_options(command, config)
    return command


def _validate_command(config: ActionConfig) -> list[str]:
    command = [
        sys.executable,
        "-m",
        "vectormeta",
        "validate",
        config.input_path,
        "--target",
        config.target,
        "--top",
        config.top,
        "--format",
        "json" if config.fail_on_warning else config.output_format,
    ]
    _append_common_options(command, config)
    if config.dim is not None:
        command.extend(["--dim", config.dim])
    return command


def _append_common_options(command: list[str], config: ActionConfig) -> None:
    if config.limit_kb is not None:
        command.extend(["--limit-kb", config.limit_kb])
    if config.stream:
        command.append("--stream")
    if config.no_fail or config.fail_on_warning:
        command.append("--no-fail")


def _optional(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _captures_output(config: ActionConfig, command: list[str]) -> bool:
    return config.fail_on_warning and "validate" in command


def _should_fail_on_warning(config: ActionConfig, command: list[str], output: str) -> bool:
    if not config.fail_on_warning or "validate" not in command:
        return False
    try:
        report = json.loads(output)
    except json.JSONDecodeError:
        print("::error::Could not parse vectormeta validation JSON output.", file=sys.stderr)
        return True
    warning_count = int(report.get("warning_count", 0))
    error_count = int(report.get("error_count", 0))
    if warning_count:
        print(f"::error::vectormeta found {warning_count} warning-level issue(s).")
    return warning_count > 0 or error_count > 0


def _group_name(command: list[str]) -> str:
    if "scan" in command:
        return "vectormeta scan"
    if "validate" in command:
        return "vectormeta validate"
    return "vectormeta"


if __name__ == "__main__":
    raise SystemExit(main())
