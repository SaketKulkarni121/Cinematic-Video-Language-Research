from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # --- Enable required PostgreSQL extensions ---
    # vector: for vector similarity search (used for embeddings)
    # pg_trgm: for trigram-based fuzzy text search
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    
    # --- Videos table ---
    # Stores video metadata
    op.create_table(
        'videos',
        sa.Column('id', sa.BigInteger(), nullable=False),  # Primary key
        sa.Column('title', sa.Text(), nullable=False),     # Video title
        sa.Column('src_url', sa.Text(), nullable=False),   # Source URL of the video
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),  # Creation timestamp
        sa.PrimaryKeyConstraint('id')
    )
    
    # --- Shots table ---
    # Stores individual shots from videos
    op.create_table(
        'shots',
        sa.Column('id', sa.BigInteger(), nullable=False),  # Primary key
        sa.Column('video_id', sa.BigInteger(), nullable=False),  # ID of the video
        sa.Column('t_start_ms', sa.Integer(), nullable=False),   # Start time in ms
        sa.Column('t_end_ms', sa.Integer(), nullable=False),     # End time in ms
        sa.Column('thumb_url', sa.Text(), nullable=True),        # Thumbnail URL
        sa.Column('embedding', sa.Text(), nullable=True),        # Embedding vector
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),  # Creation timestamp
        sa.ForeignKeyConstraint(['video_id'], ['videos.id']),    # FK constraint to videos table
        sa.PrimaryKeyConstraint('id')
    )
    
    # --- Tags table ---
    # Stores tags for categorizing shots
    op.create_table(
        'tags',
        sa.Column('id', sa.BigInteger(), nullable=False),        # Primary key
        sa.Column('slug', sa.Text(), nullable=False),            # clean tag name
        sa.Column('name', sa.Text(), nullable=False),            # Public tag name
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),  # Creation timestamp
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')                              # Ensure clean tag is unique
    )
    
    # --- Shot_tags junction table ---
    # Many-to-many relationship between shots and tags
    op.create_table(
        'shot_tags',
        sa.Column('shot_id', sa.BigInteger(), nullable=False),   # FK to shots
        sa.Column('tag_id', sa.BigInteger(), nullable=False),    # FK to tags
        sa.ForeignKeyConstraint(['shot_id'], ['shots.id']),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id']),
        sa.PrimaryKeyConstraint('shot_id', 'tag_id')             # Composite PK
    )
    
    # --- Decks table ---
    # Stores user-created decks (collections of shots)
    op.create_table(
        'decks',
        sa.Column('id', sa.BigInteger(), nullable=False),        # Primary key
        sa.Column('user_id', sa.BigInteger(), nullable=False),   # User who owns the deck
        sa.Column('title', sa.Text(), nullable=False),           # Deck title
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),  # Creation timestamp
        sa.PrimaryKeyConstraint('id')
    )
    
    # --- Deck_items junction table ---
    # Many-to-many relationship between decks and shots, with ordering
    op.create_table(
        'deck_items',
        sa.Column('deck_id', sa.BigInteger(), nullable=False),   # FK to decks
        sa.Column('shot_id', sa.BigInteger(), nullable=False),   # FK to shots
        sa.Column('sort_order', sa.Integer(), nullable=True),    # Optional ordering of shots in deck
        sa.ForeignKeyConstraint(['deck_id'], ['decks.id'], ondelete='CASCADE'),  # Cascade delete on deck removal
        sa.ForeignKeyConstraint(['shot_id'], ['shots.id'], ondelete='CASCADE'),  # Cascade delete on shot removal
        sa.PrimaryKeyConstraint('deck_id', 'shot_id')            # Composite PK
    )
    
    # --- Indexes for performance ---
    
    # Index for fast lookup of shots by video and time
    op.create_index('idx_shots_video_time', 'shots', ['video_id', 't_start_ms'])
    
    # Indexes for fast lookup in shot_tags junction table
    op.create_index('idx_shot_tags_shot', 'shot_tags', ['shot_id'])
    op.create_index('idx_shot_tags_tag', 'shot_tags', ['tag_id'])
    
    # Index for ordering deck items within a deck
    op.create_index('idx_deck_items_order', 'deck_items', ['deck_id', 'sort_order'])
    
    # --- Trigram indexes for fuzzy search on tags ---
    # Enables fast LIKE/ILIKE queries on tag name and slug
    op.execute("CREATE INDEX tag_name_trgm ON tags USING gin (name gin_trgm_ops)")
    op.execute("CREATE INDEX tag_slug_trgm ON tags USING gin (slug gin_trgm_ops)")
    
    # --- Cast embedding column to VECTOR type and create IVFFlat index ---
    # Convert embedding column from text to vector(768) for similarity search
    op.execute("ALTER TABLE shots ALTER COLUMN embedding TYPE vector(768) USING embedding::vector")
    # Create IVFFlat index for efficient vector similarity search (cosine distance)
    op.execute("CREATE INDEX shot_embedding_ivfflat ON shots USING ivfflat (embedding vector_cosine_ops) WITH (lists = 150)")

def downgrade() -> None:
    # --- Drop indexes in reverse order of creation ---
    # Drop IVFFlat index for embeddings
    op.drop_index('shot_embedding_ivfflat', table_name='shots')
    # Drop trigram indexes for tags
    op.drop_index('tag_slug_trgm', table_name='tags')
    op.drop_index('tag_name_trgm', table_name='tags')
    # Drop other indexes
    op.drop_index('idx_deck_items_order', table_name='deck_items')
    op.drop_index('idx_shot_tags_tag', table_name='shot_tags')
    op.drop_index('idx_shot_tags_shot', table_name='shot_tags')
    op.drop_index('idx_shots_video_time', table_name='shots')
    
    # --- Drop tables in reverse dependency order ---
    op.drop_table('deck_items')
    op.drop_table('decks')
    op.drop_table('shot_tags')
    op.drop_table('tags')
    op.drop_table('shots')
    op.drop_table('videos')
    
    # --- Drop PostgreSQL extensions ---
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
    op.execute("DROP EXTENSION IF EXISTS vector")
