import { isBackendReady } from "./helpers/health";

/**
 * Global setup: poll backend healthz until ready (best-effort).
 *
 * Tests that depend on real seed data assume:
 *   docker compose exec api python manage.py seed_all
 * has already been run.
 *
 * Set E2E_REQUIRE_BACKEND=1 to fail if backend is unreachable.
 */
export default async function globalSetup() {
  const ready = await isBackendReady(30_000);
  if (!ready && process.env.E2E_REQUIRE_BACKEND === "1") {
    throw new Error(
      "Backend not reachable on http://localhost:8000 — start it via `docker compose up -d api db redis`.",
    );
  }
}
