"""Initial database schema."""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """Create initial tables."""
    # Create tokens table
    op.create_table(
        'tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('address', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=100)),
        sa.Column('symbol', sa.String(length=20)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('first_seen_at', sa.DateTime(timezone=True)),
        sa.Column('last_updated_at', sa.DateTime(timezone=True)),
        sa.Column('mint_authority', sa.String(length=64)),
        sa.Column('total_supply', sa.Numeric(precision=20, scale=0)),
        sa.Column('decimals', sa.Integer()),
        sa.Column('is_mint_disabled', sa.Boolean()),
        sa.Column('is_blacklisted', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('metadata', sa.JSON()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('address')
    )

    # Create token_metrics table
    op.create_table(
        'token_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('token_id', sa.Integer()),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('price', sa.Numeric(precision=20, scale=10)),
        sa.Column('volume_24h', sa.Numeric(precision=20, scale=2)),
        sa.Column('market_cap', sa.Numeric(precision=20, scale=2)),
        sa.Column('liquidity', sa.Numeric(precision=20, scale=2)),
        sa.Column('holder_count', sa.Integer()),
        sa.Column('buy_count_24h', sa.Integer()),
        sa.Column('sell_count_24h', sa.Integer()),
        sa.Column('safety_score', sa.Integer()),
        sa.Column('hype_score', sa.Integer()),
        sa.ForeignKeyConstraint(['token_id'], ['tokens.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_id', 'timestamp')
    )

    # Create monitored_groups table
    op.create_table(
        'monitored_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.BigInteger(), nullable=False),
        sa.Column('name', sa.String(length=100)),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true')),
        sa.Column('weight', sa.Float(), server_default=sa.text('1.0')),
        sa.Column('added_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_processed_message_id', sa.BigInteger()),
        sa.Column('metadata', sa.JSON()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('group_id')
    )

    # Create token_mentions table
    op.create_table(
        'token_mentions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('token_id', sa.Integer()),
        sa.Column('group_id', sa.Integer()),
        sa.Column('message_id', sa.BigInteger()),
        sa.Column('message_text', sa.Text()),
        sa.Column('mentioned_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('sentiment', sa.Float()),
        sa.Column('metadata', sa.JSON()),
        sa.ForeignKeyConstraint(['group_id'], ['monitored_groups.id']),
        sa.ForeignKeyConstraint(['token_id'], ['tokens.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create alerts table
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('token_id', sa.Integer()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('message_id', sa.Integer()),
        sa.Column('channel_id', sa.BigInteger()),
        sa.Column('alert_type', sa.String(length=20)),
        sa.Column('verdict', sa.String(length=20)),
        sa.Column('metrics_snapshot', sa.JSON()),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false')),
        sa.ForeignKeyConstraint(['token_id'], ['tokens.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indices
    op.create_index('idx_tokens_address', 'tokens', ['address'])
    op.create_index('idx_token_metrics_timestamp', 'token_metrics', ['timestamp'])
    op.create_index('idx_token_metrics_token_id', 'token_metrics', ['token_id'])
    op.create_index('idx_alerts_created_at', 'alerts', ['created_at'])
    op.create_index('idx_alerts_token_id', 'alerts', ['token_id'])
    op.create_index('idx_token_mentions_mentioned_at', 'token_mentions', ['mentioned_at'])
    op.create_index('idx_token_mentions_token_id', 'token_mentions', ['token_id'])
    op.create_index('idx_token_mentions_group_id', 'token_mentions', ['group_id'])

def downgrade():
    """Drop all tables."""
    op.drop_table('alerts')
    op.drop_table('token_mentions')
    op.drop_table('token_metrics')
    op.drop_table('monitored_groups')
    op.drop_table('tokens')
