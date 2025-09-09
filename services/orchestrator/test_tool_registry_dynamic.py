import json
import sys
import types
from pathlib import Path

import pytest

# Ensure the orchestrator package is on the import path
sys.path.append(str(Path(__file__).resolve().parent))

from tools.registry import ToolRegistry


@pytest.mark.asyncio
async def test_dynamic_tool_loading(tmp_path: Path):
    """Ensure tools can be dynamically loaded from JSON definitions."""
    module_name = "dynamic_tool_impl"
    module = types.ModuleType(module_name)

    async def echo(text: str) -> dict:
        return {"echo": text}

    module.echo = echo
    sys.modules[module_name] = module

    tool_def = {
        "name": "echo_tool",
        "version": "1.0.0",
        "description": "Echo input text",
        "category": "test",
        "inputs_schema": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
            "additionalProperties": False,
        },
        "outputs_schema": {
            "type": "object",
            "properties": {"echo": {"type": "string"}},
            "required": ["echo"],
            "additionalProperties": False,
        },
        "side_effects": "none",
        "rbac_scope": [],
        "execution_time_estimate_ms": 1,
        "psu_cost_estimate": 0,
        "tags": [],
        "module": module_name,
        "function": "echo",
    }

    tool_path = tmp_path / "echo_tool.json"
    tool_path.write_text(json.dumps(tool_def))

    registry = ToolRegistry(tools_dir=tmp_path)
    await registry.initialize()

    tool = await registry.get_tool("echo_tool")
    result = await tool.execute({"text": "hi"})
    assert result.success
    assert result.outputs["echo"] == "hi"
