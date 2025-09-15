"""
Simple Phase 1 Test - Core AI Infrastructure
Tests basic functionality of each component individually.
"""
import asyncio
import sys
import os
import json
import logging
from datetime import datetime
from pathlib import Path

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


async def test_episodic_memory():
    """Test episodic memory system."""
    logger.info("Testing Episodic Memory...")

    try:
        from memory.episodic import EpisodicMemory

        # Create test database
        db_path = Path("test_data/episodic_test.db")
        db_path.parent.mkdir(exist_ok=True)

        episodic = EpisodicMemory(db_path)
        await episodic.initialize()

        # Store interaction
        interaction_id = await episodic.store_interaction(
            session_id="test_session",
            interaction_type="test_message",
            content={"message": "Test content", "timestamp": datetime.utcnow().isoformat()},
            agent_id="test_agent"
        )

        # Retrieve interactions
        history = await episodic.get_session_history("test_session")

        assert len(history) >= 1, "No interactions retrieved"
        assert history[0].content["message"] == "Test content"

        logger.info("✓ Episodic Memory working")
        return True

    except Exception as e:
        logger.error(f"✗ Episodic Memory failed: {str(e)}")
        return False


async def test_semantic_memory():
    """Test semantic memory system."""
    logger.info("Testing Semantic Memory...")

    try:
        from memory.semantic import SemanticMemory

        # Create test database
        db_path = Path("test_data/semantic_test.db")
        semantic = SemanticMemory(db_path)
        await semantic.initialize()

        # Store knowledge
        knowledge_id = await semantic.store_knowledge(
            knowledge_type="test_fact",
            title="Test Knowledge",
            content="This is test knowledge content for validation.",
            tags=["test", "validation"]
        )

        # Retrieve knowledge
        results = await semantic.retrieve_knowledge("test knowledge", limit=5)

        assert len(results) >= 1, "No knowledge retrieved"

        logger.info("✓ Semantic Memory working")
        return True

    except Exception as e:
        logger.error(f"✗ Semantic Memory failed: {str(e)}")
        return False


async def test_cag_store():
    """Test CAG store system."""
    logger.info("Testing CAG Store...")

    try:
        from memory.cag_store import CAGStore, CacheType

        # Create test database
        db_path = Path("test_data/cag_test.db")
        cag = CAGStore(db_path=db_path)
        await cag.initialize()

        # Store content
        test_content = {"response": "Test cached response", "confidence": 0.9}
        success = await cag.set(
            cache_key="test_key",
            content=test_content,
            cache_type=CacheType.PROMPT_RESPONSE
        )

        assert success, "Failed to store content"

        # Retrieve content
        retrieved = await cag.get("test_key")
        assert retrieved == test_content, "Retrieved content doesn't match"

        logger.info("✓ CAG Store working")
        return True

    except Exception as e:
        logger.error(f"✗ CAG Store failed: {str(e)}")
        return False


async def test_graph_rag():
    """Test Graph-RAG system."""
    logger.info("Testing Graph-RAG...")

    try:
        from memory.graph_rag import ODLSDGraphRAG, GraphQuery

        # Create test database
        db_path = Path("test_data/graph_test.db")
        graph = ODLSDGraphRAG(db_path)
        await graph.initialize()

        # Test document ingestion
        test_doc = {
            "project_name": "Test Project",
            "domain": "PV",
            "components": {
                "test_panel": {
                    "name": "Test Solar Panel",
                    "type": "solar_panel",
                    "specifications": {"power": 400}
                }
            }
        }

        count = await graph.ingest_odl_document(
            document=test_doc,
            document_id="test_doc",
            project_id="test_project"
        )

        assert count > 0, "No nodes/edges created"

        logger.info("✓ Graph-RAG working")
        return True

    except Exception as e:
        logger.error(f"✗ Graph-RAG failed: {str(e)}")
        return False


async def test_task_planner():
    """Test task planner."""
    logger.info("Testing Task Planner...")

    try:
        from planner.planner import TaskPlanner

        planner = TaskPlanner()

        # Create a simple plan
        plan = await planner.create_plan(
            task_type="general_query",
            task_description="Test task planning functionality",
            context={"test_mode": True}
        )

        assert plan.steps, "No plan steps created"
        assert len(plan.steps) > 0, "Plan has no steps"

        logger.info("✓ Task Planner working")
        return True

    except Exception as e:
        logger.error(f"✗ Task Planner failed: {str(e)}")
        return False


async def test_policy_router():
    """Test policy router."""
    logger.info("Testing Policy Router...")

    try:
        from planner.policy_router import PolicyRouter, PolicyDecision

        router = PolicyRouter()

        # Allocate budget
        await router.allocate_psu_budget("test_tenant", 1000)

        # Check policy
        decision, reason, mods = await router.check_policy_compliance(
            task_id="test_task",
            tenant_id="test_tenant",
            user_id="test_user",
            estimated_psu_cost=10,
            estimated_duration_ms=5000,
            required_permissions=[],
            context={"user_role": "admin"}
        )

        assert decision == PolicyDecision.APPROVE, f"Policy denied: {reason}"

        logger.info("✓ Policy Router working")
        return True

    except Exception as e:
        logger.error(f"✗ Policy Router failed: {str(e)}")
        return False


async def test_region_router():
    """Test region router."""
    logger.info("Testing Region Router...")

    try:
        from planner.region_router import RegionRouter, ModelCapability

        router = RegionRouter()

        # Get region config
        config = await router.get_region_config("test_tenant", {})
        assert config is not None, "No region config"

        # Select model
        selection = await router.select_model(
            capability=ModelCapability.TEXT_GENERATION,
            region=config.region,
            context={}
        )

        assert selection.selected_model is not None, "No model selected"

        logger.info("✓ Region Router working")
        return True

    except Exception as e:
        logger.error(f"✗ Region Router failed: {str(e)}")
        return False


async def test_critic_verifier():
    """Test critic verifier."""
    logger.info("Testing Critic Verifier...")

    try:
        from planner.critic import CriticVerifier
        from tools.registry import ToolResult

        critic = CriticVerifier()

        # Mock plan object
        class MockPlan:
            def __init__(self):
                self.plan_id = "test_plan"
                self.task_description = "Test task"

        # Create mock results
        results = [
            ToolResult(
                success=True,
                content={"result": "Test successful execution"},
                execution_time_ms=1000,
                intent="Test execution"
            )
        ]

        # Verify results
        verification = await critic.verify_results(
            plan=MockPlan(),
            execution_results=results,
            context={}
        )

        assert verification.overall_score >= 0, "Invalid verification score"

        logger.info("✓ Critic Verifier working")
        return True

    except Exception as e:
        logger.error(f"✗ Critic Verifier failed: {str(e)}")
        return False


async def run_all_tests():
    """Run all Phase 1 tests."""
    logger.info("🚀 Starting Phase 1 Component Tests")

    # Create test data directory
    Path("test_data").mkdir(exist_ok=True)

    tests = [
        ("Episodic Memory", test_episodic_memory),
        ("Semantic Memory", test_semantic_memory),
        ("CAG Store", test_cag_store),
        ("Graph-RAG", test_graph_rag),
        ("Task Planner", test_task_planner),
        ("Policy Router", test_policy_router),
        ("Region Router", test_region_router),
        ("Critic Verifier", test_critic_verifier),
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
    logger.info("PHASE 1 TEST RESULTS")
    logger.info("=" * 50)

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{test_name:20} {status}")

    logger.info("")
    logger.info(f"Tests passed: {passed}/{total}")

    if passed == total:
        logger.info("🎉 ALL PHASE 1 TESTS PASSED!")
        logger.info("✅ Core AI Infrastructure is working correctly")
        logger.info("🚀 Ready to proceed to Phase 2: Agent Development")
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
        success = await run_all_tests()
        await cleanup()
        return success

    # Run the tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

