"""add bot_config table for persistent settings

Revision ID: 004_add_bot_config_table
Revises: 003_merge
Create Date: 2024-07-16
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004_add_bot_config_table'
down_revision = '003'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'bot_config',
        sa.Column('alert_threshold', sa.Integer, nullable=False, server_default='5'),
        sa.Column('theme', sa.String(16), nullable=False, server_default='dark'),
        sa.Column('auto_refresh', sa.Boolean, nullable=False, server_default=sa.sql.expression.true()),
        sa.Column('notifications', sa.Boolean, nullable=False, server_default=sa.sql.expression.true()),
    )

def downgrade():
    op.drop_table('bot_config') 