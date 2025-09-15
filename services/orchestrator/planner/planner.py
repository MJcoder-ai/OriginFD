"""
Task Planner for OriginFD AI Orchestrator.
Creates execution plans with grounding and tool selection.
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4
from pydantic import BaseModel
from enum import Enum

try:
    from model_registry import ModelInfo
except ImportError:  # pragma: no cover - makes module work without registry
    ModelInfo = None  # type: ignore

try:
    from ..memory.semantic import SemanticMemory
    from ..memory.episodic import EpisodicMemory
    from ..tools.registry import ToolRegistry, ToolMetadata
except ImportError:
    # For standalone testing
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from memory.semantic import SemanticMemory
    from memory.episodic import EpisodicMemory
    from tools.registry import ToolRegistry, ToolMetadata

logger = logging.getLogger(__name__)


class PlanStepType(str, Enum):
    """Types of plan steps."""
    GROUNDING = "grounding"
    TOOL_EXECUTION = "tool_execution"
    VALIDATION = "validation"
    SYNTHESIS = "synthesis"
    HANDOVER = "handover"


class PlanStep(BaseModel):
    """Individual step in an execution plan."""
    step_id: str
    step_type: PlanStepType
    description: str
    tool_name: Optional[str] = None
    inputs: Dict[str, Any] = {}
    expected_outputs: Dict[str, Any] = {}
    dependencies: List[str] = []  # Step IDs this step depends on
    parallel_group: Optional[str] = None  # Steps that can run in parallel
    estimated_duration_ms: int = 1000
    estimated_cost_psu: int = 1
    confidence: float = 1.0
    fallback_steps: List[str] = []  # Alternative steps if this fails


class PlanningResult(BaseModel):
    """Result of the planning process."""
    plan_id: str
    task_type: str
    task_description: str
    steps: List[PlanStep]
    total_estimated_duration_ms: int
    total_estimated_cost_psu: int
    confidence: float
    grounding_sources: List[str] = []
    reasoning: str
    created_at: datetime
    metadata: Dict[str, Any] = {}


class TaskPlanner:
    """
    AI Task Planner that creates execution plans with grounding.

    Features:
    - Task decomposition into executable steps
    - Tool selection and dependency management
    - Grounding with semantic memory
    - Cost and time estimation
    - Parallel execution planning
    - Fallback strategy generation
    """

    def __init__(
        self,
        semantic_memory: Optional[SemanticMemory] = None,
        episodic_memory: Optional[EpisodicMemory] = None,
        tool_registry: Optional[ToolRegistry] = None
    ):
        self.semantic_memory = semantic_memory
        self.episodic_memory = episodic_memory
        self.tool_registry = tool_registry

        # Planning configuration
        self.max_plan_steps = 20
        self.max_planning_time_ms = 5000
        self.min_confidence_threshold = 0.6

        # Task type handlers
        self.task_handlers = {
            "component_analysis": self._plan_component_analysis,
            "design_validation": self._plan_design_validation,
            "project_optimization": self._plan_project_optimization,
            "procurement_assistance": self._plan_procurement_assistance,
            "simulation_request": self._plan_simulation_request,
            "general_query": self._plan_general_query
        }

        logger.info("TaskPlanner initialized")

    async def create_plan(
        self,
        task_type: str,
        task_description: str,
        context: Dict[str, Any],
        region_config: Optional[Dict[str, Any]] = None,
        model_info: Optional["ModelInfo"] = None,
        fallback_models: Optional[List["ModelInfo"]] = None,
    ) -> PlanningResult:
        """Create an execution plan for the given task."""
        start_time = datetime.utcnow()
        plan_id = str(uuid4())

        logger.info(f"Creating plan for task: {task_type} - {task_description}")

        try:
            # Step 1: Analyze task and gather grounding
            grounding_info = await self._gather_grounding(task_description, context)

            # Step 2: Select appropriate planning strategy
            handler = self.task_handlers.get(task_type, self._plan_general_query)

            # Step 3: Create plan steps
            steps = await handler(task_description, context, grounding_info)

            # Step 4: Optimize plan (parallel execution, cost optimization)
            optimized_steps = await self._optimize_plan(steps, context)

            # Step 5: Calculate estimates and confidence
            total_duration, total_cost, confidence = await self._calculate_plan_metrics(optimized_steps)

            # Step 6: Generate reasoning
            reasoning = await self._generate_plan_reasoning(
                task_type, task_description, optimized_steps, grounding_info
            )

            metadata = {
                    "region_config": region_config,
                    "context_summary": self._summarize_context(context),
                    "planning_time_ms": int((datetime.utcnow() - start_time).total_seconds() * 1000),
                }
            if model_info is not None:
                metadata["model"] = model_info.dict()
            if fallback_models:
                metadata["fallback_models"] = [m.dict() for m in fallback_models]

            plan = PlanningResult(
                plan_id=plan_id,
                task_type=task_type,
                task_description=task_description,
                steps=optimized_steps,
                total_estimated_duration_ms=total_duration,
                total_estimated_cost_psu=total_cost,
                confidence=confidence,
                grounding_sources=grounding_info.get("sources", []),
                reasoning=reasoning,
                created_at=start_time,
                metadata=metadata,
            )

            # Store plan in episodic memory
            if self.episodic_memory:
                await self.episodic_memory.store_interaction(
                    session_id=context.get("session_id", "system"),
                    interaction_type="plan_created",
                    content={
                        "plan_id": plan_id,
                        "task_type": task_type,
                        "steps_count": len(optimized_steps),
                        "confidence": confidence
                    },
                    agent_id="task_planner"
                )

            logger.info(f"Plan created: {plan_id} with {len(optimized_steps)} steps (confidence: {confidence:.2f})")
            return plan

        except Exception as e:
            logger.error(f"Planning failed for task {task_type}: {str(e)}")

            # Return minimal fallback plan
            fallback_step = PlanStep(
                step_id=str(uuid4()),
                step_type=PlanStepType.SYNTHESIS,
                description="Fallback: Provide basic response",
                estimated_duration_ms=500,
                estimated_cost_psu=1,
                confidence=0.3
            )

            return PlanningResult(
                plan_id=plan_id,
                task_type=task_type,
                task_description=task_description,
                steps=[fallback_step],
                total_estimated_duration_ms=500,
                total_estimated_cost_psu=1,
                confidence=0.3,
                reasoning=f"Planning failed: {str(e)}. Using fallback strategy.",
                created_at=start_time
            )

    async def _gather_grounding(
        self,
        task_description: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Gather grounding information from semantic memory and context."""
        grounding_info = {
            "relevant_knowledge": [],
            "applicable_patterns": [],
            "sources": [],
            "context_analysis": {}
        }

        if self.semantic_memory:
            # Retrieve relevant knowledge
            knowledge_items = await self.semantic_memory.retrieve_knowledge(
                query=task_description,
                limit=5
            )

            for item, score in knowledge_items:
                grounding_info["relevant_knowledge"].append({
                    "knowledge_id": item.knowledge_id,
                    "title": item.title,
                    "content": item.content[:200] + "..." if len(item.content) > 200 else item.content,
                    "relevance_score": score,
                    "confidence": item.confidence
                })
                grounding_info["sources"].append(f"knowledge:{item.knowledge_id}")

            # Find applicable patterns
            patterns = await self.semantic_memory.find_applicable_patterns(
                current_conditions=context,
                min_success_rate=0.7
            )

            for pattern, match_score in patterns:
                grounding_info["applicable_patterns"].append({
                    "pattern_id": pattern.pattern_id,
                    "description": pattern.description,
                    "actions": pattern.actions,
                    "success_rate": pattern.success_rate,
                    "match_score": match_score
                })
                grounding_info["sources"].append(f"pattern:{pattern.pattern_id}")

        # Analyze context for domain-specific information
        grounding_info["context_analysis"] = {
            "domain": context.get("domain", "general"),
            "project_type": context.get("project_type"),
            "user_role": context.get("user_role"),
            "complexity_indicators": self._analyze_complexity(task_description, context)
        }

        return grounding_info

    # Task-specific planning methods

    async def _plan_component_analysis(
        self,
        task_description: str,
        context: Dict[str, Any],
        grounding_info: Dict[str, Any]
    ) -> List[PlanStep]:
        """Plan for component analysis tasks."""
        steps = []

        # Step 1: Parse component data if needed
        if "datasheet" in task_description.lower() or "pdf" in context:
            steps.append(PlanStep(
                step_id=str(uuid4()),
                step_type=PlanStepType.TOOL_EXECUTION,
                description="Parse component datasheet",
                tool_name="ParseDatasheetTool",
                inputs={"document_url": context.get("document_url")},
                estimated_duration_ms=3000,
                estimated_cost_psu=5
            ))

        # Step 2: Classify component
        classify_step = PlanStep(
            step_id=str(uuid4()),
            step_type=PlanStepType.TOOL_EXECUTION,
            description="Classify component with standards",
            tool_name="ComponentClassificationTool",
            inputs={"component_data": "from_previous_step"},
            estimated_duration_ms=2000,
            estimated_cost_psu=3
        )
        if steps:
            classify_step.dependencies = [steps[-1].step_id]
        steps.append(classify_step)

        # Step 3: Find similar components (deduplication)
        dedupe_step = PlanStep(
            step_id=str(uuid4()),
            step_type=PlanStepType.TOOL_EXECUTION,
            description="Find similar/duplicate components",
            tool_name="ComponentDeduplicationTool",
            inputs={"component_specs": "from_previous_step"},
            dependencies=[classify_step.step_id],
            estimated_duration_ms=2500,
            estimated_cost_psu=4
        )
        steps.append(dedupe_step)

        # Step 4: Generate recommendations
        recommend_step = PlanStep(
            step_id=str(uuid4()),
            step_type=PlanStepType.TOOL_EXECUTION,
            description="Generate component recommendations",
            tool_name="ComponentRecommendationTool",
            inputs={"analysis_results": "from_previous_steps"},
            dependencies=[classify_step.step_id, dedupe_step.step_id],
            estimated_duration_ms=1500,
            estimated_cost_psu=2
        )
        steps.append(recommend_step)

        # Step 5: Synthesize results
        synthesis_step = PlanStep(
            step_id=str(uuid4()),
            step_type=PlanStepType.SYNTHESIS,
            description="Synthesize component analysis results",
            dependencies=[step.step_id for step in steps],
            estimated_duration_ms=1000,
            estimated_cost_psu=1
        )
        steps.append(synthesis_step)

        return steps

    async def _plan_design_validation(
        self,
        task_description: str,
        context: Dict[str, Any],
        grounding_info: Dict[str, Any]
    ) -> List[PlanStep]:
        """Plan for design validation tasks."""
        steps = []

        # Step 1: Validate ODL-SD document
        validate_step = PlanStep(
            step_id=str(uuid4()),
            step_type=PlanStepType.TOOL_EXECUTION,
            description="Validate ODL-SD document structure",
            tool_name="ValidateOdlTool",
            inputs={"document": context.get("odl_document")},
            estimated_duration_ms=2000,
            estimated_cost_psu=3
        )
        steps.append(validate_step)

        # Step 2: Run energy simulation
        simulation_step = PlanStep(
            step_id=str(uuid4()),
            step_type=PlanStepType.TOOL_EXECUTION,
            description="Run energy performance simulation",
            tool_name="SimulateEnergyTool",
            inputs={"design_data": "from_validation"},
            dependencies=[validate_step.step_id],
            estimated_duration_ms=5000,
            estimated_cost_psu=8
        )
        steps.append(simulation_step)

        # Step 3: Financial analysis
        finance_step = PlanStep(
            step_id=str(uuid4()),
            step_type=PlanStepType.TOOL_EXECUTION,
            description="Calculate financial metrics",
            tool_name="SimulateFinanceTool",
            inputs={"energy_results": "from_simulation", "cost_data": context.get("cost_data")},
            dependencies=[simulation_step.step_id],
            estimated_duration_ms=3000,
            estimated_cost_psu=5,
            parallel_group="analysis"
        )
        steps.append(finance_step)

        # Step 4: Compliance checking (parallel with finance)
        compliance_step = PlanStep(
            step_id=str(uuid4()),
            step_type=PlanStepType.VALIDATION,
            description="Check design compliance",
            dependencies=[validate_step.step_id],
            estimated_duration_ms=2500,
            estimated_cost_psu=4,
            parallel_group="analysis"
        )
        steps.append(compliance_step)

        # Step 5: Generate optimization suggestions
        optimize_step = PlanStep(
            step_id=str(uuid4()),
            step_type=PlanStepType.SYNTHESIS,
            description="Generate optimization recommendations",
            dependencies=[finance_step.step_id, compliance_step.step_id],
            estimated_duration_ms=2000,
            estimated_cost_psu=3
        )
        steps.append(optimize_step)

        return steps

    async def _plan_project_optimization(
        self,
        task_description: str,
        context: Dict[str, Any],
        grounding_info: Dict[str, Any]
    ) -> List[PlanStep]:
        """Plan for project optimization tasks."""
        steps = []

        # Use applicable patterns from grounding
        for pattern_info in grounding_info.get("applicable_patterns", []):
            for action in pattern_info["actions"][:3]:  # Limit to top 3 actions
                step = PlanStep(
                    step_id=str(uuid4()),
                    step_type=PlanStepType.TOOL_EXECUTION,
                    description=f"Execute optimization action: {action}",
                    tool_name=self._map_action_to_tool(action),
                    estimated_duration_ms=2000,
                    estimated_cost_psu=3,
                    confidence=pattern_info["success_rate"] * pattern_info["match_score"]
                )
                steps.append(step)

        # If no patterns found, use default optimization approach
        if not steps:
            steps.extend([
                PlanStep(
                    step_id=str(uuid4()),
                    step_type=PlanStepType.TOOL_EXECUTION,
                    description="Analyze current project configuration",
                    estimated_duration_ms=2000,
                    estimated_cost_psu=3
                ),
                PlanStep(
                    step_id=str(uuid4()),
                    step_type=PlanStepType.TOOL_EXECUTION,
                    description="Identify optimization opportunities",
                    dependencies=[steps[0].step_id] if steps else [],
                    estimated_duration_ms=3000,
                    estimated_cost_psu=5
                ),
                PlanStep(
                    step_id=str(uuid4()),
                    step_type=PlanStepType.SYNTHESIS,
                    description="Generate optimization plan",
                    dependencies=[steps[1].step_id] if len(steps) > 1 else [],
                    estimated_duration_ms=1500,
                    estimated_cost_psu=2
                )
            ])

        return steps

    async def _plan_procurement_assistance(
        self,
        task_description: str,
        context: Dict[str, Any],
        grounding_info: Dict[str, Any]
    ) -> List[PlanStep]:
        """Plan for procurement assistance tasks."""
        steps = []

        # Step 1: Analyze BOM or component requirements
        analyze_step = PlanStep(
            step_id=str(uuid4()),
            step_type=PlanStepType.TOOL_EXECUTION,
            description="Analyze procurement requirements",
            inputs={"bom_data": context.get("bom"), "requirements": context.get("requirements")},
            estimated_duration_ms=2000,
            estimated_cost_psu=3
        )
        steps.append(analyze_step)

        # Step 2: Generate RFQ
        rfq_step = PlanStep(
            step_id=str(uuid4()),
            step_type=PlanStepType.TOOL_EXECUTION,
            description="Generate RFQ documents",
            tool_name="RFQGeneratorTool",
            inputs={"requirements": "from_analysis"},
            dependencies=[analyze_step.step_id],
            estimated_duration_ms=3000,
            estimated_cost_psu=4
        )
        steps.append(rfq_step)

        # Step 3: Find suitable suppliers
        supplier_step = PlanStep(
            step_id=str(uuid4()),
            step_type=PlanStepType.TOOL_EXECUTION,
            description="Match suppliers to requirements",
            tool_name="SupplierMatchingTool",
            inputs={"component_specs": "from_analysis"},
            dependencies=[analyze_step.step_id],
            estimated_duration_ms=2500,
            estimated_cost_psu=4,
            parallel_group="sourcing"
        )
        steps.append(supplier_step)

        # Step 4: Price analysis (parallel with supplier matching)
        price_step = PlanStep(
            step_id=str(uuid4()),
            step_type=PlanStepType.TOOL_EXECUTION,
            description="Analyze market prices",
            tool_name="PriceAnalysisTool",
            dependencies=[analyze_step.step_id],
            estimated_duration_ms=2000,
            estimated_cost_psu=3,
            parallel_group="sourcing"
        )
        steps.append(price_step)

        # Step 5: Generate procurement recommendations
        recommend_step = PlanStep(
            step_id=str(uuid4()),
            step_type=PlanStepType.SYNTHESIS,
            description="Generate procurement recommendations",
            dependencies=[rfq_step.step_id, supplier_step.step_id, price_step.step_id],
            estimated_duration_ms=1500,
            estimated_cost_psu=2
        )
        steps.append(recommend_step)

        return steps

    async def _plan_simulation_request(
        self,
        task_description: str,
        context: Dict[str, Any],
        grounding_info: Dict[str, Any]
    ) -> List[PlanStep]:
        """Plan for simulation requests."""
        steps = []

        # Determine simulation type
        sim_type = self._determine_simulation_type(task_description, context)

        if sim_type == "energy":
            steps.append(PlanStep(
                step_id=str(uuid4()),
                step_type=PlanStepType.TOOL_EXECUTION,
                description="Run energy performance simulation",
                tool_name="SimulateEnergyTool",
                inputs={"design_data": context.get("design_data")},
                estimated_duration_ms=5000,
                estimated_cost_psu=8
            ))
        elif sim_type == "financial":
            steps.append(PlanStep(
                step_id=str(uuid4()),
                step_type=PlanStepType.TOOL_EXECUTION,
                description="Run financial analysis simulation",
                tool_name="SimulateFinanceTool",
                inputs={"financial_data": context.get("financial_data")},
                estimated_duration_ms=3000,
                estimated_cost_psu=5
            ))
        else:
            # Multi-type simulation
            energy_step = PlanStep(
                step_id=str(uuid4()),
                step_type=PlanStepType.TOOL_EXECUTION,
                description="Run energy simulation",
                tool_name="SimulateEnergyTool",
                estimated_duration_ms=5000,
                estimated_cost_psu=8,
                parallel_group="simulation"
            )

            finance_step = PlanStep(
                step_id=str(uuid4()),
                step_type=PlanStepType.TOOL_EXECUTION,
                description="Run financial simulation",
                tool_name="SimulateFinanceTool",
                estimated_duration_ms=3000,
                estimated_cost_psu=5,
                parallel_group="simulation"
            )

            synthesis_step = PlanStep(
                step_id=str(uuid4()),
                step_type=PlanStepType.SYNTHESIS,
                description="Combine simulation results",
                dependencies=[energy_step.step_id, finance_step.step_id],
                estimated_duration_ms=1000,
                estimated_cost_psu=2
            )

            steps.extend([energy_step, finance_step, synthesis_step])

        return steps

    async def _plan_general_query(
        self,
        task_description: str,
        context: Dict[str, Any],
        grounding_info: Dict[str, Any]
    ) -> List[PlanStep]:
        """Plan for general queries."""
        steps = []

        # Step 1: Ground the query with relevant knowledge
        grounding_step = PlanStep(
            step_id=str(uuid4()),
            step_type=PlanStepType.GROUNDING,
            description="Gather relevant knowledge for query",
            inputs={"query": task_description, "context": context},
            estimated_duration_ms=1500,
            estimated_cost_psu=2
        )
        steps.append(grounding_step)

        # Step 2: Generate response
        response_step = PlanStep(
            step_id=str(uuid4()),
            step_type=PlanStepType.SYNTHESIS,
            description="Generate grounded response",
            dependencies=[grounding_step.step_id],
            estimated_duration_ms=2000,
            estimated_cost_psu=3
        )
        steps.append(response_step)

        return steps

    # Helper methods

    async def _optimize_plan(
        self,
        steps: List[PlanStep],
        context: Dict[str, Any]
    ) -> List[PlanStep]:
        """Optimize plan for parallel execution and cost efficiency."""
        # Group steps by parallel_group
        parallel_groups = {}
        for step in steps:
            if step.parallel_group:
                if step.parallel_group not in parallel_groups:
                    parallel_groups[step.parallel_group] = []
                parallel_groups[step.parallel_group].append(step)

        # Validate dependencies
        step_ids = {step.step_id for step in steps}
        for step in steps:
            step.dependencies = [dep for dep in step.dependencies if dep in step_ids]

        # TODO: Implement more sophisticated optimization
        # - Cost-based tool selection
        # - Parallel execution optimization
        # - Dependency optimization

        return steps

    async def _calculate_plan_metrics(
        self,
        steps: List[PlanStep]
    ) -> Tuple[int, int, float]:
        """Calculate total duration, cost, and confidence for plan."""
        # Calculate parallel execution groups
        parallel_groups = {}
        sequential_steps = []

        for step in steps:
            if step.parallel_group:
                if step.parallel_group not in parallel_groups:
                    parallel_groups[step.parallel_group] = []
                parallel_groups[step.parallel_group].append(step)
            else:
                sequential_steps.append(step)

        # Calculate duration (considering parallel execution)
        total_duration = sum(step.estimated_duration_ms for step in sequential_steps)

        for group_steps in parallel_groups.values():
            # Parallel steps take the time of the longest step
            max_duration = max(step.estimated_duration_ms for step in group_steps)
            total_duration += max_duration

        # Calculate total cost (all steps contribute)
        total_cost = sum(step.estimated_cost_psu for step in steps)

        # Calculate overall confidence (weighted average)
        if steps:
            total_weight = sum(step.estimated_cost_psu for step in steps)
            weighted_confidence = sum(
                step.confidence * step.estimated_cost_psu for step in steps
            ) / total_weight if total_weight > 0 else 0.5
        else:
            weighted_confidence = 0.5

        return total_duration, total_cost, weighted_confidence

    async def _generate_plan_reasoning(
        self,
        task_type: str,
        task_description: str,
        steps: List[PlanStep],
        grounding_info: Dict[str, Any]
    ) -> str:
        """Generate human-readable reasoning for the plan."""
        reasoning_parts = [
            f"Created a {len(steps)}-step plan for {task_type} task."
        ]

        # Mention grounding sources
        if grounding_info.get("relevant_knowledge"):
            knowledge_count = len(grounding_info["relevant_knowledge"])
            reasoning_parts.append(f"Grounded with {knowledge_count} relevant knowledge items.")

        if grounding_info.get("applicable_patterns"):
            pattern_count = len(grounding_info["applicable_patterns"])
            reasoning_parts.append(f"Applied {pattern_count} learned patterns from past successes.")

        # Mention parallel execution
        parallel_steps = [s for s in steps if s.parallel_group]
        if parallel_steps:
            reasoning_parts.append(f"Optimized for parallel execution of {len(parallel_steps)} steps.")

        # Mention tool usage
        tool_steps = [s for s in steps if s.tool_name]
        if tool_steps:
            unique_tools = set(s.tool_name for s in tool_steps if s.tool_name)
            reasoning_parts.append(f"Will use {len(unique_tools)} specialized tools.")

        return " ".join(reasoning_parts)

    def _analyze_complexity(
        self,
        task_description: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze task complexity indicators."""
        complexity = {
            "text_length": len(task_description),
            "has_attachments": bool(context.get("attachments")),
            "multi_step": any(word in task_description.lower()
                             for word in ["then", "after", "next", "also", "additionally"]),
            "technical_terms": sum(1 for word in task_description.lower().split()
                                 if word in ["simulation", "optimization", "analysis", "validation"]),
            "urgency_indicators": any(word in task_description.lower()
                                   for word in ["urgent", "asap", "quickly", "immediately"])
        }

        # Calculate overall complexity score
        score = 0
        if complexity["text_length"] > 100:
            score += 1
        if complexity["has_attachments"]:
            score += 1
        if complexity["multi_step"]:
            score += 2
        if complexity["technical_terms"] > 2:
            score += 2
        if complexity["urgency_indicators"]:
            score += 1

        complexity["overall_score"] = min(score, 5)  # Cap at 5
        complexity["level"] = ["simple", "moderate", "complex", "very_complex", "expert"][min(score, 4)]

        return complexity

    def _determine_simulation_type(
        self,
        task_description: str,
        context: Dict[str, Any]
    ) -> str:
        """Determine the type of simulation needed."""
        desc_lower = task_description.lower()

        if any(word in desc_lower for word in ["energy", "performance", "output", "generation"]):
            return "energy"
        elif any(word in desc_lower for word in ["cost", "roi", "financial", "npv", "payback"]):
            return "financial"
        else:
            return "comprehensive"

    def _map_action_to_tool(self, action: str) -> Optional[str]:
        """Map pattern action to tool name."""
        action_lower = action.lower()

        if "component" in action_lower:
            if "classify" in action_lower:
                return "ComponentClassificationTool"
            elif "dedupe" in action_lower or "duplicate" in action_lower:
                return "ComponentDeduplicationTool"
            elif "recommend" in action_lower:
                return "ComponentRecommendationTool"
            elif "parse" in action_lower:
                return "ParseDatasheetTool"

        elif "simulate" in action_lower:
            if "energy" in action_lower:
                return "SimulateEnergyTool"
            elif "financial" in action_lower:
                return "SimulateFinanceTool"

        elif "validate" in action_lower:
            return "ValidateOdlTool"

        # Default to None - will be handled as a generic step
        return None

    def _summarize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of context for metadata."""
        return {
            "keys_present": list(context.keys()),
            "has_user_id": "user_id" in context,
            "has_project_data": "project" in context or "odl_document" in context,
            "has_attachments": "attachments" in context or "document_url" in context,
            "domain": context.get("domain", "unknown"),
            "complexity_level": context.get("complexity_level", "unknown")
        }
