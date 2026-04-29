# Yieldwise Auth Setup

Single-tenant multi-user auth. JSON-file backed user store at
`data/personal/auth_users.json`. Bcrypt password hashing.

## Environment Variables

| Var | Required | Purpose |
| --- | --- | --- |
| `SESSION_SECRET` | **Yes (production)** | URL-safe random ≥32 bytes. Used to sign session cookies. Rotate to invalidate all sessions. |
| `ATLAS_ADMIN_USERNAME` | First boot only | Username for the seeded admin. |
| `ATLAS_ADMIN_PASSWORD` | First boot only | Min 8 chars. Change immediately after first login via the admin UI. |
| `ATLAS_HTTPS_ONLY` | Recommended (production) | Set to `true` to mark the session cookie as `Secure`. Required if running behind TLS. |
| `ATLAS_PERSONAL_DATA_DIR` | Optional | Override the user-store directory (default: `<repo>/data/personal/`). |

## Role Model

- `admin` — full access including user management.
- `analyst` — read + write data; no user management.
- `viewer` — read-only.

## First Boot

```bash
export SESSION_SECRET=$(openssl rand -base64 32)
export ATLAS_ADMIN_USERNAME=ops
export ATLAS_ADMIN_PASSWORD='change-me-immediately'
export ATLAS_HTTPS_ONLY=true
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

The startup log will show:

```
Yieldwise auth: seeded initial admin user 'ops'
```

Visit `/login`, sign in as `ops`, change the password via `/admin/users`.

## Adding More Users

1. Sign in as admin.
2. Visit `/admin/users`.
3. Add user with username, password (≥8 chars), role.

## Disabling a User

Same UI: toggle `disabled`. Disabled users cannot log in even with correct password. Their existing sessions become invalid on next request.

## Rotating Passwords

Same UI: "Change password" sets a new password. The user must re-login.

## Backup

Back up `data/personal/auth_users.json` regularly. Format is plain JSON; passwords are bcrypt-hashed.

## Restoring

Stop uvicorn → restore the JSON file → restart. No migration step required.
