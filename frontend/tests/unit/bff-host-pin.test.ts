/**
 * SEC-013 host-pin: assertUpstreamHost must reject any URL whose host drifts
 * away from the pinned INTERNAL_API_BASE_URL host. Path-traversal is already
 * blocked in `buildTargetPath`; this is the second-line defense.
 */
import { describe, expect, it, beforeAll } from "vitest";

let assertUpstreamHost: typeof import("@/app/api/bff/[id]/route").assertUpstreamHost;
let UpstreamHostMismatch: typeof import("@/app/api/bff/[id]/route").UpstreamHostMismatch;

beforeAll(async () => {
  // INTERNAL_API_BASE_URL is read at module load. Set it before import.
  process.env.INTERNAL_API_BASE_URL = "http://api:8000";
  const mod = await import("@/app/api/bff/[id]/route");
  assertUpstreamHost = mod.assertUpstreamHost;
  UpstreamHostMismatch = mod.UpstreamHostMismatch;
});

describe("BFF upstream host pin", () => {
  it("accepts a URL on the pinned host", () => {
    expect(() =>
      assertUpstreamHost("http://api:8000/api/v1/leads/"),
    ).not.toThrow();
  });

  it("rejects an attacker-controlled host", () => {
    expect(() =>
      assertUpstreamHost("http://evil.example/api/v1/leads/"),
    ).toThrow(UpstreamHostMismatch);
  });

  it("rejects a unparseable URL", () => {
    expect(() => assertUpstreamHost("not-a-url")).toThrow(UpstreamHostMismatch);
  });

  it("rejects a same-path-different-host drift", () => {
    expect(() =>
      assertUpstreamHost("http://api.attacker.local:8000/api/v1/leads/"),
    ).toThrow(UpstreamHostMismatch);
  });
});
