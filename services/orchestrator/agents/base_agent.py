"""
Base AI Agent implementation for OriginFD platform.
All specialized agents inherit from this base class.
"""

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel

from ..memory.episodic import EpisodicMemory
from ..memory.semantic import SemanticMemory
from ..tools.registry import BaseTool, ToolRegistry, ToolResult

logger = logging.getLogger(__name__)


class AgentStatus(str, Enum):
    """Agent execution status."""

    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    WAITING = "waiting"
    ERROR = "error"
    COMPLETED = "completed"


class AgentCapability(BaseModel):
    """Agent capability definition."""

    name: str
    description: str
    tools: List[str]
    rbac_scope: List[str]
    confidence_level: float  # 0.0 to 1.0


class AgentContext(BaseModel):
    """Agent execution context."""

    session_id: str
    user_id: str
    tenant_id: str
    task_id: str
    current_state: Dict[str, Any]
    shared_scratchpad: Dict[str, Any]
    conversation_history: List[Dict[str, Any]]
    project_context: Optional[Dict[str, Any]] = None


class AgentPlan(BaseModel):
    """Agent execution plan."""

    plan_id: str
    steps: List[Dict[str, Any]]
    estimated_duration_ms: int
    estimated_cost_psu: int
    tools_required: List[str]
    dependencies: List[str]
    confidence: float
    reasoning: str


class AgentResult(BaseModel):
    """Agent execution result."""

    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    plan_executed: Optional[AgentPlan] = None
    tools_used: List[str] = []
    execution_time_ms: int
    psu_cost: int
    quality_score: float
    confidence: float
    next_actions: List[str] = []


class BaseAgent(ABC):
    """
    Base class for all AI agents in the OriginFD platform.

    Provides common functionality for:
    - Tool management and execution
    - Memory and context handling
    - Planning and execution
    - Communication with other agents
    - Quality assurance and monitoring
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        capabilities: List[AgentCapability],
        tool_registry: ToolRegistry,
        episodic_memory: EpisodicMemory,
        semantic_memory: SemanticMemory,
    ):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.capabilities = {cap.name: cap for cap in capabilities}
        self.tool_registry = tool_registry
        self.episodic_memory = episodic_memory
        self.semantic_memory = semantic_memory

        # Agent state
        self.status = AgentStatus.IDLE
        self.current_context: Optional[AgentContext] = None
        self.current_plan: Optional[AgentPlan] = None
        self.execution_history: List[AgentResult] = []

        # Performance tracking
        self.total_executions = 0
        self.success_rate = 0.0
        self.average_execution_time_ms = 0
        self.total_psu_cost = 0

        logger.info(f"Initialized agent: {self.name} ({self.agent_id})")

    @property
    @abstractmethod
    def specialized_tools(self) -> List[str]:
        """List of tools this agent specializes in using."""
        pass

    @property
    @abstractmethod
    def primary_domain(self) -> str:
        """Primary domain this agent operates in."""
        pass

    @abstractmethod
    async def create_plan(self, task: str, context: AgentContext) -> AgentPlan:
        """Create an execution plan for the given task."""
        pass

    @abstractmethod
    async def execute_plan(self, plan: AgentPlan, context: AgentContext) -> AgentResult:
        """Execute the given plan."""
        pass

    async def process_request(self, task: str, context: AgentContext) -> AgentResult:
        """
        Main entry point for processing requests.
        Handles the complete workflow: plan -> execute -> learn.
        """
        start_time = datetime.utcnow()
        self.status = AgentStatus.THINKING
        self.current_context = context

        try:
            # Store context in episodic memory
            await self.episodic_memory.store_interaction(
                session_id=context.session_id,
                agent_id=self.agent_id,
                interaction_type="request_received",
                content={"task": task, "context": context.dict()},
            )

            # Create execution plan
            plan = await self.create_plan(task, context)
            self.current_plan = plan

            # Validate plan
            validation_result = await self.validate_plan(plan, context)
            if not validation_result["valid"]:
                return AgentResult(
                    success=False,
                    error=f"Plan validation failed: {validation_result['reason']}",
                    execution_time_ms=self._get_elapsed_ms(start_time),
                    psu_cost=0,
                    quality_score=0.0,
                    confidence=0.0,
                )

            # Execute plan
            self.status = AgentStatus.EXECUTING
            result = await self.execute_plan(plan, context)

            # Update performance metrics
            self._update_performance_metrics(result)

            # Learn from execution
            await self.learn_from_execution(plan, result, context)

            self.status = AgentStatus.COMPLETED
            return result

        except Exception as e:
            logger.error(f"Agent {self.name} execution failed: {str(e)}")
            self.status = AgentStatus.ERROR

            error_result = AgentResult(
                success=False,
                error=str(e),
                execution_time_ms=self._get_elapsed_ms(start_time),
                psu_cost=0,
                quality_score=0.0,
                confidence=0.0,
            )

            self._update_performance_metrics(error_result)
            return error_result

        finally:
            self.current_context = None
            self.current_plan = None
            self.status = AgentStatus.IDLE

    async def validate_plan(
        self, plan: AgentPlan, context: AgentContext
    ) -> Dict[str, Any]:
        """
        Validate the execution plan for safety, permissions, and feasibility.
        """
        # Check RBAC permissions
        required_scopes = set()
        for tool_name in plan.tools_required:
            tool_metadata = self.tool_registry.get_tool_metadata(tool_name)
            if tool_metadata:
                required_scopes.update(tool_metadata.rbac_scope)

        # TODO: Implement actual RBAC check against user permissions
        # For now, assume validation passes

        # Check cost limits
        if plan.estimated_cost_psu > 100:  # TODO: Get from policy router
            return {
                "valid": False,
                "reason": f"Plan cost ({plan.estimated_cost_psu} PSU) exceeds limit",
            }

        # Check tool availability
        for tool_name in plan.tools_required:
            try:
                await self.tool_registry.get_tool(tool_name)
            except Exception:
                return {
                    "valid": False,
                    "reason": f"Required tool not available: {tool_name}",
                }

        return {"valid": True, "reason": "Plan validated successfully"}

    async def execute_tool(
        self, tool_name: str, inputs: Dict[str, Any], context: AgentContext
    ) -> ToolResult:
        """
        Execute a specific tool with proper error handling and logging.
        """
        try:
            tool = await self.tool_registry.get_tool(tool_name)

            # Add context to tool inputs
            enhanced_inputs = {
                **inputs,
                "_context": {
                    "agent_id": self.agent_id,
                    "session_id": context.session_id,
                    "user_id": context.user_id,
                    "tenant_id": context.tenant_id,
                },
            }

            # Execute tool
            result = await tool.execute(enhanced_inputs)

            # Log tool execution
            await self.episodic_memory.store_interaction(
                session_id=context.session_id,
                agent_id=self.agent_id,
                interaction_type="tool_execution",
                content={
                    "tool": tool_name,
                    "inputs": inputs,
                    "result": result.dict(),
                    "success": result.success,
                },
            )

            return result

        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name} - {str(e)}")
            return ToolResult(
                success=False,
                error=str(e),
                execution_time_ms=0,
                intent=f"Failed to execute {tool_name}",
            )

    async def communicate_with_agent(
        self, target_agent_id: str, message: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Communicate with another agent (handover protocol).
        """
        handover_message = {
            "from_agent": self.agent_id,
            "to_agent": target_agent_id,
            "message": message,
            "context": context,
            "timestamp": datetime.utcnow().isoformat(),
            "shared_scratchpad": (
                self.current_context.shared_scratchpad if self.current_context else {}
            ),
        }

        # Store handover in episodic memory
        await self.episodic_memory.store_interaction(
            session_id=(
                self.current_context.session_id if self.current_context else "system"
            ),
            agent_id=self.agent_id,
            interaction_type="agent_handover",
            content=handover_message,
        )

        # TODO: Implement actual agent communication mechanism
        # For now, return acknowledgment
        return {
            "acknowledged": True,
            "target_agent": target_agent_id,
            "handover_id": str(uuid.uuid4()),
        }

    async def learn_from_execution(
        self, plan: AgentPlan, result: AgentResult, context: AgentContext
    ):
        """
        Learn from execution results to improve future performance.
        """
        learning_data = {
            "agent_id": self.agent_id,
            "plan": plan.dict(),
            "result": result.dict(),
            "context_summary": {
                "task_type": context.current_state.get("task_type"),
                "domain": context.current_state.get("domain"),
                "complexity": context.current_state.get("complexity"),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Store learning data
        await self.semantic_memory.store_knowledge(
            knowledge_type="execution_learning",
            content=learning_data,
            tags=[self.agent_id, plan.plan_id, "learning"],
        )

        # Update success patterns
        if result.success:
            await self._update_success_patterns(plan, result, context)
        else:
            await self._update_failure_patterns(plan, result, context)

    async def get_capability_assessment(self, task_description: str) -> Dict[str, Any]:
        """
        Assess this agent's capability to handle a specific task.
        """
        # Analyze task requirements
        task_analysis = await self._analyze_task_requirements(task_description)

        # Calculate capability match
        capability_scores = {}
        overall_confidence = 0.0

        for cap_name, capability in self.capabilities.items():
            score = await self._calculate_capability_match(capability, task_analysis)
            capability_scores[cap_name] = score
            overall_confidence += score * capability.confidence_level

        overall_confidence = (
            overall_confidence / len(self.capabilities) if self.capabilities else 0.0
        )

        return {
            "agent_id": self.agent_id,
            "agent_name": self.name,
            "overall_confidence": overall_confidence,
            "capability_scores": capability_scores,
            "can_handle": overall_confidence > 0.6,
            "estimated_success_rate": min(overall_confidence * self.success_rate, 0.95),
            "reasoning": await self._generate_capability_reasoning(
                task_analysis, capability_scores
            ),
        }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics for this agent."""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.name,
            "total_executions": self.total_executions,
            "success_rate": self.success_rate,
            "average_execution_time_ms": self.average_execution_time_ms,
            "total_psu_cost": self.total_psu_cost,
            "current_status": self.status,
            "capabilities": list(self.capabilities.keys()),
            "specialized_tools": self.specialized_tools,
            "primary_domain": self.primary_domain,
        }

    # Private helper methods

    def _get_elapsed_ms(self, start_time: datetime) -> int:
        """Calculate elapsed time in milliseconds."""
        return int((datetime.utcnow() - start_time).total_seconds() * 1000)

    def _update_performance_metrics(self, result: AgentResult):
        """Update performance metrics based on execution result."""
        self.total_executions += 1
        self.total_psu_cost += result.psu_cost

        # Update success rate (exponential moving average)
        alpha = 0.1  # Learning rate
        success = 1.0 if result.success else 0.0
        self.success_rate = (1 - alpha) * self.success_rate + alpha * success

        # Update average execution time
        self.average_execution_time_ms = (
            self.average_execution_time_ms * (self.total_executions - 1)
            + result.execution_time_ms
        ) / self.total_executions

        # Store result in history (keep last 100)
        self.execution_history.append(result)
        if len(self.execution_history) > 100:
            self.execution_history.pop(0)

    async def _analyze_task_requirements(self, task_description: str) -> Dict[str, Any]:
        """Analyze task to understand requirements."""
        # TODO: Implement actual task analysis using NLP/AI
        # For now, return basic analysis
        return {
            "complexity": "medium",
            "domain": "general",
            "tools_needed": [],
            "estimated_duration": "unknown",
            "risk_level": "low",
        }

    async def _calculate_capability_match(
        self, capability: AgentCapability, task_analysis: Dict[str, Any]
    ) -> float:
        """Calculate how well a capability matches task requirements."""
        # TODO: Implement sophisticated capability matching
        # For now, return basic score
        return 0.8

    async def _generate_capability_reasoning(
        self, task_analysis: Dict[str, Any], capability_scores: Dict[str, float]
    ) -> str:
        """Generate human-readable reasoning for capability assessment."""
        return f"Agent {self.name} has moderate capability for this task based on available tools and past performance."

    async def _update_success_patterns(
        self, plan: AgentPlan, result: AgentResult, context: AgentContext
    ):
        """Update patterns that lead to successful executions."""
        # TODO: Implement pattern learning
        pass

    async def _update_failure_patterns(
        self, plan: AgentPlan, result: AgentResult, context: AgentContext
    ):
        """Update patterns that lead to failed executions."""
        # TODO: Implement failure pattern learning
        pass
