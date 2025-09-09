"""
SalesAdvisorAgent - Specialized AI agent for sales, ROI analysis, and proposal generation.
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4

from .base_agent import BaseAgent, AgentContext, AgentResult, AgentPlan, AgentCapability
from ..memory.episodic import EpisodicMemory
from ..memory.semantic import SemanticMemory
from ..tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class SalesAdvisorAgent(BaseAgent):
    """
    Specialized AI agent for sales and financial advisory tasks.
    
    Capabilities:
    - ROI calculations and financial modeling
    - Proposal generation and customization
    - Incentive optimization and discovery
    - Competitive analysis
    - Quote generation and pricing
    - Customer needs analysis
    """
    
    def __init__(
        self,
        tool_registry: ToolRegistry,
        episodic_memory: EpisodicMemory,
        semantic_memory: SemanticMemory
    ):
        # Define agent capabilities
        capabilities = [
            AgentCapability(
                name="financial_analysis",
                description="Calculate ROI, NPV, payback periods and financial metrics",
                tools=["SimulateFinanceTool", "CalculateROITool", "AnalyzeIncentivesTool"],
                rbac_scope=["finance_read", "sales_read"],
                confidence_level=0.92
            ),
            AgentCapability(
                name="proposal_generation",
                description="Generate customized sales proposals and quotes",
                tools=["GenerateProposalTool", "CreateQuoteTool", "CustomizeOfferTool"],
                rbac_scope=["sales_write", "proposal_create"],
                confidence_level=0.88
            ),
            AgentCapability(
                name="incentive_optimization",
                description="Find and optimize available incentives and rebates",
                tools=["FindIncentivesTool", "OptimizeIncentivesTool", "CalculateRebatesTool"],
                rbac_scope=["incentive_read", "finance_read"],
                confidence_level=0.85
            ),
            AgentCapability(
                name="competitive_analysis",
                description="Analyze competitive landscape and positioning",
                tools=["AnalyzeCompetitionTool", "BenchmarkPricingTool"],
                rbac_scope=["market_read", "competitive_read"],
                confidence_level=0.8
            ),
            AgentCapability(
                name="customer_analysis",
                description="Analyze customer needs and preferences",
                tools=["AnalyzeCustomerTool", "SegmentCustomerTool", "PersonalizeTool"],
                rbac_scope=["customer_read", "sales_read"],
                confidence_level=0.83
            )
        ]
        
        super().__init__(
            agent_id="sales_advisor_agent",
            name="Sales Advisor Agent",
            description="Specialized AI agent for sales advisory, financial analysis, and proposal generation",
            capabilities=capabilities,
            tool_registry=tool_registry,
            episodic_memory=episodic_memory,
            semantic_memory=semantic_memory
        )
        
        # Agent-specific configuration
        self.default_discount_rate = 0.06  # 6% discount rate for NPV calculations
        self.min_roi_threshold = 0.15  # 15% minimum ROI recommendation
        self.proposal_templates = ["residential", "commercial", "industrial", "utility"]
        self.incentive_databases = ["DSIRE", "federal", "state", "utility"]
        
        logger.info("SalesAdvisorAgent initialized")
    
    @property
    def specialized_tools(self) -> List[str]:
        """List of tools this agent specializes in using."""
        return [
            "SimulateFinanceTool",
            "CalculateROITool",
            "GenerateProposalTool",
            "CreateQuoteTool",
            "FindIncentivesTool",
            "OptimizeIncentivesTool",
            "AnalyzeCompetitionTool",
            "AnalyzeCustomerTool"
        ]
    
    @property
    def primary_domain(self) -> str:
        """Primary domain this agent operates in."""
        return "sales_advisory"
    
    async def create_plan(self, task: str, context: AgentContext) -> AgentPlan:
        """Create an execution plan for sales advisory tasks."""
        plan_id = str(uuid4())
        steps = []
        
        task_lower = task.lower()
        
        # Determine task type and create appropriate plan
        if "roi" in task_lower or "financial" in task_lower or "payback" in task_lower:
            steps = await self._plan_financial_analysis(task, context)
        elif "proposal" in task_lower or "quote" in task_lower:
            steps = await self._plan_proposal_generation(task, context)
        elif "incentive" in task_lower or "rebate" in task_lower:
            steps = await self._plan_incentive_optimization(task, context)
        elif "competitive" in task_lower or "competition" in task_lower:
            steps = await self._plan_competitive_analysis(task, context)
        elif "customer" in task_lower and ("analyz" in task_lower or "segment" in task_lower):
            steps = await self._plan_customer_analysis(task, context)
        else:
            # General sales advisory task
            steps = await self._plan_general_sales_task(task, context)
        
        # Calculate plan estimates
        total_duration = sum(step["estimated_duration_ms"] for step in steps)
        total_cost = sum(step["estimated_cost_psu"] for step in steps)
        
        # Calculate confidence based on available data and task complexity
        confidence = await self._calculate_plan_confidence(task, context, steps)
        
        plan = AgentPlan(
            plan_id=plan_id,
            steps=steps,
            estimated_duration_ms=total_duration,
            estimated_cost_psu=total_cost,
            tools_required=[step["tool_name"] for step in steps if step.get("tool_name")],
            dependencies=[],
            confidence=confidence,
            reasoning=await self._generate_plan_reasoning(task, steps)
        )
        
        return plan
    
    async def execute_plan(self, plan: AgentPlan, context: AgentContext) -> AgentResult:
        """Execute the sales advisory plan."""
        start_time = datetime.utcnow()
        execution_results = []
        tools_used = []
        
        try:
            logger.info(f"Executing sales advisory plan: {plan.plan_id}")
            
            # Execute steps in order
            for i, step in enumerate(plan.steps):
                step_start = datetime.utcnow()
                
                logger.debug(f"Executing step {i+1}/{len(plan.steps)}: {step['description']}")
                
                if step.get("tool_name"):
                    # Execute tool
                    tool_result = await self.execute_tool(
                        tool_name=step["tool_name"],
                        inputs=step.get("inputs", {}),
                        context=context
                    )
                    
                    execution_results.append(tool_result)
                    tools_used.append(step["tool_name"])
                    
                    # Check if step failed and handle gracefully
                    if not tool_result.success:
                        logger.warning(f"Step failed: {step['description']} - {tool_result.errors}")
                        
                        # For financial calculations, try alternative approach
                        if "financial" in step["tool_name"].lower() or "roi" in step["tool_name"].lower():
                            fallback_result = await self._execute_financial_fallback(step, context)
                            execution_results.append(fallback_result)
                else:
                    # Non-tool step (analysis, synthesis, etc.)
                    step_result = await self._execute_sales_analysis_step(step, context, execution_results)
                    execution_results.append(step_result)
                
                step_duration = (datetime.utcnow() - step_start).total_seconds() * 1000
                logger.debug(f"Step completed in {step_duration:.0f}ms")
            
            # Synthesize final results
            final_result = await self._synthesize_sales_results(
                task_description=context.current_state.get("task_description", ""),
                execution_results=execution_results,
                context=context
            )
            
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Calculate quality score
            quality_score = await self._calculate_sales_quality_score(execution_results, final_result)
            
            result = AgentResult(
                success=True,
                result=final_result,
                plan_executed=plan,
                tools_used=tools_used,
                execution_time_ms=execution_time,
                psu_cost=sum(step["estimated_cost_psu"] for step in plan.steps),
                quality_score=quality_score,
                confidence=min([r.get("confidence", 1.0) for r in execution_results] + [1.0]),
                next_actions=await self._suggest_sales_next_actions(final_result, context)
            )
            
            logger.info(f"Sales advisory plan executed successfully in {execution_time}ms")
            return result
            
        except Exception as e:
            logger.error(f"Sales advisory plan execution failed: {str(e)}")
            
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return AgentResult(
                success=False,
                error=str(e),
                plan_executed=plan,
                tools_used=tools_used,
                execution_time_ms=execution_time,
                psu_cost=0,
                quality_score=0.0,
                confidence=0.0
            )
    
    # Private planning methods
    
    async def _plan_financial_analysis(self, task: str, context: AgentContext) -> List[Dict[str, Any]]:
        """Plan financial analysis and ROI calculations."""
        steps = [
            {
                "step_id": str(uuid4()),
                "description": "Gather project financial parameters",
                "tool_name": None,
                "estimated_duration_ms": 1500,
                "estimated_cost_psu": 2
            },
            {
                "step_id": str(uuid4()),
                "description": "Run comprehensive financial simulation",
                "tool_name": "SimulateFinanceTool",
                "inputs": {
                    "project_cost": context.current_state.get("project_cost"),
                    "energy_savings": context.current_state.get("energy_savings"),
                    "system_lifetime": context.current_state.get("system_lifetime", 25),
                    "discount_rate": self.default_discount_rate,
                    "inflation_rate": context.current_state.get("inflation_rate", 0.025)
                },
                "estimated_duration_ms": 4000,
                "estimated_cost_psu": 8
            },
            {
                "step_id": str(uuid4()),
                "description": "Calculate detailed ROI metrics",
                "tool_name": "CalculateROITool",
                "inputs": {
                    "financial_data": "from_previous_step",
                    "analysis_period": context.current_state.get("analysis_period", 25)
                },
                "estimated_duration_ms": 2500,
                "estimated_cost_psu": 5
            },
            {
                "step_id": str(uuid4()),
                "description": "Find applicable incentives and rebates",
                "tool_name": "FindIncentivesTool",
                "inputs": {
                    "location": context.current_state.get("location"),
                    "system_type": context.current_state.get("system_type", "PV"),
                    "project_size": context.current_state.get("project_size")
                },
                "estimated_duration_ms": 3000,
                "estimated_cost_psu": 6
            },
            {
                "step_id": str(uuid4()),
                "description": "Generate financial analysis report",
                "tool_name": None,
                "estimated_duration_ms": 2000,
                "estimated_cost_psu": 3
            }
        ]
        
        return steps
    
    async def _plan_proposal_generation(self, task: str, context: AgentContext) -> List[Dict[str, Any]]:
        """Plan proposal and quote generation."""
        steps = [
            {
                "step_id": str(uuid4()),
                "description": "Analyze customer requirements and preferences",
                "tool_name": "AnalyzeCustomerTool",
                "inputs": {
                    "customer_data": context.current_state.get("customer_data"),
                    "project_requirements": context.current_state.get("requirements")
                },
                "estimated_duration_ms": 2500,
                "estimated_cost_psu": 4
            },
            {
                "step_id": str(uuid4()),
                "description": "Generate customized quote",
                "tool_name": "CreateQuoteTool",
                "inputs": {
                    "project_specs": context.current_state.get("project_specs"),
                    "customer_profile": "from_previous_step",
                    "pricing_strategy": context.current_state.get("pricing_strategy", "competitive")
                },
                "estimated_duration_ms": 3500,
                "estimated_cost_psu": 7
            },
            {
                "step_id": str(uuid4()),
                "description": "Calculate financial benefits and ROI",
                "tool_name": "CalculateROITool",
                "inputs": {
                    "quote_data": "from_previous_step",
                    "customer_usage": context.current_state.get("energy_usage")
                },
                "estimated_duration_ms": 2000,
                "estimated_cost_psu": 4
            },
            {
                "step_id": str(uuid4()),
                "description": "Generate comprehensive proposal document",
                "tool_name": "GenerateProposalTool",
                "inputs": {
                    "quote_data": "from_step_2",
                    "financial_analysis": "from_step_3",
                    "customer_analysis": "from_step_1",
                    "template_type": context.current_state.get("proposal_template", "standard")
                },
                "estimated_duration_ms": 4000,
                "estimated_cost_psu": 8
            }
        ]
        
        return steps
    
    async def _plan_incentive_optimization(self, task: str, context: AgentContext) -> List[Dict[str, Any]]:
        """Plan incentive discovery and optimization."""
        steps = [
            {
                "step_id": str(uuid4()),
                "description": "Search for applicable incentives and rebates",
                "tool_name": "FindIncentivesTool",
                "inputs": {
                    "location": context.current_state.get("location"),
                    "system_type": context.current_state.get("system_type"),
                    "customer_type": context.current_state.get("customer_type", "residential"),
                    "project_size": context.current_state.get("project_size"),
                    "installation_date": context.current_state.get("installation_date")
                },
                "estimated_duration_ms": 3500,
                "estimated_cost_psu": 7
            },
            {
                "step_id": str(uuid4()),
                "description": "Optimize incentive combinations",
                "tool_name": "OptimizeIncentivesTool",
                "inputs": {
                    "available_incentives": "from_previous_step",
                    "project_parameters": context.current_state.get("project_parameters"),
                    "optimization_goal": context.current_state.get("optimization_goal", "maximize_savings")
                },
                "estimated_duration_ms": 2500,
                "estimated_cost_psu": 5
            },
            {
                "step_id": str(uuid4()),
                "description": "Calculate rebate values and timelines",
                "tool_name": "CalculateRebatesTool",
                "inputs": {
                    "optimized_incentives": "from_previous_step",
                    "project_timeline": context.current_state.get("project_timeline")
                },
                "estimated_duration_ms": 2000,
                "estimated_cost_psu": 4
            },
            {
                "step_id": str(uuid4()),
                "description": "Generate incentive optimization report",
                "tool_name": None,
                "estimated_duration_ms": 1500,
                "estimated_cost_psu": 2
            }
        ]
        
        return steps
    
    async def _plan_competitive_analysis(self, task: str, context: AgentContext) -> List[Dict[str, Any]]:
        """Plan competitive analysis."""
        steps = [
            {
                "step_id": str(uuid4()),
                "description": "Analyze competitive landscape",
                "tool_name": "AnalyzeCompetitionTool",
                "inputs": {
                    "market_segment": context.current_state.get("market_segment", "residential"),
                    "location": context.current_state.get("location"),
                    "service_offerings": context.current_state.get("service_offerings")
                },
                "estimated_duration_ms": 4000,
                "estimated_cost_psu": 8
            },
            {
                "step_id": str(uuid4()),
                "description": "Benchmark pricing strategies",
                "tool_name": "BenchmarkPricingTool",
                "inputs": {
                    "competitive_data": "from_previous_step",
                    "our_pricing": context.current_state.get("our_pricing"),
                    "value_propositions": context.current_state.get("value_propositions")
                },
                "estimated_duration_ms": 3000,
                "estimated_cost_psu": 6
            },
            {
                "step_id": str(uuid4()),
                "description": "Generate competitive positioning recommendations",
                "tool_name": None,
                "estimated_duration_ms": 2000,
                "estimated_cost_psu": 3
            }
        ]
        
        return steps
    
    async def _plan_customer_analysis(self, task: str, context: AgentContext) -> List[Dict[str, Any]]:
        """Plan customer analysis and segmentation."""
        steps = [
            {
                "step_id": str(uuid4()),
                "description": "Analyze customer profile and needs",
                "tool_name": "AnalyzeCustomerTool",
                "inputs": {
                    "customer_data": context.current_state.get("customer_data"),
                    "interaction_history": context.current_state.get("interaction_history"),
                    "preferences": context.current_state.get("customer_preferences")
                },
                "estimated_duration_ms": 3000,
                "estimated_cost_psu": 6
            },
            {
                "step_id": str(uuid4()),
                "description": "Segment customer for targeted approach",
                "tool_name": "SegmentCustomerTool",
                "inputs": {
                    "customer_analysis": "from_previous_step",
                    "segmentation_criteria": context.current_state.get("segmentation_criteria")
                },
                "estimated_duration_ms": 2000,
                "estimated_cost_psu": 4
            },
            {
                "step_id": str(uuid4()),
                "description": "Personalize recommendations and approach",
                "tool_name": "PersonalizeTool",
                "inputs": {
                    "customer_segment": "from_previous_step",
                    "available_solutions": context.current_state.get("available_solutions")
                },
                "estimated_duration_ms": 2500,
                "estimated_cost_psu": 5
            }
        ]
        
        return steps
    
    async def _plan_general_sales_task(self, task: str, context: AgentContext) -> List[Dict[str, Any]]:
        """Plan general sales advisory task."""
        steps = [
            {
                "step_id": str(uuid4()),
                "description": "Analyze sales requirements and objectives",
                "tool_name": None,
                "estimated_duration_ms": 2000,
                "estimated_cost_psu": 3
            },
            {
                "step_id": str(uuid4()),
                "description": "Generate financial analysis",
                "tool_name": "SimulateFinanceTool",
                "inputs": {
                    "basic_parameters": context.current_state.get("project_data", {})
                },
                "estimated_duration_ms": 3000,
                "estimated_cost_psu": 6
            },
            {
                "step_id": str(uuid4()),
                "description": "Provide sales recommendations",
                "tool_name": None,
                "estimated_duration_ms": 2000,
                "estimated_cost_psu": 3
            }
        ]
        
        return steps
    
    # Private execution methods
    
    async def _execute_financial_fallback(
        self,
        step: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """Execute fallback financial calculations."""
        # Simple ROI calculation fallback
        project_cost = context.current_state.get("project_cost", 100000)
        annual_savings = context.current_state.get("annual_savings", 15000)
        system_lifetime = context.current_state.get("system_lifetime", 25)
        
        # Basic calculations
        simple_payback = project_cost / annual_savings if annual_savings > 0 else 999
        total_savings = annual_savings * system_lifetime
        net_savings = total_savings - project_cost
        roi_percentage = (net_savings / project_cost) * 100 if project_cost > 0 else 0
        
        return {
            "success": True,
            "content": {
                "simple_payback_years": round(simple_payback, 1),
                "total_lifetime_savings": total_savings,
                "net_savings": net_savings,
                "roi_percentage": round(roi_percentage, 1),
                "calculation_method": "simplified_fallback"
            },
            "confidence": 0.7
        }
    
    async def _execute_sales_analysis_step(
        self,
        step: Dict[str, Any],
        context: AgentContext,
        previous_results: List[Any]
    ) -> Dict[str, Any]:
        """Execute a non-tool sales analysis step."""
        step_description = step["description"]
        
        if "gather" in step_description.lower() and "financial" in step_description.lower():
            # Gather financial parameters
            return {
                "success": True,
                "content": {
                    "financial_parameters": {
                        "project_cost": context.current_state.get("project_cost", 0),
                        "annual_savings": context.current_state.get("annual_savings", 0),
                        "system_lifetime": context.current_state.get("system_lifetime", 25),
                        "discount_rate": self.default_discount_rate,
                        "analysis_ready": True
                    }
                },
                "confidence": 0.9
            }
        
        elif "analyze" in step_description.lower() and "sales" in step_description.lower():
            # Analyze sales requirements
            return {
                "success": True,
                "content": {
                    "sales_analysis": {
                        "objectives": context.current_state.get("objectives", ["maximize_roi"]),
                        "constraints": context.current_state.get("constraints", []),
                        "customer_priorities": context.current_state.get("customer_priorities", ["cost", "quality"]),
                        "analysis_complete": True
                    }
                },
                "confidence": 0.85
            }
        
        elif "generate" in step_description.lower() and "report" in step_description.lower():
            # Generate report
            report_type = "financial" if "financial" in step_description.lower() else "sales"
            
            return {
                "success": True,
                "content": {
                    "report_type": f"{report_type}_analysis_report",
                    "timestamp": datetime.utcnow().isoformat(),
                    "summary": f"Generated {report_type} analysis report",
                    "sections": ["Executive Summary", "Financial Analysis", "Recommendations", "Next Steps"],
                    "ready_for_delivery": True
                },
                "confidence": 0.9
            }
        
        elif "recommendation" in step_description.lower():
            # Generate recommendations
            recommendations = []
            
            # Extract insights from previous results
            for result in previous_results:
                if hasattr(result, 'content') and result.content:
                    content = result.content
                    if isinstance(content, dict):
                        if "roi_percentage" in content and content["roi_percentage"] > self.min_roi_threshold * 100:
                            recommendations.append("Project shows strong financial returns")
                        if "payback_years" in content and content.get("payback_years", 999) < 10:
                            recommendations.append("Attractive payback period for customer")
                        if "incentives" in content:
                            recommendations.append("Leverage available incentives to improve value proposition")
            
            if not recommendations:
                recommendations = ["Review project parameters and optimize for customer needs"]
            
            return {
                "success": True,
                "content": {
                    "recommendations": recommendations,
                    "priority_actions": recommendations[:3],  # Top 3
                    "recommendation_confidence": 0.85
                },
                "confidence": 0.85
            }
        
        else:
            # Generic analysis step
            return {
                "success": True,
                "content": {
                    "step_completed": step_description,
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "completed"
                },
                "confidence": 0.8
            }
    
    async def _synthesize_sales_results(
        self,
        task_description: str,
        execution_results: List[Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """Synthesize sales execution results into final output."""
        synthesis = {
            "task_description": task_description,
            "execution_summary": {
                "total_steps": len(execution_results),
                "successful_steps": sum(1 for r in execution_results if getattr(r, 'success', True)),
                "execution_timestamp": datetime.utcnow().isoformat()
            },
            "financial_analysis": {},
            "sales_recommendations": [],
            "key_metrics": {},
            "next_steps": [],
            "deliverables": []
        }
        
        # Extract key information from results
        for result in execution_results:
            if hasattr(result, 'content') and result.content:
                content = result.content
                
                if isinstance(content, dict):
                    # Extract financial metrics
                    if any(key in content for key in ["roi_percentage", "payback_years", "net_savings"]):
                        synthesis["financial_analysis"].update({
                            k: v for k, v in content.items() 
                            if k in ["roi_percentage", "payback_years", "net_savings", "total_savings"]
                        })
                        synthesis["key_metrics"]["financial_viability"] = "strong" if content.get("roi_percentage", 0) > 15 else "moderate"
                    
                    # Extract incentives
                    if "incentives" in content or "rebates" in content:
                        synthesis["financial_analysis"]["incentives_available"] = True
                        if "total_incentive_value" in content:
                            synthesis["key_metrics"]["incentive_value"] = content["total_incentive_value"]
                    
                    # Extract recommendations
                    if "recommendations" in content:
                        synthesis["sales_recommendations"].extend(content["recommendations"])
                    
                    # Extract proposal/quote data
                    if "quote" in content or "proposal" in content:
                        synthesis["deliverables"].append("customized_proposal")
                        if "total_price" in content:
                            synthesis["key_metrics"]["quoted_price"] = content["total_price"]
                    
                    # Extract competitive analysis
                    if "competitive" in content:
                        synthesis["key_metrics"]["competitive_position"] = content.get("position", "competitive")
        
        # Generate sales-specific recommendations
        if "roi" in task_description.lower() or "financial" in task_description.lower():
            synthesis["sales_recommendations"].append("Present financial benefits clearly to customer")
            synthesis["next_steps"].append("Schedule financial review meeting with customer")
        
        if "proposal" in task_description.lower():
            synthesis["sales_recommendations"].append("Customize proposal based on customer priorities")
            synthesis["next_steps"].append("Deliver proposal and schedule follow-up")
        
        if "incentive" in task_description.lower():
            synthesis["sales_recommendations"].append("Highlight time-sensitive incentive opportunities")
            synthesis["next_steps"].append("Assist customer with incentive applications")
        
        # Default recommendations if none found
        if not synthesis["sales_recommendations"]:
            synthesis["sales_recommendations"] = [
                "Focus on value proposition alignment with customer needs",
                "Emphasize long-term financial benefits",
                "Address any customer concerns proactively"
            ]
        
        return synthesis
    
    async def _calculate_sales_quality_score(
        self,
        execution_results: List[Any],
        final_result: Dict[str, Any]
    ) -> float:
        """Calculate quality score for sales execution."""
        if not execution_results:
            return 0.0
        
        # Base score from successful execution
        successful_steps = sum(1 for r in execution_results if getattr(r, 'success', True))
        success_rate = successful_steps / len(execution_results)
        
        # Confidence score from results
        confidences = [getattr(r, 'confidence', 0.8) for r in execution_results if hasattr(r, 'confidence')]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.8
        
        # Completeness score based on deliverables
        completeness_factors = [
            bool(final_result.get("financial_analysis")),
            bool(final_result.get("sales_recommendations")),
            bool(final_result.get("key_metrics")),
            bool(final_result.get("next_steps"))
        ]
        completeness = sum(completeness_factors) / len(completeness_factors)
        
        # Financial viability bonus
        financial_bonus = 0.1 if final_result.get("key_metrics", {}).get("financial_viability") == "strong" else 0
        
        # Weighted final score
        quality_score = (success_rate * 0.3) + (avg_confidence * 0.3) + (completeness * 0.3) + financial_bonus
        
        return min(quality_score, 1.0)
    
    async def _suggest_sales_next_actions(
        self,
        result: Dict[str, Any],
        context: AgentContext
    ) -> List[str]:
        """Suggest next actions for sales process."""
        next_actions = []
        
        # Based on financial analysis results
        if result.get("financial_analysis"):
            financial = result["financial_analysis"]
            if financial.get("roi_percentage", 0) > 20:
                next_actions.append("Highlight strong ROI in customer presentation")
            if financial.get("payback_years", 999) < 7:
                next_actions.append("Emphasize attractive payback period")
            if financial.get("incentives_available"):
                next_actions.append("Schedule incentive application assistance")
        
        # Based on deliverables
        if "customized_proposal" in result.get("deliverables", []):
            next_actions.append("Schedule proposal presentation meeting")
            next_actions.append("Prepare for customer questions and objections")
        
        # Based on competitive analysis
        competitive_pos = result.get("key_metrics", {}).get("competitive_position")
        if competitive_pos == "strong":
            next_actions.append("Leverage competitive advantages in sales process")
        elif competitive_pos == "challenged":
            next_actions.append("Address competitive concerns proactively")
        
        # Default actions
        if not next_actions:
            next_actions = [
                "Follow up with customer on analysis results",
                "Address any questions or concerns",
                "Move to next stage of sales process"
            ]
        
        return next_actions
    
    async def _calculate_plan_confidence(
        self,
        task: str,
        context: AgentContext,
        steps: List[Dict[str, Any]]
    ) -> float:
        """Calculate confidence in the sales plan."""
        base_confidence = 0.85  # Higher base confidence for sales tasks
        
        # Adjust based on available customer data
        if context.current_state.get("customer_data"):
            base_confidence += 0.05
        if context.current_state.get("project_cost") and context.current_state.get("annual_savings"):
            base_confidence += 0.05
        if context.current_state.get("location"):
            base_confidence += 0.03  # For incentive analysis
        
        # Adjust based on task complexity
        task_lower = task.lower()
        if "comprehensive" in task_lower or "detailed" in task_lower:
            base_confidence -= 0.05
        if "simple" in task_lower or "basic" in task_lower:
            base_confidence += 0.05
        
        return min(base_confidence, 1.0)
    
    async def _generate_plan_reasoning(self, task: str, steps: List[Dict[str, Any]]) -> str:
        """Generate reasoning for the sales plan."""
        reasoning_parts = [
            f"Created {len(steps)}-step sales advisory plan for: {task}"
        ]
        
        # Categorize steps
        tool_steps = [s for s in steps if s.get("tool_name")]
        analysis_steps = [s for s in steps if not s.get("tool_name")]
        
        if tool_steps:
            reasoning_parts.append(f"Plan includes {len(tool_steps)} specialized tool executions")
        
        if analysis_steps:
            reasoning_parts.append(f"Plan includes {len(analysis_steps)} analysis and synthesis steps")
        
        # Mention specific capabilities
        if any("financial" in s["description"].lower() or "roi" in s["description"].lower() for s in steps):
            reasoning_parts.append("Financial analysis capabilities will provide ROI insights")
        
        if any("proposal" in s["description"].lower() or "quote" in s["description"].lower() for s in steps):
            reasoning_parts.append("Proposal generation capabilities will create customized offers")
        
        if any("incentive" in s["description"].lower() for s in steps):
            reasoning_parts.append("Incentive optimization will maximize customer value")
        
        if any("competitive" in s["description"].lower() for s in steps):
            reasoning_parts.append("Competitive analysis will inform positioning strategy")
        
        return " ".join(reasoning_parts)

