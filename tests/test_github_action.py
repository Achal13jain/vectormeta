from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import yaml

ACTION_DIR = Path(__file__).resolve().parents[1] / "actions" / "check-metadata"


def test_github_action_metadata_defines_expected_inputs() -> None:
    action = yaml.safe_load((ACTION_DIR / "action.yml").read_text(encoding="utf-8"))

    assert action["runs"]["using"] == "composite"
    assert set(action["inputs"]) == {
        "input",
        "target",
        "mode",
        "limit-kb",
        "dim",
        "top",
        "format",
        "stream",
        "fail-on-warning",
        "no-fail",
    }
    assert action["inputs"]["input"]["required"] is True


def test_action_runner_builds_scan_and_validate_commands() -> None:
    runner = _load_runner()
    config = runner.ActionConfig(
        input_path="records.jsonl",
        target="pinecone",
        mode="both",
        limit_kb="40",
        dim="1536",
        top="5",
        output_format="table",
        stream=True,
        fail_on_warning=False,
        no_fail=False,
    )

    commands = runner.build_commands(config)

    assert [command[3] for command in commands] == ["scan", "validate"]
    assert all("--stream" in command for command in commands)
    assert _option_value(commands[0], "--limit-kb") == "40"
    assert commands[1][-2:] == ["--dim", "1536"]


def test_action_runner_fail_on_warning_forces_validate_json_and_no_fail() -> None:
    runner = _load_runner()
    config = runner.ActionConfig(
        input_path="records.jsonl",
        target="pinecone",
        mode="validate",
        limit_kb=None,
        dim=None,
        top="5",
        output_format="table",
        stream=False,
        fail_on_warning=True,
        no_fail=False,
    )

    command = runner.build_commands(config)[0]

    assert _option_value(command, "--format") == "json"
    assert "--no-fail" in command


def test_action_runner_rejects_invalid_mode() -> None:
    runner = _load_runner()

    try:
        runner.config_from_env({"INPUT_INPUT": "records.json", "INPUT_MODE": "repair"})
    except ValueError as exc:
        assert "mode" in str(exc)
    else:
        raise AssertionError("Expected invalid mode to raise ValueError.")


def _load_runner() -> ModuleType:
    module_name = "vectormeta_action_runner"
    spec = importlib.util.spec_from_file_location(module_name, ACTION_DIR / "run.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _option_value(command: list[str], option: str) -> str:
    return command[command.index(option) + 1]
