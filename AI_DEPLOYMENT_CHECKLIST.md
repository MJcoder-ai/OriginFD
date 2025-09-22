# AI Deployment Checklist for OriginFD

## Quick Reference for AI Operators

### 🚨 CRITICAL ISSUES TO AVOID (Learned from Experience)

#### 1. **IAM Permissions** ⚠️

```bash
# MUST HAVE: Service Networking Admin role
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$CLOUD_BUILD_SA" \
    --role="roles/servicenetworking.networksAdmin"
```

#### 2. **Cloud Build Variables** ⚠️

```yaml
# CORRECT: Use $COMMIT_SHA
--image=us-central1-docker.pkg.dev/project/repo/service:$COMMIT_SHA

# WRONG: $SHORT_SHA is undefined
--image=us-central1-docker.pkg.dev/project/repo/service:$SHORT_SHA
```

#### 3. **Next.js Dockerfile Structure** ⚠️

```dockerfile
# CRITICAL: Monorepo standalone build structure
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/standalone/node_modules ./node_modules
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/standalone/packages ./packages
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/standalone/apps/web ./apps/web
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/static ./apps/web/.next/static
CMD ["node", "apps/web/server.js"]  # NOT just "server.js"
```

#### 4. **CSS Import** ⚠️

```typescript
// apps/web/app/layout.tsx - MUST HAVE THIS LINE
import "./globals.css";
```

#### 5. **gcloud Commands** ⚠️

```yaml
# CORRECT: Proper args structure
- name: 'gcr.io/google.com/cloudsdktool/cloud-sdk:456.0.0-slim'
  entrypoint: 'gcloud'
  args:
    - 'run'
    - 'deploy'
    - 'web'
    - '--image'
    - 'us-central1-docker.pkg.dev/project/repo/web:$COMMIT_SHA'

# WRONG: Bash script (causes variable issues)
entrypoint: 'bash'
args: ['-c', 'gcloud run deploy web --image=...']
```

---

## 🎯 Pre-Flight Checklist

### Before Starting Deployment:

- [ ] **Read DEPLOYMENT_GUIDE.md completely**
- [ ] **Verify project structure matches requirements**
- [ ] **Check all IAM permissions are granted**
- [ ] **Confirm APIs are enabled**
- [ ] **Validate Dockerfile configurations**
- [ ] **Ensure CSS imports exist in layout files**

### During Deployment:

- [ ] **Monitor build logs continuously**
- [ ] **Check for IAM permission errors first**
- [ ] **Verify image tags are not empty**
- [ ] **Watch for container startup failures**
- [ ] **Monitor secret creation and access**

### After Deployment:

- [ ] **Test web UI for proper styling**
- [ ] **Verify all static assets load (no 404s)**
- [ ] **Check API endpoints respond**
- [ ] **Confirm database connectivity**
- [ ] **Validate secret access by services**

---

## 🔧 Quick Debug Commands

```bash
# Check build status
gcloud builds list --limit=1

# Stream build logs
gcloud beta builds log BUILD_ID --stream

# Check service status
gcloud run services list --region=us-central1

# Check container logs for errors
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=web" --limit=10

# Verify secrets exist
gcloud secrets list

# Test service endpoints
curl -f https://web-PROJECT_ID.us-central1.run.app
```

---

## 🚫 Common AI Mistakes

1. **Assuming file paths** - Always verify actual structure
2. **Skipping IAM setup** - Causes 90% of deployment failures
3. **Using wrong Cloud Build variables** - Leads to empty image tags
4. **Incorrect Dockerfile copying** - Breaks static asset serving
5. **Missing CSS imports** - Results in unstyled UI
6. **Using bash scripts** - Causes variable substitution issues

---

## ✅ Success Indicators

- Build completes with status: SUCCESS
- All services show as healthy in Cloud Run
- Web UI loads with full Tailwind CSS styling
- No 404 errors for \_next/static/\* assets
- API endpoints return proper responses
- Database migrations complete successfully

---

## 🆘 Emergency Troubleshooting

### If UI shows only plain text:

1. Check CSS import in layout.tsx
2. Verify Dockerfile COPY commands
3. Check container startup logs
4. Verify static asset paths

### If build fails with permission errors:

1. Check IAM roles on Cloud Build service account
2. Verify Service Networking Admin role
3. Check project-level permissions

### If container won't start:

1. Check server.js path in CMD
2. Verify file structure in container
3. Check environment variables
4. Review health check configuration

---

_Follow this checklist religiously to avoid the 15+ issues we encountered during the original deployment._
