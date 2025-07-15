"""Merge migration heads."""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = '003'
down_revision = ('001', '002')  # Merging heads
branch_labels = None
depends_on = None

def upgrade():
    """Empty upgrade - just merges revisions."""
    pass

def downgrade():
    """Empty downgrade."""
    pass
