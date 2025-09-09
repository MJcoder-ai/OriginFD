"""
Tool Registry for managing and executing typed tools.
All tools have versioned schemas with input/output validation.
"""
import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Type
from abc import ABC, abstractmethod
from pydantic import BaseModel, ValidationError, create_model
import importlib
import inspect

logger = logging.getLogger(__name__)


class ToolError(Exception):
    """Base exception for tool-related errors."""
    pass


class ToolValidationError(ToolError):
    """Tool input/output validation error."""
    pass


class ToolExecutionError(ToolError):
    """Tool execution error.""" 
    pass


class ToolMetadata(BaseModel):
    """Metadata for a registered tool."""
    name: str
    version: str
    description: str
    category: str
    inputs_schema: Dict[str, Any]
    outputs_schema: Dict[str, Any]
    side_effects: str  # "none", "read", "write", "external"
    rbac_scope: List[str]  # Required permissions
    execution_time_estimate_ms: int
    psu_cost_estimate: int
    tags: List[str] = []


class ToolResult(BaseModel):
    """Standardized tool execution result."""
    success: bool
    content: Optional[Any] = None  # For backward compatibility
    execution_time_ms: int
    outputs: Dict[str, Any] = {}
    errors: List[str] = []
    evidence: List[str] = []  # URIs to supporting evidence
    intent: Optional[str] = None  # Human-readable description of what was done


class BaseTool(ABC):
    """Base class for all tools."""
    
    @property
    @abstractmethod
    def metadata(self) -> ToolMetadata:
        """Tool metadata and schema definition."""
        pass
    
    @abstractmethod
    async def execute(self, inputs: Dict[str, Any]) -> ToolResult:
        """Execute the tool with given inputs."""
        pass
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate inputs against schema."""
        try:
            # Create Pydantic model from schema for validation
            input_model = create_model_from_schema(
                f"{self.metadata.name}Input", 
                self.metadata.inputs_schema
            )
            validated = input_model.parse_obj(inputs)
            return validated.dict()
        except ValidationError as e:
            raise ToolValidationError(f"Input validation failed: {e}")
    
    def validate_outputs(self, outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate outputs against schema."""
        try:
            output_model = create_model_from_schema(
                f"{self.metadata.name}Output",
                self.metadata.outputs_schema
            )
            validated = output_model.parse_obj(outputs)
            return validated.dict()
        except ValidationError as e:
            raise ToolValidationError(f"Output validation failed: {e}")


class ToolRegistry:
    """
    Registry for managing all available tools.
    Handles loading, validation, and execution of tools.
    """
    
    def __init__(self, tools_dir: Optional[Path] = None):
        self.tools_dir = tools_dir or Path(__file__).parent / "definitions"
        self.tools: Dict[str, BaseTool] = {}
        self.metadata_cache: Dict[str, ToolMetadata] = {}
    
    async def initialize(self):
        """Initialize the tool registry by loading all tools."""
        logger.info("Initializing tool registry...")
        
        # Load tools from definitions directory
        await self._load_tools_from_directory()
        
        # Load tools from external modules
        await self._load_builtin_tools()
        
        logger.info(f"Loaded {len(self.tools)} tools")
        
        # Log tool categories
        categories = {}
        for tool in self.metadata_cache.values():
            categories[tool.category] = categories.get(tool.category, 0) + 1
        
        logger.info(f"Tool categories: {categories}")
    
    async def get_tool(self, tool_name: str, version: Optional[str] = None) -> BaseTool:
        """Get a tool by name and optional version."""
        # For now, ignore version and get latest
        tool_key = tool_name
        
        if tool_key not in self.tools:
            raise ToolError(f"Tool not found: {tool_name}")
        
        return self.tools[tool_key]
    
    def list_tools(self, category: Optional[str] = None) -> List[ToolMetadata]:
        """List all available tools, optionally filtered by category."""
        tools = list(self.metadata_cache.values())
        
        if category:
            tools = [t for t in tools if t.category == category]
        
        return sorted(tools, key=lambda t: (t.category, t.name))
    
    def get_tool_metadata(self, tool_name: str) -> Optional[ToolMetadata]:
        """Get metadata for a specific tool."""
        return self.metadata_cache.get(tool_name)
    
    async def register_tool(self, tool: BaseTool):
        """Register a new tool."""
        metadata = tool.metadata
        
        # Validate metadata
        if not metadata.name:
            raise ToolError("Tool name cannot be empty")
        
        # Store tool and metadata
        self.tools[metadata.name] = tool
        self.metadata_cache[metadata.name] = metadata
        
        logger.info(f"Registered tool: {metadata.name} v{metadata.version}")
    
    async def _load_tools_from_directory(self):
        """Load tools from JSON definitions in tools directory."""
        if not self.tools_dir.exists():
            logger.warning(f"Tools directory not found: {self.tools_dir}")
            return
        
        for tool_file in self.tools_dir.glob("*.json"):
            try:
                with open(tool_file) as f:
                    tool_def = json.load(f)
                
                # Create tool from definition
                tool = await self._create_tool_from_definition(tool_def)
                await self.register_tool(tool)
                
            except Exception as e:
                logger.error(f"Failed to load tool from {tool_file}: {e}")
    
    async def _load_builtin_tools(self):
        """Load built-in tools from Python modules."""
        from .component_tools import (
            ParseDatasheetTool,
            ComponentDeduplicationTool,
            ComponentClassificationTool,
            ComponentRecommendationTool
        )
        
        builtin_tools = [
            ValidateOdlTool(),
            SimulateEnergyTool(),
            SimulateFinanceTool(),
            # Component management tools
            ParseDatasheetTool(),
            ComponentDeduplicationTool(),
            ComponentClassificationTool(),
            ComponentRecommendationTool(),
            # Add more built-in tools here
        ]
        
        for tool in builtin_tools:
            await self.register_tool(tool)
    
    async def _create_tool_from_definition(self, tool_def: Dict[str, Any]) -> BaseTool:
        """Create a tool instance from JSON definition."""
        # This would create a generic tool wrapper
        # For now, raise an error as we need specific implementation
        raise NotImplementedError("Generic tool creation from JSON not yet implemented")


def create_model_from_schema(name: str, schema: Dict[str, Any]) -> Type[BaseModel]:
    """Create a Pydantic model from JSON schema."""
    # This is a simplified implementation
    # In practice, you'd use jsonschema-to-pydantic or similar
    fields: Dict[str, tuple[Any, Any]] = {}

    if "properties" in schema:
        for field_name, field_schema in schema["properties"].items():
            field_type: Any = str  # Default type

            if field_schema.get("type") == "integer":
                field_type = int
            elif field_schema.get("type") == "number":
                field_type = float
            elif field_schema.get("type") == "boolean":
                field_type = bool
            elif field_schema.get("type") == "array":
                field_type = List[Any]
            elif field_schema.get("type") == "object":
                field_type = Dict[str, Any]

            is_required = field_name in schema.get("required", [])
            default = ... if is_required else None
            if not is_required:
                field_type = Optional[field_type]

            fields[field_name] = (field_type, default)

    return create_model(name, **fields)


# Built-in Tools

class ValidateOdlTool(BaseTool):
    """Tool for validating ODL-SD documents."""
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="validate_odl_sd",
            version="1.0.0",
            description="Validate ODL-SD document against schema",
            category="validation",
            inputs_schema={
                "type": "object",
                "properties": {
                    "document": {"type": "object", "description": "ODL-SD document to validate"},
                    "strict": {"type": "boolean", "default": True, "description": "Enable strict validation"}
                },
                "required": ["document"],
                "additionalProperties": False
            },
            outputs_schema={
                "type": "object", 
                "properties": {
                    "is_valid": {"type": "boolean"},
                    "errors": {"type": "array", "items": {"type": "string"}},
                    "warnings": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["is_valid", "errors"],
                "additionalProperties": False
            },
            side_effects="none",
            rbac_scope=["document_read"],
            execution_time_estimate_ms=100,
            psu_cost_estimate=0,
            tags=["validation", "schema"]
        )
    
    async def execute(self, inputs: Dict[str, Any]) -> ToolResult:
        """Execute validation."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            validated_inputs = self.validate_inputs(inputs)
            document = validated_inputs["document"]
            strict = validated_inputs.get("strict", True)
            
            # Import here to avoid circular imports
            from odl_sd_schema import validate_document
            
            # Perform validation
            result = validate_document(document, strict=strict)
            
            outputs = {
                "is_valid": result.is_valid,
                "errors": result.errors,
                "warnings": result.warnings
            }
            
            validated_outputs = self.validate_outputs(outputs)
            execution_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
            
            return ToolResult(
                success=True,
                execution_time_ms=execution_time,
                outputs=validated_outputs,
                intent="Validated ODL-SD document structure and content"
            )
            
        except Exception as e:
            execution_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
            return ToolResult(
                success=False,
                execution_time_ms=execution_time,
                errors=[str(e)]
            )


class SimulateEnergyTool(BaseTool):
    """Tool for energy simulation calculations."""
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="simulate_energy",
            version="1.0.0",
            description="Simulate energy production and consumption",
            category="simulation",
            inputs_schema={
                "type": "object",
                "properties": {
                    "document_id": {"type": "string"},
                    "simulation_period_years": {"type": "integer", "minimum": 1, "maximum": 30},
                    "weather_data_source": {"type": "string", "default": "pvlib"}
                },
                "required": ["document_id", "simulation_period_years"],
                "additionalProperties": False
            },
            outputs_schema={
                "type": "object",
                "properties": {
                    "annual_generation_kwh": {"type": "number"},
                    "capacity_factor": {"type": "number"},
                    "performance_ratio": {"type": "number"},
                    "monthly_generation": {"type": "array", "items": {"type": "number"}}
                },
                "required": ["annual_generation_kwh", "capacity_factor"],
                "additionalProperties": False
            },
            side_effects="read",
            rbac_scope=["simulation_run"],
            execution_time_estimate_ms=5000,
            psu_cost_estimate=2,
            tags=["simulation", "energy", "pv"]
        )
    
    async def execute(self, inputs: Dict[str, Any]) -> ToolResult:
        """Execute energy simulation."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            validated_inputs = self.validate_inputs(inputs)
            
            # Mock simulation for now
            await asyncio.sleep(0.1)  # Simulate computation
            
            outputs = {
                "annual_generation_kwh": 1500000.0,
                "capacity_factor": 0.24,
                "performance_ratio": 0.85,
                "monthly_generation": [95000, 110000, 135000, 145000, 150000, 145000,
                                     140000, 135000, 125000, 115000, 100000, 90000]
            }
            
            validated_outputs = self.validate_outputs(outputs)
            execution_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
            
            return ToolResult(
                success=True,
                execution_time_ms=execution_time,
                outputs=validated_outputs,
                intent="Simulated energy generation for solar PV system"
            )
            
        except Exception as e:
            execution_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
            return ToolResult(
                success=False,
                execution_time_ms=execution_time,
                errors=[str(e)]
            )


class SimulateFinanceTool(BaseTool):
    """Tool for financial modeling and analysis."""
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="simulate_finance",
            version="1.0.0", 
            description="Calculate financial metrics (IRR, NPV, LCOE)",
            category="finance",
            inputs_schema={
                "type": "object",
                "properties": {
                    "document_id": {"type": "string"},
                    "discount_rate": {"type": "number", "minimum": 0, "maximum": 0.3},
                    "electricity_price_per_kwh": {"type": "number", "minimum": 0},
                    "analysis_period_years": {"type": "integer", "minimum": 1, "maximum": 50}
                },
                "required": ["document_id", "discount_rate", "electricity_price_per_kwh"],
                "additionalProperties": False
            },
            outputs_schema={
                "type": "object",
                "properties": {
                    "irr_percent": {"type": "number"},
                    "npv_usd": {"type": "number"},
                    "lcoe_per_kwh": {"type": "number"},
                    "payback_period_years": {"type": "number"}
                },
                "required": ["irr_percent", "npv_usd", "lcoe_per_kwh"],
                "additionalProperties": False
            },
            side_effects="read",
            rbac_scope=["financial_analysis"],
            execution_time_estimate_ms=2000,
            psu_cost_estimate=3,
            tags=["finance", "analysis", "irr", "npv"]
        )
    
    async def execute(self, inputs: Dict[str, Any]) -> ToolResult:
        """Execute financial simulation."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            validated_inputs = self.validate_inputs(inputs)
            
            # Mock financial calculation
            await asyncio.sleep(0.05)
            
            outputs = {
                "irr_percent": 12.5,
                "npv_usd": 2850000.0,
                "lcoe_per_kwh": 0.042,
                "payback_period_years": 7.2
            }
            
            validated_outputs = self.validate_outputs(outputs)
            execution_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
            
            return ToolResult(
                success=True,
                execution_time_ms=execution_time,
                outputs=validated_outputs,
                intent="Calculated financial metrics for energy project"
            )
            
        except Exception as e:
            execution_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
            return ToolResult(
                success=False,
                execution_time_ms=execution_time,
                errors=[str(e)]
            )