# Yakima Real Estate Hub — Project Vault

Dev-facing knowledge base. Open this directory in Obsidian. The canonical source
of truth remains [`docs/`](../) — entries here are summaries with `[[wikilinks]]`
that connect ADRs, sprints, decisions, and lessons.

## Map

- [[Architecture/Overview]] — system shape and the locked decisions
- [[Sprints/INDEX]] — sprint-by-sprint logbook
- [[Decisions/INDEX]] — the 9 ADRs as living references
- [[Security/INDEX]] — threat model, audit logs, incident reports
- [[People/INDEX]] — founders, contributors, key external contacts
- [[Vendors/INDEX]] — third-party services we depend on
- [[Lessons/INDEX]] — what we learned from each phase
- [[Templates/INDEX]] — reusable templates (sprint kickoff, ADR, retro, daily)

## Daily ops

- New daily note: ⌘⇧D (drops into `Daily/YYYY-MM-DD.md`)
- New sprint retro: copy [[Templates/Sprint-Retro]]
- New ADR proposal: copy [[Templates/ADR]]
- Search across vault: ⌘F

## How this vault stays current

After every sprint:
1. Append the sprint entry to [[Sprints/INDEX]]
2. Add `Sprints/sprint-N-name.md` with the deliverables and links
3. Update [[Architecture/Overview]] if the system shape changed
4. Add any new lessons to [[Lessons/INDEX]]
5. Cross-reference from `docs/STATE-OF-THE-PROJECT.md` in the canonical tree

The vault is **secondary documentation**. When in doubt, the markdown in `docs/`
wins. This vault optimizes for navigation and synthesis, not for being the
authoritative source.
