"""
Core AI Orchestrator implementing the L1 architecture.
Planner/Router -> Tool Caller -> Critic/Verifier -> Policy Router
"""

import asyncio
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from memory.cag_store import CAGStore
from memory.episodic import EpisodicMemory
from tools.registry import ToolError, ToolRegistry

from .critic import CriticVerifier
from .model_selector import ModelSelector
from .planner import PlanningResult, TaskPlanner
from .policy_router import PolicyRouter, PSUBudgetExceeded
from .region_router import RegionRouter

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Task priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Task:
    """Represents a task to be processed by the orchestrator."""

    def __init__(
        self,
        task_id: str,
        task_type: str,
        description: str,
        context: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        self.id = task_id
        self.type = task_type
        self.description = description
        self.context = context
        self.priority = priority
        self.tenant_id = tenant_id
        self.user_id = user_id

        self.status = TaskStatus.PENDING
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

        self.plan: Optional[PlanningResult] = None
        self.execution_results: List[Dict[str, Any]] = []
        self.errors: List[str] = []
        self.patches: List[Dict[str, Any]] = []


class AIOrchestrator:
    """
    L1 AI Orchestrator following the canonical architecture:
    Planner/Router -> Tool Caller -> Critic/Verifier -> Policy Router
    """

    def __init__(self):
        self.task_planner = TaskPlanner()
        self.policy_router = PolicyRouter()
        self.region_router = RegionRouter()
        self.critic_verifier = CriticVerifier()
        self.tool_registry = ToolRegistry()
        self.model_selector = ModelSelector()
        self.cag_store = CAGStore()
        self.episodic_memory = EpisodicMemory()

        # Task management
        self.active_tasks: Dict[str, Task] = {}
        self.task_queue = asyncio.Queue()
        self.worker_tasks: List[asyncio.Task] = []
        self.max_concurrent_tasks = 5

        self._shutdown_event = asyncio.Event()

    async def initialize(self):
        """Initialize the orchestrator and start background workers."""
        logger.info("Initializing AI Orchestrator...")

        # Initialize components
        await self.tool_registry.initialize()
        await self.cag_store.initialize()
        await self.episodic_memory.initialize()

        # Start worker tasks
        for i in range(self.max_concurrent_tasks):
            worker = asyncio.create_task(self._task_worker(f"worker-{i}"))
            self.worker_tasks.append(worker)

        logger.info("AI Orchestrator initialized successfully")

    async def cleanup(self):
        """Cleanup resources and stop workers."""
        logger.info("Shutting down AI Orchestrator...")

        # Signal shutdown
        self._shutdown_event.set()

        # Cancel all worker tasks
        for worker in self.worker_tasks:
            worker.cancel()

        # Wait for workers to finish
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)

        # Cleanup components
        await self.cag_store.cleanup()
        await self.episodic_memory.cleanup()

        logger.info("AI Orchestrator shutdown complete")

    async def submit_task(
        self,
        task_type: str,
        description: str,
        context: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Submit a new task for processing.

        Returns the task ID for tracking.
        """
        task_id = str(uuid.uuid4())

        task = Task(
            task_id=task_id,
            task_type=task_type,
            description=description,
            context=context,
            priority=priority,
            tenant_id=tenant_id,
            user_id=user_id,
        )

        self.active_tasks[task_id] = task
        await self.task_queue.put(task)

        logger.info(f"Submitted task {task_id}: {description}")
        return task_id

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a task."""
        task = self.active_tasks.get(task_id)
        if not task:
            return None

        return {
            "id": task.id,
            "type": task.type,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "created_at": task.created_at,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
            "errors": task.errors,
            "patches_generated": len(task.patches),
        }

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or running task."""
        task = self.active_tasks.get(task_id)
        if not task:
            return False

        if task.status in [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        ]:
            return False

        task.status = TaskStatus.CANCELLED
        logger.info(f"Cancelled task {task_id}")
        return True

    async def _task_worker(self, worker_name: str):
        """Worker coroutine that processes tasks from the queue."""
        logger.info(f"Started task worker: {worker_name}")

        while not self._shutdown_event.is_set():
            try:
                # Get task with timeout
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)

                if task.status == TaskStatus.CANCELLED:
                    continue

                logger.info(f"Worker {worker_name} processing task {task.id}")
                await self._process_task(task)

            except asyncio.TimeoutError:
                # Normal timeout, continue loop
                continue
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}", exc_info=True)

    async def _process_task(self, task: Task):
        """Process a single task through the full pipeline."""
        try:
            task.status = TaskStatus.PLANNING
            task.started_at = datetime.utcnow()

            # Step 1: Policy Router - Check PSU budget and permissions
            await self._check_policy_constraints(task)

            # Step 2: Region Router - Select appropriate models and storage
            region_config = await self.region_router.get_region_config(
                task.tenant_id, task.context
            )

            # Step 3: Planner - Create execution plan with grounding
            task.status = TaskStatus.PLANNING
            model_info = self.model_selector.select_model(
                task.type, region_config.get("region") if region_config else None
            )
            fallback_models = self.model_selector.get_fallback_models(
                task.type, region_config.get("region") if region_config else None
            )
            plan = await self.task_planner.create_plan(
                task.type,
                task.description,
                task.context,
                region_config,
                model_info=model_info,
                fallback_models=fallback_models,
            )
            task.plan = plan

            # Step 4: Tool Execution
            task.status = TaskStatus.EXECUTING
            execution_results = await self._execute_plan(task, plan)
            task.execution_results = execution_results

            # Step 5: Critic/Verifier - Review results
            task.status = TaskStatus.REVIEWING
            verification_result = await self.critic_verifier.verify_results(
                plan, execution_results, task.context
            )

            if not verification_result.is_valid:
                task.status = TaskStatus.FAILED
                task.errors.extend(verification_result.errors)
                logger.error(
                    f"Task {task.id} failed verification: {verification_result.errors}"
                )
                return

            # Step 6: Generate JSON-Patches if needed
            patches = await self._generate_patches(task, execution_results)
            task.patches = patches

            # Complete task
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()

            # Publish usage metrics via policy router
            await self.policy_router.consume_psu_budget(
                tenant_id=task.tenant_id or "",
                actual_psu_cost=task.context.get("estimated_psu_cost", 1),
                task_id=task.id,
            )

            # Store in episodic memory for learning
            await self.episodic_memory.store_episode(
                task_id=task.id,
                task_type=task.type,
                plan=plan,
                results=execution_results,
                patches=patches,
                success=True,
            )

            logger.info(f"Task {task.id} completed successfully")

        except PSUBudgetExceeded as e:
            task.status = TaskStatus.FAILED
            task.errors.append(f"PSU budget exceeded: {str(e)}")
            logger.warning(f"Task {task.id} failed: PSU budget exceeded")

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.errors.append(str(e))
            logger.error(f"Task {task.id} failed: {e}", exc_info=True)

            # Store failed episode for learning
            await self.episodic_memory.store_episode(
                task_id=task.id,
                task_type=task.type,
                plan=task.plan,
                results=task.execution_results,
                patches=[],
                success=False,
                error=str(e),
            )

        finally:
            task.completed_at = datetime.utcnow()

    async def _check_policy_constraints(self, task: Task):
        """Check policy constraints before processing."""
        await self.policy_router.enforce_constraints(
            tenant_id=task.tenant_id,
            user_id=task.user_id,
            task_type=task.type,
            estimated_psu_cost=task.context.get("estimated_psu_cost", 1),
        )

    async def _execute_plan(
        self, task: Task, plan: PlanningResult
    ) -> List[Dict[str, Any]]:
        """Execute the plan steps using the tool registry."""
        results = []

        for step in plan.steps:
            try:
                logger.info(f"Executing step {step.step_number}: {step.tool_name}")

                # Load and execute tool
                tool = await self.tool_registry.get_tool(step.tool_name)
                result = await tool.execute(step.inputs)

                step_result = {
                    "step_number": step.step_number,
                    "tool_name": step.tool_name,
                    "inputs": step.inputs,
                    "outputs": result,
                    "execution_time_ms": result.get("execution_time_ms", 0),
                    "success": True,
                }
                results.append(step_result)

            except ToolError as e:
                step_result = {
                    "step_number": step.step_number,
                    "tool_name": step.tool_name,
                    "inputs": step.inputs,
                    "error": str(e),
                    "success": False,
                }
                results.append(step_result)

                # Fail fast on tool errors
                raise Exception(f"Tool execution failed: {str(e)}")

        return results

    async def _generate_patches(
        self, task: Task, execution_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate JSON-Patches from execution results."""
        patches = []

        # Extract patch operations from tool outputs
        for result in execution_results:
            if not result.get("success", False):
                continue

            outputs = result.get("outputs", {})
            if "patch_operations" in outputs:
                patch = {
                    "task_id": task.id,
                    "step_number": result["step_number"],
                    "tool_name": result["tool_name"],
                    "operations": outputs["patch_operations"],
                    "evidence": outputs.get("evidence", []),
                    "intent": outputs.get("intent", "Tool-generated change"),
                }
                patches.append(patch)

        return patches
