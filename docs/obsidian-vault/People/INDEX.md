# People

| Name | Role | Status | Surfaces touched |
|---|---|---|---|
| Project owner | Founder, lead developer, operator | active | every surface |
| Demo realtor (`demo-realtor@yakimaweb.local`) | Seed-only | dev-only | content |
| Demo buyer (`demo-buyer@yakimaweb.local`) | Seed-only | dev-only | marketplace |
| Demo vendors (5 base + 21 extra) | Seed-only | dev-only | marketplace |

## Roles in code

- `member` — default
- `realtor` — verified WA license via ARELLO
- `vendor` — onboarded marketplace seller
- `moderator` — staff, mod console only
- `operator` — staff, ops dashboard + mod console
- `superadmin` — Django superuser, schema access

Permission model lives in `apps/core/api/permissions.py`. Role flags on `User`
plus role decorators on views.
