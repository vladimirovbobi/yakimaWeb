# Phase 4 — Forum (Reddit-shaped)

## Goal
Threads + replies + voting + flair + score-based ranking. Moderation hooks. No DMs (out of scope).

## Done
- [ ] `/community/` index — sorted by hot/new/top
- [ ] Thread create + reply (1-level threading like blog comments)
- [ ] Vote (up/down) — 1 vote per user per item, change-able
- [ ] Flair tags (Question / Discussion / Help / Local-news / Market) — pick from fixed list
- [ ] Hot ranking algorithm (Reddit-style: log10(score)/age_factor)
- [ ] Moderation: every thread + reply through pipeline
- [ ] Tests: model invariants, vote flip, ranking math
- [ ] 5 new prompt-injection fixtures

## Models
- `Flair` — slug, label, color
- `ForumThread(ModeratableMixin, TimeStampedModel)` — author, flair FK, title, body, score (denorm)
- `ForumReply(ModeratableMixin, TimeStampedModel)` — thread FK, author, body, parent FK
- `Vote` — Generic FK to thread or reply, voter, value (-1/+1)

## Skills: caveman, frontend-design (compact dense list), security-review
