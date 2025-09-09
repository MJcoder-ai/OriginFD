"""
AI Agent Management System for OriginFD Platform.
Handles agent lifecycle, coordination, and performance monitoring.
"""
import asyncio
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Set, Tuple
from pydantic import BaseModel
import logging

from .base_agent import BaseAgent, AgentContext, AgentResult, AgentStatus
from ..memory.episodic import EpisodicMemory
from ..memory.semantic import SemanticMemory
from ..tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class TaskPriority(str, Enum):
    """Task priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentTask(BaseModel):
    """Task assigned to an agent."""
    task_id: str
    description: str
    priority: TaskPriority
    status: TaskStatus
    assigned_agent: Optional[str] = None
    context: Dict[str, Any]
    created_at: datetime
    assigned_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[AgentResult] = None
    retry_count: int = 0
    max_retries: int = 3


class AgentCapabilityMatch(BaseModel):
    """Agent capability matching result."""
    agent_id: str
    agent_name: str
    match_score: float
    confidence: float
    reasoning: str
    estimated_success_rate: float
    estimated_execution_time_ms: int
    estimated_cost_psu: int


class AgentManager:
    """
    Central management system for all AI agents.
    
    Responsibilities:
    - Agent registration and lifecycle management
    - Task assignment and load balancing
    - Agent coordination and communication
    - Performance monitoring and optimization
    - Resource allocation and cost management
    """
    
    def __init__(
        self,
        tool_registry: ToolRegistry,
        episodic_memory: EpisodicMemory,
        semantic_memory: SemanticMemory
    ):
        self.tool_registry = tool_registry
        self.episodic_memory = episodic_memory
        self.semantic_memory = semantic_memory
        
        # Agent management
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_capabilities: Dict[str, List[str]] = {}
        
        # Task management
        self.pending_tasks: List[AgentTask] = []
        self.active_tasks: Dict[str, AgentTask] = {}
        self.completed_tasks: List[AgentTask] = []
        
        # Performance tracking
        self.agent_performance: Dict[str, Dict[str, Any]] = {}
        self.system_metrics: Dict[str, Any] = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "average_execution_time_ms": 0,
            "total_cost_psu": 0,
            "agent_utilization": {}
        }
        
        # Configuration
        self.max_concurrent_tasks_per_agent = 3
        self.task_timeout_minutes = 30
        self.performance_evaluation_interval = 300  # 5 minutes
        
        # Background tasks
        self._background_tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()
        
        logger.info("AgentManager initialized")
    
    async def initialize(self):
        """Initialize the agent management system."""
        logger.info("Starting AgentManager...")
        
        # Start background tasks
        self._background_tasks = [
            asyncio.create_task(self._task_scheduler()),
            asyncio.create_task(self._performance_monitor()),
            asyncio.create_task(self._cleanup_worker()),
            asyncio.create_task(self._health_checker())
        ]
        
        logger.info("AgentManager started successfully")
    
    async def shutdown(self):
        """Shutdown the agent management system."""
        logger.info("Shutting down AgentManager...")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Wait for background tasks to complete
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        # Cancel any remaining active tasks
        for task in self.active_tasks.values():
            if task.status == TaskStatus.EXECUTING:
                task.status = TaskStatus.CANCELLED
        
        logger.info("AgentManager shutdown complete")
    
    async def register_agent(self, agent: BaseAgent):
        """Register a new agent with the manager."""
        if agent.agent_id in self.agents:
            raise ValueError(f"Agent {agent.agent_id} is already registered")
        
        self.agents[agent.agent_id] = agent
        self.agent_capabilities[agent.agent_id] = agent.specialized_tools
        self.agent_performance[agent.agent_id] = {
            "tasks_completed": 0,
            "success_rate": 0.0,
            "average_execution_time_ms": 0,
            "total_cost_psu": 0,
            "current_load": 0,
            "last_activity": datetime.utcnow()
        }
        
        logger.info(f"Registered agent: {agent.name} ({agent.agent_id})")
    
    async def unregister_agent(self, agent_id: str):
        """Unregister an agent from the manager."""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} is not registered")
        
        # Cancel any active tasks for this agent
        for task in list(self.active_tasks.values()):
            if task.assigned_agent == agent_id:
                task.status = TaskStatus.CANCELLED
                self.active_tasks.pop(task.task_id, None)
        
        # Remove agent
        self.agents.pop(agent_id, None)
        self.agent_capabilities.pop(agent_id, None)
        self.agent_performance.pop(agent_id, None)
        
        logger.info(f"Unregistered agent: {agent_id}")
    
    async def submit_task(
        self,
        description: str,
        context: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        preferred_agent: Optional[str] = None
    ) -> str:
        """Submit a new task for execution."""
        task = AgentTask(
            task_id=str(uuid.uuid4()),
            description=description,
            priority=priority,
            status=TaskStatus.PENDING,
            context=context,
            created_at=datetime.utcnow()
        )
        
        # If preferred agent is specified and available, assign directly
        if preferred_agent and preferred_agent in self.agents:
            agent_load = self._get_agent_current_load(preferred_agent)
            if agent_load < self.max_concurrent_tasks_per_agent:
                task.assigned_agent = preferred_agent
                task.status = TaskStatus.ASSIGNED
                task.assigned_at = datetime.utcnow()
        
        self.pending_tasks.append(task)
        self.system_metrics["total_tasks"] += 1
        
        logger.info(f"Submitted task: {task.task_id} (priority: {priority})")
        return task.task_id
    
    async def get_task_status(self, task_id: str) -> Optional[AgentTask]:
        """Get the current status of a task."""
        # Check active tasks
        if task_id in self.active_tasks:
            return self.active_tasks[task_id]
        
        # Check pending tasks
        for task in self.pending_tasks:
            if task.task_id == task_id:
                return task
        
        # Check completed tasks
        for task in self.completed_tasks:
            if task.task_id == task_id:
                return task
        
        return None
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or active task."""
        # Check pending tasks
        for i, task in enumerate(self.pending_tasks):
            if task.task_id == task_id:
                task.status = TaskStatus.CANCELLED
                self.pending_tasks.pop(i)
                self.completed_tasks.append(task)
                logger.info(f"Cancelled pending task: {task_id}")
                return True
        
        # Check active tasks
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.status = TaskStatus.CANCELLED
            self.active_tasks.pop(task_id)
            self.completed_tasks.append(task)
            logger.info(f"Cancelled active task: {task_id}")
            return True
        
        return False
    
    async def find_best_agent(self, task_description: str, context: Dict[str, Any]) -> Optional[AgentCapabilityMatch]:
        """Find the best agent for a given task."""
        if not self.agents:
            return None
        
        capability_matches: List[AgentCapabilityMatch] = []
        
        for agent_id, agent in self.agents.items():
            # Skip agents that are at capacity
            if self._get_agent_current_load(agent_id) >= self.max_concurrent_tasks_per_agent:
                continue
            
            # Skip agents that are in error state
            if agent.status == AgentStatus.ERROR:
                continue
            
            # Get capability assessment
            assessment = await agent.get_capability_assessment(task_description)
            
            if assessment["can_handle"]:
                match = AgentCapabilityMatch(
                    agent_id=agent_id,
                    agent_name=agent.name,
                    match_score=assessment["overall_confidence"],
                    confidence=assessment["overall_confidence"],
                    reasoning=assessment["reasoning"],
                    estimated_success_rate=assessment["estimated_success_rate"],
                    estimated_execution_time_ms=agent.average_execution_time_ms,
                    estimated_cost_psu=3  # TODO: Estimate based on task complexity
                )
                capability_matches.append(match)
        
        if not capability_matches:
            return None
        
        # Sort by match score and success rate
        capability_matches.sort(
            key=lambda m: (m.match_score * m.estimated_success_rate),
            reverse=True
        )
        
        return capability_matches[0]
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        agent_status = {}
        for agent_id, agent in self.agents.items():
            agent_status[agent_id] = {
                "name": agent.name,
                "status": agent.status,
                "current_load": self._get_agent_current_load(agent_id),
                "performance": self.agent_performance.get(agent_id, {}),
                "capabilities": self.agent_capabilities.get(agent_id, [])
            }
        
        return {
            "agents": agent_status,
            "tasks": {
                "pending": len(self.pending_tasks),
                "active": len(self.active_tasks),
                "completed": len(self.completed_tasks)
            },
            "metrics": self.system_metrics,
            "health": {
                "total_agents": len(self.agents),
                "healthy_agents": len([a for a in self.agents.values() if a.status != AgentStatus.ERROR]),
                "system_load": sum(self._get_agent_current_load(aid) for aid in self.agents.keys()),
                "uptime": datetime.utcnow()  # TODO: Track actual uptime
            }
        }
    
    async def optimize_agent_allocation(self):
        """Optimize agent allocation based on performance and load."""
        # Analyze current performance
        performance_analysis = await self._analyze_agent_performance()
        
        # Redistribute tasks if needed
        underperforming_agents = [
            agent_id for agent_id, perf in performance_analysis.items()
            if perf["success_rate"] < 0.7 and perf["tasks_completed"] > 10
        ]
        
        if underperforming_agents:
            logger.warning(f"Underperforming agents detected: {underperforming_agents}")
            # TODO: Implement task redistribution logic
        
        # Update agent priorities based on performance
        for agent_id, agent in self.agents.items():
            perf = performance_analysis.get(agent_id, {})
            if perf.get("success_rate", 0) > 0.9:
                # Prioritize high-performing agents
                self.agent_performance[agent_id]["priority_boost"] = 1.2
            elif perf.get("success_rate", 0) < 0.5:
                # Deprioritize low-performing agents
                self.agent_performance[agent_id]["priority_boost"] = 0.8
            else:
                self.agent_performance[agent_id]["priority_boost"] = 1.0
    
    # Background Tasks
    
    async def _task_scheduler(self):
        """Background task scheduler."""
        while not self._shutdown_event.is_set():
            try:
                await self._process_pending_tasks()
                await asyncio.sleep(1)  # Check every second
            except Exception as e:
                logger.error(f"Task scheduler error: {str(e)}")
                await asyncio.sleep(5)
    
    async def _performance_monitor(self):
        """Background performance monitoring."""
        while not self._shutdown_event.is_set():
            try:
                await self._update_performance_metrics()
                await self.optimize_agent_allocation()
                await asyncio.sleep(self.performance_evaluation_interval)
            except Exception as e:
                logger.error(f"Performance monitor error: {str(e)}")
                await asyncio.sleep(60)
    
    async def _cleanup_worker(self):
        """Background cleanup of completed tasks and old data."""
        while not self._shutdown_event.is_set():
            try:
                await self._cleanup_old_tasks()
                await self._cleanup_old_performance_data()
                await asyncio.sleep(3600)  # Run hourly
            except Exception as e:
                logger.error(f"Cleanup worker error: {str(e)}")
                await asyncio.sleep(3600)
    
    async def _health_checker(self):
        """Background health monitoring for agents."""
        while not self._shutdown_event.is_set():
            try:
                await self._check_agent_health()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Health checker error: {str(e)}")
                await asyncio.sleep(60)
    
    # Helper Methods
    
    async def _process_pending_tasks(self):
        """Process pending tasks by assigning them to available agents."""
        if not self.pending_tasks:
            return
        
        # Sort pending tasks by priority
        self.pending_tasks.sort(
            key=lambda t: (
                {"critical": 0, "high": 1, "normal": 2, "low": 3}[t.priority],
                t.created_at
            )
        )
        
        tasks_to_process = []
        for task in self.pending_tasks[:]:
            if task.status == TaskStatus.PENDING:
                # Find best agent if not already assigned
                if not task.assigned_agent:
                    best_match = await self.find_best_agent(task.description, task.context)
                    if best_match:
                        task.assigned_agent = best_match.agent_id
                        task.status = TaskStatus.ASSIGNED
                        task.assigned_at = datetime.utcnow()
                
                # If agent is assigned, prepare for execution
                if task.assigned_agent:
                    tasks_to_process.append(task)
                    self.pending_tasks.remove(task)
        
        # Execute assigned tasks
        for task in tasks_to_process:
            await self._execute_task(task)
    
    async def _execute_task(self, task: AgentTask):
        """Execute a task with the assigned agent."""
        if not task.assigned_agent or task.assigned_agent not in self.agents:
            task.status = TaskStatus.FAILED
            self.completed_tasks.append(task)
            return
        
        agent = self.agents[task.assigned_agent]
        
        # Create agent context
        context = AgentContext(
            session_id=task.context.get("session_id", str(uuid.uuid4())),
            user_id=task.context.get("user_id", "system"),
            tenant_id=task.context.get("tenant_id", "system"),
            task_id=task.task_id,
            current_state=task.context,
            shared_scratchpad={},
            conversation_history=[],
            project_context=task.context.get("project_context")
        )
        
        # Start execution
        task.status = TaskStatus.EXECUTING
        task.started_at = datetime.utcnow()
        self.active_tasks[task.task_id] = task
        
        # Update agent performance
        self.agent_performance[task.assigned_agent]["current_load"] += 1
        
        try:
            # Execute task
            result = await agent.process_request(task.description, context)
            
            # Update task with result
            task.result = result
            task.status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            
            # Update metrics
            if result.success:
                self.system_metrics["successful_tasks"] += 1
            else:
                self.system_metrics["failed_tasks"] += 1
            
            self.system_metrics["total_cost_psu"] += result.psu_cost
            
            logger.info(f"Task {task.task_id} completed: {task.status}")
            
        except Exception as e:
            logger.error(f"Task execution failed: {task.task_id} - {str(e)}")
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
        
        finally:
            # Clean up
            self.active_tasks.pop(task.task_id, None)
            self.completed_tasks.append(task)
            self.agent_performance[task.assigned_agent]["current_load"] -= 1
            self.agent_performance[task.assigned_agent]["tasks_completed"] += 1
            self.agent_performance[task.assigned_agent]["last_activity"] = datetime.utcnow()
    
    def _get_agent_current_load(self, agent_id: str) -> int:
        """Get current task load for an agent."""
        return self.agent_performance.get(agent_id, {}).get("current_load", 0)
    
    async def _analyze_agent_performance(self) -> Dict[str, Dict[str, Any]]:
        """Analyze performance metrics for all agents."""
        analysis = {}
        
        for agent_id, perf in self.agent_performance.items():
            if perf["tasks_completed"] > 0:
                # Calculate success rate from recent tasks
                recent_tasks = [
                    t for t in self.completed_tasks[-100:]  # Last 100 tasks
                    if t.assigned_agent == agent_id and t.completed_at
                ]
                
                successful_tasks = len([t for t in recent_tasks if t.status == TaskStatus.COMPLETED])
                success_rate = successful_tasks / len(recent_tasks) if recent_tasks else 0.0
                
                analysis[agent_id] = {
                    "success_rate": success_rate,
                    "tasks_completed": len(recent_tasks),
                    "average_execution_time": perf["average_execution_time_ms"],
                    "total_cost": perf["total_cost_psu"],
                    "current_load": perf["current_load"],
                    "last_activity": perf["last_activity"]
                }
        
        return analysis
    
    async def _update_performance_metrics(self):
        """Update system-wide performance metrics."""
        total_time = 0
        completed_count = 0
        
        for task in self.completed_tasks[-1000:]:  # Last 1000 tasks
            if task.result and task.started_at and task.completed_at:
                execution_time = (task.completed_at - task.started_at).total_seconds() * 1000
                total_time += execution_time
                completed_count += 1
        
        if completed_count > 0:
            self.system_metrics["average_execution_time_ms"] = int(total_time / completed_count)
        
        # Update agent utilization
        for agent_id in self.agents:
            current_load = self._get_agent_current_load(agent_id)
            utilization = current_load / self.max_concurrent_tasks_per_agent
            self.system_metrics["agent_utilization"][agent_id] = utilization
    
    async def _cleanup_old_tasks(self):
        """Clean up old completed tasks."""
        cutoff_time = datetime.utcnow() - timedelta(days=7)  # Keep 7 days
        
        self.completed_tasks = [
            task for task in self.completed_tasks
            if not task.completed_at or task.completed_at > cutoff_time
        ]
        
        logger.info(f"Cleaned up old tasks. Remaining: {len(self.completed_tasks)}")
    
    async def _cleanup_old_performance_data(self):
        """Clean up old performance data."""
        # TODO: Implement performance data cleanup
        pass
    
    async def _check_agent_health(self):
        """Check health status of all agents."""
        for agent_id, agent in self.agents.items():
            perf = self.agent_performance[agent_id]
            
            # Check if agent has been inactive
            if perf["last_activity"]:
                inactive_time = datetime.utcnow() - perf["last_activity"]
                if inactive_time > timedelta(hours=1):
                    logger.warning(f"Agent {agent_id} has been inactive for {inactive_time}")
            
            # Check error states
            if agent.status == AgentStatus.ERROR:
                logger.error(f"Agent {agent_id} is in error state")
                # TODO: Implement agent recovery logic
