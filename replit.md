# STACK Service Desk AI Solution

Enterprise IT service desk platform for Jade Global Software, powered by Azure OpenAI GPT-4o and LangChain. Automates resolution of common IT issues (SharePoint access, license requests, distribution list updates, Windows issues) with AI confidence scoring and SLA management.

## Run & Operate

- Frontend (React+Vite): workflow `artifacts/stack-frontend: web` — port assigned by $PORT
- Backend (Python FastAPI): workflow `artifacts/api-server: API Server` — port 8080
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from the OpenAPI spec
- `pnpm --filter @workspace/stack-frontend run typecheck` — typecheck frontend

## Stack

- pnpm workspaces, Node.js 24, TypeScript 5.9
- Frontend: React + Vite + shadcn/ui + Tailwind + Recharts + React Query
- Backend: Python 3.11 + FastAPI + SQLAlchemy (async) + asyncpg
- DB: PostgreSQL + SQLAlchemy ORM (async)
- Auth: JWT (python-jose) — Bearer token via Authorization header
- AI: Azure OpenAI GPT-4o + LangChain
- API Contract: OpenAPI spec in `lib/api-spec/openapi.yaml` → Orval codegen

## Where things live

- `lib/api-spec/openapi.yaml` — OpenAPI spec (source of truth for API contract)
- `lib/api-client-react/src/generated/` — Generated React Query hooks
- `lib/api-zod/src/generated/` — Generated Zod schemas
- `artifacts/stack-frontend/src/` — React frontend
  - `pages/` — all pages (dashboard, tickets, admin, login)
  - `contexts/AuthContext.tsx` — JWT auth state
  - `lib/apiSetup.ts` — sets base URL `/api` and Bearer token getter
- `artifacts/api-server/backend/` — Python FastAPI backend
  - `main.py` — FastAPI app entry, lifespan, route registration
  - `app/core/database.py` — async SQLAlchemy engine (handles sslmode → asyncpg ssl)
  - `app/core/config.py` — pydantic-settings config (reads env vars)
  - `app/models/` — SQLAlchemy ORM models
  - `app/api/v1/routes/` — route handlers (auth, tickets, dashboard, admin, sops, reports, roi, logs, chat)
  - `app/ai/langchain_agent.py` — LangChain AI resolution engine
  - `app/services/` — external integrations (Graph API, Freshservice, WinRM, Google Chat, Teams)
  - `app/utils/seed.py` — seeds admin + 9 agents + 2 users + SOPs + thresholds

## Architecture decisions

- asyncpg does not accept `sslmode=require` in the URL — stripped and passed as `ssl=ctx` in `connect_args` (see `database.py`)
- JWT tokens stored in `localStorage` as `stack_auth` JSON blob; custom-fetch reads it via `setAuthTokenGetter`
- Frontend uses `setBaseUrl("/api")` so all generated hooks hit `/api/...` through the shared proxy
- API routes are prefixed at `/api/v1/` in the FastAPI app itself (not rewritten by the proxy)
- Only `@jadeglobal.com` email addresses are allowed to log in

## Product

Three user roles:
- **Admin**: Full dashboard with KPIs, charts, SLA-at-risk table, recent activity; ticket management; ROI dashboard; system logs; admin config (thresholds, SLA configs, user management); SOP manager
- **Agent**: Dashboard + all tickets view + ticket detail with AI resolution, escalation, notes, audit trail
- **User**: Personal dashboard, raise ticket (category wizard), my tickets list, ticket status polling

AI features: confidence scoring (intent clarity, SOP match, historical success, input completeness), auto-resolution vs. human escalation decision, step-by-step execution output displayed in ticket detail.

## Seed Accounts

- `admin@jadeglobal.com` / `Admin@Stack2025` (admin)
- `testuser@jadeglobal.com` / `Test@Stack2025` (user)
- 9 agents: `agent1@jadeglobal.com` … `agent9@jadeglobal.com` / `Agent@Stack2025`

## User preferences

- Brand: Navy #1B3A6B (primary), Orange #F47920 (accent), Cyan #0097A7 (info)
- Only @jadeglobal.com emails allowed

## Gotchas

- Do NOT run `pnpm dev` at workspace root — use workflows
- asyncpg rejects `sslmode` URL param — always strip it before creating the engine (handled in `database.py`)
- Codegen must be re-run after any changes to `lib/api-spec/openapi.yaml`
- The API server runs from `artifacts/api-server/` as the working directory; Python module is `backend.main:app`

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
- Missing secrets (user must add): AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, GRAPH_API_CLIENT_SECRET, GOOGLE_CLIENT_SECRET, TEAMS_APP_PASSWORD, FRESHSERVICE_API_KEY, WINRM_PASSWORD, CHATBOT_WEBHOOK_SECRET, JWT_SECRET_KEY
