# Yieldwise Security Posture (v0.2)

## Auth

- **Session cookies** signed with `SESSION_SECRET`. HTTP-only, `SameSite=Lax`.
- `Secure` flag set when `ATLAS_HTTPS_ONLY=true`.
- 14-day session lifetime; re-login required after expiry.
- bcrypt cost factor 12 for password hashing.

## Protected vs. unprotected routes

- `/api/v2/*` — gated by router-level `Depends(current_user)`. Two intentional public exceptions: `/api/v2/health` (load-balancer probes) and `/api/auth/*` (login itself must be reachable; admin sub-endpoints inline-gate via `require_role("admin")`).
- `/`, `/backstage/`, `/admin/*` — gated by `StaticShellAuthGate`. Anonymous visits redirect to `/login?next=<path>`.
- Legacy `/api/*` (non-v2) routes from `api/service.py` re-exports are **NOT** gated in v0.2. A logged-out caller can still reach them. These will be rebuilt or gated in a later milestone (M6 backstage workflow pivot). Treat them as semi-public until then.

### ⚠️ Legacy `/api/*` exposure (action required for production)

Routes from `api/service.py` re-exports are NOT gated by the Plan 2 auth layer.
Plan 5 (M6) will rebuild them. Until then, **do not expose port 8000 directly
to the public internet**. Bind to `127.0.0.1` and put it behind a TLS-terminating
reverse proxy that enforces network-level auth (mTLS, OIDC, IP allowlist).

Specific dangerous endpoints currently reachable anonymously:

- `POST /api/database/bootstrap-local` — provisions schema, drops + recreates tables
- `POST /api/jobs/refresh-metrics` — kicks off long-running compute
- `POST /api/import-runs/{run_id}/persist` — writes to PostgreSQL
- `POST /api/reference-runs/{run_id}/persist` — writes to PostgreSQL
- `POST /api/communities/{community_id}/anchor-confirmation` — mutates community anchor records
- `POST /api/geo-assets/runs/{run_id}/*` — mutates geometry queue (work-orders, persist, tasks)
- `POST /api/browser-capture-runs/{run_id}/review-queue/*` — mutates capture queue
- `POST /api/browser-sampling-captures` — mutates capture queue (research-only branch should remove this entirely on main)

This list is conservative; assume any non-GET legacy `/api/*` route is a mutation.

## CSRF

We rely on `SameSite=Lax` cookie + same-origin SPA. **No separate CSRF token in v0.2.**

This is acceptable for:
- Private deployments behind corporate VPN / SSO front
- Same-origin browser app

This is NOT acceptable for:
- Public CDN-hosted dashboards with credentialed cross-origin requests
- Embedded iframes from third-party domains

If you need either, file a Plan 4+ ticket to add explicit CSRF tokens.

## Audit Log

**Not implemented in v0.2.** Login / logout / admin actions are not persisted to a queryable log. Server-level logs (`uvicorn` stdout) capture login attempts at INFO level, but there is no per-tenant audit table.

If your compliance program requires an audit log, file a Plan 4+ ticket. The natural location is a new `audit_events.json` file in `data/personal/` alongside `auth_users.json`.

## Rate Limiting

**Not implemented in v0.2.** Login endpoint does not rate-limit failed attempts. If exposed to the public internet, deploy behind a rate-limiting reverse proxy (Cloudflare, nginx with `limit_req`, etc.).

## Data Encryption

- **At rest:** customer data lives in PostgreSQL or staged JSON files. Yieldwise does not encrypt at the application layer; rely on disk-level encryption (LUKS / FileVault / BitLocker) and Postgres TDE if required.
- **In transit:** Yieldwise expects to run behind a TLS-terminating reverse proxy (nginx, Caddy, AWS ALB). The app itself does not implement TLS.

## Threat Model

In scope:
- Casual unauthorized access (lost session cookie, weak password)
- Internal abuse (analyst tries to access admin endpoints)
- Disabled-user lockout

Out of scope (v0.2):
- Sophisticated CSRF
- Brute-force credential stuffing (use a reverse proxy)
- Insider data exfiltration (use OS-level audit + DLP)
- Compromised admin account (assume admin = trusted)
