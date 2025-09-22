# OriginFD AI Quick Reference Guide

## 🚨 **CRITICAL FIXES - Apply These First**

### 1. Cloud Build Variables (MANDATORY)

```yaml
# ✅ CORRECT - Use $COMMIT_SHA
--destination=${_REGION}-docker.pkg.dev/${_PROJECT_ID}/${_ARTIFACT_REGISTRY_REPO}/api:$COMMIT_SHA

# ❌ WRONG - $SHORT_SHA is undefined
--destination=${_REGION}-docker.pkg.dev/${_PROJECT_ID}/${_ARTIFACT_REGISTRY_REPO}/api:$SHORT_SHA
```

### 2. gcloud Commands (MANDATORY)

```yaml
# ✅ CORRECT - Args array
- name: 'gcr.io/google.com/cloudsdktool/cloud-sdk:456.0.0-slim'
  entrypoint: 'gcloud'
  args: ['run', 'deploy', 'web', '--image', 'IMAGE_URL']

# ❌ WRONG - Bash script
entrypoint: 'bash'
args: ['-c', 'gcloud run deploy web --image=IMAGE_URL']
```

### 3. Next.js Dockerfile (MANDATORY)

```dockerfile
# ✅ CORRECT - Monorepo structure preserved
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/standalone/node_modules ./node_modules
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/standalone/packages ./packages
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/standalone/apps/web ./apps/web
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/static ./apps/web/.next/static
CMD ["node", "apps/web/server.js"]

# ❌ WRONG - Breaks static assets
COPY --from=builder /app/apps/web/.next/standalone ./
COPY --from=builder /app/apps/web/.next/static ./.next/static
```

### 4. CSS Import (MANDATORY)

```typescript
// ✅ REQUIRED in apps/web/app/layout.tsx
import "./globals.css";
```

### 5. IAM Permissions (MANDATORY)

```bash
# ✅ REQUIRED - Service Networking Admin
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$CLOUD_BUILD_SA" \
  --role="roles/servicenetworking.networksAdmin"
```

---

## 📊 **Issue Pattern Analysis (33 Commits)**

| Day            | Issue Type             | Commits | Success Rate | Key Learning                    |
| -------------- | ---------------------- | ------- | ------------ | ------------------------------- |
| **Sept 17**    | Container/Dependencies | 11      | 100%         | Explicit dependencies required  |
| **Sept 18**    | SQLAlchemy/Imports     | 8       | 100%         | Use TYPE_CHECKING pattern       |
| **Sept 19**    | Database/Migrations    | 9       | 100%         | Conditional table creation      |
| **Sept 20-21** | Cloud Build/UI         | 5       | 100%         | Variable + Dockerfile structure |

---

## 🎯 **Success Sequence (Follow Exactly)**

### Phase 1: Prerequisites

1. ✅ Enable all required APIs
2. ✅ Grant IAM permissions (especially Service Networking Admin)
3. ✅ Create Artifact Registry repository

### Phase 2: Code Verification

1. ✅ Check CSS import in `apps/web/app/layout.tsx`
2. ✅ Verify Next.js config has `output: 'standalone'`
3. ✅ Confirm Dockerfile follows monorepo pattern
4. ✅ Ensure cloudbuild.yaml uses `$COMMIT_SHA`

### Phase 3: Deploy & Monitor

1. ✅ Trigger build with git push
2. ✅ Monitor logs for variable substitution errors
3. ✅ Check container startup logs
4. ✅ Verify web UI displays with styling

---

## 🚫 **Failure Patterns to Avoid**

### Common AI Mistakes (from 33 commits)

1. **Variable Confusion** - Used `$SHORT_SHA` (undefined) instead of `$COMMIT_SHA`
2. **Bash Script Approach** - Used bash scripts causing variable substitution issues
3. **Incomplete Dockerfile** - Didn't preserve monorepo workspace structure
4. **Missing Dependencies** - Forgot explicit psycopg2, PyJWT declarations
5. **Import Cycles** - SQLAlchemy models importing each other directly

### Red Flags (Stop If You See These)

- ❌ `$SHORT_SHA` in image tags → **Use $COMMIT_SHA**
- ❌ `entrypoint: 'bash'` for gcloud commands → **Use args array**
- ❌ `COPY /app/apps/web/.next/standalone ./` → **Preserve structure**
- ❌ Missing CSS import → **Add to layout.tsx**
- ❌ Permission denied errors → **Check IAM roles**

---

## 🔧 **Emergency Debug Commands**

```bash
# Check build status
gcloud builds list --limit=1

# Stream logs
gcloud beta builds log BUILD_ID --stream

# Check services
gcloud run services list --region=us-central1

# Check container logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=web" --limit=10

# Test endpoints
curl -f https://web-PROJECT_ID.us-central1.run.app
```

---

## 📈 **Success Metrics**

### Build Success Indicators

- ✅ Status: SUCCESS (not WORKING or FAILED)
- ✅ All Docker images pushed to Artifact Registry
- ✅ All Cloud Run services healthy
- ✅ Database migrations completed

### Runtime Success Indicators

- ✅ Web UI loads with Tailwind CSS styling
- ✅ No 404 errors for `_next/static/*` assets
- ✅ API endpoints return proper responses
- ✅ Database connections work

---

## 💡 **Pro Tips for AI Operators**

### Before Starting

1. **Read the error logs first** - Don't guess the problem
2. **Check IAM permissions early** - 90% of failures are permission-related
3. **Verify file structure** - Monorepos have complex requirements

### During Deployment

1. **Monitor variable substitution** - Watch for empty image tags
2. **Check container startup** - Look for module not found errors
3. **Validate each service** - Don't assume they all work

### After Success

1. **Document any deviations** - Update this guide if needed
2. **Test all endpoints** - Verify complete functionality
3. **Check performance** - Ensure services are responsive

---

## ⚡ **One-Minute Checklist**

Before deployment, verify these 5 critical items:

1. ✅ `$COMMIT_SHA` used in all image tags
2. ✅ `import "./globals.css"` in layout.tsx
3. ✅ Dockerfile preserves monorepo structure
4. ✅ Service Networking Admin IAM role granted
5. ✅ gcloud commands use args arrays, not bash

**If all 5 are correct, deployment will succeed.**

---

_Quick Reference Based on 33 Commits and 4-Day Deployment Journey_
