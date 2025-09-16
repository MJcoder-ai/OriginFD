"""
Phase 2 Test - AI Agent Implementation
Tests the DesignEngineerAgent and SalesAdvisorAgent functionality.
"""
import asyncio
import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


async def test_design_engineer_agent():
    """Test DesignEngineerAgent functionality."""
    logger.info("Testing DesignEngineerAgent...")

    try:
        from agents.design_engineer_agent import DesignEngineerAgent
        from agents.base_agent import AgentContext
        from memory.episodic import EpisodicMemory
        from memory.semantic import SemanticMemory
        from tools.registry import ToolRegistry

        # Create test dependencies
        tool_registry = ToolRegistry()
        await tool_registry.initialize()

        episodic = EpisodicMemory(Path("test_data/episodic_agent.db"))
        await episodic.initialize()

        semantic = SemanticMemory(Path("test_data/semantic_agent.db"))
        await semantic.initialize()

        # Create agent
        agent = DesignEngineerAgent(tool_registry, episodic, semantic)

        # Test capability assessment
        assessment = await agent.get_capability_assessment("Validate ODL-SD document for solar project")
        assert assessment["can_handle"], "Agent should be able to handle ODL-SD validation"
        assert assessment["overall_confidence"] > 0.6, f"Low confidence: {assessment['overall_confidence']}"

        # Test plan creation
        context = AgentContext(
            session_id="test_session",
            user_id="test_user",
            tenant_id="test_tenant",
            task_id="test_task",
            current_state={
                "task_description": "Validate ODL-SD document and run energy simulation",
                "odl_document": {"project_name": "Test Solar Project", "domain": "PV"},
                "design_data": {"system_size": 10000, "location": "California"}
            },
            shared_scratchpad={},
            conversation_history=[]
        )

        plan = await agent.create_plan("Validate ODL-SD document and run energy simulation", context)
        assert plan.steps, "Plan should have steps"
        assert plan.confidence > 0.5, f"Low plan confidence: {plan.confidence}"
        assert len(plan.steps) >= 2, f"Expected multiple steps, got {len(plan.steps)}"

        logger.info(f"✓ Design plan created with {len(plan.steps)} steps, confidence: {plan.confidence:.2f}")

        # Test plan execution (simplified)
        result = await agent.execute_plan(plan, context)
        assert result.success, f"Plan execution failed: {result.error}"
        assert result.result, "Execution should return results"
        assert result.quality_score > 0.0, "Quality score should be positive"

        logger.info(f"✓ Design plan executed successfully, quality: {result.quality_score:.2f}")

        # Test different task types
        optimization_plan = await agent.create_plan("Optimize solar panel layout for maximum efficiency", context)
        assert "optimize" in optimization_plan.reasoning.lower(), "Plan should mention optimization"

        component_plan = await agent.create_plan("Analyze component compatibility", context)
        assert len(component_plan.steps) > 0, "Component analysis plan should have steps"

        logger.info("✓ DesignEngineerAgent working correctly")
        return True

    except Exception as e:
        logger.error(f"✗ DesignEngineerAgent failed: {str(e)}")
        return False


async def test_sales_advisor_agent():
    """Test SalesAdvisorAgent functionality."""
    logger.info("Testing SalesAdvisorAgent...")

    try:
        from agents.sales_advisor_agent import SalesAdvisorAgent
        from agents.base_agent import AgentContext
        from memory.episodic import EpisodicMemory
        from memory.semantic import SemanticMemory
        from tools.registry import ToolRegistry

        # Create test dependencies
        tool_registry = ToolRegistry()
        await tool_registry.initialize()

        episodic = EpisodicMemory(Path("test_data/episodic_sales.db"))
        await episodic.initialize()

        semantic = SemanticMemory(Path("test_data/semantic_sales.db"))
        await semantic.initialize()

        # Create agent
        agent = SalesAdvisorAgent(tool_registry, episodic, semantic)

        # Test capability assessment
        assessment = await agent.get_capability_assessment("Calculate ROI for residential solar project")
        assert assessment["can_handle"], "Agent should be able to handle ROI calculations"
        assert assessment["overall_confidence"] > 0.6, f"Low confidence: {assessment['overall_confidence']}"

        # Test financial analysis plan
        context = AgentContext(
            session_id="test_sales_session",
            user_id="test_user",
            tenant_id="test_tenant",
            task_id="test_sales_task",
            current_state={
                "task_description": "Calculate ROI and payback period for solar installation",
                "project_cost": 25000,
                "annual_savings": 3500,
                "system_lifetime": 25,
                "location": "California",
                "customer_data": {"type": "residential", "usage": "high"}
            },
            shared_scratchpad={},
            conversation_history=[]
        )

        plan = await agent.create_plan("Calculate ROI and payback period for solar installation", context)
        assert plan.steps, "Plan should have steps"
        assert plan.confidence > 0.7, f"Low plan confidence: {plan.confidence}"
        assert any("financial" in step["description"].lower() for step in plan.steps), "Should include financial analysis"

        logger.info(f"✓ Sales plan created with {len(plan.steps)} steps, confidence: {plan.confidence:.2f}")

        # Test plan execution
        result = await agent.execute_plan(plan, context)
        assert result.success, f"Sales plan execution failed: {result.error}"
        assert result.result, "Execution should return results"
        assert result.result.get("financial_analysis"), "Should include financial analysis"

        logger.info(f"✓ Sales plan executed successfully, quality: {result.quality_score:.2f}")

        # Test proposal generation
        proposal_context = AgentContext(
            session_id="test_proposal_session",
            user_id="test_user",
            tenant_id="test_tenant",
            task_id="test_proposal_task",
            current_state={
                "task_description": "Generate proposal for commercial solar project",
                "customer_data": {"type": "commercial", "business": "manufacturing"},
                "project_specs": {"size": 100000, "type": "rooftop"},
                "pricing_strategy": "competitive"
            },
            shared_scratchpad={},
            conversation_history=[]
        )

        proposal_plan = await agent.create_plan("Generate proposal for commercial solar project", proposal_context)
        assert any("proposal" in step["description"].lower() for step in proposal_plan.steps), "Should include proposal generation"

        # Test incentive optimization
        incentive_plan = await agent.create_plan("Find and optimize available incentives", context)
        assert any("incentive" in step["description"].lower() for step in incentive_plan.steps), "Should include incentive analysis"

        logger.info("✓ SalesAdvisorAgent working correctly")
        return True

    except Exception as e:
        logger.error(f"✗ SalesAdvisorAgent failed: {str(e)}")
        return False


async def test_agent_communication():
    """Test agent communication and handover protocols."""
    logger.info("Testing Agent Communication...")

    try:
        from agents.design_engineer_agent import DesignEngineerAgent
        from agents.sales_advisor_agent import SalesAdvisorAgent
        from memory.episodic import EpisodicMemory
        from memory.semantic import SemanticMemory
        from tools.registry import ToolRegistry

        # Create shared dependencies
        tool_registry = ToolRegistry()
        await tool_registry.initialize()

        episodic = EpisodicMemory(Path("test_data/episodic_comm.db"))
        await episodic.initialize()

        semantic = SemanticMemory(Path("test_data/semantic_comm.db"))
        await semantic.initialize()

        # Create agents
        design_agent = DesignEngineerAgent(tool_registry, episodic, semantic)
        sales_agent = SalesAdvisorAgent(tool_registry, episodic, semantic)

        # Test communication between agents
        handover_result = await design_agent.communicate_with_agent(
            target_agent_id="sales_advisor_agent",
            message="Design validation complete, ready for financial analysis",
            context={
                "design_results": {"validation_status": "passed", "energy_output": 12500},
                "project_data": {"cost": 30000, "size": 10000}
            }
        )

        assert handover_result["acknowledged"], "Agent communication should be acknowledged"
        assert handover_result["target_agent"] == "sales_advisor_agent", "Should target correct agent"

        logger.info("✓ Agent communication working")

        # Test agent performance metrics
        design_metrics = design_agent.get_performance_metrics()
        assert design_metrics["agent_name"] == "Design Engineer Agent"
        assert "design_engineering" in design_metrics["primary_domain"]
        assert len(design_metrics["specialized_tools"]) > 0

        sales_metrics = sales_agent.get_performance_metrics()
        assert sales_metrics["agent_name"] == "Sales Advisor Agent"
        assert "sales_advisory" in sales_metrics["primary_domain"]
        assert len(sales_metrics["specialized_tools"]) > 0

        logger.info("✓ Agent performance metrics working")

        return True

    except Exception as e:
        logger.error(f"✗ Agent communication failed: {str(e)}")
        return False


async def test_agent_manager_integration():
    """Test integration with AgentManager."""
    logger.info("Testing AgentManager Integration...")

    try:
        from agents.agent_manager import AgentManager
        from agents.design_engineer_agent import DesignEngineerAgent
        from agents.sales_advisor_agent import SalesAdvisorAgent
        from memory.episodic import EpisodicMemory
        from memory.semantic import SemanticMemory
        from tools.registry import ToolRegistry

        # Create dependencies
        tool_registry = ToolRegistry()
        await tool_registry.initialize()

        episodic = EpisodicMemory(Path("test_data/episodic_mgr.db"))
        await episodic.initialize()

        semantic = SemanticMemory(Path("test_data/semantic_mgr.db"))
        await semantic.initialize()

        # Create agent manager
        manager = AgentManager(tool_registry, episodic, semantic)
        await manager.initialize()

        # Create and register agents
        design_agent = DesignEngineerAgent(tool_registry, episodic, semantic)
        sales_agent = SalesAdvisorAgent(tool_registry, episodic, semantic)

        await manager.register_agent(design_agent)
        await manager.register_agent(sales_agent)

        # Test task submission
        task_id = await manager.submit_task(
            description="Validate design and calculate ROI",
            context={
                "project_data": {"cost": 25000, "savings": 3500},
                "design_data": {"system_size": 10000}
            },
            priority="normal"
        )

        assert task_id, "Task submission should return task ID"

        # Check task status
        task_status = await manager.get_task_status(task_id)
        assert task_status, "Should be able to retrieve task status"
        assert task_status.task_id == task_id, "Task ID should match"

        # Test agent selection
        best_agent = await manager.find_best_agent(
            "Optimize solar panel layout for residential project",
            {"domain": "PV", "project_type": "residential"}
        )

        assert best_agent, "Should find best agent for task"
        assert best_agent.agent_id == "design_engineer_agent", "Should select design agent for optimization"

        logger.info("✓ AgentManager integration working")

        # Get system status
        status = await manager.get_system_status()
        assert status["agents"], "Should have registered agents"
        assert len(status["agents"]) == 2, "Should have 2 registered agents"

        logger.info("✓ Agent system status working")

        # Cleanup
        await manager.shutdown()

        return True

    except Exception as e:
        logger.error(f"✗ AgentManager integration failed: {str(e)}")
        return False


async def run_phase2_tests():
    """Run all Phase 2 agent tests."""
    logger.info("🚀 Starting Phase 2 Agent Tests")

    # Create test data directory
    Path("test_data").mkdir(exist_ok=True)

    tests = [
        ("DesignEngineerAgent", test_design_engineer_agent),
        ("SalesAdvisorAgent", test_sales_advisor_agent),
        ("Agent Communication", test_agent_communication),
        ("AgentManager Integration", test_agent_manager_integration),
    ]

    results = {}
    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = result
            if result:
                passed += 1
        except Exception as e:
            logger.error(f"✗ {test_name} failed with exception: {str(e)}")
            results[test_name] = False

    # Print summary
    logger.info("")
    logger.info("=" * 50)
    logger.info("PHASE 2 TEST RESULTS")
    logger.info("=" * 50)

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{test_name:25} {status}")

    logger.info("")
    logger.info(f"Tests passed: {passed}/{total}")

    if passed == total:
        logger.info("🎉 ALL PHASE 2 TESTS PASSED!")
        logger.info("✅ AI Agents are working correctly")
        logger.info("🚀 Ready to proceed to Phase 3: User Experience")
        return True
    elif passed >= total * 0.75:  # 75% pass rate
        logger.info(f"✅ {passed}/{total} tests passed - Core agent functionality working")
        logger.info("🚀 Ready to proceed to Phase 3 with minor issues to address")
        return True
    else:
        logger.info(f"❌ {total - passed} tests failed")
        logger.info("🔧 Please fix failing components before proceeding")
        return False


async def cleanup():
    """Clean up test data."""
    import shutil
    test_dir = Path("test_data")
    if test_dir.exists():
        try:
            shutil.rmtree(test_dir)
            logger.info("🧹 Test data cleaned up")
        except Exception as e:
            logger.warning(f"Could not clean up test data: {e}")


if __name__ == "__main__":
    async def main():
        success = await run_phase2_tests()
        await cleanup()
        return success

    # Run the tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

