import { request } from "@playwright/test";

const BACKEND_URL = process.env.E2E_BACKEND_URL || "http://localhost:8000";
const HEALTH_PATH = "/api/public/v1/meta/healthz/";

/**
 * Polls the backend `/healthz` endpoint until 200 or timeout.
 * Returns true if backend is reachable, false otherwise.
 */
export async function isBackendReady(timeoutMs = 30_000): Promise<boolean> {
  const ctx = await request.newContext();
  const start = Date.now();
  let lastStatus = 0;

  try {
    while (Date.now() - start < timeoutMs) {
      try {
        const res = await ctx.get(`${BACKEND_URL}${HEALTH_PATH}`, {
          timeout: 5_000,
        });
        lastStatus = res.status();
        if (res.ok()) return true;
      } catch {
        // ignore, retry
      }
      await new Promise((r) => setTimeout(r, 1_000));
    }
    // eslint-disable-next-line no-console
    console.warn(
      `[e2e] Backend not ready after ${timeoutMs}ms (last status ${lastStatus})`,
    );
    return false;
  } finally {
    await ctx.dispose();
  }
}
