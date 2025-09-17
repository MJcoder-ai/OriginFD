"""
DesignEngineerAgent - Specialized AI agent for ODL-SD validation and design optimization.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..memory.episodic import EpisodicMemory
from ..memory.semantic import SemanticMemory
from ..tools.registry import ToolRegistry
from .base_agent import AgentCapability, AgentContext, AgentPlan, AgentResult, BaseAgent

logger = logging.getLogger(__name__)


class DesignEngineerAgent(BaseAgent):
    """
    Specialized AI agent for design engineering tasks.

    Capabilities:
    - ODL-SD document validation and analysis
    - Energy performance simulation
    - Design optimization recommendations
    - Component compatibility checking
    - Code compliance validation
    - Cost optimization analysis
    """

    def __init__(
        self,
        tool_registry: ToolRegistry,
        episodic_memory: EpisodicMemory,
        semantic_memory: SemanticMemory,
    ):
        # Define agent capabilities
        capabilities = [
            AgentCapability(
                name="odl_sd_validation",
                description="Validate ODL-SD documents for compliance and correctness",
                tools=["ValidateOdlTool", "CheckComplianceTool"],
                rbac_scope=["design_read", "design_write"],
                confidence_level=0.9,
            ),
            AgentCapability(
                name="energy_simulation",
                description="Run energy performance simulations and analysis",
                tools=["SimulateEnergyTool", "AnalyzePerformanceTool"],
                rbac_scope=["simulation_run", "design_read"],
                confidence_level=0.85,
            ),
            AgentCapability(
                name="design_optimization",
                description="Optimize designs for performance, cost, and compliance",
                tools=[
                    "OptimizeLayoutTool",
                    "OptimizeCostTool",
                    "SuggestImprovementsTool",
                ],
                rbac_scope=["design_write", "optimization_run"],
                confidence_level=0.8,
            ),
            AgentCapability(
                name="component_analysis",
                description="Analyze components and their compatibility",
                tools=["ComponentClassificationTool", "ComponentCompatibilityTool"],
                rbac_scope=["component_read", "design_read"],
                confidence_level=0.88,
            ),
        ]

        super().__init__(
            agent_id="design_engineer_agent",
            name="Design Engineer Agent",
            description="Specialized AI agent for ODL-SD validation, energy simulation, and design optimization",
            capabilities=capabilities,
            tool_registry=tool_registry,
            episodic_memory=episodic_memory,
            semantic_memory=semantic_memory,
        )

        # Agent-specific configuration
        self.supported_domains = ["PV", "BESS", "Hybrid"]
        self.simulation_confidence_threshold = 0.7
        self.optimization_improvement_threshold = 0.05  # 5% minimum improvement

        logger.info("DesignEngineerAgent initialized")

    @property
    def specialized_tools(self) -> List[str]:
        """List of tools this agent specializes in using."""
        return [
            "ValidateOdlTool",
            "SimulateEnergyTool",
            "SimulateFinanceTool",
            "OptimizeLayoutTool",
            "ComponentClassificationTool",
            "ComponentCompatibilityTool",
            "CheckComplianceTool",
        ]

    @property
    def primary_domain(self) -> str:
        """Primary domain this agent operates in."""
        return "design_engineering"

    async def create_plan(self, task: str, context: AgentContext) -> AgentPlan:
        """Create an execution plan for design engineering tasks."""
        plan_id = str(uuid4())
        steps = []

        task_lower = task.lower()

        # Determine task type and create appropriate plan
        if "validate" in task_lower and (
            "odl" in task_lower or "document" in task_lower
        ):
            steps = await self._plan_odl_validation(task, context)
        elif "simulate" in task_lower or "performance" in task_lower:
            steps = await self._plan_energy_simulation(task, context)
        elif "optimize" in task_lower:
            steps = await self._plan_design_optimization(task, context)
        elif "component" in task_lower and "analyz" in task_lower:
            steps = await self._plan_component_analysis(task, context)
        else:
            # General design engineering task
            steps = await self._plan_general_design_task(task, context)

        # Calculate plan estimates
        total_duration = sum(step["estimated_duration_ms"] for step in steps)
        total_cost = sum(step["estimated_cost_psu"] for step in steps)

        # Calculate confidence based on task complexity and available tools
        confidence = await self._calculate_plan_confidence(task, context, steps)

        plan = AgentPlan(
            plan_id=plan_id,
            steps=steps,
            estimated_duration_ms=total_duration,
            estimated_cost_psu=total_cost,
            tools_required=[
                step["tool_name"] for step in steps if step.get("tool_name")
            ],
            dependencies=[],
            confidence=confidence,
            reasoning=await self._generate_plan_reasoning(task, steps),
        )

        return plan

    async def execute_plan(self, plan: AgentPlan, context: AgentContext) -> AgentResult:
        """Execute the design engineering plan."""
        start_time = datetime.utcnow()
        execution_results = []
        tools_used = []

        try:
            logger.info(f"Executing design engineering plan: {plan.plan_id}")

            # Execute steps in order
            for i, step in enumerate(plan.steps):
                step_start = datetime.utcnow()

                logger.debug(
                    f"Executing step {i+1}/{len(plan.steps)}: {step['description']}"
                )

                if step.get("tool_name"):
                    # Execute tool
                    tool_result = await self.execute_tool(
                        tool_name=step["tool_name"],
                        inputs=step.get("inputs", {}),
                        context=context,
                    )

                    execution_results.append(tool_result)
                    tools_used.append(step["tool_name"])

                    # Check if step failed
                    if not tool_result.success:
                        logger.warning(
                            f"Step failed: {step['description']} - {tool_result.errors}"
                        )

                        # Try fallback if available
                        if step.get("fallback_tool"):
                            logger.info(
                                f"Trying fallback tool: {step['fallback_tool']}"
                            )
                            fallback_result = await self.execute_tool(
                                tool_name=step["fallback_tool"],
                                inputs=step.get("inputs", {}),
                                context=context,
                            )
                            execution_results.append(fallback_result)
                            tools_used.append(step["fallback_tool"])
                else:
                    # Non-tool step (analysis, synthesis, etc.)
                    step_result = await self._execute_analysis_step(
                        step, context, execution_results
                    )
                    execution_results.append(step_result)

                step_duration = (datetime.utcnow() - step_start).total_seconds() * 1000
                logger.debug(f"Step completed in {step_duration:.0f}ms")

            # Synthesize final results
            final_result = await self._synthesize_results(
                task_description=context.current_state.get("task_description", ""),
                execution_results=execution_results,
                context=context,
            )

            execution_time = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )

            # Calculate quality score
            quality_score = await self._calculate_quality_score(
                execution_results, final_result
            )

            result = AgentResult(
                success=True,
                result=final_result,
                plan_executed=plan,
                tools_used=tools_used,
                execution_time_ms=execution_time,
                psu_cost=sum(step["estimated_cost_psu"] for step in plan.steps),
                quality_score=quality_score,
                confidence=min(
                    [r.get("confidence", 1.0) for r in execution_results] + [1.0]
                ),
                next_actions=await self._suggest_next_actions(final_result, context),
            )

            logger.info(
                f"Design engineering plan executed successfully in {execution_time}ms"
            )
            return result

        except Exception as e:
            logger.error(f"Design engineering plan execution failed: {str(e)}")

            execution_time = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )

            return AgentResult(
                success=False,
                error=str(e),
                plan_executed=plan,
                tools_used=tools_used,
                execution_time_ms=execution_time,
                psu_cost=0,
                quality_score=0.0,
                confidence=0.0,
            )

    # Private planning methods

    async def _plan_odl_validation(
        self, task: str, context: AgentContext
    ) -> List[Dict[str, Any]]:
        """Plan ODL-SD document validation."""
        steps = [
            {
                "step_id": str(uuid4()),
                "description": "Validate ODL-SD document structure and syntax",
                "tool_name": "ValidateOdlTool",
                "inputs": {
                    "document": context.current_state.get("odl_document"),
                    "validation_level": "comprehensive",
                },
                "estimated_duration_ms": 3000,
                "estimated_cost_psu": 5,
                "fallback_tool": None,
            },
            {
                "step_id": str(uuid4()),
                "description": "Check design compliance with standards",
                "tool_name": "CheckComplianceTool",
                "inputs": {
                    "design_data": "from_previous_step",
                    "standards": context.current_state.get(
                        "compliance_standards", ["NEC", "IEEE"]
                    ),
                },
                "estimated_duration_ms": 2500,
                "estimated_cost_psu": 4,
            },
            {
                "step_id": str(uuid4()),
                "description": "Generate validation report and recommendations",
                "tool_name": None,  # Analysis step
                "estimated_duration_ms": 1500,
                "estimated_cost_psu": 2,
            },
        ]

        return steps

    async def _plan_energy_simulation(
        self, task: str, context: AgentContext
    ) -> List[Dict[str, Any]]:
        """Plan energy performance simulation."""
        steps = [
            {
                "step_id": str(uuid4()),
                "description": "Prepare simulation parameters",
                "tool_name": None,
                "estimated_duration_ms": 1000,
                "estimated_cost_psu": 1,
            },
            {
                "step_id": str(uuid4()),
                "description": "Run energy performance simulation",
                "tool_name": "SimulateEnergyTool",
                "inputs": {
                    "design_data": context.current_state.get("design_data"),
                    "location": context.current_state.get("location"),
                    "simulation_period": context.current_state.get(
                        "simulation_period", "annual"
                    ),
                },
                "estimated_duration_ms": 8000,
                "estimated_cost_psu": 12,
            },
            {
                "step_id": str(uuid4()),
                "description": "Analyze simulation results and identify optimization opportunities",
                "tool_name": "AnalyzePerformanceTool",
                "inputs": {"simulation_results": "from_previous_step"},
                "estimated_duration_ms": 3000,
                "estimated_cost_psu": 5,
            },
        ]

        return steps

    async def _plan_design_optimization(
        self, task: str, context: AgentContext
    ) -> List[Dict[str, Any]]:
        """Plan design optimization."""
        steps = [
            {
                "step_id": str(uuid4()),
                "description": "Analyze current design performance",
                "tool_name": "SimulateEnergyTool",
                "inputs": {"design_data": context.current_state.get("design_data")},
                "estimated_duration_ms": 5000,
                "estimated_cost_psu": 8,
            },
            {
                "step_id": str(uuid4()),
                "description": "Optimize component layout",
                "tool_name": "OptimizeLayoutTool",
                "inputs": {
                    "current_layout": context.current_state.get("layout_data"),
                    "optimization_goals": context.current_state.get(
                        "optimization_goals", ["performance", "cost"]
                    ),
                },
                "estimated_duration_ms": 6000,
                "estimated_cost_psu": 10,
            },
            {
                "step_id": str(uuid4()),
                "description": "Optimize for cost efficiency",
                "tool_name": "OptimizeCostTool",
                "inputs": {
                    "design_data": "from_previous_steps",
                    "budget_constraints": context.current_state.get(
                        "budget_constraints"
                    ),
                },
                "estimated_duration_ms": 4000,
                "estimated_cost_psu": 7,
            },
            {
                "step_id": str(uuid4()),
                "description": "Generate optimization recommendations",
                "tool_name": "SuggestImprovementsTool",
                "inputs": {
                    "original_design": context.current_state.get("design_data"),
                    "optimized_designs": "from_previous_steps",
                },
                "estimated_duration_ms": 2000,
                "estimated_cost_psu": 3,
            },
        ]

        return steps

    async def _plan_component_analysis(
        self, task: str, context: AgentContext
    ) -> List[Dict[str, Any]]:
        """Plan component analysis."""
        steps = [
            {
                "step_id": str(uuid4()),
                "description": "Classify components with industry standards",
                "tool_name": "ComponentClassificationTool",
                "inputs": {
                    "components": context.current_state.get("components"),
                    "classification_standards": ["UNSPSC", "eCl@ss"],
                },
                "estimated_duration_ms": 3000,
                "estimated_cost_psu": 5,
            },
            {
                "step_id": str(uuid4()),
                "description": "Check component compatibility",
                "tool_name": "ComponentCompatibilityTool",
                "inputs": {
                    "components": "from_previous_step",
                    "system_requirements": context.current_state.get(
                        "system_requirements"
                    ),
                },
                "estimated_duration_ms": 2500,
                "estimated_cost_psu": 4,
            },
            {
                "step_id": str(uuid4()),
                "description": "Generate component analysis report",
                "tool_name": None,
                "estimated_duration_ms": 1500,
                "estimated_cost_psu": 2,
            },
        ]

        return steps

    async def _plan_general_design_task(
        self, task: str, context: AgentContext
    ) -> List[Dict[str, Any]]:
        """Plan general design engineering task."""
        steps = [
            {
                "step_id": str(uuid4()),
                "description": "Analyze design requirements",
                "tool_name": None,
                "estimated_duration_ms": 2000,
                "estimated_cost_psu": 3,
            },
            {
                "step_id": str(uuid4()),
                "description": "Validate design against standards",
                "tool_name": "ValidateOdlTool",
                "inputs": {"document": context.current_state.get("design_data")},
                "estimated_duration_ms": 3000,
                "estimated_cost_psu": 5,
            },
            {
                "step_id": str(uuid4()),
                "description": "Provide design recommendations",
                "tool_name": None,
                "estimated_duration_ms": 2000,
                "estimated_cost_psu": 3,
            },
        ]

        return steps

    # Private execution methods

    async def _execute_analysis_step(
        self, step: Dict[str, Any], context: AgentContext, previous_results: List[Any]
    ) -> Dict[str, Any]:
        """Execute a non-tool analysis step."""
        step_description = step["description"]

        if "prepare simulation" in step_description.lower():
            # Prepare simulation parameters
            return {
                "success": True,
                "content": {
                    "simulation_parameters": {
                        "timestep": "hourly",
                        "weather_data": "TMY3",
                        "analysis_period": "annual",
                    }
                },
                "confidence": 0.9,
            }

        elif "analyze" in step_description.lower():
            # Perform analysis on previous results
            analysis_result = {
                "analysis_summary": f"Completed {step_description}",
                "key_findings": [],
                "recommendations": [],
            }

            # Extract insights from previous results
            for result in previous_results:
                if hasattr(result, "content") and result.content:
                    if isinstance(result.content, dict):
                        if "performance" in result.content:
                            analysis_result["key_findings"].append(
                                "Performance data analyzed"
                            )
                        if "efficiency" in result.content:
                            analysis_result["key_findings"].append(
                                "Efficiency metrics extracted"
                            )

            return {"success": True, "content": analysis_result, "confidence": 0.85}

        elif (
            "generate" in step_description.lower()
            and "report" in step_description.lower()
        ):
            # Generate report
            return {
                "success": True,
                "content": {
                    "report_type": "design_engineering_analysis",
                    "timestamp": datetime.utcnow().isoformat(),
                    "summary": f"Generated report for: {step_description}",
                    "sections": [
                        "Executive Summary",
                        "Technical Analysis",
                        "Recommendations",
                    ],
                },
                "confidence": 0.9,
            }

        else:
            # Generic analysis step
            return {
                "success": True,
                "content": {
                    "step_completed": step_description,
                    "timestamp": datetime.utcnow().isoformat(),
                },
                "confidence": 0.8,
            }

    async def _synthesize_results(
        self, task_description: str, execution_results: List[Any], context: AgentContext
    ) -> Dict[str, Any]:
        """Synthesize execution results into final output."""
        synthesis = {
            "task_description": task_description,
            "execution_summary": {
                "total_steps": len(execution_results),
                "successful_steps": sum(
                    1 for r in execution_results if getattr(r, "success", True)
                ),
                "execution_timestamp": datetime.utcnow().isoformat(),
            },
            "key_findings": [],
            "recommendations": [],
            "technical_details": {},
            "next_steps": [],
        }

        # Extract key information from results
        for i, result in enumerate(execution_results):
            if hasattr(result, "content") and result.content:
                content = result.content

                if isinstance(content, dict):
                    # Extract validation results
                    if "validation" in str(content).lower():
                        synthesis["key_findings"].append("Design validation completed")
                        if "compliance" in content:
                            synthesis["technical_details"]["compliance_status"] = (
                                content.get("compliance")
                            )

                    # Extract simulation results
                    if (
                        "simulation" in str(content).lower()
                        or "performance" in str(content).lower()
                    ):
                        synthesis["key_findings"].append(
                            "Performance simulation completed"
                        )
                        if "energy_output" in content:
                            synthesis["technical_details"]["energy_performance"] = (
                                content.get("energy_output")
                            )

                    # Extract optimization results
                    if (
                        "optimization" in str(content).lower()
                        or "improvement" in str(content).lower()
                    ):
                        synthesis["key_findings"].append(
                            "Design optimization completed"
                        )
                        if "improvements" in content:
                            synthesis["recommendations"].extend(
                                content.get("improvements", [])
                            )

        # Generate recommendations based on task type
        if "optimize" in task_description.lower():
            synthesis["recommendations"].append(
                "Review optimization suggestions and implement high-impact changes"
            )
            synthesis["next_steps"].append("Run validation tests on optimized design")

        if "validate" in task_description.lower():
            synthesis["recommendations"].append(
                "Address any compliance issues identified"
            )
            synthesis["next_steps"].append(
                "Update design documentation with validation results"
            )

        if "simulate" in task_description.lower():
            synthesis["recommendations"].append(
                "Analyze performance metrics against requirements"
            )
            synthesis["next_steps"].append(
                "Consider optimization opportunities identified"
            )

        return synthesis

    async def _calculate_quality_score(
        self, execution_results: List[Any], final_result: Dict[str, Any]
    ) -> float:
        """Calculate quality score for the execution."""
        if not execution_results:
            return 0.0

        # Base score from successful execution
        successful_steps = sum(
            1 for r in execution_results if getattr(r, "success", True)
        )
        success_rate = successful_steps / len(execution_results)

        # Confidence score from results
        confidences = [
            getattr(r, "confidence", 0.8)
            for r in execution_results
            if hasattr(r, "confidence")
        ]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.8

        # Completeness score
        completeness = (
            1.0
            if final_result.get("key_findings") and final_result.get("recommendations")
            else 0.7
        )

        # Weighted final score
        quality_score = (
            (success_rate * 0.4) + (avg_confidence * 0.4) + (completeness * 0.2)
        )

        return min(quality_score, 1.0)

    async def _suggest_next_actions(
        self, result: Dict[str, Any], context: AgentContext
    ) -> List[str]:
        """Suggest next actions based on results."""
        next_actions = []

        # Based on result content
        if "validation" in str(result).lower():
            next_actions.append("Review validation results and address any issues")
            next_actions.append("Update design documentation")

        if "optimization" in str(result).lower():
            next_actions.append("Implement recommended optimizations")
            next_actions.append("Re-run validation after changes")

        if "simulation" in str(result).lower():
            next_actions.append("Analyze performance against requirements")
            next_actions.append("Consider design modifications for improvement")

        # Default actions
        if not next_actions:
            next_actions.append("Review results with stakeholders")
            next_actions.append("Document findings and recommendations")

        return next_actions

    async def _calculate_plan_confidence(
        self, task: str, context: AgentContext, steps: List[Dict[str, Any]]
    ) -> float:
        """Calculate confidence in the execution plan."""
        base_confidence = 0.8

        # Adjust based on task complexity
        task_lower = task.lower()
        if any(word in task_lower for word in ["complex", "advanced", "comprehensive"]):
            base_confidence -= 0.1

        # Adjust based on available context
        if context.current_state.get("design_data"):
            base_confidence += 0.05
        if context.current_state.get("requirements"):
            base_confidence += 0.05

        # Adjust based on tool availability
        required_tools = [
            step.get("tool_name") for step in steps if step.get("tool_name")
        ]
        # TODO: Check actual tool availability

        return min(base_confidence, 1.0)

    async def _generate_plan_reasoning(
        self, task: str, steps: List[Dict[str, Any]]
    ) -> str:
        """Generate reasoning for the execution plan."""
        reasoning_parts = [
            f"Created {len(steps)}-step plan for design engineering task: {task}"
        ]

        # Categorize steps
        tool_steps = [s for s in steps if s.get("tool_name")]
        analysis_steps = [s for s in steps if not s.get("tool_name")]

        if tool_steps:
            reasoning_parts.append(
                f"Plan includes {len(tool_steps)} tool executions for technical analysis"
            )

        if analysis_steps:
            reasoning_parts.append(
                f"Plan includes {len(analysis_steps)} analysis steps for synthesis and recommendations"
            )

        # Mention specific capabilities used
        if any("validate" in s["description"].lower() for s in steps):
            reasoning_parts.append(
                "Validation capabilities will ensure design compliance"
            )

        if any("simulate" in s["description"].lower() for s in steps):
            reasoning_parts.append(
                "Simulation capabilities will provide performance insights"
            )

        if any("optimize" in s["description"].lower() for s in steps):
            reasoning_parts.append(
                "Optimization capabilities will identify improvement opportunities"
            )

        return " ".join(reasoning_parts)
