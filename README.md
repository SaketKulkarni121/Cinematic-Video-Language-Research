# CVLR Backend - Video Analysis Research Platform

This project implements a backend system for analyzing and organizing video content at the shot level, designed to support research in cinematic video language understanding. The system provides tools for video segmentation, semantic tagging, and similarity search using both traditional database techniques and vector embeddings.

## Project Overview

The platform enables researchers to:
- Upload and segment videos into individual shots
- Apply descriptive tags to shots for categorization
- Organize shots into collections called "decks"
- Perform similarity search using both tag-based and vector-based methods
- Build datasets for video analysis research

## Technology Stack

**Core Framework:**
- FastAPI for the web API
- SQLAlchemy 2.x for database operations
- Alembic for database migrations

**Database:**
- PostgreSQL 16 with pgvector extension for vector storage
- pg_trgm extension for fuzzy text search

**Language:** Python 3.11

## Getting Started

```bash
# Set up environment and start database
cp env.example .env
docker compose up -d

# Create Python environment and install dependencies
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Initialize database schema
alembic upgrade head

# Optional: populate with sample data
python -m scripts.seed

# Start the API server
uvicorn app.main:app --reload
```

Test the system by calling `GET /health` - it should return `{ "ok": true }`.

## Database Design

The schema is designed to be simple yet extensible for research applications:

```
videos
  id PK, title, src_url, created_at

shots
  id PK, video_id FK -> videos.id
  t_start_ms, t_end_ms, thumb_url
  embedding VECTOR(768) NULL  # Vector representation for similarity search
  created_at
  IDX (video_id, t_start_ms)
  IVFFlat(embedding vector_cosine_ops) WITH (lists=150)

tags
  id PK, slug UNIQUE, name
  GIN(name gin_trgm_ops), GIN(slug gin_trgm_ops)  # Fuzzy search support

shot_tags
  PK (shot_id, tag_id)  # Many-to-many relationship
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

Future additions will include `comments` and `search_logs` tables for research data collection.

## Search Capabilities

### Tag-Based Search

Uses PostgreSQL's trigram similarity for fuzzy matching on tag names and slugs. This allows researchers to find content even with approximate search terms.

- `GET /tags?query=...&threshold=0.2&page=1&page_size=24`
- `GET /shots?tag_query=...` finds shots with similar tags

The threshold parameter controls search precision - lower values require more exact matches.

### Vector Similarity Search

Enables semantic search by converting text queries to vector representations and finding similar shots.

- `GET /shots?q=...&top_k=200` performs vector similarity search

Currently uses a mock embedder for development. The database structure is ready for integration with models like CLIP or other embedding systems.

The `hybrid=true` option combines vector similarity with tag matching. This approach may be useful for research applications where both semantic and categorical information are relevant.

### Pagination

Standard pagination with `page` and `page_size` parameters for handling large result sets.

## API Structure

The API follows REST conventions with endpoints organized by resource type:

### Shots and Search
- `GET /shots` - Main search endpoint with comprehensive parameters
- `GET /shots/{id}` - Retrieve specific shot with related metadata

### Tags
- `GET /tags` - Search and browse tags
- `POST /tags` - Create new tags
- `PUT /tags/{id}` - Update existing tags

### Decks
- `GET /decks?user_id=...` - Retrieve user's collections
- `POST /decks` - Create new collection
- `POST /decks/{deck_id}/items` - Add shot to collection
- `DELETE /decks/{deck_id}/items/{shot_id}` - Remove shot from collection
- `PUT /decks/{deck_id}/items/reorder` - Reorder shots in collection

### Videos
- `POST /videos` - Upload new video content
- `GET /videos/{id}` - Retrieve video information

## Database Configuration

Required PostgreSQL extensions:

```sql
CREATE EXTENSION IF NOT EXISTS vector;      -- Vector storage and similarity
CREATE EXTENSION IF NOT EXISTS pg_trgm;     -- Fuzzy text search
```

Performance indices:

```sql
-- Vector similarity search
CREATE INDEX IF NOT EXISTS shot_embedding_ivfflat
ON shots USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 150);

-- Fuzzy search on tags
CREATE INDEX IF NOT EXISTS tag_name_trgm ON tags USING gin (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS tag_slug_trgm ON tags USING gin (slug gin_trgm_ops);

-- Query optimization
CREATE INDEX IF NOT EXISTS idx_shots_video_time ON shots (video_id, t_start_ms);
CREATE INDEX IF NOT EXISTS idx_shot_tags_shot ON shot_tags (shot_id);
CREATE INDEX IF NOT EXISTS idx_shot_tags_tag  ON shot_tags (tag_id);
CREATE INDEX IF NOT EXISTS idx_deck_items_order ON deck_items (deck_id, sort_order);
```

## Environment Configuration

The `.env` file requires:
```
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/shotdb
EMBEDDER=mock  # Will be replaced with actual embedding model
```

## Sample Data

The seeding script (`python -m scripts.seed`) creates:
- Sample video content
- Multiple shots with timing information
- Various tags and relationships
- Example deck with organized shots

## Development Roadmap

Planned improvements include:
- Integration with production embedding models
- User authentication and authorization
- Comment and search logging systems
- Performance optimization with caching
- Vector search parameter tuning

## Research Considerations

Several design decisions warrant further investigation:
- Effectiveness of hybrid search combining vector and tag similarity
- Optimal vector similarity metrics for video content
- Index type selection (IVFFlat vs HNSW) for different scales
- Handling of shots without vector representations

This system provides a foundation for video analysis research while maintaining flexibility for future enhancements and research directions.
