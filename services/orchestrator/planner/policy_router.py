"""
Policy Router for OriginFD AI Orchestrator.
Manages PSU budgets, permissions, and execution policies.
"""
import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4
from pydantic import BaseModel
from enum import Enum

logger = logging.getLogger(__name__)


class PolicyViolationType(str, Enum):
    """Types of policy violations."""
    BUDGET_EXCEEDED = "budget_exceeded"
    PERMISSION_DENIED = "permission_denied"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    RESOURCE_LIMIT_EXCEEDED = "resource_limit_exceeded"
    TIME_LIMIT_EXCEEDED = "time_limit_exceeded"
    CONTENT_POLICY_VIOLATION = "content_policy_violation"


class PolicyDecision(str, Enum):
    """Policy routing decisions."""
    APPROVE = "approve"
    DENY = "deny"
    MODIFY = "modify"
    DEFER = "defer"
    ESCALATE = "escalate"


class PSUBudgetExceeded(Exception):
    """Exception raised when PSU budget is exceeded."""
    def __init__(self, requested: int, available: int, tenant_id: str):
        self.requested = requested
        self.available = available
        self.tenant_id = tenant_id
        super().__init__(f"PSU budget exceeded: requested {requested}, available {available}")


class PolicyViolation(BaseModel):
    """Policy violation record."""
    violation_id: str
    violation_type: PolicyViolationType
    description: str
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    task_id: Optional[str] = None
    severity: str = "medium"  # low, medium, high, critical
    timestamp: datetime
    metadata: Dict[str, Any] = {}


class BudgetAllocation(BaseModel):
    """PSU budget allocation."""
    tenant_id: str
    total_budget: int
    used_budget: int
    reserved_budget: int
    period_start: datetime
    period_end: datetime
    rollover_allowed: bool = True
    overage_limit: int = 0  # Additional PSU allowed beyond budget


class RateLimit(BaseModel):
    """Rate limiting configuration."""
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    resource_type: str  # "api_calls", "tool_executions", "agent_tasks"
    limit_count: int
    time_window_seconds: int
    current_count: int = 0
    window_start: datetime


class PolicyRouter:
    """
    Policy Router for managing execution policies, budgets, and permissions.
    
    Features:
    - PSU budget management per tenant/user
    - Rate limiting and resource quotas
    - Permission-based access control
    - Content policy enforcement
    - Dynamic policy adjustment
    - Violation tracking and reporting
    """
    
    def __init__(self):
        # Budget management
        self.budget_allocations: Dict[str, BudgetAllocation] = {}
        self.rate_limits: Dict[str, RateLimit] = {}
        
        # Policy violations
        self.violations: List[PolicyViolation] = []
        self.violation_thresholds = {
            PolicyViolationType.BUDGET_EXCEEDED: 3,  # Max violations per hour
            PolicyViolationType.RATE_LIMIT_EXCEEDED: 10,
            PolicyViolationType.PERMISSION_DENIED: 5
        }

        # Default policies
        self.default_policies = {
            "max_task_duration_minutes": 30,
            "max_concurrent_tasks_per_user": 5,
            "max_concurrent_tasks_per_tenant": 20,
            "max_tool_executions_per_task": 20,
            "max_psu_per_task": 100,
            "require_approval_above_psu": 50,
            "content_filtering_enabled": True
        }
        
        # Permission mappings
        self.role_permissions = {
            "admin": ["*"],
            "project_manager": [
                "design_read", "design_write", "simulation_run",
                "procurement_read", "procurement_write",
                "finance_read"
            ],
            "engineer": [
                "design_read", "design_write", "simulation_run",
                "component_read", "component_write"
            ],
            "viewer": [
                "design_read", "component_read", "finance_read"
            ]
        }

        logger.info("PolicyRouter initialized")

        # Track active tasks for concurrency limits
        self.active_tasks_by_user: Dict[str, int] = {}
        self.active_tasks_by_tenant: Dict[str, int] = {}

    def register_task_start(self, tenant_id: Optional[str], user_id: Optional[str]):
        """Register the start of a task for concurrency tracking."""
        if tenant_id:
            self.active_tasks_by_tenant[tenant_id] = self.active_tasks_by_tenant.get(tenant_id, 0) + 1
        if user_id:
            key = f"{tenant_id or 'global'}:{user_id}"
            self.active_tasks_by_user[key] = self.active_tasks_by_user.get(key, 0) + 1

    def register_task_completion(self, tenant_id: Optional[str], user_id: Optional[str]):
        """Register the completion of a task for concurrency tracking."""
        if tenant_id and tenant_id in self.active_tasks_by_tenant:
            self.active_tasks_by_tenant[tenant_id] = max(0, self.active_tasks_by_tenant[tenant_id] - 1)
            if self.active_tasks_by_tenant[tenant_id] == 0:
                del self.active_tasks_by_tenant[tenant_id]
        if user_id:
            key = f"{tenant_id or 'global'}:{user_id}"
            if key in self.active_tasks_by_user:
                self.active_tasks_by_user[key] = max(0, self.active_tasks_by_user[key] - 1)
                if self.active_tasks_by_user[key] == 0:
                    del self.active_tasks_by_user[key]
    
    async def check_policy_compliance(
        self,
        task_id: str,
        tenant_id: Optional[str],
        user_id: Optional[str],
        estimated_psu_cost: int,
        estimated_duration_ms: int,
        required_permissions: List[str],
        context: Dict[str, Any]
    ) -> Tuple[PolicyDecision, Optional[str], Dict[str, Any]]:
        """
        Check if a task complies with all applicable policies.
        
        Returns:
            (decision, reason, modifications)
        """
        try:
            violations = []
            modifications = {}
            
            # Check PSU budget
            budget_check = await self._check_psu_budget(
                tenant_id, user_id, estimated_psu_cost
            )
            if not budget_check["approved"]:
                violations.append(PolicyViolation(
                    violation_id=str(uuid4()),
                    violation_type=PolicyViolationType.BUDGET_EXCEEDED,
                    description=budget_check["reason"],
                    tenant_id=tenant_id,
                    user_id=user_id,
                    task_id=task_id,
                    severity="high",
                    timestamp=datetime.utcnow(),
                    metadata={"requested_psu": estimated_psu_cost, "available_psu": budget_check.get("available", 0)}
                ))
            
            # Check permissions
            permission_check = await self._check_permissions(
                user_id, required_permissions, context
            )
            if not permission_check["approved"]:
                violations.append(PolicyViolation(
                    violation_id=str(uuid4()),
                    violation_type=PolicyViolationType.PERMISSION_DENIED,
                    description=permission_check["reason"],
                    tenant_id=tenant_id,
                    user_id=user_id,
                    task_id=task_id,
                    severity="medium",
                    timestamp=datetime.utcnow(),
                    metadata={"required_permissions": required_permissions}
                ))
            
            # Check rate limits
            rate_check = await self._check_rate_limits(
                tenant_id, user_id, "task_execution"
            )
            if not rate_check["approved"]:
                violations.append(PolicyViolation(
                    violation_id=str(uuid4()),
                    violation_type=PolicyViolationType.RATE_LIMIT_EXCEEDED,
                    description=rate_check["reason"],
                    tenant_id=tenant_id,
                    user_id=user_id,
                    task_id=task_id,
                    severity="medium",
                    timestamp=datetime.utcnow()
                ))
            
            # Check resource limits
            resource_check = await self._check_resource_limits(
                estimated_duration_ms, context
            )
            if not resource_check["approved"]:
                violations.append(PolicyViolation(
                    violation_id=str(uuid4()),
                    violation_type=PolicyViolationType.RESOURCE_LIMIT_EXCEEDED,
                    description=resource_check["reason"],
                    tenant_id=tenant_id,
                    user_id=user_id,
                    task_id=task_id,
                    severity="medium",
                    timestamp=datetime.utcnow()
                ))
            
            # Check content policy
            content_check = await self._check_content_policy(context)
            if not content_check["approved"]:
                violations.append(PolicyViolation(
                    violation_id=str(uuid4()),
                    violation_type=PolicyViolationType.CONTENT_POLICY_VIOLATION,
                    description=content_check["reason"],
                    tenant_id=tenant_id,
                    user_id=user_id,
                    task_id=task_id,
                    severity="high",
                    timestamp=datetime.utcnow()
                ))
            
            # Record violations
            self.violations.extend(violations)
            
            # Make policy decision
            if not violations:
                # All checks passed
                await self._reserve_psu_budget(tenant_id, user_id, estimated_psu_cost)
                await self._update_rate_limits(tenant_id, user_id, "task_execution")
                return PolicyDecision.APPROVE, None, {}
            
            # Check if we can modify the task to make it compliant
            critical_violations = [v for v in violations if v.severity == "critical"]
            high_violations = [v for v in violations if v.severity == "high"]
            
            if critical_violations:
                # Cannot proceed with critical violations
                reason = f"Critical policy violations: {', '.join(v.description for v in critical_violations)}"
                return PolicyDecision.DENY, reason, {}
            
            elif high_violations:
                # High violations require escalation
                reason = f"High severity violations require approval: {', '.join(v.description for v in high_violations)}"
                return PolicyDecision.ESCALATE, reason, {"violations": [v.dict() for v in violations]}
            
            else:
                # Try to modify task to address medium/low violations
                modifications = await self._generate_modifications(violations, context)
                if modifications:
                    reason = f"Task modified to address policy violations: {', '.join(v.description for v in violations)}"
                    return PolicyDecision.MODIFY, reason, modifications
                else:
                    reason = f"Cannot resolve policy violations: {', '.join(v.description for v in violations)}"
                    return PolicyDecision.DENY, reason, {}
        
        except Exception as e:
            logger.error(f"Policy check failed: {str(e)}")
            return PolicyDecision.DENY, f"Policy check error: {str(e)}", {}
    
    async def allocate_psu_budget(
        self,
        tenant_id: str,
        total_budget: int,
        period_days: int = 30,
        rollover_allowed: bool = True,
        overage_limit: int = 0
    ):
        """Allocate PSU budget for a tenant."""
        period_start = datetime.utcnow()
        period_end = period_start + timedelta(days=period_days)
        
        allocation = BudgetAllocation(
            tenant_id=tenant_id,
            total_budget=total_budget,
            used_budget=0,
            reserved_budget=0,
            period_start=period_start,
            period_end=period_end,
            rollover_allowed=rollover_allowed,
            overage_limit=overage_limit
        )
        
        self.budget_allocations[tenant_id] = allocation
        
        logger.info(f"Allocated {total_budget} PSU budget for tenant {tenant_id}")
    
    async def set_rate_limit(
        self,
        resource_type: str,
        limit_count: int,
        time_window_seconds: int,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """Set rate limit for a resource."""
        key = f"{tenant_id or 'global'}:{user_id or 'all'}:{resource_type}"
        
        rate_limit = RateLimit(
            tenant_id=tenant_id,
            user_id=user_id,
            resource_type=resource_type,
            limit_count=limit_count,
            time_window_seconds=time_window_seconds,
            current_count=0,
            window_start=datetime.utcnow()
        )
        
        self.rate_limits[key] = rate_limit
        
        logger.info(f"Set rate limit: {resource_type} = {limit_count}/{time_window_seconds}s for {key}")
    
    async def consume_psu_budget(
        self,
        tenant_id: str,
        actual_psu_cost: int,
        task_id: str
    ):
        """Consume PSU budget after task completion."""
        if tenant_id in self.budget_allocations:
            allocation = self.budget_allocations[tenant_id]
            
            # Move from reserved to used
            allocation.reserved_budget = max(0, allocation.reserved_budget - actual_psu_cost)
            allocation.used_budget += actual_psu_cost
            
            logger.debug(f"Consumed {actual_psu_cost} PSU for tenant {tenant_id} (task: {task_id})")
        else:
            logger.warning(f"No budget allocation found for tenant {tenant_id}")
    
    async def release_psu_reservation(
        self,
        tenant_id: str,
        reserved_psu: int,
        task_id: str
    ):
        """Release PSU reservation if task is cancelled."""
        if tenant_id in self.budget_allocations:
            allocation = self.budget_allocations[tenant_id]
            allocation.reserved_budget = max(0, allocation.reserved_budget - reserved_psu)
            
            logger.debug(f"Released {reserved_psu} PSU reservation for tenant {tenant_id} (task: {task_id})")
    
    async def get_budget_status(self, tenant_id: str) -> Dict[str, Any]:
        """Get current budget status for a tenant."""
        if tenant_id not in self.budget_allocations:
            return {"error": "No budget allocation found"}
        
        allocation = self.budget_allocations[tenant_id]
        available = allocation.total_budget - allocation.used_budget - allocation.reserved_budget
        
        return {
            "tenant_id": tenant_id,
            "total_budget": allocation.total_budget,
            "used_budget": allocation.used_budget,
            "reserved_budget": allocation.reserved_budget,
            "available_budget": available,
            "period_start": allocation.period_start.isoformat(),
            "period_end": allocation.period_end.isoformat(),
            "utilization_percent": (allocation.used_budget / allocation.total_budget) * 100,
            "overage_limit": allocation.overage_limit
        }
    
    async def get_violations(
        self,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        hours_back: int = 24
    ) -> List[PolicyViolation]:
        """Get policy violations within specified timeframe."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        
        filtered_violations = [
            v for v in self.violations
            if v.timestamp >= cutoff_time
            and (not tenant_id or v.tenant_id == tenant_id)
            and (not user_id or v.user_id == user_id)
        ]
        
        return filtered_violations
    
    # Private methods
    
    async def _check_psu_budget(
        self,
        tenant_id: Optional[str],
        user_id: Optional[str],
        requested_psu: int
    ) -> Dict[str, Any]:
        """Check if PSU budget allows the request."""
        if not tenant_id:
            # No tenant-specific budget, allow for now
            return {"approved": True}
        
        if tenant_id not in self.budget_allocations:
            # No budget allocation, deny
            return {
                "approved": False,
                "reason": f"No PSU budget allocation for tenant {tenant_id}",
                "available": 0
            }
        
        allocation = self.budget_allocations[tenant_id]
        
        # Check if budget period has expired
        if datetime.utcnow() > allocation.period_end:
            # Reset budget for new period
            allocation.used_budget = 0
            allocation.reserved_budget = 0
            allocation.period_start = datetime.utcnow()
            allocation.period_end = allocation.period_start + timedelta(days=30)
        
        available = (
            allocation.total_budget + allocation.overage_limit 
            - allocation.used_budget - allocation.reserved_budget
        )
        
        if requested_psu <= available:
            return {"approved": True, "available": available}
        else:
            return {
                "approved": False,
                "reason": f"Insufficient PSU budget: requested {requested_psu}, available {available}",
                "available": available
            }
    
    async def _check_permissions(
        self,
        user_id: Optional[str],
        required_permissions: List[str],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check if user has required permissions."""
        if not required_permissions:
            return {"approved": True}
        
        # Get user role from context
        user_role = context.get("user_role", "viewer")
        user_permissions = self.role_permissions.get(user_role, [])
        
        # Admin has all permissions
        if "*" in user_permissions:
            return {"approved": True}
        
        # Check specific permissions
        missing_permissions = [
            perm for perm in required_permissions 
            if perm not in user_permissions
        ]
        
        if missing_permissions:
            return {
                "approved": False,
                "reason": f"Missing permissions: {', '.join(missing_permissions)}"
            }
        else:
            return {"approved": True}
    
    async def _check_rate_limits(
        self,
        tenant_id: Optional[str],
        user_id: Optional[str],
        resource_type: str
    ) -> Dict[str, Any]:
        """Check rate limits for resource usage."""
        # Check user-specific rate limit first
        if user_id:
            user_key = f"{tenant_id or 'global'}:{user_id}:{resource_type}"
            if user_key in self.rate_limits:
                limit_check = await self._check_single_rate_limit(user_key)
                if not limit_check["approved"]:
                    return limit_check
        
        # Check tenant-wide rate limit
        if tenant_id:
            tenant_key = f"{tenant_id}:all:{resource_type}"
            if tenant_key in self.rate_limits:
                limit_check = await self._check_single_rate_limit(tenant_key)
                if not limit_check["approved"]:
                    return limit_check
        
        # Check global rate limit
        global_key = f"global:all:{resource_type}"
        if global_key in self.rate_limits:
            return await self._check_single_rate_limit(global_key)
        
        return {"approved": True}
    
    async def _check_single_rate_limit(self, key: str) -> Dict[str, Any]:
        """Check a single rate limit."""
        rate_limit = self.rate_limits[key]
        current_time = datetime.utcnow()
        
        # Check if window has expired
        window_elapsed = (current_time - rate_limit.window_start).total_seconds()
        if window_elapsed >= rate_limit.time_window_seconds:
            # Reset window
            rate_limit.current_count = 0
            rate_limit.window_start = current_time
        
        if rate_limit.current_count >= rate_limit.limit_count:
            return {
                "approved": False,
                "reason": f"Rate limit exceeded for {rate_limit.resource_type}: {rate_limit.current_count}/{rate_limit.limit_count}"
            }
        else:
            return {"approved": True}
    
    async def _check_resource_limits(
        self,
        estimated_duration_ms: int,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check resource usage limits."""
        max_duration_ms = self.default_policies["max_task_duration_minutes"] * 60 * 1000
        
        if estimated_duration_ms > max_duration_ms:
            return {
                "approved": False,
                "reason": f"Task duration exceeds limit: {estimated_duration_ms/1000:.1f}s > {max_duration_ms/1000:.1f}s"
            }

        # Check concurrent task limits
        tenant_id = context.get("tenant_id")
        user_id = context.get("user_id")

        if user_id:
            user_key = f"{tenant_id or 'global'}:{user_id}"
            user_active = self.active_tasks_by_user.get(user_key, 0)
            if user_active >= self.default_policies["max_concurrent_tasks_per_user"]:
                return {
                    "approved": False,
                    "reason": f"User has too many concurrent tasks: {user_active}"
                }

        if tenant_id:
            tenant_active = self.active_tasks_by_tenant.get(tenant_id, 0)
            if tenant_active >= self.default_policies["max_concurrent_tasks_per_tenant"]:
                return {
                    "approved": False,
                    "reason": f"Tenant has too many concurrent tasks: {tenant_active}"
                }

        return {"approved": True}
    
    async def _check_content_policy(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check content policy compliance."""
        if not self.default_policies["content_filtering_enabled"]:
            return {"approved": True}

        def _collect_strings(obj: Any) -> List[str]:
            strings: List[str] = []
            if isinstance(obj, dict):
                for v in obj.values():
                    strings.extend(_collect_strings(v))
            elif isinstance(obj, list):
                for item in obj:
                    strings.extend(_collect_strings(item))
            elif isinstance(obj, str):
                strings.append(obj)
            else:
                strings.append(str(obj))
            return strings

        text = " ".join(_collect_strings(context)).lower()

        banned_terms = {"malware", "hack", "exploit"}
        for term in banned_terms:
            if term in text:
                return {"approved": False, "reason": f"Content contains banned term: {term}"}

        email_pattern = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
        phone_pattern = re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b")
        if email_pattern.search(text) or phone_pattern.search(text):
            return {"approved": False, "reason": "Content appears to contain PII"}

        return {"approved": True}
    
    async def _reserve_psu_budget(
        self,
        tenant_id: Optional[str],
        user_id: Optional[str],
        psu_amount: int
    ):
        """Reserve PSU budget for a task."""
        if tenant_id and tenant_id in self.budget_allocations:
            allocation = self.budget_allocations[tenant_id]
            allocation.reserved_budget += psu_amount
    
    async def _update_rate_limits(
        self,
        tenant_id: Optional[str],
        user_id: Optional[str],
        resource_type: str
    ):
        """Update rate limit counters."""
        # Update user-specific rate limit
        if user_id:
            user_key = f"{tenant_id or 'global'}:{user_id}:{resource_type}"
            if user_key in self.rate_limits:
                self.rate_limits[user_key].current_count += 1
        
        # Update tenant-wide rate limit
        if tenant_id:
            tenant_key = f"{tenant_id}:all:{resource_type}"
            if tenant_key in self.rate_limits:
                self.rate_limits[tenant_key].current_count += 1
        
        # Update global rate limit
        global_key = f"global:all:{resource_type}"
        if global_key in self.rate_limits:
            self.rate_limits[global_key].current_count += 1
    
    async def _generate_modifications(
        self,
        violations: List[PolicyViolation],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate task modifications to address policy violations."""
        modifications = {}
        
        for violation in violations:
            if violation.violation_type == PolicyViolationType.BUDGET_EXCEEDED:
                # Suggest reducing PSU cost
                requested_psu = violation.metadata.get("requested_psu", 0)
                available_psu = violation.metadata.get("available_psu", 0)
                if available_psu > 0:
                    modifications["max_psu_cost"] = available_psu
                    modifications["reduce_tool_usage"] = True
            
            elif violation.violation_type == PolicyViolationType.RESOURCE_LIMIT_EXCEEDED:
                # Suggest reducing task scope
                modifications["max_duration_ms"] = self.default_policies["max_task_duration_minutes"] * 60 * 1000
                modifications["simplify_task"] = True
            
            elif violation.violation_type == PolicyViolationType.RATE_LIMIT_EXCEEDED:
                # Suggest deferring task
                modifications["defer_seconds"] = 300  # 5 minutes
        
        return modifications

