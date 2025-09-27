# Repository Guidelines

## Project Structure & Module Organization

- `apps/web` hosts the Next.js shell; `apps/mobile-*` contain React Native spikes; shared TypeScript utilities live in `packages/ts`.
- Backend FastAPI, Celery, and orchestration services reside under `services/*`; domain logic is centralized in `domains/` for reuse across surfaces.
- Generated clients and assets are tracked in `generated/`; infra and operational tooling are split between `infra/` and `ops/`.
- Tests live in `tests/` with fixtures in `tests/factories.py`; keep UI unit specs beside their sources as `*.test.ts[x]`.

## Build, Test, and Development Commands

- `pnpm install`: sync all workspace dependencies using the pinned pnpm 8 lockfile.
- `pnpm --filter @originfd/web dev`: run the Next.js shell with Tailwind in watch mode.
- `pnpm lint`, `pnpm type-check`, `pnpm build`: execute turbo-managed lint, TypeScript, and build pipelines across workspaces.
- `poetry install --with dev`: create the Python 3.12 environment for API services and workers.
- `poetry run pytest tests -q --maxfail=1`: run backend suites; `pnpm test` aggregates frontend and shared packages.
- `pnpm generate:api-client`: refresh the TypeScript API client after FastAPI schema changes.

## Coding Style & Naming Conventions

- TypeScript uses two-space indentation, trailing commas, and sorted imports via Prettier + ESLint.
- React components and Zustand stores adopt PascalCase filenames; shared hooks live in `src/hooks` and begin with `use*`.
- Python modules remain snake_case and are formatted with Black (88 chars) and isort; commit `.env.local.example` changes rather than secrets.

## Testing Guidelines

- Frontend units run with Vitest (`pnpm --filter @originfd/web test:unit`) and Playwright covers end-to-end flows (`pnpm --filter @originfd/web test`).
- Backend contracts live in `tests/api` and `tests/integration`; update `tests/factories.py` when schemas evolve.
- Target both success and failure cases; keep fixtures minimal and deterministic.

## Commit & Pull Request Guidelines

- Prefix commits with intent tokens like `feat(scope):`, `fix:`, or `CRITICAL FIX:` to mirror history; include generated assets or migrations in the same commit.
- PRs should link issues, summarize changes, attach evidence (screenshots or cURL for UI/API updates), and note completion of `pnpm lint`, `pnpm test`, and `poetry run pytest`.
- Tag owning teams and Release Engineering when touching infra, Docker, or deployment assets, and ensure the change is runnable end-to-end before requesting review.
