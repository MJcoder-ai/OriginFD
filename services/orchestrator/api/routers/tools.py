"""API endpoints for interacting with typed tools."""
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse

from tools.registry import ToolMetadata, ToolResult, ToolRegistry
from tools.generate_sdk import generate_typescript_sdk, generate_python_sdk

router = APIRouter()


def _get_registry(request: Request) -> ToolRegistry:
    orchestrator = getattr(request.app.state, "orchestrator", None)
    if not orchestrator or not hasattr(orchestrator, "tool_registry"):
        raise HTTPException(status_code=500, detail="Tool registry not available")
    return orchestrator.tool_registry


def _sample_from_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    sample: Dict[str, Any] = {}
    props = schema.get("properties", {})
    required = set(schema.get("required", []))
    for name, prop in props.items():
        typ = prop.get("type")
        if typ == "string":
            if "enum" in prop:
                value = prop["enum"][0]
            else:
                value = prop.get("default", "example")
        elif typ == "integer":
            value = prop.get("default", prop.get("minimum", 0))
        elif typ == "number":
            value = prop.get("default", prop.get("minimum", 0.0))
        elif typ == "boolean":
            value = prop.get("default", True)
        elif typ == "array":
            value = []
        elif typ == "object":
            value = {}
        else:
            value = None
        sample[name] = value
    return sample


@router.get("/", response_model=list[ToolMetadata])
async def list_tools(request: Request):
    """List available tools and their metadata."""
    registry = _get_registry(request)
    return registry.list_tools()


@router.post("/{tool_name}/sample", response_model=ToolResult)
async def run_tool_sample(tool_name: str, request: Request):
    """Execute a tool using auto-generated sample inputs."""
    registry = _get_registry(request)
    tool = await registry.get_tool(tool_name)
    inputs = _sample_from_schema(tool.metadata.inputs_schema)
    return await tool.execute(inputs)


@router.get("/sdk/typescript", response_class=PlainTextResponse)
async def download_typescript_sdk(request: Request) -> PlainTextResponse:
    """Generate TypeScript types for all tools."""
    registry = _get_registry(request)
    code = generate_typescript_sdk(registry)
    return PlainTextResponse(code, media_type="text/plain")


@router.get("/sdk/python", response_class=PlainTextResponse)
async def download_python_sdk(request: Request) -> PlainTextResponse:
    """Generate Python types for all tools."""
    registry = _get_registry(request)
    code = generate_python_sdk(registry)
    return PlainTextResponse(code, media_type="text/plain")
