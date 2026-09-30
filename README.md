# Field & Forge — An Agentic Arc Product

A fictional agricultural manufacturing quoting demo: three hopper scenarios, eight simulated human review gates, deterministic Python calculations, customer PDFs, simulated acceptance, and buy-only requisitions.

**Live demo:** https://agentic-arc-manufacturing.vercel.app/

## What is included

- React/TypeScript frontend, original Agentic Arc logo assets and Field & Forge wordmark.
- FastAPI backend with Decimal costing, pricing, feature/history route estimates, scenario fixtures and PDF export.
- Supabase schema migrations, session isolation, inventory reservations and versioned shop rules.
- Quote-scoped MCP server and a scripted host harness for its twelve tools.
- Python tests and explicit opt-in hosted integration checks.

This is the current deployed application source. Generated build output, credentials, live database records, private discovery material, local deployment configuration and session test artifacts are intentionally excluded.

## Local setup

Use Python 3.12 and Node 22.12+.

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
npm ci
cp .env.example .env
npm run build
.venv/bin/uvicorn app:app --host 127.0.0.1 --port 8000
```

Before running the app, configure your own Supabase project in `.env` and apply the SQL files under `supabase/migrations` in filename order. Generate a new random `ARC_BACKEND_TOKEN` for your server, then use a trusted database administration session to insert its SHA-256 hex digest into `arc_private.server_keys(digest)`. Store the plaintext token only in the server environment. The public migrations intentionally contain no pre-provisioned deployment capability. Never expose this token in frontend variables or commit `.env`.

Required variables: `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `ARC_BACKEND_TOKEN`. There is no local-database fallback and no model API key requirement.

## Verification

```sh
npm run typecheck
npm run build
.venv/bin/python -m pytest -q tests
```

The scripts below create synthetic records in the configured database; run them only against a project you administer:

```sh
.venv/bin/python scripts/check_security.py
.venv/bin/python scripts/check_hosted.py
.venv/bin/python scripts/check_shop_rules.py
node scripts/check_mcp.mjs
```

The MCP harness expects the local app at port 8000 unless its documented environment override is set. It is a scripted protocol test, not a Recorded AI run. `scripts/build_source_pack.py` can regenerate the synthetic source pack.

## Deployment

`vercel.json` selects FastAPI and builds the frontend. Set the three server variables as sensitive Vercel environment variables. Preserve `public/assets`, `backend/assets` and `backend/playbooks` in the deployment. `/api/health` verifies Python arithmetic and runtime assets. Connecting this repository to a Vercel project is a separate deployment configuration step.

## MCP connection

Create a quote in Live MCP mode and generate its quote-scoped client connection in the app. Use Streamable HTTP at `/mcp` with `Authorization: Bearer <quote capability>`. The host must support a custom bearer header; OAuth registration is not implemented. The capability expires with the seven-day demo session; generating another revokes the previous one.

Tools: `list_pending_jobs`, `claim_job`, `get_quote_context`, `read_source`, `lookup_catalog_and_history`, `inspect_inventory`, `calculate_quote`, `calculate_schedule`, `compare_acceptance_cost`, `submit_stage_proposal`, `add_risk_finding`, `report_job_failure`.

Scope is one quote and its sources/jobs. MCP cannot approve human gates, reserve/commit stock, send email, place purchases or authorize production. No host account connector is registered by this repository.

## Known limits

All scenario companies, supplier offers and job history are synthetic. Approvals identify a demo visitor and simulated role; they are never real authorization. Win likelihood is illustrative, synthetic history. Business days use US Central and a synthetic Mon–Fri calendar without holiday or capacity guarantees. Custom requests need engineering review and are not silently assigned a prepared estimate. Customer acceptance and procurement are simulations; no purchase order, payment, email or production release occurs.

Granola and Drive cards remain setup required until the owner selects and authorizes source records. Real AI-host scenario recordings remain a separate human-assisted step; saved fixtures are prepared examples.

## Copyright

Copyright (c) 2026 Ben Dudley. All rights reserved. **No open-source license is granted.** See [COPYRIGHT](COPYRIGHT). Third-party dependencies retain their own licenses. Public visibility does not grant an additional license to reuse the application or original brand assets.
