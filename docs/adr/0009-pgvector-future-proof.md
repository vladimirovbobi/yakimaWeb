# ADR-0009: pgvector Schema Now, Semantic Search at v1.1

- **Status:** Accepted
- **Date:** 2026-05-03
- **Supersedes:** —
- **Superseded by:** —
- **Deciders:** Yakima Real Estate Hub Engineering
- **Tags:** database, search, ai, future-proofing

## Context

Yakima Real Estate Hub's content surface (Phases 2-5) ships three searchable models: `Post`, `ForumThread`, and `Service` (marketplace). The v1 search experience is keyword-driven: users typing "cash-out refinancing" expect the documents that contain those exact words. Postgres full-text search via `tsvector` columns is fully adequate for that — well-indexed FTS handles tens of millions of rows with sub-100 ms p95.

But the product roadmap explicitly calls out semantic search at v1.1. The user query "find me posts about cash-out refinancing for buyers in Selah" needs to surface a post titled "Equity-tap loans for first-time owners in the Lower Valley" even though those exact words don't co-occur. That's a vector-search problem, not an FTS one.

The decision in front of us is *when* to bring vector search into the schema:

- Bring the column in at v1: pay a small migration cost now, none at v1.1.
- Defer until v1.1: pay zero now, larger migration cost later (alter table on a production-loaded `Post`, `ForumThread`, `Service`).

ADR-0003 locks Gemini as the AI provider. Gemini's `text-embedding-004` produces 768-dim embeddings (Gemini also supports configurable output dim down to 256). The schema decision must accommodate an embedding model whose exact dim we'll commit to at activation time.

## Decision

Install the **pgvector extension** on Postgres in dev and prod. Add an `embedding` column to `Post`, `ForumThread`, and `Service` models in Sprint 0c, **nullable**, with an HNSW index. **No embedding generation runs in v1** — the column stays NULL across all rows until v1.1 activates a Celery task that computes embeddings on save and a search endpoint that toggles between FTS and cosine-similarity vector mode.

V1 search continues to use Postgres FTS via `tsvector`. The pgvector schema is groundwork only.

The dev compose file switches from `postgres:16-alpine` to `pgvector/pgvector:pg16` (which is just Postgres 16 with the extension preinstalled). Prod (Railway Postgres) supports the `vector` extension via `CREATE EXTENSION` — verified.

## Rationale

**Alternatives evaluated.**

| Option | Verdict | Notes |
|---|---|---|
| **Defer schema entirely until v1.1** | Rejected | Adding a vector column to a production-loaded `Post` table at v1.1 means an `ALTER TABLE ... ADD COLUMN ... DEFAULT NULL` (cheap) plus a backfill task to compute embeddings for every existing row. The schema add itself is fine; the backfill is what hurts. By having the column from v1, every new row ships embedding-ready, and the v1.1 task only has to backfill v1's content (a bounded one-time job rather than perpetual). |
| **Pinecone / Weaviate / Qdrant external service** | Rejected | Adds a third-party service ($/month at the lowest tier; another integration for the moderation pipeline; another secret; another point of failure; cross-service latency on every search). At our scale (10K MAU steady-state per the master plan), pgvector on the same Postgres instance handles the load without breaking a sweat. |
| **Postgres FTS only forever** | Rejected | Adequate for keyword search, completely inadequate for the semantic queries the v1.1 product brief calls out. Putting it off doesn't make the requirement go away; it just makes the v1.1 migration bigger. |
| **pgvector schema-ready, deferred activation (chosen)** | Accepted | Zero v1 ops cost (just a nullable column and an unused index). v1.1 migration is purely additive (a Celery task + a query mode toggle). Future-proof without committing to embedding model details until activation. |

**Why pgvector specifically.**

- Native Postgres extension; no separate service to operate, monitor, or pay for.
- Well-documented Django integration via `django-pgvector` (or raw SQL — both viable).
- HNSW index scales to ~1M vectors comfortably on a small Postgres instance; we'll be far under that at 10K MAU.
- Same Postgres instance means joins between FTS results and vector results are trivial (no cross-service joins, no eventual consistency).
- Backups, point-in-time recovery, replication — all the Postgres operational machinery applies to the vector data unchanged.

**Why nullable + index now, generation later.**

- Adding a column with `NULL` default is a metadata-only operation in modern Postgres — no table rewrite, no lock beyond the brief catalog update.
- An HNSW index on a NULL-only column has effectively zero cost (HNSW doesn't index NULLs in pgvector).
- When v1.1 lands, the only schema work is removing the nullable constraint (or not — null can mean "not yet embedded" forever).
- We don't have to commit to embedding dimensions today. The most-likely model (`gemini-embedding-001` / `text-embedding-004` family) outputs configurable dims. We pick at activation.

**Embedding model decision deferred.** Likely candidates at v1.1:

- Gemini `text-embedding-004` — fits ADR-0003, pay-per-call alongside our existing Gemini usage.
- OpenAI `text-embedding-3-small` — cheaper per token, requires onboarding a second AI provider.
- Open-source `bge-small-en-v1.5` via a hosted endpoint — costs more ops, zero per-call.

Recommend `text-embedding-004` with 768-dim output at activation time, but the column type is `vector` (variable dim per row is not supported, so dim is fixed at column creation; we'll set it once based on the chosen model — see implementation notes). If we change models post-v1.1, we drop and recompute; the schema design accommodates a single-shot recomputation.

**Why now and not later.**

- The marginal cost of the column + index in Sprint 0c is small (one migration, ~10 lines of Django model code per app, one compose-file image swap).
- The marginal cost of the same migration on a production-loaded `Post` table at v1.1 is the same metadata change *plus* a coordinated backfill, *plus* the cognitive cost of a multi-step migration plan.
- Front-loading the cheap part is a textbook future-proofing move: cheap to do early, expensive to do late.

## Consequences

### Positive
- v1.1 semantic search activation is purely additive: no schema migrations on hot tables.
- No new service to operate; pgvector lives in the existing Postgres.
- Single backup/restore covers vector data automatically.
- Joins between keyword (FTS) and semantic results are first-class SQL.
- Embedding model choice can be deferred without blocking v1.

### Negative
- Dev compose image is `pgvector/pgvector:pg16` instead of the more familiar `postgres:16-alpine` — one extra thing to know about.
- An unused column and index ship in v1; effectively zero cost but noisy in introspection tools.
- Locking the dim at column creation means a model change post-v1.1 requires a column drop + re-add (rare, one-shot operation).

### Neutral
- The `vector` type adds a third "specialty" Postgres feature alongside `tsvector` and `JSONB` already in use.
- Index choice (HNSW vs IVFFlat) is deferred to activation. HNSW is the modern default and uses more memory; IVFFlat is faster to build but slower to query. We'll benchmark at v1.1 with realistic data.

## Implementation notes

- **Sprint 0c migration** (`apps/content/migrations/00XX_pgvector_schema.py`):

  ```python
  from django.db import migrations
  from pgvector.django import VectorExtension, VectorField

  class Migration(migrations.Migration):
      dependencies = [("content", "00XX_previous")]
      operations = [
          VectorExtension(),  # CREATE EXTENSION IF NOT EXISTS vector
          migrations.AddField(
              model_name="post",
              name="embedding",
              field=VectorField(dimensions=768, null=True, blank=True),
          ),
          # raw SQL for HNSW index (django-pgvector 0.x exposes Index helpers; raw SQL is also fine)
          migrations.RunSQL(
              sql=(
                  "CREATE INDEX CONCURRENTLY IF NOT EXISTS post_embedding_hnsw_idx "
                  "ON content_post USING hnsw (embedding vector_cosine_ops);"
              ),
              reverse_sql="DROP INDEX IF EXISTS post_embedding_hnsw_idx;",
          ),
      ]
  ```

  Mirror for `apps/forum/models.py::ForumThread.embedding` and `apps/marketplace/models.py::Service.embedding`.

- **`pyproject.toml`**: add `pgvector` (the Python client + Django integration). Pin `pgvector>=0.3,<0.5`.

- **`docker-compose.yml`** (db service):

  ```yaml
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
  ```

- **Production (Railway)**: Railway's managed Postgres supports `CREATE EXTENSION vector;`. The migration runs on first deploy of Sprint 0c. No infrastructure work beyond the migration itself.

- **v1 search**: continues to use FTS. `apps/content/models.py::Post` keeps its `search_vector` (`SearchVectorField`) and trigger. `apps/content/api/views.py::PostSearchView` uses `SearchQuery` + `SearchRank`. The `embedding` column is invisible to v1 code paths.

- **v1.1 plan** (sketch, not in this ADR's scope):
  1. Celery task `apps.content.tasks.embed_post(post_id)` — calls Gemini `text-embedding-004`, writes to `embedding`, dispatches via `post_save` signal on `Post`.
  2. Backfill management command `python manage.py backfill_embeddings --model post --batch 100`.
  3. Search endpoint adds `?mode=semantic` — runs `embedding <=> query_embedding` (cosine distance) instead of FTS rank. Hybrid mode merges both with reciprocal rank fusion.

## Risks and mitigations

- **Risk:** `pgvector/pgvector:pg16` image diverges operationally from `postgres:16-alpine` (e.g., different config defaults). **Mitigation:** dev sanity test asserts `pg_isready` and `CREATE EXTENSION vector` succeed; CI runs the same image; documented in `docs/RUNBOOK.md`.
- **Risk:** The 768-dim choice ages out (a future Gemini model uses a different dim). **Mitigation:** dim is per-column; we can drop and re-create at v1.1 or v1.2 with a backfill task. Schema design assumes one-shot migration is acceptable for the rare model swap.
- **Risk:** HNSW index memory pressure at scale. **Mitigation:** HNSW is the right default for our scale (≤10K MAU implies ~hundreds of thousands of rows across all three models, well within HNSW comfort). If ever stressed, we re-evaluate IVFFlat. Benchmark gate at v1.1 activation.
- **Risk:** Schema change blocks a Phase 2 deploy. **Mitigation:** the migration uses `CREATE EXTENSION IF NOT EXISTS` and `CREATE INDEX CONCURRENTLY` — both run safely on a live database.

## Validation

The decision is validated when:
- Sprint 0c migration applies cleanly in dev and on Railway prod.
- `Post.embedding`, `ForumThread.embedding`, `Service.embedding` exist and accept NULL.
- HNSW index visible in `pg_indexes` on each table.
- v1 FTS search performance unchanged (no regression on EXPLAIN plans).
- Phase 2 ships with `embedding` column NULL across all rows; no v1 code path reads or writes it.

We revisit if: pgvector becomes unmaintained (unlikely; it's a Postgres-team-adjacent project); if Railway Postgres drops `vector` extension support; or if at v1.1 activation the volume actually demands a separate vector store (we'd run a 30-day pilot of pgvector first, hard data only).

## References

- Internal: `docs/adr/0003-gemini-as-ai-provider.md`, `docs/adr/0005-split-architecture.md`, `apps/content/models.py`, `apps/forum/models.py`, `apps/marketplace/models.py`, `docs/RUNBOOK.md`.
- External: pgvector README (github.com/pgvector/pgvector); `django-pgvector` integration; Gemini text embeddings API docs; HNSW algorithm paper (Malkov & Yashunin, 2016); reciprocal rank fusion for hybrid search.
