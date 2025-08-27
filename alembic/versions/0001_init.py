"""Initial migration

Revision ID: 0001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable required extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    
    # Create videos table
    op.create_table('videos',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('src_url', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create shots table
    op.create_table('shots',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('video_id', sa.BigInteger(), nullable=False),
        sa.Column('t_start_ms', sa.Integer(), nullable=False),
        sa.Column('t_end_ms', sa.Integer(), nullable=False),
        sa.Column('thumb_url', sa.Text(), nullable=True),
        sa.Column('embedding', sa.Text(), nullable=True),  # Will be cast to VECTOR
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create tags table
    op.create_table('tags',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('slug', sa.Text(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    
    # Create shot_tags junction table
    op.create_table('shot_tags',
        sa.Column('shot_id', sa.BigInteger(), nullable=False),
        sa.Column('tag_id', sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(['shot_id'], ['shots.id'], ),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ),
        sa.PrimaryKeyConstraint('shot_id', 'tag_id')
    )
    
    # Create decks table
    op.create_table('decks',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create deck_items junction table
    op.create_table('deck_items',
        sa.Column('deck_id', sa.BigInteger(), nullable=False),
        sa.Column('shot_id', sa.BigInteger(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['deck_id'], ['decks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['shot_id'], ['shots.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('deck_id', 'shot_id')
    )
    
    # Create indexes
    op.create_index('idx_shots_video_time', 'shots', ['video_id', 't_start_ms'])
    op.create_index('idx_shot_tags_shot', 'shot_tags', ['shot_id'])
    op.create_index('idx_shot_tags_tag', 'shot_tags', ['tag_id'])
    op.create_index('idx_deck_items_order', 'deck_items', ['deck_id', 'sort_order'])
    
    # Create trigram indexes for fuzzy search
    op.execute("CREATE INDEX tag_name_trgm ON tags USING gin (name gin_trgm_ops)")
    op.execute("CREATE INDEX tag_slug_trgm ON tags USING gin (slug gin_trgm_ops)")
    
    # Cast embedding column to VECTOR type and create IVFFlat index
    op.execute("ALTER TABLE shots ALTER COLUMN embedding TYPE vector(768) USING embedding::vector")
    op.execute("CREATE INDEX shot_embedding_ivfflat ON shots USING ivfflat (embedding vector_cosine_ops) WITH (lists = 150)")


def downgrade() -> None:
    # Drop indexes
    op.drop_index('shot_embedding_ivfflat', table_name='shots')
    op.drop_index('tag_slug_trgm', table_name='tags')
    op.drop_index('tag_name_trgm', table_name='tags')
    op.drop_index('idx_deck_items_order', table_name='deck_items')
    op.drop_index('idx_shot_tags_tag', table_name='shot_tags')
    op.drop_index('idx_shot_tags_shot', table_name='shot_tags')
    op.drop_index('idx_shots_video_time', table_name='shots')
    
    # Drop tables
    op.drop_table('deck_items')
    op.drop_table('decks')
    op.drop_table('shot_tags')
    op.drop_table('tags')
    op.drop_table('shots')
    op.drop_table('videos')
    
    # Drop extensions
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
    op.execute("DROP EXTENSION IF EXISTS vector")
