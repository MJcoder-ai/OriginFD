# Repository Guidelines

## Project Structure & Module Organization

OriginFD is a pnpm + Poetry monorepo. `apps/web` hosts the Next.js UI, `apps/mobile-*` hold React Native spikes, and shared TypeScript libraries live in `packages/ts`. Python FastAPI, Celery, and orchestration services reside under `services/*`, while cross-cutting domain logic sits in `domains`. Generated assets land in `generated/`, infra and operational tooling live in `infra/` and `ops/`, and regression suites live in `tests/` with reusable fixtures in `tests/factories.py`. Automation scripts such as the API client generator stay in `scripts/`.

## Build, Test & Development Commands

- `pnpm install` (root): hydrate all workspace dependencies with the pinned pnpm 8 lockfile.
- `pnpm --filter @originfd/web dev`: launch the Next.js shell with Tailwind CSS watch mode.
- `pnpm build` / `pnpm lint` / `pnpm type-check`: run the turbo pipelines across every workspace.
- `poetry install --with dev`: create the Python 3.12 environment used by `services/api` and orchestrator workers.
- `pnpm generate:api-client`: refresh the TypeScript client from the running FastAPI schema after backend changes.

## Coding Style & Naming Conventions

Prettier and ESLint run via pre-commit; expect two-space indentation, trailing commas, and sorted imports across TypeScript files. React components and Zustand stores use PascalCase filenames, while shared hooks live under `src/hooks` and start with `use`. Python code is auto-formatted with Black (88 chars) and isort, and modules stay snake_case; keep secrets out of version control by populating `.env.local.example` variants.

## Testing Guidelines

`pnpm test` fans out turbo-managed suites and unit specs should sit beside their source as `*.test.ts[x]`. UI units rely on Vitest (`pnpm --filter @originfd/web test:unit`) and end-to-end journeys run under Playwright (`pnpm --filter @originfd/web test`). Backend contracts live in `tests/api` and `tests/integration`; execute `poetry run pytest tests -q --maxfail=1` and include both success and failure assertions, updating fixtures in `tests/factories.py` when schemas shift.

## Commit & Pull Request Guidelines

Match the history by prefixing commits with intent tokens such as `feat(scope):`, `fix:`, or urgent `CRITICAL FIX:` when stabilizing production. Keep commits runnable and include generated clients or migrations alongside the change to keep CI green. PRs need a crisp summary, linked issue, evidence (screenshots or cURL) for user-facing updates, and a checklist covering `pnpm lint`, `pnpm test`, and relevant `poetry run pytest` runs; tag the owning team and Release Engineering when infra or Docker assets move.
