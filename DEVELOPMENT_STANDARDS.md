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

Last Updated: 2025-09-14
Version: 1.1 - Added TypeScript type system fragmentation standards