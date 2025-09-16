# OriginFD Setup Guide

## Prerequisites

- Node.js 18+ 
- pnpm 8+
- Git

## Quick Start

1. **Clone repository**
   ```bash
   git clone <repository-url>
   cd OriginFD
   ```

2. **Install dependencies**
   ```bash
   pnpm install
   ```

3. **Start development server**
   ```bash
   cd apps/web
   pnpm dev
   ```

   The application will be available at `http://localhost:3000` (or `http://localhost:3001` if 3000 is in use).

## Project Structure

```
OriginFD/
├── apps/
│   └── web/                 # Next.js 14 web application
├── packages/
│   └── ts/                  # TypeScript packages
│       ├── types-odl/       # ODL-SD types (buildable)
│       ├── http-client/     # API client (buildable)  
│       └── ui/              # UI components (WIP)
└── docs/                    # Project documentation
```

## Development

- **Web app only**: `cd apps/web && pnpm dev`
- **Build web app**: `cd apps/web && pnpm build`
- **Build packages**: `cd packages/ts/types-odl && pnpm build`

## Demo Credentials

- Email: `admin@originfd.com`
- Password: `admin`

## Environment Variables

The web app can proxy API requests when `NEXT_PUBLIC_API_URL` is defined, but during local development without a backend you can leave this variable unset to use mock handlers under `app/api/bridge/*`.

## Status

✅ Next.js 14 web application with authentication
✅ Dashboard with project management UI  
✅ TypeScript packages for types and API client
⚠️  UI package requires additional component implementation
⚠️  Backend services not yet implemented
