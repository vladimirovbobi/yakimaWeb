# ARELLO API Notes (Licensee Verification Service v2)

> Source: https://www.arello.com/information.cfm + LVWS v2 docs PDF
> Status: pre-sandbox. Schema below is from public docs; confirm exact field names with sandbox response.

## What ARELLO is
Association of Real Estate License Law Officials. Centralized database of US + Canadian real estate licensees (~3M records). Updated daily from state agencies. Their LVWS (License Verification Web Service) v2 is REST/JSON.

## Vendor contact
- Email: support@arello.org
- Phone: 312-300-4800
- Pricing: ~$300/mo base; volume tiers negotiable
- Docs PDF: https://www.arello.com/docs/ARELLO-LVWSv2-Documentation.pdf
- Sandbox: requested via support email

## Endpoints (expected — confirm with sandbox)

### Search by license number + jurisdiction
```
GET /api/v2/search?jurisdiction=WA&license_number=12345&last_name=Smith
Authorization: Bearer <API_KEY>
```

Expected response shape (200):
```json
{
  "results": [{
    "license_number": "12345",
    "jurisdiction": "WA",
    "license_type": "BROKER",
    "status": "ACTIVE",
    "first_name": "Jane",
    "last_name": "Smith",
    "issue_date": "2022-03-15",
    "expiration_date": "2026-03-14",
    "city": "Yakima",
    "discipline": null
  }],
  "count": 1,
  "checked_at": "2026-05-03T14:32:11Z"
}
```

Status values: `ACTIVE`, `EXPIRED`, `SUSPENDED`, `REVOKED`, `INACTIVE`, `SURRENDERED`
License types in WA: `BROKER`, `MANAGING_BROKER`, `DESIGNATED_BROKER`, `BRANCH_MANAGER`, `REAL_ESTATE_FIRM`

### Bulk search (post-MVP)
```
POST /api/v2/bulk_search
Body: { "jurisdiction": "WA", "license_numbers": ["12345", "12346", ...] }
```

## Sandbox curl example
```bash
# Once sandbox key is granted:
curl -H "Authorization: Bearer SANDBOX_KEY" \
     "https://lvws-sandbox.arello.com/api/v2/search?jurisdiction=WA&license_number=999999"
```

## Failure modes + handling

| Status | Cause | Our action |
|---|---|---|
| 200 + count=0 | License not found | `verification_status='not_found'`; surface "We couldn't find that license number — please double-check or contact support" |
| 200 + status=ACTIVE | Verified | Set `verification_status='verified'`, `verified_at=now`, grant `is_realtor=True` |
| 200 + status=EXPIRED/SUSPENDED/REVOKED | Disqualifying | Set status accordingly; revoke `is_realtor` if previously granted; email user |
| 401/403 | API key invalid | Alert ops; fail-soft (queue for retry) — never reject signup |
| 429 | Rate limited | Exponential backoff via Celery retry |
| 5xx | ARELLO down | Queue with retry; signup proceeds in `pending` state |
| Timeout (>10s) | Network | Same as 5xx |

## Re-verification cadence
- Initial check: synchronous on signup (≤2s budget; if exceeds → background)
- Recurring: Celery beat every 30 days for all `verified` realtors
- WA renewal cycle: 2 years; expiration date stored, beat task escalates to weekly checks within 60 days of expiration

## Privacy / Data handling
- License numbers are public records (DOL lookup is public). Storing them is fine.
- Full ARELLO response stored as JSONB in `LicenseCheck.raw_response` for audit defense
- Realtor disputes: ops can review raw response chronology in admin

## Implementation skeleton (apps/accounts/services/arello.py)

```python
import dataclasses
import requests
from django.conf import settings
from typing import Literal

@dataclasses.dataclass
class LicenseRecord:
    license_number: str
    jurisdiction: str
    license_type: str
    status: Literal['ACTIVE','EXPIRED','SUSPENDED','REVOKED','INACTIVE','SURRENDERED','NOT_FOUND']
    first_name: str
    last_name: str
    expiration_date: str | None
    raw: dict

class ARelloError(Exception): pass
class ARelloRateLimited(ARelloError): pass
class ARelloDown(ARelloError): pass

def verify_license(license_number: str, last_name: str = "", jurisdiction: str = "WA") -> LicenseRecord:
    url = f"{settings.ARELLO_BASE_URL}/api/v2/search"
    headers = {"Authorization": f"Bearer {settings.ARELLO_API_KEY}"}
    params = {"jurisdiction": jurisdiction, "license_number": license_number}
    if last_name:
        params["last_name"] = last_name

    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
    except requests.RequestException as e:
        raise ARelloDown(str(e))

    if r.status_code == 429:
        raise ARelloRateLimited()
    if r.status_code >= 500:
        raise ARelloDown(f"HTTP {r.status_code}")
    if r.status_code != 200:
        raise ARelloError(f"HTTP {r.status_code}: {r.text[:200]}")

    data = r.json()
    if data.get("count", 0) == 0:
        return LicenseRecord(
            license_number=license_number, jurisdiction=jurisdiction,
            license_type="", status="NOT_FOUND", first_name="", last_name=last_name,
            expiration_date=None, raw=data
        )
    rec = data["results"][0]
    return LicenseRecord(
        license_number=rec["license_number"],
        jurisdiction=rec["jurisdiction"],
        license_type=rec["license_type"],
        status=rec["status"],
        first_name=rec.get("first_name", ""),
        last_name=rec.get("last_name", ""),
        expiration_date=rec.get("expiration_date"),
        raw=rec,
    )
```

## Test fixtures (apps/accounts/tests/fixtures/arello/)
- `active_broker.json`
- `expired_managing_broker.json`
- `suspended_broker.json`
- `revoked_broker.json`
- `not_found.json`
- `rate_limited.json` (429 body)
- `server_error.json` (500 body)

Use `responses` or `httpretty` library to mock requests.

## Open items
- [ ] Get sandbox API key
- [ ] Confirm exact field names (some docs refer to `agent_status` vs `status`)
- [ ] Confirm rate limits
- [ ] Confirm whether discipline records are inline or separate endpoint
