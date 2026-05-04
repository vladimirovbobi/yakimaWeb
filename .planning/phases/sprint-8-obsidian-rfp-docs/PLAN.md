# Sprint 8 — Obsidian Vault + RFP + Doc Completion (NEW)

> Predecessor: Sprint 7. Master plan: `C:\Users\vladi\.claude\plans\i-want-you-to-validated-brook.md`.

## Goal

Dev-facing knowledge base via Obsidian + complete the missing enterprise doc set.

## Tasks

1. **Obsidian vault.** New `docs/obsidian-vault/` directory.
   - `.obsidian/` config: dark theme, Templater plugin enabled, Dataview plugin enabled, hotkeys for daily-note + new-ADR.
   - Vault structure:
     - `Architecture/` — links to ADRs, system diagrams, tech-decision rationale
     - `Decisions/` — one note per ADR with [[wikilinks]]
     - `Sprints/` — one note per sprint with retro template
     - `People/` — team + key vendors + key users
     - `Vendors/` — third-party vendor relationships (ARELLO, Gemini, Postmark, R2, Sentry, Cloudflare)
     - `Lessons/` — incident write-ups and lessons learned
     - `Templates/` — sprint-kickoff template, ADR template, retro template
   - Pre-wire backlinks: each `Decisions/ADR-NNNN.md` stub links to the canonical `docs/adr/NNNN-*.md` and to relevant `Sprints/` notes.
   - Decision: vault is **secondary** — canonical source remains `docs/`. Vault entries are summaries with [[backlinks]], not copies.

2. **`docs/RFP.md` — write the missing RFP.** Sections:
   - Project overview & vision
   - Scope (in/out)
   - Success criteria + KPIs
   - Milestones + delivery cadence
   - Vendor expectations (technical, communication, IP, security)
   - Selection process + timeline
   - IP terms + licensing
   - Termination + dispute resolution
   - Submission guidelines

3. **Complete skeleton enterprise docs:**
   - `docs/launch/BETA-PROGRAM.md` (currently skeleton)
   - `docs/launch/CRISIS-RESPONSE.md` (currently skeleton)
   - `docs/launch/STATUS-PAGE.md` (currently skeleton)
   - `docs/SECURITY-FINAL.md` (currently half — fill Sprint 2 polish results)

4. **Complete half-done research notes:**
   - `docs/research/arello-api-notes.md` — fill from real ARELLO integration learnings
   - `docs/research/marketplace-patterns/ebay-ux-teardown.md` — finish patterns analysis
   - `docs/research/marketplace-patterns/fiverr-ux-teardown.md` — finish patterns analysis

## Verification

- Obsidian vault opens cleanly in Obsidian app; backlinks resolve; templates work
- RFP doc covers all 9 sections
- Every skeleton/half doc reaches "done" state
- pytest + ruff + djlint clean (docs don't affect those but worth confirming nothing broke)

## Sign-off

- [ ] Obsidian vault structure in place with `.obsidian/` config
- [ ] All ADRs have backlink stubs in vault
- [ ] RFP doc complete
- [ ] 4 launch + security docs complete
- [ ] 3 research docs complete
- [ ] Sprint 8 commit pushed
