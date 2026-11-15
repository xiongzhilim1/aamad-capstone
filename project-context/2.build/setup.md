# Setup — Peers & Circles (capstone MVP)

Project skeleton produced by `@project.mgr` (`*setup-project`, `*install-dependencies`, `*configure-env`, `*document-setup`). Setup only: no business logic. Traces to `project-context/1.define/sad.md` §1–§5 and `ux.md` §4.

## 1. Repository structure

```
aamad-capstone/
├── frontend/                 Next.js 16 (App Router) + TypeScript + Tailwind v4   → @frontend.eng
│   ├── app/                  scaffold pages (placeholder; replaced per ux.md)
│   ├── next.config.ts        /api/* → BACKEND_URL rewrite (SAD §3, §6)
│   ├── AGENTS.md             written by Next.js; points agents at the bundled docs
│   └── .env.example          BACKEND_URL
├── backend/                  FastAPI + CrewAI, Python 3.12, uv                    → @backend.eng
│   ├── app/main.py           FastAPI app with GET /healthz only
│   ├── app/ai/               the two crew wrappers go here (SAD §4 Runtime Integration Layer)
│   ├── app/crews/config/     agents.yaml / tasks.yaml go here (CrewAI adapter rule)
│   ├── migrations/           Alembic migrations (not initialised yet)
│   ├── tests/test_healthz.py smoke test
│   ├── Dockerfile            python:3.12-slim + uv, locked install, /healthz HEALTHCHECK
│   └── .env.example          backend env names (SAD §4)
├── evals/                    eval suite location for @qa.eng (*run-evals)
├── docker-compose.yml        Postgres 16 + backend (local development)
├── .github/workflows/ci.yml  lint, type-check, test, build (no deploy)
└── .env.example              AAMAD_TARGET_RUNTIME (framework setting)
```

## 2. Toolchain and pinned versions

| Tool | Version | Notes |
|------|---------|-------|
| Node.js | 24.19.0 (local, nvm) | CI uses Node 24 |
| npm | bundled with Node 24 | lockfile `frontend/package-lock.json` |
| Python | 3.12.13 | `backend/.python-version`; `requires-python >=3.12,<3.13` |
| uv | 0.13.7 | lockfile `backend/uv.lock`; same version in Dockerfile and CI |
| Docker | 29.9.3, Compose v5.7.0 | Docker Desktop, installed by the operator 2026-11-15; CLI at `~/.docker/bin` |

## 3. Dependencies

**Frontend** (`create-next-app@16.4.6`, exact versions from `package.json`): `next` 16.4.6, `react` / `react-dom` 19.3.0, `tailwindcss` 4.3.3, `@tailwindcss/turbopack` 4.3.3, `eslint-config-next` 16.4.6, TypeScript 5. `npm audit --omit=dev`: **0 vulnerabilities**; 7 moderate findings are in dev-only dependencies (recorded, not fixed with `audit fix --force`).

**Backend** (resolved in `uv.lock`):

| Package | Version | Why |
|---------|---------|-----|
| `crewai[anthropic]` | 1.15.41 | runtime for the two crews (SAD Pattern Decision) |
| `anthropic` | 0.73.0 | pulled in by the CrewAI `anthropic` extra (native provider) |
| `fastapi[standard]` | 0.163.0 | API layer; includes `uvicorn` 0.54.0 |
| `sqlmodel` | 0.0.50 | ORM over SQLAlchemy (SAD §4) |
| `alembic` | 1.20.1 | migrations |
| `psycopg[binary]` | 3.3.9 | Postgres driver (Supabase in production) |
| `pydantic-settings` | 2.16.3 | env-based config |
| dev: `pytest` 9.2.0, `httpx` 0.28.1, `ruff` 0.17.5, `mypy` 2.4.1 | | tests, lint, types |

Not installed (left for the owning persona): a UI component library or icon set (`@frontend.eng`, per ux.md), a typed OpenAPI client generator (`@integration.eng`).

## 4. Environment

Names only; real values never committed (`.env` and `.env.*` are git-ignored except `.env.example`).

- `backend/.env.example`: `ANTHROPIC_API_KEY`, `DATABASE_URL`, `SESSION_SECRET`, `DEMO_ACCESS_CODE`, `ALLOWED_ORIGINS`, `AI_SPEND_CAP_USD` (20), `AI_MODEL_SUGGEST` / `AI_MODEL_ASSIST` (`claude-sonnet-5-5`), `AAMAD_TARGET_RUNTIME`.
- `frontend/.env.example`: `BACKEND_URL` (server-side, used by the rewrite).
- Root `.env.example`: `AAMAD_TARGET_RUNTIME=crewai`.

## 5. Local development

```bash
# one-time
cp backend/.env.example backend/.env          # copy, don't rename; then fill ANTHROPIC_API_KEY etc.
cp frontend/.env.example frontend/.env.local
cd frontend && npm install && cd ..
cd backend && uv sync && cd ..

# run (Docker Desktop required for the database)
docker compose up db                           # Postgres on :5432
cd backend && uv run uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev                     # http://localhost:3000, /api → :8000

# checks
cd backend && uv run ruff check . && uv run mypy app && uv run pytest -q
cd frontend && npm run lint && npx next typegen && npx tsc --noEmit && npm run build
```

If the shell has a project-root virtualenv active, `unset VIRTUAL_ENV` before `uv run` in `backend/` (uv otherwise warns and uses `backend/.venv` anyway).

## 6. CI

`.github/workflows/ci.yml` runs on pull requests and pushes to `main`: backend (uv sync from lock, ruff, ruff format check, mypy, pytest against a Postgres 16 service, Docker build) and frontend (npm ci, eslint, tsc, next build). No deploy step (delivery-workflow rule). The manual evals workflow is added by `@qa.eng`.

## 7. Verification (2026-11-15)

| Check | Result |
|-------|--------|
| Backend `pytest` (`/healthz`) | 1 passed |
| Backend `ruff check`, `ruff format --check`, `mypy --strict app` | passed |
| Frontend `eslint`, `tsc --noEmit`, `next build` | passed |
| Backend served `GET /healthz` locally | `{"status":"ok"}` |
| Frontend proxy `GET /api/healthz` on :3000 | `{"status":"ok"}`, confirming the SAD §6 rewrite |
| `docker compose up -d db` | passed: Postgres 16.16, healthy on :5432 |
| `docker build backend` and `GET /healthz` from the container | passed: `{"status":"ok"}` |
| `docker compose up backend` (full stack) | **not tested**: needs `backend/.env` |
| CI workflow on GitHub | First run (43716537343): backend passed; frontend failed at `tsc` (`LayoutProps` not found: route types are generated into `.next/`). Fixed by adding `npx next typegen` before `tsc`; re-run result below |

## 8. Spec drift for `@system.arch` (reported, not patched)

1. **Model provider path**: the SAD says the crews call the model "through CrewAI's model layer (LiteLLM)". CrewAI 1.15.41 offers a native Anthropic provider via the `anthropic` extra, which was installed instead of LiteLLM (fewer layers). OQ-A03 still applies and now reads: verify that `anthropic` 0.73.0 inside CrewAI can call `claude-sonnet-5-5` without `temperature`, and whether it passes structured outputs and `effort`; if the pinned SDK is too old, decide between upgrading it or calling it outside CrewAI.
2. **Frontend env name**: SAD §4 lists `NEXT_PUBLIC_API_BASE_URL`. Because the browser calls relative `/api/*` (SAD §3/§6 rewrite), the frontend needs only a server-side `BACKEND_URL`; no `NEXT_PUBLIC_` variable exists.

## Sources

- `project-context/1.define/sad.md` (v1, §1–§5, Model and Context Strategy), `ux.md` (approved), `prd.md` (v1.2)
- `.claude/rules/adapter-crewai.md`, `.claude/rules/aamad-core.md`
- Operator decisions 2026-11-15: install Docker Desktop; Tailwind + CSS variables; scaffold and install
- Package registries (npm, PyPI via uv) at install time, 2026-11-15

## Assumptions

- `create-next-app@16.4.6` defaults (`cacheComponents`, `partialPrefetching`) are kept; `@frontend.eng` may change them.
- The scaffold's `frontend/README.md` was removed (persona rule: no README); `frontend/AGENTS.md` from Next.js was kept because it points coding agents at the version-matched docs.
- Palette A tokens are not written here; `@frontend.eng` maps them per ux.md §4.

## Open Questions

- OQ-A03 (updated above): native Anthropic SDK 0.73.0 compatibility with 5.5-generation parameters.
- Whether to fix the 7 moderate dev-dependency audit findings now or leave them to Next.js updates.

## Audit

- 2026-11-15 — persona: `project-mgr` — actions: `*setup-project`, `*install-dependencies`, `*configure-env`, `*document-setup` — runtime resolved: `crewai` (env `AAMAD_TARGET_RUNTIME`, matches `aamad.config.yml`) — no model calls made; no secrets written.
- 2026-11-15 — persona: `project-mgr` — action: `sync-docs` — Doc sync: no descriptive updates (setup.md is the only allowlisted doc and was written in this change set; the root README describes the AAMAD framework, not the app). Spec drift is reported in §8 for `@system.arch`.
- 2026-11-15 — persona: `project-mgr` — action: `*document-setup` (update) — Docker verified: compose db healthy; backend image builds and serves /healthz.
- 2026-11-15 — persona: `project-mgr` — action: CI fix — added `next typegen` before `tsc` in CI and in the local check command.
