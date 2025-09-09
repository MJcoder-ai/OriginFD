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

### Marketplace & Commerce
- Component marketplace with supplier management
- RFQ and procurement workflows
- Escrow and payment processing
- Service handover and provider switching

## Documentation

- [Development Plan](DEVELOPMENT_PLAN.md) - Phased development approach
- [Canonical Development Guide](OriginFD_Canonical%20Development%20Guide.md) - Architecture and patterns
- [ODL-SD v4.1 Specification](odl_sd_v41_spec.md) - Document format specification  
- [AI Architecture](ODL_SD%20AI%20Architecture_v_1_1.md) - AI system design

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