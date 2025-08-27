# CVLR Backend (FastAPI + Postgres + pgvector)

Minimal backend for a Shotdeck-style app with:

- Shot-level data model
- Fuzzy tag search (name + slug) using pg_trgm
- Optional vector search on shots.embedding via pgvector
- Decks for saving shots
- Clean seams to add comments and search logs later

## Stack

- **FastAPI** • **SQLAlchemy 2.x** • **Alembic**
- **PostgreSQL 16** • **pgvector** • **pg_trgm**
- **Python 3.11**

## Quick Start

```bash
cp env.example .env
docker compose up -d

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

alembic upgrade head

# optional: seed demo rows
python -m scripts.seed

# run api
uvicorn app.main:app --reload
```

Health check:

```
GET /health -> { "ok": true }
```

## Schema (MVP-lite)

```
videos
  id PK, title, src_url, created_at

shots
  id PK, video_id FK -> videos.id
  t_start_ms, t_end_ms, thumb_url
  embedding VECTOR(768) NULL
  created_at
  IDX (video_id, t_start_ms)
  IVFFlat(embedding vector_cosine_ops) WITH (lists=150)

tags
  id PK, slug UNIQUE, name
  GIN(name gin_trgm_ops), GIN(slug gin_trgm_ops)

shot_tags
  PK (shot_id, tag_id)
  FK shot_id -> shots.id
  FK tag_id -> tags.id
  IDX (shot_id), (tag_id)

decks
  id PK, user_id, title, created_at
  IDX (user_id)

deck_items
  PK (deck_id, shot_id)
  FK deck_id -> decks.id ON DELETE CASCADE
  FK shot_id -> shots.id ON DELETE CASCADE
  IDX (deck_id, sort_order)
```

Future tables (not included yet): `comments`, `search_logs`.

## Search

### Fuzzy Tag Search

Endpoint: `GET /tags?query=...&threshold=0.2&page=1&page_size=24`

Uses trigram similarity on name and slug; sorts by max similarity.

`GET /shots?tag_query=...` returns shots having any tag whose similarity ≥ threshold.

### Vector Recall (Optional)

Endpoint: `GET /shots?q=...&top_k=200`

Text is embedded to a vector (pluggable). Default mock embedder if `EMBEDDER=mock`.

ANN query: `ORDER BY embedding <-> :query_vec LIMIT :top_k`.

If tags also provided:

- `hybrid=true` (default): intersect ANN candidates with tag matches.
- `hybrid=false`: union and de-dup.

### Pagination

`page` (default 1), `page_size` (default 24, max 60).

## API Overview

### Shots & Search

- `GET /shots`
  - Params: `q`, `top_k`, `tag_slugs[]`, `tag_query`, `threshold`, `hybrid`, `page`, `page_size`

- `GET /shots/{id}`
  - Returns shot + video + tags + "more like this" if embedding present.

### Tags

- `GET /tags`
  - Params: `query`, `threshold`, `page`, `page_size`

- `POST /tags`
  - Body: `{ "slug": "...", "name": "..." }`

- `PUT /tags/{id}`
  - Body: `{ "slug": "...?", "name": "...?" }`

### Decks

- `GET /decks?user_id=...`

- `POST /decks`
  - Body: `{ "user_id": 1, "title": "My Deck" }`

- `POST /decks/{deck_id}/items`
  - Body: `{ "shot_id": 123, "sort_order": 10 }`

- `DELETE /decks/{deck_id}/items/{shot_id}`

- `PUT /decks/{deck_id}/items/reorder`
  - Body: `[ { "shot_id": 1, "sort_order": 0 }, ... ]`

### Videos

- `POST /videos`
  - Body: `{ "title": "...", "src_url": "..." }`

- `GET /videos/{id}`

### Health

- `GET /health`

## Indices & Extensions

Enable extensions in the initial migration:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

Create indices:

```sql
-- Ann index for embeddings (adjust lists as data grows)
CREATE INDEX IF NOT EXISTS shot_embedding_ivfflat
ON shots USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 150);

-- Fuzzy search on tag name and slug
CREATE INDEX IF NOT EXISTS tag_name_trgm ON tags USING gin (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS tag_slug_trgm ON tags USING gin (slug gin_trgm_ops);

-- Common filters
CREATE INDEX IF NOT EXISTS idx_shots_video_time ON shots (video_id, t_start_ms);
CREATE INDEX IF NOT EXISTS idx_shot_tags_shot ON shot_tags (shot_id);
CREATE INDEX IF NOT EXISTS idx_shot_tags_tag  ON shot_tags (tag_id);
CREATE INDEX IF NOT EXISTS idx_deck_items_order ON deck_items (deck_id, sort_order);
```

## Configuration

`.env`:

```
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/shotdb
EMBEDDER=mock  # optional: enables mock text embeddings for dev
```

`docker-compose.yml`: Postgres 16 with pgvector, healthcheck, port 5432.

## Seeding

`python -m scripts.seed` inserts:

- one demo video
- a few shots (no real embeddings)
- a few tags and shot_tag links
- one deck with deck_items

## Scaling Later

- Add `comments` and `search_logs` tables with FK to shots and users.
- Add Redis cache for hot queries, small TTL.
- Increase IVFFlat lists as corpus grows; `ANALYZE shots` after bulk ingest.
- Swap mock embedder for CLIP or other model.
