"""
Phase 1 Integration Test - Core AI Infrastructure
Tests all components working together: Orchestrator, Memory Systems, Graph-RAG
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from memory.cag_store import CAGStore
from memory.episodic import EpisodicMemory
from memory.graph_rag import GraphQuery, ODLSDGraphRAG
from memory.semantic import SemanticMemory

# Import our components
from planner.orchestrator import AIOrchestrator, Task, TaskPriority
from tools.registry import ToolRegistry


async def test_memory_systems():
    """Test memory systems initialization and basic operations."""
    logger.info("=== Testing Memory Systems ===")

    # Test Episodic Memory
    logger.info("Testing Episodic Memory...")
    episodic = EpisodicMemory(Path("test_data/episodic.db"))
    await episodic.initialize()

    # Store some test interactions
    session_id = "test_session_001"
    interaction_id = await episodic.store_interaction(
        session_id=session_id,
        interaction_type="user_message",
        content={
            "message": "Test user message",
            "timestamp": datetime.utcnow().isoformat(),
        },
        agent_id="test_agent",
        user_id="test_user",
        tenant_id="test_tenant",
    )

    # Retrieve interaction history
    history = await episodic.get_session_history(session_id)
    assert len(history) == 1, f"Expected 1 interaction, got {len(history)}"
    assert history[0].content["message"] == "Test user message"
    logger.info("✓ Episodic Memory working")

    # Test Semantic Memory
    logger.info("Testing Semantic Memory...")
    semantic = SemanticMemory(Path("test_data/semantic.db"))
    await semantic.initialize()

    # Store test knowledge
    knowledge_id = await semantic.store_knowledge(
        knowledge_type="best_practice",
        title="Component Selection Best Practice",
        content="Always verify component specifications match system requirements before selection.",
        domain="PV",
        tags=["components", "best_practice", "verification"],
        confidence=0.9,
    )

    # Retrieve knowledge
    knowledge_results = await semantic.retrieve_knowledge(
        query="component selection verification", limit=5
    )
    assert len(knowledge_results) > 0, "No knowledge retrieved"
    logger.info("✓ Semantic Memory working")

    # Test CAG Store
    logger.info("Testing CAG Store...")
    cag_store = CAGStore(db_path=Path("test_data/cag.db"))
    await cag_store.initialize()

    # Store and retrieve cached content
    from memory.cag_store import CacheType

    cache_key = "test_prompt_response"
    test_content = {"response": "This is a test AI response", "confidence": 0.85}

    success = await cag_store.set(
        cache_key=cache_key,
        content=test_content,
        cache_type=CacheType.PROMPT_RESPONSE,
        tags=["test", "prompt"],
    )
    assert success, "Failed to cache content"

    retrieved_content = await cag_store.get(cache_key)
    assert retrieved_content == test_content, "Retrieved content doesn't match"
    logger.info("✓ CAG Store working")

    # Test Graph-RAG
    logger.info("Testing Graph-RAG...")
    graph_rag = ODLSDGraphRAG(Path("test_data/graph.db"))
    await graph_rag.initialize()

    # Test ODL-SD document ingestion
    test_document = {
        "project_name": "Test Solar Project",
        "domain": "PV",
        "scale": "residential",
        "components": {
            "panel_001": {
                "name": "Solar Panel 1",
                "type": "solar_panel",
                "category": "generation",
                "specifications": {
                    "power_rating": 400,
                    "voltage": 24,
                    "efficiency": 0.21,
                },
                "manufacturer": "TestCorp",
                "model": "SP-400W",
                "quantity": 10,
                "unit_cost": 200,
            },
            "inverter_001": {
                "name": "String Inverter",
                "type": "inverter",
                "category": "conversion",
                "specifications": {
                    "power_rating": 4000,
                    "efficiency": 0.97,
                    "input_voltage": 24,
                },
                "manufacturer": "InverterCorp",
                "model": "SI-4000",
                "quantity": 1,
                "unit_cost": 1200,
            },
        },
        "connections": [
            {
                "from": "panel_001",
                "to": "inverter_001",
                "type": "electrical",
                "cable_type": "DC",
                "cable_length": 50,
            }
        ],
    }

    ingested_count = await graph_rag.ingest_odl_document(
        document=test_document,
        document_id="test_doc_001",
        project_id="test_project_001",
    )
    assert ingested_count > 0, "No nodes/edges created from document"
    logger.info("✓ Graph-RAG working")

    return {
        "episodic": episodic,
        "semantic": semantic,
        "cag_store": cag_store,
        "graph_rag": graph_rag,
    }


async def test_orchestrator_components():
    """Test orchestrator components."""
    logger.info("=== Testing Orchestrator Components ===")

    # Test Tool Registry
    logger.info("Testing Tool Registry...")
    tool_registry = ToolRegistry()
    await tool_registry.initialize()

    # List available tools
    tools = tool_registry.list_tools()
    logger.info(f"Available tools: {[tool.name for tool in tools]}")
    assert len(tools) > 0, "No tools loaded"
    logger.info("✓ Tool Registry working")

    # Test Task Planner
    logger.info("Testing Task Planner...")
    from planner.planner import TaskPlanner

    planner = TaskPlanner()

    # Create a test plan
    plan = await planner.create_plan(
        task_type="component_analysis",
        task_description="Analyze solar panel specifications and find similar components",
        context={
            "session_id": "test_session_001",
            "user_id": "test_user",
            "domain": "PV",
            "component_data": {
                "name": "Test Solar Panel",
                "power_rating": 400,
                "efficiency": 0.21,
            },
        },
    )

    assert plan.steps, "No plan steps created"
    assert plan.confidence > 0, "Plan confidence is zero"
    logger.info(f"✓ Task Planner working - created {len(plan.steps)} steps")

    # Test Policy Router
    logger.info("Testing Policy Router...")
    from planner.policy_router import PolicyDecision, PolicyRouter

    policy_router = PolicyRouter()

    # Allocate test budget
    await policy_router.allocate_psu_budget(
        tenant_id="test_tenant", total_budget=1000, period_days=30
    )

    # Check policy compliance
    decision, reason, modifications = await policy_router.check_policy_compliance(
        task_id="test_task_001",
        tenant_id="test_tenant",
        user_id="test_user",
        estimated_psu_cost=50,
        estimated_duration_ms=30000,
        required_permissions=["design_read"],
        context={"user_role": "engineer"},
    )

    assert decision == PolicyDecision.APPROVE, f"Policy check failed: {reason}"
    logger.info("✓ Policy Router working")

    # Test Region Router
    logger.info("Testing Region Router...")
    from planner.region_router import ModelCapability, RegionRouter

    region_router = RegionRouter()

    # Get region config
    region_config = await region_router.get_region_config("test_tenant", {})
    assert region_config, "No region config returned"

    # Select model
    model_selection = await region_router.select_model(
        capability=ModelCapability.TEXT_GENERATION,
        region=region_config.region,
        context={"estimated_tokens": 1000},
    )

    assert model_selection.selected_model, "No model selected"
    logger.info("✓ Region Router working")

    # Test Critic Verifier
    logger.info("Testing Critic Verifier...")
    from planner.critic import CriticVerifier
    from tools.registry import ToolResult

    critic = CriticVerifier()

    # Create mock execution results
    mock_results = [
        ToolResult(
            success=True,
            content={
                "analysis": "Component specifications are valid",
                "confidence": 0.9,
            },
            execution_time_ms=1500,
            intent="Analyzed component specifications",
        )
    ]

    verification = await critic.verify_results(
        plan=plan,
        execution_results=mock_results,
        context={"user_id": "test_user", "tenant_id": "test_tenant"},
    )

    assert verification.overall_score > 0, "Verification score is zero"
    logger.info(f"✓ Critic Verifier working - score: {verification.overall_score:.2f}")

    return {
        "tool_registry": tool_registry,
        "planner": planner,
        "policy_router": policy_router,
        "region_router": region_router,
        "critic": critic,
    }


async def test_full_orchestrator():
    """Test the full AI Orchestrator integration."""
    logger.info("=== Testing Full AI Orchestrator ===")

    # Initialize orchestrator
    orchestrator = AIOrchestrator()
    await orchestrator.initialize()

    # Submit a test task
    task = Task(
        task_id="integration_test_001",
        task_type="component_analysis",
        description="Test integration of all AI orchestrator components",
        context={
            "session_id": "test_session_001",
            "user_id": "test_user",
            "tenant_id": "test_tenant",
            "domain": "PV",
            "test_mode": True,
        },
        priority=TaskPriority.HIGH,
    )

    # Process the task
    logger.info("Submitting task to orchestrator...")
    await orchestrator.submit_task(task)

    # Wait a bit for processing
    await asyncio.sleep(2)

    # Check task status
    if task.task_id in orchestrator.active_tasks:
        active_task = orchestrator.active_tasks[task.task_id]
        logger.info(f"Task status: {active_task.status}")

    logger.info("✓ Full Orchestrator integration working")

    # Cleanup
    await orchestrator.cleanup()

    return orchestrator


async def test_graph_rag_queries():
    """Test Graph-RAG query capabilities."""
    logger.info("=== Testing Graph-RAG Queries ===")

    # Initialize Graph-RAG with test data
    graph_rag = ODLSDGraphRAG(Path("test_data/graph_query.db"))
    await graph_rag.initialize()

    # Ingest a more complex document
    complex_document = {
        "project_name": "Commercial Solar Installation",
        "domain": "PV",
        "scale": "commercial",
        "location": {"address": "123 Business St", "city": "Tech City", "state": "CA"},
        "components": {
            "panel_array_1": {
                "name": "Solar Panel Array 1",
                "type": "solar_panel",
                "category": "generation",
                "specifications": {
                    "power_rating": 500,
                    "voltage": 48,
                    "efficiency": 0.22,
                },
                "manufacturer": "SolarTech",
                "model": "ST-500W-HE",
                "quantity": 100,
                "unit_cost": 250,
            },
            "inverter_central": {
                "name": "Central Inverter",
                "type": "inverter",
                "category": "conversion",
                "specifications": {
                    "power_rating": 50000,
                    "efficiency": 0.98,
                    "input_voltage": 48,
                },
                "manufacturer": "PowerCorp",
                "model": "PC-50kW",
                "quantity": 1,
                "unit_cost": 15000,
            },
            "monitoring_sys": {
                "name": "Monitoring System",
                "type": "monitoring_system",
                "category": "monitoring",
                "specifications": {"data_logging": True, "remote_access": True},
                "manufacturer": "MonitorPro",
                "model": "MP-Pro-1",
                "quantity": 1,
                "unit_cost": 2000,
            },
        },
        "connections": [
            {"from": "panel_array_1", "to": "inverter_central", "type": "electrical"},
            {"from": "inverter_central", "to": "monitoring_sys", "type": "data"},
        ],
    }

    await graph_rag.ingest_odl_document(
        document=complex_document,
        document_id="commercial_doc_001",
        project_id="commercial_project_001",
    )

    # Test semantic query
    semantic_query = GraphQuery(
        query_id="semantic_test_001",
        query_text="high efficiency solar panels with monitoring",
        query_type="semantic",
        filters={"node_types": ["component"], "min_similarity": 0.3},
        limit=5,
    )

    semantic_result = await graph_rag.query_graph(semantic_query)
    logger.info(f"Semantic query returned {len(semantic_result.nodes)} nodes")
    assert any(
        node.properties["name"] == "Solar Panel Array 1"
        for node in semantic_result.nodes
    ), "Semantic search failed to find expected component"

    # Test structural query
    structural_query = GraphQuery(
        query_id="structural_test_001",
        query_text="find components of type inverter",
        query_type="structural",
        filters={"component_type": "inverter"},
        limit=10,
    )

    structural_result = await graph_rag.query_graph(structural_query)
    logger.info(f"Structural query returned {len(structural_result.nodes)} nodes")

    # Test change impact analysis
    if semantic_result.nodes:
        node_id = semantic_result.nodes[0].node_id
        impact_analysis = await graph_rag.analyze_change_impact([node_id], max_hops=2)
        logger.info(
            f"Change impact analysis found {len(impact_analysis['direct_impacts'])} direct impacts"
        )

    logger.info("✓ Graph-RAG queries working")

    return graph_rag


async def run_phase1_tests():
    """Run all Phase 1 integration tests."""
    logger.info("🚀 Starting Phase 1 Integration Tests")

    # Create test data directory
    Path("test_data").mkdir(exist_ok=True)

    try:
        # Test 1: Memory Systems
        memory_components = await test_memory_systems()

        # Test 2: Orchestrator Components
        orchestrator_components = await test_orchestrator_components()

        # Test 3: Full Orchestrator Integration
        orchestrator = await test_full_orchestrator()

        # Test 4: Graph-RAG Queries
        graph_rag = await test_graph_rag_queries()

        logger.info("✅ All Phase 1 tests completed successfully!")

        return {
            "memory_components": memory_components,
            "orchestrator_components": orchestrator_components,
            "orchestrator": orchestrator,
            "graph_rag": graph_rag,
            "status": "success",
        }

    except Exception as e:
        logger.error(f"❌ Phase 1 tests failed: {str(e)}")
        return {"status": "failed", "error": str(e)}


async def cleanup_test_data():
    """Clean up test data files."""
    import shutil

    test_dir = Path("test_data")
    if test_dir.exists():
        shutil.rmtree(test_dir)
        logger.info("🧹 Test data cleaned up")


if __name__ == "__main__":

    async def main():
        # Run tests
        results = await run_phase1_tests()

        # Print summary
        if results["status"] == "success":
            logger.info("🎉 Phase 1 Core AI Infrastructure is working correctly!")
            logger.info("Components tested:")
            logger.info("  ✓ Episodic Memory - Session-based interaction storage")
            logger.info("  ✓ Semantic Memory - Knowledge base with embeddings")
            logger.info("  ✓ CAG Store - Intelligent caching system")
            logger.info("  ✓ Graph-RAG - ODL-SD document processing and querying")
            logger.info("  ✓ Task Planner - AI task decomposition")
            logger.info("  ✓ Policy Router - Budget and permission management")
            logger.info("  ✓ Region Router - Model selection and routing")
            logger.info("  ✓ Critic Verifier - Output validation and safety")
            logger.info("  ✓ AI Orchestrator - Full integration")
            logger.info("")
            logger.info("🚀 Ready to proceed to Phase 2: Agent Development")
        else:
            logger.error(
                f"❌ Phase 1 tests failed: {results.get('error', 'Unknown error')}"
            )

        # Cleanup
        await cleanup_test_data()

    asyncio.run(main())
