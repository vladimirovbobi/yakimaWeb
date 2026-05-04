# Access Matrix — Yakima Real Estate Hub

**Version:** 1.0
**Date:** 2026-05-03
**Owner:** Yakima Real Estate Hub Engineering
**Status:** Active — authoritative
**Cross-references:** [SRS.md](./SRS.md), [ICD.md](./ICD.md), [SECURITY-PLAYBOOK.md](./SECURITY-PLAYBOOK.md), [RUNBOOK.md](./RUNBOOK.md)

> Authoritative source for "who can do what." Every PR that touches authentication, authorization, viewsets, permission classes, or URL routing MUST verify against this document. View-audit checklist for Sprint 0b ships against this matrix.

---

## 1. Document Control

| Field | Value |
|---|---|
| Version | 1.0 |
| Effective | 2026-05-03 |
| Owner | Yakima Real Estate Hub Engineering |
| Review cadence | After each phase ships, plus quarterly |
| Approvers | Lead engineer (PR sign-off) + security reviewer for any role/permission delta |
| Supersedes | None — initial version |
| Distribution | Repo contributors. Excerpts shared in onboarding. |
| Change control | Adding a new role or permission requires updating this doc + an ADR + tests in `apps/<scope>/tests/test_permissions.py`. |

---

## 2. Roles

Roles are listed in increasing order of trust. Each higher role inherits the capabilities of all lower roles unless explicitly noted.

| # | Role | Trust | Definition |
|---|---|---|---|
| 0 | **Anonymous** | None | No auth. Public visitor. |
| 1 | **Member** | Verified email | Authenticated user with confirmed email. Default for new signups after email verification. |
| 2 | **Realtor** | Member + ARELLO-verified WA license | `User` with `RealtorProfile` where `status='verified'`. Can publish blog posts. |
| 3 | **Vendor** | Member + admin-approved | `User` with `VendorProfile` where `is_approved=True`. Can list services in the marketplace. |
| 4 | **Mod** | Staff role | `is_staff=True` AND in Django group `moderator`. Acts on flagged content. |
| 5 | **Op** | Staff role | `is_staff=True` AND in Django group `operator`. Everything mods can do plus business actions (suspend users, refund tool runs, view analytics). |
| 6 | **Admin** | Superuser | `is_superuser=True`. Django admin access. Behind 2FA + IP allowlist. |

Notes:

- A user CAN hold both Realtor and Vendor roles simultaneously (a realtor who also sells photography services).
- Mod and Op are distinct Django groups. A staff member typically holds Op (which subsumes Mod), but pure Mod (no Op) is supported for outsourced moderation.
- Admin (superuser) bypass is auditable: every admin action writes to `audit.ActionLog`. Do not use the admin to bypass workflow when a non-admin path exists; it's logged.
- Email-unverified users exist as a transient state (post-signup, pre-confirmation). Treat as Anonymous for write actions; Member for reads. See §11 Edge cases.

---

## 3. Action Types

| Action | Meaning |
|---|---|
| **None** | Forbidden. Returns 401 (unauth) or 403 (auth, insufficient role). |
| **View** | Read a single resource by ID. |
| **List** | Read a paginated index of resources. |
| **Create** | Insert a new resource. May trigger moderation pipeline. |
| **Update-own** | Update a resource where the user is the owner (`.author`, `.user`, `.created_by`, etc.). |
| **Update-any** | Update any resource regardless of owner. |
| **Delete-own** | Delete a resource where the user is the owner. Often subject to a time window (e.g., 15 min after Create). |
| **Delete-any** | Delete any resource regardless of owner. |
| **Approve** | Mark a resource as approved (out of mod queue, into public). |
| **Suspend** | Temporarily disable a user / resource. Reversible. |
| **Reset / Refund** | Op-level: reset usage counters, refund tool runs, etc. |
| **Override** | Admin-level: override a mod or op decision; recorded with reason. |

---

## 4. Master Resource × Role Matrix

Cells use the action vocabulary from §3. Multiple actions are comma-separated. Where ownership matters, "-own" / "-any" disambiguate. "subject to mod" indicates the action triggers the moderation pipeline (visibility may be deferred). "with window" indicates a time-limited self-service action (default 15 min unless noted).

### 4.1 Public marketing & static surfaces

| Resource | Anonymous | Member | Realtor | Vendor | Mod | Op | Admin |
|---|---|---|---|---|---|---|---|
| Homepage `/` | View | View | View | View | View | View | View |
| `/about/` | View | View | View | View | View | View | View |
| `/guidelines/` | View | View | View | View | View | View | View |
| `/privacy/` | View | View | View | View | View | View | View |
| `/terms/` | View | View | View | View | View | View | View |
| `/healthz/` | View | View | View | View | View | View | View |
| `/sitemap.xml` | View | View | View | View | View | View | View |
| `/robots.txt` | View | View | View | View | View | View | View |
| Status page (`status.yakimaweb.com`) | View | View | View | View | View | View | View |

### 4.2 Authentication

| Resource | Anonymous | Member | Realtor | Vendor | Mod | Op | Admin |
|---|---|---|---|---|---|---|---|
| Sign up (`/accounts/signup/`) | Create | None | None | None | None | None | None |
| Sign in (`/accounts/login/`) | Create | None (already in) | None | None | None | None | None |
| Sign out (`/accounts/logout/`) | None | Create | Create | Create | Create | Create | Create |
| Password reset request | Create | Create | Create | Create | Create | Create | Create |
| Password reset confirm | Create (with token) | Create | Create | Create | Create | Create | Create |
| Email verify confirm | Create (with token) | Create | Create | Create | Create | Create | Create |
| Email change | None | Create-own | Create-own | Create-own | Create-own | Create-own | Create-own |
| 2FA setup | None | Setup-own (optional) | Setup-own (optional) | Setup-own (optional) | **Required** | **Required** | **Required** |
| 2FA disable | None | Disable-own | Disable-own | Disable-own | None (must remain) | None | None (must remain) |

### 4.3 Posts (Yakima Web org posts + Realtor blog posts)

| Resource | Anonymous | Member | Realtor | Vendor | Mod | Op | Admin |
|---|---|---|---|---|---|---|---|
| Yakima Web posts (`type='org'`) | View, List | View, List | View, List | View, List | View, List | View, List, Update-any, Delete-any | Update-any, Delete-any |
| Realtor blog posts (`type='blog'`) — published | View, List | View, List | View, List | View, List | View, List | View, List | View, List |
| Realtor blog posts — own drafts | None | None | View-own, List-own | None | None | View-any | View-any |
| Create blog post | None | None | Create (subject to mod) | None | None | None | None |
| Update blog post | None | None | Update-own (subject to mod re-check) | None | None | Update-any | Update-any |
| Delete blog post | None | None | Delete-own | None | None | Delete-any | Delete-any |
| Lead-magnet pages (`type='lead_magnet'`) | View | View | View | View | View | View, Update-any | Update-any |

### 4.4 Comments

| Resource | Anonymous | Member | Realtor | Vendor | Mod | Op | Admin |
|---|---|---|---|---|---|---|---|
| Comments on a post | View, List | View, List, Create (subject to mod) | View, List, Create | View, List, Create | View, List, Approve, Delete-any | View, List, Approve, Delete-any | Update-any, Delete-any |
| Update comment | None | Update-own (with 15-min window) | Update-own (window) | Update-own (window) | Update-any | Update-any | Update-any |
| Delete comment | None | Delete-own | Delete-own | Delete-own | Delete-any | Delete-any | Delete-any |
| Removed comment placeholder | View ("Removed by moderation") | View | View | View | View, View-original | View, View-original | View-original |

### 4.5 Forum

| Resource | Anonymous | Member | Realtor | Vendor | Mod | Op | Admin |
|---|---|---|---|---|---|---|---|
| Threads (list, view) | View, List | View, List, Create (subject to mod) | View, List, Create | View, List, Create | View, List, Approve, Delete-any, Lock | View, List, Approve, Delete-any, Lock | Update-any, Delete-any |
| Thread (own) | n/a | Update-own (window), Delete-own | same | same | n/a | n/a | n/a |
| Replies | View, List | View, List, Create (subject to mod) | same | same | View, List, Approve, Delete-any | same | Update-any, Delete-any |
| Reply (own) | n/a | Update-own (window), Delete-own | same | same | n/a | n/a | n/a |
| Vote (up/down on thread or reply) | None | Create-own (1 per item, switchable) | same | same | View aggregate | View aggregate | View aggregate |
| Flair (assign to own thread) | None | Create-own | same | same | Update-any | same | same |
| Lock thread | None | None | None | None | Approve+Lock | same | same |
| Pin thread | None | None | None | None | None | Approve+Pin | same |

### 4.6 Marketplace

| Resource | Anonymous | Member | Realtor | Vendor | Mod | Op | Admin |
|---|---|---|---|---|---|---|---|
| Service (list, view) | View, List | View, List | View, List | View, List, Create-own | View, List | View, List | Update-any, Delete-any |
| Service (own) | n/a | n/a | n/a | Update-own, Delete-own (subject to mod re-check) | n/a | Suspend-any | same |
| Package (list, view) | View, List | View, List | View, List | View, List, Create-own | View, List | View, List | Update-any, Delete-any |
| Package (own) | n/a | n/a | n/a | Update-own, Delete-own | n/a | Suspend-any | same |
| Bundle (list, view) | View, List | View, List | View, List | View, List, Create-own | View, List | View, List | Update-any, Delete-any |
| Bundle (own) | n/a | n/a | n/a | Update-own, Delete-own | n/a | Suspend-any | same |
| Vendor profile (verified+approved, public) | View, List | View, List | View, List | View, List | View, List | View, List | View, List |
| Vendor profile (own) | n/a | n/a | n/a | Update-own | n/a | Suspend, Activate | Override |
| Realtor profile (verified, public) | View, List | View, List | View, List | View, List | View, List | View, List | View, List |
| Realtor profile (unverified — pending) | None | View-own | View-own | n/a | View-any | View-any | View-any |
| Realtor profile (own) | n/a | n/a | Update-own | n/a | n/a | Suspend, Activate | Override |
| Lead (sent by buyer) | None | Create (as buyer) | Create | Create | View-any (anonymized) | View-any | View-any |
| Lead (vendor side) | None | View-own as buyer | n/a | View-own as vendor, Update-status-own | View-any | View-any | View-any |
| LeadMessage | None | Create + View-own (party to lead only) | same | same (vendor party) | None | View-any (escalated) | View-any |
| Review | None | Create-once-per-Lead (post-completion, as buyer) | same | View-aggregate-own | Approve, Delete-any | same | same |
| All public review feeds | View, List | View, List | View, List | View, List | View, List | View, List | View, List |

### 4.7 Moderation & flagging

| Resource | Anonymous | Member | Realtor | Vendor | Mod | Op | Admin |
|---|---|---|---|---|---|---|---|
| Flag any UGC | None | Create | Create | Create | Create, View-any | Create, View-any | View-any |
| ModerationDecision | None | None | None | None | View-own-queue, Create | View-any, Create | Override (reason required) |
| Mod queue | None | None | None | None | View, Act | View, Act, Override | View, Act, Override |
| Moderation policies + rules | None | None | None | None | View | View, Update | Update |

### 4.8 AI tools (description writer, furniture remover)

| Resource | Anonymous | Member | Realtor | Vendor | Mod | Op | Admin |
|---|---|---|---|---|---|---|---|
| Tool landing pages | View | View | View | View | View | View | View |
| Run (execute) tool | None | Create (subject to rate limit + spend cap) | same | same | same | same, Disable-feature | same, Disable-feature |
| ToolUsage | None | View-own | View-own | View-own | View-aggregate | View-aggregate, Refund | Reset, Refund |
| Tool admin (toggle, raise cap) | None | None | None | None | None | Disable-feature | Update-config |

### 4.9 Realtor verification

| Resource | Anonymous | Member | Realtor | Vendor | Mod | Op | Admin |
|---|---|---|---|---|---|---|---|
| Submit verification (`POST /accounts/verify/`) | None | Submit-once (1 active) | already-verified | none | None | None | Override |
| LicenseCheck (per-call audit row) | None | View-own | View-own | n/a | View-any | View-any | re-verify (manual trigger) |

### 4.10 Audit

| Resource | Anonymous | Member | Realtor | Vendor | Mod | Op | Admin |
|---|---|---|---|---|---|---|---|
| ActionLog | None | None | None | None | None | View, List | Search, Export |
| AccessLog | None | None | None | None | None | View, List | Search, Export |
| Audit log purge | None | None | None | None | None | None | **Forbidden** (append-only by policy) |

### 4.11 Operations

| Resource | Anonymous | Member | Realtor | Vendor | Mod | Op | Admin |
|---|---|---|---|---|---|---|---|
| Operator dashboard | None | None | None | None | None | View | View |
| Business metrics dashboard | None | None | None | None | View (mod-relevant slices) | View | View |
| User management — list users | None | None | None | None | None | View, List | View, List |
| User management — suspend | None | None | None | None | None | Suspend (logged) | Suspend, Override |
| User management — role change | None | None | None | None | None | None | Update (logged) |
| User management — delete | None | None | None | None | None | None | **Soft-delete only** (hard-delete forbidden by policy) |

### 4.12 Django admin

| Resource | Anonymous | Member | Realtor | Vendor | Mod | Op | Admin |
|---|---|---|---|---|---|---|---|
| `/admin/` | None | None | None | None | None | None | View (post-2FA + IP allowlist) |
| All ModelAdmins | None | None | None | None | None | None | per `ModelAdmin.has_*_permission` |

### 4.13 Webhooks & system endpoints

| Resource | Anonymous | Member | Realtor | Vendor | Mod | Op | Admin |
|---|---|---|---|---|---|---|---|
| Postmark inbound webhook | Create (signed) | None | None | None | None | None | View logs |
| ARELLO callback (if configured) | Create (signed) | None | None | None | None | None | View logs |
| Sentry inbound | n/a (outbound only) | n/a | n/a | n/a | n/a | View dashboard | same |

---

## 5. URL → Permission Mapping

The pattern catalog reflects the post-Sprint-0b URL refactor: public read endpoints under `/api/public/v1/`, authenticated endpoints under `/api/v1/`. Next.js routes consume these.

### 5.1 Public read API (`/api/public/v1/`)

| URL | Method | DRF permission | Notes |
|---|---|---|---|
| `/api/public/v1/healthz/` | GET | `AllowAny` | Status |
| `/api/public/v1/healthz/deep/` | GET | `AllowAny` | Slower checks; same payload shape |
| `/api/public/v1/posts/` | GET | `AllowAny` | List published posts |
| `/api/public/v1/posts/<slug>/` | GET | `AllowAny` | View post |
| `/api/public/v1/posts/<slug>/comments/` | GET | `AllowAny` | List comments |
| `/api/public/v1/threads/` | GET | `AllowAny` | List threads |
| `/api/public/v1/threads/<slug>/` | GET | `AllowAny` | View thread + replies |
| `/api/public/v1/services/` | GET | `AllowAny` | List services |
| `/api/public/v1/services/<slug>/` | GET | `AllowAny` | View service + packages + bundles |
| `/api/public/v1/vendors/` | GET | `AllowAny` | List approved vendor profiles |
| `/api/public/v1/vendors/<slug>/` | GET | `AllowAny` | View vendor + reviews |
| `/api/public/v1/realtors/` | GET | `AllowAny` | List verified realtor profiles |
| `/api/public/v1/realtors/<slug>/` | GET | `AllowAny` | View realtor + posts |
| `/api/public/v1/categories/` | GET | `AllowAny` | Marketplace category tree |
| `/api/public/v1/tools/` | GET | `AllowAny` | List AI tool landing-page metadata |
| `/api/public/v1/sitemap.xml` | GET | `AllowAny` | Sitemap |
| `/api/public/v1/robots.txt` | GET | `AllowAny` | Robots |

### 5.2 Authenticated API (`/api/v1/`)

| URL | Method | Permission | Notes |
|---|---|---|---|
| `/api/v1/accounts/me/` | GET | `IsAuthenticated` | Current user |
| `/api/v1/accounts/me/` | PATCH | `IsAuthenticated` | Update own profile |
| `/api/v1/accounts/me/email/` | POST | `IsAuthenticated` | Change email (re-verify) |
| `/api/v1/accounts/2fa/setup/` | POST | `IsAuthenticated` | Enroll TOTP |
| `/api/v1/accounts/2fa/disable/` | POST | `IsAuthenticated & ~IsStaff` | Staff cannot disable |
| `/api/v1/accounts/verify/` | POST | `IsAuthenticated` | Submit license for ARELLO |
| `/api/v1/accounts/verify/status/` | GET | `IsAuthenticated` | Own verification status |
| `/api/v1/accounts/license-checks/` | GET | `IsAuthenticated` | Own LicenseCheck rows |
| `/api/v1/posts/` | POST | `IsRealtor \| IsAdmin` | Create post |
| `/api/v1/posts/<slug>/` | PATCH | `IsOwnerOrReadOnly & (IsRealtor \| IsOperator)` | Update |
| `/api/v1/posts/<slug>/` | DELETE | `IsOwnerOrReadOnly \| IsOperator \| IsAdmin` | Delete |
| `/api/v1/posts/<slug>/comments/` | POST | `IsAuthenticated & ~IsSuspended` | Create comment |
| `/api/v1/comments/<id>/` | PATCH | `IsOwnerWithinWindow \| IsModerator \| IsOperator` | Update (within 15 min if owner) |
| `/api/v1/comments/<id>/` | DELETE | `IsOwner \| IsModerator \| IsOperator \| IsAdmin` | Delete |
| `/api/v1/threads/` | POST | `IsAuthenticated & ~IsSuspended` | Create |
| `/api/v1/threads/<slug>/` | PATCH | `IsOwnerWithinWindow \| IsModerator \| IsOperator` | Update |
| `/api/v1/threads/<slug>/replies/` | POST | `IsAuthenticated & ~IsSuspended` | Reply |
| `/api/v1/threads/<slug>/lock/` | POST | `IsModerator \| IsOperator \| IsAdmin` | Lock |
| `/api/v1/votes/` | POST | `IsAuthenticated & ~IsSuspended` | Vote (idempotent per item) |
| `/api/v1/services/` | POST | `IsVendor` | Create service |
| `/api/v1/services/<slug>/` | PATCH | `IsOwner & IsVendor` | Update own |
| `/api/v1/services/<slug>/` | DELETE | `IsOwner & IsVendor` | Delete own |
| `/api/v1/services/<slug>/packages/` | POST | `IsOwner & IsVendor` | Add package |
| `/api/v1/packages/<id>/` | PATCH/DELETE | `IsOwner & IsVendor` | Update/delete own |
| `/api/v1/leads/` | POST | `IsAuthenticated & ~IsSuspended` | Send inquiry as buyer |
| `/api/v1/leads/` | GET | `IsAuthenticated` | Filtered by participation (buyer or vendor) |
| `/api/v1/leads/<id>/` | GET | `IsLeadParty \| IsOperator` | View if party or op |
| `/api/v1/leads/<id>/messages/` | POST | `IsLeadParty` | Reply |
| `/api/v1/leads/<id>/status/` | PATCH | `IsLeadVendor` | Vendor updates status |
| `/api/v1/reviews/` | POST | `IsLeadBuyer & LeadCompleted & NotPreviouslyReviewed` | Once per Lead |
| `/api/v1/flags/` | POST | `IsAuthenticated & ~IsSuspended` | Flag any UGC |
| `/api/v1/moderation/queue/` | GET | `IsModerator \| IsOperator` | Mod queue |
| `/api/v1/moderation/decisions/` | POST | `IsModerator \| IsOperator` | Decide on a flagged item |
| `/api/v1/moderation/decisions/<id>/override/` | POST | `IsAdmin` | Override |
| `/api/v1/tools/description-writer/run/` | POST | `IsAuthenticated & ~IsSuspended & WithinRateLimit & WithinSpendCap` | Run |
| `/api/v1/tools/furniture-remover/run/` | POST | same | Run |
| `/api/v1/tools/usage/me/` | GET | `IsAuthenticated` | Own usage |
| `/api/v1/tools/usage/aggregate/` | GET | `IsOperator \| IsAdmin` | Roll-up |
| `/api/v1/operations/dashboard/` | GET | `IsOperator \| IsAdmin` | Op dashboard data |
| `/api/v1/operations/users/` | GET | `IsOperator \| IsAdmin` | Search users |
| `/api/v1/operations/users/<id>/suspend/` | POST | `IsOperator \| IsAdmin` | Suspend |
| `/api/v1/operations/users/<id>/role/` | PATCH | `IsAdmin` | Role change |
| `/api/v1/audit/actions/` | GET | `IsOperator \| IsAdmin` | ActionLog |
| `/api/v1/audit/access/` | GET | `IsOperator \| IsAdmin` | AccessLog |

### 5.3 Webhooks (`/api/webhooks/`)

| URL | Method | Auth | Notes |
|---|---|---|---|
| `/api/webhooks/postmark/inbound/` | POST | Signed payload (HMAC) | Incoming email parsing |
| `/api/webhooks/postmark/bounce/` | POST | Signed payload | Bounce notifications |
| `/api/webhooks/arello/callback/` | POST | Signed payload | ARELLO async callback (if used) |

Unsigned or signature-mismatched webhooks → 401 + log to `audit.AccessLog` with `actor=None` and `note='unsigned_webhook'`.

### 5.4 Django admin (`/admin/`)

All admin URLs require:

1. `AdminIPAllowlistMiddleware` — request IP must be in `ADMIN_IP_ALLOWLIST` env var (CIDR list).
2. `is_superuser=True`.
3. `django-otp` verified TOTP token.

Per-model permissions controlled by `ModelAdmin.has_view_permission` / `has_change_permission` / `has_delete_permission`. Default deny on `ActionLog` and `AccessLog` for delete (append-only invariant).

---

## 6. DRF Permission Classes

Defined in `apps/core/permissions.py`. Each is unit-tested in `apps/core/tests/test_permissions.py`.

### 6.1 Built-in DRF

| Class | Use |
|---|---|
| `AllowAny` | Public reads under `/api/public/v1/`. |
| `IsAuthenticated` | Anything that requires a member. |

### 6.2 Custom

```python
class IsRealtor(BasePermission):
    """Verified WA realtor only."""
    def has_permission(self, request, view):
        u = request.user
        return (
            u.is_authenticated
            and hasattr(u, "realtor_profile")
            and u.realtor_profile.status == "verified"
        )


class IsVendor(BasePermission):
    """Approved marketplace vendor only."""
    def has_permission(self, request, view):
        u = request.user
        return (
            u.is_authenticated
            and hasattr(u, "vendor_profile")
            and u.vendor_profile.is_approved is True
        )


class IsModerator(BasePermission):
    def has_permission(self, request, view):
        u = request.user
        return u.is_authenticated and u.groups.filter(name="moderator").exists()


class IsOperator(BasePermission):
    def has_permission(self, request, view):
        u = request.user
        return u.is_authenticated and (
            u.groups.filter(name="operator").exists() or u.is_superuser
        )


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_superuser


class IsSuspended(BasePermission):
    """Inverse: True when user is suspended. Use with ~IsSuspended."""
    def has_permission(self, request, view):
        u = request.user
        return u.is_authenticated and getattr(u, "is_suspended", False)


class IsOwnerOrReadOnly(BasePermission):
    """Object-level: owner can write; everyone else reads only."""
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        owner = getattr(obj, "author", None) or getattr(obj, "user", None) or getattr(obj, "created_by", None)
        return owner == request.user


class IsOwnerWithinWindow(BasePermission):
    """Owner can write within the model's edit window."""
    window_seconds = 15 * 60
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        owner = getattr(obj, "author", None) or getattr(obj, "user", None)
        if owner != request.user:
            return False
        age = (timezone.now() - obj.created_at).total_seconds()
        return age <= self.window_seconds


class IsLeadParty(BasePermission):
    """Buyer or vendor on the lead."""
    def has_object_permission(self, request, view, obj):
        return request.user in (obj.buyer, obj.service.vendor.user)


class IsLeadBuyer(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj.buyer


class IsLeadVendor(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj.service.vendor.user


class WithinRateLimit(BasePermission):
    """Tool-run rate limit (per-user, per-tool, per-day)."""
    def has_permission(self, request, view):
        return rate_limit_ok(request.user, view.tool_slug)


class WithinSpendCap(BasePermission):
    """Daily spend cap."""
    def has_permission(self, request, view):
        return today_spend_usd() < settings.GEMINI_DAILY_SPEND_CAP_USD
```

### 6.3 Composition

DRF permission classes compose with `&`, `|`, `~`. Examples used in viewsets:

| ViewSet | `permission_classes` |
|---|---|
| Public post list | `[AllowAny]` |
| Authed comment create | `[IsAuthenticated & ~IsSuspended]` |
| Realtor blog write | `[IsRealtor \| IsAdmin]` |
| Comment update | `[IsOwnerWithinWindow \| IsModerator \| IsOperator]` |
| Mod queue | `[IsModerator \| IsOperator]` |
| Op dashboard | `[IsOperator \| IsAdmin]` |
| Override decision | `[IsAdmin]` |
| Lead message | `[IsAuthenticated & IsLeadParty]` |
| Tool run | `[IsAuthenticated & ~IsSuspended & WithinRateLimit & WithinSpendCap]` |

---

## 7. Object-Level Permissions

Object-level checks fire after class-level. Used wherever ownership matters.

| Resource | Owner field | Window for "self-update" | Notes |
|---|---|---|---|
| Post | `author` | None (always editable; mod re-runs on each save) | Drafts only readable by author + ops. |
| Comment | `author` | 15 min | After window: read-only to author; mods can still update/delete. |
| Thread | `author` | 15 min | Same shape. Locked threads disable all updates. |
| Reply | `author` | 15 min | Same. |
| Vote | `user` | n/a | Idempotent: re-creating with the same direction → no-op; opposite direction → flip. |
| Service | `vendor.user` | None | Update triggers mod re-check. |
| Package | `service.vendor.user` | None | Same. |
| Bundle | `service.vendor.user` | None | Same. |
| Lead | `buyer` (creator), `service.vendor.user` (recipient) | n/a | Lead is jointly visible to both parties. |
| LeadMessage | `sender` | n/a | Visible to both lead parties. |
| Review | `author` (= lead buyer) | None after publish | One per Lead, only after lead is `completed`. |
| Flag | `reporter` | n/a | Reporter sees own flags; mods see all. |
| ToolUsage | `user` | n/a | Self-view only; ops view aggregates. |
| RealtorProfile | `user` | None | Status changes require ARELLO verification or admin override. |
| VendorProfile | `user` | None | Approval is op/admin-only. |
| LicenseCheck | `realtor_profile.user` | n/a | Read-only to owner; append-only system-wide. |

---

## 8. Public Read Implementation

The URL split is the central enforcement mechanism.

### 8.1 `/api/public/v1/` — public reads

- `permission_classes = [AllowAny]` (default).
- ViewSets are `ReadOnlyModelViewSet` — only `GET` is wired.
- No JWT cookie required; authenticated requests are accepted but not differentiated (the same response body regardless of `request.user`).
- Caching headers: `Cache-Control: public, max-age=300, s-maxage=600` for list endpoints; `max-age=60, s-maxage=300` for detail. Caddy + Cloudflare cache aggressively.
- `ETag` + `Last-Modified` set via `django.views.decorators.http.last_modified`.
- Filtered to "published + approved" status. Drafts, pending-mod items, and removed items are excluded.

### 8.2 `/api/v1/` — authenticated

- `permission_classes` start with `IsAuthenticated` and add specifics.
- JWT cookie required: `httpOnly; SameSite=Strict; Secure` in prod; `Secure=False` in dev.
- CSRF: double-submit pattern. SimpleJWT cookie middleware verifies CSRF token on unsafe methods.
- `Cache-Control: no-store` on all responses.
- 401 (no JWT) and 403 (insufficient role) clearly distinguished — no information leak about resource existence.

### 8.3 Object-existence leak prevention

Returning 404 vs 403 can leak existence to unauthenticated users. The convention:

- Public read endpoints: 404 if not in the public set (regardless of whether a non-public copy exists).
- Authenticated endpoints: 403 if the user is authenticated but lacks role; 404 if the resource doesn't exist for them; 401 if not authenticated.
- Owner-only objects: prefer 404 over 403 when the requester is not the owner, to avoid confirming existence.

---

## 9. Rate Limits

Enforced by `django-axes` + DRF throttles + custom Redis counters.

| Surface | Rate | Bucket | Notes |
|---|---|---|---|
| Sign in | 5 attempts / 5 min / IP+user | django-axes | Locks the user for 30 min; staff gets a notification. |
| Sign up | 3 / hour / IP | DRF throttle | Plus reCAPTCHA on the form. |
| Password reset request | 3 / hour / email | DRF throttle | Generic success response regardless. |
| Comment create | 10 / hour / user | Redis counter | Plus mod queue gate. |
| Thread create | 5 / hour / user | Redis counter | |
| Reply create | 30 / hour / user | Redis counter | |
| Vote | 200 / hour / user | Redis counter | Idempotent re-votes count. |
| Lead create | 20 / day / user | Redis counter | Anti-spam. |
| Flag | 30 / day / user | Redis counter | High false-positive rate is preferable to under-flagging. |
| Tool run (description writer) | 20 / day / member | Redis counter (`WithinRateLimit`) | Higher caps for verified realtors via override. |
| Tool run (furniture remover) | 5 / day / member | Redis counter | Image-heavy; tighter cap. |
| Public read | 600 / min / IP | DRF anon throttle | High; meant to deflect scrapers, not real readers. |

Rate-limit hits → HTTP 429 with `Retry-After` header.

---

## 10. Audit Linkage

Each action either writes to `audit.ActionLog`, `audit.AccessLog`, both, or neither. The default is "writes log to ActionLog; reads log to AccessLog." Exceptions are below.

| Action category | ActionLog | AccessLog |
|---|---|---|
| Anonymous read of public resource | No | No (unless flagged path) |
| Authenticated read | No | Yes |
| Member write (post/comment/thread/reply/vote) | Yes | Yes |
| Vendor write (service/package/bundle) | Yes | Yes |
| Realtor profile update | Yes | Yes |
| License verify submission | Yes (also LicenseCheck) | Yes |
| Mod decision | Yes (with prior + new state) | Yes |
| Op suspend/activate | Yes (with reason) | Yes |
| Admin override | Yes (with reason — required field) | Yes |
| Tool run | Yes (also ToolUsage) | Yes |
| Webhook receipt | Yes (raw payload) | No (system actor) |
| Health check | No | No |
| Sign in / sign out | Yes | Yes |
| 2FA setup / disable | Yes | Yes |

`ActionLog` is append-only by policy (no DELETE permission, even for superuser). `AccessLog` has retention: detail rows older than 90 days are aggregated to daily roll-ups; raw rows are then dropped via the `prune_audit_log_retention` management command.

---

## 11. Edge Cases

### 11.1 Suspended users (`User.is_suspended=True`)

- Cannot sign in. Sign-in endpoint returns "This account is suspended. Email support@yakimaweb.com to appeal."
- Existing sessions / JWTs remain valid until expiry — the JWT middleware checks `is_suspended` on every request and returns 403 + clears cookies.
- Public reads are unaffected — anonymous reading is the default capability.
- Suspended Realtor profiles: badges hide; published posts remain (mod can hide individually).
- Suspended Vendor profiles: services hide from marketplace; existing leads stay visible to both parties.

### 11.2 Email-unverified users

- Account exists in `User`. `email_verified=False`.
- Reads: full anonymous + authenticated-public read access.
- Writes: blocked. Comment/thread/reply/vote/lead Create returns 403 with "Verify your email to participate. [Resend verification email]".
- Auto-resend: one click; rate-limited (3 / hour / user).
- After verification: full Member capabilities.

### 11.3 Realtor pending verification

- `RealtorProfile.status='pending'`.
- User is treated as Member for capability purposes.
- UI shows "Verification pending" banner with the expected timeline.
- Cannot publish blog posts (the `IsRealtor` check fails on `status != 'verified'`).
- Can edit the profile; re-submits the verification.
- ARELLO retries (Celery exponential backoff) up to 24h. If still pending after 24h: auto-email "We're still working on verifying. No action needed." Then daily emails through 7 days. After 7 days: status flips to `verification_failed` and ops review.

### 11.4 Vendor not approved

- `VendorProfile.is_approved=False`.
- User is treated as Member for capability purposes.
- Cannot create services. UI shows "Vendor application under review."
- Op/Admin reviews the application via the operator dashboard. Approval flips `is_approved=True`; rejection sends a templated email with reason and the user can re-apply after edits.

### 11.5 Multi-role users

- A user can be both Realtor and Vendor (a realtor selling photography). Both profiles attach to the single `User`.
- Permission classes are independent: `IsRealtor` checks `RealtorProfile`, `IsVendor` checks `VendorProfile`. A user holding both passes both.
- Mod and Op are Django groups; a user can be in both. Capability is the union.
- A staff user (Mod/Op/Admin) MUST have `is_staff=True` and 2FA enrolled (enforced by `DJANGO_OTP_REQUIRED_FOR_STAFF=True` in prod).

### 11.6 Locked threads / archived content

- Locked thread: replies disabled for all roles except Op/Admin (for moderation cleanup).
- Archived post: read-only for everyone including author; ops can unarchive with logged action.

### 11.7 Public profile visibility

- Verified realtor: profile public.
- Pending/failed realtor: profile **not public**; only the user themselves and Op/Admin can view.
- Approved vendor: profile public.
- Pending vendor: profile not public; user + Op/Admin only.
- Suspended (any): profile hidden from public listings; direct URL returns 404 to anonymous, 403 to authenticated members.

### 11.8 Deleted resources

- Comment delete → soft-delete (sets `is_deleted=True`, blanks `body`). Slot remains visible with "Removed" placeholder.
- Thread/reply delete → same shape.
- Post delete → soft-delete by author/op; admin hard-delete is reserved for legal removals only.
- User delete → never. Use suspend + (optionally) anonymize PII via `apps.accounts.tasks.anonymize_user`.

---

## 12. Change Control

Adding a new role:

1. ADR documenting why a new role is needed and what subset of capabilities it has.
2. Update §2 (Roles) of this doc.
3. Update §4 (matrix) — every relevant resource row gets a column update.
4. Add the Django group / permission class.
5. Add tests in `apps/<scope>/tests/test_permissions.py` covering each row that changed.
6. Update `apps/operations/services/role_definitions.py` if the operator dashboard needs to surface the role.

Adding a new permission:

1. ADR if the permission introduces new policy (ownership rules, time windows, etc.).
2. Add the permission class to `apps/core/permissions.py`.
3. Add unit tests covering pass + fail cases.
4. Wire into the relevant viewset.
5. Update §6.2 of this doc.

Removing a role or permission:

1. Document why in an ADR. Removals are rare.
2. Migration: rename or drop the Django group; reassign affected users to the closest equivalent role.
3. Update viewsets and tests.
4. Update §2 + §4.

Every change to this matrix lands as a single PR that updates the doc, the code, and the tests in lockstep. PR template includes a checkbox: "Updated ACCESS-MATRIX.md? — required if this PR touches auth/permissions/URL routing."

---

## 13. View Audit Checklist (Sprint 0b)

For each viewset / route in the codebase, confirm:

- [ ] Lives under the correct base (`/api/public/v1/` for public, `/api/v1/` otherwise).
- [ ] `permission_classes` is set (no implicit `IsAuthenticated` defaulting unintentionally to public).
- [ ] Class-level permissions match §4 (matrix) for the relevant resource.
- [ ] Object-level permissions use the right ownership predicate from §7.
- [ ] Drafts / pending / removed items are excluded from public list endpoints.
- [ ] Test coverage in `apps/<app>/tests/test_permissions.py` for: anon access, member access, owner access, non-owner-member access, mod access, op access, admin access. One test method per relevant cell of §4.
- [ ] Throttle class set per §9 if applicable.
- [ ] Audit logging fires per §10.

This checklist runs as part of the Sprint 0b PR review.

---

— *Yakima Real Estate Hub Engineering, 2026-05-03*
