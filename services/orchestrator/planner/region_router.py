"""
Region Router for OriginFD AI Orchestrator.
Handles regional model selection, data residency, and compliance.
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4
from pydantic import BaseModel
from enum import Enum

logger = logging.getLogger(__name__)


class Region(str, Enum):
    """Supported regions."""
    US_EAST = "us-east"
    US_WEST = "us-west"
    EU_CENTRAL = "eu-central"
    EU_WEST = "eu-west"
    APAC_SOUTHEAST = "apac-southeast"
    APAC_NORTHEAST = "apac-northeast"


class ModelProvider(str, Enum):
    """AI model providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure-openai"
    GOOGLE = "google"
    LOCAL = "local"


class ModelCapability(str, Enum):
    """Model capabilities."""
    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    EMBEDDING = "embedding"
    IMAGE_ANALYSIS = "image_analysis"
    DOCUMENT_ANALYSIS = "document_analysis"
    REASONING = "reasoning"
    MATH = "math"
    FUNCTION_CALLING = "function_calling"


class ModelConfig(BaseModel):
    """Model configuration."""
    provider: ModelProvider
    model_name: str
    capabilities: List[ModelCapability]
    max_tokens: int
    cost_per_1k_tokens: float
    latency_ms_p50: int
    latency_ms_p95: int
    availability_regions: List[Region]
    data_residency_compliant: bool
    supports_function_calling: bool = False
    context_window: int = 4096
    quality_score: float = 0.8  # 0.0 to 1.0


class RegionConfig(BaseModel):
    """Regional configuration."""
    region: Region
    primary_models: Dict[ModelCapability, ModelConfig]
    fallback_models: Dict[ModelCapability, List[ModelConfig]]
    data_residency_required: bool
    compliance_requirements: List[str]
    latency_requirements_ms: int
    cost_optimization_enabled: bool
    load_balancing_enabled: bool


class ModelSelection(BaseModel):
    """Model selection result."""
    selected_model: ModelConfig
    fallback_models: List[ModelConfig]
    region: Region
    selection_reason: str
    estimated_cost: float
    estimated_latency_ms: int
    compliance_status: str


class RegionRouter:
    """
    Region Router for managing regional AI model deployment and selection.

    Features:
    - Data residency compliance
    - Regional model optimization
    - Cost and latency optimization
    - Automatic failover
    - Load balancing
    - Compliance monitoring
    """

    def __init__(self):
        # Model configurations
        self.model_configs: Dict[str, ModelConfig] = {}
        self.region_configs: Dict[Region, RegionConfig] = {}
        # Tenant region preferences
        self.tenant_region_map: Dict[str, Region] = {}

        # Initialize default configurations
        self._initialize_model_configs()
        self._initialize_region_configs()
        self._initialize_tenant_region_map()

        # Performance tracking
        self.model_performance: Dict[str, Dict[str, Any]] = {}
        self.region_performance: Dict[Region, Dict[str, Any]] = {}

        # Load balancing
        self.model_load: Dict[str, int] = {}

        logger.info("RegionRouter initialized")

    async def get_region_config(
        self,
        tenant_id: Optional[str],
        context: Dict[str, Any]
    ) -> RegionConfig:
        """Get regional configuration for a tenant."""
        # Determine region based on tenant preferences and data residency
        target_region = await self._determine_target_region(tenant_id, context)

        if target_region in self.region_configs:
            return self.region_configs[target_region]
        else:
            # Fall back to US East as default
            logger.warning(f"No config for region {target_region}, using US East")
            return self.region_configs[Region.US_EAST]

    async def select_model(
        self,
        capability: ModelCapability,
        region: Region,
        context: Dict[str, Any],
        requirements: Optional[Dict[str, Any]] = None
    ) -> ModelSelection:
        """Select the best model for a specific capability and region."""
        requirements = requirements or {}

        region_config = self.region_configs.get(region, self.region_configs[Region.US_EAST])

        # Get candidate models
        primary_model = region_config.primary_models.get(capability)
        fallback_models = region_config.fallback_models.get(capability, [])

        if not primary_model:
            logger.error(f"No primary model configured for {capability} in {region}")
            # Try to find any model with this capability
            primary_model = await self._find_fallback_model(capability, region)

        if not primary_model:
            raise ValueError(f"No model available for {capability} in {region}")

        # Check if primary model meets requirements
        selected_model = primary_model
        selection_reason = f"Primary model for {capability} in {region}"

        # Apply selection criteria
        if requirements.get("max_latency_ms"):
            if primary_model.latency_ms_p95 > requirements["max_latency_ms"]:
                # Look for faster fallback
                faster_model = await self._find_faster_model(
                    fallback_models, requirements["max_latency_ms"]
                )
                if faster_model:
                    selected_model = faster_model
                    selection_reason = "Selected for lower latency requirement"

        if requirements.get("max_cost_per_1k_tokens"):
            if primary_model.cost_per_1k_tokens > requirements["max_cost_per_1k_tokens"]:
                # Look for cheaper fallback
                cheaper_model = await self._find_cheaper_model(
                    fallback_models, requirements["max_cost_per_1k_tokens"]
                )
                if cheaper_model:
                    selected_model = cheaper_model
                    selection_reason = "Selected for cost optimization"

        if requirements.get("min_quality_score"):
            if primary_model.quality_score < requirements["min_quality_score"]:
                # Look for higher quality fallback
                better_model = await self._find_better_quality_model(
                    fallback_models, requirements["min_quality_score"]
                )
                if better_model:
                    selected_model = better_model
                    selection_reason = "Selected for higher quality requirement"

        # Load balancing
        if region_config.load_balancing_enabled:
            current_load = self.model_load.get(selected_model.model_name, 0)
            if current_load > 10:  # Threshold for load balancing
                balanced_model = await self._find_load_balanced_model(
                    [selected_model] + fallback_models
                )
                if balanced_model and balanced_model != selected_model:
                    selected_model = balanced_model
                    selection_reason = "Load balanced to less busy model"

        # Estimate cost and latency
        estimated_tokens = context.get("estimated_tokens", 1000)
        estimated_cost = (estimated_tokens / 1000) * selected_model.cost_per_1k_tokens
        estimated_latency = selected_model.latency_ms_p95

        # Check compliance
        compliance_status = "compliant"
        if region_config.data_residency_required and not selected_model.data_residency_compliant:
            compliance_status = "non_compliant_data_residency"
            logger.warning(f"Model {selected_model.model_name} not compliant with data residency requirements")

        # Update load tracking
        self.model_load[selected_model.model_name] = self.model_load.get(selected_model.model_name, 0) + 1

        return ModelSelection(
            selected_model=selected_model,
            fallback_models=fallback_models,
            region=region,
            selection_reason=selection_reason,
            estimated_cost=estimated_cost,
            estimated_latency_ms=estimated_latency,
            compliance_status=compliance_status
        )

    async def update_model_performance(
        self,
        model_name: str,
        actual_latency_ms: int,
        actual_cost: float,
        quality_score: float,
        success: bool
    ):
        """Update model performance metrics."""
        if model_name not in self.model_performance:
            self.model_performance[model_name] = {
                "total_requests": 0,
                "successful_requests": 0,
                "average_latency_ms": 0,
                "average_cost": 0,
                "average_quality": 0,
                "last_updated": datetime.utcnow()
            }

        perf = self.model_performance[model_name]
        perf["total_requests"] += 1

        if success:
            perf["successful_requests"] += 1

        # Update running averages
        total = perf["total_requests"]
        perf["average_latency_ms"] = (
            (perf["average_latency_ms"] * (total - 1) + actual_latency_ms) / total
        )
        perf["average_cost"] = (
            (perf["average_cost"] * (total - 1) + actual_cost) / total
        )
        perf["average_quality"] = (
            (perf["average_quality"] * (total - 1) + quality_score) / total
        )
        perf["last_updated"] = datetime.utcnow()

        # Decrease load counter
        if model_name in self.model_load:
            self.model_load[model_name] = max(0, self.model_load[model_name] - 1)

        logger.debug(f"Updated performance for {model_name}: success={success}, latency={actual_latency_ms}ms")

    async def get_regional_status(self) -> Dict[Region, Dict[str, Any]]:
        """Get status of all regions."""
        status = {}

        for region, config in self.region_configs.items():
            region_perf = self.region_performance.get(region, {})

            model_status = {}
            for capability, model in config.primary_models.items():
                model_perf = self.model_performance.get(model.model_name, {})
                model_status[capability.value] = {
                    "model": model.model_name,
                    "provider": model.provider.value,
                    "current_load": self.model_load.get(model.model_name, 0),
                    "success_rate": (
                        model_perf.get("successful_requests", 0) /
                        max(model_perf.get("total_requests", 1), 1)
                    ),
                    "average_latency_ms": model_perf.get("average_latency_ms", 0),
                    "available": region in model.availability_regions
                }

            status[region] = {
                "region": region.value,
                "data_residency_required": config.data_residency_required,
                "compliance_requirements": config.compliance_requirements,
                "models": model_status,
                "total_requests": region_perf.get("total_requests", 0),
                "average_latency_ms": region_perf.get("average_latency_ms", 0)
            }

        return status

    # Private methods

    def _initialize_model_configs(self):
        """Initialize default model configurations."""
        # OpenAI Models
        self.model_configs["gpt-4"] = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-4",
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.REASONING,
                ModelCapability.FUNCTION_CALLING
            ],
            max_tokens=8192,
            cost_per_1k_tokens=0.03,
            latency_ms_p50=2000,
            latency_ms_p95=5000,
            availability_regions=[Region.US_EAST, Region.US_WEST, Region.EU_WEST],
            data_residency_compliant=False,
            supports_function_calling=True,
            context_window=8192,
            quality_score=0.95
        )

        self.model_configs["gpt-3.5-turbo"] = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-3.5-turbo",
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.FUNCTION_CALLING
            ],
            max_tokens=4096,
            cost_per_1k_tokens=0.002,
            latency_ms_p50=1000,
            latency_ms_p95=2500,
            availability_regions=[Region.US_EAST, Region.US_WEST, Region.EU_WEST],
            data_residency_compliant=False,
            supports_function_calling=True,
            context_window=4096,
            quality_score=0.85
        )

        # Anthropic Models
        self.model_configs["claude-3-opus"] = ModelConfig(
            provider=ModelProvider.ANTHROPIC,
            model_name="claude-3-opus",
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.REASONING,
                ModelCapability.CODE_GENERATION
            ],
            max_tokens=4096,
            cost_per_1k_tokens=0.015,
            latency_ms_p50=1500,
            latency_ms_p95=4000,
            availability_regions=[Region.US_EAST, Region.US_WEST],
            data_residency_compliant=False,
            context_window=200000,
            quality_score=0.92
        )

        # Azure OpenAI (EU compliant)
        self.model_configs["azure-gpt-4"] = ModelConfig(
            provider=ModelProvider.AZURE_OPENAI,
            model_name="azure-gpt-4",
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.REASONING,
                ModelCapability.FUNCTION_CALLING
            ],
            max_tokens=8192,
            cost_per_1k_tokens=0.035,
            latency_ms_p50=2500,
            latency_ms_p95=6000,
            availability_regions=[Region.EU_CENTRAL, Region.EU_WEST],
            data_residency_compliant=True,
            supports_function_calling=True,
            context_window=8192,
            quality_score=0.93
        )

        # Embedding models
        self.model_configs["text-embedding-ada-002"] = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="text-embedding-ada-002",
            capabilities=[ModelCapability.EMBEDDING],
            max_tokens=8191,
            cost_per_1k_tokens=0.0001,
            latency_ms_p50=500,
            latency_ms_p95=1500,
            availability_regions=[Region.US_EAST, Region.US_WEST, Region.EU_WEST],
            data_residency_compliant=False,
            context_window=8191,
            quality_score=0.88
        )

    def _initialize_region_configs(self):
        """Initialize regional configurations."""
        # US East
        self.region_configs[Region.US_EAST] = RegionConfig(
            region=Region.US_EAST,
            primary_models={
                ModelCapability.TEXT_GENERATION: self.model_configs["gpt-4"],
                ModelCapability.REASONING: self.model_configs["gpt-4"],
                ModelCapability.FUNCTION_CALLING: self.model_configs["gpt-4"],
                ModelCapability.EMBEDDING: self.model_configs["text-embedding-ada-002"]
            },
            fallback_models={
                ModelCapability.TEXT_GENERATION: [
                    self.model_configs["gpt-3.5-turbo"],
                    self.model_configs["claude-3-opus"]
                ],
                ModelCapability.REASONING: [
                    self.model_configs["claude-3-opus"],
                    self.model_configs["gpt-3.5-turbo"]
                ]
            },
            data_residency_required=False,
            compliance_requirements=["SOC2", "HIPAA"],
            latency_requirements_ms=5000,
            cost_optimization_enabled=True,
            load_balancing_enabled=True
        )

        # EU Central (GDPR compliant)
        self.region_configs[Region.EU_CENTRAL] = RegionConfig(
            region=Region.EU_CENTRAL,
            primary_models={
                ModelCapability.TEXT_GENERATION: self.model_configs["azure-gpt-4"],
                ModelCapability.REASONING: self.model_configs["azure-gpt-4"],
                ModelCapability.FUNCTION_CALLING: self.model_configs["azure-gpt-4"]
            },
            fallback_models={
                ModelCapability.TEXT_GENERATION: [
                    self.model_configs["gpt-4"]  # Only if data residency not required
                ]
            },
            data_residency_required=True,
            compliance_requirements=["GDPR", "ISO27001"],
            latency_requirements_ms=6000,
            cost_optimization_enabled=False,  # Compliance over cost
            load_balancing_enabled=True
        )

        # US West
        self.region_configs[Region.US_WEST] = RegionConfig(
            region=Region.US_WEST,
            primary_models={
                ModelCapability.TEXT_GENERATION: self.model_configs["gpt-3.5-turbo"],
                ModelCapability.REASONING: self.model_configs["claude-3-opus"],
                ModelCapability.EMBEDDING: self.model_configs["text-embedding-ada-002"]
            },
            fallback_models={
                ModelCapability.TEXT_GENERATION: [
                    self.model_configs["gpt-4"],
                    self.model_configs["claude-3-opus"]
                ]
            },
            data_residency_required=False,
            compliance_requirements=["SOC2"],
            latency_requirements_ms=4000,
            cost_optimization_enabled=True,
            load_balancing_enabled=True
        )

    def _initialize_tenant_region_map(self) -> None:
        """Initialize tenant-specific region preferences."""
        self.tenant_region_map = {
            "tenant_us": Region.US_WEST,
            "tenant_eu": Region.EU_CENTRAL,
        }

    async def _determine_target_region(
        self,
        tenant_id: Optional[str],
        context: Dict[str, Any]
    ) -> Region:
        """Determine target region based on tenant and context."""
        # Check context for explicit region preference
        if "preferred_region" in context:
            try:
                return Region(context["preferred_region"])
            except ValueError:
                logger.warning(f"Invalid region preference: {context['preferred_region']}")

        # Check for data residency requirements
        if context.get("data_residency_required"):
            user_location = context.get("user_location", "US")
            if user_location.startswith("EU"):
                return Region.EU_CENTRAL
            elif user_location.startswith("APAC"):
                return Region.APAC_SOUTHEAST

        # Tenant-specific region preference
        if tenant_id and tenant_id in self.tenant_region_map:
            return self.tenant_region_map[tenant_id]

        # Default to US East
        return Region.US_EAST

    async def _find_fallback_model(
        self,
        capability: ModelCapability,
        region: Region
    ) -> Optional[ModelConfig]:
        """Find any model with the required capability."""
        for model in self.model_configs.values():
            if (capability in model.capabilities and
                region in model.availability_regions):
                return model
        return None

    async def _find_faster_model(
        self,
        candidate_models: List[ModelConfig],
        max_latency_ms: int
    ) -> Optional[ModelConfig]:
        """Find the fastest model under the latency limit."""
        suitable_models = [
            m for m in candidate_models
            if m.latency_ms_p95 <= max_latency_ms
        ]

        if suitable_models:
            return min(suitable_models, key=lambda m: m.latency_ms_p95)
        return None

    async def _find_cheaper_model(
        self,
        candidate_models: List[ModelConfig],
        max_cost_per_1k_tokens: float
    ) -> Optional[ModelConfig]:
        """Find the cheapest model under the cost limit."""
        suitable_models = [
            m for m in candidate_models
            if m.cost_per_1k_tokens <= max_cost_per_1k_tokens
        ]

        if suitable_models:
            return min(suitable_models, key=lambda m: m.cost_per_1k_tokens)
        return None

    async def _find_better_quality_model(
        self,
        candidate_models: List[ModelConfig],
        min_quality_score: float
    ) -> Optional[ModelConfig]:
        """Find the highest quality model above the quality threshold."""
        suitable_models = [
            m for m in candidate_models
            if m.quality_score >= min_quality_score
        ]

        if suitable_models:
            return max(suitable_models, key=lambda m: m.quality_score)
        return None

    async def _find_load_balanced_model(
        self,
        candidate_models: List[ModelConfig]
    ) -> Optional[ModelConfig]:
        """Find the least loaded model."""
        if not candidate_models:
            return None

        # Sort by current load (ascending)
        sorted_models = sorted(
            candidate_models,
            key=lambda m: self.model_load.get(m.model_name, 0)
        )

        return sorted_models[0]

