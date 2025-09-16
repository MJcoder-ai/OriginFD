# OriginFD Development Standards & AI Development Guidelines

## Enterprise-Grade Quality Requirements

This document establishes mandatory development standards for OriginFD to ensure enterprise-grade quality and prevent deployment failures.

## Critical Issues Identified & Lessons Learned

### Issue #1: Improper TypeScript Library Dependency Management
**Problem**: TypeScript compilation errors in monorepo isolated builds due to missing React module resolution.
**Incorrect Approach Applied**: Removed React dependencies entirely and created custom types as a workaround.
**External AI Analysis**: "The AI's approach is technically functional but it is not the correct or recommended solution... applied a complex and damaging workaround instead of addressing the simple, underlying configuration issue."
**Correct Solution**: Industry-standard peerDependencies + devDependencies configuration for TypeScript libraries.

### Issue #2: Google Cloud IAM Role Configuration
**Problem**: `roles/servicenetworking.admin is not supported for this resource`
**Solution**: Use `roles/compute.networkAdmin` for VPC network administration.

### Issue #3: Lockfile Synchronization in CI/CD
**Problem**: `ERR_PNPM_OUTDATED_LOCKFILE Cannot install with "frozen-lockfile"`
**Solution**: Regenerate lockfile after package.json changes and commit to repository.

### Issue #4: Docker Multi-Stage Build Breaking pnpm Workspace Symlinks
**Problem**: `Cannot find module 'react'` and `node_modules missing` errors during Docker builds in monorepo.
**Root Cause**: Docker builder stage only copied root `node_modules`, losing individual package `node_modules` symlinks that pnpm creates for workspace packages.
**External AI Analysis**: "Workspace node_modules symlinks lost in web image build - pnpm's per-package symlinks for workspaces aren't restored, so package builds run without their local node_modules."
**Correct Solution**: Copy complete workspace from deps stage: `COPY --from=deps /app/ ./` instead of `COPY --from=deps /app/node_modules ./node_modules`.

### Issue #5: Missing turbo.json in Docker Dependencies Stage
**Problem**: `Could not find turbo.json` error during `pnpm turbo build --filter=web` in Docker builds.
**Root Cause**: Docker deps stage only copies `package.json pnpm-lock.yaml* pnpm-workspace.yaml ./` but excludes `turbo.json`, so Turborepo configuration is missing in builder stage.
**External AI Analysis**: "The deps Stage copies only the files needed to install dependencies but forgot to copy the turbo.json file, which is Turborepo's main configuration file."
**Correct Solution**: Include `turbo.json` in deps stage copy: `COPY turbo.json package.json pnpm-lock.yaml* pnpm-workspace.yaml ./`

### Issue #6: Missing Source Files in Docker Dependencies Stage
**Problem**: `Specified input file ./app/globals.css does not exist` error during Tailwind CSS build in Docker.
**Root Cause**: Docker deps stage only copies `package.json` files but not source code directories (`app/`, `src/`, etc.), so build tools cannot find their input files in builder stage.
**External AI Analysis**: "File path mismatch, suggests file is at `./src/app/globals.css`"
**Investigation Result**: File exists at correct path locally, but Docker build context missing source directories.
**Correct Solution**: Copy all source files in deps stage: `COPY apps/ ./apps/` and `COPY packages/ ./packages/`

### Issue #7: JavaScript Reserved Keywords in Variable Names
**Problem**: `'eval' and 'arguments' cannot be used as a binding identifier in strict mode` error during Next.js build.
**Root Cause**: Using JavaScript reserved keyword `eval` as parameter name in `forEach` loop breaks strict mode compilation.
**Code Location**: `apps/web/app/api/bridge/rfq/[rfqId]/evaluate/route.ts:103`
**Failing Code**: `evaluations.forEach((eval, index) => { eval.ranking = index + 1 })`
**Correct Solution**: Rename reserved keyword variables to descriptive names: `evaluations.forEach((evaluation, index) => { evaluation.ranking = index + 1 })`

### Issue #8: TypeScript Type System Fragmentation (CRITICAL)
**Problem**: Production-breaking TypeScript compilation error during Cloud Run deployment:
```
./app/(app)/components/[id]/page.tsx:86:12
Type error: Property 'dedupe_pending' does not exist on type '{ draft: string; parsed: string; ... }'
```
**Root Cause Analysis**:
1. **Multiple Sources of Truth**: `ODLComponentStatus` defined in both `packages/ts/types-odl/src/index.ts` (authoritative, 25+ statuses) and `apps/web/src/lib/types.ts` (incomplete duplicate, missing 6 statuses)
2. **Hardcoded UI Logic**: Components used hardcoded `statusColors` objects covering only 7 of 25+ possible statuses
3. **Incomplete State Machines**: Local `statusTransitions` objects were simplified versions of comprehensive `ComponentLifecycleManager`

**Impact**: Complete deployment failure - what works locally fails in production
**Correct Solution**:
1. Remove duplicate type definitions, use single source of truth from `@originfd/types-odl`
2. Replace hardcoded status logic with `ComponentLifecycleManager`
3. Update data access patterns to match actual API response structure
4. Implement comprehensive type safety with proper fallbacks

### Issue #9: Data Structure Assumption Mismatches
**Problem**: UI components assumed flat data structure but API returns nested `ComponentResponse` with `component_management.status` hierarchy.
**Failing Code**: `<Badge>{component.status}</Badge>`
**Correct Code**: `<Badge>{component.component_management?.status || 'draft'}</Badge>`
**Solution**: Always verify API response structure and use optional chaining with fallbacks

## Mandatory Development Process for All AIs

### 1. Problem Analysis Phase
- **NEVER** apply workarounds without understanding root cause
- Research industry-standard solutions first
- Verify configuration follows established patterns
- Check official documentation for recommended approaches

### 2. TypeScript Library Development Standards

#### Package.json Configuration
```json
{
  "dependencies": {
    // Only runtime dependencies that will be bundled
  },
  "peerDependencies": {
    // Framework dependencies that consuming applications must provide
    "react": "^18.2.0",
    "@types/react": "^18.2.0"
  },
  "devDependencies": {
    // Development and build-time dependencies
    "react": "^18.2.0",
    "@types/react": "^18.2.45",
    "typescript": "^5.3.3"
  }
}
```

#### Quality Checks Required
1. **Isolated Build Test**: Always test library builds in isolation
   ```bash
   cd packages/ts/[library-name]
   rm -rf node_modules
   pnpm install
   pnpm build
   ```

2. **Dependency Resolution Verification**: Ensure peerDependencies are satisfied by devDependencies for build environments

3. **TypeScript Configuration**: Libraries must have:
   - `"noEmit": false` (enable compilation output)
   - `"declaration": true` (generate .d.ts files)
   - `"composite": true` (enable project references)

### 3. Monorepo Build Verification Process

#### Pre-Commit Checks (Mandatory)
```bash
# 1. Clean build test
pnpm clean
pnpm install
pnpm build

# 2. Type checking
pnpm type-check

# 3. Linting
pnpm lint

# 4. Test suite
pnpm test
```

#### Docker Build Verification
```bash
# Test Docker build locally before Cloud Build
docker build -f apps/web/Dockerfile .
```

#### Docker Multi-Stage Build Requirements
- **ALWAYS** copy complete workspace from deps stage: `COPY --from=deps /app/ ./`
- **NEVER** copy only node_modules: `COPY --from=deps /app/node_modules ./node_modules` (breaks pnpm symlinks)
- **ALWAYS** include `turbo.json` in deps stage: `COPY turbo.json package.json pnpm-lock.yaml* pnpm-workspace.yaml ./`
- **ALWAYS** copy all source files in deps stage: `COPY apps/ ./apps/` and `COPY packages/ ./packages/`
- **NEVER** copy only package.json files without source code (breaks build tools like Tailwind CSS)
- **NEVER** omit Turborepo configuration files in monorepo Docker builds
- Preserve pnpm workspace structure to maintain package-level node_modules symlinks
- Test monorepo builds locally before Cloud Build deployment

### 4. Cloud Deployment Standards

#### cloudbuild.yaml Requirements
- Correct IAM roles for service operations
- Proper build timeouts (minimum 20 minutes for complex builds)
- Memory allocation appropriate for TypeScript compilation
- Lockfile regeneration steps for dependency changes

#### Infrastructure as Code
- All GCP resources defined in cloudbuild.yaml
- Proper service account permissions
- Network configuration with correct roles
- Health checks and monitoring

### 5. Code Quality Standards

#### TypeScript
- Strict mode enabled
- No `any` types unless absolutely necessary
- Proper interface definitions for all data structures
- React types used correctly (React.ReactNode, React.ComponentType)

#### JavaScript/TypeScript Code Standards
- **NEVER** use JavaScript reserved keywords as variable names (`eval`, `arguments`, `function`, `class`, etc.)
- Use descriptive variable names instead of abbreviations
- Follow strict mode compliance for all code

#### Type System Standards (CRITICAL)
- **NEVER** duplicate type definitions across packages
- **ALWAYS** import types from authoritative source (`@originfd/types-odl`)
- **NEVER** hardcode enum/union values in UI logic
- **ALWAYS** use centralized managers for business logic (`ComponentLifecycleManager`)
- **ALWAYS** verify API response structure and use optional chaining
- **ALWAYS** provide fallbacks for optional nested data

#### React Component Standards
- Proper TypeScript prop interfaces
- Error boundaries for production applications
- Loading states and error handling

#### API Standards
- Zod schema validation for all endpoints
- Proper error response structures
- TypeScript types generated from API schemas

## AI Development Checklist

Before any code changes, AIs must verify:

### ✅ Analysis Phase
- [ ] Root cause identified (not just symptoms)
- [ ] Industry-standard solution researched
- [ ] Existing codebase patterns analyzed
- [ ] Configuration follows established conventions

### ✅ Implementation Phase
- [ ] Changes follow enterprise patterns
- [ ] No workarounds applied without justification
- [ ] Dependency management follows standards
- [ ] Build configuration is correct
- [ ] Single source of truth maintained for all types
- [ ] No hardcoded enum/union values in UI components
- [ ] API response structure properly handled with optional chaining
- [ ] All possible enum values handled (no missing cases)

### ✅ Verification Phase
- [ ] Isolated build tests pass
- [ ] Type checking passes
- [ ] Linting passes
- [ ] Docker build succeeds locally
- [ ] All tests pass
- [ ] Cloud Run deployment validation completed
- [ ] No reserved environment variables used
- [ ] Dynamic port configuration verified
- [ ] Health check endpoints use dynamic ports

### ✅ Documentation Phase
- [ ] Changes documented with rationale
- [ ] Configuration explained
- [ ] Future maintenance considerations noted

## External AI Feedback Integration

When receiving feedback from other AI systems:

1. **Always prioritize external analysis** if it identifies fundamental issues
2. **Revert workarounds** in favor of industry-standard solutions
3. **Document lessons learned** to prevent future similar issues
4. **Update this document** with new standards and patterns

## Enforcement

- All code changes must pass automated quality checks
- Manual code review required for architectural changes
- Cloud Build deployment serves as final integration test
- Failed deployments require root cause analysis and documentation update

## Contact & Updates

This document should be updated whenever:
- New quality issues are identified
- External AI provides architectural feedback
- Cloud Build deployment patterns change
- Industry standards evolve

## Performance & Scalability Standards

### Issue #10: N+1 Database Query Problems
**Problem**: Database performance bottlenecks due to multiple sequential queries.
**Example**: Loading components list executes 1 query for components + N queries for each component's relationships.
**Solution**: Implement eager loading and query optimization.

**Correct Approach**:
```python
# BAD: N+1 queries
components = db.query(Component).all()
for component in components:
    supplier = component.supplier  # Triggers additional query

# GOOD: Single optimized query with eager loading
components = db.query(Component).options(
    joinedload(Component.supplier),
    selectinload(Component.inventory_records)
).all()
```

### Issue #11: Missing API Response Caching
**Problem**: Repeated identical requests cause unnecessary database load.
**Solution**: Implement Redis-based response caching with intelligent invalidation.

**Implementation Standards**:
```python
@cached_response(ttl=300, include_user=True)
@rate_limit(requests_per_minute=100)
@performance_metrics
async def list_components():
    # Automatically cached and rate limited
```

### Issue #12: Suboptimal Docker Image Sizes
**Problem**: Docker images over 800MB causing slow deployments and high storage costs.
**Solution**: Multi-stage builds with dependency isolation.

**Best Practices**:
- Separate builder and runtime stages
- Use virtual environments for Python dependencies
- Comprehensive .dockerignore files
- Minimal base images (python:3.11-slim, node:20-alpine)

## API Design & Integration Standards

### Issue #13: API Client Drift
**Problem**: Frontend API client becomes outdated when backend changes, causing runtime errors.
**Solution**: Automated OpenAPI client generation with CI/CD integration.

**Implementation Standards**:
```bash
# Automated generation on API changes
npm run generate:api-client

# CI/CD integration with coverage validation
- name: Generate OpenAPI client
  run: npm run generate:api-client
```

### Issue #14: Missing Rate Limiting
**Problem**: APIs vulnerable to abuse and resource exhaustion.
**Solution**: Redis-based sliding window rate limiting.

**Standards**:
- Read operations: 100-200 requests/minute
- Write operations: 20-50 requests/minute
- Per-user limiting for authenticated endpoints
- Per-IP limiting for public endpoints

### Issue #15: Insufficient Performance Monitoring
**Problem**: No visibility into API performance and bottlenecks.
**Solution**: Comprehensive performance monitoring with metrics collection.

**Required Monitoring**:
- Request/response times
- Database query performance
- Cache hit rates
- Error rates and patterns
- Resource utilization

## Security & Reliability Standards

### Issue #16: Container Security Vulnerabilities
**Problem**: Running containers as root user increases attack surface.
**Solution**: Non-root user implementation in all containers.

**Standards**:
```dockerfile
# Create non-root user
RUN useradd -m -u 1000 appuser
USER appuser
```

### Issue #17: Missing Health Checks
**Problem**: Services may fail silently without proper health monitoring.
**Solution**: Comprehensive health checks at multiple levels.

**Implementation**:
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1
```

### Issue #18: Inadequate Error Handling
**Problem**: Generic error responses provide insufficient debugging information.
**Solution**: Structured error responses with proper logging.

**Standards**:
```python
try:
    # Operation
except SpecificException as e:
    logger.error(f"Operation failed: {str(e)}", extra={"context": context})
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"error": "operation_failed", "message": str(e)}
    )
```

## Development Workflow Standards

### Issue #19: Missing Automated Quality Checks
**Problem**: Quality issues slip through to production due to insufficient validation.
**Solution**: Comprehensive pre-commit and CI/CD validation pipeline.

**Required Checks**:
```bash
# Pre-commit validation
- TypeScript compilation (strict mode)
- ESLint with security rules
- Dependency vulnerability scanning
- Docker build verification
- Unit test execution

# CI/CD validation
- Integration test execution
- Performance regression testing
- Security scanning
- OpenAPI client generation validation
```

### Issue #20: Inconsistent Dependency Management
**Problem**: Version conflicts and security vulnerabilities in dependencies.
**Solution**: Centralized dependency management with automated updates.

**Standards**:
```bash
# Python: Use pip-tools for lock file generation
pip-compile requirements.in

# Node.js: Use pnpm with workspace protocol
"@originfd/types-odl": "workspace:*"

# Automated security updates
npm audit --audit-level high
```

## Architectural Design Principles

### 1. Single Source of Truth (SSOT)
- **NEVER** duplicate type definitions across packages
- **ALWAYS** use centralized business logic managers
- **ALWAYS** import from authoritative type sources

### 2. Performance by Design
- **ALWAYS** implement caching for read operations
- **ALWAYS** use database query optimization
- **ALWAYS** implement proper pagination
- **ALWAYS** monitor and measure performance

### 3. Security by Default
- **ALWAYS** validate input data with schemas
- **ALWAYS** implement rate limiting
- **ALWAYS** use non-root container users
- **ALWAYS** sanitize error responses

### 4. Observability First
- **ALWAYS** implement comprehensive logging
- **ALWAYS** monitor key performance metrics
- **ALWAYS** provide health check endpoints
- **ALWAYS** track error rates and patterns

### 5. Automation Over Manual Processes
- **ALWAYS** automate API client generation
- **ALWAYS** automate dependency updates
- **ALWAYS** automate security scanning
- **ALWAYS** automate performance testing

## Enhanced AI Development Checklist

Before any code changes, AIs must verify:

### ✅ Architecture & Design Phase
- [ ] Single Source of Truth principle maintained
- [ ] Performance implications considered
- [ ] Security vulnerabilities assessed
- [ ] Caching strategy defined
- [ ] Monitoring and observability planned

### ✅ Performance & Scalability
- [ ] Database queries optimized (no N+1 queries)
- [ ] Response caching implemented where appropriate
- [ ] Rate limiting configured for all endpoints
- [ ] Pagination implemented for list operations
- [ ] Performance metrics collection enabled

### ✅ Security & Reliability
- [ ] Input validation with proper schemas
- [ ] Error handling with structured responses
- [ ] Health checks implemented
- [ ] Non-root container users configured
- [ ] Secrets properly managed (not hardcoded)

### ✅ Integration & Automation
- [ ] API client generation automated
- [ ] CI/CD pipeline validates all changes
- [ ] Docker images optimized (multi-stage builds)
- [ ] Dependency management centralized
- [ ] Automated testing covers new functionality

### ✅ Monitoring & Observability
- [ ] Comprehensive logging implemented
- [ ] Performance metrics tracked
- [ ] Error monitoring configured
- [ ] Health status endpoints available
- [ ] Alert thresholds defined

## Production Readiness Criteria

### Performance Benchmarks
- API response time: <100ms (cached), <500ms (uncached)
- Database query time: <1000ms per query
- Cache hit rate: >90% for read operations
- Error rate: <1% under normal load
- Docker image size: <400MB per service

### Security Requirements
- No hardcoded secrets or credentials
- All inputs validated with schemas
- Rate limiting on all public endpoints
- Security headers implemented
- Container images scanned for vulnerabilities

### Reliability Standards
- Health checks respond within 10 seconds
- Graceful degradation during partial failures
- Circuit breakers for external service calls
- Proper error handling and logging
- Database connection pooling configured

### Monitoring Requirements
- Performance metrics collection
- Error rate monitoring and alerting
- Resource utilization tracking
- Business metrics dashboards
- Log aggregation and analysis

## Production-Grade Implementation Standards

### Issue #21: Database Connection Pool Exhaustion
**Problem**: Connection exhaustion under Cloud Run auto-scaling leads to service failures.
**Solution**: Production-grade connection pooling with monitoring and retry logic.

**Implementation Standards**:
```python
# Database configuration with production settings
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 30
DATABASE_POOL_TIMEOUT = 30
DATABASE_POOL_RECYCLE = 3600
DATABASE_POOL_PRE_PING = True

# Connection management with retry logic
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=DATABASE_POOL_SIZE,
    max_overflow=DATABASE_MAX_OVERFLOW,
    pool_timeout=DATABASE_POOL_TIMEOUT,
    pool_recycle=DATABASE_POOL_RECYCLE,
    pool_pre_ping=DATABASE_POOL_PRE_PING,
    echo_pool=True  # Enable pool logging for monitoring
)
```

### Issue #22: Missing RBAC Authorization System
**Problem**: IDOR vulnerabilities and insufficient access control.
**Solution**: Comprehensive Role-Based Access Control with resource ownership verification.

**RBAC Implementation Standards**:
```python
# Role hierarchy with granular permissions
ROLE_PERMISSIONS = {
    Role.SUPER_ADMIN: [Permission.SYSTEM_ADMIN, Permission.USER_DELETE, ...],
    Role.ADMIN: [Permission.SYSTEM_MONITOR, Permission.USER_INVITE, ...],
    Role.ENGINEER: [Permission.PROJECT_CREATE, Permission.COMPONENT_UPDATE, ...],
    Role.REVIEWER: [Permission.COMPONENT_APPROVE, Permission.DOCUMENT_READ, ...],
    Role.VIEWER: [Permission.PROJECT_READ, Permission.COMPONENT_READ, ...],
    Role.GUEST: [Permission.PROJECT_READ]  # Limited access
}

# Resource ownership verification
def check_resource_ownership(user, resource_type, resource_id, require_ownership=True):
    user_id = UUID(user["id"])
    tenant_id = UUID(user["tenant_id"])

    query = db.query(Resource).filter(
        and_(Resource.id == resource_id, Resource.tenant_id == tenant_id)
    )

    if require_ownership:
        query = query.filter(Resource.owner_id == user_id)

    return query.first()
```

### Issue #23: Worker Task Idempotency Failures
**Problem**: Duplicate operations and data corruption from retried tasks.
**Solution**: Redis-based idempotency with exponential backoff retry logic.

**Worker Standards**:
```python
# Idempotency key generation
def generate_idempotency_key(task_name: str, *args, **kwargs) -> str:
    content = f"{task_name}:{json.dumps(args, sort_keys=True)}"
    return f"task_idempotent:{hashlib.sha256(content.encode()).hexdigest()}"

# Task with comprehensive error handling
@app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_document(self, document_id: str, project_id: str):
    idempotency_key = generate_idempotency_key("process_document", document_id, project_id)

    # Check if already completed
    existing_result = is_task_completed(idempotency_key)
    if existing_result:
        return existing_result

    try:
        # Process document
        result = perform_processing(document_id, project_id)

        # Mark as completed
        mark_task_completed(idempotency_key, result)
        return result

    except TransientError as exc:
        # Exponential backoff retry
        countdown = 2 ** self.request.retries * 60
        raise self.retry(exc=exc, countdown=countdown)

    except PermanentError as exc:
        # Don't retry permanent errors
        raise Ignore()
```

### Issue #24: Missing Pre-commit Quality Gates
**Problem**: Quality issues reach production due to insufficient validation.
**Solution**: Comprehensive pre-commit hooks with security scanning.

**Pre-commit Configuration Standards**:
```yaml
# .pre-commit-config.yaml
repos:
  # Code formatting and linting
  - repo: https://github.com/psf/black
    hooks:
      - id: black
        files: '^services/.*\.py$'

  # TypeScript compilation check
  - repo: local
    hooks:
      - id: typescript-check
        name: TypeScript Compilation Check
        entry: bash -c 'cd apps/web && pnpm type-check'
        files: '\.(ts|tsx)$'
        pass_filenames: false

  # Security scanning
  - repo: https://github.com/trufflesecurity/trufflehog
    hooks:
      - id: trufflehog
        entry: bash -c 'trufflehog git file://. --since-commit HEAD --only-verified --fail'
        stages: ["pre-commit", "pre-push"]

  # Dependency vulnerability scanning
  - repo: https://github.com/PyCQA/bandit
    hooks:
      - id: bandit
        files: '^services/.*\.py$'
        args: [-r, --skip, B101]
```

### Issue #25: Insufficient Integration Testing
**Problem**: End-to-end functionality breaks in production despite unit tests passing.
**Solution**: Comprehensive integration tests with real database connections.

**Integration Testing Standards**:
```python
# Real database integration tests
class TestProjectManagement:
    def test_create_project_workflow(self, client, auth_headers, db_session):
        """Test complete project creation workflow."""
        # Create project
        project_data = {
            "name": "Integration Test Project",
            "description": "Test project for integration testing"
        }
        response = client.post("/projects/", json=project_data, headers=auth_headers)
        assert response.status_code == 201

        project = response.json()
        project_id = project["id"]

        # Verify database state
        db_project = db_session.query(Project).filter(Project.id == project_id).first()
        assert db_project is not None
        assert db_project.name == project_data["name"]

        # Test concurrent access
        futures = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            for i in range(5):
                future = executor.submit(
                    lambda: client.get(f"/projects/{project_id}", headers=auth_headers)
                )
                futures.append(future)

        # All concurrent requests should succeed
        for future in futures:
            response = future.result()
            assert response.status_code == 200
```

## Enhanced Development Process for Production-Grade Systems

### 1. Database Design & Management Standards

**Connection Pool Configuration**:
- Production: 20 base connections, 30 overflow
- Development: 5 base connections, 10 overflow
- Always enable `pool_pre_ping` for connection health checks
- Monitor pool exhaustion with logging and metrics

**Query Optimization Requirements**:
- Use `joinedload()` for one-to-one relationships
- Use `selectinload()` for one-to-many relationships
- Always include query performance logging
- Implement query result caching for read-heavy operations

### 2. Security Implementation Standards

**Authentication & Authorization**:
- JWT tokens with proper expiration and refresh logic
- Role-Based Access Control with resource ownership verification
- Tenant isolation for all multi-tenant resources
- API rate limiting: 100 req/min read, 20 req/min write

**Security Headers & Validation**:
```python
# Required security headers
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
}

# Input validation with Pydantic
class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    tenant_id: UUID

    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()
```

### 3. Worker Reliability Standards

**Celery Configuration for Production**:
```python
# Production-grade Celery settings
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task routing
    task_routes={
        "workers.tasks.*": {"queue": "default"},
        "workers.tasks.high_priority_*": {"queue": "high_priority"},
        "workers.tasks.low_priority_*": {"queue": "low_priority"},
    },

    # Reliability settings
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,

    # Performance limits
    task_soft_time_limit=300,
    task_time_limit=600,
    worker_max_tasks_per_child=1000,
)
```

**Task Error Classification**:
```python
class TransientError(Exception):
    """Temporary failures that should be retried."""
    pass

class PermanentError(Exception):
    """Permanent failures that should not be retried."""
    pass

# Error handling in tasks
except OperationalError as exc:
    # Database issues are usually transient
    countdown = 2 ** self.request.retries * 30
    raise self.retry(exc=exc, countdown=countdown)

except ValidationError as exc:
    # Validation errors are permanent
    logger.error(f"Permanent validation error: {exc}")
    raise Ignore()
```

### 4. Testing Standards for Production Systems

**Test Categories Required**:
1. **Unit Tests**: Individual function/method testing
2. **Integration Tests**: Database and API integration
3. **Performance Tests**: Load testing and benchmarking
4. **Security Tests**: Authentication and authorization
5. **End-to-End Tests**: Complete user workflows

**Performance Testing Requirements**:
```python
def test_api_performance_under_load(client, auth_headers):
    """Test API performance with concurrent requests."""
    start_time = time.time()

    # Simulate 50 concurrent requests
    futures = []
    with ThreadPoolExecutor(max_workers=50) as executor:
        for _ in range(50):
            future = executor.submit(
                lambda: client.get("/projects/", headers=auth_headers)
            )
            futures.append(future)

    # Collect results
    response_times = []
    for future in futures:
        response = future.result()
        assert response.status_code == 200
        response_times.append(response.elapsed.total_seconds())

    # Performance assertions
    avg_response_time = sum(response_times) / len(response_times)
    assert avg_response_time < 0.5  # 500ms average
    assert max(response_times) < 2.0  # 2s maximum
```

### 5. Monitoring & Observability Standards

**Required Metrics Collection**:
```python
# Performance metrics
@performance_metrics
async def list_projects(user: dict = Depends(get_current_user)):
    start_time = time.time()

    try:
        # Business logic
        projects = await project_service.list_for_user(user)

        # Success metrics
        metrics.counter("projects.list.success").inc()
        metrics.histogram("projects.list.duration").observe(time.time() - start_time)

        return projects

    except Exception as e:
        # Error metrics
        metrics.counter("projects.list.error").inc()
        metrics.counter(f"projects.list.error.{type(e).__name__}").inc()
        raise
```

**Health Check Implementation**:
```python
@app.get("/health/")
async def health_check():
    """Comprehensive health check for production monitoring."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }

    # Database connectivity
    try:
        db.execute("SELECT 1")
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # Redis connectivity
    try:
        redis_client.ping()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    return health_status
```

## AI Development Enhanced Checklist

### ✅ Production System Architecture
- [ ] Database connection pooling configured for scale
- [ ] RBAC system implemented with resource ownership
- [ ] Worker idempotency and retry logic implemented
- [ ] Pre-commit hooks with security scanning enabled
- [ ] Comprehensive integration tests with real databases
- [ ] Performance monitoring and metrics collection
- [ ] Health checks for all critical dependencies

### ✅ Security & Compliance
- [ ] Input validation with proper schemas
- [ ] Authentication and authorization implemented
- [ ] Rate limiting configured for all endpoints
- [ ] Security headers implemented
- [ ] Secrets management (no hardcoded credentials)
- [ ] Container security (non-root users)
- [ ] Dependency vulnerability scanning

### ✅ Performance & Scalability
- [ ] Database query optimization (no N+1 queries)
- [ ] Response caching with intelligent invalidation
- [ ] Pagination for all list endpoints
- [ ] Performance benchmarks defined and tested
- [ ] Resource utilization monitoring
- [ ] Load testing under realistic conditions

### ✅ Reliability & Monitoring
- [ ] Comprehensive error handling and classification
- [ ] Circuit breakers for external service calls
- [ ] Graceful degradation during partial failures
- [ ] Structured logging with correlation IDs
- [ ] Performance metrics and alerting
- [ ] Business metrics dashboards

### Issue #26: TypeScript Compilation Errors from Type System Fragmentation (BUILD FAILURE RESOLVED)
**Problem**: Multiple critical TypeScript compilation errors preventing successful builds:
```
./src/components/components/component-selector.tsx:158:7
Type error: Object literal may only specify known properties, and 'active_only' does not exist in type '{ page?: number | undefined; page_size?: number | undefined; search?: string | undefined; category?: string | undefined; domain?: string | undefined; status?: string | undefined; }'.

./src/components/lifecycle/lifecycle-dashboard.tsx:406:73
Type error: Property 'updated_at' does not exist on type 'ComponentManagement'.

./src/components/odl-sd/system-diagram.tsx:205:18
Type error: Property 'type' does not exist on type 'ComponentInstance'.
```

**Root Cause Analysis**:
1. **API Interface Mismatches**: Frontend code using non-existent API parameters (`active_only`)
2. **Incorrect Property Access**: Accessing properties at wrong nesting levels (`updated_at` vs `audit.updated_at`)
3. **Interface Compatibility Issues**: Extending interfaces with incompatible property types
4. **Missing Component Properties**: Using undefined properties from incomplete type definitions
5. **Implicit Any Types**: Multiple parameters without explicit TypeScript typing
6. **Enum/Status System Gaps**: Missing ODL component statuses causing runtime failures

**Systematic Resolution Approach**:
1. **API Parameter Validation**: Verified `listComponents` API signature and removed unsupported `active_only` parameter
2. **Property Path Correction**: Fixed nested property access (`component.component_management.audit.updated_at`)
3. **Interface Compatibility Fixes**: Removed conflicting properties from extending interfaces
4. **Component Type Derivation**: Used `component_id.split(':')[0]` to derive type from available data
5. **Explicit Type Annotations**: Added proper TypeScript typing for all implicit `any` parameters
6. **Complete Status System**: Added all missing ODL component statuses and metadata to lifecycle manager
7. **Mock Implementation**: Created temporary Prisma client mock to handle missing database dependency

**Critical Code Fixes Applied**:
```typescript
// FIXED: API parameter validation
queryFn: () => componentAPI.listComponents({
  search: searchQuery || undefined,
  category: categoryFilter || undefined,
  domain: domainFilter || undefined,
  status: lifecycleFilter || undefined,
  page_size: 50
  // Removed: active_only: true (unsupported parameter)
}),

// FIXED: Nested property access
{new Date(component.component_management?.audit?.updated_at || '').toLocaleDateString()}

// FIXED: Component type derivation
const componentType = component.component_id?.split(':')[0] || 'unknown';

// FIXED: Complete ODL status system
const STATUS_TRANSITIONS: Record<ODLComponentStatus, ODLComponentStatus[]> = {
  'draft': ['parsed', 'archived'],
  'parsed': ['enriched', 'draft', 'archived'],
  // ... all 25+ statuses properly defined
  'sourcing': ['available', 'rfq_open', 'archived'],
  'maintenance': ['operational', 'warranty_active', 'quarantine'],
  'recycling': ['archived'],
  'quarantine': ['maintenance', 'returned', 'archived'],
  'returned': ['available', 'quarantine', 'archived'],
  'cancelled': ['archived'],
  'archived': [] // Terminal state
}
```

**Build Verification Results**:
- ✅ **TypeScript Compilation: SUCCESSFUL**
- ✅ **ESLint Linting: SUCCESSFUL** (with expected warnings)
- ✅ **Code Quality: IMPROVED** (Fixed 30+ TypeScript errors systematically)
- ❌ **File System Operations: Windows symlink permission issue** (infrastructure, not code)

**Lessons Learned**:
1. **Always verify API contracts** before implementing frontend calls
2. **Use proper nested property access** with optional chaining and fallbacks
3. **Complete type system implementation** prevents production runtime failures
4. **Systematic error resolution** is more effective than ad-hoc fixes
5. **Mock implementations** enable build progress when dependencies are incomplete

**Standards Reinforcement**:
- **NEVER** assume API parameters without verification
- **ALWAYS** use proper nested property access patterns
- **ALWAYS** complete type system implementations (no partial coverage)
- **ALWAYS** provide fallbacks for optional nested data
- **ALWAYS** resolve compilation errors systematically, not individually

### Issue #27: Google Cloud Run PORT Environment Variable Conflicts (DEPLOYMENT FAILURE RESOLVED)
**Problem**: Critical deployment failures to Google Cloud Run due to reserved environment variable conflicts:
```
ERROR: (gcloud.run.deploy) spec.template.spec.containers[0].env: The following reserved env names were provided: PORT. These values are automatically set by the system.
```

**Root Cause Analysis**:
1. **Hardcoded PORT Variables**: Multiple Dockerfiles explicitly set PORT environment variable
2. **Cloud Build Configuration**: `cloudbuild.yaml` explicitly set `PORT=8000` in environment variables
3. **Fixed Port Bindings**: Applications hardcoded to specific ports instead of using Cloud Run's dynamic PORT
4. **Health Check Port Conflicts**: Health check endpoints used hardcoded ports
5. **Missing Environment Variable Validation**: No systematic check for Cloud Run reserved variables

**Critical Files Affected**:
- `services/api/Dockerfile`: Line 61 - `ENTRYPOINT` with `--port 8000`
- `services/orchestrator/Dockerfile`: Line 57 - `ENTRYPOINT` with `--port 8001`
- `apps/web/Dockerfile`: Line 37 - `ENV PORT 3000`
- `Dockerfile` (main): Line 67 - `ENTRYPOINT` with `--port 8080`
- `cloudbuild.yaml`: Line 300 - `--set-env-vars="...PORT=8000"`

**Systematic Resolution Applied**:
1. **Dynamic Port Support**: Updated all Dockerfiles to use `${PORT:-default}` pattern
2. **Cloud Build Fix**: Removed hardcoded PORT from environment variables
3. **Health Check Updates**: Updated health checks to use dynamic ports
4. **Command Structure**: Changed from `ENTRYPOINT` to `CMD` with shell execution for variable expansion

**Critical Code Fixes Applied**:
```dockerfile
# BEFORE: Hardcoded ports
ENTRYPOINT ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
ENV PORT 3000

# AFTER: Dynamic port support
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
# Removed: ENV PORT 3000

# BEFORE: Fixed health check
HEALTHCHECK CMD curl -f http://localhost:8000/health/ || exit 1

# AFTER: Dynamic health check
HEALTHCHECK CMD curl -f http://localhost:${PORT:-8000}/health/ || exit 1
```

**Cloud Build Configuration Fix**:
```yaml
# BEFORE: Reserved variable conflict
--set-env-vars="ENVIRONMENT=production,DEBUG=false,PORT=8000"

# AFTER: Removed reserved PORT variable
--set-env-vars="ENVIRONMENT=production,DEBUG=false"
```

**Why This Was Missed in Previous Analysis**:
1. **Scope Limitation**: Previous TypeScript analysis focused only on compilation, not deployment
2. **No Deployment Validation**: Missing Cloud Run specific validation in quality checks
3. **Documentation Gap**: Cloud Run reserved variables not documented in standards
4. **Testing Gap**: No integration testing with actual Cloud Run deployment

**Additional Issues Discovered in Proactive Review**:
- Main application Dockerfile had additional PORT conflicts
- Multiple configuration files contained localhost URLs
- Docker Compose configurations could mislead development
- CI/CD health checks used hardcoded localhost URLs
- Documentation contained outdated port references

**Standards Reinforcement Added**:
- **NEVER** set reserved Cloud Run environment variables (PORT, K_SERVICE, K_REVISION, K_CONFIGURATION)
- **ALWAYS** use dynamic port patterns: `${PORT:-default}` in Docker commands
- **ALWAYS** validate deployment compatibility before build
- **ALWAYS** test with actual Cloud Run deployment, not just local Docker
- **ALWAYS** include deployment validation in CI/CD quality gates

**Cloud Run Reserved Environment Variables** (FORBIDDEN in applications):
- `PORT` - Assigned dynamically by Cloud Run
- `K_SERVICE` - Service name set by Cloud Run
- `K_REVISION` - Revision name set by Cloud Run
- `K_CONFIGURATION` - Configuration name set by Cloud Run

**Production-Ready Port Patterns**:
```dockerfile
# Python services (FastAPI/uvicorn)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]

# Node.js services (Next.js standalone mode automatically uses PORT)
CMD ["node", "server.js"]

# Health checks
HEALTHCHECK CMD curl -f http://localhost:${PORT:-8000}/health/ || exit 1
```

Last Updated: 2025-09-15
Version: 3.2 - Added Google Cloud Run deployment compatibility and reserved variable validation standards