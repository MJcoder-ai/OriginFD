# OpenAPI Client Generation

This document describes the automated OpenAPI client generation system that prevents API client drift between the FastAPI backend and TypeScript frontend.

## Overview

The system automatically:

1. **Detects API changes** in the backend
2. **Generates TypeScript clients** from OpenAPI schema
3. **Validates compatibility** with existing client usage
4. **Creates alerts** when manual intervention is needed
5. **Ensures consistency** between backend and frontend

## How It Works

### 1. Backend Schema Detection

The FastAPI backend automatically exposes OpenAPI schema at:

- **Schema JSON**: `http://localhost:8000/openapi.json`
- **Interactive Docs**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### 2. Automated Generation

The generation script (`scripts/generate-api-client.js`):

1. Fetches the live OpenAPI schema from the running API
2. Uses `openapi-generator-cli` to generate TypeScript client
3. Analyzes existing client to ensure coverage
4. Creates detailed reports and comparisons

### 3. GitHub Actions Integration

The workflow (`.github/workflows/api-client-sync.yml`) automatically:

- **Triggers** on changes to `services/api/**`
- **Runs weekly** to catch any drift
- **Can be manually triggered** with force regeneration
- **Creates issues** when action is required
- **Comments on PRs** with compatibility analysis

## Usage

### Local Development

```bash
# Generate client locally (requires API server running)
npm run generate:api-client

# Start API and generate client automatically
npm run api:generate-client

# Manual API server management
npm run api:start
# In another terminal:
npm run generate:api-client
```

### CI/CD Integration

The system automatically runs on:

- **Push to main** with API changes
- **Pull requests** affecting the API
- **Weekly schedule** (Mondays at 2 AM UTC)
- **Manual trigger** via GitHub Actions UI

### Generated Output

```
generated/
├── api-client/
│   ├── api/              # Generated API client classes
│   ├── models/           # TypeScript type definitions
│   └── generation-report.json  # Coverage and analysis report
└── temp/
    └── openapi.json      # Downloaded schema (temporary)
```

## Configuration

### Script Configuration

Edit `scripts/generate-api-client.js` to customize:

```javascript
const CONFIG = {
  // API endpoints
  apiUrl: process.env.API_URL || "http://localhost:8000",

  // Output paths
  outputDir: path.join(__dirname, "..", "generated", "api-client"),
  currentClientPath: path.join(
    __dirname,
    "..",
    "packages",
    "ts",
    "http-client",
    "src",
    "index.ts",
  ),

  // Generator settings
  generatorName: "typescript-axios",
  packageName: "@originfd/http-client-generated",
};
```

### Environment Variables

```bash
# API server URL (default: http://localhost:8000)
API_URL=http://localhost:8000

# Database URL for API server
DATABASE_URL=postgresql://user:pass@localhost:5432/originfd

# Environment mode
ENVIRONMENT=development
```

## Integration Workflow

### 1. Developer Adds New API Endpoint

```python
# services/api/api/routers/new_feature.py
@router.post("/new-endpoint")
async def new_endpoint(data: NewRequest) -> NewResponse:
    """New API endpoint"""
    return {"result": "success"}
```

### 2. System Detects Changes

- GitHub Actions triggers on file changes
- Script fetches updated OpenAPI schema
- Generates new TypeScript client

### 3. Analysis and Validation

The system checks:

- **Coverage**: Are all endpoints represented?
- **Compatibility**: Do existing method calls still work?
- **New methods**: What needs to be added to the client?

### 4. Developer Integration

```typescript
// packages/ts/http-client/src/index.ts
export class OriginFDClient {
  // Add new method based on generated client
  async newEndpoint(data: NewRequest): Promise<NewResponse> {
    return this.api.post("new-endpoint", { json: data }).json<NewResponse>();
  }
}
```

## Troubleshooting

### Common Issues

1. **API Server Not Running**

   ```bash
   # Error: API server not accessible
   # Solution: Start the API server
   cd services/api && python main.py
   ```

2. **Database Connection Issues**

   ```bash
   # Error: Database connection failed
   # Solution: Set up test database
   export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/originfd_test
   ```

3. **Generation Failures**
   ```bash
   # Error: Failed to generate client
   # Solution: Check OpenAPI schema validity
   curl http://localhost:8000/openapi.json | jq .
   ```

### Manual Recovery

If automation fails, manually sync the client:

```bash
# 1. Start API server
cd services/api && python main.py &

# 2. Download schema
curl http://localhost:8000/openapi.json > temp/openapi.json

# 3. Generate client manually
npx openapi-generator-cli generate \
  -i temp/openapi.json \
  -g typescript-axios \
  -o generated/api-client

# 4. Compare and update existing client
# Review generated/api-client/api/*.ts files
# Update packages/ts/http-client/src/index.ts accordingly
```

## Best Practices

### 1. API Design

- **Use proper HTTP methods** (GET, POST, PUT, DELETE)
- **Define clear request/response models** with Pydantic
- **Add comprehensive docstrings** for OpenAPI documentation
- **Use consistent naming conventions**

### 2. Client Maintenance

- **Review generated clients** before integrating
- **Add tests** for new API methods
- **Update type definitions** as needed
- **Monitor coverage reports** in CI/CD

### 3. Versioning Strategy

- **Semantic versioning** for API changes
- **Backward compatibility** for minor versions
- **Migration guides** for breaking changes
- **Deprecation notices** before removal

## Monitoring and Alerts

### GitHub Issues

The system automatically creates issues when:

- **Coverage drops below 95%**
- **Missing methods** are detected
- **Generation fails** repeatedly

### PR Comments

On pull requests, the system provides:

- **Coverage analysis** for API changes
- **Impact assessment** on frontend clients
- **Actionable recommendations** for developers

### Weekly Reports

Scheduled runs provide:

- **Drift detection** between deployments
- **Coverage trends** over time
- **Proactive maintenance** alerts

## Future Enhancements

### Planned Features

1. **Automatic PR creation** for client updates
2. **Multiple language support** (Python, Go, etc.)
3. **API versioning** and schema comparison
4. **Performance impact analysis**
5. **Integration with API testing**

### Contributing

To improve the generation system:

1. **Report issues** with specific use cases
2. **Submit PRs** for bug fixes or features
3. **Update documentation** for new patterns
4. **Add test cases** for edge scenarios

---

For questions or support, create an issue with the `api-sync` label.
