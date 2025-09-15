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

Last Updated: 2025-09-15
Version: 2.0 - Added comprehensive architectural improvement standards