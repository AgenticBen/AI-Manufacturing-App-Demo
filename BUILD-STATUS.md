# Visible quoting workflow — September 30, 2026

Controlling scope: `Astra Prompt/00-START-HERE.md` and tasks 01–06, plus Ben’s request for a comprehensive survey / requirements document and the supplied Ivy Hopper Works logo.

Implementation commit: `fbd259a` — https://github.com/AgenticBen/AI-Manufacturing-App-Demo/commit/fbd259a
Final candidate: https://agentic-arc-manufacturing-4t7bivh5h-agenticbens-projects.vercel.app (`dpl_4GBqA9bhGzv2fC84uFExJiYfqbUH`).
Presentation / production URL: https://agentic-arc-manufacturing.vercel.app

| Deliverable | Status | Verification |
|---|---|---|
| 1 · D1–D13 / Data sources | done-and-verified | Additive, read-only Supabase library; stable record/row IDs; spreadsheet, supplier, card, folder, transcript and document views; nine one-page historical quote PDFs; five real supplier websites with demo-price disclosure. |
| 2 · Exact agent instructions | done-and-verified | 22 exact versioned playbooks in Supabase D13, COMMON disclosure, scoped inputs/tools/output fields and human checks. |
| 3 · Shared step layout / review / corrections | done-and-verified | Server-enforced document-open and confirmation gates, PM/Ops confirmation, explicit simulated messages, old/new targeted prepared corrections and audit trail. Browser correction reopened dependent reviews and preserved the prior output. |
| 4 · Document trail | done-and-verified | All 18 artifacts for seed, grain and feed; numbered citations, Python-generated PDFs, session ownership. Mobile document sheet fits 390 px. Grain/feed BOM row offsets verified against the actual library. |
| 5 · Agents / handoffs / cost orchestration | done-and-verified | Supervisor and scoped subagents; executable pack-size rejection → supervisor → targeted prepared rerun → QA pass; procurement draft; acceptance price variance and buy-only list; PM handoff and explicit simulated sends. |
| 6 · Process map / timing | done-and-verified | Eight steps plus acceptance; owners, agents, inputs and outputs. Clickable read-only seed step exploration preserves real gates. Baseline labeled per research summary; 90-minute per-stage allocation labeled modeled; actual session elapsed times remain separate. |
| P1 · All scenarios and material library | done-and-verified | Hosted full eight-gate acceptance runs for seed, grain and feed; 18 artifact PDFs each. Ammonium nitrate is specialist-only. Missing-material template remains pending until human approval; approved supplements are quote-scoped in Supabase, preserving session isolation. |
| P2 · Optional controls | done-and-verified | Insurance discussion options use USD TBD and do not change price; customer requirements-summary email is simulated; completion extraction is explicitly future-only. |
| Comprehensive survey / requirements | done-and-verified | 173 questions in 14 sections, populated seed/grain/feed examples, search and grouped fields; all answers retained in quote evidence, D11 surveys and D12 client requirements; 15-page requirements PDF contains all 173 questions. Unknown values remain unconfirmed when the original clarification is resolved. Changed scope is saved without a fixture estimate. |
| Ivy Hopper Works identity | done-and-verified | Supplied PNG copied byte-for-byte; branded manufacturer header in Quote pipeline and survey. Desktop and 390 px mobile screenshots verified; customer identities retained. |

## Verification evidence

- 63 Python tests pass, including all 32 original tests. TypeScript and Vite build pass. Final Vercel build is Ready.
- `artifacts/visible-workflow-seed-proof.json`, `artifacts/visible-workflow-grain-proof.json`, `artifacts/visible-workflow-feed-proof.json`: locked-before-review / approved-after-review gates, acceptance recheck, buy-only purchasing, simulated messages and PDFs. Seed is rerun against the final survey build; grain/feed hosted proofs precede the survey addition, with all three subsequently covered by the expanded local artifact/citation tests.
- `artifacts/comprehensive-survey-proof.json`: hosted persistence of 173 fields, complete PDF, exact logo bytes, and changed-scope preservation without a misleading quote.
- `artifacts/comprehensive-requirements.pdf`: 15 pages; all 173 question strings found in extracted text.
- Browser checks: 1440 px and 390 px; source panels, instructions, correction comparison, gated review, process-map jump, searchable survey, save from mobile, requirements register, logo and pipeline. No horizontal overflow at 390 px.
- Original P0 isolation verification denied private-table access and invalid server capability; private quotes remain accessed through session-scoped routes. New PDF routes reuse the same ownership check.
- Main UI remains below its original size: `frontend/src/main.tsx` is 44,865 bytes (original 48,997); new UI is in components.
- Publication scan found no credentials, PII or large files. `.env.example` was explicitly inspected and contains placeholders only. Unrelated local documentation and the deployment-specific server-key digest are preserved and excluded from the commit.

## Release history

- Initial checkpoint: `5a1ed8c`, pushed before redesign; app source matched existing published `7907cda`.
- Task previews: sources `2y9whrwsd`, playbooks `ajv3hv7y2`, layout `m5z6u9306`, documents `k3d2ojghv`, cost orchestration `3fbpzisvo` (all under the existing Vercel project).
- P0 production was promoted before P1: code `f1613ac`, tested preview `dpl_8tcgfDuVu8XBvjh7rSCuSWv6hEpZ`, production deployment `dpl_66vLpF9eenKDGcYhhBwPJaGqGnJu`.
- P1 / P2 preview `dpl_F4LJNqZBLmBzqGSqWzfcYwbqQkkC`: all three hosted acceptance paths passed before the additional survey request.
- Final survey release promoted and verified: production `dpl_GTHQsDi5KLqdEdwzrpE6n38TJ5VV` is Ready. Public `/api/catalog`, `/api/process-map`, `/api/health`, logo, survey persistence and PDF smoke checks pass. Initial alias propagation briefly served the older catalog; the recheck passed after propagation. Browser production pipeline verified with the release query `?release=fbd259a` to avoid the in-app browser’s prior page cache.

All provider copies, supplier prices and agent outputs remain labeled fictional/prepared. No real emails, purchases, model inference, provider sync or production engineering release is claimed. Research summaries are cited in the process map and D9; report figures without checkable URLs are labeled accordingly.
