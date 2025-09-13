# OriginFD Cloud Deployment Guide

This guide walks through deploying OriginFD to Google Cloud Platform using Cloud Build, Cloud Run, and other GCP services.

## Prerequisites

1. **Google Cloud Project**: `originfd` (Project Number: 203727718263)
2. **Enabled APIs**:
   - Cloud Build API
   - Artifact Registry API
   - Cloud Run API
   - Cloud SQL API
   - Memorystore (Redis) API
   - VPC Access API
   - Secret Manager API
   - Compute Engine API

## Architecture Overview

The deployment consists of:
- **API Service**: FastAPI backend (Cloud Run)
- **Orchestrator Service**: AI orchestration and task management (Cloud Run)
- **Workers Service**: Background task processing with Celery (Cloud Run)
- **Web Application**: Next.js frontend (Cloud Run)
- **Database**: PostgreSQL (Cloud SQL)
- **Cache/Queue**: Redis (Memorystore)
- **Networking**: VPC with private connectivity

## Step 1: Set up IAM Permissions

The Cloud Build service account needs the following permissions to deploy the infrastructure:

```bash
# Set variables
PROJECT_ID="originfd"
PROJECT_NUMBER="203727718263"
CLOUDBUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

# Grant necessary roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CLOUDBUILD_SA}" \
  --role="roles/cloudsql.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CLOUDBUILD_SA}" \
  --role="roles/redis.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CLOUDBUILD_SA}" \
  --role="roles/vpcaccess.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CLOUDBUILD_SA}" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CLOUDBUILD_SA}" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CLOUDBUILD_SA}" \
  --role="roles/secretmanager.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CLOUDBUILD_SA}" \
  --role="roles/compute.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CLOUDBUILD_SA}" \
  --role="roles/iam.serviceAccountUser"
```

## Step 2: Create Cloud Build Trigger

1. **Connect to GitHub Repository**:
   ```bash
   gcloud builds triggers create github \
     --project=$PROJECT_ID \
     --repo-name=OriginFD \
     --repo-owner=YOUR_GITHUB_USERNAME \
     --branch-pattern="^main$" \
     --build-config=cloudbuild.yaml \
     --name="originfd-deploy"
   ```

2. **Manual Trigger (Alternative)**:
   ```bash
   gcloud builds submit --config=cloudbuild.yaml .
   ```

## Step 3: Deployment Process

The `cloudbuild.yaml` file automates the entire deployment:

### Infrastructure Setup
- Creates Artifact Registry for Docker images
- Sets up VPC network with private subnet
- Provisions Cloud SQL PostgreSQL instance
- Creates Memorystore Redis instance
- Configures Serverless VPC Access connector
- Generates and stores secrets (JWT, database, Redis URLs)

### Application Deployment
- Builds Docker images for all 4 services
- Deploys to Cloud Run with appropriate configurations
- Runs database migrations
- Sets up load balancer and external IP

### Services Deployed
1. **API** (`/api/*`): Port 8000, private access, database connection
2. **Orchestrator** (`/orchestrator/*`): Port 8001, private access
3. **Workers**: Background processing, no direct HTTP access
4. **Web** (`/*`): Port 3000, public access, frontend application

## Step 4: Post-Deployment Configuration

### Domain Setup (Optional)
To use a custom domain:
1. Point your domain to the load balancer IP
2. Set up SSL certificate in Cloud Load Balancer
3. Update the web service environment variables

### Monitoring and Logging
- All services automatically log to Cloud Logging
- Set up monitoring dashboards in Cloud Monitoring
- Configure alerting for service health and performance

### Scaling Configuration
Services are configured with automatic scaling:
- **API**: 1-10 instances, 80 concurrent requests
- **Orchestrator**: 1-5 instances, 40 concurrent requests
- **Workers**: 1-10 instances, 20 concurrent requests
- **Web**: 1-20 instances, 100 concurrent requests

## Environment Variables

### Production Configuration
The deployment sets the following environment variables:

**API/Orchestrator/Workers**:
- `ENVIRONMENT=production`
- `DEBUG=false`
- `DATABASE_URL` (from Secret Manager)
- `REDIS_URL` (from Secret Manager)
- `JWT_SECRET_KEY` (from Secret Manager)

**Web Application**:
- `NODE_ENV=production`
- `NEXT_PUBLIC_API_URL` (auto-configured to API service URL)

## Security Considerations

### Network Security
- All backend services (API, Orchestrator, Workers) are not publicly accessible
- Database and Redis are on private network without external IPs
- Frontend communicates with backend through internal VPC

### Secret Management
- All sensitive configuration stored in Secret Manager
- Secrets are automatically rotated and versioned
- Services access secrets through service account authentication

### Authentication
- JWT-based authentication with rotating secret keys
- Services communicate using internal service authentication
- Public endpoints require proper authorization headers

## Troubleshooting

### Build Failures
1. Check IAM permissions are correctly set
2. Verify all required APIs are enabled
3. Check build logs in Cloud Build console

### Service Startup Issues
1. Review service logs in Cloud Logging
2. Verify database connectivity from VPC connector
3. Check secret availability and formatting

### Performance Issues
1. Monitor service metrics in Cloud Monitoring
2. Adjust CPU/memory allocation in Cloud Run services
3. Scale Redis instance if queue processing is slow

## Cost Optimization

### Development Environment
For development, you can:
- Use smaller Cloud SQL instance (db-f1-micro)
- Reduce Redis instance size
- Set lower max instances on Cloud Run services

### Production Scaling
- Monitor actual usage and adjust instance limits
- Use Cloud SQL read replicas for heavy read workloads
- Consider Cloud CDN for static assets

## Maintenance

### Database Backups
- Cloud SQL automatically creates daily backups
- Configure backup retention policy as needed
- Test restore procedures regularly

### Updates and Deployments
- All deployments are atomic through Cloud Run revisions
- Use Cloud Build triggers for automated deployments
- Implement blue-green deployments for zero downtime

### Monitoring
Set up alerts for:
- Service health check failures
- High error rates or latency
- Resource utilization thresholds
- Database connection issues

## Support

For issues with the deployment:
1. Check service logs in Google Cloud Console
2. Review Cloud Build execution history
3. Verify network connectivity and security rules
4. Monitor service performance metrics