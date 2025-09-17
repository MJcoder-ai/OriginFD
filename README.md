# OriginFD - Enterprise Energy System Platform

OriginFD is an enterprise-grade platform for solar PV, BESS (Battery Energy Storage Systems), and hybrid energy system design, procurement, construction, and operations management. Built on the ODL-SD v4.1 specification with integrated AI architecture.

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- pnpm 8+
- Docker & Docker Compose
- PostgreSQL 15+ (for production)
- Redis 7+ (for production)

### Local Development Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/MJcoder-ai/OriginFD.git
   cd OriginFD
   ```

2. **Install Python dependencies**

   ```bash
   pip install poetry
   poetry install
   ```

3. **Install Node.js dependencies**

   ```bash
   npm install -g pnpm
   pnpm install
   ```

4. **Start development environment**

   ```bash
   docker-compose up -d postgres redis
   poetry run alembic upgrade head
   docker-compose up
   ```

5. **Access applications**
   - Web UI: http://localhost:3000
   - API Gateway: http://localhost:8000
   - AI Orchestrator: http://localhost:8001
   - API Docs: http://localhost:8000/docs

## Dependency Management

Python dependencies are managed with [Poetry](https://python-poetry.org/).
All packages are declared in `pyproject.toml`, and the legacy
`requirements.txt` file has been removed. Install dependencies with:

```bash
poetry install
```

If a `requirements.txt` file is needed for other tooling, generate one
using:

```bash
poetry export -f requirements.txt --output requirements.txt
```

## Architecture Overview

OriginFD follows a microservices architecture with the following key components:

### Core Services

- **API Gateway** (`services/api/`): FastAPI-based REST API and webhooks
- **AI Orchestrator** (`services/orchestrator/`): L1 AI system with Planner/Router
- **Workers** (`services/workers/`): Background job processing with Celery
- **Web App** (`apps/web/`): Next.js 14 frontend with SSR

### Domain Logic

- **PV** (`domains/pv/`): Solar PV system sizing and design
- **BESS** (`domains/bess/`): Battery storage system design
- **Grid** (`domains/grid/`): Grid integration and compliance
- **Finance** (`domains/finance/`): Financial modeling and analysis
- **Commerce** (`domains/commerce/`): Marketplace and transactions

### Shared Packages

- **Python** (`packages/py/`): Shared Python libraries
- **TypeScript** (`packages/ts/`): Shared frontend components and types

## Development Workflow

### Code Organization

- Follow the canonical folder structure defined in `OriginFD_Canonical Development Guide.md`
- All ODL-SD document mutations use JSON-Patch for auditability
- RBAC and phase gates enforce governance at the API level
- Domain logic is framework-agnostic and purely functional

### Running Tests

```bash
# Python tests
poetry run pytest

# TypeScript tests
pnpm test

# All tests
pnpm run test && poetry run pytest
```

### Code Quality

```bash
# Format code
poetry run black .
poetry run isort .
pnpm run format

# Lint code
poetry run flake8 .
pnpm run lint

# Type checking
poetry run mypy .
pnpm run type-check
```

## Deployment

### Google Cloud Platform

The platform is designed for GCP deployment using:

- **Cloud Run** for services
- **Cloud SQL** (PostgreSQL) for data
- **Memorystore** (Redis) for caching
- **Pub/Sub** for messaging
- **Secret Manager** for secrets
- **Artifact Registry** for images

Deploy using Terraform:

```bash
cd infra/gcp/terraform/envs/dev
terraform init
terraform plan
terraform apply
```

## Key Features

### ODL-SD v4.1 Compliance

- Complete energy system lifecycle management
- JSON Schema validation for all documents
- Hierarchical scaling from residential to utility-scale
- Multi-domain support (PV, BESS, Grid, SCADA)

### AI-Powered Design

- Ground-before-Generate approach with Graph-RAG
- Deterministic tools with typed I/O schemas
- Policy Router for budget enforcement (PSU metering)
- Critic/Verifier gates for quality assurance

### Enterprise Security

- Role-Based Access Control (RBAC)
- Phase gates for approval workflows
- Audit trails for all document changes
- Data residency compliance (US/EU/APAC)

### Component Lifecycle Management (ODL-SD v4.1)

- **19-Stage Lifecycle**: Complete component management from draft to archive
- **Automated Workflows**: RFQ/bidding, purchase order management, inventory tracking
- **Media Asset Management**: Document processing, AI extraction, compliance validation
- **Stakeholder Integration**: Role-based access with 15+ user profiles
- **State Machine Validation**: Controlled transitions with requirements checking

### Marketplace & Commerce

- Component marketplace with supplier management
- RFQ and procurement workflows
- Escrow and payment processing
- Service handover and provider switching

### Tool Registry & SDK

- Tool metadata exposed via `/tools` on the AI Orchestrator
- Run any tool with sample inputs via `POST /tools/{tool_name}/sample`
- Generate client SDK types: `python services/orchestrator/tools/generate_sdk.py`
- Download generated SDKs:
  - TypeScript: http://localhost:8001/tools/sdk/typescript
  - Python: http://localhost:8001/tools/sdk/python

## Component Lifecycle Management

OriginFD implements a comprehensive 19-stage component lifecycle management system compliant with ODL-SD v4.1 specification. This system provides complete traceability from initial component creation through end-of-life disposal.

### Lifecycle Stages Overview

The component lifecycle consists of four major phases with 19 distinct stages:

#### **Planning & Data Processing (Stages 1-5)**

1. **DRAFT** → Initial component record creation and basic data capture
2. **PARSED** → Datasheet parsing and technical specification extraction
3. **ENRICHED** → Data enrichment, classification assignment, and normalization
4. **DEDUPE_PENDING** → Automated duplicate detection and conflict resolution
5. **COMPLIANCE_PENDING** → Regulatory compliance review and certificate validation

#### **Procurement & Ordering (Stages 6-11)**

6. **APPROVED** → Component approved for procurement with quality assurance
7. **AVAILABLE** → Component available for RFQ creation and project assignment
8. **RFQ_OPEN** → Request for Quote published, collecting supplier bids
9. **RFQ_AWARDED** → Supplier selected, preparing purchase order
10. **PURCHASING** → Purchase order processing and approval workflow
11. **ORDERED** → Order confirmed by supplier, production in progress

#### **Logistics & Deployment (Stages 12-15)**

12. **SHIPPED** → Component shipped from supplier, tracking in transit
13. **RECEIVED** → Component received, inspected, and stored in inventory
14. **INSTALLED** → Component physically installed at project location
15. **COMMISSIONED** → Component commissioned, tested, and integrated

#### **Operations & End-of-Life (Stages 16-19)**

16. **OPERATIONAL** → Component in active service, performance monitoring
17. **WARRANTY_ACTIVE** → Component under warranty coverage with active monitoring
18. **RETIRED** → Component end-of-life, decommissioning in progress
19. **ARCHIVED** → Component record archived, lifecycle complete

### Key Workflow Integrations

#### **RFQ/Bidding System**

- Create RFQs for available components with detailed specifications
- Automated bid collection and evaluation with scoring matrix
- Supplier communication and award management
- Integration with component lifecycle progression

```typescript
// Example RFQ Creation
POST /api/bridge/rfq
{
  "component_id": "comp_001",
  "title": "Solar PV Modules for Utility Project",
  "quantity": 250000,
  "evaluation_criteria": {
    "price_weight": 40,
    "delivery_weight": 20,
    "quality_weight": 25,
    "experience_weight": 10,
    "sustainability_weight": 5
  }
}
```

#### **Purchase Order Management**

- Automated PO generation from awarded RFQs
- Multi-level approval workflows (Procurement → Finance → Executive)
- Supplier acknowledgment tracking and milestone management
- Financial integration with budget controls

```typescript
// Example PO Status Update
PATCH /api/bridge/purchase-orders/po_001/status
{
  "new_status": "shipped",
  "updated_by": "user_procurement_001",
  "notes": "Shipment tracking: ABC123456"
}
```

#### **Media Asset Management**

- Document upload with automated processing (OCR, data extraction)
- AI-powered metadata extraction and classification
- Version control with audit trails
- Compliance document validation and expiration tracking

```typescript
// Example Media Asset Upload
POST /api/bridge/media/assets
{
  "component_id": "comp_001",
  "asset_type": "datasheet",
  "file_name": "Component_Datasheet_v2.3.pdf",
  "visibility": "public"
}
```

#### **Lifecycle Transitions**

- State machine validation with transition rules
- Requirement verification before status changes
- Automated notifications to relevant stakeholders
- Audit trail creation for all transitions

```typescript
// Example Lifecycle Transition
POST /api/bridge/components/comp_001/lifecycle
{
  "new_status": "operational",
  "transition_reason": "Commissioning tests completed successfully",
  "updated_by": "user_commissioning_001",
  "metadata": {
    "project_id": "proj_001",
    "installation_location": "Phoenix Solar Farm - Block A"
  }
}
```

### User Profile Integration

The system supports 15+ distinct user profiles with role-based access:

- **Data Entry Specialist**: Component creation and data capture (Stages 1-3)
- **Technical Review Engineer**: Technical validation and compliance (Stages 2-5)
- **Procurement Manager**: Strategic sourcing and supplier management (Stages 6-11)
- **Project Manager**: Component deployment and integration (Stages 14-15)
- **Operations Manager**: System monitoring and maintenance (Stages 16-18)
- **Asset Manager**: End-of-life and disposal management (Stages 18-19)

Each role has customized dashboards, KPIs, and workflow notifications aligned with their lifecycle engagement patterns.

### API Endpoints

#### **Component Management**

- `GET /api/bridge/components` - List components with filtering
- `GET /api/bridge/components/{id}` - Get component details
- `POST /api/bridge/components/{id}/lifecycle` - Update lifecycle status
- `GET /api/bridge/components/stats` - Component statistics

#### **RFQ Management**

- `GET /api/bridge/rfq` - List RFQs with status filtering
- `POST /api/bridge/rfq` - Create new RFQ
- `POST /api/bridge/rfq/{id}/bids` - Submit bid
- `POST /api/bridge/rfq/{id}/evaluate` - Evaluate bids
- `POST /api/bridge/rfq/{id}/award` - Award RFQ

#### **Purchase Order Management**

- `GET /api/bridge/purchase-orders` - List purchase orders
- `POST /api/bridge/purchase-orders` - Create purchase order
- `POST /api/bridge/purchase-orders/{id}/approve` - Approve PO
- `PATCH /api/bridge/purchase-orders/{id}/status` - Update PO status

#### **Media Assets**

- `GET /api/bridge/media/assets` - List media assets
- `POST /api/bridge/media/assets` - Upload new asset
- `GET /api/bridge/media/processing` - Processing job status

### Performance Metrics

- **Data Quality**: >95% accuracy across all lifecycle stages
- **Processing Speed**: <4 hours for standard transitions
- **Compliance Rate**: >99% regulatory compliance validation
- **Automation Level**: 85% of transitions automated with human oversight
- **Stakeholder Satisfaction**: >95% user satisfaction across all profiles

## Documentation

- [Development Plan](DEVELOPMENT_PLAN.md) - Phased development approach
- [Canonical Development Guide](OriginFD_Canonical%20Development%20Guide.md) - Architecture and patterns
- [ODL-SD v4.1 Specification](odl_sd_v41_spec.md) - Document format specification
- [AI Architecture](ODL_SD%20AI%20Architecture_v_1_1.md) - AI system design
- [Component Lifecycle Validation](COMPONENT_LIFECYCLE_VALIDATION.md) - Complete workflow validation
- [User Profile Engagement Analysis](USER_PROFILE_ENGAGEMENT_ANALYSIS.md) - Stakeholder interaction patterns

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes following the coding standards
4. Add tests for new functionality
5. Submit a pull request

## License

Copyright (c) 2025 OriginFD. All rights reserved.

## Support

For support and questions:

- Email: support@originfd.com
- Documentation: https://docs.originfd.com
- Issues: https://github.com/MJcoder-ai/OriginFD/issues
