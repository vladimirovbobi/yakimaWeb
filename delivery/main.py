"""FastAPI app for the Delivery service. Mounted under /api/delivery/."""
from __future__ import annotations

import datetime as dt
import hashlib
import logging
from typing import Any

import httpx
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from auth import AuthenticatedUser, auth_dependency
from config import get_settings
from db import (
    DeliveryAccessLog,
    DeliveryFile,
    DeliveryPackage,
    get_session,
)
from storage import get_storage
from validation import validate_upload


log = logging.getLogger("delivery")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI(
    title="Yakima Web — Delivery Service",
    version="1.0.0",
    docs_url=None,        # closed in prod; flip via env when iterating
    redoc_url=None,
    openapi_url=None,
)


# ────────────────────────────────────────────────────────────────────────────
# Healthz + root
# ────────────────────────────────────────────────────────────────────────────
@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok", "service": get_settings().service_name}


# ────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────
async def _get_package_or_404(session: AsyncSession, package_id: int) -> DeliveryPackage:
    pkg = (await session.execute(
        select(DeliveryPackage).where(DeliveryPackage.id == package_id)
    )).scalar_one_or_none()
    if pkg is None:
        raise HTTPException(status_code=404, detail="package_not_found")
    return pkg


def _enforce_vendor_owner(pkg: DeliveryPackage, user: AuthenticatedUser) -> None:
    if pkg.vendor_id != user.user_id:
        raise HTTPException(status_code=403, detail="not_owner")


def _enforce_buyer_owner(pkg: DeliveryPackage, user: AuthenticatedUser) -> None:
    if pkg.buyer_id != user.user_id:
        raise HTTPException(status_code=403, detail="not_buyer")


async def _log_access(
    session: AsyncSession,
    *,
    package_id: int,
    file_id: int | None,
    user_id: int,
    action: str,
    request: Request,
) -> None:
    session.add(DeliveryAccessLog(
        package_id=package_id,
        file_id=file_id,
        user_id=user_id,
        action=action,
        ip_addr=request.client.host if request.client else "",
        user_agent=(request.headers.get("user-agent") or "")[:240],
    ))


# ────────────────────────────────────────────────────────────────────────────
# Vendor: create package
# ────────────────────────────────────────────────────────────────────────────
@app.post("/api/delivery/v1/packages")
async def create_package(
    lead_id:  int = Form(...),
    buyer_id: int = Form(...),
    name:     str = Form("Delivery"),
    note:     str = Form(""),
    user:     AuthenticatedUser = Depends(auth_dependency),
    session:  AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    if not user.is_vendor:
        raise HTTPException(status_code=403, detail="vendor_only")

    pkg = DeliveryPackage(
        lead_id=lead_id,
        vendor_id=user.user_id,
        buyer_id=buyer_id,
        name=name[:240],
        note=note,
        status="open",
    )
    session.add(pkg)
    await session.flush()
    await session.commit()
    return {"package_id": pkg.id, "status": pkg.status}


# ────────────────────────────────────────────────────────────────────────────
# Vendor: upload a file
# ────────────────────────────────────────────────────────────────────────────
@app.post("/api/delivery/v1/packages/{package_id}/files")
async def upload_file(
    package_id: int,
    request:    Request,
    file:       UploadFile = File(...),
    user:       AuthenticatedUser = Depends(auth_dependency),
    session:    AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    pkg = await _get_package_or_404(session, package_id)
    _enforce_vendor_owner(pkg, user)
    if pkg.status != "open":
        raise HTTPException(status_code=400, detail="package_not_open")

    # Stream, then validate. We avoid streaming-validation because magic-byte
    # sniff needs the front of the file. For very large archives, we cap at
    # 500 MB before hitting validation.
    payload = await file.read()
    s = get_settings()
    if len(payload) > s.max_file_size_archive:
        raise HTTPException(status_code=400, detail="file_too_large")

    result = validate_upload(file.filename or "blob", payload)
    if not result.allowed:
        raise HTTPException(status_code=400, detail=f"invalid_file:{result.reason}")

    sha = hashlib.sha256(payload).hexdigest()
    storage = get_storage()
    key = storage.make_key(package_id, file.filename or "blob")
    storage.put(key, payload, file.content_type or "application/octet-stream")

    df = DeliveryFile(
        package_id=package_id,
        filename=(file.filename or "blob")[:240],
        content_type=(file.content_type or "application/octet-stream")[:80],
        size_bytes=len(payload),
        sha256=sha,
        storage_path=key,
        scan_status="skipped",  # img-worker AV scan dispatch is a Sprint 9 follow-up
    )
    session.add(df)
    await _log_access(
        session,
        package_id=package_id,
        file_id=None,  # set after flush
        user_id=user.user_id,
        action="upload",
        request=request,
    )
    await session.flush()
    await session.commit()
    return {
        "file_id":      df.id,
        "filename":     df.filename,
        "size_bytes":   df.size_bytes,
        "sha256":       df.sha256,
        "category":     result.category,
    }


# ────────────────────────────────────────────────────────────────────────────
# Vendor: finalize package
# ────────────────────────────────────────────────────────────────────────────
@app.post("/api/delivery/v1/packages/{package_id}/finalize")
async def finalize_package(
    package_id: int,
    request:    Request,
    user:       AuthenticatedUser = Depends(auth_dependency),
    session:    AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    pkg = await _get_package_or_404(session, package_id)
    _enforce_vendor_owner(pkg, user)
    if pkg.status == "finalized":
        return {"status": "already_finalized"}

    await session.execute(
        update(DeliveryPackage)
        .where(DeliveryPackage.id == package_id)
        .values(status="finalized", finalized_at=dt.datetime.utcnow())
    )
    await _log_access(
        session,
        package_id=package_id,
        file_id=None,
        user_id=user.user_id,
        action="finalize",
        request=request,
    )
    await session.commit()

    # Webhook back to Django so it can flip Lead.status to 'won'.
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                get_settings().django_webhook_url,
                json={
                    "package_id": package_id,
                    "lead_id":    pkg.lead_id,
                    "vendor_id":  pkg.vendor_id,
                    "buyer_id":   pkg.buyer_id,
                },
                headers={"X-Webhook-Source": "delivery"},
            )
    except Exception:  # webhook failures are non-fatal
        log.exception("django webhook failed for package %d", package_id)

    return {"status": "finalized", "package_id": package_id}


# ────────────────────────────────────────────────────────────────────────────
# Buyer: manifest
# ────────────────────────────────────────────────────────────────────────────
@app.get("/api/delivery/v1/packages/{package_id}/manifest")
async def manifest(
    package_id: int,
    request:    Request,
    user:       AuthenticatedUser = Depends(auth_dependency),
    session:    AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    pkg = await _get_package_or_404(session, package_id)
    if user.user_id not in (pkg.buyer_id, pkg.vendor_id) and not user.is_staff:
        raise HTTPException(status_code=403, detail="not_authorized")
    if pkg.status != "finalized" and user.user_id == pkg.buyer_id:
        raise HTTPException(status_code=409, detail="not_yet_finalized")

    files = (await session.execute(
        select(DeliveryFile).where(DeliveryFile.package_id == package_id)
    )).scalars().all()

    await _log_access(
        session,
        package_id=package_id,
        file_id=None,
        user_id=user.user_id,
        action="manifest",
        request=request,
    )
    await session.commit()

    return {
        "package_id":  pkg.id,
        "name":        pkg.name,
        "note":        pkg.note,
        "status":      pkg.status,
        "finalized_at": pkg.finalized_at.isoformat() if pkg.finalized_at else None,
        "files": [
            {
                "id":         f.id,
                "filename":   f.filename,
                "size_bytes": f.size_bytes,
                "content_type": f.content_type,
                "sha256":     f.sha256,
                "scan_status": f.scan_status,
            }
            for f in files
        ],
    }


# ────────────────────────────────────────────────────────────────────────────
# Buyer: signed download URL
# ────────────────────────────────────────────────────────────────────────────
@app.get("/api/delivery/v1/packages/{package_id}/files/{file_id}")
async def download_file(
    package_id: int,
    file_id:    int,
    request:    Request,
    user:       AuthenticatedUser = Depends(auth_dependency),
    session:    AsyncSession = Depends(get_session),
):
    pkg = await _get_package_or_404(session, package_id)
    if user.user_id not in (pkg.buyer_id, pkg.vendor_id) and not user.is_staff:
        raise HTTPException(status_code=403, detail="not_authorized")
    if pkg.status != "finalized" and user.user_id == pkg.buyer_id:
        raise HTTPException(status_code=409, detail="not_yet_finalized")

    f = (await session.execute(
        select(DeliveryFile).where(
            DeliveryFile.id == file_id,
            DeliveryFile.package_id == package_id,
        )
    )).scalar_one_or_none()
    if f is None:
        raise HTTPException(status_code=404, detail="file_not_found")

    storage = get_storage()
    url = storage.signed_url(f.storage_path, get_settings().signed_url_ttl_seconds)

    await _log_access(
        session,
        package_id=package_id,
        file_id=f.id,
        user_id=user.user_id,
        action="download",
        request=request,
    )
    await session.commit()
    return RedirectResponse(url=url, status_code=302)


# ────────────────────────────────────────────────────────────────────────────
# Vendor: access log
# ────────────────────────────────────────────────────────────────────────────
@app.get("/api/delivery/v1/packages/{package_id}/access-log")
async def access_log(
    package_id: int,
    user:       AuthenticatedUser = Depends(auth_dependency),
    session:    AsyncSession = Depends(get_session),
    limit:      int = 100,
    offset:     int = 0,
) -> dict[str, Any]:
    pkg = await _get_package_or_404(session, package_id)
    _enforce_vendor_owner(pkg, user)
    rows = (await session.execute(
        select(DeliveryAccessLog)
        .where(DeliveryAccessLog.package_id == package_id)
        .order_by(DeliveryAccessLog.created_at.desc())
        .offset(max(0, int(offset)))
        .limit(max(1, min(int(limit), 500)))
    )).scalars().all()
    return {
        "results": [
            {
                "id":         r.id,
                "user_id":    r.user_id,
                "action":     r.action,
                "ip_addr":    r.ip_addr,
                "user_agent": r.user_agent,
                "file_id":    r.file_id,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ],
    }


# CORS — allow Next.js origin in dev. Production runs behind Caddy on the
# same host so CORS isn't strictly needed but doesn't hurt.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    allow_credentials=True,
)


@app.exception_handler(HTTPException)
async def http_exc_handler(_request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type":   "about:blank",
            "title":  exc.detail if isinstance(exc.detail, str) else "error",
            "status": exc.status_code,
        },
    )
