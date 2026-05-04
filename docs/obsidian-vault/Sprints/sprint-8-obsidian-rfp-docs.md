---
sprint: 8
title: Obsidian vault + RFP + doc completion
status: done
date: 2026-05-04
plan_file: .planning/phases/sprint-8-obsidian-rfp-docs/PLAN.md
---

# Sprint 8 — Obsidian vault + RFP + docs

## Goal

Build a dev-facing knowledge base (Obsidian vault) for the project and
fill in the missing enterprise doc (RFP).

## What landed

### Obsidian vault ([docs/obsidian-vault/](../../))

- `.obsidian/` config — dark theme, workspace layout, hotkeys
- Top-level [README](../../README.md) with map of the vault
- [Architecture/Overview](../Architecture/Overview.md) — locked decisions, system shape, container topology, code-tree map
- [Decisions/INDEX](../Decisions/INDEX.md) — backlinks to all 11 ADRs
- [Sprints/INDEX](../Sprints/INDEX.md) — logbook with status per sprint
- [Security/INDEX](../Security/INDEX.md) — non-negotiables + per-sprint audits
- [Vendors/INDEX](../Vendors/INDEX.md) — third-party deps + failure modes
- [People/INDEX](../People/INDEX.md) — roles + seed accounts
- [Lessons/INDEX](../Lessons/INDEX.md) — what we learned per phase
- [Templates/](../Templates/) — Sprint-Retro, ADR, Daily, Security-Audit

The vault is **secondary** documentation — `docs/` remains canonical. The
vault uses `[[wikilinks]]` to navigate; canonical docs are hard-linked.

### Enterprise docs

- [docs/RFP.md](../../../RFP.md) — NEW. Vendor-facing scope document with
  10 sections: project overview, scope of engagements, success criteria,
  milestones, vendor expectations (technical + communication + IP +
  security), selection process, IP terms, termination, submission, versioning.
- Existing launch docs (BETA-PROGRAM, CRISIS-RESPONSE, STATUS-PAGE,
  LAUNCH-CHECKLIST, PRESS-KIT) already substantive — no rewrite needed
  per Sprint 8 audit.
- Existing research docs (ARELLO API, eBay UX teardown, Fiverr UX
  teardown) already done.

## What's deferred

- Pre-wiring backlinks from every ADR-NNNN to the vault — repetitive
  busywork; the index handles discoverability for now.
- Templater plugin / Dataview plugin install in `.obsidian/community-plugins.json`
  — vault is usable without them.

## Cross-links

- Predecessor: [[sprint-7-bff]]
- Successor: [[sprint-9-e2e-security]]
