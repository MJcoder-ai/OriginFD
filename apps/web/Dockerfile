# OriginFD Web Application Dockerfile
# Multi-stage build for Next.js
FROM node:20-alpine AS base
WORKDIR /app

# Install pnpm
RUN npm install -g pnpm

# Dependencies stage
FROM base AS deps
# Install dependencies based on preferred package manager
COPY turbo.json package.json pnpm-lock.yaml* pnpm-workspace.yaml ./
COPY apps/ ./apps/
COPY packages/ ./packages/
RUN pnpm install --frozen-lockfile

# Builder stage
FROM base AS builder
WORKDIR /app

# Copy the complete workspace from deps stage to preserve pnpm symlinks
COPY --from=deps /app/ ./

# Set environment variables for build
ENV NEXT_TELEMETRY_DISABLED 1
ENV TURBO_TELEMETRY_DISABLED 1
ENV NODE_ENV production

# Build the Next.js application with complete workspace
RUN pnpm turbo build --filter=web

# Runner stage
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy standalone output and static assets into the application directory
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/standalone/node_modules ./node_modules
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/standalone/package.json ./package.json
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/standalone/apps/web ./apps/web
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/public ./apps/web/public
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/static ./apps/web/.next/static

USER nextjs

EXPOSE 3000

# Health check with dynamic port support
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-3000}/api/health || exit 1

CMD ["node", "apps/web/server.js"]
