"""seed default user role

Revision ID: 9a2f0d1c4e77
Revises: bbab44c5ffa6
Create Date: 2026-05-03 17:20:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "9a2f0d1c4e77"
down_revision: Union[str, Sequence[str], None] = "bbab44c5ffa6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DEFAULT_USER_ROLE_ID = "11111111-1111-1111-1111-111111111111"


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        f"""
        INSERT INTO roles (id, name)
        VALUES ('{DEFAULT_USER_ROLE_ID}'::uuid, 'user')
        ON CONFLICT (name) DO NOTHING;
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        f"""
        DELETE FROM roles
        WHERE id = '{DEFAULT_USER_ROLE_ID}'::uuid AND name = 'user';
        """
    )
